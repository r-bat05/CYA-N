"""
    CYA N - AI LOCAL DISPATCHER V7.4.0
    Entry Point dell'applicazione.

    Novità V7.4.0 (Routing purity — output NN come unica fonte):
    - [ROUTING PURITY] Rimossa _should_sticky_route() e l'intero meccanismo
      di Domain Retention/override basato su soglie di confidenza Python
      (sticky_tech_switch_min, sticky_short_override_min, sticky_short_words).
      Il dominio instradato è ora SEMPRE quello indicato da class_id, senza
      eccezioni basate su last_active_domain.
    - [ROUTING PURITY] Rimossa la declassificazione pipeline per query corte
      (min_words_for_pipeline): se class_id è una classe pipeline (4/5/6),
      la pipeline viene eseguita a prescindere dal numero di parole.
    - [ROUTING PURITY] Rimossa la promozione "SCORE PIPELINE" (mono→pipeline
      via domain_scores + pipeline_score_min): non esiste più nessuna logica
      che promuove una classificazione mono-dominio della NN a pipeline.
    - [ROUTING PURITY] Rimossa [P0] GUARDIA GENERAL: era già codice morto
      dopo la rimozione della promozione score-based, dato che 'general' non
      è mai incluso in PIPELINE_CLASSES (vedi nn_classifier.py).
    - [ROUTING PURITY] Rimosso _TECHNICAL_DOMAINS: usato solo dai meccanismi
      sopra.
    - Risultato: class_id (e la sua mappatura PIPELINE_CLASSES/_CLASS_TO_DOMAIN)
      è l'UNICA fonte che decide dominio singolo vs pipeline. domain_scores,
      difficulty e is_followup restano solo a scopo di log/debug — nessuna
      logica in questo file li usa più per alterare l'instradamento.
    - [HISTORY] domain_switched resta: NON è instradamento, decide solo se
      isolare la chat history passata all'agente per evitare contaminazione
      tra domini diversi. Non cambia mai il dominio scelto dalla NN.

    Novità V7.3.0 (Cleanup post-branch build_classifier_NN):
    - [CLEANUP] Rimosso il ramo di fallback a keyword-dispatcher (mai
      importato, codice morto). Se il classifier non è disponibile, il
      turno viene scartato con un errore esplicito.
    - [CLEANUP] Rimossa _has_domain_keywords() e last_pipeline_domains.

    Novità V7.2.0:
    - [ROUTER SWAP] llm_router.py rimosso. Import sostituito con
      nn_classifier.py (MultiTaskMLP locale, nessuna chiamata Ollama per
      il routing). Interfaccia predict() identica.

    Novità V7.0.0:
    - [NEURAL] Sostituito routing k-NN con neural_classifier.py.
    - [NEURAL] Pipeline detection integrata nel class_id del classifier.
"""

import sys
import time
import psutil
import config
from ai_engine import get_ai_model, ResourceExhaustedError
from nn_classifier import predict as router_predict, PIPELINE_CLASSES, DOMAIN_NAMES, unload_router

_ERROR_PREFIXES  = ("Errore Ollama:", "Errore Generico:", "__SYS_WARN__:")
_CLASS_TO_DOMAIN = {0: 'coding', 1: 'math', 2: 'rights', 3: 'general'}


def print_banner():
    print("\n" + "=" * 60)
    print("      CYA N  |  AI LOCAL DISPATCHER V7.4.0    ")
    print("      (Coding • Math • Rights • General)      ")
    print("=" * 60 + "\n")


def _update_history(history: list, user_input: str, response: str, max_messages: int):
    """[CHAT] Aggiunge il turno corrente alla history e applica la sliding window."""
    history.append({'role': 'user',      'content': user_input})
    history.append({'role': 'assistant', 'content': response})
    if len(history) > max_messages:
        del history[:len(history) - max_messages]


def _is_error(result: str) -> bool:
    """Controlla se il risultato è un messaggio d'errore di sistema."""
    return not result or any(result.startswith(p) for p in _ERROR_PREFIXES)


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
            # FASE 0: ROUTING NEURALE — class_id è l'UNICA fonte di verità.
            # domain_scores, difficulty e is_followup sono solo diagnostica:
            # nessuna riga di codice sotto li usa per cambiare l'instradamento.
            # ---------------------------------------------------------
            print("\n⚙️  Fase 0 — Classificazione Neurale (NN Router)...")
            class_id, confidence, domain_scores, difficulty, is_followup = router_predict(
                user_input, last_active_domain, chat_history
            )

            if class_id == -1:
                print("⚠️  [ERRORE] Neural classifier non disponibile: richiesta non instradabile.")
                print("   Verifica che 'classifier/nn_weights.pt' sia presente (esegui train_nn.py) e riprova.")
                print("\n" + "_" * 60 + "\n")
                continue

            if domain_scores:
                scores_str = ' | '.join(f"{k}:{v:.2f}" for k, v in domain_scores.items())
                print(f"🔍 [DEBUG NEURAL] Scores: [{scores_str}] | "
                      f"Difficulty: {difficulty} | Followup: {is_followup}")

            domain_switched = False  # [HISTORY] solo igiene contesto, non instradamento
            is_hybrid        = False
            domain_a = domain_b = ""

            if class_id in PIPELINE_CLASSES:
                domain_a, domain_b = PIPELINE_CLASSES[class_id]
                is_hybrid = True
                print(f"🔍 [DEBUG NEURAL] Classe={DOMAIN_NAMES[class_id]} | "
                      f"Confidence={confidence:.2f} | "
                      f"Pipeline: {domain_a.upper()} → {domain_b.upper()}")
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
                print(f"\n╭── 🧠 PIPELINE IBRIDA [{domain_a.upper()} → {domain_b.upper()}] in azione...")
                print(f"│ Agente A (Draft): {agents[domain_a].model_name}")
                print(f"│ Agente B (Merge): {agents[domain_b].model_name}")
                print(f"╰──────────────────────────────────────────")

                print(f"\n⚙️  Fase 1/3 — Elaborazione contesto [{domain_a.upper()}] in corso...")
                try:
                    output_a = agents[domain_a].resolve_pipeline_a(
                        user_input, domain_b, chat_history
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
                        user_input, output_a, domain_a, chat_history
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
                    result = agents[domain_b].execute_critic_pass(output_b, user_input)
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
            print(f"│ Modello: {ai_agent.model_name}")
            print(f"╰──────────────────────────────────────────")

            try:
                result = ai_agent.resolve(user_input, effective_history)
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


if __name__ == "__main__":
    main()