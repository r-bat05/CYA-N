"""
    CYA N - AI LOCAL DISPATCHER V7.1.0
    Entry Point dell'applicazione.

    Novità V7.1.0:
    - [ROUTER] predict() ora restituisce (class_id, conf, scores, difficulty, is_followup).
    - [STICKY V7.2] _should_sticky_route semplificato: LLM-first.
      La logica Python ridotta a 3 step:
        1. Override esplicito (context switch tecnico)
        2. LLM is_followup=True → stick
        3. Pipeline follow-up (Python-side, fuori visibilità LLM)
      Rimossi step query_corta e weak_general: il LLM ora li gestisce direttamente
      tramite is_followup. Questo elimina i falsi sticky su "ricetta sacher?",
      "Dio esiste?", "consiglio scarpe" quando il LLM classifica correttamente.
    - [HISTORY] History isolation su domain switch: quando il dominio cambia,
      viene passata history vuota all'agente per evitare contaminazione da
      risposte precedenti di un dominio diverso (fix "esempio?" → risposta TFR).
    - [LOG] Stampa difficulty e domain_scores dal router.

    Novità V7.0.0:
    - [NEURAL] Sostituito routing k-NN con neural_classifier.py → llm_router.py
    - [NEURAL] Pipeline detection integrata nel class_id del classifier
    - [CLEANUP] Rimossi classify_knn, initialize_store, pipeline_order_matrix
"""

import re as _re
import sys
import time
import psutil
import config
import dispatcher_request
from ai_engine import get_ai_model, ResourceExhaustedError
from llm_router import predict as router_predict, PIPELINE_CLASSES, DOMAIN_NAMES, unload_router
from dispatcher_request import keyword_loader, _count_hits

_ERROR_PREFIXES    = ("Errore Ollama:", "Errore Generico:", "__SYS_WARN__:")
_TECHNICAL_DOMAINS = {'coding', 'math', 'rights'}
_CLASS_TO_DOMAIN   = {0: 'coding', 1: 'math', 2: 'rights', 3: 'general'}


def print_banner():
    print("\n" + "=" * 60)
    print("      CYA N  |  AI LOCAL DISPATCHER V7.1.0    ")
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


def _has_domain_keywords(query: str, domain: str) -> bool:
    """Restituisce True se la query contiene almeno una keyword del dominio dato."""
    kw_map = {
        'coding': keyword_loader.CODING,
        'math':   keyword_loader.MATH,
        'rights': keyword_loader.RIGHTS,
    }
    if domain not in kw_map:
        return False
    s_lower = query.lower()
    tokens  = set(_re.findall(r'[a-zA-Z0-9_+#]+', s_lower))
    return _count_hits(tokens, s_lower, kw_map[domain]) > 0


