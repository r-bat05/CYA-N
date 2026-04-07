"""
    MOTORE AI IBRIDO V6.2.3 (LLM Pipeline & Critic Pass)

    Novita' V6.2.3:
    - [FIX CRITICO] Anti-pattern return testuale per OOM: il metodo generate()
      ora solleva ResourceExhaustedError invece di restituire una stringa senza
      prefisso emoji. Questo permette a main.py di intercettare correttamente
      l'esaurimento delle risorse con un blocco try/except tipizzato, evitando
      che l'output di errore venga passato al secondo agente della pipeline.

    Novita' V6.2.2:
    - [FIX CRITICO] Bug tag <think> frammentati sullo streaming: il controllo
      per chunk singolo (`"<think>" in content`) fallisce quando Ollama spezza
      il tag su piu' token consecutivi (es. chunk1="<th", chunk2="ink>").
      Il contenuto di ragionamento "bucava" il filtro e veniva stampato a video,
      creando incoerenza tra output visibile e full_response interna.
      Fix: introdotto stream_buf come buffer di accumulo. Per ogni chunk il
      contenuto viene appeso al buffer e poi drenato in un loop finche' non
      ci sono piu' operazioni possibili. La ricerca dei tag avviene sempre
      sul buffer completo, non sul singolo chunk. La soglia di flush conserva
      gli ultimi _GUARD=7 caratteri se contengono un '<' che potrebbe essere
      l'inizio di un tag incompleto, rimandando l'output al chunk successivo.

    Novita' V6.2.1:
    - [FIX CRITICO] Bug "buco nero" tag <think> in streaming: la logica
      precedente usava due `if` sequenziali indipendenti. Quando il chunk
      conteneva entrambi i tag (<think>pensiero</think>risposta), il primo `if`
      eseguiva content.split("<think>", 1)[0], riducendo `content` a stringa
      vuota PRIMA che il secondo `if` potesse trovare </think>. Risultato:
      is_thinking rimaneva bloccato su True e tutto l'output successivo veniva
      scartato silenziosamente.

    Novita' V6.2:
    - [FIX] Bug prefisso errori: rimosso "\\n\\n" iniziale dai return degli except.
    - [FIX] Bug chunk thinking misto (parziale, completato in V6.2.1).

    Novita' V6.1:
    - [FIX] Vulnerabilita' C: troncamento difensivo in resolve_pipeline_b (max 6000 chars).
    - [FIX] Vulnerabilita' B: firma execute_critic_pass aggiornata con original_query.
"""

import ollama
import time
import psutil
from abc import ABC, abstractmethod
from helper import clean_response, SpinnerContext, print_time_elapsed
from prompts_templates import get_prompts, PIPELINE_PROMPTS
import config

# Lunghezza del tag piu' lungo che dobbiamo rilevare: len("</think>") = 8.
# Teniamo _GUARD = 7 caratteri in coda al buffer se contengono '<',
# per non perdere un tag spezzato tra due chunk consecutivi.
_GUARD = len("</think>") - 1  # 7


class ResourceExhaustedError(Exception):
    """
    Sollevata da generate() quando check_resources() fallisce.
    Sostituisce il precedente anti-pattern del return testuale senza prefisso
    emoji, permettendo a main.py di intercettarla con un blocco tipizzato
    invece di affidarsi al fragile check startswith(_ERROR_PREFIXES).
    """
    pass


