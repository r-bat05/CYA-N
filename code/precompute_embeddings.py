"""
precompute_embeddings.py — CYA N | Step 2: Pre-calcolo Embedding
================================================================
Legge dataset_v2.jsonl, codifica ogni query+history con MiniLM-L12-v2,
salva embeddings + label in embeddings_v2.pkl.

Path attesi (dalla root del progetto):
  INPUT  → code/dataset_v2.jsonl
  OUTPUT → code/classifier/embeddings_v2.pkl

NOTA is_followup [AGGIORNATO — Report Gemini punto 2]
  Il campo is_followup è presente nel JSONL e viene letto DIRETTAMENTE dal
  record (r.get('is_followup')), NON derivato da keyword o dalla presenza
  della history. È assegnato strutturalmente in build_dataset_v2.py tramite
  i costruttori _fu() (True) e _cd()/_r() (False), all'atto stesso della
  creazione del record. Questo vincolo architetturale è intenzionale e va
  protetto: non reintrodurre MAI derivazioni testuali/euristiche qui.
  Il controllo sotto fa fallire lo script se un record ne è privo, per
  intercettare subito eventuali regressioni nel generatore del dataset.

NOTA history [FIX — Report Gemini punto 3]
  build_input_str() non è più locale: importata da history_utils.py, unica
  fonte di verità condivisa anche con nn_classifier.py in fase di inferenza.
"""

import json
import pickle
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

from history_utils import build_input_str, HISTORY_MAX_TURNS

# ─── CONFIG ───────────────────────────────────────────────────────────────────
ENCODER_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
DATASET_PATH  = Path('code/dataset_v2.jsonl')
OUTPUT_PATH   = Path('code/classifier/embeddings_v2.pkl')
BATCH_SIZE    = 64
# ──────────────────────────────────────────────────────────────────────────────


def load_dataset(path: Path) -> list[dict]:
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            # [FIX Gemini #2] Guardia difensiva: il campo is_followup DEVE
            # esistere ed essere strutturale (bool), mai assente/derivato.
            if 'is_followup' not in record:
                raise ValueError(
                    f"Record senza campo 'is_followup' alla riga {line_num}: "
                    f"{record.get('query', '???')!r}. "
                    f"Il campo va assegnato in build_dataset_v2.py tramite "
                    f"_fu()/_cd()/_r(), mai omesso."
                )
            records.append(record)
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

    difficulty_labels = torch.tensor(
        [r['difficulty'] - 1 for r in records],
        dtype=torch.long,
    )  # [N]

    # [FIX Gemini #2] letto direttamente dal record, non derivato.
    is_followup_labels = torch.tensor(
        [1.0 if r.get('is_followup') else 0.0 for r in records],
        dtype=torch.float32,
    )  # [N]

    # ── 5. Indici di split ───────────────────────────────────────────────────
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
        'embeddings':         embeddings,
        'domain_labels':      domain_labels,
        'difficulty_labels':  difficulty_labels,
        'is_followup_labels': is_followup_labels,
        'splits': splits,
        'input_strings': input_strings,
        'meta': {
            'encoder_model':      ENCODER_MODEL,
            'n_records':          n,
            'history_max_turns':  HISTORY_MAX_TURNS,
            'normalized':         True,
            'is_followup_source': 'structural_field_in_jsonl',  # [FIX doc]
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

    print(f"\n  --- IS_FOLLOWUP (campo strutturale del JSONL) ---")
    pos = int(is_followup_labels.sum())
    print(f"  positivi : {pos}  ({pos/n*100:.1f}%)")
    print(f"  negativi : {n-pos}  ({(n-pos)/n*100:.1f}%)")

    pipeline_cnt = sum(1 for r in records if r.get('is_pipeline'))
    print(f"\n  --- PIPELINE ---")
    print(f"  pipeline records: {pipeline_cnt}  ({pipeline_cnt/n*100:.1f}%)")


if __name__ == '__main__':
    precompute()