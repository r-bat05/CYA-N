"""
    CONFIGURAZIONE CENTRALE (CYA N)

    Questo file contiene tutte le costanti, i percorsi e le impostazioni
    del progetto. Modifica questo file per cambiare modelli, soglie RAM
    o parametri di generazione senza toccare la logica del codice.

    Novità V6.3.0:
    - [FEATURE] Parametri k-NN aggiunti a SEMANTIC_SETTINGS per il nuovo
      motore VectorStore (vector_store.py + LanceDB).
      knn_k, knn_min_vote_ratio, knn_min_abs_votes sostituiscono la logica
      a centroide e i parametri di spread/min_score ormai deprecati.
    - [DEPRECATO] confidence_threshold, multi_domain_spread, multi_domain_min_score
      rimangono per riferimento ma non sono più letti dal codice di routing.

    Novità V6.2.4:
    - [DEPRECATO] confidence_threshold in SEMANTIC_SETTINGS non è più usato
      come gate di routing. Il parametro rimane per riferimento e debug.

    Novità V6.0:
    - [FEATURE] Aggiunta sezione PIPELINE_SETTINGS per la configurazione
      della pipeline sequenziale multi-agente (query ibride).
"""

import os

# --- 1. GESTIONE PERCORSI (Cross-Platform) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Percorso della cartella keywords/
KEYWORDS_DIR = os.path.join(BASE_DIR, '../keywords')

# --- 2. COSTANTI HARDWARE ---
GB = 1024 * 1024 * 1024  # Byte in 1 GB

RAM_THRESHOLDS = {
    'small':    2.0 * GB,
    'medium':   5.5 * GB,
    'large':   12.0 * GB,
    'math_opt': 1.0 * GB
}

# --- 3. CONFIGURAZIONE MODELLI AI ---
MODELS_CONFIG = {
    'coding': {
        'primary':               "qwen3.5:9b",
        'fallback':              "qwen2.5-coder:1.5b",
        'temperature':           0.5,
        'ram_threshold':         'medium',
        'fallback_ram_threshold':'small'
    },
    'math': {
        'primary':               "deepseek-r1:7b",
        'fallback':              None,
        'temperature':           0.2,
        'ram_threshold':         'math_opt',
        'fallback_ram_threshold': None
    },
    'rights': {
        'primary':               "gpt-oss:20b",
        'fallback':              "llama3.2:3b",
        'temperature':           0.4,
        'ram_threshold':         'large',
        'fallback_ram_threshold':'small'
    },
    'general': {
        'primary':               "gpt-oss:20b",
        'fallback':              "llama3.2:3b",
        'temperature':           0.7,
        'ram_threshold':         'large',
        'fallback_ram_threshold':'small'
    }
}

# --- 4. IMPOSTAZIONI SISTEMA ---
SYSTEM_SETTINGS = {
    'spinner_timeout':  60,
    'ollama_keep_alive': '60s',
    'ctx_size':         4096
}

# --- 5. CONFIGURAZIONE DISPATCHER (SMART MATCH & LEVENSHTEIN) ---
# Usato solo come fallback quando il servizio embedding è non disponibile.

LEV_MIN_LEN = 4

LEV_TOLERANCE_MAP = {
    6:            1,
    10:           2,
    float('inf'): 3
}

# --- 6. CONFIGURAZIONE SEMANTIC ROUTER ---
#
# PARAMETRI DEPRECATI (mantenuti solo per riferimento storico e debug):
# - confidence_threshold: era il gate sul margin coseno (V6.2.3 e precedenti).
# - multi_domain_spread:  era la soglia per lo spread coseno tra domini.
# - multi_domain_min_score: score assoluto minimo del secondo dominio.
# Questi parametri NON sono più letti dal codice di routing (V6.3.0+).
#
# PARAMETRI k-NN ATTIVI (VectorStore V1.0):
# - knn_k: numero di vicini più prossimi estratti per ogni query.
#   Aumentare per maggiore stabilità statistica; ridurre per velocità.
#   Valore consigliato: 10 (bilanciamento precisione/performance).
#
# - knn_min_vote_ratio: percentuale minima di voti che il secondo dominio
#   deve ottenere sul totale combinato (top + second) per attivare la pipeline.
#   Formula: second_votes / (top_votes + second_votes) >= knn_min_vote_ratio
#   Con k=10: 0.30 significa che il secondo dominio deve avere ≥3 voti su 10
#   combinati col primo. Abbassare rende il sistema più sensibile agli ibridi.
#
# - knn_min_abs_votes: numero assoluto minimo di voti del secondo dominio.
#   Questo filtro è la vera difesa contro i falsi ibridi: un dominio con
#   0-2 voti non può mai attivare la pipeline, indipendentemente dal ratio.
#   Con k=10 e min_abs_votes=3: il secondo dominio deve vincere almeno 3
#   query dei 10 vicini più prossimi. È una soglia semanticamente robusta.
#
# - debug: se True, stampa i voti k-NN dettagliati per ogni query.
#   Impostare False in produzione.

SEMANTIC_SETTINGS = {
    'enabled':               True,
    'embedding_model':       'nomic-embed-text',

    # --- Deprecati (V6.2.x) — non più letti dal routing ---
    'confidence_threshold':  0.06,
    'multi_domain_spread':   0.08,
    'multi_domain_min_score':0.58,

    'debug': False,

    # --- Parametri k-NN attivi (V6.3.0 / VectorStore V1.0) ---
    'knn_k':              10,    # vicini da estrarre per query
    'knn_min_vote_ratio': 0.30,  # % minima voti secondo dominio su combined
    'knn_min_abs_votes':  3,     # voti assoluti minimi per il secondo dominio
}

# --- 7. CONFIGURAZIONE PIPELINE MULTI-AGENTE ---
#
# hybrid_threshold:
#   Soglia proporzionale per il keyword fallback (sem_ok=False).
#
# min_words_for_pipeline:
#   Numero minimo di parole per autorizzare l'arco multi-agente.
#   Query sotto soglia vengono degradate a mono-dominio.
#
# pipeline_order_matrix:
#   Ordine autoritativo degli agenti nella pipeline.
#   Criterio primario: chi parla per primo definisce il contesto.
#   - RIGHTS → CODING: la norma vincola l'implementazione tecnica
#   - MATH   → CODING: la formula precede la sua implementazione
#   - RIGHTS → MATH:   la norma determina il calcolo da applicare

PIPELINE_SETTINGS = {
    'hybrid_threshold': 0.30,
    'min_words_for_pipeline': 8,
    'pipeline_order_matrix': {
        frozenset({'rights', 'coding'}): ('rights', 'coding'),
        frozenset({'math',   'coding'}): ('math',   'coding'),
        frozenset({'rights', 'math'}):   ('rights', 'math'),
    }
}