class BaseAI(ABC):
    def __init__(self, category):
        if category not in config.MODELS_CONFIG:
            print(f"WARNING Categoria '{category}' non trovata in config. Uso 'general'.")
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
        start_time = time.time()
        target_model = self.fallback_model if self.is_using_fallback else self.model_name

        options = {
            'temperature': self.temperature,
            'num_ctx': config.SYSTEM_SETTINGS['ctx_size']
        }
        keep_alive = 0 if force_unload else config.SYSTEM_SETTINGS['ollama_keep_alive']

        spinner_msg = (f"Consultando [{target_model}]..." if stream_output
                       else f"Elaborazione in background [{target_model}]...")
        spinner = SpinnerContext(spinner_msg)
        spinner.start()

        # Buffer di accumulo per la gestione robusta dei tag <think> frammentati.
        # Ogni chunk viene appeso qui prima di essere processato.
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
                # Processa il buffer finche' ci sono operazioni completabili.
                # Si ferma quando: non ci sono tag completi e il residuo e'
                # troppo corto per determinare se un '<' e' un tag parziale.
                keep_draining = True
                while keep_draining:
                    keep_draining = False

                    if is_thinking:
                        close_idx = stream_buf.find("</think>")
                        if close_idx != -1:
                            # Tag di chiusura trovato: esci dalla modalita' thinking
                            is_thinking = False
                            stream_buf = stream_buf[close_idx + 8:]  # 8 = len("</think>")
                            if stream_output:
                                spinner.stop()
                            keep_draining = True  # potrebbe esserci contenuto dopo </think>
                        else:
                            # Nessun </think> ancora: scarta il contenuto di thinking
                            # ma tieni gli ultimi _GUARD chars per non perdere il tag spezzato
                            if len(stream_buf) > _GUARD:
                                stream_buf = stream_buf[-_GUARD:]
                            # Non possiamo fare altro: aspetta il prossimo chunk
                    else:
                        open_idx = stream_buf.find("<think>")
                        if open_idx != -1:
                            # Tag di apertura trovato: emetti tutto cio' che precede
                            safe = stream_buf[:open_idx]
                            stream_buf = stream_buf[open_idx + 7:]  # 7 = len("<think>")
                            is_thinking = True
                            if safe:
                                display_content = clean_response(safe)
                                if display_content and stream_output:
                                    spinner.stop()
                                    print(display_content, end="", flush=True)
                                full_response += safe
                            keep_draining = True  # processa il resto del buffer
                        else:
                            # Nessun <think> nel buffer. Determina il punto di flush sicuro.
                            # Se c'e' un '<' negli ultimi _GUARD caratteri, potrebbe essere
                            # l'inizio di un <think> spezzato: non emettere oltre quel punto.
                            lt_pos = stream_buf.rfind('<')
                            if lt_pos != -1 and lt_pos >= len(stream_buf) - _GUARD:
                                # '<' vicino alla fine: emetti solo fino a lt_pos
                                safe = stream_buf[:lt_pos]
                                stream_buf = stream_buf[lt_pos:]
                            else:
                                # Nessun '<' pericoloso in coda: flush completo
                                safe = stream_buf
                                stream_buf = ""

                            if safe:
                                display_content = clean_response(safe)
                                if display_content and stream_output:
                                    spinner.stop()
                                    print(display_content, end="", flush=True)
                                full_response += safe
                            # Non c'e' altro da drenare: aspetta il prossimo chunk

            # --- FLUSH FINALE ---
            # Lo stream e' terminato. Qualsiasi contenuto rimasto nel buffer
            # che non sia inside un blocco thinking deve essere emesso.
            if stream_buf and not is_thinking:
                display_content = clean_response(stream_buf)
                if display_content and stream_output:
                    spinner.stop()
                    print(display_content, end="", flush=True)
                full_response += stream_buf

            if not full_response:
                return "ATTENZIONE: Il modello non ha generato output."

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
    def resolve(self, prompt: str): pass

    @abstractmethod
    def resolve_pipeline_a(self, prompt: str, domain_b: str): pass

    @abstractmethod
    def resolve_pipeline_b(self, original_prompt: str, output_a: str, domain_a: str): pass

    @abstractmethod
    def execute_critic_pass(self, draft_b: str, original_prompt: str): pass


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
            {'role': 'system',    'content': sys_prompt},
            {'role': 'assistant', 'content': draft_b},
            {'role': 'user',      'content': critic}
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
            {'role': 'user',      'content': critic}
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
