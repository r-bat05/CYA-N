"""
    VECTOR STORE V1.2 — LanceDB k-NN Engine

    Novita' V1.2:
    - [REFACTOR] Il dizionario INTENT_SENTENCES è stato separato e spostato in `db_query.py`
      per migliorare la leggibilità e la scalabilità del file principale.
    - [FIX] Aggiornato il metodo deprecato table_names() con list_tables() per
      evitare warning durante la verifica del database.

    Novita' V1.1:
    - [TUNING] Aggiunte 4 frasi anti-trappola a INTENT_SENTENCES per ancorare
      il k-NN su query edge-case identificate durante lo stress test.

    V1.0 — LanceDB k-NN Engine:
    Sostituisce il PrototypeStore a centroide (semantic_router.py V2.0) con un
    database vettoriale su disco e ricerca k-Nearest Neighbors esatti.

    Logica di ibridazione (doppia condizione):
    Un secondo dominio viene attivato SOLO SE raggiunge ENTRAMBE:
    - knn_min_abs_votes  : voti assoluti minimi (es. >= 4 su 10 da V6.3.1)
    - knn_min_vote_ratio : % voti su combinato top+second (es. >= 30%)

    Gestione del ciclo di vita:
    - Primo avvio: il DB non esiste -> initialize_store() lo costruisce
    - Avvii successivi: il DB esiste -> caricamento istantaneo da disco
    - Per forzare una ricostruzione: eseguire `python vector_store.py`
"""

import os
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
from db_query import INTENT_SENTENCES  # <-- Importazione del dizionario separato

# ---------------------------------------------------------------------------
# COSTANTI
# ---------------------------------------------------------------------------

DB_PATH    = os.path.join(config.BASE_DIR, "vector_db")
TABLE_NAME = "intent_vectors"
VECTOR_DIM = 768  # dimensione output di nomic-embed-text

_DEFAULT_K              = 10
_DEFAULT_MIN_VOTE_RATIO = 0.30
_DEFAULT_MIN_ABS_VOTES  = 3

_table = None

# ---------------------------------------------------------------------------
# UTILITA' VETTORIALI
# ---------------------------------------------------------------------------

def l2_normalize(vec: List[float]) -> List[float]:
    """
    Normalizza un vettore alla lunghezza unitaria (norma L2 = 1).
    Con vettori normalizzati, la distanza L2 di LanceDB e' monotonicamente
    equivalente alla distanza coseno, senza richiedere una metrica specifica.
    """
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return vec
    return [x / norm for x in vec]


def _embed(text: str, model: str) -> Optional[List[float]]:
    """Chiama ollama.embeddings e restituisce il vettore grezzo, o None in caso di errore."""
    try:
        response = ollama.embeddings(model=model, prompt=text)
        return response['embedding']
    except Exception as e:
        print(f"WARNING VectorStore: embedding fallito -> {e}")
        return None


# ---------------------------------------------------------------------------
# INIZIALIZZAZIONE E ACCESSO AL DB
# ---------------------------------------------------------------------------

def initialize_store() -> bool:
    """
    Inizializza il Vector Store su disco (LanceDB).
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
            count = _table.count_rows()
            print(f"   OK  VectorStore caricato da disco: {count} vettori in '{DB_PATH}'.")
            return True
        except Exception as e:
            print(f"   WARN VectorStore: tabella esistente non apribile ({e}). Ricostruzione...")
            _table = None

    # --- Caso 2: costruzione da zero ---
    total_sentences = sum(len(v) for v in INTENT_SENTENCES.values())
    print(f"\nCostruzione Vector Store ({total_sentences} frasi totali, salvataggio su disco)...")
    print(f"   Percorso DB: {DB_PATH}")
    print(f"   Questo avviene solo al primo avvio. Gli avvii successivi saranno istantanei.\n")

    records = []
    all_ok = True

    for domain, sentences in INTENT_SENTENCES.items():
        embedded_count = 0
        for sentence in sentences:
            vec = _embed(sentence, model)
            if vec is None:
                all_ok = False
                continue
            norm_vec = l2_normalize(vec)
            records.append({
                "vector": norm_vec,
                "domain": domain,
                "sentence": sentence
            })
            embedded_count += 1

        status = "OK" if embedded_count == len(sentences) else "WARN"
        print(f"   {status}  [{domain:7s}] {embedded_count}/{len(sentences)} frasi embeddate")

    if not records:
        print("\nERRORE VectorStore: nessun vettore generato.")
        print("   Verifica che Ollama sia attivo e che il modello 'nomic-embed-text' sia installato.")
        return False

    try:
        _table = db.create_table(TABLE_NAME, data=records, mode="overwrite")
        print(f"\n   OK  VectorStore creato: {len(records)}/{total_sentences} vettori salvati su disco.\n")
        if not all_ok:
            print("   WARN Alcune frasi non sono state embeddate. Il routing potrebbe essere meno preciso.")
        return True
    except Exception as e:
        print(f"\nERRORE VectorStore: errore durante la creazione della tabella -> {e}")
        _table = None
        return False


def _get_table():
    """
    Restituisce il riferimento alla tabella LanceDB.
    """
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
# CLASSIFICAZIONE k-NN
# ---------------------------------------------------------------------------

def classify_knn(text: str) -> Tuple[List[str], float, bool]:
    """
    Classifica il testo tramite votazione k-NN sui vettori del database.
    """
    k         = config.SEMANTIC_SETTINGS.get('knn_k',              _DEFAULT_K)
    min_ratio = config.SEMANTIC_SETTINGS.get('knn_min_vote_ratio', _DEFAULT_MIN_VOTE_RATIO)
    min_votes = config.SEMANTIC_SETTINGS.get('knn_min_abs_votes',  _DEFAULT_MIN_ABS_VOTES)
    model     = config.SEMANTIC_SETTINGS['embedding_model']

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

    vote_counts: Dict[str, int] = {}
    for row in results:
        domain_val = row['domain']
        vote_counts[domain_val] = vote_counts.get(domain_val, 0) + 1

    ranked        = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
    top_domain,   top_votes   = ranked[0]
    second_domain             = ranked[1][0] if len(ranked) > 1 else None
    second_votes              = ranked[1][1] if len(ranked) > 1 else 0

    total_results = len(results)
    confidence    = top_votes / total_results if total_results > 0 else 0.0

    combined = top_votes + second_votes
    domains  = [top_domain]

    if (second_domain is not None
            and second_votes >= min_votes
            and combined > 0
            and (second_votes / combined) >= min_ratio):
        domains.append(second_domain)

    if config.SEMANTIC_SETTINGS.get('debug', False):
        print(f"\n   [k-NN DEBUG] Voti: { {d: v for d, v in ranked} }")
        print(f"   [k-NN DEBUG] Domini={domains} | Confidence={confidence:.2f} "
              f"| k={k} | min_votes={min_votes} | min_ratio={min_ratio}")
        if second_domain:
            ratio_str = f"{second_votes}/{combined} = {second_votes/combined:.2f}" if combined else "N/A"
            print(f"   [k-NN DEBUG] Secondo dominio '{second_domain}': "
                  f"voti={second_votes}, ratio={ratio_str}, "
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