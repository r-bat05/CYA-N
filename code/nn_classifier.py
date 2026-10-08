"""
nn_classifier.py — CYA N | Step 5: Neural Classifier Inference Module
=======================================================================
Interfaccia pubblica INVARIATA:
    predict(text, history) → (class_id, conf, domain_scores, diff, is_followup)
    unload_router()

[v4] 3 reti indipendenti (model_architecture.py) in un unico checkpoint.
  - class_id   : argmax a 7 classi + bias pipeline (tarato sul VAL, salvato nel checkpoint).
  - conf       : probabilità softmax della classe scelta.
  - domain_scores (solo diagnostica, per main.py): P(mono) + somma P(pipeline che lo contengono).
  - difficulty : ordinale con soglia fallback (salvata nel checkpoint).
  - is_followup: sigmoid ≥ soglia (salvata nel checkpoint).
Nessuna soglia in config.py: tutti i parametri di decisione vivono nel checkpoint.
"""

import time
import gc
import torch
from sentence_transformers import SentenceTransformer
from typing import Tuple, Optional

from history_utils import build_input_str, HISTORY_MAX_TURNS
from domains import MONO_DOMAINS, DOMAIN_NAMES, PIPELINE_CLASSES
from classifier_config import WEIGHTS_PATH, ENCODER_MODEL_NAME, ENCODER_MAX_SEQ_LEN
from model_architecture import (
    MODEL_CLASSES, CKPT_VERSION, CKPT_VERSION_KEY, CKPT_TASKS,
    CKPT_STATE_KEY, CKPT_PARAMS_KEY, CKPT_METRICS_KEY,
    decide_domain, decide_difficulty,
)

_CLASS_TO_NAME = {i: n for i, n in enumerate(DOMAIN_NAMES)}

_models:  Optional[dict]                = None
_params:  Optional[dict]                = None
_encoder: Optional[SentenceTransformer] = None
_loaded:  bool                          = False


def _fmt_metric(value) -> str:
    return f"{value:.4f}" if isinstance(value, (int, float)) else "N/A"


def _load_model():
    global _models, _params, _encoder, _loaded

    if _loaded:
        return

    if not WEIGHTS_PATH.exists():
        raise FileNotFoundError(
            f"Pesi NN non trovati: {WEIGHTS_PATH}\n"
            "Eseguire prima train_nn.py per generarli."
        )

    print(f"[NN_CLASSIFIER] Caricamento encoder: {ENCODER_MODEL_NAME}")
    _encoder = SentenceTransformer(ENCODER_MODEL_NAME)
    _encoder.max_seq_length = ENCODER_MAX_SEQ_LEN
    _encoder.eval()

    print(f"[NN_CLASSIFIER] Caricamento pesi: {WEIGHTS_PATH}")
    ckpt = torch.load(str(WEIGHTS_PATH), map_location='cpu', weights_only=True)
    if ckpt.get(CKPT_VERSION_KEY) != CKPT_VERSION:
        raise RuntimeError("Checkpoint in formato obsoleto (MultiTaskMLP): rieseguire train_nn.py")

    models, params = {}, {}
    for t in CKPT_TASKS:
        m = MODEL_CLASSES[t]()
        m.load_state_dict(ckpt[t][CKPT_STATE_KEY])
        m.eval()
        models[t] = m
        params[t] = ckpt[t][CKPT_PARAMS_KEY]
        met = ckpt[t].get(CKPT_METRICS_KEY, {})
        print(f"[NN_CLASSIFIER] {t:10s} params={params[t]} | "
              + " | ".join(f"{k}={_fmt_metric(v)}" for k, v in met.items()))

    _models, _params, _loaded = models, params, True


def _build_input_str(query: str, history: list) -> str:
    user_turns = [m['content'] for m in history if m.get('role') == 'user'][-HISTORY_MAX_TURNS:]
    return build_input_str(query, user_turns)


def predict(
    text: str,
    history: list = None,
) -> Tuple[int, float, dict, int, bool]:
    history = history or []

    try:
        _load_model()
    except FileNotFoundError as e:
        print(f"[NN_CLASSIFIER] {e} → fallback keyword")
        return -1, 0.0, {}, 2, False
    except Exception as e:
        print(f"[NN_CLASSIFIER] Errore caricamento ({e}) → fallback keyword")
        return -1, 0.0, {}, 2, False

    try:
        input_str = _build_input_str(text, history)

        with torch.no_grad():
            emb = _encoder.encode([input_str], normalize_embeddings=True, show_progress_bar=False)
            x   = torch.from_numpy(emb).float()
            lg_dom = _models['domain'](x).squeeze(0)        # [7]
            lg_dif = _models['difficulty'](x).squeeze(0)    # [2]
            lg_fu  = _models['followup'](x).reshape(())     # scalare

        probs    = torch.softmax(lg_dom, dim=0)
        class_id = int(decide_domain(lg_dom, _params['domain']['bias_pipe']).item())
        confidence = float(probs[class_id].item())

        scores = {n: float(probs[i]) for i, n in enumerate(MONO_DOMAINS)}
        for cid, (a, b) in PIPELINE_CLASSES.items():
            scores[a] += float(probs[cid])
            scores[b] += float(probs[cid])
        domain_scores = {n: round(v, 4) for n, v in scores.items()}

        difficulty  = int(decide_difficulty(lg_dif, _params['difficulty']['thr_fallback']).item())
        is_followup = bool(torch.sigmoid(lg_fu).item() >= _params['followup']['thr'])

        return class_id, confidence, domain_scores, difficulty, is_followup

    except Exception as e:
        print(f"[NN_CLASSIFIER] Errore inference ({e}) → fallback keyword")
        return -1, 0.0, {}, 2, False


def unload_router():
    """Libera esplicitamente encoder MiniLM e reti dalla RAM Python."""
    global _models, _params, _encoder, _loaded
    if _models is None and _encoder is None:
        return
    _models, _params, _encoder, _loaded = None, None, None, False
    gc.collect()
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
