"""
classifier_config.py — CYA N | Path e costanti condivise del pipeline
classificatore neurale (dataset → embeddings → training → inference →
evaluation). [report_patch.md CFG-1/2/3/4]. Zero dipendenze pesanti
(nessun torch/sentence-transformers): sicuro da importare anche nel
percorso runtime a basso consumo RAM.

[F0-A] RUN_TAG / eval_results_path(): ogni esecuzione di step4_evaluation.py
salva un JSON per-ID (eval_results_<tag>_<set>.json) — è il "baseline congelato"
per il confronto "Guardia" (compare_runs.py). Tag da env CYA_RUN_TAG.
"""

import os
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH           = _BASE_DIR / 'dataset_v2.jsonl'
EMBEDDINGS_PATH         = _BASE_DIR / 'classifier' / 'embeddings_v2.pkl'
WEIGHTS_PATH            = _BASE_DIR / 'classifier' / 'nn_weights.pt'
DIFFICULTY_LABELS_PATH  = _BASE_DIR / 'difficulty_labels.json'
EVAL_DATASET_PATH       = _BASE_DIR / 'eval_dataset.jsonl'

ENCODER_MAX_SEQ_LEN = 256  # default MiniLM = 128: oltre, la coda ([QUERY] / nucleo tecnico) viene troncata
ENCODER_MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
EMBEDDING_DIM       = 384  # deve combaciare con ENCODER_MODEL_NAME

# [F0-A] Tag della run (es. 'base', 'f1d', 'f2_1'). Default 'run'.
RUN_TAG = os.environ.get('CYA_RUN_TAG', '').strip() or 'run'


def eval_results_path(set_name: str, tag: str = None) -> Path:
    """eval_results_<tag>_<set>.json (set = dev|test|all): una run dev e una test
    con lo stesso tag non si sovrascrivono."""
    return _BASE_DIR / f"eval_results_{tag or RUN_TAG}_{set_name}.json"
