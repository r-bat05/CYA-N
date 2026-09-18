"""
nn_classifier.py — CYA N | Step 5: Neural Classifier Inference Module
=======================================================================
Drop-in replacement di llm_router.py.
Stessa interfaccia pubblica:
    predict(text, history) → (class_id, conf, domain_scores, diff, is_followup)
    unload_router()

[REFACTOR — report_patch.md] DOMAIN_NAMES, PIPELINE_CLASSES,
PIPELINE_ORDER (DUP-2, DUP-3) importati da domains.py; path pesi/encoder
(CFG-1, CFG-3) da classifier_config.py; MultiTaskMLP e chiavi checkpoint
(DUP-1, CFG-5) da model_architecture.py. Nessun impatto comportamentale.

[FIX Criticità 3 — Report Gemini] Rimosso il parametro last_domain da
predict(): mai letto nel body, residuo del vecchio sticky routing.

[FIX Criticità 2 — Report Gemini] unload_router() libera davvero encoder
MiniLM (~470MB) e pesi MLP (del + gc.collect()) — necessario sul vincolo
hardware di sviluppo (8GB RAM).

[FIX Bug A] DOMAIN_THRESHOLD/PIPELINE_PAIR_THRESHOLD lette da
config.NEURAL_CLASSIFIER_SETTINGS (logica a due stadi, vedi _derive_class_id).

[FIX Report Gemini punto 3] _build_input_str() delega a
history_utils.build_input_str(), stessa funzione usata in training.
"""

import time
import gc
import torch
from sentence_transformers import SentenceTransformer
from typing import Tuple, Optional

import config
from history_utils import build_input_str, HISTORY_MAX_TURNS
from domains import DOMAIN_NAMES, PIPELINE_CLASSES, PIPELINE_ORDER
from classifier_config import WEIGHTS_PATH, ENCODER_MODEL_NAME
from model_architecture import (
    MultiTaskMLP,
    CKPT_STATE_DICT_KEY,
    CKPT_TEST_F1_DOMAIN_KEY,
    CKPT_TEST_DIFF_ACC_KEY,
    CKPT_TEST_FOLLOWUP_F1_KEY,
)

_CLASS_TO_NAME = {i: n for i, n in enumerate(DOMAIN_NAMES)}

DOMAIN_THRESHOLD        = config.NEURAL_CLASSIFIER_SETTINGS.get('threshold_mono',     0.35)
PIPELINE_PAIR_THRESHOLD = config.NEURAL_CLASSIFIER_SETTINGS.get('threshold_pipeline', 0.60)

_model:   Optional[MultiTaskMLP]        = None
_encoder: Optional[SentenceTransformer] = None
_loaded:  bool                          = False


def _fmt_metric(value) -> str:
    """[M6 FIX] Evita ValueError/TypeError quando la chiave manca dal checkpoint."""
    return f"{value:.4f}" if isinstance(value, (int, float)) else "N/A"


def _load_model():
    global _model, _encoder, _loaded

    if _loaded:
        return

    if not WEIGHTS_PATH.exists():
        raise FileNotFoundError(
            f"Pesi NN non trovati: {WEIGHTS_PATH}\n"
            "Eseguire prima train_nn.py per generarli."
        )

    print(f"[NN_CLASSIFIER] Caricamento encoder: {ENCODER_MODEL_NAME}")
    _encoder = SentenceTransformer(ENCODER_MODEL_NAME)
    _encoder.eval()

    print(f"[NN_CLASSIFIER] Caricamento pesi: {WEIGHTS_PATH}")
    ckpt = torch.load(str(WEIGHTS_PATH), map_location='cpu', weights_only=False)

    _model = MultiTaskMLP()
    _model.load_state_dict(ckpt[CKPT_STATE_DICT_KEY])
    _model.eval()

    print(f"[NN_CLASSIFIER] Test F1-macro domain : {_fmt_metric(ckpt.get(CKPT_TEST_F1_DOMAIN_KEY))}")
    print(f"[NN_CLASSIFIER] Test difficulty acc  : {_fmt_metric(ckpt.get(CKPT_TEST_DIFF_ACC_KEY))}")
    print(f"[NN_CLASSIFIER] Test is_followup F1  : {_fmt_metric(ckpt.get(CKPT_TEST_FOLLOWUP_F1_KEY))}")

    _loaded = True


