"""
    VECTOR STORE V1.6 — LanceDB Distance-Weighted k-NN Engine

    Novita' V1.6:
    - [BUG1a] Top-Domain Guard bypass per query brevi: se la query ha meno
      parole di sticky_short_words, il guardiano NON degrada a 'general'.
      Il sistema si fida del punteggio vettoriale puro, permettendo a main.py
      di ricevere il dominio tecnico corretto e di innescare il Context Switch.
    - [BUG1b] _keyword_confirm ora integra la Fase 2 (Soft-Match Levenshtein):
      se la Fase 1 (Hard-Match) non produce hit, i token vengono analizzati
      tramite phase2_soft_match_best_domain per variazioni morfologiche
      (es. "integrali" → "integrale", "derivata" → "derivate").
      Questo risolve la Rigidita' del Keyword Confirm che causava degradi
      erronei a 'general' per query con termini al plurale o in forma flessa.
    - [BUG_B] Import di dispatcher_request spostato a livello modulo:
      la funzione _keyword_confirm era nel hot path del routing e chiamava
      lazy import ad ogni invocazione (overhead ripetuto inutilmente).

    Novita' V1.5:
    - [P1] knn_weight_epsilon configurabile.
    - [P3] Supporto BRIDGE_SENTENCES.
"""

import os
import re
import sys
import math
import ollama
from typing import List, Dict, Tuple, Optional

try:
    import lancedb
except ImportError as e:
    raise ImportError(
        "VectorStore richiede lancedb. Installalo con: pip install lancedb"
    ) from e

import config
from db_query import INTENT_SENTENCES, BRIDGE_SENTENCES

# [BUG_B] Import a livello modulo (era lazy import dentro _keyword_confirm).
# Nessun rischio di import circolare: dispatcher_request importa solo config.
from dispatcher_request import (
    _count_hits,
    keyword_loader,
    get_allowed_errors,
    phase2_soft_match_best_domain,
)

# ---------------------------------------------------------------------------
# COSTANTI
# ---------------------------------------------------------------------------

DB_PATH    = os.path.join(config.BASE_DIR, "vector_db")
TABLE_NAME = "intent_vectors"
VECTOR_DIM = 768  # dimensione output di nomic-embed-text

_DEFAULT_K              = 10
_DEFAULT_MIN_VOTE_RATIO = 0.30
_DEFAULT_MIN_SCORE      = 3.0
_DEFAULT_EPSILON        = 0.1

_table = None

# ---------------------------------------------------------------------------
# UTILITA' VETTORIALI
# ---------------------------------------------------------------------------

