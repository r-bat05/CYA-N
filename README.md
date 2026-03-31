# 🧠 CYA N (Choose Your AI - Noob)

[![Versione](https://img.shields.io/badge/Versione-6.2.4_Stabile-blue.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg)]()
[![Ollama](https://img.shields.io/badge/Backend-Ollama-black.svg)]()
[![Privacy](https://img.shields.io/badge/Privacy-100%25_Offline-success.svg)]()

**CYA N** è un orchestratore intelligente per Large Language Models (LLM) progettato per funzionare interamente in locale. Agisce come un **dispatcher ibrido**: analizza le tue richieste tracciando un arco di instradamento semantico e testuale, smistando automaticamente l'input verso l'agente IA più qualificato o orchestrando una collaborazione tra più agenti per query complesse. 

Progettato con un focus estremo sull'ottimizzazione delle risorse, CYA N traccia archi operativi fluidi anche su macchine consumer con soli **8 GB di RAM**, grazie a un innovativo sistema di controllo dinamico della memoria e sincronizzazione hardware.

---

## ✨ Funzionalità Principali e Architettura V6

- 🔀 **Routing Ibrido a 3 Livelli:** 1. **Filtro di Complessità:** Le query inferiori a 8 parole vengono declassate a mono-dominio per preservare la RAM.
  2. **Semantic Router (Fase 0):** Utilizza gli embedding vettoriali (`nomic-embed-text`) per calcolare la similarità coseno. È in grado di estrarre domini singoli o rilevare query ibride bypassando i drop di confidenza.
  3. **Keyword Fallback (Fase 1 e 2):** In caso di ambiguità, interviene un matcher basato sulla Distanza di Levenshtein, con tolleranza dinamica degli errori di battitura.
- 🧠 **Pipeline Multi-Agente (Draft & Merge):** Se la query richiede due domini (es. Coding + Rights), CYA N esegue i modelli in sequenza. L'Agente A genera una bozza tecnica, dopodiché l'Agente B (definito tramite una `pipeline_order_matrix` autoritativa) integra la bozza con la sua specializzazione.
- 🔎 **Critic Pass (Auto-Revisione):** Per prevenire allucinazioni ("Fiducia Cieca"), l'Agente B esegue un passaggio finale in cui critica e corregge la propria sintesi confrontandola con la query originale dell'utente.
- 🛡️ **Guardia Dinamica della RAM:** Prima di caricare un modello, il sistema interroga l'hardware (`psutil`). Se la memoria è insufficiente, esegue un **downgrade preventivo** a un modello più leggero. Durante la pipeline, un ciclo di polling mette in pausa l'esecuzione finché la VRAM del primo agente non viene completamente rilasciata (`keep_alive=0`).
- 🧹 **Difesa del Contesto & Sanificazione:** Troncamento automatico degli output intermedi a 6000 caratteri per evitare la saturazione dei token. Sanificazione automatica da tag `<think>`, caratteri asiatici anomali e macro LaTeX.

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