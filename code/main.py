"""
    CYA N - AI LOCAL DISPATCHER V7.0.0
    Entry Point dell'applicazione.

    Novità V7.0.0:
    - [NEURAL] Sostituito routing k-NN (vector_store.py / LanceDB) con
      neural_classifier.py: MLP 7 classi su embedding nomic-embed-text frozen.
    - [NEURAL] Pipeline detection integrata nel class_id del classifier:
      classi 4-6 → pipeline diretta, elimina frozenset e pipeline_order_matrix.
    - [NEURAL] is_pipeline_candidate=True bypassa _should_sticky_route:
      conf >= threshold_pipeline è il segnale autoritativo per la pipeline.
    - [NEURAL] Pipeline declassata (query troppo corta) torna al path sticky
      con original_sem_domains=[domain_a, domain_b] per override detection.
    - [CLEANUP] Rimossi classify_knn, initialize_store, pipeline_order_matrix.
"""

import re as _re
import sys
import time
import psutil
import config
import dispatcher_request
from ai_engine import get_ai_model, ResourceExhaustedError
from neural_classifier import predict as neural_predict, PIPELINE_CLASSES, DOMAIN_NAMES
from dispatcher_request import keyword_loader, _count_hits

_ERROR_PREFIXES    = ("Errore Ollama:", "Errore Generico:", "__SYS_WARN__:")
_TECHNICAL_DOMAINS = {'coding', 'math', 'rights'}
# Mapping class_id mono-domain → stringa dominio
_CLASS_TO_DOMAIN   = {0: 'coding', 1: 'math', 2: 'rights', 3: 'general'}


def print_banner():
    print("\n" + "=" * 60)
    print("      CYA N  |  AI LOCAL DISPATCHER V7.0.0    ")
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
    """
    Restituisce True se la query contiene almeno una keyword del dominio dato.
    """
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
    last_domain: str
) -> tuple:
    """
    Domain Retention V7.0 — ordine di valutazione:
      1. Override (context switch) — soglia differenziata per lunghezza query.
      2. Pattern espliciti — solo se nessun override ha scattato.
      3. Trigger query corta — con eccezione solo per query non cortissime.
      4. Trigger weak-general.

    Returns: (should_stick, sticky_domain, reason, override_target)

    NOTA: questa funzione NON viene chiamata per pipeline candidate confermate
    (is_pipeline_candidate=True). Il neural classifier con conf >= threshold_pipeline
    è il segnale autoritativo; la pipeline viene eseguita direttamente.
    """
    if not last_domain or last_domain not in _TECHNICAL_DOMAINS:
        return False, last_domain, '', None

    tech_switch_min    = config.SYSTEM_SETTINGS.get('sticky_tech_switch_min',    0.38)
    short_override_min = config.SYSTEM_SETTINGS.get('sticky_short_override_min', 0.65)
    short_threshold    = config.SYSTEM_SETTINGS.get('sticky_short_words',        10)
    weak_gen_conf      = config.SYSTEM_SETTINGS.get('sticky_weak_general_conf',  0.65)
    followup_triggers  = config.SYSTEM_SETTINGS.get('sticky_followup_triggers',  [])

    word_count  = len(query.split())
    top_domain  = sem_domains[0] if sem_domains else 'general'
    is_short    = word_count < short_threshold
    query_lower = query.lower()

    # --- 1. Override: context switch verso dominio tecnico diverso ---
    override_threshold = short_override_min if is_short else tech_switch_min
    switching_domains  = [
        d for d in sem_domains
        if d in _TECHNICAL_DOMAINS and d != last_domain
    ]
    if switching_domains and sem_confidence >= override_threshold:
        override_target = top_domain if top_domain in switching_domains else switching_domains[0]
        return False, last_domain, '', override_target

    # --- 2. Pattern espliciti ---
    for trigger in followup_triggers:
        if trigger in query_lower:
            return True, last_domain, f'pattern_match("{trigger}")', None

    # --- 3. Trigger query corta ---
    if is_short:
        very_short = word_count < 6
        if (not very_short
                and top_domain == 'general'
                and sem_confidence < weak_gen_conf
                and not _has_domain_keywords(query, last_domain)):
            return False, last_domain, 'short_no_kw_general', None
        return True, last_domain, 'query_corta', None

    # --- 4. Trigger weak-general ---
    if top_domain == 'general' and sem_confidence < weak_gen_conf:
        if _has_domain_keywords(query, last_domain):
            return True, last_domain, f'weak_general(conf={sem_confidence:.2f}<{weak_gen_conf})', None
        return False, last_domain, '', None

    return False, last_domain, '', None


