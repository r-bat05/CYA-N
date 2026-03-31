"""
    CYA N - AI LOCAL DISPATCHER V6.2.3
    Entry Point dell'applicazione.

    Responsabilità:
    1. Interfaccia Utente (CLI Loop).
    2. Orchestrazione tra Dispatcher e Engine AI.
    3. Gestione elegante degli errori e dell'uscita.

    Novità V6.2.3:
    - [FIX] Bug ordine pipeline semantica: ora il CASO A (arco ibrido vettoriale)
      applica la pipeline_order_matrix di config.py prima di assegnare domain_a
      e domain_b. In precedenza l'ordine era determinato dallo score coseno del
      router (sem_domains[0], sem_domains[1]), bypassando completamente la matrice
      e producendo ordini di esecuzione errati (es. coding → rights invece di
      rights → coding per query GDPR).
"""

import sys
import time
import psutil
import config
import dispatcher_request
from ai_engine import get_ai_model

# FIX: Riparato l'arco di dipendenza importando l'istanza corretta
from semantic_router import semantic_router as sem_router

# Prefissi che identificano un messaggio di errore/avviso strutturato
# restituito da generate() via return (non dallo streaming).
_ERROR_PREFIXES = ("⛔", "❌", "⚠️")


def print_banner():
    print("\n" + "=" * 60)
    print("      CYA N  |  AI LOCAL DISPATCHER V6.2.3    ")
    print("      (Coding • Math • Rights • General)      ")
    print("=" * 60 + "\n")


