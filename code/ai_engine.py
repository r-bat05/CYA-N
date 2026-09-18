"""
    MOTORE AI IBRIDO V6.9.0

    Novita' V6.9.0 (Refactor — report_patch.md):
    - [DUP-4 / Opzione B] CodeLlamaAI/DeepSeekAI/GptOssAI unificate in
      un'unica classe DomainAI, guidata dalla tabella dati
      prompts_templates.DOMAIN_AI_CONFIG. get_ai_model() restituisce
      sempre DomainAI(category). Comportamento equivalente byte-per-byte
      ai messages generati dalle 3 classi precedenti.
    - [DUP-5] would_use_fallback(difficulty, fallback_model): unica
      formula per la decisione di tier, usata sia da
      _resolve_tier_from_difficulty() sia da main.py::_expected_model().

"""

import ollama
import time
import psutil
from abc import ABC, abstractmethod
from helper import clean_response, SpinnerContext, print_time_elapsed
from prompts_templates import get_prompts, PIPELINE_PROMPTS, DOMAIN_AI_CONFIG
import config

_OPEN_TAG  = config.SYSTEM_SETTINGS.get('think_open_tag',  '<think>')
_CLOSE_TAG = config.SYSTEM_SETTINGS.get('think_close_tag', '</think>')
_GUARD = max(len(_OPEN_TAG), len(_CLOSE_TAG)) - 1


class ResourceExhaustedError(Exception):
    """Sollevata da generate() quando check_resources() fallisce."""
    pass


def would_use_fallback(difficulty: int, fallback_model) -> bool:
    """
    [DUP-5 FIX] Unica formula per "userà il tier fallback dato questo
    difficulty e questo fallback_model". Usata sia dal comportamento
    reale (_resolve_tier_from_difficulty) sia dall'anteprima di log
    (main.py::_expected_model).
    """
    threshold = config.TIER_ROUTING_SETTINGS.get('fallback_max_difficulty', 1)
    return bool(difficulty <= threshold and fallback_model)