def main():
    print_banner()

    agents = {
        'coding':  get_ai_model('coding'),
        'math':    get_ai_model('math'),
        'rights':  get_ai_model('rights'),
        'general': get_ai_model('general')
    }

    # [CHAT] Stato globale di sessione
    chat_history: list = []
    max_history_turns  = config.SYSTEM_SETTINGS.get('max_history_turns', 3)
    max_messages       = max_history_turns * 2

    # [STICKY] Dominio primario dell'ultimo turno valido (solo domini tecnici)
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

            # [CHAT+STICKY] Comando reset
            if user_input.lower() in ['/reset', '/clear']:
                chat_history.clear()
                last_active_domain = ''
                print("🔄 Chat history e dominio attivo azzerati.\n")
                continue

            # ---------------------------------------------------------
            # FASE 0: ROUTING NEURALE
            # ---------------------------------------------------------
            print("\n⚙️  Fase 0 — Classificazione Neurale (MLP su embedding frozen)...")
            class_id, confidence = neural_predict(user_input, last_active_domain)

            is_hybrid  = False
            domain_a   = domain_b = ""
            categories_segments = {k: [] for k in agents.keys()}

            # =============================================================
            # CASO FALLBACK: classifier non disponibile (model.pt assente
            # o embedding Ollama irraggiungibile)
            # =============================================================
            if class_id == -1:
                print("⚠️  [FALLBACK] Neural classifier non disponibile.")
                print("🔄 [FALLBACK] Attivazione instradamento a Keyword come emergenza...")

                is_hybrid, domain_a, domain_b = dispatcher_request.detect_hybrid(user_input)
                if not is_hybrid:
                    winning_domain = dispatcher_request.classify_segment(user_input)
                    if winning_domain == 'general':
                        # Nel fallback non conosciamo la confidenza reale:
                        # passiamo 1.0 per disabilitare il weak-general trigger.
                        # Lo sticky si affida solo a pattern trigger e lunghezza.
                        stick, sticky_domain, reason, override_target = _should_sticky_route(
                            user_input, ['general'], 1.0, last_active_domain
                        )
                        if stick:
                            print(f"📎 [STICKY] Keyword fallback su 'general'. "
                                  f"Domain Retention → {sticky_domain.upper()} [{reason}]")
                            winning_domain = sticky_domain
                        elif override_target:
                            winning_domain = override_target

                    categories_segments[winning_domain if winning_domain in categories_segments
                                        else 'general'] = [user_input]

            # =============================================================
            # ROUTING NEURALE VALIDO
            # =============================================================
            else:
                word_count = len(user_input.split())
                min_words  = config.PIPELINE_SETTINGS.get('min_words_for_pipeline', 12)

                # ----------------------------------------------------------
                # Determina domini e candidatura pipeline dalla classe predetta.
                #
                # original_sem_domains è passato a _should_sticky_route e serve
                # per l'override detection anche quando la pipeline è declassata:
                #   - class pipeline   → [domain_a, domain_b]  (entrambi visibili)
                #   - class mono       → [top_domain]
                # ----------------------------------------------------------
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
                    # original_sem_domains resta [domain_a, domain_b] per override

                print(f"🔍 [DEBUG NEURAL] Classe={DOMAIN_NAMES[class_id]} | "
                      f"Confidence={confidence:.2f} | "
                      f"Pipeline={'CONFERMATA' if is_pipeline_candidate else 'NO'}")

                # ----------------------------------------------------------
                # [NEURAL PIPELINE] Pipeline confermata dal classifier:
                # la confidenza >= threshold_pipeline è il segnale autoritativo.
                # Si bypassa _should_sticky_route per evitare che l'override
                # degradi erroneamente la pipeline a mono-domain (es. il caso
                # "scrivi codice Python per Pitagora" con last_domain='math'
                # che nel k-NN veniva dirottato a CODING anziché MATH→CODING).
                # ----------------------------------------------------------
                if is_pipeline_candidate:
                    print(f"🔍 [DEBUG NEURAL] Pipeline diretta: "
                          f"{domain_a.upper()} → {domain_b.upper()} "
                          f"(sticky routing bypassato)")
                    is_hybrid = True

                # ----------------------------------------------------------
                # [STICKY] Valutazione Domain Retention
                # Applicata solo per mono-domain e pipeline declassate.
                # ----------------------------------------------------------
                else:
                    stick, sticky_domain, reason, override_target = _should_sticky_route(
                        user_input, original_sem_domains, confidence, last_active_domain
                    )

                    if stick:
                        print(f"📎 [STICKY] Domain Retention attivo: "
                              f"routing forzato → {sticky_domain.upper()} "
                              f"(last='{last_active_domain}', "
                              f"neural top='{original_sem_domains[0]}', conf={confidence:.2f}, "
                              f"trigger='{reason}')")
                        is_hybrid = False
                        categories_segments[sticky_domain] = [user_input]

                    elif override_target:
                        # Context switch esplicito verso dominio tecnico rilevato
                        print(f"🔀 [SWITCH] Context switch rilevato: "
                              f"{last_active_domain.upper() if last_active_domain else 'NONE'} → "
                              f"{override_target.upper()} "
                              f"(conf={confidence:.2f})")
                        is_hybrid = False
                        categories_segments[override_target if override_target in categories_segments
                                            else 'general'] = [user_input]

                    else:
                        target = original_sem_domains[0]
                        print(f"🔍 [DEBUG NEURAL] Dominio: {target.upper()}")
                        categories_segments[target if target in categories_segments
                                            else 'general'] = [user_input]

            # ---------------------------------------------------------
            # [P0] GUARDIA GENERAL
            # Rilevante principalmente per il path di fallback keyword,
            # dove detect_hybrid() può restituire 'general' come dominio.
            # ---------------------------------------------------------
            if is_hybrid and 'general' in (domain_a, domain_b):
                target = 'general' if domain_a == 'general' else domain_a
                print(f"🔍 [P0 GENERAL GUARD] Downgrade ibrido: GENERAL isolato. "
                      f"Routing mono-dominio → {target.upper()}")
                is_hybrid = False
                categories_segments[target] = [user_input]

            # ---------------------------------------------------------
            # ESECUZIONE PIPELINE IBRIDA
            # domain_a e domain_b sono già settati da PIPELINE_CLASSES[class_id]
            # (routing neurale) o da detect_hybrid() (fallback keyword).
            # ---------------------------------------------------------
            if is_hybrid:
                print(f"\n╭── 🧠 PIPELINE IBRIDA [{domain_a.upper()} → {domain_b.upper()}] in azione...")
                print(f"│ Agente A (Draft): {agents[domain_a].model_name}")
                print(f"│ Agente B (Merge): {agents[domain_b].model_name}")
                print(f"╰──────────────────────────────────────────")

                # FASE 1/3: Agente A
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

                # Sincronizzazione RAM
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

                # FASE 2/3: Agente B
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

                # FASE 3/3: Critic Pass
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
            has_tasks = any(segments for segments in categories_segments.values())
            if not has_tasks:
                print("⚠️  Input non processabile o archi non individuati.")
                continue

            for category, segments in categories_segments.items():
                if not segments:
                    continue

                full_query = "\n".join(segments)
                ai_agent   = agents[category]

                print(f"\n╭── 🧠 MODULO [{category.upper()}] in azione...")
                print(f"│ Modello: {ai_agent.model_name}")
                print(f"╰──────────────────────────────────────────")

                try:
                    result = ai_agent.resolve(full_query, chat_history)
                except ResourceExhaustedError as e:
                    print(f"\n⛔ OOM — Esecuzione interrotta: {e}")
                    print("\n" + "_" * 60 + "\n")
                    continue

                if _is_error(result):
                    print(result)
                else:
                    _update_history(chat_history, user_input, result, max_messages)
                    if category in _TECHNICAL_DOMAINS:
                        last_active_domain = category

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
