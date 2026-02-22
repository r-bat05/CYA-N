"""
    CONFIGURAZIONE CENTRALE (CYA N)
    
    Questo file contiene tutte le costanti, i percorsi e le impostazioni
    del progetto. Modifica questo file per cambiare modelli, soglie RAM
    o parametri di generazione senza toccare la logica del codice.
"""

import os

# --- 1. GESTIONE PERCORSI (Cross-Platform) ---
# Calcola automaticamente la cartella dove si trova questo file (code/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Percorso della cartella Keywords (un livello sopra code/, poi dentro keywords/)
KEYWORDS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'keywords')

# --- 2. COSTANTI HARDWARE ---
GB = 1024 * 1024 * 1024  # Byte in 1 GB

# Soglie di RAM richieste per avviare i modelli (Safe Mode)
# Se la RAM disponibile è inferiore a queste soglie, il sistema attiva il fallback o si ferma.
RAM_THRESHOLDS = {
    'small': 2.0 * GB,    # Per Qwen 1.5B / Llama 3.2 3B
    'medium': 5.5 * GB,   # Per CodeLlama 7B / Qwen2.5-Coder 7B
    'large': 12.0 * GB,   # Per GPT-OSS 20B
    'math_opt': 1.0 * GB  # Soglia bassa specifica per DeepSeek (Math)
}

# --- 3. CONFIGURAZIONE MODELLI AI ---
# Struttura: Categoria -> {primario, fallback, temperatura, ram_type}
MODELS_CONFIG = {
    'coding': {
        'primary': "qwen2.5-coder:7b",   
        'fallback': "qwen2.5-coder:1.5b",
        'temperature': 0.5, #un buon connubio tra creatività e rigidità delle risposte (no allucinazioni)
        'ram_threshold': 'medium', 
        'fallback_ram_threshold': 'small'
    },
    'math': {
        'primary': "deepseek-r1:7b",
        'fallback': None,  # Nessun fallback per la matematica (richiede reasoning)
        'temperature': 0.2, #massimo rigore nelle risposte, no creatività ma solo procedimenti logici fissi
        'ram_threshold': 'math_opt',
        'fallback_ram_threshold': None
    },
    'rights': {
        'primary': "gpt-oss:20b",
        'fallback': "llama3.2:3b",
        'temperature': 0.4, #leggera creatività ma gran rigore per non inventare concetti/decreti
        'ram_threshold': 'large',
        'fallback_ram_threshold': 'small'
    },
    'general': {
        'primary': "gpt-oss:20b",
        'fallback': "llama3.2:3b",
        'temperature': 0.7, #simile ai modelli AI distribuiti, ottimo per avere un linguaggio più naturale
        'ram_threshold': 'large',
        'fallback_ram_threshold': 'small'
    }
}

# --- 4. IMPOSTAZIONI SISTEMA ---
SYSTEM_SETTINGS = {
    'spinner_timeout': 60,   # Secondi prima di un warning (opzionale)
    'ollama_keep_alive': '60s', # Tempo di permanenza modello in RAM per evitare di caricarlo ad ogni richiesta
    'ctx_size': 4096         # Finestra di contesto token
}