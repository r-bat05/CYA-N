"""
precompute_embeddings.py — CYA N | Step 2: Pre-calcolo Embedding
================================================================
Legge dataset_v2.jsonl, codifica ogni query+history con MiniLM-L12-v2,
salva embeddings + label in embeddings_v2.pkl.

[REFACTOR — report_patch.md] Path (CFG-2/3) da classifier_config.py,
lista domini (DUP-2) da domains.py.

NOTA is_followup: letto DIRETTAMENTE dal record (r.get('is_followup')),
mai derivato da keyword/history — assegnato in build_dataset_v2.py da
_fu()/_cd()/_r(). Fail-fast se un record ne è privo.

NOTA history: build_input_str() importata da history_utils.py, stessa
funzione usata da nn_classifier.py in inferenza.
"""

import json
import pickle
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

from history_utils import build_input_str, HISTORY_MAX_TURNS
from domains import MONO_DOMAINS
from classifier_config import DATASET_PATH, EMBEDDINGS_PATH, ENCODER_MODEL_NAME

BATCH_SIZE = 64


def load_dataset(path: Path) -> list[dict]:
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if 'is_followup' not in record:
                raise ValueError(
                    f"Record senza campo 'is_followup' alla riga {line_num}: "
                    f"{record.get('query', '???')!r}. "
                    f"Il campo va assegnato in build_dataset_v2.py tramite _fu()/_cd()/_r()."
                )
            records.append(record)
    return records


def precompute(dataset_path: Path = DATASET_PATH, output_path: Path = EMBEDDINGS_PATH):

    print(f"[1/5] Caricamento dataset: {dataset_path}")
    records = load_dataset(dataset_path)
    n = len(records)
    print(f"      {n} record trovati.")

    print(f"[2/5] Costruzione input strings (history_max_turns={HISTORY_MAX_TURNS})...")
    input_strings = [
        build_input_str(r['query'], r.get('history', []))
        for r in records
    ]

    print(f"[3/5] Caricamento encoder: {ENCODER_MODEL_NAME}")
    encoder = SentenceTransformer(ENCODER_MODEL_NAME)

    print(f"      Encoding {n} stringhe (batch_size={BATCH_SIZE})...")
    embeddings_np = encoder.encode(
        input_strings,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    embeddings = torch.from_numpy(embeddings_np).float()
    print(f"      Shape: {embeddings.shape}")

    print(f"[4/5] Costruzione tensori label...")

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
    )

    difficulty_labels = torch.tensor([r['difficulty'] - 1 for r in records], dtype=torch.long)
    is_followup_labels = torch.tensor(
        [1.0 if r.get('is_followup') else 0.0 for r in records], dtype=torch.float32
    )

    split_indices = {'train': [], 'val': [], 'test': []}
    for i, r in enumerate(records):
        split_indices[r['split']].append(i)

    splits = {k: torch.tensor(v, dtype=torch.long) for k, v in split_indices.items()}

    print(f"[5/5] Salvataggio: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        'embeddings':         embeddings,
        'domain_labels':      domain_labels,
        'difficulty_labels':  difficulty_labels,
        'is_followup_labels': is_followup_labels,
        'splits': splits,
        'input_strings': input_strings,
        'meta': {
            'encoder_model':      ENCODER_MODEL_NAME,
            'n_records':          n,
            'history_max_turns':  HISTORY_MAX_TURNS,
            'normalized':         True,
            'is_followup_source': 'structural_field_in_jsonl',
            'is_followup_positives': int(is_followup_labels.sum()),
            'split_sizes': {k: len(v) for k, v in split_indices.items()},
        },
    }

    with open(output_path, 'wb') as f:
        pickle.dump(payload, f)

    size_mb = output_path.stat().st_size / 1e6

    print(f"\n{'='*50}")
    print(f"EMBEDDINGS SALVATI → {output_path}  ({size_mb:.1f} MB)")
    print(f"{'='*50}")
    print(f"  Record totali    : {n}")
    print(f"  Embedding shape  : {list(embeddings.shape)}")
    print(f"  Split train/val/test: {len(splits['train'])} / {len(splits['val'])} / {len(splits['test'])}")

    print(f"\n  --- DOMAIN LABELS ---")
    for i, name in enumerate(MONO_DOMAINS):   # [DUP-2 FIX]
        cnt = int(domain_labels[:, i].sum())
        print(f"  {name:8s}: {cnt:4d}  ({cnt/n*100:.1f}%)")

    print(f"\n  --- DIFFICULTY ---")
    for i, name in enumerate(['semplice', 'media', 'complessa']):
        cnt = int((difficulty_labels == i).sum())
        print(f"  {name:10s}: {cnt:4d}  ({cnt/n*100:.1f}%)")

    print(f"\n  --- IS_FOLLOWUP (campo strutturale del JSONL) ---")
    pos = int(is_followup_labels.sum())
    print(f"  positivi : {pos}  ({pos/n*100:.1f}%)")
    print(f"  negativi : {n-pos}  ({(n-pos)/n*100:.1f}%)")

    pipeline_cnt = sum(1 for r in records if r.get('is_pipeline'))
    print(f"\n  --- PIPELINE ---")
    print(f"  pipeline records: {pipeline_cnt}  ({pipeline_cnt/n*100:.1f}%)")


if __name__ == '__main__':
    precompute()