"""
    CYA N - AI LOCAL DISPATCHER V7.6.0
    Entry Point dell'applicazione.
"""

import sys
import time
import psutil
import config
from ai_engine import get_ai_model, ResourceExhaustedError, would_use_fallback
from nn_classifier import predict as router_predict, PIPELINE_CLASSES, DOMAIN_NAMES, unload_router

_ERROR_PREFIXES  = ("Errore Ollama:", "Errore Generico:", "__SYS_WARN__:")
# [M5 FIX] Derivato da nn_classifier.DOMAIN_NAMES (unica fonte di verità)
# invece di ridichiarato come dict indipendente: prima, un domani un quinto
# dominio mono richiedeva l'aggiornamento sincrono di DUE file.
_CLASS_TO_DOMAIN = {i: name for i, name in enumerate(DOMAIN_NAMES[:4])}


def print_banner():
    print("\n" + "=" * 60)
    print("      CYA N  |  AI LOCAL DISPATCHER V7.6.0    ")
    print("      (Coding • Math • Rights • General)      ")
    print("=" * 60 + "\n")


_HISTORY_MSG_MAX_CHARS = config.SYSTEM_SETTINGS.get('history_message_max_chars', 1200)


def _truncate_for_history(text: str, limit: int = _HISTORY_MSG_MAX_CHARS) -> str:
    """
    [C1 FIX] Tronca un singolo messaggio PRIMA di inserirlo in chat_history.
    Prima nessun cap esisteva sulla lunghezza dei messaggi (solo sul numero,
    via max_history_turns): con ctx_size=4096 fisso per tutti i domini, una
    sliding window di 10 messaggi con risposte lunghe (codice, spiegazioni
    rights estese) rischiava l'overflow silenzioso in Ollama, che tronca
    tipicamente dall'inizio del contesto — perdendo il system prompt stesso
    senza errore visibile. Il testo COMPLETO resta comunque stampato
    all'utente durante lo streaming in ai_engine.py::generate(): questo
    troncamento agisce solo su ciò che viene ricordato nei turni successivi.
    """
    if len(text) > limit:
        return text[:limit] + "\n...[STORICO TRONCATO PER LIMITI DI CONTESTO]..."
    return text


def _update_history(history: list, user_input: str, response: str, max_messages: int):
    """[CHAT] Aggiunge il turno corrente alla history e applica la sliding window."""
    history.append({'role': 'user',      'content': _truncate_for_history(user_input)})
    history.append({'role': 'assistant', 'content': _truncate_for_history(response)})
    if len(history) > max_messages:
        del history[:len(history) - max_messages]


def _is_error(result: str) -> bool:
    """Controlla se il risultato è un messaggio d'errore di sistema."""
    return not result or any(result.startswith(p) for p in _ERROR_PREFIXES)


def _expected_model(agent, difficulty: int) -> str:
    """
    [DIFF-ROUTING] Anteprima informativa (SOLO log) del modello che verrà
    selezionato dato `difficulty`. Il valore REALE resta deciso a runtime
    da check_resources() in ai_engine.py.
    [DUP-5 FIX] Usa ai_engine.would_use_fallback(), stessa formula del
    comportamento reale — prima duplicata qui a mano.
    """
    if would_use_fallback(difficulty, agent.fallback_model):
        return f"{agent.fallback_model} (fallback, diff={difficulty})"
    return f"{agent.model_name} (primary, diff={difficulty})"



