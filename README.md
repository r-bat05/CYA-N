# 🧠 CYA N (Choose Your AI - Noob)

[![Versione](https://img.shields.io/badge/Versione-5.2_Stabile-blue.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg)]()
[![Ollama](https://img.shields.io/badge/Backend-Ollama-black.svg)]()
[![Privacy](https://img.shields.io/badge/Privacy-100%25_Offline-success.svg)]()

**CYA N** è un orchestratore intelligente per Large Language Models (LLM) progettato per funzionare interamente in locale. Agisce come un **dispatcher ibrido**: analizza le tue richieste tracciando un arco di instradamento semantico (tramite embedding vettoriali) e testuale (tramite algoritmi di tolleranza), smistando automaticamente l'input verso l'Intelligenza Artificiale più qualificata per quel dominio. 

Progettato con un focus estremo sull'ottimizzazione delle risorse, CYA N traccia archi operativi fluidi anche su macchine consumer con soli **8GB di RAM**, grazie a un innovativo sistema di controllo dinamico della memoria.

---

## ✨ Funzionalità Principali

- 🕵️ **100% Offline & Privacy Assoluta:** Nessuna connessione internet richiesta per l'inferenza. Ogni arco di comunicazione si esaurisce all'interno della tua macchina.
- 🔀 **Routing Ibrido & Multi-Dominio (V4.1):** Smistamento primario vettoriale tramite `nomic-embed-text` (similarità coseno). In caso di incertezza, il sistema attiva un arco di fallback testuale elastico basato sulla **Distanza di Levenshtein** per tollerare gli errori di battitura. Supporta archi paralleli per query ibride.
- 🛡️ **Guardia Dinamica della RAM (Pre-polling):** Prima di caricare un modello, il sistema interroga l'hardware (`psutil`). Se la memoria è insufficiente, traccia un **arco di emergenza preventivo** verso un modello più leggero, azzerando i crash per *Out of Memory*.
- 💾 **Agenti Stateful:** I modelli vengono instanziati una singola volta all'avvio. Questo arco di persistenza mantiene lo stato in memoria, predisponendo l'architettura per la cronologia di conversazione.
- ⚡ **Asincrono e Reattivo:** Generazione dell'output in streaming continuo con interfaccia CLI dinamica (spinner di caricamento).
- 🧹 **Filtri a Runtime:** Sanificazione automatica dell'arco generativo (rimozione tag `<think>`, eliminazione caratteri asiatici anomali, conversione macro matematiche complesse in Unicode puro).

---

## 🏗️ Topologia del Sistema e Archi di Instradamento

Il flusso di esecuzione segue un percorso gerarchico e sicuro. Di seguito lo schema logico del routing ibrido e degli archi di fallback:

```mermaid
graph TD
    A[Richiesta Utente] --> B(Semantic Router vettoriale)
    B -->|Bassa Confidenza| C(Keyword Matcher Levenshtein)
    B -->|Alta Confidenza| D{Smistamento Domini}
    C --> D
    
    D -->|Coding| E{RAM > 5.5GB?}
    D -->|Math| F[DeepSeek-R1 7B]
    D -->|Rights/General| G{RAM > 12GB?}
    
    E -->|Sì| H[Qwen3.5 9B]
    E -->|No / Fallback| I[Qwen2.5-Coder 1.5B]
    
    G -->|Sì| J[GPT-OSS 20B]
    G -->|No / Fallback| K[Llama 3.2 3B]
    
    H --> Z((Output Sanificato))
    I --> Z
    F --> Z
    J --> Z
    K --> Z