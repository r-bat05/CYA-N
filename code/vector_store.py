"""
    VECTOR STORE V1.4 — LanceDB Distance-Weighted k-NN Engine

    Novita' V1.4:
    - [FEATURE] Distance-Weighted Voting: abbandonato il conteggio uniforme
      (1 vettore = 1 voto). Ogni vettore estratto dal k-NN contribuisce con un
      peso inversamente proporzionale alla sua distanza spaziale dalla query.
      Formula: weight = 1.0 / (dist + 0.001). L'epsilon 0.001 previene la
      divisione per zero in caso di match testuale esatto (dist ~ 0.0).
    - [FIX] Eliminata la "Tirannia della Maggioranza": un singolo clone perfetto
      (distanza ~0.01, peso ~90) supera numericamente 9 vettori rumore distanti
      (distanza ~0.5, peso ~2 ciascuno, totale ~18).
    - [UPDATE] knn_min_abs_votes rinominato in knn_min_score in config.py.
      Il default interno _DEFAULT_MIN_SCORE riflette il nuovo range decimale.
    - [UPDATE] Log debug aggiornati: "voti" -> "score", valori float a 2 decimali.

    Novita' V1.2:
    - [REFACTOR] Il dizionario INTENT_SENTENCES e' stato separato in `db_query.py`.
    - [FIX] Aggiornato il metodo deprecato table_names() con list_tables().

    Novita' V1.1:
    - [TUNING] Aggiunte 4 frasi anti-trappola a INTENT_SENTENCES.

    V1.0 — LanceDB k-NN Engine:
    Sostituisce il PrototypeStore a centroide (semantic_router.py V2.0).

    Logica di ibridazione (doppia condizione):
    Un secondo dominio viene attivato SOLO SE raggiunge ENTRAMBE:
    - knn_min_score     : score ponderato minimo (es. >= 5.0)
    - knn_min_vote_ratio: % score su combinato top+second (es. >= 30%)
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
from db_query import INTENT_SENTENCES

# ---------------------------------------------------------------------------
# COSTANTI
# ---------------------------------------------------------------------------

DB_PATH    = os.path.join(config.BASE_DIR, "vector_db")
TABLE_NAME = "intent_vectors"
VECTOR_DIM = 768  # dimensione output di nomic-embed-text

_DEFAULT_K              = 10
_DEFAULT_MIN_VOTE_RATIO = 0.30
_DEFAULT_MIN_SCORE      = 5.0

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
# CLASSIFICAZIONE k-NN (Distance-Weighted)
# ---------------------------------------------------------------------------

def classify_knn(text: str) -> Tuple[List[str], float, bool]:
    """
    Classifica il testo tramite votazione k-NN pesata sulla distanza.

    Ogni vettore estratto contribuisce con peso = 1.0 / (dist + 0.001),
    in modo che i cloni ravvicinati dominino sui vettori rumore distanti.
    """
    k         = config.SEMANTIC_SETTINGS.get('knn_k',              _DEFAULT_K)
    min_ratio = config.SEMANTIC_SETTINGS.get('knn_min_vote_ratio', _DEFAULT_MIN_VOTE_RATIO)
    min_score = config.SEMANTIC_SETTINGS.get('knn_min_score',      _DEFAULT_MIN_SCORE)
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

    # --- Distance-Weighted Voting ---
    vote_counts: Dict[str, float] = {}
    for row in results:
        domain_val = row['domain']
        dist = row.get('_distance', 0.0)
        weight = 1.0 / (dist + 0.001)
        vote_counts[domain_val] = vote_counts.get(domain_val, 0.0) + weight

    ranked        = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
    top_domain,   top_score    = ranked[0]
    second_domain              = ranked[1][0] if len(ranked) > 1 else None
    second_score               = ranked[1][1] if len(ranked) > 1 else 0.0

    total_score = sum(s for _, s in ranked)
    confidence  = top_score / total_score if total_score > 0 else 0.0

    combined = top_score + second_score
    domains  = [top_domain]

    if (second_domain is not None
            and second_score >= min_score
            and combined > 0
            and (second_score / combined) >= min_ratio):
        domains.append(second_domain)

    if config.SEMANTIC_SETTINGS.get('debug', False):
        print(f"\n   [k-NN DEBUG] Score: { {d: f'{s:.2f}' for d, s in ranked} }")
        print(f"   [k-NN DEBUG] Domini={domains} | Confidence={confidence:.2f} "
              f"| k={k} | min_score={min_score:.2f} | min_ratio={min_ratio}")
        if second_domain:
            ratio_str = f"{second_score:.2f}/{combined:.2f} = {second_score/combined:.2f}" if combined else "N/A"
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
