"""
nn_classifier.py — CYA N | Step 5: Neural Classifier Inference Module
=======================================================================
Drop-in replacement di llm_router.py.
Stessa interfaccia pubblica:
    predict(text, history) → (class_id, conf, domain_scores, diff, is_followup)
    unload_router()

[FIX Criticità 3 — Report Gemini] Rimosso il parametro last_domain da
predict(): non era mai letto nel body della funzione, residuo
dell'euristica sticky routing (_should_sticky_route) già eliminata da
main.py in V7.4.0. La NN non ha alcun neurone addestrato su questa
stringa: passarla era dead code silenzioso.

[FIX Criticità 2 — Report Gemini] unload_router() ora libera davvero
encoder MiniLM (~470MB) e pesi MLP dalla RAM Python (del + gc.collect()),
invece di essere un pass. Necessario sul vincolo hardware di sviluppo
(8GB RAM): senza unload reale, il classificatore resta caricato mentre
Ollama tenta di allocare il modello generativo dell'agente.

Dipendenze:
  - code/classifier/nn_weights.pt    (prodotto da train_nn.py)
  - paraphrase-multilingual-MiniLM-L12-v2  (sentence-transformers, frozen)

[FIX — Bug A] Le soglie DOMAIN_THRESHOLD e PIPELINE_PAIR_THRESHOLD erano
hardcoded a 0.50 ENTRAMBE, ignorando config.NEURAL_CLASSIFIER_SETTINGS
(threshold_mono=0.35, threshold_pipeline=0.60) già definito ma mai
importato. DOMAIN_THRESHOLD era inoltre dead code: no   n referenziata in
nessuna funzione. La doppia soglia "candidatura permissiva / conferma
severa" descritta nei commenti originali non esisteva mai a runtime.
Ora entrambe sono lette da config.py e usate in due stadi distinti in
_derive_class_id().

[FIX — Report Gemini punto 3] _build_input_str() ora delega la
formattazione della stringa a history_utils.build_input_str(), la stessa
funzione usata in fase di training da precompute_embeddings.py.
"""

import time
import gc
import torch
import torch.nn as nn
from sentence_transformers import SentenceTransformer
from typing import Tuple, Optional
from pathlib import Path

import config
from history_utils import build_input_str, HISTORY_MAX_TURNS

# ─── COSTANTI PUBBLICHE (identiche a llm_router.py) ──────────────────────────
DOMAIN_NAMES: list = [
    'coding', 'math', 'rights', 'general',   # class_id 0-3
    'math->coding',                            # class_id 4
    'rights->coding',                          # class_id 5
    'rights->math',                            # class_id 6
]

PIPELINE_CLASSES: dict = {
    4: ('math',   'coding'),
    5: ('rights', 'coding'),
    6: ('rights', 'math'),
}

_CLASS_TO_NAME = {i: n for i, n in enumerate(DOMAIN_NAMES)}

# ─── CONFIG ───────────────────────────────────────────────────────────────────
_BASE_DIR      = Path(__file__).resolve().parent
_WEIGHTS_PATH  = _BASE_DIR / 'classifier' / 'nn_weights.pt'
_ENCODER_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
_HISTORY_TURNS = HISTORY_MAX_TURNS   # unica fonte di verità: history_utils.py

# [FIX Bug A] Soglie lette da config.py — DOMAIN_THRESHOLD è la soglia
# PERMISSIVA di stadio 1 (un dominio tecnico "entra in lizza" per la
# pipeline), PIPELINE_PAIR_THRESHOLD è la soglia SEVERA di stadio 2 (la
# coppia va confermata pipeline solo se ENTRAMBI i domini la superano).
DOMAIN_THRESHOLD        = config.NEURAL_CLASSIFIER_SETTINGS.get('threshold_mono',     0.35)
PIPELINE_PAIR_THRESHOLD = config.NEURAL_CLASSIFIER_SETTINGS.get('threshold_pipeline', 0.60)

# Ordine canonico delle pipeline (deve coincidere con config.py)
_PIPELINE_ORDER = {
    frozenset({'math',   'coding'}): 4,   # math->coding
    frozenset({'rights', 'coding'}): 5,   # rights->coding
    frozenset({'rights', 'math'}):   6,   # rights->math
}

# ─── ARCHITETTURA (identica a train_nn.py) ───────────────────────────────────
class MultiTaskMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(384, 256), nn.LayerNorm(256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 128), nn.LayerNorm(128), nn.ReLU(), nn.Dropout(0.2),
        )
        self.domain_head     = nn.Sequential(nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, 4))
        self.difficulty_head = nn.Sequential(nn.Linear(128, 32), nn.ReLU(), nn.Linear(32, 3))
        self.followup_head   = nn.Linear(128, 1)

    def forward(self, x: torch.Tensor):
        h = self.backbone(x)
        return self.domain_head(h), self.difficulty_head(h), self.followup_head(h)


