"""
classifier_config.py — CYA N | Path e costanti condivise del pipeline
classificatore neurale (dataset → embeddings → training → inference →
evaluation). [report_patch.md CFG-1/2/3/4]. Zero dipendenze pesanti
(nessun torch/sentence-transformers): sicuro da importare anche nel
percorso runtime a basso consumo RAM.
"""

from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH           = _BASE_DIR / 'dataset_v2.jsonl'
EMBEDDINGS_PATH         = _BASE_DIR / 'classifier' / 'embeddings_v2.pkl'
WEIGHTS_PATH            = _BASE_DIR / 'classifier' / 'nn_weights.pt'
DIFFICULTY_LABELS_PATH  = _BASE_DIR / 'difficulty_labels.json'
EVAL_DATASET_PATH       = _BASE_DIR / 'eval_dataset.jsonl'

ENCODER_MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
EMBEDDING_DIM       = 384  # deve combaciare con ENCODER_MODEL_NAME