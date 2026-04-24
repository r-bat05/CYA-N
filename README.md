# 🧠 CYA N (Choose Your AI - Noob)

[![Versione](https://img.shields.io/badge/Versione-6.5.0_Stabile-blue.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg)]()
[![Ollama](https://img.shields.io/badge/Backend-Ollama-black.svg)]()
[![Database](https://img.shields.io/badge/VectorDB-LanceDB-red.svg)]()
[![Privacy](https://img.shields.io/badge/Privacy-100%25_Offline-success.svg)]()

**CYA N** è un orchestratore intelligente per Large Language Models (LLM) progettato per funzionare interamente in locale. Agisce come un **dispatcher ibrido**: analizza le tue richieste tracciando un arco di instradamento semantico e testuale, smistando automaticamente l'input verso l'agente IA più qualificato o orchestrando una collaborazione tra più agenti per query complesse. 

Progettato con un focus estremo sull'ottimizzazione delle risorse, CYA N traccia archi operativi fluidi anche su macchine consumer con soli **8 GB di RAM**, grazie a un innovativo sistema di controllo dinamico della memoria e sincronizzazione hardware.

---

## ✨ Funzionalità Principali e Architettura V6.5.0

- 🔀 **Routing Ibrido Avanzato a 3 Livelli:** 1. **Filtro di Complessità:** Le query inferiori a 8 parole vengono declassate a mono-dominio per preservare la RAM.
  2. **Vector Store (Distance-Weighted k-NN):** Sostituisce la vecchia similarità coseno con un motore vettoriale basato su **LanceDB**. Usa una formula di decadimento del peso (`weight = 1.0 / (dist + epsilon)`) per garantire ibridazioni chirurgiche e gestire i domini secondari con estrema precisione.
  3. **Keyword Fallback (Fase 1 e 2):** In caso di ambiguità semantica o indisponibilità del DB, interviene un matcher basato sulla Distanza di Levenshtein, con tolleranza dinamica degli errori di battitura.
- 🛡️ **GENERAL Isolation (P0 Guard):** Un sofisticato sistema di sicurezza che impedisce al dominio generalista di inquinare le pipeline tecniche (Semantic Bleed). Se `GENERAL` viene estratto in una query ibrida, la pipeline viene abortita e degradata al dominio tecnico dominante.
- 🧠 **Pipeline Multi-Agente (Draft & Merge):** Se la query richiede due domini (es. Coding + Rights), CYA N esegue i modelli in sequenza. L'Agente A genera una bozza tecnica, dopodiché l'Agente B (definito tramite una `pipeline_order_matrix` autoritativa) integra la bozza con la sua specializzazione.
- 🔎 **Critic Pass (Auto-Revisione):** Per prevenire allucinazioni ("Fiducia Cieca"), l'Agente B esegue un passaggio finale in cui critica e corregge la propria sintesi confrontandola con la query originale dell'utente.
- ⏱️ **Guardia Dinamica e Sincronizzazione RAM:** Prima di caricare un modello, il sistema interroga l'hardware (`psutil`). Se la memoria è insufficiente, esegue un **downgrade preventivo** a un modello più leggero. Durante la pipeline, un ciclo di polling con *timeout configurabile* mette in pausa l'esecuzione finché la VRAM del primo agente non viene completamente rilasciata (`keep_alive=0`).
- 🧹 **Difesa del Contesto Dinamica:** Troncamento automatico degli output intermedi basato su parametri configurabili (es. 9000 caratteri) per evitare la saturazione dei token. Sanificazione dinamica dai tag di reasoning (es. `<think>`, `<|thought|>`), caratteri asiatici anomali e macro LaTeX.

---

## 🏗️ Topologia del Sistema e Archi di Instradamento

Il flusso di esecuzione segue un percorso gerarchico e sicuro. Di seguito lo schema logico del routing ibrido e degli archi di fallback:

```mermaid
graph TD
    A[Richiesta Utente] --> B(Vector Store LanceDB k-NN)
    B -->|Bassa Confidenza / Offline| C(Keyword Matcher Levenshtein)
    B -->|Alta Confidenza| D{Smistamento Domini}
    C --> D
    
    D -->|P0 Guard Intercept| L[Isolamento GENERAL]
    L --> D
    
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