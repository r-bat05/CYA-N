"""
    SEMANTIC ROUTER V3.0

    Wrapper di compatibilità che mantiene l'interfaccia pubblica invariata
    per main.py. Tutta la logica di embedding, indicizzazione e classificazione
    è ora delegata a vector_store.py (LanceDB k-NN).

    V3.0 — Breaking changes interni (interfaccia pubblica invariata):
    - Rimossi: PrototypeStore, cosine_similarity, _average_vectors.
    - Rimosso: dizionario INTENT_SENTENCES (spostato in vector_store.py).
    - classify() è ora un delegato diretto di vector_store.classify_knn().
    - La firma pubblica Tuple[List[str], float, bool] rimane identica alla V2.0.

    Nota sul terzo elemento (bool sem_ok):
    Il significato è invariato: True se il sistema ha prodotto un risultato
    affidabile, False se il servizio embedding è fisicamente non disponibile
    e main.py deve attivare il fallback a keyword.
    Con k-NN, sem_ok=False si verifica SOLO se Ollama non risponde, non per
    query con bassa confidenza (che sono gestite internamente dalla logica
    di votazione con min_abs_votes e min_vote_ratio).
"""

from typing import List, Tuple
from vector_store import classify_knn


class SemanticRouter:
    """
    Classificatore semantico basato su k-NN vettoriale (LanceDB).

    Istanza singleton usata da main.py come autorità primaria di routing.
    L'inizializzazione del DB è separata (initialize_store() in vector_store.py)
    e avviene in main() prima del loop principale.
    """

    def classify(self, text: str) -> Tuple[List[str], float, bool]:
        """
        Classifica il testo e restituisce (domini, confidence, sem_ok).

        Delega interamente a vector_store.classify_knn().
        Vedere la docstring di quella funzione per la semantica completa
        dei valori restituiti.
        """
        return classify_knn(text)


# Istanza globale — importata da main.py come:
#   from semantic_router import semantic_router as sem_router
semantic_router = SemanticRouter()
