"""
    MOTORE AI IBRIDO V6.1 (LLM Pipeline & Critic Pass)

    Novità V6.1:
    - [FIX] Vulnerabilità C: Aggiunto troncamento difensivo dell'arco di contesto
      in `resolve_pipeline_b` per evitare la saturazione della RAM/Token (max 6000 chars).
    - [FIX] Vulnerabilità B: Aggiornata la firma di `execute_critic_pass` per ricevere
      l'arco informativo della query originale e inocularlo nel prompt dell'Agente B.
"""

import ollama
import time
import psutil
from abc import ABC, abstractmethod
from helper import clean_response, SpinnerContext, print_time_elapsed
from prompts_templates import get_prompts, PIPELINE_PROMPTS
import config


class BaseAI(ABC):
    """
    Classe astratta che gestisce la logica comune di generazione e controllo risorse.
    Si inizializza leggendo i parametri direttamente da config.MODELS_CONFIG.
    """

    def __init__(self, category):
        if category not in config.MODELS_CONFIG:
            print(f"⚠️ Categoria '{category}' non trovata in config. Uso 'general'.")
            category = 'general'

        self.cfg = config.MODELS_CONFIG[category]
        self.category = category
        self.model_name = self.cfg['primary']
        self.fallback_model = self.cfg['fallback']
        self.temperature = self.cfg['temperature']

        self.primary_ram_req = config.RAM_THRESHOLDS[self.cfg['ram_threshold']]

        self.fallback_ram_req = 0
        if self.cfg['fallback_ram_threshold']:
            self.fallback_ram_req = config.RAM_THRESHOLDS[self.cfg['fallback_ram_threshold']]

        self.is_using_fallback = False

    def check_resources(self):
        """
        Controlla la RAM disponibile confrontandola con le soglie in config.py.
        Restituisce True se si può procedere, False se le risorse sono insufficienti.
        """
        try:
            available_ram = psutil.virtual_memory().available
        except Exception as e:
            print(f"⚠️ Impossibile leggere la RAM di sistema: {e}. Procedo a rischio.")
            return True

        # CASO 1: Siamo già in modalità Fallback
        if self.is_using_fallback:
            if available_ram < self.fallback_ram_req:
                print(f"\n⛔ ERRORE CRITICO: RAM insufficiente anche per il modello leggero.")
                print(f"   Disponibili: {available_ram / config.GB:.2f} GB "
                      f"< Richiesti: {self.fallback_ram_req / config.GB:.2f} GB")
                return False
            return True

        # CASO 2: Tentativo con Modello Primario
        if available_ram < self.primary_ram_req:
            print(f"\n⚠️  RAM INSUFFICIENTE per {self.model_name}")
            print(f"   Disponibili: {available_ram / config.GB:.2f} GB "
                  f"< Richiesti: {self.primary_ram_req / config.GB:.2f} GB")

            if self.fallback_model:
                print(f"📉  Downgrade PREVENTIVO a [{self.fallback_model}]...")
                self.is_using_fallback = True
                return self.check_resources()
            else:
                print(f"❌  Nessun modello di riserva configurato per {self.category}.")
                return False

        return True

    def generate(self, messages: list, stream_output=True, force_unload=False):
        """Gestisce la chiamata a Ollama, lo streaming e la pulizia."""

        # 1. Controllo Risorse
        if not self.check_resources():
            self.is_using_fallback = False
            return "⛔ SISTEMA ARRESTATO PER MANCANZA DI MEMORIA."

        full_response = ""
        start_time = time.time()

        # 2. Selezione Modello
        target_model = self.fallback_model if self.is_using_fallback else self.model_name

        # 3. Impostazioni di Sistema da config.py
        options = {
            'temperature': self.temperature,
            'num_ctx': config.SYSTEM_SETTINGS['ctx_size']
        }
        
        # 4. Scelta del keep_alive (scaricamento forzato per pipeline)
        keep_alive = 0 if force_unload else config.SYSTEM_SETTINGS['ollama_keep_alive']

        spinner_msg = f"Consultando [{target_model}]..." if stream_output else f"Elaborazione in background [{target_model}]..."
        spinner = SpinnerContext(spinner_msg)
        spinner.start()

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
                content = chunk['message']['content']

                # --- LOGICA DI FILTRAGGIO STREAMING ---
                if "<think>" in content:
                    is_thinking = True
                    content = content.replace("<think>", "")

                if "</think>" in content:
                    is_thinking = False
                    content = content.replace("</think>", "")
                    if stream_output:
                        spinner.stop()

                if is_thinking:
                    continue

                if content:
                    display_content = clean_response(content)
                    if display_content and stream_output:
                        spinner.stop()
                        print(display_content, end="", flush=True)

                full_response += content

            if not full_response:
                return "\n\n⚠️  ATTENZIONE: Il modello non ha generato output."

        except ollama.ResponseError as e:
            return (f"\n\n❌ Errore Ollama: {e}\n"
                    f"Assicurati che il servizio sia attivo.")
        except Exception as e:
            return (f"\n\n❌ Errore Generico: {e}\n"
                    f"Verifica la connessione o il modello ('ollama pull {target_model}').")

        finally:
            # FIX BUG #1: il finally garantisce il reset su OGNI path di uscita
            spinner.stop()
            self.is_using_fallback = False

        if stream_output:
            print_time_elapsed(start_time)
            
        return clean_response(full_response)

    @abstractmethod
    def resolve(self, prompt: str):
        pass

    @abstractmethod
    def resolve_pipeline_a(self, prompt: str, domain_b: str):
        pass

    @abstractmethod
    def resolve_pipeline_b(self, original_prompt: str, output_a: str, domain_a: str):
        pass

    @abstractmethod
    def execute_critic_pass(self, draft_b: str, original_prompt: str):
        pass


