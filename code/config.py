"""
    CONFIGURAZIONE CENTRALE (CYA N)

    Novità V7.0.0 (Routing purity — output NN come unica fonte):
    - [ROUTING PURITY] Rimossi da SYSTEM_SETTINGS: sticky_short_words,
      sticky_tech_switch_min, sticky_short_override_min. Servivano solo a
      _should_sticky_route() in main.py, rimossa: il dominio instradato è
      ora sempre e solo quello indicato da class_id.
    - [ROUTING PURITY] Rimossi da PIPELINE_SETTINGS: hybrid_threshold
      (già dead code, non referenziato da nessun modulo), min_words_for_pipeline
      e pipeline_order_matrix/pipeline_score_min (servivano solo alla
      declassificazione/promozione pipeline in main.py, rimosse).
    - NEURAL_CLASSIFIER_SETTINGS NON toccato: threshold_mono/threshold_pipeline
      sono usati DENTRO nn_classifier.py per derivare class_id dai domain_probs
      grezzi — fanno parte del meccanismo con cui la NN produce il proprio
      output, non sono un file esterno che lo altera a posteriori.

    Novità V6.9.0 (Cleanup post-branch build_classifier_NN):
    - [CLEANUP] Rimossi BASE_DIR, KEYWORDS_DIR e il relativo import os:
      residuo del vecchio dispatcher a keyword, sostituito interamente
      dal NN Classifier (nn_classifier.py).
"""

# --- 1. COSTANTI HARDWARE ---
GB = 1024 * 1024 * 1024

RAM_THRESHOLDS = {
    'small':    0.5 * GB,
    'medium':   5.5 * GB,
    'large':   12.0 * GB,
    'math_opt': 0.5 * GB #2.5
}

# --- 2. CONFIGURAZIONE MODELLI AI ---
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

# --- 3. IMPOSTAZIONI SISTEMA ---
SYSTEM_SETTINGS = {
    'spinner_timeout':   60,
    'ollama_keep_alive': '60s',
    'ctx_size':          4096,

    # Tag di ragionamento del modello.
    'think_open_tag':  '<think>',
    'think_close_tag': '</think>',

    # [CHAT] Profondità sliding window della chat history.
    'max_history_turns': 5,

    # [CJK] Filtro caratteri Cinese/Giapponese/Coreano in clean_response().
    'cjk_filter_enabled': True,
}

# --- 4. CONFIGURAZIONE NEURAL CLASSIFIER ---
# Soglie interne al meccanismo di decisione della NN (_derive_class_id in
# nn_classifier.py): trasformano i domain_probs grezzi in class_id.
# Fanno parte di COME la rete produce il proprio output, non lo alterano
# a posteriori — per questo restano, a differenza delle soglie rimosse sopra.
NEURAL_CLASSIFIER_SETTINGS = {
    'threshold_mono':     0.35,   # soglia candidatura stadio 1 (permissiva)
    'threshold_pipeline': 0.60,   # soglia conferma coppia stadio 2 (severa)
}

# --- 5. CONFIGURAZIONE PIPELINE MULTI-AGENTE ---
# Solo meccanica di esecuzione (RAM, troncamento contesto) — nessuna soglia
# che decide SE o VERSO QUALE dominio instradare: quella decisione è
# interamente di nn_classifier.py.
PIPELINE_SETTINGS = {
    'pipeline_max_context_chars': 9000,
    'ram_sync_timeout':           20.0,
    'ram_unload_wait':            3,
}