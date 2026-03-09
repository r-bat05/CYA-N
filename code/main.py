"""
    CYA N - AI LOCAL DISPATCHER V5.2
    Entry Point dell'applicazione.

    Responsabilità:
    1. Interfaccia Utente (CLI Loop).
    2. Orchestrazione tra Dispatcher e Engine AI.
    3. Gestione elegante degli errori e dell'uscita.

    Novità V5.2:
    - Gli agenti AI vengono istanziati una sola volta all'avvio (fuori dal loop)
      e riutilizzati per tutta la durata della sessione. Questo prepara
      l'architettura per l'integrazione della chat history, che richiede
      oggetti persistenti tra un turno e l'altro.
"""

import sys
import dispatcher_request
from ai_engine import get_ai_model

# Prefissi che identificano un messaggio di errore/avviso strutturato
# restituito da generate() via return (non dallo streaming).
_ERROR_PREFIXES = ("⛔", "❌", "⚠️")


def print_banner():
    print("\n" + "=" * 60)
    print("      CYA N  |  AI LOCAL DISPATCHER V5.2      ")
    print("      (Coding • Math • Rights • General)      ")
    print("=" * 60 + "\n")


def main():
    print_banner()

    # Pre-istanziazione degli agenti: creati una volta sola all'avvio
    # e riutilizzati per tutta la sessione. Ogni agente mantiene il proprio
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
            # FASE 1: ANALISI E SMISTAMENTO
            # ---------------------------------------------------------
            categories_segments = dispatcher_request.split_and_dispatch(user_input)

            has_tasks = any(segments for segments in categories_segments.values())
            if not has_tasks:
                print("⚠️  Input non processabile.")
                continue

            # ---------------------------------------------------------
            # FASE 2: ESECUZIONE
            # ---------------------------------------------------------
            for category, segments in categories_segments.items():
                if not segments:
                    continue

                full_query = "\n".join(segments)
                ai_agent   = agents[category]

                print(f"\n╭── 🧠 MODULO [{category.upper()}] in azione...")
                print(f"│ Modello: {ai_agent.model_name}")
                print(f"╰──────────────────────────────────────────")

                # generate() usa due canali di output distinti:
                #   - Streaming (chunk per chunk) → stampa diretta a schermo.
                #   - Return value               → usato SOLO per errori strutturati.
                # Mostriamo il return value solo se contiene un segnale di errore,
                # per evitare la doppia stampa dell'output normale.
                result = ai_agent.resolve(full_query)

                if result and any(result.startswith(prefix) for prefix in _ERROR_PREFIXES):
                    print(result)

                print("\n" + "_" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n\n🛑 Interruzione manuale rilevata.")
            print("Chiusura pulita del sistema...")
            sys.exit(0)

        except Exception as e:
            print(f"\n❌ ERRORE IMPREVISTO: {e}")
            print("Consiglio: Verifica che Ollama sia attivo")


if __name__ == "__main__":
    main()