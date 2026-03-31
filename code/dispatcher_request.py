"""
    DISPATCHER NEUTRALE (Data-Driven) - Versione Smart Match V4.2 (Debug Mode)

    Novità V4.2:
    - [FIX] Bug ordine pipeline keyword: la pipeline_order_matrix di config.py
      viene ora applicata come criterio PRIMARIO di ordinamento degli agenti in
      detect_hybrid(), non più come semplice tie-breaker.
      In V4.1, quando primary_hits != secondary_hits, l'ordine era determinato
      dal conteggio degli hit: 3 coding vs 2 rights → coding parlava per primo,
      ignorando la regola architetturale "rights → coding" della matrice.
      Ora la matrice è autoritativa per tutte le coppie definite; il conteggio
      degli hit e la gerarchia diventano fallback esclusivamente per coppie
      non presenti in matrice.
"""

import re
import os
from typing import Optional, Tuple
import config


# Toggle per abilitare/disabilitare i log di debug nel terminale
DEBUG_DISPATCHER = True

def _debug_log(message: str):
    """Traccia un arco informativo a video se il debug è attivo."""
    if DEBUG_DISPATCHER:
        print(f"🔍 [DEBUG DISPATCHER] {message}")


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

        # SHARED_TECH: keyword presenti sia in CODING che in MATH.
        self.SHARED_TECH = self.CODING & self.MATH

    def _read_file(self, filepath) -> set:
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


# Istanza globale — creata una sola volta all'avvio
keyword_loader = KeywordLoader()


# =====================================================================
# MOTORE MATEMATICO: DISTANZA DI LEVENSHTEIN E TOLLERANZA
# =====================================================================

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calcola la distanza di Levenshtein ottimizzata in memoria.
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
                for token in kw.split():
                    matched_tokens.add(token)
        else:
            if kw in tokens:
                hits += 1
                matched_tokens.add(kw)

    return hits, matched_tokens


def _count_hits(tokens: set, text_lower: str, keywords: set) -> int:
    """
    Versione minimale di phase1_hard_match usata dal rilevatore ibrido.
    """
    count = 0
    for kw in keywords:
        if ' ' in kw:
            if kw in text_lower:
                count += 1
        else:
            if kw in tokens:
                count += 1
    return count


def phase2_soft_match_best_domain(orphan: str,
                                   domain_keywords: dict,
                                   allowed_errors: int) -> Optional[str]:
    """
    FASE 2: Soft-Match best-distance tramite distanza di Levenshtein.
    """
    best_domain: Optional[str] = None
    best_dist = allowed_errors + 1  

    for domain, keywords in domain_keywords.items():
        for kw in keywords:
            if ' ' in kw:
                continue  
            if abs(len(orphan) - len(kw)) > allowed_errors:
                continue
            dist = levenshtein_distance(orphan, kw)
            if dist < best_dist:
                best_dist   = dist
                best_domain = domain

    return best_domain


# =====================================================================
# RILEVAMENTO QUERY IBRIDE
# =====================================================================

def detect_hybrid(query: str) -> Tuple[bool, str, str]:
    """
    Determina se una query richiede un arco di pipeline multi-agente.

    Logica di ordinamento (V4.2):
    La pipeline_order_matrix è il criterio PRIMARIO. Se la coppia di domini
    rilevata è presente in matrice, l'ordine viene imposto indipendentemente
    dal conteggio degli hit. Il conteggio e la gerarchia restano attivi solo
    come fallback per coppie non coperte dalla matrice.
    """
    # --- NUOVO: FILTRO DI COMPLESSITÀ (V4.3) ---
    word_count = len(query.split())
    min_words = config.PIPELINE_SETTINGS.get('min_words_for_pipeline', 8)
    if word_count < min_words:
        _debug_log(f"Rilevamento Ibrido annullato: query troppo corta ({word_count} < {min_words} parole).")
        return False, '', ''
    # -------------------------------------------

    s_lower = query.lower()
    tokens  = set(re.findall(r'\w+', s_lower))

    coding_excl_kws = keyword_loader.CODING  - keyword_loader.SHARED_TECH
    math_excl_kws   = keyword_loader.MATH    - keyword_loader.SHARED_TECH

    coding_excl = _count_hits(tokens, s_lower, coding_excl_kws)
    math_excl   = _count_hits(tokens, s_lower, math_excl_kws)
    rights_hits = _count_hits(tokens, s_lower, keyword_loader.RIGHTS)

    domain_scores = {
        'coding': coding_excl,
        'math':   math_excl,
        'rights': rights_hits,
    }
    active = sorted(
        [(d, s) for d, s in domain_scores.items() if s > 0],
        key=lambda x: x[1],
        reverse=True
    )

    if len(active) < 2:
        return False, '', ''

    primary_domain,   primary_hits   = active[0]
    secondary_domain, secondary_hits = active[1]

    total = primary_hits + secondary_hits
    if total == 0:
        return False, '', ''

    threshold       = config.PIPELINE_SETTINGS['hybrid_threshold']
    secondary_ratio = secondary_hits / total
    
    _debug_log(f"Rilevamento Ibrido: Ratio={secondary_ratio:.2f} (Soglia={threshold})")

    if secondary_ratio < threshold:
        return False, '', ''

    # -----------------------------------------------------------------
    # [FIX V4.2] Determinazione ordine agenti:
    # La pipeline_order_matrix è applicata come criterio primario per
    # TUTTE le coppie definite, indipendentemente dal conteggio degli hit.
    # Questo garantisce che regole semantiche architetturali (es. rights → coding)
    # non vengano sovrascritte da una differenza numerica accidentale negli hit.
    # Il fallback hit-count/hierarchy rimane attivo per coppie non in matrice.
    # -----------------------------------------------------------------
    pair   = frozenset({primary_domain, secondary_domain})
    matrix = config.PIPELINE_SETTINGS['pipeline_order_matrix']

    if pair in matrix:
        domain_a, domain_b = matrix[pair]
        _debug_log(f"Ordine imposto da pipeline_order_matrix: {domain_a.upper()} → {domain_b.upper()}")
    else:
        # Fallback: chi ha più hit parla per primo; in parità, usa gerarchia
        if primary_hits != secondary_hits:
            domain_a, domain_b = primary_domain, secondary_domain
        else:
            hierarchy = ['rights', 'coding', 'math', 'general']
            ordered   = sorted(
                [primary_domain, secondary_domain],
                key=lambda d: hierarchy.index(d)
            )
            domain_a, domain_b = ordered[0], ordered[1]
        _debug_log(f"Coppia non in matrice. Ordine da hit/gerarchia: "
                   f"{domain_a.upper()} → {domain_b.upper()}")

    _debug_log(f"Arco Ibrido Confermato: {domain_a} -> {domain_b}")
    return True, domain_a, domain_b


