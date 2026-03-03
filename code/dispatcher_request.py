"""
    DISPATCHER NEUTRALE (Data-Driven) - Versione Smart Match V3.1 (Levenshtein)

    Fix:
    - [BUG #3] Soft-Match: sostituiti tre 'if' indipendenti con 'if/elif/elif'.
      Una parola orfana ora contribuisce al massimo a UN solo dominio per chiamata,
      eliminando l'inflazione artificiale dei contatori.
    - [BUG #7] Priorità 'rights' ricalibrata: non più assoluta su qualsiasi hit.
      Il dominio legale prevale solo se i suoi hit superano la somma degli hit
      tecnici (coding + math), oppure se è l'unico dominio attivato.
      Questo previene che un singolo soft-match su una parola di 4 lettere
      diriga una query tecnica verso il modello legale.
"""

import re
import os
import config


class KeywordLoader:
    """Singleton per il caricamento lazy delle keyword dai file di testo."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KeywordLoader, cls).__new__(cls)
            cls._instance._load_keywords()
        return cls._instance

    def _load_keywords(self):
        keywords_dir = config.KEYWORDS_DIR
        self.CODING = self._read_file(os.path.join(keywords_dir, 'coding.txt'))
        self.MATH   = self._read_file(os.path.join(keywords_dir, 'math.txt'))
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


# Istanza globale — creata una sola volta all'avvio (Pattern Singleton)
keyword_loader = KeywordLoader()


# =====================================================================
# MOTORE MATEMATICO: DISTANZA DI LEVENSHTEIN E TOLLERANZA
# =====================================================================

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calcola la distanza di Levenshtein ottimizzata in memoria (usa solo 2 righe
    della matrice anzichè l'intera griglia NxM).
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions    = previous_row[j + 1] + 1
            deletions     = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def get_allowed_errors(word_len: int) -> int:
    """
    Calcola dinamicamente gli errori ammessi in base alla lunghezza della parola,
    usando la mappa configurata in config.LEV_TOLERANCE_MAP.
    Parole sotto config.LEV_MIN_LEN caratteri richiedono match esatto (0 errori).
    """
    if word_len < config.LEV_MIN_LEN:
        return 0

    for max_len in sorted(config.LEV_TOLERANCE_MAP.keys()):
        if word_len <= max_len:
            return config.LEV_TOLERANCE_MAP[max_len]
    return 0


# =====================================================================
# MOTORE DI RICERCA A DUE FASI (HARD-MATCH → SOFT-MATCH)
# =====================================================================

def phase1_hard_match(tokens: set, text_original: str, keywords: set) -> tuple:
    """
    FASE 1: Match esatto O(1) tramite lookup su set (tabelle hash).
    Restituisce (hit_count, matched_tokens_set).
    - Parole singole: ricerca hash diretta nel set di token.
    - Frasi composte: ricerca sottostringa esatta nel testo normalizzato.
    """
    hits = 0
    matched_tokens = set()

    for kw in keywords:
        if ' ' in kw:
            if kw in text_original:
                hits += 1
        else:
            if kw in tokens:
                hits += 1
                matched_tokens.add(kw)

    return hits, matched_tokens


def phase2_soft_match(orphan: str, keywords: set, allowed_errors: int) -> bool:
    """
    FASE 2: Soft-Match elastico tramite distanza di Levenshtein.
    Applicato solo alle parole orfane (non matchate in Fase 1).
    """
    for kw in keywords:
        if ' ' not in kw:
            # Cortocircuito prestazionale: se la differenza di lunghezza supera già
            # gli errori ammessi, il match è matematicamente impossibile.
            if abs(len(orphan) - len(kw)) > allowed_errors:
                continue
            if levenshtein_distance(orphan, kw) <= allowed_errors:
                return True
    return False


def classify_segment_fast(segment: str) -> str:
    """
    Orchestrazione della classificazione in due fasi per un singolo segmento.
    """
    s_lower = segment.lower()
    tokens  = set(re.findall(r'\w+', s_lower))

    # --- FASE 1: HARD-MATCH ---
    c_hits, c_matched = phase1_hard_match(tokens, s_lower, keyword_loader.CODING)
    m_hits, m_matched = phase1_hard_match(tokens, s_lower, keyword_loader.MATH)
    r_hits, r_matched = phase1_hard_match(tokens, s_lower, keyword_loader.RIGHTS)

    coding_hits = c_hits
    math_hits   = m_hits
    rights_hits = r_hits

    # Parole orfane: token che non hanno trovato match in nessun dominio
    all_matched = c_matched | m_matched | r_matched
    orphans     = tokens - all_matched

    # --- FASE 2: SOFT-MATCH ---
    # FIX BUG #3: 'if/elif/elif' invece di tre 'if' indipendenti.
    # Ogni parola orfana contribuisce al massimo a UN dominio per iterazione,
    # seguendo l'ordine di priorità: rights > coding > math.
    # Questo impedisce che un singolo token infli artificialmente più contatori.
    for orphan in orphans:
        word_len       = len(orphan)
        allowed_errors = get_allowed_errors(word_len)

        if allowed_errors == 0:
            continue

        if phase2_soft_match(orphan, keyword_loader.RIGHTS, allowed_errors):
            rights_hits += 1
        elif phase2_soft_match(orphan, keyword_loader.CODING, allowed_errors):
            coding_hits += 1
        elif phase2_soft_match(orphan, keyword_loader.MATH, allowed_errors):
            math_hits += 1

    # --- LOGICA DI PRIORITÀ ---

    technical_hits = coding_hits + math_hits

    # 1. Priorità Rights — FIX BUG #7: non più assoluta su qualsiasi hit.
    #    Rights prevale solo se:
    #    (a) ha hit E supera la somma degli hit tecnici (query chiaramente legale), oppure
    #    (b) è l'unico dominio attivato (nessun segnale tecnico presente).
    if rights_hits > 0 and (rights_hits > technical_hits or technical_hits == 0):
        return 'rights'

    # 2. Confronto diretto Coding vs Math
    if coding_hits > math_hits:
        return 'coding'

    if math_hits > coding_hits:
        return 'math'

    # 3. Stallo semantico (pareggio con hit > 0): si preferisce Math
    #    per preservare le capacità di reasoning logico-deduttivo.
    if coding_hits == math_hits and math_hits > 0:
        return 'math'

    # 4. Nessuna keyword trovata → GENERAL
    return 'general'


def split_and_dispatch(query: str) -> dict:
    """
    Spezza la richiesta in segmenti frasali e classifica ciascuno.
    Restituisce un dizionario categoria → lista di segmenti.
    """
    segments = re.split(r'[.?\n]', query)

    categorized_segments = {
        'coding':  [],
        'math':    [],
        'rights':  [],
        'general': []
    }

    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        category = classify_segment_fast(segment)
        if category in categorized_segments:
            categorized_segments[category].append(segment)

    return categorized_segments