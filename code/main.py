"""
    CYA N - AI LOCAL DISPATCHER V5.0
    Entry Point dell'applicazione.
    
    Responsabilità:
    1. Interfaccia Utente (CLI Loop).
    2. Orchestrazione tra Dispatcher e Engine AI.
    3. Gestione elegante degli errori e dell'uscita.
"""

import sys
import dispatcher_request
from ai_engine import get_ai_model

def print_banner():
    print("\n" + "="*60)
    print("      CYA N  |  AI LOCAL DISPATCHER V5.0      ")
    print("      (Coding • Math • Rights • General)      ")
    print("="*60 + "\n")

def main():
    print_banner()

    while True:
        try:
            # 1. Input Utente
            try:
                user_input = input("Inserisci la tua richiesta (o 'exit' per uscire): ").strip()
            except EOFError:
                # Gestisce il caso di CTRL+D o fine input
                break

            # Condizioni di uscita
            if not user_input:
                print("⚠️  Richiesta vuota. Riprova.")
                continue
                
            if user_input.lower() in ['exit', 'esci', 'quit', 'q']:
                print("\nChiusura sessione. A presto! 👋")
                break

            # ---------------------------------------------------------
            # FASE 1: ANALISI E SMISTAMENTO
            # ---------------------------------------------------------
            # Il dispatcher spezza la richiesta in sottotask (es. una parte math, una coding)
            categories_segments = dispatcher_request.split_and_dispatch(user_input)
            
            # Verifica se abbiamo trovato qualcosa
            has_tasks = any(segments for segments in categories_segments.values())
            
            if not has_tasks:
                # Fallback estremo se il dispatcher ritorna dizionario vuoto (raro)
                print("⚠️  Input non processabile.")
                continue

            # ---------------------------------------------------------
            # FASE 2: ESECUZIONE
            # ---------------------------------------------------------
            for category, segments in categories_segments.items():
                if segments:
                    # Ricostruisce la query per quella specifica categoria
                    full_query = "\n".join(segments)
                    
                    # Factory: Ottiene l'agente configurato per questa categoria
                    ai_agent = get_ai_model(category)
                    
                    if ai_agent:
                        # Header visivo per far capire all'utente chi sta rispondendo
                        print(f"\n╭── 🧠 MODULO [{category.upper()}] in azione...")
                        print(f"│ Modello: {ai_agent.model_name}")
                        print(f"╰──────────────────────────────────────────")
                        
                        # Esecuzione (gestisce spinner e streaming internamente)
                        ai_agent.resolve(full_query)
                        
                        print("\n" + "_"*60 + "\n")
                    else:
                        print(f"\n❌ Errore Configurazione: Nessun agente per '{category}'\n")

        except KeyboardInterrupt:
            print("\n\n🛑 Interruzione manuale rilevata.")
            print("Chiusura pulita del sistema...")
            sys.exit(0)
            
        except Exception as e:
            print(f"\n❌ ERRORE IMPREVISTO: {e}")
            print("Consiglio: Verifica che Ollama sia attivo")

if __name__ == "__main__":
    main()