# ─── STATO GLOBALE (singleton) ───────────────────────────────────────────────
_model:   Optional[MultiTaskMLP]        = None
_encoder: Optional[SentenceTransformer] = None
_loaded:  bool                          = False


def _load_model():
    global _model, _encoder, _loaded

    if _loaded:
        return

    if not _WEIGHTS_PATH.exists():
        raise FileNotFoundError(
            f"Pesi NN non trovati: {_WEIGHTS_PATH}\n"
            "Eseguire prima train_nn.py per generarli."
        )

    print(f"[NN_CLASSIFIER] Caricamento encoder: {_ENCODER_MODEL}")
    _encoder = SentenceTransformer(_ENCODER_MODEL)
    _encoder.eval()

    print(f"[NN_CLASSIFIER] Caricamento pesi: {_WEIGHTS_PATH}")
    ckpt = torch.load(str(_WEIGHTS_PATH), map_location='cpu', weights_only=False)

    _model = MultiTaskMLP()
    _model.load_state_dict(ckpt['model_state_dict'])
    _model.eval()

    print(f"[NN_CLASSIFIER] Test F1-macro domain : {ckpt.get('test_f1_domain', 'N/A'):.4f}")
    print(f"[NN_CLASSIFIER] Test difficulty acc  : {ckpt.get('test_diff_acc', 'N/A'):.4f}")
    print(f"[NN_CLASSIFIER] Test is_followup F1  : {ckpt.get('test_followup_f1', 'N/A'):.4f}")

    _loaded = True


def _build_input_str(query: str, history: list) -> str:
    """
    Estrae le query utente da chat_history (lista di dict {role, content})
    e delega la formattazione a history_utils.build_input_str — la STESSA
    funzione usata in fase di training. [Fix Report Gemini punto 3]
    """
    user_turns = [
        m['content'] for m in history
        if m.get('role') == 'user'
    ][-_HISTORY_TURNS:]
    return build_input_str(query, user_turns)


def _derive_class_id(
    domain_probs: torch.Tensor,          # shape [4], sigmoid applicata
    candidate_threshold: float = DOMAIN_THRESHOLD,
    pipeline_threshold: float = PIPELINE_PAIR_THRESHOLD,
) -> Tuple[int, float]:
    """
    Da domain_probs [coding, math, rights, general] → (class_id, confidence).

    LOGICA A DUE STADI [FIX Bug A]:
      Stadio 1 (permissivo, candidate_threshold=0.35): quali domini tecnici
        superano la soglia minima per essere "in lizza" per una pipeline.
      Stadio 2 (severo, pipeline_threshold=0.60): la coppia top-2 viene
        CONFERMATA pipeline solo se ENTRAMBI i probs superano questa soglia
        più alta. Altrimenti si scende a mono-domain (argmax sui 4).

      Questo impedisce che un dominio tecnico "debole" (es. math=0.40 dovuto
      a parole matematiche di contorno in una query di puro coding) faccia
      scattare una pipeline fantasma — serve una confidenza alta su ENTRAMBI
      i domini, non solo il minimo storico di 0.50.

    CONFIDENCE:
      - Pipeline:    min(prob_a, prob_b)
      - Mono-domain: prob del dominio vincente
    """
    probs_np = domain_probs.cpu().numpy()
    names_4  = ['coding', 'math', 'rights', 'general']

    tech_candidates = [
        (names_4[i], float(probs_np[i]))
        for i in range(3)
        if probs_np[i] >= candidate_threshold
    ]

    if len(tech_candidates) >= 2:
        tech_sorted = sorted(tech_candidates, key=lambda x: x[1], reverse=True)
        top2 = tech_sorted[:2]
        pair = frozenset({top2[0][0], top2[1][0]})

        if pair in _PIPELINE_ORDER and min(top2[0][1], top2[1][1]) >= pipeline_threshold:
            class_id   = _PIPELINE_ORDER[pair]
            confidence = min(top2[0][1], top2[1][1])
            return class_id, confidence

    class_id   = int(domain_probs.argmax().item())
    confidence = float(probs_np[class_id])
    return class_id, confidence


# ─── INTERFACCIA PUBBLICA ────────────────────────────────────────────────────

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

        domain_scores = {
            'coding':  round(float(domain_probs[0]), 4),
            'math':    round(float(domain_probs[1]), 4),
            'rights':  round(float(domain_probs[2]), 4),
            'general': round(float(domain_probs[3]), 4),
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
    """
    [FIX Criticità 2] Libera esplicitamente encoder MiniLM (~470MB) e pesi
    MLP dalla RAM Python. Va chiamata subito dopo la classificazione,
    PRIMA che Ollama carichi il modello generativo dell'agente. Costo:
    ricaricamento (encoder + pesi) al turno successivo (~1-3s), accettabile
    sul vincolo hardware di sviluppo (8GB RAM).
    """
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