class BaseAI(ABC):
    def __init__(self, category):
        if category not in config.MODELS_CONFIG:
            print(f"WARNING Categoria '{category}' non trovata in config. Uso 'general'.")
            category = 'general'

        self.cfg              = config.MODELS_CONFIG[category]
        self.category         = category
        self.model_name       = self.cfg['primary']
        self.fallback_model   = self.cfg['fallback']
        self.temperature      = self.cfg['temperature']
        self.prompt_tier      = self.cfg.get('prompt_tier', 'compact')
        self.primary_ram_req  = config.RAM_THRESHOLDS[self.cfg['ram_threshold']]
        self.fallback_ram_req = 0
        if self.cfg['fallback_ram_threshold']:
            self.fallback_ram_req = config.RAM_THRESHOLDS[self.cfg['fallback_ram_threshold']]
        self.is_using_fallback = False
        self._last_used_model = None

    def _resolve_tier_from_difficulty(self, difficulty: int) -> None:
        """Imposta is_using_fallback PRIMA di check_resources()/generate()."""
        self.is_using_fallback = would_use_fallback(difficulty, self.fallback_model)

    def _truncate_context(self, text: str) -> str:
        limit = config.PIPELINE_SETTINGS.get('pipeline_max_context_chars', 6000)
        if len(text) > limit:
            return text[:limit] + "\n...[ARCO INFORMATIVO TRONCATO PER LIMITI DI CONTESTO]..."
        return text

    @staticmethod
    def _merge_few_shot(sys_prompt: str, few_shot: str) -> str:
        if few_shot and few_shot.strip():
            return f"{sys_prompt}\n\n{few_shot.strip()}"
        return sys_prompt

    def explicit_unload(self):
        target = self._last_used_model or self.model_name
        try:
            ollama.generate(model=target, prompt="", keep_alive=0)
        except Exception:
            pass
        self._last_used_model = None

    def check_resources(self):
        try:
            available_ram = psutil.virtual_memory().available
        except Exception as e:
            print(f"WARNING Impossibile leggere la RAM di sistema: {e}. Procedo a rischio.")
            return True

        if self.is_using_fallback:
            if available_ram < self.fallback_ram_req:
                print(f"\nERRORE CRITICO: RAM insufficiente anche per il modello leggero.")
                print(f"   Disponibili: {available_ram / config.GB:.2f} GB "
                      f"< Richiesti: {self.fallback_ram_req / config.GB:.2f} GB")
                return False
            return True

        if available_ram < self.primary_ram_req:
            print(f"\nWARN RAM INSUFFICIENTE per {self.model_name}")
            print(f"   Disponibili: {available_ram / config.GB:.2f} GB "
                  f"< Richiesti: {self.primary_ram_req / config.GB:.2f} GB")
            if self.fallback_model:
                print(f"Downgrade PREVENTIVO a [{self.fallback_model}]...")
                self.is_using_fallback = True
                return self.check_resources()
            else:
                print(f"ERRORE Nessun modello di riserva configurato per {self.category}.")
                return False

        return True

    def generate(self, messages: list, stream_output=True, force_unload=False):
        if not self.check_resources():
            self.is_using_fallback = False
            raise ResourceExhaustedError(
                f"RAM insufficiente per avviare qualsiasi modello nel dominio '{self.category}'. "
                f"Libera memoria e riprova."
            )

        full_response = ""
        start_time    = time.time()
        target_model  = self.fallback_model if self.is_using_fallback else self.model_name
        self._last_used_model = target_model

        options = {
            'temperature': self.temperature,
            'num_ctx':     config.SYSTEM_SETTINGS['ctx_size']
        }
        keep_alive = 0 if force_unload else config.SYSTEM_SETTINGS['ollama_keep_alive']

        spinner_msg = (f"Consultando [{target_model}]..." if stream_output
                       else f"Elaborazione in background [{target_model}]...")
        spinner = SpinnerContext(spinner_msg)
        spinner.start()

        stream_buf  = ""
        is_thinking = False

        try:
            stream = ollama.chat(
                model=target_model,
                messages=messages,
                stream=True,
                keep_alive=keep_alive,
                options=options
            )

            for chunk in stream:
                stream_buf += chunk['message']['content']

                keep_draining = True
                while keep_draining:
                    keep_draining = False

                    if is_thinking:
                        close_idx = stream_buf.find(_CLOSE_TAG)
                        if close_idx != -1:
                            is_thinking = False
                            stream_buf  = stream_buf[close_idx + len(_CLOSE_TAG):]
                            if stream_output:
                                spinner.stop()
                            keep_draining = True
                        else:
                            if len(stream_buf) > _GUARD:
                                stream_buf = stream_buf[-_GUARD:]
                    else:
                        open_idx = stream_buf.find(_OPEN_TAG)
                        if open_idx != -1:
                            safe       = stream_buf[:open_idx]
                            stream_buf = stream_buf[open_idx + len(_OPEN_TAG):]
                            is_thinking = True
                            if safe:
                                display_content = clean_response(safe)
                                if display_content and stream_output:
                                    spinner.stop()
                                    print(display_content, end="", flush=True)
                                full_response += safe
                            keep_draining = True
                        else:
                            lt_pos = stream_buf.rfind('<')
                            if lt_pos != -1 and lt_pos >= len(stream_buf) - _GUARD:
                                safe       = stream_buf[:lt_pos]
                                stream_buf = stream_buf[lt_pos:]
                            else:
                                safe       = stream_buf
                                stream_buf = ""

                            if safe:
                                display_content = clean_response(safe)
                                if display_content and stream_output:
                                    spinner.stop()
                                    print(display_content, end="", flush=True)
                                full_response += safe

            if stream_buf and not is_thinking:
                display_content = clean_response(stream_buf)
                if display_content and stream_output:
                    spinner.stop()
                    print(display_content, end="", flush=True)
                full_response += stream_buf

            if not full_response:
                return "__SYS_WARN__: Il modello non ha generato output."

        except ollama.ResponseError as e:
            return (f"Errore Ollama: {e}\n"
                    f"Assicurati che il servizio sia attivo.")
        except Exception as e:
            return (f"Errore Generico: {e}\n"
                    f"Verifica la connessione o il modello ('ollama pull {target_model}').")

        finally:
            spinner.stop()
            self.is_using_fallback = False

        if stream_output:
            print_time_elapsed(start_time)

        return clean_response(full_response)

    @abstractmethod
    def resolve(self, prompt: str, history: list = None, difficulty: int = 2): pass

    @abstractmethod
    def resolve_pipeline_a(self, prompt: str, domain_b: str, history: list = None, difficulty: int = 2): pass

    @abstractmethod
    def resolve_pipeline_b(self, original_prompt: str, output_a: str, domain_a: str, history: list = None, difficulty: int = 2): pass

    @abstractmethod
    def execute_critic_pass(self, draft_b: str, original_prompt: str, difficulty: int = 2): pass


