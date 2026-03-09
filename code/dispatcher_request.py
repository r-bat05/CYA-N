"""
    DISPATCHER IBRIDO V4.1 (Semantic + Keyword + Multi-Domain)

    Aggiornamento architetturale V4.1:
    - classify_segment_fast() ora restituisce list[str] invece di str.
      Quando il SemanticRouter rileva una query ibrida (es. coding + rights),
      la lista contiene più di un dominio e lo stesso segmento viene accodato
      a tutti i moduli corrispondenti. main.py non richiede modifiche perché
      itera già su tutti i domini di categories_segments.

    Flusso di classificazione per segmento:
        1. [SEMANTIC]  SemanticRouter.classify() → (list[domini], confidenza)
        2. [CHECK]     confidenza >= soglia?      → ritorna list[domini] semantici
        3. [FALLBACK]  keyword Hard-Match (Phase 1) + Soft-Match (Phase 2)
                       → restituisce sempre [singolo_dominio]

    Precedenti fix mantenuti:
    - [BUG #3] Soft-Match: 'if/elif/elif' — ogni token orfano contribuisce
      al massimo a UN solo dominio per iterazione.
    - [BUG #7] Priorità 'rights' ricalibrata: prevale solo se supera la somma
      degli hit tecnici, o se è l'unico dominio attivato.
"""

import re
import os
import config
from semantic_router import semantic_router


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
    Calcola dinamicamente gli errori ammessi in base alla lunghezza della parola.
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
            if abs(len(orphan) - len(kw)) > allowed_errors:
                continue
            if levenshtein_distance(orphan, kw) <= allowed_errors:
                return True
    return False


def _keyword_classify(segment: str) -> str:
    """
    Classificazione tramite keyword matching (Hard + Soft).
    Estratta come funzione privata, richiamata come fallback dal routing ibrido.
    Restituisce sempre un singolo dominio (stringa).
    """
    s_lower = segment.lower()
    tokens  = set(re.findall(r'\w+', s_lower))

    c_hits, c_matched = phase1_hard_match(tokens, s_lower, keyword_loader.CODING)
    m_hits, m_matched = phase1_hard_match(tokens, s_lower, keyword_loader.MATH)
    r_hits, r_matched = phase1_hard_match(tokens, s_lower, keyword_loader.RIGHTS)

    coding_hits = c_hits
    math_hits   = m_hits
    rights_hits = r_hits

    all_matched = c_matched | m_matched | r_matched
    orphans     = tokens - all_matched

    # FIX BUG #3: if/elif/elif — ogni orfano contribuisce a un solo dominio
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

    technical_hits = coding_hits + math_hits

    # FIX BUG #7: rights non ha più priorità assoluta
    if rights_hits > 0 and (rights_hits > technical_hits or technical_hits == 0):
        return 'rights'
    if coding_hits > math_hits:
        return 'coding'
    if math_hits > coding_hits:
        return 'math'
    if coding_hits == math_hits and math_hits > 0:
        return 'math'

    return 'general'


def classify_segment_fast(segment: str) -> list:
    """
    Orchestrazione del routing ibrido per un singolo segmento.
    Restituisce SEMPRE una list[str] con uno o più domini.

    Fase 0 — Semantic Router (se abilitato in config):
        Converte il segmento in embedding e confronta con i prototipi.
        Se la confidenza supera la soglia, restituisce la lista di domini
        (1 o 2 in caso di query ibrida multi-dominio).

    Fase 1+2 — Keyword Matcher (fallback):
        Attivato quando il Semantic Router è disabilitato, non disponibile,
        o produce una confidenza insufficiente. Restituisce sempre [dominio].
    """
    # --- FASE 0: SEMANTIC ROUTER ---
    if config.SEMANTIC_SETTINGS.get('enabled', False):
        domains, confidence = semantic_router.classify(segment)
        threshold = config.SEMANTIC_SETTINGS.get('confidence_threshold', 0.06)
        if confidence >= threshold:
            return domains

    # --- FASE 1 + 2: KEYWORD MATCHER (fallback) ---
    return [_keyword_classify(segment)]


def split_and_dispatch(query: str) -> dict:
    """
    Spezza la richiesta in segmenti frasali e classifica ciascuno.
    Restituisce un dizionario categoria → lista di segmenti.

    Un singolo segmento può comparire in più categorie se il SemanticRouter
    lo classifica come multi-dominio (es. sia coding che rights).
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

        # classify_segment_fast restituisce list[str] (1 o più domini)
        categories = classify_segment_fast(segment)
        for category in categories:
            if category in categorized_segments:
                categorized_segments[category].append(segment)

    return categorized_segments