# =====================================================================
# CLASSIFICAZIONE SEGMENTO (routing mono-dominio)
# =====================================================================

def classify_segment(segment: str) -> str:
    """
    Orchestrazione della classificazione in due fasi per un singolo segmento.
    """
    _debug_log("-" * 40)
    _debug_log(f"Valutazione Arco di Routing: '{segment}'")
    
    s_lower = segment.lower()
    tokens  = set(re.findall(r'\w+', s_lower))
    _debug_log(f"Token estratti: {tokens}")

    # --- FASE 1: HARD-MATCH ---
    c_hits, c_matched = phase1_hard_match(tokens, s_lower, keyword_loader.CODING)
    m_hits, m_matched = phase1_hard_match(tokens, s_lower, keyword_loader.MATH)
    r_hits, r_matched = phase1_hard_match(tokens, s_lower, keyword_loader.RIGHTS)

    coding_hits = c_hits
    math_hits   = m_hits
    rights_hits = r_hits

    _debug_log(f"FASE 1 (Hard-Match) - C:{coding_hits} | M:{math_hits} | R:{rights_hits}")

    # Parole orfane: token non matchati in nessun dominio durante la Fase 1.
    all_matched = c_matched | m_matched | r_matched
    orphans     = tokens - all_matched
    
    if orphans:
        _debug_log(f"Orfani per Fase 2: {orphans}")

    # --- FASE 2: SOFT-MATCH (best-distance) ---
    domain_keywords = {
        'rights': keyword_loader.RIGHTS,
        'coding': keyword_loader.CODING,
        'math':   keyword_loader.MATH,
    }

    for orphan in orphans:
        word_len       = len(orphan)
        allowed_errors = get_allowed_errors(word_len)

        if allowed_errors == 0:
            continue

        best = phase2_soft_match_best_domain(orphan, domain_keywords, allowed_errors)
        if best:
            _debug_log(f"FASE 2 (Soft-Match) - '{orphan}' recuperato come -> {best.upper()}")
            if best == 'rights':
                rights_hits += 1
            elif best == 'coding':
                coding_hits += 1
            elif best == 'math':
                math_hits += 1

    # --- LOGICA DI PRIORITÀ (Layer 2) ---
    _debug_log(f"Punteggio Finale Archi - C:{coding_hits} | M:{math_hits} | R:{rights_hits}")

    technical_hits = coding_hits + math_hits

    # 1. Priorità Rights
    if rights_hits > 0 and (rights_hits > technical_hits or technical_hits == 0):
        _debug_log("Esito: RIGHTS (Priorità Normativa/Maggioranza)")
        return 'rights'

    # 2. Confronto diretto Coding vs Math
    if coding_hits > math_hits:
        _debug_log("Esito: CODING (Maggioranza Tecnica)")
        return 'coding'

    if math_hits > coding_hits:
        _debug_log("Esito: MATH (Maggioranza Tecnica)")
        return 'math'

    # 3. Stallo semantico
    if coding_hits == math_hits and math_hits > 0:
        _debug_log("Esito: MATH (Risoluzione Stallo Semantico)")
        return 'math'

    # 4. Nessuna keyword
    _debug_log("Esito: GENERAL (Nessun arco specifico trovato)")
    return 'general'


# =====================================================================
# ENTRY POINT PUBBLICO
# =====================================================================

def split_and_dispatch(query: str) -> dict:
    """
    Spezza la richiesta in segmenti frasali e classifica ciascuno.
    """
    segments = re.split(r'[.?!\n;]', query)

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

        category = classify_segment(segment)
        if category in categorized_segments:
            categorized_segments[category].append(segment)

    return categorized_segments
