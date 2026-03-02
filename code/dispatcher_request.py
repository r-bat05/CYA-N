"""
    DISPATCHER NEUTRALE (Data-Driven) - Versione Smart Match V3.0 (Levenshtein)
    
    Refactoring:
    - Utilizza config.py per i percorsi dei file keyword e i parametri di tolleranza.
    - Implementa un'architettura a due fasi: Hard-Match O(1) + Soft-Match elastico.
"""

import re
import os
import config # <-- Importa la configurazione centralizzata

class KeywordLoader:
    """ Singleton per il caricamento delle keyword. """
    _instance = None 

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KeywordLoader, cls).__new__(cls)
            cls._instance._load_keywords()
        return cls._instance

    def _load_keywords(self):
        # Utilizza il percorso centralizzato definito in config.py
        keywords_dir = config.KEYWORDS_DIR
        
        # Caricamento liste dai file di testo
        self.CODING = self._read_file(os.path.join(keywords_dir, 'coding.txt'))
        self.MATH = self._read_file(os.path.join(keywords_dir, 'math.txt'))
        self.RIGHTS = self._read_file(os.path.join(keywords_dir, 'rights.txt'))

    def _read_file(self, filepath):
        unique_words = set()
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    clean_line = line.strip().lower()
                    if clean_line and not clean_line.startswith('#'):
                        unique_words.add(clean_line)
        except FileNotFoundError:
            print(f"⚠️  ATTENZIONE: File keyword non trovato -> {filepath}")
        return unique_words

# Istanza globale (viene creata una sola volta all'avvio)
keyword_loader = KeywordLoader()

# =====================================================================
# MOTORE MATEMATICO: DISTANZA DI LEVENSHTEIN E TOLLERANZA
# =====================================================================

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calcola la distanza di Levenshtein ottimizzata in memoria (usa solo 2 righe della matrice).
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def get_allowed_errors(word_len: int) -> int:
    """
    Arco di tolleranza: calcola dinamicamente gli errori ammessi in base 
    alla mappa configurata in config.py.
    """
    if word_len < config.LEV_MIN_LEN:
        return 0
    
    # Ordina le chiavi per garantire la valutazione a gradini (6, 10, inf)
    for max_len in sorted(config.LEV_TOLERANCE_MAP.keys()):
        if word_len <= max_len:
            return config.LEV_TOLERANCE_MAP[max_len]
    return 0

# =====================================================================
# MOTORE DI RICERCA A DUE FASI (HARD-MATCH -> SOFT-MATCH)
# =====================================================================

def phase1_hard_match(tokens: set, text_original: str, keywords: set) -> tuple:
    """
    FASE 1: Match esatto O(1). 
    Restituisce gli hit totali e il Set di token che hanno trovato corrispondenza.
    """
    hits = 0
    matched_tokens = set()
    
    for kw in keywords:
        if ' ' in kw:
            # Frase composta: Ricerca sottostringa esatta
            if kw in text_original:
                hits += 1
        else:
            # Parola singola: Ricerca Hash esatta
            if kw in tokens:
                hits += 1
                matched_tokens.add(kw)
                
    return hits, matched_tokens

def phase2_soft_match(orphan: str, keywords: set, allowed_errors: int) -> bool:
    """
    FASE 2: Soft-Match elastico applicato solo alle parole orfane.
    """
    for kw in keywords:
        # Applica Levenshtein solo alle parole singole
        if ' ' not in kw:
            # Cortocircuito Prestazionale: Se la differenza di lunghezza supera gli errori 
            # ammessi, è matematicamente impossibile che la parola combaci. Si salta il calcolo!
            if abs(len(orphan) - len(kw)) > allowed_errors:
                continue
            
            # Calcolo effettivo dell'arco di trasformazione
            if levenshtein_distance(orphan, kw) <= allowed_errors:
                return True
    return False

def classify_segment_fast(segment: str) -> str:
    """
    Orchestrazione della classificazione in due fasi.
    """
    s_lower = segment.lower()
    tokens = set(re.findall(r'\w+', s_lower))
    
    # --- FASE 1: HARD-MATCH (Veloce) ---
    c_hits, c_matched = phase1_hard_match(tokens, s_lower, keyword_loader.CODING)
    m_hits, m_matched = phase1_hard_match(tokens, s_lower, keyword_loader.MATH)
    r_hits, r_matched = phase1_hard_match(tokens, s_lower, keyword_loader.RIGHTS)
    
    coding_hits = c_hits
    math_hits = m_hits
    rights_hits = r_hits
    
    # Identificazione delle parole orfane (che non hanno matchato nulla in nessun dominio)
    all_matched = c_matched | m_matched | r_matched
    orphans = tokens - all_matched
    
    # --- FASE 2: SOFT-MATCH (Elastico) ---
    for orphan in orphans:
        word_len = len(orphan)
        allowed_errors = get_allowed_errors(word_len)
        
        # Se la parola è troppo corta o non ammette errori, passiamo alla successiva
        if allowed_errors == 0:
            continue
            
        # Tenta il recupero elastico sui tre domini
        if phase2_soft_match(orphan, keyword_loader.RIGHTS, allowed_errors):
            rights_hits += 1
        if phase2_soft_match(orphan, keyword_loader.CODING, allowed_errors):
            coding_hits += 1
        if phase2_soft_match(orphan, keyword_loader.MATH, allowed_errors):
            math_hits += 1

    # --- LOGICA DI PRIORITÀ ---
    
    # 1. Priorità assoluta a Rights
    if rights_hits > 0: 
        return 'rights'
    
    # 2. Confronto Diretto Coding vs Math
    if coding_hits > math_hits:
        return 'coding'
        
    if math_hits > coding_hits:
        return 'math'
        
    # 3. Risoluzione dello Stallo Semantico (Pareggio)
    if coding_hits == math_hits and math_hits > 0:
        return 'math'

    # 4. Nessuna Keyword -> GENERAL
    return 'general'

def split_and_dispatch(query: str) -> dict:
    """
    Spezza la richiesta in frasi e le classifica.
    """
    segments = re.split(r'[.?\n]', query)
    
    categorized_segments = {
        'coding': [],
        'math': [], 
        'rights': [],
        'general': [] 
    }
    
    for segment in segments:
        segment = segment.strip()
        if not segment: continue
        
        category = classify_segment_fast(segment)
        if category in categorized_segments:
            categorized_segments[category].append(segment)
            
    return categorized_segments