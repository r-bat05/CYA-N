"""
    MOTORE AI IBRIDO V6.6.2

    Novita' V6.6.2:
    - [BUG1] Stringa di fallback per output vuoto modificata da "ATTENZIONE: ..."
      a "__SYS_WARN__: ...". Il vecchio prefisso coincideva con l'output legittimo
      dei modelli (es. "ATTENZIONE: questo codice e' pericoloso"), causando
      un falso positivo in _is_error() di main.py che spezzava silenziosamente
      la Chat History e lo Sticky Routing.

    Novita' V6.6.1:
    - [BUG4] _GUARD calcolato su max(len(_OPEN_TAG), len(_CLOSE_TAG)) - 1.
    - [BUGA] execute_critic_pass() ora chiama _truncate_context(draft_b).

    Novita' V6.6.0:
    - [CHAT] Chat History integrata in resolve(), resolve_pipeline_a(),
      resolve_pipeline_b().
    - [CHAT] few_shot fuso nel system prompt.
    - [CHAT] execute_critic_pass() invariato nel design (no history).

    Novita' V6.5.0:
    - [P2] Rimossi magic numbers. Aggiunto BaseAI._truncate_context().

    Novita' V6.2.3:
    - [FIX CRITICO] generate() solleva ResourceExhaustedError invece di
      restituire stringa senza prefisso emoji.
"""

import ollama
import time
import psutil
from abc import ABC, abstractmethod
from helper import clean_response, SpinnerContext, print_time_elapsed
from prompts_templates import get_prompts, PIPELINE_PROMPTS
import config

# --- Tag di ragionamento (configurabili via config.SYSTEM_SETTINGS) ---
_OPEN_TAG  = config.SYSTEM_SETTINGS.get('think_open_tag',  '<think>')
_CLOSE_TAG = config.SYSTEM_SETTINGS.get('think_close_tag', '</think>')

# [BUG4 FIX] La guardia deve essere profonda quanto il tag PIU' LUNGO.
_GUARD = max(len(_OPEN_TAG), len(_CLOSE_TAG)) - 1


class ResourceExhaustedError(Exception):
    """Sollevata da generate() quando check_resources() fallisce."""
    pass


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
        self.primary_ram_req  = config.RAM_THRESHOLDS[self.cfg['ram_threshold']]
        self.fallback_ram_req = 0
        if self.cfg['fallback_ram_threshold']:
            self.fallback_ram_req = config.RAM_THRESHOLDS[self.cfg['fallback_ram_threshold']]
        self.is_using_fallback = False
        self._last_used_model = None   # [DIFETTO2] Traccia il modello realmente usato

    def _truncate_context(self, text: str) -> str:
        """
        [P2] Tronca il contesto passato tra agenti al limite configurato.
        """
        limit = config.PIPELINE_SETTINGS.get('pipeline_max_context_chars', 6000)
        if len(text) > limit:
            return text[:limit] + "\n...[ARCO INFORMATIVO TRONCATO PER LIMITI DI CONTESTO]..."
        return text

    @staticmethod
    def _merge_few_shot(sys_prompt: str, few_shot: str) -> str:
        """
        [CHAT] Fonde il few-shot nel system prompt.
        """
        if few_shot and few_shot.strip():
            return f"{sys_prompt}\n\n{few_shot.strip()}"
        return sys_prompt
    
    def explicit_unload(self):
        """
        [DIFETTO2 FIX] Forza lo scaricamento esplicito del modello da Ollama.

        generate() invia keep_alive=0 nel body della request, ma su Linux il
        rilascio del mmap dei tensori avviene in modo asincrono: il processo
        Ollama può impiegare secondi prima di restituire le pagine fisiche all'OS.
        Una seconda chiamata separata con prompt vuoto forza Ollama a processare
        il comando di unload immediatamente, prima che main.py avvii il polling RAM.

        Usa _last_used_model (tracciato in generate()) per evitare di caricare
        accidentalmente un modello non attivo solo per scaricarlo.
        """
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
        self._last_used_model = target_model  # [DIFETTO2] Salva prima che finally resetti lo stato

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

                # --- DRAIN LOOP ---
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

            # --- FLUSH FINALE ---
            if stream_buf and not is_thinking:
                display_content = clean_response(stream_buf)
                if display_content and stream_output:
                    spinner.stop()
                    print(display_content, end="", flush=True)
                full_response += stream_buf

            # [BUG1 FIX] Prefisso univoco __SYS_WARN__: invece di ATTENZIONE:
            # per evitare falsi positivi in _is_error() di main.py quando il
            # modello inizia legittimamente una risposta con "ATTENZIONE:".
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
    def resolve(self, prompt: str, history: list = None): pass

    @abstractmethod
    def resolve_pipeline_a(self, prompt: str, domain_b: str, history: list = None): pass

    @abstractmethod
    def resolve_pipeline_b(self, original_prompt: str, output_a: str, domain_a: str, history: list = None): pass

    @abstractmethod
    def execute_critic_pass(self, draft_b: str, original_prompt: str): pass


