"""
step4_evaluation.py — CYA N | Step 4: Valutazione qualitativa NN classifier
=============================================================================
Esecuzione:
    cd <root_progetto>
    python code/step4_evaluation.py

Richiede:
    - code/classifier/nn_weights.pt   (train_nn.py)
    - paraphrase-multilingual-MiniLM-L12-v2  (sentence-transformers)

Output:
    - Tabella risultati per ogni query
    - Riepilogo accuracy per categoria
    - Lista falsi positivi/negativi critici
    - Diagnosi automatica per soglie PIPELINE_PAIR_THRESHOLD

Il set di query è strutturato in 6 categorie:
  A. Mono-domain chiari (20)       → verifica base classificazione
  B. Pipeline ibride esplicite (9) → verifica attivazione pipeline
  C. False pipeline (6)            → verifica NO-pipeline su query ambigue
  D. Follow-up ambigui (10)        → verifica is_followup=True
  E. Cambio dominio (6)            → verifica is_followup=False con history
  F. Edge case critici (8)         → casi noti difficili per il LLM router
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from nn_classifier import predict, DOMAIN_NAMES, PIPELINE_CLASSES

# ─── SET DI SMOKE TEST ───────────────────────────────────────────────────────

SMOKE_TESTS = [

    # ═══════════════════════════════════════════════════════════
    # A. MONO-DOMAIN CHIARI
    # ═══════════════════════════════════════════════════════════

    # --- CODING (5) ---
    {
        "id": "A-C1", "category": "mono_domain",
        "query": "Scrivi una funzione Python che calcola il fattoriale in modo ricorsivo.",
        "history": [], "last_domain": "",
        "expected_class_id": 0, "expected_domain": "coding",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "A-C2", "category": "mono_domain",
        "query": "Come si configura una pipeline CI/CD con GitHub Actions?",
        "history": [], "last_domain": "",
        "expected_class_id": 0, "expected_domain": "coding",
        "expected_followup": False, "expected_diff_min": 2,
    },
    {
        "id": "A-C3", "category": "mono_domain",
        "query": "Implementa l'algoritmo di Dijkstra in Python per trovare il cammino minimo.",
        "history": [], "last_domain": "",
        "expected_class_id": 0, "expected_domain": "coding",
        "expected_followup": False, "expected_diff_min": 2,
    },
    {
        "id": "A-C4", "category": "mono_domain",
        "query": "binary search implementazione Python",
        "history": [], "last_domain": "",
        "expected_class_id": 0, "expected_domain": "coding",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "A-C5", "category": "mono_domain",
        "query": "Spiegami come funziona il Virtual DOM in React rispetto al DOM reale.",
        "history": [], "last_domain": "",
        "expected_class_id": 0, "expected_domain": "coding",
        "expected_followup": False, "expected_diff_min": 2,
    },

    # --- MATH (5) ---
    {
        "id": "A-M1", "category": "mono_domain",
        "query": "Calcola la derivata di f(x) = x^3 + 2x - sin(x).",
        "history": [], "last_domain": "",
        "expected_class_id": 1, "expected_domain": "math",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "A-M2", "category": "mono_domain",
        "query": "Dimostra il teorema di Pitagora evidenziando tutti i passaggi algebrici.",
        "history": [], "last_domain": "",
        "expected_class_id": 1, "expected_domain": "math",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "A-M3", "category": "mono_domain",
        "query": "Applica il processo di ortogonalizzazione di Gram-Schmidt a questo set di vettori.",
        "history": [], "last_domain": "",
        "expected_class_id": 1, "expected_domain": "math",
        "expected_followup": False, "expected_diff_min": 2,
    },
    {
        "id": "A-M4", "category": "mono_domain",
        "query": "autovalori matrice 3x3",
        "history": [], "last_domain": "",
        "expected_class_id": 1, "expected_domain": "math",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "A-M5", "category": "mono_domain",
        "query": "Studia il carattere della serie numerica usando il criterio del rapporto.",
        "history": [], "last_domain": "",
        "expected_class_id": 1, "expected_domain": "math",
        "expected_followup": False, "expected_diff_min": 2,
    },

    # --- RIGHTS (5) ---
    {
        "id": "A-R1", "category": "mono_domain",
        "query": "Quali sono i diritti del lavoratore in caso di licenziamento illegittimo?",
        "history": [], "last_domain": "",
        "expected_class_id": 2, "expected_domain": "rights",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "A-R2", "category": "mono_domain",
        "query": "Cosa prevede il GDPR per la notifica di un data breach entro 72 ore?",
        "history": [], "last_domain": "",
        "expected_class_id": 2, "expected_domain": "rights",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "A-R3", "category": "mono_domain",
        "query": "Spiegami le differenze tra nullità e annullabilità di un contratto.",
        "history": [], "last_domain": "",
        "expected_class_id": 2, "expected_domain": "rights",
        "expected_followup": False, "expected_diff_min": 2,
    },
    {
        "id": "A-R4", "category": "mono_domain",
        "query": "qual è il codice penale per il furto?",
        "history": [], "last_domain": "",
        "expected_class_id": 2, "expected_domain": "rights",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "A-R5", "category": "mono_domain",
        "query": "Quali sono le tutele legali contro il licenziamento discriminatorio per lo Statuto dei Lavoratori?",
        "history": [], "last_domain": "",
        "expected_class_id": 2, "expected_domain": "rights",
        "expected_followup": False, "expected_diff_min": 2,
    },

    # --- GENERAL (5) ---
    {
        "id": "A-G1", "category": "mono_domain",
        "query": "Dammi la ricetta tradizionale per la pasta alla carbonara.",
        "history": [], "last_domain": "",
        "expected_class_id": 3, "expected_domain": "general",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "A-G2", "category": "mono_domain",
        "query": "chi sei?",
        "history": [], "last_domain": "",
        "expected_class_id": 3, "expected_domain": "general",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "A-G3", "category": "mono_domain",
        "query": "Spiegami le cause e le conseguenze della Prima Guerra Mondiale.",
        "history": [], "last_domain": "",
        "expected_class_id": 3, "expected_domain": "general",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "A-G4", "category": "mono_domain",
        "query": "Cosa intendeva Platone con la teoria delle idee e il mito della caverna?",
        "history": [], "last_domain": "",
        "expected_class_id": 3, "expected_domain": "general",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "A-G5", "category": "mono_domain",
        "query": "Spiegami come funziona il fuorigioco nel calcio moderno con il VAR.",
        "history": [], "last_domain": "",
        "expected_class_id": 3, "expected_domain": "general",
        "expected_followup": False, "expected_diff_min": 1,
    },

    # ═══════════════════════════════════════════════════════════
    # B. PIPELINE IBRIDE ESPLICITE
    # ═══════════════════════════════════════════════════════════

    {
        "id": "B-MC1", "category": "pipeline",
        "query": "Implementa in Python la FFT e dimostra il teorema di Nyquist-Shannon con derivazione matematica.",
        "history": [], "last_domain": "",
        "expected_class_id": 4, "expected_domain": "math->coding",
        "expected_followup": False, "expected_diff_min": 3,
    },
    {
        "id": "B-MC2", "category": "pipeline",
        "query": "gradiente coniugato Python sparse",
        "history": [], "last_domain": "",
        "expected_class_id": 4, "expected_domain": "math->coding",
        "expected_followup": False, "expected_diff_min": 2,
    },
    {
        "id": "B-MC3", "category": "pipeline",
        "query": "Implementa regressione lineare multipla in Python e dimostra la teoria dei minimi quadrati.",
        "history": [], "last_domain": "",
        "expected_class_id": 4, "expected_domain": "math->coding",
        "expected_followup": False, "expected_diff_min": 2,
    },
    {
        "id": "B-RC1", "category": "pipeline",
        "query": "Scrivi script Python per calcolo TFR rispettando D.Lgs. 66/2003 con calcolo normativo.",
        "history": [], "last_domain": "",
        "expected_class_id": 5, "expected_domain": "rights->coding",
        "expected_followup": False, "expected_diff_min": 2,
    },
    {
        "id": "B-RC2", "category": "pipeline",
        "query": "Codice Python per busta paga conforme CCNL con calcolo IRPEF e detrazioni.",
        "history": [], "last_domain": "",
        "expected_class_id": 5, "expected_domain": "rights->coding",
        "expected_followup": False, "expected_diff_min": 3,
    },
    {
        "id": "B-RC3", "category": "pipeline",
        "query": "Implementa in Python un registro automatico dei trattamenti Art. 30 GDPR che tracci operazioni CRUD.",
        "history": [], "last_domain": "",
        "expected_class_id": 5, "expected_domain": "rights->coding",
        "expected_followup": False, "expected_diff_min": 3,
    },
    {
        "id": "B-RM1", "category": "pipeline",
        "query": "Qual è la formula matematica per calcolare l'indennità Jobs Act in funzione dell'anzianità?",
        "history": [], "last_domain": "",
        "expected_class_id": 6, "expected_domain": "rights->math",
        "expected_followup": False, "expected_diff_min": 2,
    },
    {
        "id": "B-RM2", "category": "pipeline",
        "query": "Dimostra matematicamente la soglia di usura secondo la Banca d'Italia e la L. 108/1996.",
        "history": [], "last_domain": "",
        "expected_class_id": 6, "expected_domain": "rights->math",
        "expected_followup": False, "expected_diff_min": 2,
    },
    {
        "id": "B-RM3", "category": "pipeline",
        "query": "Calcola matematicamente il piano di ammortamento alla francese secondo normativa bancaria italiana.",
        "history": [], "last_domain": "",
        "expected_class_id": 6, "expected_domain": "rights->math",
        "expected_followup": False, "expected_diff_min": 2,
    },

    # ═══════════════════════════════════════════════════════════
    # C. FALSE PIPELINE — devono restare mono-domain
    # ═══════════════════════════════════════════════════════════

    {
        "id": "C-FP1", "category": "false_pipeline",
        "query": "codice Python per sommare una lista di numeri",
        "history": [], "last_domain": "",
        # "codice" + "sommare" (parola matematica) → NON pipeline, è coding puro
        "expected_class_id": 0, "expected_domain": "coding",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "C-FP2", "category": "false_pipeline",
        "query": "cosa dice la legge sul codice fiscale?",
        "history": [], "last_domain": "",
        # "codice" ≠ coding → rights
        "expected_class_id": 2, "expected_domain": "rights",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "C-FP3", "category": "false_pipeline",
        "query": "qual è il codice penale per il furto?",
        "history": [], "last_domain": "",
        # "codice penale" ≠ coding
        "expected_class_id": 2, "expected_domain": "rights",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "C-FP4", "category": "false_pipeline",
        "query": "scrivi una funzione Python che calcola la media di una lista",
        "history": [], "last_domain": "",
        # "calcola la media" = operazione banale, non math domain
        "expected_class_id": 0, "expected_domain": "coding",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "C-FP5", "category": "false_pipeline",
        "query": "cos'è la media geometrica?",
        "history": [], "last_domain": "",
        # Domanda teorica math, non richiede codice
        "expected_class_id": 1, "expected_domain": "math",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "C-FP6", "category": "false_pipeline",
        "query": "spiegami la normativa sui contratti di lavoro",
        "history": [], "last_domain": "",
        # "contratti" è concetto rights puro
        "expected_class_id": 2, "expected_domain": "rights",
        "expected_followup": False, "expected_diff_min": 2,
    },

    # ═══════════════════════════════════════════════════════════
    # D. FOLLOW-UP AMBIGUI (is_followup DEVE essere True)
    # ═══════════════════════════════════════════════════════════

    {
        "id": "D-FU1", "category": "followup",
        "query": "perché?",
        "history": [
            {"role": "user",      "content": "Come funziona la ricorsione in Python?"},
            {"role": "assistant", "content": "La ricorsione è quando una funzione chiama se stessa..."},
        ],
        "last_domain": "coding",
        "expected_class_id": 0, "expected_domain": "coding",
        "expected_followup": True, "expected_diff_min": 1,
    },
    {
        "id": "D-FU2", "category": "followup",
        "query": "non ho capito il passaggio 2",
        "history": [
            {"role": "user",      "content": "Dimostra il teorema di Cauchy."},
            {"role": "assistant", "content": "Il teorema di Cauchy afferma che..."},
        ],
        "last_domain": "math",
        "expected_class_id": 1, "expected_domain": "math",
        "expected_followup": True, "expected_diff_min": 1,
    },
    {
        "id": "D-FU3", "category": "followup",
        "query": "e le sanzioni quanto sono?",
        "history": [
            {"role": "user",      "content": "Come funziona la violazione del GDPR per una PMI?"},
            {"role": "assistant", "content": "Le sanzioni GDPR possono arrivare fino a..."},
        ],
        "last_domain": "rights",
        "expected_class_id": 2, "expected_domain": "rights",
        "expected_followup": True, "expected_diff_min": 1,
    },
    {
        "id": "D-FU4", "category": "followup",
        "query": "e quindi?",
        "history": [
            {"role": "user",      "content": "Consigliami un film di fantascienza."},
            {"role": "assistant", "content": "Ti consiglio Blade Runner 2049..."},
        ],
        "last_domain": "general",
        "expected_class_id": 3, "expected_domain": "general",
        "expected_followup": True, "expected_diff_min": 1,
    },
    {
        "id": "D-FU5", "category": "followup",
        "query": "spiega meglio",
        "history": [
            {"role": "user",      "content": "Come funziona l'algoritmo di Dijkstra?"},
            {"role": "assistant", "content": "Dijkstra esplora il grafo partendo dal nodo sorgente..."},
        ],
        "last_domain": "coding",
        "expected_class_id": 0, "expected_domain": "coding",
        "expected_followup": True, "expected_diff_min": 1,
    },
    {
        "id": "D-FU6", "category": "followup",
        "query": "riesci a farlo in Java?",
        "history": [
            {"role": "user",      "content": "Scrivi codice Python per ordinare una lista."},
            {"role": "assistant", "content": "Puoi usare sorted() o list.sort()..."},
        ],
        "last_domain": "coding",
        "expected_class_id": 0, "expected_domain": "coding",
        "expected_followup": True, "expected_diff_min": 1,
    },
    {
        "id": "D-FU7", "category": "followup",
        "query": "e la diagonalizzazione?",
        "history": [
            {"role": "user",      "content": "Spiega la decomposizione spettrale."},
            {"role": "assistant", "content": "La decomposizione spettrale di A = Q Λ Q^T..."},
        ],
        "last_domain": "math",
        "expected_class_id": 1, "expected_domain": "math",
        "expected_followup": True, "expected_diff_min": 2,
    },
    {
        "id": "D-FU8", "category": "followup",
        "query": "e il DPO è obbligatorio?",
        "history": [
            {"role": "user",      "content": "Quando si nomina un Data Protection Officer?"},
            {"role": "assistant", "content": "Il DPO è obbligatorio quando..."},
        ],
        "last_domain": "rights",
        "expected_class_id": 2, "expected_domain": "rights",
        "expected_followup": True, "expected_diff_min": 2,
    },
    {
        "id": "D-FU9", "category": "followup",
        "query": "aggiungi la gestione degli errori",
        "history": [
            {"role": "user",      "content": "Scrivi un parser JSON in Python."},
            {"role": "assistant", "content": "Ecco il parser: import json..."},
        ],
        "last_domain": "coding",
        "expected_class_id": 0, "expected_domain": "coding",
        "expected_followup": True, "expected_diff_min": 2,
    },
    {
        "id": "D-FU10", "category": "followup",
        "query": "puoi fare un esempio numerico?",
        "history": [
            {"role": "user",      "content": "Spiega come si calcola la covarianza."},
            {"role": "assistant", "content": "La covarianza Cov(X,Y) = E[(X-μX)(Y-μY)]..."},
        ],
        "last_domain": "math",
        "expected_class_id": 1, "expected_domain": "math",
        "expected_followup": True, "expected_diff_min": 1,
    },

    # ═══════════════════════════════════════════════════════════
    # E. CAMBIO DOMINIO (is_followup DEVE essere False)
    # ═══════════════════════════════════════════════════════════

    {
        "id": "E-CD1", "category": "domain_switch",
        "query": "consigliami un ristorante a Roma",
        "history": [
            {"role": "user",      "content": "Implementa server REST in Flask."},
            {"role": "assistant", "content": "Ecco un server Flask..."},
        ],
        "last_domain": "coding",
        "expected_class_id": 3, "expected_domain": "general",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "E-CD2", "category": "domain_switch",
        "query": "cosa mangio stasera?",
        "history": [
            {"role": "user",      "content": "Qual è la normativa GDPR sulla data retention?"},
            {"role": "assistant", "content": "Il GDPR prevede..."},
        ],
        "last_domain": "rights",
        "expected_class_id": 3, "expected_domain": "general",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "E-CD3", "category": "domain_switch",
        "query": "qual è la capitale della Francia?",
        "history": [
            {"role": "user",      "content": "Come configuro Kubernetes per il load balancing?"},
            {"role": "assistant", "content": "Per configurare Kubernetes..."},
        ],
        "last_domain": "coding",
        "expected_class_id": 3, "expected_domain": "general",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "E-CD4", "category": "domain_switch",
        "query": "Dio esiste?",
        "history": [
            {"role": "user",      "content": "Come funziona l'algoritmo di Dijkstra?"},
            {"role": "assistant", "content": "Dijkstra è un algoritmo greedy..."},
        ],
        "last_domain": "coding",
        "expected_class_id": 3, "expected_domain": "general",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "E-CD5", "category": "domain_switch",
        "query": "consigliami scarpe uomo",
        "history": [
            {"role": "user",      "content": "Come funziona la fattorizzazione LU?"},
            {"role": "assistant", "content": "La fattorizzazione LU decompone A = LU..."},
        ],
        "last_domain": "math",
        "expected_class_id": 3, "expected_domain": "general",
        "expected_followup": False, "expected_diff_min": 1,
    },
    {
        "id": "E-CD6", "category": "domain_switch",
        "query": "chi ha vinto il mondiale 2022?",
        "history": [
            {"role": "user",      "content": "Implementa la firma digitale RSA in Python."},
            {"role": "assistant", "content": "Per RSA usiamo la libreria cryptography..."},
        ],
        "last_domain": "coding",
        "expected_class_id": 3, "expected_domain": "general",
        "expected_followup": False, "expected_diff_min": 1,
    },

    # ═══════════════════════════════════════════════════════════
    # F. EDGE CASE CRITICI
    # ═══════════════════════════════════════════════════════════

    {
        "id": "F-EC1", "category": "edge_case",
        "query": "2+2",
        "history": [], "last_domain": "",
        # Problema noto: piccolo calcolo → general, NON math (per il LLM router)
        # Il dataset training lo etichetta math (vedi dataset_v2.jsonl)
        "expected_class_id": 3, "expected_domain": "math",
        "expected_followup": False, "expected_diff_min": 1,
        "note": "Query numerica banale: il dataset la etichetta 'general' (vedi expand_dataset_v2.py)"
    },
    {
        "id": "F-EC2", "category": "edge_case",
        "query": "Spiegami come funziona il debug delle tue emozioni per superare un trauma.",
        "history": [], "last_domain": "",
        # "debug" è termine coding ma il contesto è psicologico → general
        "expected_class_id": 3, "expected_domain": "general",
        "expected_followup": False, "expected_diff_min": 1,
        "note": "Keyword 'debug' fuorviante: contesto è psicologico, atteso general"
    },
    {
        "id": "F-EC3", "category": "edge_case",
        "query": "Come si calcola la sezione aurea e come è stata applicata nell'architettura rinascimentale?",
        "history": [], "last_domain": "",
        # Contiene "calcola" e "sezione aurea" (math) ma il contesto è storico-artistico → general
        "expected_class_id": 3, "expected_domain": "general",
        "expected_followup": False, "expected_diff_min": 1,
        "note": "Math keyword ma contesto storico-artistico: atteso general per dataset training"
    },
    {
        "id": "F-EC4", "category": "edge_case",
        "query": "Come si implementa l'autenticazione tramite token JWT in un'API REST?",
        "history": [], "last_domain": "",
        # Misto sicurezza/diritto/coding: atteso coding per keyword tecniche dominanti
        "expected_class_id": 0, "expected_domain": "coding",
        "expected_followup": False, "expected_diff_min": 2,
        "note": "JWT, API, REST: keyword coding dominanti, sicurezza non è rights"
    },
    {
        "id": "F-EC5", "category": "edge_case",
        "query": "Mio figlio ha rotto qualcosa in casa per un lancio sbagliato, chi è responsabile verso il vicino?",
        "history": [], "last_domain": "",
        # Formulazione colloquiale di una domanda legale → rights
        "expected_class_id": 2, "expected_domain": "rights",
        "expected_followup": False, "expected_diff_min": 1,
        "note": "Formulazione colloquiale: deve essere classificata rights nonostante il registro informale"
    },
    {
        "id": "F-EC6", "category": "edge_case",
        "query": "rispiega il passaggio 2",
        "history": [
            {"role": "user",      "content": "Dimostra per induzione la somma dei primi n numeri."},
            {"role": "assistant", "content": "Caso base: n=1, P(1) = 1 = 1(1+1)/2 ✓..."},
        ],
        "last_domain": "math",
        # Shortissimo follow-up: il NN deve cogliere il contesto dalla history
        "expected_class_id": 1, "expected_domain": "math",
        "expected_followup": True, "expected_diff_min": 1,
        "note": "Follow-up corto: dipende fortemente dalla history injection nell'embedding"
    },
    {
        "id": "F-EC7", "category": "edge_case",
        "query": "come si calcola l'IVA su una fattura?",
        "history": [
            {"role": "user",      "content": "Come funziona la partita IVA?"},
            {"role": "assistant", "content": "La partita IVA è un codice identificativo fiscale..."},
        ],
        "last_domain": "general",
        # Domanda math-adjacent ma in contesto fiscale/normativo: atteso math (calcolo numerico)
        # oppure general (topic finanziario generico) — caso borderline
        "expected_class_id": 1, "expected_domain": "math",
        "expected_followup": False, "expected_diff_min": 1,
        "note": "Borderline math/general: il dataset lo etichetta math (calcolo percentuale)"
    },
    {
        "id": "F-EC8", "category": "edge_case",
        "query": "implementa il login con JWT in Flask",
        "history": [
            {"role": "user",      "content": "Come funziona l'autenticazione a due fattori?"},
            {"role": "assistant", "content": "Il 2FA aggiunge un secondo fattore di verifica..."},
        ],
        "last_domain": "general",
        # Cambio verso coding puro da history general → is_followup=False, coding
        "expected_class_id": 0, "expected_domain": "coding",
        "expected_followup": False, "expected_diff_min": 2,
        "note": "Cambio dominio general→coding con query tecnica esplicita: deve classificare coding"
    },
]

# ─── RUNNER ───────────────────────────────────────────────────────────────────

_DOMAIN_NAMES_4 = ['coding', 'math', 'rights', 'general']

def _class_id_to_domain(class_id: int) -> str:
    from nn_classifier import DOMAIN_NAMES
    return DOMAIN_NAMES[class_id] if 0 <= class_id < len(DOMAIN_NAMES) else "???"

def _is_pipeline(class_id: int) -> bool:
    return class_id in PIPELINE_CLASSES

def run_evaluation():
    results = []

    print("\n" + "=" * 80)
    print("  CYA N — STEP 4: SMOKE TEST NN CLASSIFIER")
    print("=" * 80)
    print(f"  Query totali: {len(SMOKE_TESTS)}\n")

    # SALVO LE QUERY ERRATE NEL FILE - lo cancello se già esiste
    file_wrong_queries = "wrong_query.md"
    #cancello il file se esiste
    if os.path.exists(file_wrong_queries):
        os.remove(file_wrong_queries)

    for tc in SMOKE_TESTS:
        print(f"  [{tc['id']}] {tc['query'][:65]}{'...' if len(tc['query']) > 65 else ''}")

        try:
            class_id, confidence, domain_scores, difficulty, is_followup = predict(
                tc['query'],
                last_domain=tc.get('last_domain', ''),
                history=tc.get('history', []),
            )
        except Exception as e:
            print(f"         ⚠ ERRORE: {e}")
            results.append({**tc, "status": "ERROR", "actual_class_id": -1,
                            "actual_domain": "???", "actual_followup": False,
                            "actual_diff": -1, "confidence": 0.0})
            continue

        actual_domain = _class_id_to_domain(class_id)
        exp_domain    = tc['expected_domain']
        exp_followup  = tc['expected_followup']
        exp_diff_min  = tc['expected_diff_min']

        ok_domain   = actual_domain == exp_domain
        ok_followup = is_followup   == exp_followup
        ok_diff     = difficulty    >= exp_diff_min

        errore = 0

        if ok_domain and ok_followup:
            status = "✅ OK"
        elif ok_domain and not ok_followup:
            status = "⚠ FOLLOWUP_ERR"
            errore = 1
        elif not ok_domain and ok_followup:
            status = "❌ DOMAIN_ERR"
            errore = 1
        else:
            status = "❌ BOTH_ERR"
            errore = 1
            

        dom_str = (f"  → {actual_domain.upper()} "
                   f"(exp: {exp_domain.upper()}) {'' if ok_domain else '← WRONG'}")
        fu_str  = (f"  followup={is_followup} "
                   f"(exp: {exp_followup}) {'' if ok_followup else '← WRONG'}")
        d_str   = f"  diff={difficulty} conf={confidence:.3f}"

        print(f"     {status}")
        print(f"     {dom_str}")
        print(f"     {fu_str}")
        print(f"     {d_str}")
        if 'note' in tc:
            print(f"     📝 {tc['note']}")
        print()

        #scrivo su file le query errate
        if(errore == 1):
            #ricreo / creo il file (modalità append)
            with open(file_wrong_queries, "a", encoding="utf-8") as file:
                file.write(f"\nfrase: {tc['query']}\n{status}\n{dom_str}\n{fu_str}{d_str}\n")

        results.append({
            **tc,
            "status":           status,
            "actual_class_id":  class_id,
            "actual_domain":    actual_domain,
            "actual_followup":  is_followup,
            "actual_diff":      difficulty,
            "confidence":       confidence,
            "ok_domain":        ok_domain,
            "ok_followup":      ok_followup,
        })

    _print_summary(results)
    _diagnose_thresholds(results)
    return results


def _print_summary(results: list):
    by_cat = {}
    for r in results:
        cat = r['category']
        by_cat.setdefault(cat, []).append(r)

    print("=" * 80)
    print("  RIEPILOGO PER CATEGORIA")
    print("=" * 80)

    total_ok = 0
    for cat, items in by_cat.items():
        dom_ok = sum(1 for r in items if r.get('ok_domain', False))
        fu_ok  = sum(1 for r in items if r.get('ok_followup', True))
        n      = len(items)
        full_ok = sum(1 for r in items if r.get('ok_domain') and r.get('ok_followup'))
        total_ok += full_ok
        print(f"  {cat:20s}: {full_ok}/{n} completamente corretti | "
              f"domain={dom_ok}/{n} | followup={fu_ok}/{n}")

    total = len(results)
    print(f"\n  TOTALE: {total_ok}/{total} ({total_ok/total*100:.1f}%)")

    # Falsi positivi/negativi critici
    errors = [r for r in results if "❌" in r.get('status', '')]
    warnings = [r for r in results if "⚠" in r.get('status', '')]

    if errors:
        print(f"\n  ─── ERRORI CRITICI ({len(errors)}) ───────────────────────")
        for r in errors:
            print(f"  [{r['id']}] atteso={r['expected_domain'].upper()} "
                  f"→ ottenuto={r['actual_domain'].upper()} | "
                  f"query: {r['query'][:55]}...")

    if warnings:
        print(f"\n  ─── AVVERTENZE followup ({len(warnings)}) ──────────────────")
        for r in warnings:
            print(f"  [{r['id']}] followup atteso={r['expected_followup']} "
                  f"→ ottenuto={r['actual_followup']} | "
                  f"query: {r['query'][:55]}...")


def _diagnose_thresholds(results: list):
    """
    Analizza i confidence score per suggerire aggiustamenti alla soglia
    PIPELINE_PAIR_THRESHOLD in nn_classifier.py.
    """
    print(f"\n  ─── DIAGNOSI SOGLIE PIPELINE ────────────────────────────────")

    pipeline_correct = [r for r in results if r['category'] == 'pipeline' and r.get('ok_domain')]
    pipeline_wrong   = [r for r in results if r['category'] == 'pipeline' and not r.get('ok_domain')]
    false_pipe       = [r for r in results if r['category'] == 'false_pipeline' and
                        _is_pipeline(r.get('actual_class_id', -1))]

    if pipeline_correct:
        confs = [r['confidence'] for r in pipeline_correct]
        print(f"  Pipeline corrette ({len(pipeline_correct)}): "
              f"conf min={min(confs):.3f} mean={sum(confs)/len(confs):.3f}")

    if pipeline_wrong:
        print(f"  Pipeline mancate  ({len(pipeline_wrong)}): "
              f"IDs = {[r['id'] for r in pipeline_wrong]}")

    if false_pipe:
        print(f"  ⚠ FALSE PIPELINE  ({len(false_pipe)}): "
              f"IDs = {[r['id'] for r in false_pipe]}")
        confs_fp = [r['confidence'] for r in false_pipe]
        print(f"    → Alzare PIPELINE_PAIR_THRESHOLD sopra {max(confs_fp):.3f}")
    else:
        print(f"  ✓ Nessuna false pipeline rilevata")

    print("=" * 80)


if __name__ == '__main__':
    run_evaluation()