def _build_input_str(query: str, history: list) -> str:
    """Estrae le query utente dalla history e delega a history_utils.build_input_str."""
    user_turns = [
        m['content'] for m in history
        if m.get('role') == 'user'
    ][-HISTORY_MAX_TURNS:]   # [ARCH-3 FIX] uso diretto, rimosso alias _HISTORY_TURNS
    return build_input_str(query, user_turns)


def _derive_class_id(
    domain_probs: torch.Tensor,
    candidate_threshold: float = DOMAIN_THRESHOLD,
    pipeline_threshold: float = PIPELINE_PAIR_THRESHOLD,
) -> Tuple[int, float]:
    """
    LOGICA A DUE STADI:
      Stadio 1 (candidate_threshold): domini "in lizza" per una pipeline.
      Stadio 2 (pipeline_threshold): coppia top-2 CONFERMATA pipeline solo
      se ENTRAMBI i probs superano questa soglia più alta; altrimenti
      mono-domain (argmax sui 4).
    CONFIDENCE: pipeline = min(prob_a, prob_b); mono-domain = prob vincente.
    """
    probs_np = domain_probs.cpu().numpy()
    names_4  = DOMAIN_NAMES[:4]   # [DUP-2 FIX]

    tech_candidates = [
        (names_4[i], float(probs_np[i]))
        for i in range(3)
        if probs_np[i] >= candidate_threshold
    ]

    if len(tech_candidates) >= 2:
        tech_sorted = sorted(tech_candidates, key=lambda x: x[1], reverse=True)
        top2 = tech_sorted[:2]
        pair = frozenset({top2[0][0], top2[1][0]})

        if pair in PIPELINE_ORDER and min(top2[0][1], top2[1][1]) >= pipeline_threshold:
            class_id   = PIPELINE_ORDER[pair]
            confidence = min(top2[0][1], top2[1][1])
            return class_id, confidence

    class_id   = int(domain_probs.argmax().item())
    confidence = float(probs_np[class_id])
    return class_id, confidence


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
        t0 = time.time()

        input_str = _build_input_str(text, history)

        with torch.no_grad():
            emb = _encoder.encode(
                [input_str],
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            x = torch.from_numpy(emb).float()

        with torch.no_grad():
            _model.eval()
            logits_dom, logits_diff, logit_fu = _model(x)

        domain_probs = torch.sigmoid(logits_dom.squeeze(0))
        diff_probs   = torch.softmax(logits_diff.squeeze(0), dim=0)
        fu_prob      = torch.sigmoid(logit_fu.squeeze()).item()

        class_id, confidence = _derive_class_id(domain_probs)

        domain_scores = {   # [DUP-2 FIX]
            name: round(float(prob), 4)
            for name, prob in zip(DOMAIN_NAMES[:4], domain_probs)
        }

        difficulty  = int(diff_probs.argmax().item()) + 1
        is_followup = fu_prob >= 0.5

        ms = (time.time() - t0) * 1000
        label = _CLASS_TO_NAME[class_id]
        scores_str = ' | '.join(f"{k}:{v:.3f}" for k, v in domain_scores.items())
        print(f"[NN_CLASSIFIER] {label.upper()} | conf={confidence:.3f} | "
              f"diff={difficulty} | followup={is_followup} (fu_prob={fu_prob:.3f}) | "
              f"scores=[{scores_str}] | {ms:.0f}ms")

        return class_id, confidence, domain_scores, difficulty, is_followup

    except Exception as e:
        print(f"[NN_CLASSIFIER] Errore inference ({e}) → fallback keyword")
        return -1, 0.0, {}, 2, False


def unload_router():
    """Libera esplicitamente encoder MiniLM e pesi MLP dalla RAM Python."""
    global _model, _encoder, _loaded
    if _model is None and _encoder is None:
        return
    del _model, _encoder
    _model, _encoder, _loaded = None, None, False
    gc.collect()
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass