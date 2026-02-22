"""
    DISPATCHER NEUTRALE (Data-Driven) - Versione Smart Match V2.0
    
    Refactoring:
    - Utilizza config.py per i percorsi dei file keyword.
    - Mantiene la logica Smart Match (distinzione parola singola vs frase).
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
        
        # Debug opzionale (puoi decommentarlo se vuoi vedere quante parole carica)
        # print(f"[Dispatcher] Caricati: Coding={len(self.CODING)}, Math={len(self.MATH)}, Rights={len(self.RIGHTS)}")

    def _read_file(self, filepath):
        unique_words = set()
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    # Pulisce la riga e la converte in minuscolo
                    clean_line = line.strip().lower()
                    # Ignora righe vuote o commenti (iniziano con #)
                    if clean_line and not clean_line.startswith('#'):
                        unique_words.add(clean_line)
        except FileNotFoundError:
            print(f"⚠️  ATTENZIONE: File keyword non trovato -> {filepath}")
            print(f"    Verifica che la cartella '{config.KEYWORDS_DIR}' esista e contenga i file .txt")
        return unique_words

# Istanza globale (viene creata una sola volta all'avvio)
keyword_loader = KeywordLoader()

def count_smart_matches(text_tokens: set, text_original: str, keywords: set) -> int:
    """
    Conta le corrispondenze usando una logica ibrida:
    - Se la keyword è una parola singola (es. "var"), cerca il match esatto nei token.
    - Se la keyword è una frase (es. "machine learning"), cerca la sottostringa nel testo.
    """
    hits = 0
    for kw in keywords:
        if ' ' in kw:
            # Frase composta: Cerca la sottostringa (es. "diritto civile")
            if kw in text_original:
                hits += 1
        else:
            # Parola singola: Cerca il token esatto (es. "var" trova "var" ma non "variabile")
            if kw in text_tokens:
                hits += 1
    return hits

def classify_segment_fast(segment: str) -> str:
    """
    Classificazione basata sui dati con logica Smart Match.
    """
    s_lower = segment.lower()
    
    # Tokenizzazione: Spezza la frase in parole singole pulite (rimuove punteggiatura)
    # Esempio: "cos'è il var?" -> {'cos', 'è', 'il', 'var'}
    tokens = set(re.findall(r'\w+', s_lower))
    
    # Conteggio Smart usando il loader globale
    coding_hits = count_smart_matches(tokens, s_lower, keyword_loader.CODING)
    math_hits = count_smart_matches(tokens, s_lower, keyword_loader.MATH)
    rights_hits = count_smart_matches(tokens, s_lower, keyword_loader.RIGHTS)
    
    # --- LOGICA DI PRIORITÀ ---
    
    # 1. Priorità assoluta a Rights (per evitare che termini generici coding sovrascrivano il legale)
    if rights_hits > 0: 
        return 'rights'
    
    # 2. Confronto Diretto Coding vs Math
    if coding_hits > math_hits:
        return 'coding'
        
    if math_hits > coding_hits:
        return 'math'

    # 3. Pareggio o Nessuna Keyword -> GENERAL
    return 'general'

def split_and_dispatch(query: str) -> dict:
    """
    Spezza la richiesta in frasi e le classifica.
    Restituisce un dizionario: { 'coding': [...], 'math': [...], ... }
    """
    # Spezza su punto, punto interrogativo e a capo
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