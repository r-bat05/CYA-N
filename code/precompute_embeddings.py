"""
precompute_embeddings.py — CYA N | Step 2: Pre-calcolo Embedding
================================================================
Legge dataset_v2.jsonl, codifica query+history con MiniLM-L12-v2 (max_seq_length da
classifier_config), salva embeddings + label (domain, difficulty, is_followup, class)
in embeddings_v2.pkl.

class_labels (v3): id di classe 0..6 (DOMAIN_NAMES) per la selezione del checkpoint
in train_nn.py con la stessa regola dell'inferenza.
NOTA is_followup: letto dal record, mai derivato. build_input_str() da history_utils.py.
"""

import json
import pickle
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

from history_utils import build_input_str, HISTORY_MAX_TURNS
from domains import MONO_DOMAINS, DOMAIN_NAMES
from classifier_config import DATASET_PATH, EMBEDDINGS_PATH, ENCODER_MODEL_NAME, ENCODER_MAX_SEQ_LEN

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


def _class_id(r: dict) -> int:
    """Classe derivata (0-3 mono, 4-6 pipeline) — fail-fast se incoerente."""
    if r['is_pipeline']:
        return DOMAIN_NAMES.index(r['pipeline_type'])
    act = [d for d in MONO_DOMAINS if r['domain_labels'][d] == 1]
    if len(act) != 1:
        raise ValueError(f"Record non-pipeline con {len(act)} domini attivi: {r['query']!r}")
    return MONO_DOMAINS.index(act[0])


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
    print(f"      max_seq_length: {encoder.max_seq_length} -> {ENCODER_MAX_SEQ_LEN}")
    encoder.max_seq_length = ENCODER_MAX_SEQ_LEN

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
        [[float(r['domain_labels'][d]) for d in MONO_DOMAINS] for r in records],
        dtype=torch.float32,
    )
    difficulty_labels = torch.tensor([r['difficulty'] - 1 for r in records], dtype=torch.long)
    is_followup_labels = torch.tensor(
        [1.0 if r.get('is_followup') else 0.0 for r in records], dtype=torch.float32
    )
    class_labels = torch.tensor([_class_id(r) for r in records], dtype=torch.long)

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
        'class_labels':       class_labels,
        'splits': splits,
        'input_strings': input_strings,
        'meta': {
            'encoder_model':      ENCODER_MODEL_NAME,
            'max_seq_length':     ENCODER_MAX_SEQ_LEN,
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
    for i, name in enumerate(MONO_DOMAINS):
        cnt = int(domain_labels[:, i].sum())
        print(f"  {name:8s}: {cnt:4d}  ({cnt/n*100:.1f}%)")

    print(f"\n  --- CLASSI (class_labels) ---")
    for i, name in enumerate(DOMAIN_NAMES):
        cnt = int((class_labels == i).sum())
        print(f"  {name:16s}: {cnt:4d}  ({cnt/n*100:.1f}%)")

    print(f"\n  --- DIFFICULTY ---")
    for i, name in enumerate(['semplice', 'media', 'complessa']):
        cnt = int((difficulty_labels == i).sum())
        print(f"  {name:10s}: {cnt:4d}  ({cnt/n*100:.1f}%)")

    print(f"\n  --- IS_FOLLOWUP (campo strutturale del JSONL) ---")
    pos = int(is_followup_labels.sum())
    print(f"  positivi : {pos}  ({pos/n*100:.1f}%)")
    print(f"  negativi : {n-pos}  ({(n-pos)/n*100:.1f}%)")


if __name__ == '__main__':
    precompute()