class CodeLlamaAI(BaseAI):
    def __init__(self):
        super().__init__('coding')

    def resolve(self, prompt: str, history: list = None):
        history = history or []
        sys_prompt, few_shot, _ = get_prompts('coding')
        combined_sys = self._merge_few_shot(sys_prompt, few_shot)
        final_prompt = (f"[RICHIESTA]: {prompt}\n\n"
                        f"[IMPORTANTE]: Spiega il codice e i concetti ESCLUSIVAMENTE IN ITALIANO.")
        messages = [
            {'role': 'system', 'content': combined_sys},
            *history,
            {'role': 'user',   'content': final_prompt}
        ]
        return self.generate(messages)

    def resolve_pipeline_a(self, prompt: str, domain_b: str, history: list = None):
        history = history or []
        sys_prompt, few_shot, _ = get_prompts('coding')
        combined_sys = self._merge_few_shot(sys_prompt, few_shot)
        directional  = PIPELINE_PROMPTS['directional'].format(domain_b=domain_b.upper())
        final_prompt = f"[RICHIESTA]: {prompt}\n{directional}"
        messages = [
            {'role': 'system', 'content': combined_sys},
            *history,
            {'role': 'user',   'content': final_prompt}
        ]
        return self.generate(messages, stream_output=False, force_unload=True)

    def resolve_pipeline_b(self, original_prompt: str, output_a: str, domain_a: str, history: list = None):
        output_a = self._truncate_context(output_a)
        history  = history or []
        sys_prompt, _, _ = get_prompts('coding')
        handoff = PIPELINE_PROMPTS['handoff'].format(
            original_query=original_prompt,
            domain_a=domain_a.upper(),
            output_a=output_a,
            domain_b=self.category.upper()
        )
        messages = [
            {'role': 'system', 'content': sys_prompt},
            *history,
            {'role': 'user',   'content': handoff}
        ]
        return self.generate(messages, stream_output=False, force_unload=False)

    def execute_critic_pass(self, draft_b: str, original_prompt: str):
        draft_b    = self._truncate_context(draft_b)
        sys_prompt, _, _ = get_prompts('coding')
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


class DeepSeekAI(BaseAI):
    def __init__(self):
        super().__init__('math')

    def resolve(self, prompt: str, history: list = None):
        history = history or []
        _, _, enforcement = get_prompts('math')
        messages = [
            *history,
            {'role': 'user', 'content': f"{prompt}{enforcement}"}
        ]
        return self.generate(messages)

    def resolve_pipeline_a(self, prompt: str, domain_b: str, history: list = None):
        history = history or []
        _, _, enforcement = get_prompts('math')
        directional = PIPELINE_PROMPTS['directional'].format(domain_b=domain_b.upper())
        messages = [
            *history,
            {'role': 'user', 'content': f"{prompt}{enforcement}{directional}"}
        ]
        return self.generate(messages, stream_output=False, force_unload=True)

    def resolve_pipeline_b(self, original_prompt: str, output_a: str, domain_a: str, history: list = None):
        output_a = self._truncate_context(output_a)
        history  = history or []
        _, _, enforcement = get_prompts('math')
        handoff = PIPELINE_PROMPTS['handoff'].format(
            original_query=original_prompt,
            domain_a=domain_a.upper(),
            output_a=output_a,
            domain_b=self.category.upper()
        )
        messages = [
            *history,
            {'role': 'user', 'content': f"{handoff}{enforcement}"}
        ]
        return self.generate(messages, stream_output=False, force_unload=False)

    def execute_critic_pass(self, draft_b: str, original_prompt: str):
        draft_b         = self._truncate_context(draft_b)
        critic_template = PIPELINE_PROMPTS['critic']
        if "{original_query}" in critic_template:
            critic = critic_template.format(original_query=original_prompt)
        else:
            critic = f"{critic_template}\n\n[DOMANDA ORIGINALE DELL'UTENTE]:\n\"{original_prompt}\""
        messages = [
            {'role': 'assistant', 'content': draft_b},
            {'role': 'user',      'content': critic}
        ]
        return self.generate(messages, stream_output=True, force_unload=False)


class GptOssAI(BaseAI):
    def __init__(self, category='general'):
        super().__init__(category)

    def resolve(self, prompt: str, history: list = None):
        history = history or []
        sys_prompt, few_shot, _ = get_prompts(self.category)
        combined_sys      = self._merge_few_shot(sys_prompt, few_shot)
        full_user_content = (f"[RICHIESTA UTENTE]: {prompt}\n\n"
                             f"[IMPORTANTE]: Rispondi IN ITALIANO.")
        messages = [
            {'role': 'system', 'content': combined_sys},
            *history,
            {'role': 'user',   'content': full_user_content}
        ]
        return self.generate(messages)

    def resolve_pipeline_a(self, prompt: str, domain_b: str, history: list = None):
        history = history or []
        sys_prompt, few_shot, _ = get_prompts(self.category)
        combined_sys      = self._merge_few_shot(sys_prompt, few_shot)
        directional       = PIPELINE_PROMPTS['directional'].format(domain_b=domain_b.upper())
        full_user_content = f"[RICHIESTA UTENTE]: {prompt}\n{directional}"
        messages = [
            {'role': 'system', 'content': combined_sys},
            *history,
            {'role': 'user',   'content': full_user_content}
        ]
        return self.generate(messages, stream_output=False, force_unload=True)

    def resolve_pipeline_b(self, original_prompt: str, output_a: str, domain_a: str, history: list = None):
        output_a = self._truncate_context(output_a)
        history  = history or []
        sys_prompt, _, _ = get_prompts(self.category)
        handoff = PIPELINE_PROMPTS['handoff'].format(
            original_query=original_prompt,
            domain_a=domain_a.upper(),
            output_a=output_a,
            domain_b=self.category.upper()
        )
        messages = [
            {'role': 'system', 'content': sys_prompt},
            *history,
            {'role': 'user',   'content': handoff}
        ]
        return self.generate(messages, stream_output=False, force_unload=False)

    def execute_critic_pass(self, draft_b: str, original_prompt: str):
        draft_b         = self._truncate_context(draft_b)
        sys_prompt, _, _ = get_prompts(self.category)
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
    if category == 'coding':
        return CodeLlamaAI()
    elif category == 'math':
        return DeepSeekAI()
    elif category == 'rights':
        return GptOssAI(category='rights')
    else:
        return GptOssAI(category='general')
