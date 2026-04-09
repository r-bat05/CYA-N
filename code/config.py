"""
    CONFIGURAZIONE CENTRALE (CYA N)

    Questo file contiene tutte le costanti, i percorsi e le impostazioni
    del progetto. Modifica questo file per cambiare modelli, soglie RAM
    o parametri di generazione senza toccare la logica del codice.

    Novità V6.4.0:
    - [UPDATE] knn_min_abs_votes rinominato in knn_min_score per riflettere
      il passaggio al Distance-Weighted k-NN (V1.4 di vector_store.py).
      Il valore non e' piu' un conteggio intero di voti ma uno score decimale
      ponderato sulla distanza. Valore iniziale: 5.0.
    - [DEPRECATO] knn_min_abs_votes rimosso (non piu' letto dal codice).

    Novità V6.3.1:
    - [TUNING] knn_min_abs_votes alzato da 3 a 4.

    Novità V6.3.0:
    - [FEATURE] Parametri k-NN aggiunti a SEMANTIC_SETTINGS per il nuovo
      motore VectorStore (vector_store.py + LanceDB).

    Novità V6.2.4:
    - [DEPRECATO] confidence_threshold in SEMANTIC_SETTINGS non e' piu' usato.

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
# - knn_min_abs_votes: conteggio intero voti (V6.3.x). Sostituito da knn_min_score.
# Questi parametri NON sono piu' letti dal codice di routing (V6.4.0+).
#
# PARAMETRI k-NN ATTIVI (VectorStore V1.4 — Distance-Weighted):
# - knn_k: numero di vicini piu' prossimi estratti per ogni query.
#
# - knn_min_vote_ratio: percentuale minima di score che il secondo dominio
#   deve ottenere sul totale combinato (top + second) per attivare la pipeline.
#   Formula: second_score / (top_score + second_score) >= knn_min_vote_ratio
#
# - knn_min_score: score ponderato minimo del secondo dominio (float).
#   Sostituisce knn_min_abs_votes. Con la formula 1/(dist+0.001):
#     dist ~0.01  -> peso ~90   (clone perfetto)
#     dist ~0.15  -> peso ~6.25 (match buono)
#     dist ~0.50  -> peso ~2.0  (vettore rumore)
#   Valore 5.0: il secondo dominio deve avere almeno un vettore mediamente
#   vicino per attivare la pipeline. Da calibrare con i test empirici.
#
# - debug: se True, stampa gli score k-NN dettagliati per ogni query.

SEMANTIC_SETTINGS = {
    'enabled':               True,
    'embedding_model':       'nomic-embed-text',

    # --- Deprecati (V6.2.x / V6.3.x) — non piu' letti dal routing ---
    'confidence_threshold':  0.06,
    'multi_domain_spread':   0.08,
    'multi_domain_min_score':0.58,

    'debug': True,

    # --- Parametri k-NN attivi (V6.4.0 / VectorStore V1.4) ---
    'knn_k':              10,    # vicini da estrarre per query
    'knn_min_vote_ratio': 0.30,  # % minima score secondo dominio su combined
    'knn_min_score':      7.5,   # score ponderato minimo per il secondo dominio
}

# --- 7. CONFIGURAZIONE PIPELINE MULTI-AGENTE ---
#
# hybrid_threshold:
#   Soglia proporzionale per il keyword fallback (sem_ok=False).
#
# min_words_for_pipeline:
#   Numero minimo di parole per autorizzare l'arco multi-agente.
#
# pipeline_order_matrix:
#   Ordine autoritativo degli agenti nella pipeline.

PIPELINE_SETTINGS = {
    'hybrid_threshold': 0.30,
    'min_words_for_pipeline': 8,
    'pipeline_order_matrix': {
        frozenset({'rights', 'coding'}): ('rights', 'coding'),
        frozenset({'math',   'coding'}): ('math',   'coding'),
        frozenset({'rights', 'math'}):   ('rights', 'math'),
    }
}
