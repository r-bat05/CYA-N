"""
nn_classifier.py — CYA N | Step 5: Neural Classifier Inference Module
=======================================================================
Interfaccia pubblica INVARIATA:
    predict(text, history) → (class_id, conf, domain_scores, diff, is_followup)
    unload_router()

[v4] 3 reti indipendenti (model_architecture.py) in un unico checkpoint (versione 4).
  - class_id   : argmax a 7 classi + bias pipeline (tarato sul VAL, salvato nel checkpoint).
  - conf       : probabilità softmax della classe scelta.
  - domain_scores (solo diagnostica, per main.py): P(mono) + somma P(pipeline che lo contengono).
  - difficulty : ordinale con soglia fallback (salvata nel checkpoint).
  - is_followup: sigmoid ≥ soglia (salvata nel checkpoint).
Nessuna soglia in config.py: tutti i parametri di decisione vivono nel checkpoint.

[v5 — report_followup_switch_domain.md]
  F1-A  Gate: is_followup=True è possibile SOLO se esiste almeno un turno utente in history
        (prima: la rete poteva dare True anche con history vuota — N-RAMBLE1, VMN-100, VSH-044).
        Env CYA_FU_GATE=0 disattiva il gate (solo per riprodurre il baseline F0 "puro").
  [v6] Checkpoint v4: un solo modello per task (rimossi ensemble, testa multi-label e 'arch').
        I checkpoint v2/v3 vanno rigenerati con train_nn.py.
  DEBUG LAST_DEBUG: dict aggiornato a ogni predict() con input, has_history, p_followup, thr,
        gate, logit. main.py lo stampa: permette di capire SE un False viene dal gate (history
        vuota) o dalla soglia (p < thr). Nessuna modifica all'interfaccia pubblica.
"""

import gc
import os
import torch
from sentence_transformers import SentenceTransformer
from typing import Tuple, Optional

from history_utils import build_input_str, HISTORY_MAX_TURNS
from domains import MONO_DOMAINS, PIPELINE_CLASSES
from classifier_config import WEIGHTS_PATH, ENCODER_MODEL_NAME, ENCODER_MAX_SEQ_LEN
from model_architecture import (
    build_model, CKPT_VERSION, CKPT_VERSION_KEY, CKPT_TASKS,
    CKPT_STATE_KEY, CKPT_PARAMS_KEY, CKPT_METRICS_KEY,
    decide_domain, decide_difficulty,
)

_FU_GATE = os.environ.get("CYA_FU_GATE", "1") == "1"

_models:  Optional[dict]                = None   # task -> nn.Module
_params:  Optional[dict]                = None
_encoder: Optional[SentenceTransformer] = None
_loaded:  bool                          = False

LAST_DEBUG: dict = {}


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
        raise RuntimeError(f"Checkpoint in formato obsoleto (versione {ckpt.get(CKPT_VERSION_KEY)}, "
                           f"attesa {CKPT_VERSION}): rieseguire train_nn.py")

    models, params = {}, {}
    for t in CKPT_TASKS:
        m = build_model(t)
        m.load_state_dict(ckpt[t][CKPT_STATE_KEY])
        m.eval()
        models[t] = m
        params[t] = ckpt[t][CKPT_PARAMS_KEY]
        met = ckpt[t].get(CKPT_METRICS_KEY, {})
        print(f"[NN_CLASSIFIER] {t:10s} params={params[t]} | "
              + " | ".join(f"{k}={_fmt_metric(v)}" for k, v in met.items()))

    _models, _params, _loaded = models, params, True


def _user_turns(history: list) -> list:
    """[F1-A] SOLO i turni utente (ultimi HISTORY_MAX_TURNS), come nel training."""
    return [m['content'] for m in history if m.get('role') == 'user'][-HISTORY_MAX_TURNS:]


def predict(
    text: str,
    history: list = None,
) -> Tuple[int, float, dict, int, bool]:
    global LAST_DEBUG
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
        user_turns = _user_turns(history)
        has_hist   = bool(user_turns)
        input_str  = build_input_str(text, user_turns)

        with torch.no_grad():
            emb = _encoder.encode([input_str], normalize_embeddings=True, show_progress_bar=False)
            x   = torch.from_numpy(emb).float()
            lg_dom = _models['domain'](x).squeeze(0)        # [7]
            lg_dif = _models['difficulty'](x).squeeze(0)    # [2]
            lg_fu  = _models['followup'](x).reshape(())     # scalare

        probs    = torch.softmax(lg_dom, dim=0)
        pdom     = _params['domain']
        class_id = int(decide_domain(lg_dom, pdom['bias_pipe']).item())
        confidence = float(probs[class_id].item())

        scores = {n: float(probs[i]) for i, n in enumerate(MONO_DOMAINS)}
        for cid, (a, b) in PIPELINE_CLASSES.items():
            scores[a] += float(probs[cid])
            scores[b] += float(probs[cid])
        domain_scores = {n: round(v, 4) for n, v in scores.items()}

        difficulty  = int(decide_difficulty(lg_dif, _params['difficulty']['thr_fallback']).item())
        p_fu        = float(torch.sigmoid(lg_fu).item())
        thr_fu      = _params['followup']['thr']
        is_followup = (has_hist or not _FU_GATE) and (p_fu >= thr_fu)     # [F1-A] gate history vuota

        LAST_DEBUG = {'input': input_str, 'has_history': has_hist, 'p_followup': p_fu,
                      'thr_followup': thr_fu, 'logit_followup': float(lg_fu.item()),
                      'gate_blocked': (not has_hist) and _FU_GATE and p_fu >= thr_fu}
        return class_id, confidence, domain_scores, difficulty, bool(is_followup)

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
