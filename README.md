# 🧠 CYA N (Choose Your AI - Noob)

[![Versione](https://img.shields.io/badge/Versione-6.8.0_Stabile-blue.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg)]()
[![Ollama](https://img.shields.io/badge/Backend-Ollama-black.svg)]()
[![Database](https://img.shields.io/badge/VectorDB-LanceDB-red.svg)]()
[![Privacy](https://img.shields.io/badge/Privacy-100%25_Offline-success.svg)]()

**CYA N** è un orchestratore intelligente per Large Language Models (LLM) progettato per funzionare interamente in locale. Agisce come un **dispatcher ibrido**: analizza le tue richieste tracciando un arco di instradamento semantico e testuale, smistando automaticamente l'input verso l'agente IA più qualificato o orchestrando una collaborazione tra più agenti per query complesse. 

Progettato con un focus estremo sull'ottimizzazione delle risorse, CYA N traccia archi operativi fluidi anche su macchine consumer con soli **8 GB di RAM**, grazie a un innovativo sistema di controllo dinamico della memoria e sincronizzazione hardware.

---

## ✨ Funzionalità Principali e Architettura V6.8.0

- 🔀 **Routing Ibrido Avanzato a 3 Livelli:** 1. **Filtro di Complessità:** Le query inferiori a 8 parole vengono declassate a mono-dominio per preservare la RAM.
  2. **Vector Store (Distance-Weighted k-NN):** Motore vettoriale basato su **LanceDB**. Usa una formula di decadimento del peso (`weight = 1.0 / (dist + epsilon)`) per garantire ibridazioni chirurgiche e gestire i domini secondari con estrema precisione. Il guardiano di Top-Domain viene bypassato per query brevi, fidandosi del k-NN puro.
  3. **Keyword Fallback (Fase 1 e 2):** In caso di ambiguità semantica o indisponibilità del DB, interviene un matcher in due fasi: *Hard-Match* rigoroso O(1) e *Soft-Match* basato sulla Distanza di Levenshtein, con tolleranza dinamica per varianti morfologiche e plurali.
- 📌 **Domain Retention (Sticky Routing):** Le query brevi di follow-up (es. *"E in Python?"*, *"Fammi un esempio"*) non contengono keyword sufficienti e finirebbero erroneamente in `general`. Lo *Sticky Routing* le ancora forzatamente all'ultimo dominio tecnico attivo. Il sistema esegue un *Context Switch* solo quando il k-NN rileva un drastico cambio di argomento con alta confidenza (> 0.45).
- 💬 **Chat History (Sliding Window):** Il sistema gestisce dialoghi multi-turno tramite una finestra scorrevole salvata in RAM. L'iniezione dinamica della cronologia e la fusione automatica del *Few-Shot* nel System Prompt evitano la saturazione della *Context Window*, permettendo all'utente di fare riferimenti anaforici alle query precedenti.
- 🛡️ **GENERAL Isolation (P0 Guard):** Un sofisticato sistema di sicurezza che impedisce al dominio generalista di inquinare le pipeline tecniche (Semantic Bleed). Se `GENERAL` viene estratto in una query ibrida, la pipeline viene abortita e degradata al dominio tecnico dominante.
- 🧠 **Pipeline Multi-Agente (Draft & Merge):** Se la query richiede due domini (es. Coding + Rights), CYA N esegue i modelli in sequenza. L'Agente A genera una bozza tecnica, dopodiché l'Agente B (definito tramite una `pipeline_order_matrix` autoritativa) integra la bozza con la sua specializzazione.
- 🔎 **Critic Pass (Auto-Revisione):** Per prevenire allucinazioni ("Fiducia Cieca"), l'Agente B esegue un passaggio finale in cui critica e corregge la propria sintesi confrontandola con la query originale dell'utente. *La Chat History è intenzionalmente esclusa in questa fase per garantire oggettività.*
- ⏱️ **Guardia Dinamica ed Explicit Unload (RAM):** Prima di caricare un modello, il sistema interroga l'hardware (`psutil`) per un eventuale **downgrade preventivo**. Durante le pipeline, per evitare il crash, viene inviata una chiamata API di **Explicit Unload** al termine dell'Agente A. Il sistema attende che il Kernel Linux rilasci fisicamente le pagine di memoria (mmap) prima di avviare il polling di sincronizzazione per il secondo Agente.
- 🧹 **Sanificazione Code-Block Aware:** Troncamento automatico degli output intermedi per non saturare i token (es. 9000 char). Il parsing finale intercetta i tag di ragionamento (letti dinamicamente dal config), esegue la traduzione matematica (LaTeX -> Unicode) e applica i filtri CJK **esclusivamente sul testo discorsivo**, proteggendo i blocchi di codice Markdown e la loro sintassi.

---

## 🏗️ Topologia del Sistema e Archi di Instradamento

Il flusso di esecuzione segue un percorso gerarchico e sicuro. Di seguito lo schema logico del routing ibrido e degli archi di fallback:

```mermaid
graph TD
    A[Richiesta Utente] --> B(Vector Store LanceDB k-NN)
    B -->|Bassa Confidenza / Offline| C(Keyword Matcher Levenshtein)
    B -->|Alta Confidenza| D{Smistamento Domini}
    C --> D
    
    D -->|Query Breve di Follow-Up| S[Sticky Routing / Domain Retention]
    S --> D
    
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