def l2_normalize(vec: List[float]) -> List[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return vec
    return [x / norm for x in vec]


def _embed(text: str, model: str) -> Optional[List[float]]:
    try:
        response = ollama.embeddings(model=model, prompt=text)
        return response['embedding']
    except Exception as e:
        print(f"WARNING VectorStore: embedding fallito -> {e}")
        return None


# ---------------------------------------------------------------------------
# KEYWORD CONFIRM (Fase 1 Hard-Match + Fase 2 Soft-Match)
# ---------------------------------------------------------------------------

def _keyword_confirm(text: str, domain: str) -> bool:
    """
    Verifica la presenza di keyword del dominio nel testo.

    [BUG1b FIX] Due fasi:
    1. Hard-Match O(1) tramite _count_hits.
    2. Se Fase 1 restituisce 0 hit, Soft-Match tramite Levenshtein
       (phase2_soft_match_best_domain) sui token rimasti orfani.
       Questo gestisce varianti morfologiche (plurali, coniugazioni).

    I simboli '+' e '#' sono inclusi nella tokenizzazione per supportare
    keyword come 'c++', 'c#' (coerente con dispatcher_request.py).
    """
    kw_map: Dict[str, set] = {
        'coding': keyword_loader.CODING,
        'math':   keyword_loader.MATH,
        'rights': keyword_loader.RIGHTS,
    }
    if domain not in kw_map:
        return False

    s_lower = text.lower()
    tokens  = set(re.findall(r'[a-zA-Z0-9_+#]+', s_lower))

    # --- Fase 1: Hard-Match ---
    if _count_hits(tokens, s_lower, kw_map[domain]) > 0:
        return True

    # --- Fase 2: Soft-Match (Levenshtein) sui token orfani ---
    # Cerchiamo solo nel dominio target (già identificato dal k-NN).
    target_keywords = {domain: kw_map[domain]}
    for token in tokens:
        allowed = get_allowed_errors(len(token))
        if allowed == 0:
            continue
        best = phase2_soft_match_best_domain(token, target_keywords, allowed)
        if best == domain:
            return True

    return False


# ---------------------------------------------------------------------------
# INIZIALIZZAZIONE E ACCESSO AL DB
# ---------------------------------------------------------------------------

def initialize_store() -> bool:
    """
    Inizializza il Vector Store su disco (LanceDB).

    [P3] Processa sia INTENT_SENTENCES (frasi mono-dominio) sia
    BRIDGE_SENTENCES (frasi condivise tra due domini).
    """
    global _table

    model = config.SEMANTIC_SETTINGS['embedding_model']

    try:
        db = lancedb.connect(DB_PATH)
    except Exception as e:
        print(f"ERRORE VectorStore: impossibile connettersi al DB in '{DB_PATH}' -> {e}")
        return False

    # --- Caso 1: tabella gia' esistente ---
    if TABLE_NAME in db.list_tables():
        try:
            _table = db.open_table(TABLE_NAME)
            count  = _table.count_rows()
            print(f"   OK  VectorStore caricato da disco: {count} vettori in '{DB_PATH}'.")
            return True
        except Exception as e:
            print(f"   WARN VectorStore: tabella esistente non apribile ({e}). Ricostruzione...")
            _table = None

    # --- Caso 2: costruzione da zero ---
    total_mono   = sum(len(v) for v in INTENT_SENTENCES.values())
    total_bridge = sum(
        len(sentences) * len(domains)
        for domains, sentences in BRIDGE_SENTENCES.items()
    )
    total_records = total_mono + total_bridge

    print(f"\nCostruzione Vector Store ({total_mono} frasi mono + {total_bridge} record bridge"
          f" = {total_records} totali, salvataggio su disco)...")
    print(f"   Percorso DB: {DB_PATH}")
    print(f"   Questo avviene solo al primo avvio. Gli avvii successivi saranno istantanei.\n")

    records = []
    all_ok  = True

    # --- [STEP 1] Frasi mono-dominio ---
    for domain, sentences in INTENT_SENTENCES.items():
        embedded_count = 0
        for sentence in sentences:
            vec = _embed(sentence, model)
            if vec is None:
                all_ok = False
                continue
            records.append({
                "vector":   l2_normalize(vec),
                "domain":   domain,
                "sentence": sentence
            })
            embedded_count += 1

        status = "OK" if embedded_count == len(sentences) else "WARN"
        print(f"   {status}  [{domain:7s}] {embedded_count}/{len(sentences)} frasi mono embeddate")

    # --- [STEP 2] Frasi bridge (P3) ---
    bridge_totals: Dict[str, int] = {}
    for domain_pair, sentences in BRIDGE_SENTENCES.items():
        pair_label     = f"{domain_pair[0]}<->{domain_pair[1]}"
        embedded_count = 0
        for sentence in sentences:
            vec = _embed(sentence, model)
            if vec is None:
                all_ok = False
                continue
            norm_vec = l2_normalize(vec)
            for domain in domain_pair:
                records.append({
                    "vector":   norm_vec,
                    "domain":   domain,
                    "sentence": sentence
                })
            embedded_count += 1

        expected = len(sentences)
        status   = "OK" if embedded_count == expected else "WARN"
        print(f"   {status}  [bridge {pair_label}] {embedded_count}/{expected} frasi embeddate "
              f"→ {embedded_count * len(domain_pair)} record creati")
        bridge_totals[pair_label] = embedded_count

    if not records:
        print("\nERRORE VectorStore: nessun vettore generato.")
        print("   Verifica che Ollama sia attivo e che il modello 'nomic-embed-text' sia installato.")
        return False

    try:
        _table = db.create_table(TABLE_NAME, data=records, mode="overwrite")
        print(f"\n   OK  VectorStore creato: {len(records)} record totali salvati su disco.\n")
        if not all_ok:
            print("   WARN Alcune frasi non sono state embeddate. Il routing potrebbe essere meno preciso.")
        return True
    except Exception as e:
        print(f"\nERRORE VectorStore: errore durante la creazione della tabella -> {e}")
        _table = None
        return False


def _get_table():
    global _table
    if _table is not None:
        return _table
    try:
        db = lancedb.connect(DB_PATH)
        if TABLE_NAME in db.list_tables():
            _table = db.open_table(TABLE_NAME)
            return _table
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# CLASSIFICAZIONE k-NN (Distance-Weighted)
# ---------------------------------------------------------------------------

def classify_knn(text: str) -> Tuple[List[str], float, bool]:
    """
    Classifica il testo tramite votazione k-NN pesata sulla distanza.

    [BUG1a FIX] Top-Domain Guard: per query brevi (< sticky_short_words parole)
    il guardiano è disabilitato. Il sistema si fida del punteggio vettoriale
    puro, consentendo a main.py di rilevare correttamente il context switch
    (es. "Teorema di Pitagora?" → math, anche senza keyword esatte nel testo).

    [P1] Formula peso: weight = 1.0 / (dist + epsilon)
    Con epsilon=0.1 i pesi sono stabili nell'ordine 1-10.
    """
    k         = config.SEMANTIC_SETTINGS.get('knn_k',              _DEFAULT_K)
    min_ratio = config.SEMANTIC_SETTINGS.get('knn_min_vote_ratio', _DEFAULT_MIN_VOTE_RATIO)
    min_score = config.SEMANTIC_SETTINGS.get('knn_min_score',      _DEFAULT_MIN_SCORE)
    epsilon   = config.SEMANTIC_SETTINGS.get('knn_weight_epsilon', _DEFAULT_EPSILON)
    model     = config.SEMANTIC_SETTINGS['embedding_model']

    # [BUG1a] Soglia brevità query (letta da SYSTEM_SETTINGS per coerenza con main.py)
    short_threshold = config.SYSTEM_SETTINGS.get('sticky_short_words', 7)
    is_short_query  = len(text.split()) < short_threshold

    table = _get_table()
    if table is None:
        print("WARN VectorStore non disponibile. Attivazione fallback a keyword.")
        return ['general'], 0.0, False

    query_vec = _embed(text, model)
    if query_vec is None:
        return ['general'], 0.0, False

    query_vec_norm = l2_normalize(query_vec)

    try:
        results = table.search(query_vec_norm).limit(k).to_list()
    except Exception as e:
        print(f"WARN VectorStore: ricerca k-NN fallita -> {e}")
        return ['general'], 0.0, False

    if not results:
        return ['general'], 0.0, False

    # --- Distance-Weighted Voting ---
    vote_counts: Dict[str, float] = {}
    for row in results:
        domain_val = row['domain']
        dist       = row.get('_distance', 0.0)
        weight     = 1.0 / (dist + epsilon)
        vote_counts[domain_val] = vote_counts.get(domain_val, 0.0) + weight

    ranked        = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
    top_domain,   top_score    = ranked[0]
    second_domain              = ranked[1][0] if len(ranked) > 1 else None
    second_score               = ranked[1][1] if len(ranked) > 1 else 0.0

    total_score = sum(s for _, s in ranked)
    confidence  = top_score / total_score if total_score > 0 else 0.0

    combined = top_score + second_score
    domains  = [top_domain]

    _ratio = round(second_score / combined, 2) if combined else 0.0

    if (second_domain is not None
            and second_score >= min_score
            and _ratio >= min_ratio):
        domains.append(second_domain)
    elif (second_domain is not None
            and second_score >= min_score
            and 0.27 <= _ratio < min_ratio):
        # Soft zone: keyword check (Fase 1 + Fase 2) sul secondo dominio
        if _keyword_confirm(text, second_domain):
            domains.append(second_domain)
            if config.SEMANTIC_SETTINGS.get('debug', False):
                print(f"   [k-NN SOFT ZONE] '{second_domain}' confermato da keyword. Pipeline attivata.")
        elif config.SEMANTIC_SETTINGS.get('debug', False):
            print(f"   [k-NN SOFT ZONE] '{second_domain}' ratio={_ratio} in soft zone, 0 keyword hit. Mono-dominio.")

    # --- Top-domain guard ---
    # [BUG1a FIX] Bypass per query brevi: su query brevi il k-NN è il segnale
    # più affidabile. Forzare 'general' qui causerebbe il falso positivo dello
    # sticky routing (es. "Teorema di Pitagora?" resterebbe su coding).
    if len(domains) == 1 and top_domain != 'general':
        if not is_short_query and not _keyword_confirm(text, top_domain):
            if config.SEMANTIC_SETTINGS.get('debug', False):
                print(f"   [k-NN TOP GUARD] '{top_domain}' ha 0 keyword hit. Fallback → GENERAL.")
            domains = ['general']
        elif is_short_query and config.SEMANTIC_SETTINGS.get('debug', False):
            print(f"   [k-NN TOP GUARD] Query breve ({len(text.split())} parole): "
                  f"guardiano bypassato, fiducia al k-NN puro → '{top_domain}'.")

    if config.SEMANTIC_SETTINGS.get('debug', False):
        print(f"\n   [k-NN DEBUG] Score: { {d: f'{s:.2f}' for d, s in ranked} }")
        print(f"   [k-NN DEBUG] Domini={domains} | Confidence={confidence:.2f} "
              f"| k={k} | epsilon={epsilon} | min_score={min_score:.2f} | min_ratio={min_ratio}")
        if second_domain:
            ratio_str = f"{second_score:.2f}/{combined:.2f} = {_ratio}" if combined else "N/A"
            print(f"   [k-NN DEBUG] Secondo dominio '{second_domain}': "
                  f"score={second_score:.2f}, ratio={ratio_str}, "
                  f"ibrido={'SI' if len(domains) > 1 else 'NO'}")

    return domains, confidence, True


# ---------------------------------------------------------------------------
# ENTRY POINT — Ricostruzione forzata
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Ricostruzione forzata del Vector Store in corso...")
    print(f"   DB path: {DB_PATH}\n")

    try:
        _db = lancedb.connect(DB_PATH)
        if TABLE_NAME in _db.list_tables():
            _db.drop_table(TABLE_NAME)
            print(f"   OK  Tabella '{TABLE_NAME}' rimossa.\n")
        else:
            print(f"   INFO Tabella '{TABLE_NAME}' non presente — sara' creata da zero.\n")
    except Exception as _e:
        print(f"   WARN Impossibile rimuovere la tabella esistente: {_e}")
        print("      Tento comunque la ricostruzione con mode='overwrite'...\n")

    _table = None

    ok = initialize_store()
    sys.exit(0 if ok else 1)
