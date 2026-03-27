"""
    CONFIGURAZIONE CENTRALE (CYA N)

    Questo file contiene tutte le costanti, i percorsi e le impostazioni
    del progetto. Modifica questo file per cambiare modelli, soglie RAM
    o parametri di generazione senza toccare la logica del codice.

    Fix:
    - [TYPO] 'Configuraizone' → 'Configurazione' nel docstring originale.

    Novità V6.0:
    - [FEATURE] Aggiunta sezione PIPELINE_SETTINGS per la configurazione
      della pipeline sequenziale multi-agente (query ibride).
"""

import os

# --- 1. GESTIONE PERCORSI (Cross-Platform) ---
# Calcola automaticamente la cartella dove si trova questo file (code/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Percorso della cartella keywords/ (un livello sopra code/)
KEYWORDS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'keywords')

# --- 2. COSTANTI HARDWARE ---
GB = 1024 * 1024 * 1024  # Byte in 1 GB

# Soglie di RAM richieste per avviare i modelli (Safe Mode).
# Se la RAM disponibile è inferiore a queste soglie, il sistema
# attiva il fallback preventivo o si ferma.
RAM_THRESHOLDS = {
    'small':    2.0 * GB,   # Per Qwen 1.5B / Llama 3.2 3B
    'medium':   5.5 * GB,   # Per Qwen3.5 9B / Qwen2.5-Coder 7B
    'large':   12.0 * GB,   # Per GPT-OSS 20B
    'math_opt': 1.0 * GB    # Soglia bassa specifica per DeepSeek (Math)
}

# --- 3. CONFIGURAZIONE MODELLI AI ---
# Struttura: Categoria → { primario, fallback, temperatura, ram_type }
MODELS_CONFIG = {
    'coding': {
        'primary':               "qwen3.5:9b",
        'fallback':              "qwen2.5-coder:1.5b",
        'temperature':           0.5,    # Connubio tra creatività e rigore (no allucinazioni)
        'ram_threshold':         'medium',
        'fallback_ram_threshold':'small'
    },
    'math': {
        'primary':               "deepseek-r1:7b",
        'fallback':              None,   # Nessun fallback: il reasoning richiede almeno 7B
        'temperature':           0.2,    # Massimo rigore, nessuna creatività
        'ram_threshold':         'math_opt',
        'fallback_ram_threshold': None
    },
    'rights': {
        'primary':               "gpt-oss:20b",
        'fallback':              "llama3.2:3b",
        'temperature':           0.4,    # Leggera creatività, gran rigore per non inventare decreti
        'ram_threshold':         'large',
        'fallback_ram_threshold':'small'
    },
    'general': {
        'primary':               "gpt-oss:20b",
        'fallback':              "llama3.2:3b",
        'temperature':           0.7,    # Linguaggio naturale, simile ai modelli cloud
        'ram_threshold':         'large',
        'fallback_ram_threshold':'small'
    }
}

# --- 4. IMPOSTAZIONI SISTEMA ---
SYSTEM_SETTINGS = {
    'spinner_timeout':  60,     # Secondi prima di un warning (opzionale)

    # Il modello resta in RAM 60s dopo l'ultima risposta.
    # Scelta architetturale deliberata: in vista dell'integrazione della chat
    # history, richieste consecutive sullo stesso dominio sono la norma.
    # Tenere il modello caldo elimina i tempi di ricarica da disco tra un
    # turno e l'altro. Il rischio di contesa RAM su switch rapido di dominio
    # è accettato come caso limite poco frequente rispetto al beneficio.
    'ollama_keep_alive': '60s',

    'ctx_size':         4096    # Finestra di contesto in token
}

# --- 5. CONFIGURAZIONE DISPATCHER (SMART MATCH & LEVENSHTEIN) ---

# Lunghezza minima della parola affinché venga calcolata la distanza di Levenshtein.
# Parole con meno di 4 caratteri (es. "sql", "api", "bug") bypassano il Soft-Match
# richiedendo un'uguaglianza rigorosa. Questo previene che preposizioni comuni
# si trasformino in falsi positivi.
LEV_MIN_LEN = 4

# Mappatura della soglia proporzionale degli errori (Soft-Match).
# Struttura: { lunghezza_massima_parola : numero_errori_tollerati }
# L'algoritmo scorre questo dizionario per stabilire dinamicamente l'arco di
# tolleranza in base alla lunghezza della singola parola orfana dell'utente.
LEV_TOLERANCE_MAP = {
    6:            1,    # Da 4 a 6 caratteri  → max 1 errore  (es. "array" tollera "aray")
    10:           2,    # Da 7 a 10 caratteri → max 2 errori  (es. "funzione" tollera "funzzione")
    float('inf'): 3     # Oltre 10 caratteri  → max 3 errori  (es. "polimorfismo" tollera "polimorfsimo")
}