# --- IMPLEMENTAZIONI SPECIFICHE ---

class CodeLlamaAI(BaseAI):
    def __init__(self):
        super().__init__('coding')

    def resolve(self, prompt: str):
        sys_prompt, few_shot, _ = get_prompts('coding')
        final_prompt = (f"{few_shot}\n[RICHIESTA]: {prompt}\n\n"
                        f"[IMPORTANTE]: Spiega il codice e i concetti ESCLUSIVAMENTE IN ITALIANO.")
        messages = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user',   'content': final_prompt}
        ]
        return self.generate(messages)

    def resolve_pipeline_a(self, prompt: str, domain_b: str):
        sys_prompt, few_shot, _ = get_prompts('coding')
        directional = PIPELINE_PROMPTS['directional'].format(domain_b=domain_b.upper())
        final_prompt = f"{few_shot}\n[RICHIESTA]: {prompt}\n{directional}"
        messages = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user',   'content': final_prompt}
        ]
        return self.generate(messages, stream_output=False, force_unload=True)

    def resolve_pipeline_b(self, original_prompt: str, output_a: str, domain_a: str):
        # Difesa saturazione arco di contesto (max 6000 caratteri)
        if len(output_a) > 6000:
            output_a = output_a[:6000] + "\n...[ARCO INFORMATIVO TRONCATO PER LIMITI DI CONTESTO]..."

        sys_prompt, _, _ = get_prompts('coding')
        handoff = PIPELINE_PROMPTS['handoff'].format(
            original_query=original_prompt,
            domain_a=domain_a.upper(),
            output_a=output_a,
            domain_b=self.category.upper()
        )
        messages = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user',   'content': handoff}
        ]
        return self.generate(messages, stream_output=False, force_unload=False)

    def execute_critic_pass(self, draft_b: str, original_prompt: str):
        sys_prompt, _, _ = get_prompts('coding')
        
        critic_template = PIPELINE_PROMPTS['critic']
        if "{original_query}" in critic_template:
            critic = critic_template.format(original_query=original_prompt)
        else:
            critic = f"{critic_template}\n\n[DOMANDA ORIGINALE DELL'UTENTE]:\n\"{original_prompt}\""

        messages = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'assistant', 'content': draft_b},
            {'role': 'user',   'content': critic}
        ]
        return self.generate(messages, stream_output=True, force_unload=False)