def _should_sticky_route(
    query: str,
    sem_domains: list,
    sem_confidence: float,
    last_domain: str,
    is_followup_llm: bool = False,
    last_pipeline_domains: tuple = ('', ''),
) -> tuple:
    """
    Domain Retention V7.2 — LLM-first.

    Il LLM (tramite is_followup_llm) è il segnale primario per il follow-up.
    Il Python gestisce solo ciò che il LLM non può vedere:
      1. Override esplicito (context switch verso dominio tecnico diverso)
      2. LLM is_followup=True → stick
      3. Pipeline follow-up (Python-side: last_pipeline_domains non è nel contesto LLM)

    Returns: (should_stick, sticky_domain, reason, override_target)
    """
    if not last_domain or last_domain not in _TECHNICAL_DOMAINS:
        return False, last_domain, '', None

    tech_switch_min    = config.SYSTEM_SETTINGS.get('sticky_tech_switch_min',    0.38)
    short_override_min = config.SYSTEM_SETTINGS.get('sticky_short_override_min', 0.65)
    short_threshold    = config.SYSTEM_SETTINGS.get('sticky_short_words',        10)

    word_count = len(query.split())
    top_domain = sem_domains[0] if sem_domains else 'general'
    is_short   = word_count < short_threshold

    # --- 1. Override: context switch verso dominio tecnico diverso ---
    override_threshold = short_override_min if is_short else tech_switch_min
    switching_domains  = [
        d for d in sem_domains
        if d in _TECHNICAL_DOMAINS and d != last_domain
    ]
    if switching_domains and sem_confidence >= override_threshold:
        override_target = top_domain if top_domain in switching_domains else switching_domains[0]
        return False, last_domain, '', override_target

    # --- 2. LLM dice follow-up → stick ---
    if is_followup_llm:
        return True, last_domain, 'llm_followup', None

    # --- 3. Pipeline follow-up (Python-side, fuori dalla visibilità LLM) ---
    pipe_a, pipe_b = last_pipeline_domains
    if (pipe_a and pipe_b
            and last_domain == pipe_b
            and top_domain == 'general'
            and _has_domain_keywords(query, pipe_a)):
        return True, pipe_a, f'pipeline_followup({pipe_a})', None

    return False, last_domain, '', None


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
    last_pipeline_domains: tuple = ('', '')

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
                last_active_domain    = ''
                last_pipeline_domains = ('', '')
                print("🔄 Chat history e dominio attivo azzerati.\n")
                continue

            # ---------------------------------------------------------
            # FASE 0: ROUTING NEURALE
            # ---------------------------------------------------------
            print("\n⚙️  Fase 0 — Classificazione Neurale (LLM Router)...")
            class_id, confidence, domain_scores, difficulty, is_followup_llm = router_predict(
                user_input, last_active_domain, chat_history
            )

            is_hybrid  = False
            domain_a   = domain_b = ""
            domain_switched = False  # [HISTORY] flag per isolamento history
            categories_segments = {k: [] for k in agents.keys()}

            # =============================================================
            # CASO FALLBACK: classifier non disponibile
            # =============================================================
            if class_id == -1:
                print("⚠️  [FALLBACK] Neural classifier non disponibile.")
                print("🔄 [FALLBACK] Attivazione instradamento a Keyword come emergenza...")

                is_hybrid, domain_a, domain_b = dispatcher_request.detect_hybrid(user_input)
                if not is_hybrid:
                    winning_domain = dispatcher_request.classify_segment(user_input)
                    if winning_domain == 'general':
                        # In fallback: sticky solo se LLM non disponibile, usa Python puro
                        stick, sticky_domain, reason, override_target = _should_sticky_route(
                            user_input, ['general'], 1.0, last_active_domain,
                            is_followup_llm=False,
                            last_pipeline_domains=last_pipeline_domains,
                        )
                        if stick:
                            print(f"📎 [STICKY] Keyword fallback su 'general'. "
                                  f"Domain Retention → {sticky_domain.upper()} [{reason}]")
                            winning_domain = sticky_domain
                        elif override_target:
                            winning_domain = override_target

                    if winning_domain != last_active_domain and last_active_domain:
                        domain_switched = True

                    categories_segments[winning_domain if winning_domain in categories_segments
                                        else 'general'] = [user_input]

            # =============================================================
            # ROUTING NEURALE VALIDO
            # =============================================================
            else:
                word_count = len(user_input.split())
                min_words  = config.PIPELINE_SETTINGS.get('min_words_for_pipeline', 12)

                # Log scores e difficulty
                if domain_scores:
                    scores_str = ' | '.join(f"{k}:{v:.2f}" for k, v in domain_scores.items())
                    print(f"🔍 [DEBUG NEURAL] Scores: [{scores_str}] | Difficulty: {difficulty}")

                if class_id in PIPELINE_CLASSES:
                    domain_a, domain_b = PIPELINE_CLASSES[class_id]
                    original_sem_domains  = [domain_a, domain_b]
                    is_pipeline_candidate = True
                else:
                    top_domain = _CLASS_TO_DOMAIN[class_id]
                    original_sem_domains  = [top_domain]
                    is_pipeline_candidate = False

                # Declassifica pipeline se query troppo corta
                if is_pipeline_candidate and word_count < min_words:
                    print(f"🔍 [DEBUG NEURAL] Classe pipeline declassata: "
                          f"query troppo corta ({word_count} < {min_words} parole).")
                    is_pipeline_candidate = False

                print(f"🔍 [DEBUG NEURAL] Classe={DOMAIN_NAMES[class_id]} | "
                      f"Confidence={confidence:.2f} | "
                      f"Pipeline={'CONFERMATA' if is_pipeline_candidate else 'NO'}")

                if is_pipeline_candidate:
                    print(f"🔍 [DEBUG NEURAL] Pipeline diretta: "
                          f"{domain_a.upper()} → {domain_b.upper()} "
                          f"(sticky routing bypassato)")
                    is_hybrid = True

                else:
                    stick, sticky_domain, reason, override_target = _should_sticky_route(
                        user_input, original_sem_domains, confidence, last_active_domain,
                        is_followup_llm=is_followup_llm,
                        last_pipeline_domains=last_pipeline_domains,
                    )

                    if stick:
                        print(f"📎 [STICKY] Domain Retention attivo: "
                              f"routing forzato → {sticky_domain.upper()} "
                              f"(last='{last_active_domain}', "
                              f"neural top='{original_sem_domains[0]}', conf={confidence:.2f}, "
                              f"trigger='{reason}')")
                        is_hybrid = False
                        categories_segments[sticky_domain] = [user_input]
                        # sticky → stesso dominio, no switch

                    elif override_target:
                        print(f"🔀 [SWITCH] Context switch rilevato: "
                              f"{last_active_domain.upper() if last_active_domain else 'NONE'} → "
                              f"{override_target.upper()} "
                              f"(conf={confidence:.2f})")
                        is_hybrid = False
                        domain_switched = True  # [HISTORY] dominio cambia → isola history
                        categories_segments[override_target if override_target in categories_segments
                                            else 'general'] = [user_input]

                    else:
                        target = original_sem_domains[0]
                        print(f"🔍 [DEBUG NEURAL] Dominio: {target.upper()}")
                        if target != last_active_domain and last_active_domain:
                            domain_switched = True  # [HISTORY] dominio cambia → isola history
                        categories_segments[target if target in categories_segments
                                            else 'general'] = [user_input]

            # ---------------------------------------------------------
            # [P0] GUARDIA GENERAL
            # ---------------------------------------------------------
            if is_hybrid and 'general' in (domain_a, domain_b):
                target = 'general' if domain_a == 'general' else domain_a
                print(f"🔍 [P0 GENERAL GUARD] Downgrade ibrido: GENERAL isolato. "
                      f"Routing mono-dominio → {target.upper()}")
                is_hybrid = False
                if target != last_active_domain and last_active_domain:
                    domain_switched = True
                categories_segments[target] = [user_input]

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
                    last_active_domain    = domain_b
                    last_pipeline_domains = (domain_a, domain_b)

                print("\n" + "_" * 60 + "\n")
                continue

            # ---------------------------------------------------------
            # ESECUZIONE MONO-DOMINIO
            # ---------------------------------------------------------
            has_tasks = any(segments for segments in categories_segments.values())
            if not has_tasks:
                print("⚠️  Input non processabile o archi non individuati.")
                continue

            for category, segments in categories_segments.items():
                if not segments:
                    continue

                full_query = "\n".join(segments)
                ai_agent   = agents[category]

                # [HISTORY] Isola la history se il dominio è cambiato:
                # evita che il modello del nuovo dominio "veda" risposte
                # di un dominio diverso e generi output contaminati.
                effective_history = [] if domain_switched else chat_history
                if domain_switched:
                    print(f"🔄 [HISTORY] Domain switch rilevato: history isolata per {category.upper()}")

                print(f"\n╭── 🧠 MODULO [{category.upper()}] in azione...")
                print(f"│ Modello: {ai_agent.model_name}")
                print(f"╰──────────────────────────────────────────")

                try:
                    result = ai_agent.resolve(full_query, effective_history)
                except ResourceExhaustedError as e:
                    print(f"\n⛔ OOM — Esecuzione interrotta: {e}")
                    print("\n" + "_" * 60 + "\n")
                    continue

                if _is_error(result):
                    print(result)
                else:
                    _update_history(chat_history, user_input, result, max_messages)
                    last_active_domain    = category          # aggiorna sempre, anche su 'general'
                    last_pipeline_domains = ('', '')          # reset sempre su mono-domain

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
