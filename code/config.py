"""
    CONFIGURAZIONE CENTRALE (CYA N)

    Novità V6.8.0:
    - [STICKY_FIX2] sticky_tech_switch_min abbassato da 0.45 a 0.38.
      Con 0.45, query ibride brevi con confidenza k-NN 0.40 (es. "Teorema di Pitagora"
      classificato ['rights','math'] con conf=0.40) non innescaravano l'override di
      context switch. Il valore 0.38 cattura questi casi mantenendo la protezione
      da false positives (confidenze < 0.38 sono troppo incerte per un switch forzato).

    Novità V6.7.4:
    - [STICKY_FIX] sticky_weak_general_conf aggiunto a SYSTEM_SETTINGS.
    - [STICKY_FIX] sticky_followup_triggers aggiunto a SYSTEM_SETTINGS.

    Novità V6.7.3:
    - [CJK] cjk_filter_enabled aggiunto a SYSTEM_SETTINGS.
    - [CLEANUP] Rimosse chiavi deprecate da SEMANTIC_SETTINGS.

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
    'small':    1.0 * GB,
    'medium':   5.5 * GB,
    'large':   12.0 * GB,
    'math_opt': 2.5 * GB 
}

# --- 3. CONFIGURAZIONE MODELLI AI ---
MODELS_CONFIG = {
    'coding': {
        'primary':                "qwen2.5-coder:1.5b", #qwen 9b
        'fallback':               "qwen2.5-coder:1.5b",
        'temperature':            0.5,
        'ram_threshold':          'medium',
        'fallback_ram_threshold': 'small'
    },
    'math': {
        'primary':                "qwen2.5-coder:1.5b", #deepseek
        'fallback':               None,
        'temperature':            0.2,
        'ram_threshold':          'math_opt',
        'fallback_ram_threshold': None
    },
    'rights': {
        'primary':                "qwen2.5-coder:1.5b", #gpt-oss
        'fallback':               "qwen2.5-coder:1.5b",
        'temperature':            0.4,
        'ram_threshold':          'large',
        'fallback_ram_threshold': 'small'
    },
    'general': {
        'primary':                "qwen2.5-coder:1.5b", #gpt-oss
        'fallback':               "qwen2.5-coder:1.5b",
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
    'think_open_tag':  '<think>',
    'think_close_tag': '</think>',

    # [CHAT] Profondità sliding window della chat history.
    'max_history_turns': 5,

    # [STICKY] Soglia parole per query "corta" -> candidata allo sticky routing.
    'sticky_short_words': 10,

    # [STICKY] Soglia di confidenza k-NN per il context switch verso un dominio
    # tecnico diverso dall'ultimo attivo.
    # [V6.8.0] Abbassato da 0.45 a 0.38: query ibride brevi con conf~0.40
    # (es. "Teorema di Pitagora" classificato ['rights','math']) ora innescano
    # correttamente l'override di context switch invece di restare sticky.
    'sticky_tech_switch_min': 0.38,

    # Soglia confidenza per l'override su query corte (< sticky_short_words).
    # Più alta di sticky_tech_switch_min: su query corte il follow-up è più probabile
    # del context switch, quindi serve un segnale k-NN più forte per forzare lo switch.
    'sticky_short_override_min': 0.65,

    # [STICKY_FIX] Soglia confidenza per il Weak-General Trigger.
    # Se k-NN classifica 'general' con confidenza < questa soglia durante una
    # sessione tecnica attiva, la query è trattata come follow-up discorsivo
    # e il Domain Retention viene mantenuto (solo se keyword del dominio presenti).
    # Range consigliato: 0.60-0.70. Abbassare se troppi false-sticky.
    'sticky_weak_general_conf': 0.65,

    # [STICKY_FIX] Trigger espliciti di follow-up conversazionale in italiano.
    # Se una di queste substring è presente nella query (case-insensitive),
    # il Domain Retention è forzato indipendentemente dalla lunghezza della query.
    # Aggiungere nuove frasi senza modificare il codice.
    'sticky_followup_triggers': [
        'rispiega',
        'non capisco',
        'cosa intendi',
        'cosa significa',
        'come mai hai',
        'perché hai',
        'hai scritto',
        "nel tuo esempio",
        'nel codice',
        'mi spieghi',
        'spiegami meglio',
        'puoi spiegare',
        'dimmi di più',
        'in che senso',
        'cosa vuol dire',
        'approfondisci',
        'vuoi dire che',
        'intendi dire',
        'ma quindi',
        'non mi è chiaro',
        'non è chiaro',
        'ripeti',
        'rispiega',
        'chiariscimi',
    ],

    # [CJK] Filtro caratteri Cinese/Giapponese/Coreano in clean_response().
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
    'min_words_for_pipeline':     12,

    # [P2] Limite caratteri per il contesto passato tra agenti (A->B e critic pass).
    'pipeline_max_context_chars': 9000,

    # [P4] Timeout sincronizzazione RAM tra Agente A e B.
    'ram_sync_timeout':           20.0,
    'ram_unload_wait':            3,

    'pipeline_order_matrix': {
        frozenset({'rights', 'coding'}): ('rights', 'coding'),
        frozenset({'math',   'coding'}): ('math',   'coding'),
        frozenset({'rights', 'math'}):   ('rights', 'math'),
    }
}