class DeepSeekAI(BaseAI):
    def __init__(self):
        super().__init__('math')

    def resolve(self, prompt: str):
        _, _, enforcement = get_prompts('math')
        messages = [{'role': 'user', 'content': f"{prompt}{enforcement}"}]
        return self.generate(messages)

    def resolve_pipeline_a(self, prompt: str, domain_b: str):
        _, _, enforcement = get_prompts('math')
        directional = PIPELINE_PROMPTS['directional'].format(domain_b=domain_b.upper())
        messages = [{'role': 'user', 'content': f"{prompt}{enforcement}{directional}"}]
        return self.generate(messages, stream_output=False, force_unload=True)

    def resolve_pipeline_b(self, original_prompt: str, output_a: str, domain_a: str):
        # Difesa saturazione arco di contesto
        if len(output_a) > 6000:
            output_a = output_a[:6000] + "\n...[ARCO INFORMATIVO TRONCATO PER LIMITI DI CONTESTO]..."

        _, _, enforcement = get_prompts('math')
        handoff = PIPELINE_PROMPTS['handoff'].format(
            original_query=original_prompt,
            domain_a=domain_a.upper(),
            output_a=output_a,
            domain_b=self.category.upper()
        )
        messages = [{'role': 'user', 'content': f"{handoff}{enforcement}"}]
        return self.generate(messages, stream_output=False, force_unload=False)

    def execute_critic_pass(self, draft_b: str, original_prompt: str):
        critic_template = PIPELINE_PROMPTS['critic']
        if "{original_query}" in critic_template:
            critic = critic_template.format(original_query=original_prompt)
        else:
            critic = f"{critic_template}\n\n[DOMANDA ORIGINALE DELL'UTENTE]:\n\"{original_prompt}\""

        messages = [
            {'role': 'assistant', 'content': draft_b},
            {'role': 'user',   'content': critic}
        ]
        return self.generate(messages, stream_output=True, force_unload=False)


class GptOssAI(BaseAI):
    def __init__(self, category='general'):
        super().__init__(category)

    def resolve(self, prompt: str):
        sys_prompt, few_shot, _ = get_prompts(self.category)
        full_user_content = (f"{few_shot}\n[RICHIESTA UTENTE]: {prompt}\n\n"
                             f"[IMPORTANTE]: Rispondi IN ITALIANO.")
        messages = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user',   'content': full_user_content}
        ]
        return self.generate(messages)

    def resolve_pipeline_a(self, prompt: str, domain_b: str):
        sys_prompt, few_shot, _ = get_prompts(self.category)
        directional = PIPELINE_PROMPTS['directional'].format(domain_b=domain_b.upper())
        full_user_content = f"{few_shot}\n[RICHIESTA UTENTE]: {prompt}\n{directional}"
        messages = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user',   'content': full_user_content}
        ]
        return self.generate(messages, stream_output=False, force_unload=True)

    def resolve_pipeline_b(self, original_prompt: str, output_a: str, domain_a: str):
        # Difesa saturazione arco di contesto
        if len(output_a) > 6000:
            output_a = output_a[:6000] + "\n...[ARCO INFORMATIVO TRONCATO PER LIMITI DI CONTESTO]..."

        sys_prompt, _, _ = get_prompts(self.category)
        handoff = PIPELINE_PROMPTS['handoff'].format(
            original_query=original_prompt,
            domain_a=domain_a.upper(),
            output_a=output_a,
            domain_b=self.category.upper()
        )
        messages = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user',   'content': handoff}
        ]
        return self.generate(messages, stream_output=False, force_unload=False)

    def execute_critic_pass(self, draft_b: str, original_prompt: str):
        sys_prompt, _, _ = get_prompts(self.category)
        
        critic_template = PIPELINE_PROMPTS['critic']
        if "{original_query}" in critic_template:
            critic = critic_template.format(original_query=original_prompt)
        else:
            critic = f"{critic_template}\n\n[DOMANDA ORIGINALE DELL'UTENTE]:\n\"{original_prompt}\""

        messages = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'assistant', 'content': draft_b},
            {'role': 'user',   'content': critic}
        ]
        return self.generate(messages, stream_output=True, force_unload=False)


# --- FACTORY ---

def get_ai_model(category: str):
    """
    Factory che restituisce l'istanza corretta in base alla categoria.
    La logica dei modelli è definita in config.py;
    qui mappiamo la categoria alla classe Python che costruisce il prompt.
    """
    if category == 'coding':
        return CodeLlamaAI()
    elif category == 'math':
        return DeepSeekAI()
    elif category == 'rights':
        return GptOssAI(category='rights')
    else:
        return GptOssAI(category='general')