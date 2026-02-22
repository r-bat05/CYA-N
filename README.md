# 🧠 CYA N (Choose Your AI - Noob)

[![Versione](https://img.shields.io/badge/Versione-5.0_Stabile-blue.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg)]()
[![Ollama](https://img.shields.io/badge/Backend-Ollama-black.svg)]()
[![Privacy](https://img.shields.io/badge/Privacy-100%25_Offline-success.svg)]()

**CYA N** è un orchestratore intelligente per Large Language Models (LLM) progettato per funzionare interamente in locale. Agisce come un **dispatcher semantico**: analizza le tue richieste testuali e le smista automaticamente all'Intelligenza Artificiale più qualificata per quel dominio, garantendo prestazioni ottimali senza mai inviare i tuoi dati su server esterni.

Progettato con un focus estremo sull'ottimizzazione delle risorse, CYA N è in grado di funzionare in modo fluido anche su macchine consumer con soli **8GB di RAM**, grazie a un innovativo sistema di controllo dinamico della memoria.

---

## ✨ Funzionalità Principali

- 🕵️ **100% Offline & Privacy Assoluta:** Nessuna connessione internet richiesta per l'inferenza. I tuoi dati e le tue porzioni di codice non escono mai dal tuo computer.
- 🔀 **Smart Dispatching V2.0:** Smistamento istantaneo (complessità $\mathcal{O}(1)$) basato su dizionari lessicali (`keywords/`). Seleziona autonomamente tra Coding, Matematica, Diritto o ambito Generale.
- 🛡️ **Guardia Dinamica della RAM (Pre-polling):** Prima di caricare un modello, il sistema interroga l'hardware (`psutil`). Se la memoria è insufficiente, effettua un **Fallback Preventivo** verso un modello più leggero, azzerando i crash per *Out of Memory*.
- ⚡ **Asincrono e Reattivo:** Generazione dell'output in streaming continuo con interfaccia CLI dinamica (spinner di caricamento).
- 🧹 **Filtri a Runtime:** Sanificazione automatica dell'output (rimozione tag `<think>`, conversione LaTeX $\rightarrow$ Unicode in tempo reale).

---

## 🏗️ Architettura del Sistema

Il flusso di esecuzione segue un percorso gerarchico e sicuro. Di seguito lo schema logico del routing e dei fallback:

```mermaid
graph TD
    A[Richiesta Utente] --> B(Smart Dispatcher)
    B -->|Coding| C{RAM > 5.5GB?}
    B -->|Math| D[DeepSeek-R1 7B]
    B -->|Rights/General| E{RAM > 12GB?}
    
    C -->|Sì| F[Qwen2.5-Coder 7B]
    C -->|No Fallback| G[Qwen2.5-Coder 1.5B]
    
    E -->|Sì| H[GPT-OSS 20B]
    E -->|No Fallback| I[Llama 3.2 3B]
    
    F --> Z((Output Sanificato))
    G --> Z
    D --> Z
    H --> Z
    I --> Z