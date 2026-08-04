"""
precompute_embeddings.py — CYA N | Step 2: Pre-calcolo Embedding
================================================================
Legge dataset_v2.jsonl, codifica ogni query+history con MiniLM-L12-v2,
salva embeddings + label in embeddings_v2.pkl.

Path attesi (dalla root del progetto):
  INPUT  → code/dataset_v2.jsonl
  OUTPUT → code/classifier/embeddings_v2.pkl

NOTA is_followup
  Il campo is_followup non è presente nel JSONL.
  Viene derivato automaticamente: history non vuota → is_followup=1.
  Risultato: 42 positivi su 1274 (ratio ~1:29).
  Il neural head per is_followup va addestrato con pos_weight alto
  o sostituito con Python heuristics (vedi train_nn.py).
"""

import json
import pickle
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

# ─── CONFIG ───────────────────────────────────────────────────────────────────
ENCODER_MODEL    = 'paraphrase-multilingual-MiniLM-L12-v2'
DATASET_PATH     = Path('code/dataset_v2.jsonl')
OUTPUT_PATH      = Path('code/classifier/embeddings_v2.pkl')
HISTORY_MAX_TURNS = 2   # quante query della history concatenare (da config)
BATCH_SIZE        = 64
# ──────────────────────────────────────────────────────────────────────────────


def build_input_str(query: str, history: list) -> str:
    """
    Costruisce la stringa di input per l'encoder.
    Formato: "[HISTORY] q_{n-2} | q_{n-1} [QUERY] query_corrente"
    Se history è vuota restituisce solo la query.
    """
    if history:
        hist_slice = history[-HISTORY_MAX_TURNS:]
        hist_str = " | ".join(hist_slice)
        return f"[HISTORY] {hist_str} [QUERY] {query}"
    return query


def load_dataset(path: Path) -> list[dict]:
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def precompute(dataset_path: Path = DATASET_PATH, output_path: Path = OUTPUT_PATH):

    # ── 1. Caricamento dataset ───────────────────────────────────────────────
    print(f"[1/5] Caricamento dataset: {dataset_path}")
    records = load_dataset(dataset_path)
    n = len(records)
    print(f"      {n} record trovati.")

    # ── 2. Build input strings ───────────────────────────────────────────────
    print(f"[2/5] Costruzione input strings (history_max_turns={HISTORY_MAX_TURNS})...")
    input_strings = [
        build_input_str(r['query'], r.get('history', []))
        for r in records
    ]

    # ── 3. Encoding ─────────────────────────────────────────────────────────
    print(f"[3/5] Caricamento encoder: {ENCODER_MODEL}")
    encoder = SentenceTransformer(ENCODER_MODEL)

    print(f"      Encoding {n} stringhe (batch_size={BATCH_SIZE})...")
    embeddings_np = encoder.encode(
        input_strings,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,   # L2-normalizzazione in-encoder
    )
    embeddings = torch.from_numpy(embeddings_np).float()   # [N, 384]
    print(f"      Shape: {embeddings.shape}")

    # ── 4. Costruzione tensori label ─────────────────────────────────────────
    print(f"[4/5] Costruzione tensori label...")

    # domain_labels [N, 4] float — multi-label (Sigmoid)
    domain_labels = torch.tensor(
        [
            [
                float(r['domain_labels']['coding']),
                float(r['domain_labels']['math']),
                float(r['domain_labels']['rights']),
                float(r['domain_labels']['general']),
            ]
            for r in records
        ],
        dtype=torch.float32,
    )  # [N, 4]

    # difficulty_labels [N] long — indice di classe per CrossEntropyLoss
    # difficulty nel JSONL è 1/2/3 → convertiamo a 0/1/2
    difficulty_labels = torch.tensor(
        [r['difficulty'] - 1 for r in records],
        dtype=torch.long,
    )  # [N]

    # is_followup_labels [N] float — derivato da history (non presente nel JSONL)
    # ⚠ WARNING: solo 42 positivi su 1274. Usare pos_weight in BCELoss o
    #   sostituire con Python heuristics in nn_classifier.py.
    is_followup_labels = torch.tensor(
        [1.0 if r.get('is_followup') else 0.0 for r in records],
        dtype=torch.float32,
    )  # [N]

    # ── 5. Indici di split ───────────────────────────────────────────────────
    # Il campo 'split' è già nel dataset (train/val/test)
    split_indices = {'train': [], 'val': [], 'test': []}
    for i, r in enumerate(records):
        split_indices[r['split']].append(i)

    splits = {
        k: torch.tensor(v, dtype=torch.long)
        for k, v in split_indices.items()
    }

    # ── 6. Salvataggio ───────────────────────────────────────────────────────
    print(f"[5/5] Salvataggio: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        # tensori principali
        'embeddings':         embeddings,         # [N, 384] float32
        'domain_labels':      domain_labels,      # [N, 4]   float32 multi-label
        'difficulty_labels':  difficulty_labels,  # [N]      int64  (0,1,2)
        'is_followup_labels': is_followup_labels, # [N]      float32 (derivato da history)
        # split indices
        'splits': splits,   # dict: 'train'/'val'/'test' → LongTensor di indici
        # debug
        'input_strings': input_strings,
        # metadati
        'meta': {
            'encoder_model':      ENCODER_MODEL,
            'n_records':          n,
            'history_max_turns':  HISTORY_MAX_TURNS,
            'normalized':         True,
            'is_followup_source': 'derived_from_history',
            'is_followup_positives': int(is_followup_labels.sum()),
            'split_sizes': {k: len(v) for k, v in split_indices.items()},
        },
    }

    with open(output_path, 'wb') as f:
        pickle.dump(payload, f)

    size_mb = output_path.stat().st_size / 1e6

    # ── Report finale ────────────────────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"EMBEDDINGS SALVATI → {output_path}  ({size_mb:.1f} MB)")
    print(f"{'='*50}")
    print(f"  Record totali    : {n}")
    print(f"  Embedding shape  : {list(embeddings.shape)}")
    print(f"  Split train/val/test: "
          f"{len(splits['train'])} / {len(splits['val'])} / {len(splits['test'])}")

    print(f"\n  --- DOMAIN LABELS ---")
    for i, name in enumerate(['coding', 'math', 'rights', 'general']):
        cnt = int(domain_labels[:, i].sum())
        print(f"  {name:8s}: {cnt:4d}  ({cnt/n*100:.1f}%)")

    print(f"\n  --- DIFFICULTY ---")
    for i, name in enumerate(['semplice', 'media', 'complessa']):
        cnt = int((difficulty_labels == i).sum())
        print(f"  {name:10s}: {cnt:4d}  ({cnt/n*100:.1f}%)")

    print(f"\n  --- IS_FOLLOWUP (derivato da history) ---")
    pos = int(is_followup_labels.sum())
    print(f"  positivi : {pos}  ({pos/n*100:.1f}%)")
    print(f"  negativi : {n-pos}  ({(n-pos)/n*100:.1f}%)")
    print(f"  ⚠ ratio molto sbilanciato — usare pos_weight in BCELoss")

    pipeline_cnt = sum(1 for r in records if r.get('is_pipeline'))
    print(f"\n  --- PIPELINE ---")
    print(f"  pipeline records: {pipeline_cnt}  ({pipeline_cnt/n*100:.1f}%)")


if __name__ == '__main__':
    precompute()
