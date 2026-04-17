"""
    CONFIGURAZIONE CENTRALE (CYA N)

    Novità V6.7.3:
    - [CJK] cjk_filter_enabled aggiunto a SYSTEM_SETTINGS. Toggle per il filtro
      caratteri CJK in helper.py. Default True (comportamento invariato).
      Impostare False per abilitare stringhe asiatiche nei code block.
    - [CLEANUP] Rimosse chiavi deprecate da SEMANTIC_SETTINGS:
      confidence_threshold, multi_domain_spread, multi_domain_min_score.
      Non referenziate in nessun modulo attivo (sostituite dalla logica k-NN).

    Novità V6.7.2:
    - [BUG2] Rimosso sticky_confidence_threshold: dead config.
    - [BUG4] _GUARD in ai_engine ora calcolato su max(open, close) tag length.
    - [BUG5] clean_response ora code-block aware.
    - [BUG6] Think tag regex in helper.py ora dinamica da config.

    Novità V6.7.0:
    - [STICKY] sticky_short_words e sticky_tech_switch_min aggiunti a SYSTEM_SETTINGS.

    Novità V6.6.0:
    - [CHAT] max_history_turns aggiunto a SYSTEM_SETTINGS.

    Novità V6.5.0:
    - [P1] knn_weight_epsilon aggiunto a SEMANTIC_SETTINGS.
    - [P2] pipeline_max_context_chars aggiunto a PIPELINE_SETTINGS.
    - [P2] think_open_tag / think_close_tag aggiunti a SYSTEM_SETTINGS.
    - [P4] ram_sync_timeout aggiunto a PIPELINE_SETTINGS.
"""

import os

# --- 1. GESTIONE PERCORSI (Cross-Platform) ---
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
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
        'primary':                "qwen3.5:9b",
        'fallback':               "qwen2.5-coder:1.5b",
        'temperature':            0.5,
        'ram_threshold':          'medium',
        'fallback_ram_threshold': 'small'
    },
    'math': {
        'primary':                "deepseek-r1:7b",
        'fallback':               None,
        'temperature':            0.2,
        'ram_threshold':          'math_opt',
        'fallback_ram_threshold': None
    },
    'rights': {
        'primary':                "gpt-oss:20b",
        'fallback':               "llama3.2:3b",
        'temperature':            0.4,
        'ram_threshold':          'large',
        'fallback_ram_threshold': 'small'
    },
    'general': {
        'primary':                "gpt-oss:20b",
        'fallback':               "llama3.2:3b",
        'temperature':            0.7,
        'ram_threshold':          'large',
        'fallback_ram_threshold': 'small'
    }
}

# --- 4. IMPOSTAZIONI SISTEMA ---
SYSTEM_SETTINGS = {
    'spinner_timeout':   60,
    'ollama_keep_alive': '60s',
    'ctx_size':          4096,

    # [P2] Tag di ragionamento del modello.
    # Modificare qui per supportare modelli con tag diversi (es. <thinking></thinking>).
    'think_open_tag':  '<think>',
    'think_close_tag': '</think>',

    # [CHAT] Profondità sliding window della chat history.
    # Valore = numero di scambi completi (user+assistant).
    # 3 turni = 6 messaggi totali. Abbassare a 2 su hardware molto limitato.
    'max_history_turns': 3,

    # [STICKY] Soglia parole per query "corta" → candidata allo sticky routing.
    'sticky_short_words': 7,

    # [STICKY] Soglia di confidenza k-NN per il context switch verso un dominio
    # tecnico diverso dall'ultimo attivo.
    # Range consigliato: 0.40–0.55.
    'sticky_tech_switch_min': 0.45,

    # [CJK] Filtro caratteri Cinese/Giapponese/Coreano in clean_response().
    # True  → comportamento default: rimuove CJK dal testo discorsivo.
    # False → disabilitare se si lavora con stringhe asiatiche in code block.
    'cjk_filter_enabled': True,
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
    'enabled':         True,
    'embedding_model': 'nomic-embed-text',

    'debug': True,

    # --- Parametri k-NN attivi ---
    'knn_k':              10,
    'knn_weight_epsilon': 0.1,
    'knn_min_vote_ratio': 0.30,
    'knn_min_score':      3.0,
}

# --- 7. CONFIGURAZIONE PIPELINE MULTI-AGENTE ---
PIPELINE_SETTINGS = {
    'hybrid_threshold':           0.30,
    'min_words_for_pipeline':     8,

    # [P2] Limite caratteri per il contesto passato tra agenti (A→B e critic pass).
    'pipeline_max_context_chars': 9000,

    # [P4] Timeout sincronizzazione RAM tra Agente A e B.
    'ram_sync_timeout':           20.0,

    'pipeline_order_matrix': {
        frozenset({'rights', 'coding'}): ('rights', 'coding'),
        frozenset({'math',   'coding'}): ('math',   'coding'),
        frozenset({'rights', 'math'}):   ('rights', 'math'),
    }
}
