"""
    CONFIGURAZIONE CENTRALE (CYA N)

    Questo file contiene tutte le costanti, i percorsi e le impostazioni
    del progetto. Modifica questo file per cambiare modelli, soglie RAM
    o parametri di generazione senza toccare la logica del codice.

    Fix:
    - [TYPO] 'Configuraizone' → 'Configurazione' nel docstring originale.

    Novità V6.2.4:
    - [DEPRECATO] confidence_threshold in SEMANTIC_SETTINGS non è più usato
      come gate di routing in main.py. Il router semantico è ora l'autorità
      primaria indipendentemente dal margin tra i due domini classificati.
      Il parametro rimane per riferimento e debug ma non influenza il flusso.
      Vedi semantic_router.py V2.0 e main.py V6.2.4 per i dettagli.

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
# confidence_threshold [DEPRECATO come gate]:
#   In V6.2.3 e precedenti, veniva usato come soglia sul margin tra
#   1° e 2° classificato per decidere se andare a keyword (CASO C).
#   In V6.2.4 questo gate è stato rimosso: un margin basso non indica
#   un fallimento del router, indica una query con due domini vicini
#   (esattamente il caso ibrido). Il router è ora l'autorità primaria.
#   Il parametro rimane per calibrazione/debug ma non influenza il routing.
#
# multi_domain_spread:
#   Se il margin tra 1° e 2° classificato è ≤ questo valore,
#   ENTRAMBI i domini vengono attivati (pipeline multi-agente).
#   Calibrato su test reale. Abbassare → multi-dominio più selettivo.
#
# multi_domain_min_score:
#   Score assoluto minimo che il 2° classificato deve superare
#   per essere incluso nel multi-dominio. Evita di attivare 'general'
#   su query specialistiche dove è strutturalmente sempre basso.
#
# debug:
#   Se True, stampa score coseno dettagliati per ogni query.
#   Impostare False in produzione.
SEMANTIC_SETTINGS = {
    'enabled':               True,
    'embedding_model':       'nomic-embed-text',
    'confidence_threshold':  0.06,   # DEPRECATO come gate — solo riferimento
    'multi_domain_spread':   0.08,   # attiva multi-dominio se margin ≤ 0.08
    'multi_domain_min_score':0.58,   # score minimo assoluto per 2° dominio
    'debug': False
}

# --- 7. CONFIGURAZIONE PIPELINE MULTI-AGENTE ---
#
# hybrid_threshold:
#   Soglia proporzionale per il keyword fallback (sem_ok=False).
#   Formula: hits_secondario_excl / (hits_primario_excl + hits_secondario_excl) >= threshold
#
# min_words_for_pipeline:
#   Numero minimo di parole per autorizzare l'arco multi-agente.
#   Query sotto soglia vengono degradate a mono-dominio anche se
#   il router rileva due domini vicini.
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
