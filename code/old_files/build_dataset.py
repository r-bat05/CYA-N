"""
BUILD DATASET V1.0
Genera dataset.pkl da db_query.py per il training del neural classifier.

Mapping classi:
  0: coding          (mono-domain)
  1: math            (mono-domain)
  2: rights          (mono-domain)
  3: general         (mono-domain)
  4: math->coding    (pipeline bridge coding<->math)
  5: rights->coding  (pipeline bridge coding<->rights)
  6: rights->math    (pipeline bridge math<->rights)

Bridge general<->X: il dominio tecnico vince (general<->math → 1, general<->rights → 2).

Uso: python build_dataset.py
"""

import os
import sys
import pickle
import ollama
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_query import INTENT_SENTENCES, BRIDGE_SENTENCES
import config

EMBEDDING_MODEL = 'nomic-embed-text'
DATASET_PATH    = os.path.join(config.BASE_DIR, 'dataset.pkl')

DOMAIN_TO_CLASS = {
    'coding':  0,
    'math':    1,
    'rights':  2,
    'general': 3,
}

# Pipeline bridges → classe pipeline
BRIDGE_TO_CLASS = {
    frozenset({'coding', 'math'}):   4,  # math->coding
    frozenset({'coding', 'rights'}): 5,  # rights->coding
    frozenset({'math',   'rights'}): 6,  # rights->math
}

# Bridge con general → dominio tecnico (mono-domain)
GENERAL_BRIDGE_CLASS = {
    frozenset({'general', 'math'}):   1,  # -> math
    frozenset({'general', 'rights'}): 2,  # -> rights
}

CLASS_NAMES = ['coding', 'math', 'rights', 'general',
               'math->coding', 'rights->coding', 'rights->math']


def embed(text: str):
    try:
        return ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)['embedding']
    except Exception as e:
        print(f"  WARN embedding fallito: '{text[:60]}' → {e}")
        return None


def main():
    dataset  = []
    n_failed = 0

    print(f"Embedding model : {EMBEDDING_MODEL}")
    print(f"Output          : {DATASET_PATH}\n")

    # --- 1. INTENT_SENTENCES (mono-domain) ---
    for domain, sentences in INTENT_SENTENCES.items():
        cls = DOMAIN_TO_CLASS[domain]
        ok  = 0
        print(f"[{domain.upper()}] {len(sentences)} frasi → classe {cls} ({CLASS_NAMES[cls]})")
        for text in sentences:
            emb = embed(text)
            if emb is not None:
                dataset.append({'embedding': emb, 'label': cls, 'text': text})
                ok += 1
            else:
                n_failed += 1
        print(f"   OK: {ok}/{len(sentences)}\n")

    # --- 2. BRIDGE_SENTENCES ---
    print("[BRIDGE]")
    for pair, sentences in BRIDGE_SENTENCES.items():
        key = frozenset(pair)
        if key in BRIDGE_TO_CLASS:
            cls = BRIDGE_TO_CLASS[key]
        elif key in GENERAL_BRIDGE_CLASS:
            cls = GENERAL_BRIDGE_CLASS[key]
        else:
            print(f"  WARN coppia non mappata: {pair} — saltata.")
            continue

        ok = 0
        print(f"  {pair} → classe {cls} ({CLASS_NAMES[cls]}) | {len(sentences)} frasi")
        for text in sentences:
            emb = embed(text)
            if emb is not None:
                dataset.append({'embedding': emb, 'label': cls, 'text': text})
                ok += 1
            else:
                n_failed += 1
        print(f"   OK: {ok}/{len(sentences)}")

    # --- Report finale ---
    counts = Counter(d['label'] for d in dataset)
    print(f"\nTotale campioni : {len(dataset)}  ({n_failed} falliti)")
    print("Distribuzione classi:")
    for i in range(7):
        bar = '█' * counts.get(i, 0)
        print(f"  [{i}] {CLASS_NAMES[i]:15s}: {counts.get(i, 0):4d}  {bar}")

    with open(DATASET_PATH, 'wb') as f:
        pickle.dump(dataset, f)
    print(f"\nSalvato: {DATASET_PATH}")


if __name__ == '__main__':
    main()