def main():
    print_banner()

    # Pre-istanziazione degli agenti: creati una volta sola all'avvio
    # e riutilizzati per tutta la sessione. Ogni agente mantiene un arco di
    # stato interno (necessario per la chat history).
    agents = {
        'coding':  get_ai_model('coding'),
        'math':    get_ai_model('math'),
        'rights':  get_ai_model('rights'),
        'general': get_ai_model('general')
    }

    while True:
        try:
            # 1. Input Utente
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
            # FASE 0: ROUTING SEMANTICO VETTORIALE (V6.2.4)
            # ---------------------------------------------------------
            print("\n⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale...")
            sem_domains, sem_confidence = sem_router.classify(user_input)
            
            # --- NUOVO: FILTRO DI COMPLESSITÀ VETTORIALE ---
            word_count = len(user_input.split())
            min_words = getattr(config, 'PIPELINE_SETTINGS', {}).get('min_words_for_pipeline', 8)

            # Se il router rileva 2 domini ma la query è elementare, degrada a mono-dominio
            if len(sem_domains) == 2 and word_count < min_words:
                print(f"🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: query troppo corta ({word_count} < {min_words} parole).")
                sem_domains = [sem_domains[0]] # Conserviamo solo il dominio principale
            # -----------------------------------------------

            # Recuperiamo la soglia di sicurezza
            sem_threshold = getattr(config, 'SEMANTIC_SETTINGS', {}).get('confidence_threshold', 0.06)

            is_hybrid = False
            domain_a = domain_b = ""
            categories_segments = {k: [] for k in agents.keys()}

            # CASO A: Il Semantic Router ha confermato un arco Ibrido (Multi-Dominio)
            if len(sem_domains) == 2:
                print(f"🔍 [DEBUG SEMANTICO] Arco Ibrido Vettoriale confermato (Spread = {sem_confidence:.4f}).")
                print(f"🔍 [DEBUG SEMANTICO] Domini Estratti: {sem_domains}")
                is_hybrid = True

                # [FIX V6.2.3] Applica pipeline_order_matrix come criterio primario
                # di ordinamento. In V6.2.2 l'ordine era determinato dallo score
                # coseno (sem_domains[0/1]), ignorando la semantica architetturale
                # della matrice (es. rights → coding perché il codice deve
                # implementare la norma, non il contrario).
                pair = frozenset(sem_domains)
                matrix = config.PIPELINE_SETTINGS['pipeline_order_matrix']
                if pair in matrix:
                    domain_a, domain_b = matrix[pair]
                    print(f"🔍 [DEBUG SEMANTICO] Ordine applicato da pipeline_order_matrix: "
                          f"{domain_a.upper()} → {domain_b.upper()}")
                else:
                    # Fallback: mantieni l'ordine del router (score decrescente)
                    domain_a, domain_b = sem_domains[0], sem_domains[1]
                    print(f"🔍 [DEBUG SEMANTICO] Coppia non in matrice. Ordine da score: "
                          f"{domain_a.upper()} → {domain_b.upper()}")

            # CASO B: Confidenza alta per un Mono-Dominio
            elif sem_confidence >= sem_threshold:
                print(f"🔍 [DEBUG SEMANTICO] Confidenza Alta ({sem_confidence:.4f} >= {sem_threshold}).")
                print(f"🔍 [DEBUG SEMANTICO] Dominio Estratto: {sem_domains}")
                target = sem_domains[0]
                if target in categories_segments:
                    categories_segments[target] = [user_input]
                else:
                    categories_segments['general'] = [user_input]
                    
            # CASO C: Ambiguità totale o fallimento (Fallback)
            else:
                print(f"🔍 [DEBUG SEMANTICO] Confidenza Bassa ({sem_confidence:.4f} < {sem_threshold}).")
                print("🔄 [FALLBACK] Arco Semantico Reciso. Attivazione instradamento a Keyword...")
                
                # ---------------------------------------------------------
                # FASE 1 & 2: FALLBACK KEYWORD E RILEVAMENTO IBRIDO
                # ---------------------------------------------------------
                is_hybrid, domain_a, domain_b = dispatcher_request.detect_hybrid(user_input)

                if not is_hybrid:
                    categories_segments = dispatcher_request.split_and_dispatch(user_input)

            # ---------------------------------------------------------
            # ESECUZIONE PIPELINE IBRIDA
            # ---------------------------------------------------------
            if is_hybrid:
                print(f"\n╭── 🧠 PIPELINE IBRIDA [{domain_a.upper()} → {domain_b.upper()}] in azione...")
                print(f"│ Agente A (Draft): {agents[domain_a].model_name}")
                print(f"│ Agente B (Merge): {agents[domain_b].model_name}")
                print(f"╰──────────────────────────────────────────")

                # FASE 1/3: Esecuzione silenziosa Agente A
                print(f"\n⚙️  Fase 1/3 — Elaborazione contesto [{domain_a.upper()}] in corso...")
                output_a = agents[domain_a].resolve_pipeline_a(user_input, domain_b)
                
                if not output_a or any(output_a.startswith(prefix) for prefix in _ERROR_PREFIXES):
                    print(output_a)
                    print("\n" + "_" * 60 + "\n")
                    continue

                # Arco di Sincronizzazione Attiva (Polling RAM)
                print("⚙️  Sincronizzazione — Attesa rilascio hardware...")
                target_ram = agents[domain_b].primary_ram_req
                timeout_sincronizzazione = 5.0
                inizio_attesa = time.time()
                
                while (time.time() - inizio_attesa) < timeout_sincronizzazione:
                    memoria_disponibile = psutil.virtual_memory().available
                    if memoria_disponibile >= target_ram:
                        break 
                    time.sleep(0.5)

                # FASE 2/3: Esecuzione silenziosa Agente B (Integrazione)
                print(f"⚙️  Fase 2/3 — Integrazione dominio [{domain_b.upper()}] in corso...")
                output_b = agents[domain_b].resolve_pipeline_b(user_input, output_a, domain_a)
                
                if not output_b or any(output_b.startswith(prefix) for prefix in _ERROR_PREFIXES):
                    print(output_b)
                    print("\n" + "_" * 60 + "\n")
                    continue

                # FASE 3/3: Critic Pass (Streaming visibile)
                print(f"⚙️  Fase 3/3 — Autovalutazione e sintesi [{domain_b.upper()}]...")
                print("-" * 42)
                
                result = agents[domain_b].execute_critic_pass(output_b, user_input)
                if result and any(result.startswith(prefix) for prefix in _ERROR_PREFIXES):
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

                result = ai_agent.resolve(full_query)

                if result and any(result.startswith(prefix) for prefix in _ERROR_PREFIXES):
                    print(result)

                print("\n" + "_" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n\n🛑 Interruzione manuale rilevata.")
            print("Chiusura sicura degli archi di sistema...")
            sys.exit(0)

        except Exception as e:
            print(f"\n❌ ERRORE IMPREVISTO: {e}")
            print("Consiglio: Verifica che l'arco di comunicazione con Ollama (o il modello vettoriale) sia attivo")


if __name__ == "__main__":
    main()
