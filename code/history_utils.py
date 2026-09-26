"""
history_utils.py — CYA N | Costruzione canonica dell'input per l'encoder NN
=============================================================================
Unica fonte di verità per la trasformazione (query, history) -> stringa di
input passata a paraphrase-multilingual-MiniLM-L12-v2.

Risolve Criticità #3 del Report Gemini: build_input_str() era duplicata
indipendentemente in precompute_embeddings.py (training) e nn_classifier.py
(inferenza), con firme diverse (list[str] vs list[dict]). Una divergenza
futura anche minima tra le due implementazioni altera l'embedding a 384
dimensioni in modo silenzioso, degradando l'accuratezza in produzione senza
sollevare alcun errore.

Ogni chiamante resta responsabile di estrarre dalla propria struttura dati
nativa la lista di stringhe (query utente precedenti, ordine cronologico)
PRIMA di invocare questa funzione — che non conosce dict, ruoli o JSONL.
"""

HISTORY_MAX_TURNS = 1  # [D1-C] Allineato al training: ogni record del dataset ha al
# massimo 1 query di history (vedi build_dataset_v2.py). Con MAX_TURNS=2 l'inferenza,
# dal 3° messaggio di sessione in poi, costruiva un formato "[HISTORY] q1 | q2 [QUERY]"
# mai visto in training (mismatch train/inference, vedi piano_lavoro_espansione_dataset.md
# §2.6 e §3-D1). Riportare a 2 solo se in futuro si aggiungono seed con history a 2 turni
# (opzione B del piano, rimandata alla Fase 2).


def build_input_str(query: str, history_queries: list) -> str:
    """
    Formato: "[HISTORY] q_{n-2} | q_{n-1} [QUERY] query_corrente"
    Se history_queries è vuota, restituisce solo la query.

    Args:
        query: query corrente da classificare.
        history_queries: lista di stringhe — SOLO testo delle query utente
                          precedenti, già estratte dal chiamante.
    """
    if history_queries:
        hist_slice = history_queries[-HISTORY_MAX_TURNS:]
        hist_str = " | ".join(hist_slice)
        return f"[HISTORY] {hist_str} [QUERY] {query}"
    return query