class DomainAI(BaseAI):
    """
    [Opzione B — report_patch.md §5] Unica classe concreta per tutti e 4
    i domini: sostituisce CodeLlamaAI/DeepSeekAI/GptOssAI (stesso
    scheletro di 4 metodi, differenza solo nel template del "content"
    finale). Le differenze sono dati (DOMAIN_AI_CONFIG), non codice.
    """
    def __init__(self, category):
        super().__init__(category)
        self._behavior = DOMAIN_AI_CONFIG[self.category]

    def resolve(self, prompt: str, history: list = None, difficulty: int = 2):
        self._resolve_tier_from_difficulty(difficulty)
        history = history or []
        sys_prompt, few_shot, enforcement = get_prompts(self.category, self.prompt_tier)
        combined_sys = self._merge_few_shot(sys_prompt, few_shot)
        content = self._behavior['resolve_template'].format(
            prompt=prompt, enforcement=enforcement, directional='',
            lang_note=self._behavior['lang_note'] or ''
        )
        messages = [
            {'role': 'system', 'content': combined_sys},
            *history,
            {'role': 'user',   'content': content}
        ]
        return self.generate(messages)

    def resolve_pipeline_a(self, prompt: str, domain_b: str, history: list = None, difficulty: int = 2):
        self._resolve_tier_from_difficulty(difficulty)
        history = history or []
        sys_prompt, few_shot, enforcement = get_prompts(self.category, self.prompt_tier)
        combined_sys = self._merge_few_shot(sys_prompt, few_shot)
        directional  = PIPELINE_PROMPTS['directional'].format(domain_b=domain_b.upper())
        content = self._behavior['pipeline_a_template'].format(
            prompt=prompt, enforcement=enforcement, directional=directional,
            lang_note=self._behavior['lang_note'] or ''
        )
        messages = [
            {'role': 'system', 'content': combined_sys},
            *history,
            {'role': 'user',   'content': content}
        ]
        return self.generate(messages, stream_output=False, force_unload=True)

    def resolve_pipeline_b(self, original_prompt: str, output_a: str, domain_a: str, history: list = None, difficulty: int = 2):
        self._resolve_tier_from_difficulty(difficulty)
        output_a = self._truncate_context(output_a)
        history  = history or []
        sys_prompt, _, enforcement = get_prompts(self.category, self.prompt_tier)
        handoff = PIPELINE_PROMPTS['handoff'].format(
            original_query=original_prompt,
            domain_a=domain_a.upper(),
            output_a=output_a,
            domain_b=self.category.upper()
        )
        content = self._behavior['pipeline_b_template'].format(handoff=handoff, enforcement=enforcement)
        messages = [
            {'role': 'system', 'content': sys_prompt},
            *history,
            {'role': 'user',   'content': content}
        ]
        return self.generate(messages, stream_output=False, force_unload=False)

    def execute_critic_pass(self, draft_b: str, original_prompt: str, difficulty: int = 2):
        self._resolve_tier_from_difficulty(difficulty)
        draft_b = self._truncate_context(draft_b)
        sys_prompt, _, _ = get_prompts(self.category, self.prompt_tier)
        critic_template  = PIPELINE_PROMPTS['critic']
        if "{original_query}" in critic_template:
            critic = critic_template.format(original_query=original_prompt)
        else:
            critic = f"{critic_template}\n\n[DOMANDA ORIGINALE DELL'UTENTE]:\n\"{original_prompt}\""
        messages = [
            {'role': 'system',    'content': sys_prompt},
            {'role': 'assistant', 'content': draft_b},
            {'role': 'user',      'content': critic}
        ]
        return self.generate(messages, stream_output=True, force_unload=False)


def get_ai_model(category: str):
    return DomainAI(category)