"""
    CYA N - AI LOCAL DISPATCHER V6.7.3
    Entry Point dell'applicazione.

    Novita' V6.7.3:
    - [BUG1] _ERROR_PREFIXES: "ATTENZIONE:" sostituito con "__SYS_WARN__:" per
      eliminare il falso positivo che spezzava la Chat History quando i modelli
      iniziavano legittimamente una risposta con "ATTENZIONE:".
    - [REFACTOR] Eliminato il layer di astrazione semantic_router.py (guscio vuoto).
      classify_knn importata direttamente da vector_store. Nessun cambio funzionale.

    Novita' V6.7.2:
    - [BUG2] Rimosso Override A da _should_sticky_route(): era dead code.

    Novita' V6.7.0:
    - [STICKY] Implementazione Domain Retention (Sticky Routing).

    Novita' V6.6.0:
    - [CHAT] chat_history: lista globale di sessione (sliding window).
    - [CHAT] Comando '/reset' per svuotare history.

    Novita' V6.5.0:
    - [P0] GENERAL isolation: downgrade ibrido se un dominio e' 'general'.
    - [P4] timeout_sincronizzazione letto da config.PIPELINE_SETTINGS.
"""

import sys
import time
import psutil
import config
import dispatcher_request
from ai_engine import get_ai_model, ResourceExhaustedError
# [REFACTOR] Import diretto da vector_store: semantic_router.py eliminato.
from vector_store import classify_knn
from vector_store import initialize_store

# [BUG1 FIX] "__SYS_WARN__:" sostituisce "ATTENZIONE:" per evitare falsi positivi:
# i modelli usano legittimamente "ATTENZIONE:" in risposte valide (es. avvisi di sicurezza),
# causando il blocco silenzioso di _update_history() e la corruzione dello stato sticky.
_ERROR_PREFIXES   = ("Errore Ollama:", "Errore Generico:", "__SYS_WARN__:")
_TECHNICAL_DOMAINS = {'coding', 'math', 'rights'}


def print_banner():
    print("\n" + "=" * 60)
    print("      CYA N  |  AI LOCAL DISPATCHER V6.7.3    ")
    print("      (Coding • Math • Rights • General)      ")
    print("=" * 60 + "\n")


def _update_history(history: list, user_input: str, response: str, max_messages: int):
    """
    [CHAT] Aggiunge il turno corrente alla history e applica la sliding window.
    """
    history.append({'role': 'user',      'content': user_input})
    history.append({'role': 'assistant', 'content': response})
    if len(history) > max_messages:
        del history[:len(history) - max_messages]


def _is_error(result: str) -> bool:
    """Controlla se il risultato e' un messaggio d'errore di sistema."""
    return not result or any(result.startswith(p) for p in _ERROR_PREFIXES)


def _should_sticky_route(
    query: str,
    sem_domains: list,
    sem_confidence: float,
    last_domain: str
) -> tuple:
    """
    [STICKY V3 / BUG2 FIX] Domain Retention con singolo Override.

    Override unico: k-NN con confidenza >= tech_switch_min su dominio tecnico
    diverso dall'ultimo attivo → context switch (sticky non applicato).

    Innesco sticky: SOLO query brevi (follow-up pattern).
    """
    if not last_domain or last_domain not in _TECHNICAL_DOMAINS:
        return False, last_domain

    tech_switch_min = config.SYSTEM_SETTINGS.get('sticky_tech_switch_min', 0.45)
    short_threshold = config.SYSTEM_SETTINGS.get('sticky_short_words', 7)

    top_domain = sem_domains[0] if sem_domains else 'general'
    is_short   = len(query.split()) < short_threshold

    # Override: confidenza sufficiente su un dominio tecnico diverso → context switch
    if (top_domain in _TECHNICAL_DOMAINS
            and top_domain != last_domain
            and sem_confidence >= tech_switch_min):
        return False, last_domain

    # Innesco sticky: solo query brevi (pattern follow-up)
    if is_short:
        return True, last_domain

    return False, last_domain


def main():
    print_banner()

    print("⚙️  Inizializzazione Vector Store (Distance-Weighted k-NN su LanceDB)...")
    store_ok = initialize_store()
    if not store_ok:
        print("⚠️  VectorStore non disponibile. Il sistema usera' il fallback a keyword per tutto il routing.")

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

            # [CHAT+STICKY] Comando reset: azzera history e stato sticky
            if user_input.lower() in ['/reset', '/clear']:
                chat_history.clear()
                last_active_domain = ''
                print("🔄 Chat history e dominio attivo azzerati.\n")
                continue

            # ---------------------------------------------------------
            # FASE 0: ROUTING SEMANTICO VETTORIALE
            # ---------------------------------------------------------
            print("\n⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...")
            # [REFACTOR] Chiamata diretta a classify_knn (ex sem_router.classify)
            sem_domains, sem_confidence, sem_ok = classify_knn(user_input)

            is_hybrid  = False
            domain_a   = domain_b = ""
            categories_segments = {k: [] for k in agents.keys()}

            # =============================================================
            # CASO FALLBACK: servizio embedding non disponibile
            # =============================================================
            if not sem_ok:
                print("⚠️  [FALLBACK] Servizio embedding non disponibile.")
                print("🔄 [FALLBACK] Attivazione instradamento a Keyword come emergenza...")

                is_hybrid, domain_a, domain_b = dispatcher_request.detect_hybrid(user_input)
                if not is_hybrid:
                    winning_domain = dispatcher_request.classify_segment(user_input)
                    if winning_domain == 'general':
                        stick, sticky_domain = _should_sticky_route(
                            user_input, ['general'], 0.0, last_active_domain
                        )
                        if stick:
                            print(f"📎 [STICKY] Keyword fallback su 'general'. "
                                  f"Domain Retention → {sticky_domain.upper()}")
                            winning_domain = sticky_domain

                    categories_segments[winning_domain if winning_domain in categories_segments
                                        else 'general'] = [user_input]

            else:
                word_count = len(user_input.split())
                min_words  = config.PIPELINE_SETTINGS.get('min_words_for_pipeline', 8)

                if len(sem_domains) == 2 and word_count < min_words:
                    print(f"🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: "
                          f"query troppo corta ({word_count} < {min_words} parole).")
                    sem_domains = [sem_domains[0]]

                print(f"🔍 [DEBUG SEMANTICO] Domini: {sem_domains}  |  "
                      f"Confidence k-NN: {sem_confidence:.2f}")

                # ---------------------------------------------------------
                # [STICKY] Valutazione Domain Retention
                # ---------------------------------------------------------
                stick, sticky_domain = _should_sticky_route(
                    user_input, sem_domains, sem_confidence, last_active_domain
                )

                if stick:
                    tech_switch_min = config.SYSTEM_SETTINGS.get('sticky_tech_switch_min', 0.45)
                    print(f"📎 [STICKY] Domain Retention attivo: "
                          f"routing forzato → {sticky_domain.upper()} "
                          f"(last='{last_active_domain}', "
                          f"k-NN top='{sem_domains[0]}', conf={sem_confidence:.2f}, "
                          f"soglia_switch={tech_switch_min})")
                    is_hybrid = False
                    categories_segments[sticky_domain] = [user_input]

                elif len(sem_domains) == 2:
                    print(f"🔍 [DEBUG SEMANTICO] Arco Ibrido confermato "
                          f"(min_score={config.SEMANTIC_SETTINGS.get('knn_min_score', 3.0):.2f}, "
                          f"min_vote_ratio={config.SEMANTIC_SETTINGS.get('knn_min_vote_ratio', 0.30)}).")
                    is_hybrid = True

                    pair   = frozenset(sem_domains)
                    matrix = config.PIPELINE_SETTINGS['pipeline_order_matrix']
                    if pair in matrix:
                        domain_a, domain_b = matrix[pair]
                        print(f"🔍 [DEBUG SEMANTICO] Ordine da pipeline_order_matrix: "
                              f"{domain_a.upper()} → {domain_b.upper()}")
                    else:
                        domain_a, domain_b = sem_domains[0], sem_domains[1]
                        print(f"🔍 [DEBUG SEMANTICO] Coppia non in matrice. "
                              f"Ordine da score k-NN: {domain_a.upper()} → {domain_b.upper()}")

                else:
                    target = sem_domains[0]
                    print(f"🔍 [DEBUG SEMANTICO] Dominio: {target.upper()}")
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
                categories_segments[target] = [user_input]

            # ---------------------------------------------------------
            # ESECUZIONE PIPELINE IBRIDA
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

                # Sincronizzazione RAM [P4]
                print("⚙️  Sincronizzazione — Attendendo lo scaricamento del modello precedente...")
                target_ram               = agents[domain_b].primary_ram_req
                timeout_sincronizzazione = config.PIPELINE_SETTINGS.get('ram_sync_timeout', 20.0)
                inizio_attesa            = time.time()

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
