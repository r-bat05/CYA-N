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

# [F1-B / RC14] Cap difensivo. main.py salva history fino a 1200 caratteri: con
# ENCODER_MAX_SEQ_LEN=256 token una history lunga troncherebbe la [QUERY] (la parte
# che conta), situazione MAI vista in training (history max 23 parole, totale max 60).
# I cap agiscono SOLO oltre soglia e lasciano il testo BYTE-IDENTICO sotto soglia:
# nessun record del dataset attuale cambia -> embeddings_v2.pkl resta valido
# (verificato con assert su dataset_v2.jsonl: vedi test in consegna).
HISTORY_MAX_WORDS = 30    # training: max osservato 23 parole
QUERY_MAX_WORDS   = 180   # training: max osservato ~60 parole (eval: ~100)
QUERY_HEAD_WORDS  = 40    # oltre il cap si tengono testa (40) + coda (140): il nucleo
                          # tecnico sta spesso in coda (es. N-EXT1)


def _cap_head(text: str, max_words: int) -> str:
    words = text.split()
    return text if len(words) <= max_words else " ".join(words[:max_words])


def cap_query(query: str) -> str:
    words = query.split()
    if len(words) <= QUERY_MAX_WORDS:
        return query
    tail = QUERY_MAX_WORDS - QUERY_HEAD_WORDS
    return " ".join(words[:QUERY_HEAD_WORDS]) + " … " + " ".join(words[-tail:])


def history_text(history_queries: list) -> str:
    """Testo della history (ultimi HISTORY_MAX_TURNS turni, ognuno con cap parole)."""
    hist_slice = [_cap_head(h, HISTORY_MAX_WORDS) for h in history_queries[-HISTORY_MAX_TURNS:]]
    return " | ".join(hist_slice)


def build_input_str(query: str, history_queries: list) -> str:
    """
    Formato: "[HISTORY] q_{n-2} | q_{n-1} [QUERY] query_corrente"
    Se history_queries è vuota, restituisce solo la query.

    Args:
        query: query corrente da classificare.
        history_queries: lista di stringhe — SOLO testo delle query utente
                          precedenti, già estratte dal chiamante.
    """
    query = cap_query(query)
    if history_queries:
        return f"[HISTORY] {history_text(history_queries)} [QUERY] {query}"
    return query
