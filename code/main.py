"""
    CYA N - AI LOCAL DISPATCHER V6.1
    Entry Point dell'applicazione.

    Responsabilità:
    1. Interfaccia Utente (CLI Loop).
    2. Orchestrazione tra Dispatcher e Engine AI.
    3. Gestione elegante degli errori e dell'uscita.

    Novità V6.1:
    - [FIX] Implementato Arco di Sincronizzazione Attiva (Polling) tra Fase 1 e 2 
      della pipeline per consentire il rilascio asincrono della VRAM.
    - [FIX] Aggiornata la firma di execute_critic_pass per iniettare l'arco 
      informativo originale (Vulnerabilità B).
"""

import sys
import time
import psutil
import config
import dispatcher_request
from ai_engine import get_ai_model

# Prefissi che identificano un messaggio di errore/avviso strutturato
# restituito da generate() via return (non dallo streaming).
_ERROR_PREFIXES = ("⛔", "❌", "⚠️")


def print_banner():
    print("\n" + "=" * 60)
    print("      CYA N  |  AI LOCAL DISPATCHER V6.1      ")
    print("      (Coding • Math • Rights • General)      ")
    print("=" * 60 + "\n")


def main():
    print_banner()

    # Pre-istanziazione degli agenti: creati una volta sola all'avvio
    # e riutilizzati per tutta la sessione. Ogni agente mantiene un arco di
    # stato interno (necessario per la chat history del prossimo sprint).
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
            # FASE 1: RILEVAMENTO QUERY IBRIDA (PIPELINE V6.0+)
            # ---------------------------------------------------------
            is_hybrid, domain_a, domain_b = dispatcher_request.detect_hybrid(user_input)

            if is_hybrid:
                print(f"\n╭── 🧠 PIPELINE IBRIDA [{domain_a.upper()} → {domain_b.upper()}] in azione...")
                print(f"│ Agente A (Draft): {agents[domain_a].model_name}")
                print(f"│ Agente B (Merge): {agents[domain_b].model_name}")
                print(f"╰──────────────────────────────────────────")

                # FASE 1/3: Esecuzione silenziosa Agente A
                print(f"\n⚙️  Fase 1/3 — Elaborazione contesto [{domain_a.upper()}] in corso...")
                output_a = agents[domain_a].resolve_pipeline_a(user_input, domain_b)
                
                # Se l'output_a è un messaggio d'errore o blocco RAM, recidi l'arco della pipeline
                if not output_a or any(output_a.startswith(prefix) for prefix in _ERROR_PREFIXES):
                    print(output_a)
                    print("\n" + "_" * 60 + "\n")
                    continue

                # --- ARCO DI SINCRONIZZAZIONE ATTIVA (Fix Vulnerabilità A) ---
                print("⚙️  Sincronizzazione — Attesa rilascio hardware...")
                # Recuperiamo la soglia di RAM richiesta dall'Agente B
                target_ram = agents[domain_b].primary_ram_req
                timeout_sincronizzazione = 5.0
                inizio_attesa = time.time()
                
                # Ciclo di polling per dare tempo al demone Ollama di scaricare l'Agente A
                while (time.time() - inizio_attesa) < timeout_sincronizzazione:
                    memoria_disponibile = psutil.virtual_memory().available
                    if memoria_disponibile >= target_ram:
                        break # Arco hardware stabilizzato, proseguiamo
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
                
                # Fix Vulnerabilità B: iniettiamo l'arco informativo originale (user_input)
                result = agents[domain_b].execute_critic_pass(output_b, user_input)
                if result and any(result.startswith(prefix) for prefix in _ERROR_PREFIXES):
                    print(result)

                print("\n" + "_" * 60 + "\n")
                continue

            # ---------------------------------------------------------
            # FASE 2: ANALISI E SMISTAMENTO (MONO-DOMINIO CLASSSICO)
            # ---------------------------------------------------------
            categories_segments = dispatcher_request.split_and_dispatch(user_input)

            has_tasks = any(segments for segments in categories_segments.values())
            if not has_tasks:
                print("⚠️  Input non processabile.")
                continue

            # ---------------------------------------------------------
            # FASE 3: ESECUZIONE (MONO-DOMINIO)
            # ---------------------------------------------------------
            for category, segments in categories_segments.items():
                if not segments:
                    continue

                full_query = "\n".join(segments)
                ai_agent   = agents[category]

                print(f"\n╭── 🧠 MODULO [{category.upper()}] in azione...")
                print(f"│ Modello: {ai_agent.model_name}")
                print(f"╰──────────────────────────────────────────")

                # generate() usa due archi di output distinti:
                #   - Streaming (chunk per chunk) → stampa diretta a schermo.
                #   - Return value               → usato SOLO per errori strutturati.
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
            print("Consiglio: Verifica che l'arco di comunicazione con Ollama sia attivo")


if __name__ == "__main__":
    main()