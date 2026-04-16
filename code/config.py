"""
    CONFIGURAZIONE CENTRALE (CYA N)

    Novità V6.7.0:
    - [STICKY] sticky_short_words e sticky_confidence_threshold aggiunti a
      SYSTEM_SETTINGS per la logica di Domain Retention (Sticky Routing).

    Novità V6.6.0:
    - [CHAT] max_history_turns aggiunto a SYSTEM_SETTINGS.
      Controlla la profondità della sliding window della chat history.
      Impostato a 3 (= 6 messaggi totali) per sicurezza su 8GB RAM con ctx=4096.

    Novità V6.5.0:
    - [P1] knn_weight_epsilon aggiunto a SEMANTIC_SETTINGS.
    - [P2] pipeline_max_context_chars aggiunto a PIPELINE_SETTINGS.
    - [P2] think_open_tag / think_close_tag aggiunti a SYSTEM_SETTINGS.
    - [P4] ram_sync_timeout aggiunto a PIPELINE_SETTINGS.

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

    # [P2] Tag di ragionamento del modello.
    'think_open_tag':  '<think>',
    'think_close_tag': '</think>',

    # [CHAT] Profondità sliding window della chat history.
    # Valore = numero di scambi completi (user+assistant).
    # 3 turni = 6 messaggi totali. Abbassare a 2 su hardware molto limitato.
    'max_history_turns': 3,

    # [STICKY] Soglia parole per query "corta" → candidata allo sticky routing.
    # Query con meno di N parole sono considerate follow-up ad alta probabilità.
    'sticky_short_words': 7,

    # [STICKY] Soglia di confidenza k-NN sotto la quale il risultato è
    # considerato "non affidabile" e lo sticky routing può prevalere.
    # Se il k-NN assegna 'general' con confidenza < questa soglia, si applica
    # il domain retention verso l'ultimo dominio attivo.
    # Range consigliato: 0.55–0.70. Con 0.65 si mantiene sensibilità buona.
    'sticky_confidence_threshold': 0.65,
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
    'knn_weight_epsilon': 0.1,
    'knn_min_vote_ratio': 0.30,
    'knn_min_score':      3.0,
}

# --- 7. CONFIGURAZIONE PIPELINE MULTI-AGENTE ---
PIPELINE_SETTINGS = {
    'hybrid_threshold':          0.30,
    'min_words_for_pipeline':    8,

    # [P2] Limite caratteri per il contesto passato tra agenti.
    'pipeline_max_context_chars': 9000,

    # [P4] Timeout sincronizzazione RAM tra Agente A e B.
    'ram_sync_timeout':           20.0,

    'pipeline_order_matrix': {
        frozenset({'rights', 'coding'}): ('rights', 'coding'),
        frozenset({'math',   'coding'}): ('math',   'coding'),
        frozenset({'rights', 'math'}):   ('rights', 'math'),
    }
}
