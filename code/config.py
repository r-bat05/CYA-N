"""
    CONFIGURAZIONE CENTRALE (CYA N)

    Novità V7.2.0 (Difficulty Tier Routing): vedi TIER_ROUTING_SETTINGS

"""

# --- 1. COSTANTI HARDWARE ---
GB = 1024 * 1024 * 1024

RAM_THRESHOLDS = {
    'small':    1 * GB,
    'medium':   5.5 * GB,
    'large':   12.0 * GB,
    # [C2 FIX] Era 0.5GB: INFERIORE a 'small'=1GB nonostante deepseek-r1:7b
    # (primary math, NESSUN fallback) sia più grande di qwen2.5-coder:1.5b
    # e gemma3:4b (entrambi coperti da 'small'). check_resources() passava
    # quasi sempre anche con RAM insufficiente, spostando l'errore da
    # ResourceExhaustedError (pulito) a un Errore Ollama/Generico grezzo in
    # generate(). Valore ricalcolato per coerenza d'ordine con
    # medium(9b→5.5GB) e large(20b→12GB) (~0.6GB/miliardo di parametri
    # osservato su questi due punti): 7B * 0.6 ≈ 4.2GB, arrotondato a 4.5GB
    # con margine di sicurezza. Va verificato con `ollama show deepseek-r1:7b`
    # sulla quantizzazione realmente in uso prima di considerarlo definitivo.
    'math_opt': 4.5 * GB,
}

# --- 2. CONFIGURAZIONE MODELLI AI ---
# [TIER] prompt_tier ('compact' | 'extended'): riflette l'architettura
# FINALE intesa (modelli grandi commentati inline), non la config di test
# attuale dove tutti i 'primary' puntano allo stesso modello piccolo.
# Vedi report_prompt_tiering.md §2 per la motivazione per dominio.
MODELS_CONFIG = {
    'coding': {
        'primary':                "qwen3.5:9b",
        'fallback':               "qwen2.5-coder:1.5b",
        'temperature':            0.5,
        'ram_threshold':          'medium',
        'fallback_ram_threshold': 'small',
        'prompt_tier':            'extended',
    },
    'math': {
        'primary':                "deepseek-r1:7b",
        'fallback':               "deepseek-r1:1.5b",
        'temperature':            0.2,
        'ram_threshold':          'math_opt',
        'fallback_ram_threshold': 'small',
        #DEEPSEEK FA GIA' REASONING INTERNO --> mettere extendend sarebbe ripetitivo
        'prompt_tier':            'compact', 
    },
    'rights': {
        'primary':                "gpt-oss:20b",
        'fallback':               "gemma3:4b",
        'temperature':            0.4,
        'ram_threshold':          'large',
        'fallback_ram_threshold': 'small',
        'prompt_tier':            'extended',
    },
    'general': {
        'primary':                "gpt-oss:20b", 
        'fallback':               "gemma3:4b",
        'temperature':            0.7,
        'ram_threshold':          'large',
        'fallback_ram_threshold': 'small',
        'prompt_tier':            'extended',
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

    # [C1 FIX] Cap in caratteri per singolo messaggio salvato in chat_history
    # (main.py::_update_history). Prima non esisteva alcun limite sulla
    # LUNGHEZZA dei messaggi (solo sul numero, via max_history_turns): con
    # ctx_size=4096 token e fino a 10 messaggi in sliding window (risposte
    # coding con blocchi di codice, spiegazioni rights estese), il system
    # prompt poteva essere troncato in overflow da Ollama senza alcun errore
    # visibile. 1200 char/messaggio lascia margine per system prompt
    # (extended tier + few-shot) + query corrente entro il budget di 4096
    # token (~16000 char stimati per l'italiano/inglese misto).
    'history_message_max_chars': 1200,

    # [CJK] Filtro caratteri Cinese/Giapponese/Coreano in clean_response().
    'cjk_filter_enabled': True,
}

NEURAL_CLASSIFIER_SETTINGS = {
    # Vincolo usato SOLO da train_nn.py per tarare il bias pipeline sul VAL:
    # massimo tasso di query mono classificate come pipeline. Le soglie di decisione
    # (bias pipeline, soglia fallback, soglia followup) NON vivono più qui: sono nel checkpoint.
    'max_false_pipeline_rate': 0.02,
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

# --- 6. TIER ROUTING (Difficulty-based Primary/Fallback) ---
# [DIFF-ROUTING] La difficolta' calcolata dal NN Classifier determina ora
# quale TIER di modello (primary/fallback) viene usato nel dominio già
# instradato da class_id. Politica ORTOGONALE al routing di dominio (che
# resta esclusivamente class_id, vedi Routing Purity V7.0-V7.4): qui si
# decide solo QUALE modello dentro il dominio, mai QUALE dominio.
# difficulty <= fallback_max_difficulty -> fallback SEMPRE, indipendente
# dalla RAM disponibile (query semplice, non serve il modello pesante).
# difficulty >  fallback_max_difficulty -> primary di default, ma
# check_resources() in ai_engine.py mantiene INVARIATO il downgrade di
# sicurezza se la RAM è insufficiente (rete di sicurezza hardware, non
# rimossa).
TIER_ROUTING_SETTINGS = {
    'fallback_max_difficulty': 1,
}