def main():
    print_banner()

    agents = {
        'coding':  get_ai_model('coding'),
        'math':    get_ai_model('math'),
        'rights':  get_ai_model('rights'),
        'general': get_ai_model('general')
    }

    chat_history: list      = []
    max_history_turns       = config.SYSTEM_SETTINGS.get('max_history_turns', 3)
    max_messages            = max_history_turns * 2
    last_active_domain: str = ''

    while True:
        try:
            try:
                user_input = input("Inserisci la tua richiesta (o 'exit' per uscire): ").strip()
            except EOFError:
                break

            if not user_input:
                print("⚠️  Richiesta vuota. Riprova.")
                continue

            if user_input.lower() in ['exit', 'esci', 'quit', 'q']:
                print("\nChiusura sessione. A presto! 👋")
                break

            if user_input.lower() in ['/reset', '/clear']:
                chat_history.clear()
                last_active_domain = ''
                print("🔄 Chat history e dominio attivo azzerati.\n")
                continue

            # ---------------------------------------------------------
            # FASE 0: ROUTING NEURALE — class_id è l'UNICA fonte di verità
            # per il DOMINIO. domain_scores resta solo diagnostica.
            # `difficulty` guida invece il TIER (primary/fallback) del
            # modello nel dominio già scelto — vedi ai_engine.py
            # ::_resolve_tier_from_difficulty(). Non altera mai class_id.
            # ---------------------------------------------------------
            print("\n⚙️  Fase 0 — Classificazione Neurale (NN Router)...")
            class_id, confidence, domain_scores, difficulty, is_followup = router_predict(
                user_input, chat_history
            )

            if class_id == -1:
                print("⚠️  [ERRORE] Neural classifier non disponibile: richiesta non instradabile.")
                print("   Verifica che 'classifier/nn_weights.pt' sia presente (esegui train_nn.py) e riprova.")
                print("\n" + "_" * 60 + "\n")
                continue

            if domain_scores:
                scores_str = ' | '.join(f"{k}:{v:.2f}" for k, v in domain_scores.items())
                print(f"🔍 [DEBUG NEURAL] Scores: [{scores_str}] | "
                      f"Difficulty: {difficulty} (→ tier routing) | Followup: {is_followup}")

            domain_switched = False  # [HISTORY] solo igiene contesto, non instradamento
            is_hybrid        = False
            domain_a = domain_b = ""

            if class_id in PIPELINE_CLASSES:
                domain_a, domain_b = PIPELINE_CLASSES[class_id]
                is_hybrid = True
                print(f"🔍 [DEBUG NEURAL] Classe={DOMAIN_NAMES[class_id]} | "
                      f"Confidence={confidence:.2f} | "
                      f"Pipeline: {domain_a.upper()} → {domain_b.upper()}")
                # [A1 FIX] L'isolamento history esisteva PRIMA solo nel ramo
                # mono-dominio: se l'ultimo dominio attivo era 'general' e la
                # nuova richiesta attivava una pipeline math->coding, la
                # history general contaminava l'agente A senza protezione —
                # lo stesso scenario che questo meccanismo doveva evitare,
                # ma applicato a un solo ramo di codice invece che a entrambi.
                if last_active_domain and domain_a != last_active_domain:
                    domain_switched = True
            else:
                target = _CLASS_TO_DOMAIN[class_id]
                print(f"🔍 [DEBUG NEURAL] Classe={DOMAIN_NAMES[class_id]} | "
                      f"Confidence={confidence:.2f} | Dominio: {target.upper()}")
                if last_active_domain and target != last_active_domain:
                    domain_switched = True  # [HISTORY] dominio cambia → isola history

            unload_router()

            # ---------------------------------------------------------
            # ESECUZIONE PIPELINE IBRIDA
            # ---------------------------------------------------------
            if is_hybrid:
                # [A1 FIX] Stesso pattern di isolamento già usato nel ramo
                # mono-dominio, ora applicato anche qui.
                effective_history = [] if domain_switched else chat_history
                if domain_switched:
                    print(f"🔄 [HISTORY] Domain switch rilevato: history isolata per "
                          f"pipeline {domain_a.upper()}→{domain_b.upper()}")

                print(f"\n╭── 🧠 PIPELINE IBRIDA [{domain_a.upper()} → {domain_b.upper()}] in azione...")
                print(f"│ Agente A (Draft): {_expected_model(agents[domain_a], difficulty)}")
                print(f"│ Agente B (Merge): {_expected_model(agents[domain_b], difficulty)}")
                print(f"╰──────────────────────────────────────────")

                print(f"\n⚙️  Fase 1/3 — Elaborazione contesto [{domain_a.upper()}] in corso...")
                try:
                    output_a = agents[domain_a].resolve_pipeline_a(
                        user_input, domain_b, effective_history, difficulty
                    )
                except ResourceExhaustedError as e:
                    print(f"\n⛔ OOM — Pipeline interrotta in Fase 1/3: {e}")
                    print("\n" + "_" * 60 + "\n")
                    continue

                if _is_error(output_a):
                    print(output_a)
                    print("\n" + "_" * 60 + "\n")
                    continue

                print("⚙️  Sincronizzazione — Scaricamento esplicito modello A in corso...")
                agents[domain_a].explicit_unload()

                unload_wait              = config.PIPELINE_SETTINGS.get('ram_unload_wait', 1.5)
                target_ram               = agents[domain_b].primary_ram_req
                timeout_sincronizzazione = config.PIPELINE_SETTINGS.get('ram_sync_timeout', 20.0)
                inizio_attesa            = time.time()
                time.sleep(unload_wait)

                while (time.time() - inizio_attesa) < timeout_sincronizzazione:
                    if psutil.virtual_memory().available >= target_ram:
                        break
                    time.sleep(0.5)
                else:
                    print("⚠️  Timeout sincronizzazione RAM: procedo comunque.")

                print(f"⚙️  Fase 2/3 — Integrazione dominio [{domain_b.upper()}] in corso...")
                try:
                    output_b = agents[domain_b].resolve_pipeline_b(
                        user_input, output_a, domain_a, effective_history, difficulty
                    )
                except ResourceExhaustedError as e:
                    print(f"\n⛔ OOM — Pipeline interrotta in Fase 2/3: {e}")
                    print("\n" + "_" * 60 + "\n")
                    continue

                if _is_error(output_b):
                    print(output_b)
                    print("\n" + "_" * 60 + "\n")
                    continue

                print(f"⚙️  Fase 3/3 — Autovalutazione e sintesi [{domain_b.upper()}]...")
                print("-" * 42)

                try:
                    result = agents[domain_b].execute_critic_pass(output_b, user_input, difficulty)
                except ResourceExhaustedError as e:
                    print(f"\n⛔ OOM — Pipeline interrotta in Fase 3/3: {e}")
                    print("\n" + "_" * 60 + "\n")
                    continue

                if _is_error(result):
                    print(result)
                else:
                    _update_history(chat_history, user_input, result, max_messages)
                    last_active_domain = domain_b

                print("\n" + "_" * 60 + "\n")
                continue

            # ---------------------------------------------------------
            # ESECUZIONE MONO-DOMINIO
            # ---------------------------------------------------------
            ai_agent = agents[target]

            # [HISTORY] Isola la history se il dominio è cambiato: evita che
            # il modello del nuovo dominio "veda" risposte di un dominio
            # diverso e generi output contaminati. Non altera MAI target.
            effective_history = [] if domain_switched else chat_history
            if domain_switched:
                print(f"🔄 [HISTORY] Domain switch rilevato: history isolata per {target.upper()}")

            print(f"\n╭── 🧠 MODULO [{target.upper()}] in azione...")
            print(f"│ Modello: {_expected_model(ai_agent, difficulty)}")
            print(f"╰──────────────────────────────────────────")

            try:
                result = ai_agent.resolve(user_input, effective_history, difficulty)
            except ResourceExhaustedError as e:
                print(f"\n⛔ OOM — Esecuzione interrotta: {e}")
                print("\n" + "_" * 60 + "\n")
                continue

            if _is_error(result):
                print(result)
            else:
                _update_history(chat_history, user_input, result, max_messages)
                last_active_domain = target   # aggiorna sempre, anche su 'general'

            print("\n" + "_" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n\n🛑 Interruzione manuale rilevata.")
            print("Chiusura sicura degli archi di sistema...")
            sys.exit(0)

        except Exception as e:
            print(f"\n❌ ERRORE IMPREVISTO: {e}")
            print("Consiglio: Verifica che l'arco di comunicazione con Ollama sia attivo.")
            print("\n" + "_" * 60 + "\n")


if __name__ == "__main__":
    main()