# --- 6. CONFIGURAZIONE SEMANTIC ROUTER ---
#
# Il Semantic Router usa nomic-embed-text (274 MB via Ollama) per convertire
# query e prototipi di dominio in vettori e selezionare il dominio tramite
# similarità coseno. Si attiva prima del keyword matcher (ibrido).
#
# Prerequisito: ollama pull nomic-embed-text
#
# confidence_threshold:
#   Soglia sul MARGINE tra 1° e 2° classificato.
#   Calibrata a 0.06 su test reale (confidence osservata 0.0781).
#   Abbassare → il router semantico interviene di più (meno fallback a keyword).
#   Alzare    → il router semantico interviene solo sui casi netti.
#
# multi_domain_spread:
#   Se la differenza di score tra 1° e 2° classificato è ≤ questo valore,
#   ENTRAMBI i domini vengono attivati (la query va a due agenti).
#   Usato per query genuinamente ibride (es. coding + rights).
#   Abbassare → multi-dominio solo su query molto ambigue.
#   Alzare    → multi-dominio più frequente (più risposte, più RAM usata).
#
# multi_domain_min_score:
#   Score minimo assoluto che il secondo classificato deve superare
#   per essere incluso nel multi-dominio. Evita di attivare 'general'
#   su query specialistiche dove è strutturalmente sempre basso (~0.50).
#
# Se il modello nomic-embed-text non è disponibile, il sistema degrada
# automaticamente al solo keyword matcher senza crash.
SEMANTIC_SETTINGS = {
    'enabled':               True,
    'embedding_model':       'nomic-embed-text',
    'confidence_threshold':  0.06,   # calibrato su test reale (era 0.10)
    'multi_domain_spread':   0.08,   # attiva multi-dominio se margin ≤ 0.08
    'multi_domain_min_score':0.58,   # score minimo per attivare secondo dominio

    # Se True, stampa in console i punteggi coseno per ogni query.
    # Utile per calibrare le soglie. Impostare False in produzione.
    'debug': False
}

# --- 7. CONFIGURAZIONE PIPELINE MULTI-AGENTE ---
#
# Controlla il comportamento della pipeline sequenziale per query ibride,
# ovvero query che richiedono competenze di due domini contemporaneamente.
#
# hybrid_threshold:
#   Soglia proporzionale sul rapporto tra hit esclusivi del dominio secondario
#   e totale degli hit esclusivi dei due domini coinvolti.
#   Formula: hits_secondario_excl / (hits_primario_excl + hits_secondario_excl) >= threshold
#   Gli hit "esclusivi" escludono le keyword condivise tra coding e math
#   (SHARED_TECH, calcolato dinamicamente in KeywordLoader), che altrimenti
#   gonfierebbero artificialmente lo score del dominio debole.
#
#   Valore 0.30 = punto di partenza calibrato sui 3 esempi numerici di progettazione.
#   Da affinare empiricamente dopo i test su query reali.
#   Abbassare → pipeline attivata più facilmente (più falsi positivi).
#   Alzare    → pipeline attivata solo su query chiaramente ibride.
#
# pipeline_order_matrix:
#   Tie-break per determinare l'ordine A→B quando i due domini hanno
#   lo stesso numero di hit esclusivi. La chiave è un frozenset dei due domini,
#   il valore è la tupla (Agent_A, Agent_B).
#   Logica: chi parla per primo definisce il contesto per il secondo.
#   - RIGHTS → CODING: il codice deve rispettare una norma (GDPR + DB, contratto + nullità)
#   - MATH   → CODING: il codice implementa una formula (ammortamento, norma vettore)
#   - RIGHTS → MATH:   la matematica serve a quantificare un istituto giuridico
#   Nei casi non in matrice (es. coding→rights), l'ordine è determinato dagli score.
PIPELINE_SETTINGS = {
    'hybrid_threshold': 0.30,

    'pipeline_order_matrix': {
        frozenset({'rights', 'coding'}): ('rights', 'coding'),
        frozenset({'math',   'coding'}): ('math',   'coding'),
        frozenset({'rights', 'math'}):   ('rights', 'math'),
    }
}
