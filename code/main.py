"""
    CYA N - AI LOCAL DISPATCHER V6.3.1
    Entry Point dell'applicazione.

    Novità V6.3.1 — Gestione OOM tramite eccezione tipizzata:
    - [FIX] Rimosso l'anti-pattern del check testuale startswith(_ERROR_PREFIXES)
      per le chiamate resolve, resolve_pipeline_a, resolve_pipeline_b e
      execute_critic_pass. Tutte le chiamate agli agenti sono ora avvolte in
      un blocco try/except ResourceExhaustedError importato da ai_engine.
      L'intercettazione è tipizzata: nessuna stringa di errore può "bucare"
      il filtro per mancanza di emoji prefix.
    - [INVARIATO] Il check _ERROR_PREFIXES rimane attivo solo dove ha senso:
      sugli errori Ollama (ResponseError, eccezione generica) che generate()
      restituisce ancora via return testuale.

    Novità V6.3.0 — VectorStore k-NN:
    - [FEATURE] Aggiunta chiamata a initialize_store() all'avvio, prima del loop.
    - [UPDATE] Import di initialize_store da vector_store.
    - [UPDATE] Label debug aggiornate da "Margin/spread" a "Confidence/voti k-NN".
    - [INVARIATO] Tutta la logica di routing, pipeline ibrida e mono-dominio
      è identica alla V6.2.4.

    Novità V6.2.4 — Routing Semantico come Autorità Primaria:
    - [BREAKING] classify() del SemanticRouter restituisce ora 3 valori:
      (domains, confidence, sem_ok).
    - [FIX ARCHITETTURALE] Rimosso il gate confidence_threshold.
"""

import sys
import time
import psutil
import config
import dispatcher_request
from ai_engine import get_ai_model, ResourceExhaustedError
from semantic_router import semantic_router as sem_router
from vector_store import initialize_store

# Prefissi per errori Ollama (ResponseError, connessione) restituiti via return
# testuale da generate(). NON usati per il check OOM (ora gestito da eccezione).
_ERROR_PREFIXES = ("Errore Ollama:", "Errore Generico:", "ATTENZIONE:")


def print_banner():
    print("\n" + "=" * 60)
    print("      CYA N  |  AI LOCAL DISPATCHER V6.3.1    ")
    print("      (Coding • Math • Rights • General)      ")
    print("=" * 60 + "\n")


def main():
    print_banner()

    print("⚙️  Inizializzazione Vector Store (k-NN su LanceDB)...")
    store_ok = initialize_store()
    if not store_ok:
        print("⚠️  VectorStore non disponibile. Il sistema userà il fallback a keyword per tutto il routing.")

    agents = {
        'coding':  get_ai_model('coding'),
        'math':    get_ai_model('math'),
        'rights':  get_ai_model('rights'),
        'general': get_ai_model('general')
    }

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

            # ---------------------------------------------------------
            # FASE 0: ROUTING SEMANTICO VETTORIALE (k-NN)
            # ---------------------------------------------------------
            print("\n⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (k-NN)...")
            sem_domains, sem_confidence, sem_ok = sem_router.classify(user_input)

            is_hybrid = False
            domain_a = domain_b = ""
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
                    if winning_domain in categories_segments:
                        categories_segments[winning_domain] = [user_input]
                    else:
                        categories_segments['general'] = [user_input]

            else:
                word_count = len(user_input.split())
                min_words  = config.PIPELINE_SETTINGS.get('min_words_for_pipeline', 8)

                if len(sem_domains) == 2 and word_count < min_words:
                    print(f"🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: "
                          f"query troppo corta ({word_count} < {min_words} parole).")
                    sem_domains = [sem_domains[0]]

                print(f"🔍 [DEBUG SEMANTICO] Domini: {sem_domains}  |  "
                      f"Confidence k-NN: {sem_confidence:.2f}")

                if len(sem_domains) == 2:
                    print(f"🔍 [DEBUG SEMANTICO] Arco Ibrido confermato "
                          f"(min_abs_votes={config.SEMANTIC_SETTINGS.get('knn_min_abs_votes', 3)}, "
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
                              f"Ordine da voti k-NN: {domain_a.upper()} → {domain_b.upper()}")

                else:
                    target = sem_domains[0]
                    print(f"🔍 [DEBUG SEMANTICO] Dominio: {target.upper()}")
                    if target in categories_segments:
                        categories_segments[target] = [user_input]
                    else:
                        categories_segments['general'] = [user_input]

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
                    output_a = agents[domain_a].resolve_pipeline_a(user_input, domain_b)
                except ResourceExhaustedError as e:
                    print(f"\n⛔ OOM — Pipeline interrotta in Fase 1/3: {e}")
                    print("\n" + "_" * 60 + "\n")
                    continue

                if not output_a or any(output_a.startswith(p) for p in _ERROR_PREFIXES):
                    print(output_a)
                    print("\n" + "_" * 60 + "\n")
                    continue

                # Sincronizzazione RAM
                print("⚙️  Sincronizzazione — Attendendo lo scaricamento del modello precedente...")
                target_ram               = agents[domain_b].primary_ram_req
                timeout_sincronizzazione = 20.0
                inizio_attesa            = time.time()

                while (time.time() - inizio_attesa) < timeout_sincronizzazione:
                    if psutil.virtual_memory().available >= target_ram:
                        break
                    time.sleep(0.5)
                else:
                    print("⚠️  Timeout sincronizzazione RAM: procedo comunque.")

                # FASE 2/3: Agente B (Integrazione)
                print(f"⚙️  Fase 2/3 — Integrazione dominio [{domain_b.upper()}] in corso...")
                try:
                    output_b = agents[domain_b].resolve_pipeline_b(user_input, output_a, domain_a)
                except ResourceExhaustedError as e:
                    print(f"\n⛔ OOM — Pipeline interrotta in Fase 2/3: {e}")
                    print("\n" + "_" * 60 + "\n")
                    continue

                if not output_b or any(output_b.startswith(p) for p in _ERROR_PREFIXES):
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

                if result and any(result.startswith(p) for p in _ERROR_PREFIXES):
                    print(result)

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
                    result = ai_agent.resolve(full_query)
                except ResourceExhaustedError as e:
                    print(f"\n⛔ OOM — Esecuzione interrotta: {e}")
                    print("\n" + "_" * 60 + "\n")
                    continue

                if result and any(result.startswith(p) for p in _ERROR_PREFIXES):
                    print(result)

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
