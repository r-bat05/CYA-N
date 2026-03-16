"""
    DISPATCHER NEUTRALE (Data-Driven) - Versione Smart Match V3.2

    Fix/Miglioramenti rispetto a V3.1:
    - [BUG #8] Risolto token leakage delle keyword composte (multi-word):
      i token componenti di una keyword multi-parola matchata vengono ora
      aggiunti a matched_tokens, impedendo che rimangano orfani e
      contribuiscano via soft-match a domini errati (double-counting).
    - [IMPROVEMENT] Soft-Match best-distance: l'assegnazione dell'orfano
      non segue più un ordine di priorità fisso (rights > coding > math),
      ma va al dominio con la keyword a distanza di Levenshtein minima.
      Ogni orfano contribuisce ancora al massimo a UN solo dominio.
    - [MINOR] Delimitatori di split estesi: aggiunti '!' e ';'.
    - [MINOR] Rinominata classify_segment_fast → classify_segment.
      Il nome precedente era fuorviante dopo l'introduzione di Levenshtein.
"""

import re
import os
from typing import Optional
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

    FIX BUG #8: i token componenti delle keyword composte matchate vengono
    aggiunti a matched_tokens. Questo impedisce che "quick" e "sort" (da
    "quick sort") rimangano orfani e vengano erroneamente soft-matchati
    verso altri domini, gonfiandone i contatori.
    """
    hits = 0
    matched_tokens = set()

    for kw in keywords:
        if ' ' in kw:
            if kw in text_original:
                hits += 1
                # FIX BUG #8: marca i token componenti come già gestiti.
                for token in kw.split():
                    matched_tokens.add(token)
        else:
            if kw in tokens:
                hits += 1
                matched_tokens.add(kw)

    return hits, matched_tokens


def phase2_soft_match_best_domain(orphan: str,
                                   domain_keywords: dict,
                                   allowed_errors: int) -> Optional[str]:
    """
    FASE 2: Soft-Match best-distance tramite distanza di Levenshtein.
    Applicato solo alle parole orfane (non matchate in Fase 1).

    Scansiona tutti e tre i domini e assegna l'orfano a quello che contiene
    la keyword con distanza minima. In caso di parità di distanza, vince il
    primo dominio incontrato nell'ordine del dizionario (rights, coding, math),
    coerente con la gerarchia di priorità del sistema.

    Restituisce il nome del dominio vincente, o None se nessun dominio
    ha una keyword entro la soglia di tolleranza.
    """
    best_domain: Optional[str] = None
    best_dist = allowed_errors + 1  # soglia esclusiva: deve essere strettamente < best_dist

    for domain, keywords in domain_keywords.items():
        for kw in keywords:
            if ' ' in kw:
                continue  # il soft-match opera solo su parole singole
            # Cortocircuito: differenza di lunghezza già oltre soglia → skip
            if abs(len(orphan) - len(kw)) > allowed_errors:
                continue
            dist = levenshtein_distance(orphan, kw)
            if dist < best_dist:
                best_dist   = dist
                best_domain = domain

    return best_domain


def classify_segment(segment: str) -> str:
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

    # Parole orfane: token non matchati in nessun dominio durante la Fase 1.
    # Grazie al FIX BUG #8, i token componenti di keyword composte matchate
    # sono già inclusi nei rispettivi matched_tokens e non appariranno qui.
    all_matched = c_matched | m_matched | r_matched
    orphans     = tokens - all_matched

    # --- FASE 2: SOFT-MATCH (best-distance) ---
    # L'ordine del dizionario definisce la priorità in caso di parità di distanza:
    # rights > coding > math. Coerente con la gerarchia della logica di priorità finale.
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
        if best == 'rights':
            rights_hits += 1
        elif best == 'coding':
            coding_hits += 1
        elif best == 'math':
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
    Delimitatori: . ? ! ; e newline.
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
