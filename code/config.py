"""
    CONFIGURAZIONE CENTRALE (CYA N)

    Novità V6.5.0:
    - [P1] knn_weight_epsilon aggiunto a SEMANTIC_SETTINGS.
      Sostituisce l'epsilon hardcoded 0.001 in vector_store.py con un valore
      configurabile (default 0.1). Ricalibrato knn_min_score da 7.5 a 3.0
      per il nuovo range di pesi (con epsilon=0.1 i pesi sono nell'ordine 1-10,
      non 2-1000).
    - [P2] pipeline_max_context_chars aggiunto a PIPELINE_SETTINGS.
      Sostituisce il magic number 6000 hardcoded in ai_engine.py.
    - [P2] think_open_tag / think_close_tag aggiunti a SYSTEM_SETTINGS.
      Permettono di cambiare il tag di ragionamento senza toccare ai_engine.py.
    - [P4] ram_sync_timeout aggiunto a PIPELINE_SETTINGS.
      Sostituisce il magic number 20.0 hardcoded in main.py.

    Novità V6.4.0:
    - [UPDATE] knn_min_abs_votes rinominato in knn_min_score (Distance-Weighted).
"""

import os

# --- 1. GESTIONE PERCORSI (Cross-Platform) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS_DIR = os.path.join(BASE_DIR, '../keywords')

# --- 2. COSTANTI HARDWARE ---
GB = 1024 * 1024 * 1024

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
    'ctx_size':         4096,

    # [P2] Tag di ragionamento del modello. Cambiarli qui per supportare
    # modelli alternativi (es. Qwen Reasoning usa <|thought|>...</|thought|>).
    # NOTA: aggiornare anche clean_response() in helper.py se si cambia il tag.
    'think_open_tag':  '<think>',
    'think_close_tag': '</think>',
}

# --- 5. CONFIGURAZIONE DISPATCHER (SMART MATCH & LEVENSHTEIN) ---
LEV_MIN_LEN = 4

LEV_TOLERANCE_MAP = {
    6:            1,
    10:           2,
    float('inf'): 3
}

# --- 6. CONFIGURAZIONE SEMANTIC ROUTER ---
SEMANTIC_SETTINGS = {
    'enabled':               True,
    'embedding_model':       'nomic-embed-text',

    # --- Deprecati (mantenuti per riferimento storico) ---
    'confidence_threshold':  0.06,
    'multi_domain_spread':   0.08,
    'multi_domain_min_score':0.58,

    'debug': True,

    # --- Parametri k-NN attivi (V6.5.0) ---
    'knn_k':              10,

    # [P1] Epsilon per la formula peso = 1 / (dist + epsilon).
    # Valore precedente: 0.001 (causava pesi estremi fino a 1000).
    # Valore attuale:    0.1   (pesi nell'ordine 1–10, molto più stabili).
    # Impatto sul ratio: con epsilon=0.1 e due cloni a dist~0.05, il secondo
    # dominio ottiene weight~6.67 vs il primo ~6.67: ratio=50% → hybrid ✓
    # Con il vecchio epsilon, il ratio collassava a <2% per match esatti.
    'knn_weight_epsilon': 0.1,

    'knn_min_vote_ratio': 0.30,

    # [P1] Ricalibrato da 7.5 a 3.0 per il nuovo range di pesi (epsilon=0.1).
    # Con epsilon=0.1: dist~0.15 → weight~4.0 (era ~6.25 con epsilon=0.001).
    # knn_min_score=3.0 richiede almeno un vettore con dist < 0.23 nel secondo
    # dominio per attivare la pipeline. Calibrare empiricamente se necessario.
    'knn_min_score':      3.0,
}

# --- 7. CONFIGURAZIONE PIPELINE MULTI-AGENTE ---
PIPELINE_SETTINGS = {
    'hybrid_threshold':          0.30,
    'min_words_for_pipeline':    8,

    # [P2] Limite caratteri per il contesto passato tra agenti.
    # Sostituisce il magic number 9000 in ai_engine.py.
    'pipeline_max_context_chars': 9000,

    # [P4] Timeout (secondi) per la sincronizzazione RAM tra Agente A e B.
    # Aumentare su macchine lente o con modelli pesanti (es. 40–60s).
    'ram_sync_timeout':           20.0,

    'pipeline_order_matrix': {
        frozenset({'rights', 'coding'}): ('rights', 'coding'),
        frozenset({'math',   'coding'}): ('math',   'coding'),
        frozenset({'rights', 'math'}):   ('rights', 'math'),
    }
}
