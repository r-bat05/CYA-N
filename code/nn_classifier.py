"""
nn_classifier.py — CYA N | Step 5: Neural Classifier Inference Module
=======================================================================
Drop-in replacement di llm_router.py.
Stessa interfaccia pubblica:
    predict(text, last_domain, history) → (class_id, conf, domain_scores, diff, is_followup)
    unload_router()

Dipendenze:
  - code/classifier/nn_weights.pt    (prodotto da train_nn.py)
  - paraphrase-multilingual-MiniLM-L12-v2  (sentence-transformers, frozen)

Architettura identica a train_nn.py — NON modificare senza aggiornare entrambi.

PIPELINE DERIVATION:
  La testa domain ha 4 uscite (coding, math, rights, general).
  I class_id 4/5/6 (pipeline) sono derivati POST-HOC controllando
  quali coppie di domini tecnici superano PIPELINE_PAIR_THRESHOLD.
  Questa soglia è volutamente più alta di DOMAIN_THRESHOLD per evitare
  pipeline false attivate da segnali deboli.
"""

import os
import time
import torch
import torch.nn as nn
from sentence_transformers import SentenceTransformer
from typing import Tuple, Optional
from pathlib import Path

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

# class_id → nome dominio (pipeline usano nomi compositi)
_CLASS_TO_NAME = {i: n for i, n in enumerate(DOMAIN_NAMES)}

# ─── CONFIG ───────────────────────────────────────────────────────────────────
_BASE_DIR        = Path(__file__).resolve().parent
_WEIGHTS_PATH    = _BASE_DIR / 'classifier' / 'nn_weights.pt'
_ENCODER_MODEL   = 'paraphrase-multilingual-MiniLM-L12-v2'
_HISTORY_TURNS   = 2          # deve coincidere con precompute_embeddings.py

# Soglie di classificazione.
# DOMAIN_THRESHOLD: soglia binaria per attivare un singolo dominio.
# PIPELINE_PAIR_THRESHOLD: soglia per considerare una COPPIA di domini attivi
# (più alta per evitare pipeline false attivate da segnali deboli, es. 0.52 coding
#  + 0.51 math su una query che è solo coding con parole matematiche di contorno).
DOMAIN_THRESHOLD       = 0.50
PIPELINE_PAIR_THRESHOLD = 0.50   # calibrare dopo smoke test Step 4

# Ordine canonico delle pipeline (deve coincidere con config.py)
_PIPELINE_ORDER = {
    frozenset({'math',   'coding'}): 4,   # math->coding
    frozenset({'rights', 'coding'}): 5,   # rights->coding
    frozenset({'rights', 'math'}):   6,   # rights->math
}

# ─── ARCHITETTURA (identica a train_nn.py) ───────────────────────────────────
class MultiTaskMLP(nn.Module):
    """
    Backbone condiviso + 3 teste.
    forward() restituisce LOGIT GREZZI (nessuna attivazione finale).
    Le attivazioni vengono applicate in predict() a inference time.
    """

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
_model:   Optional[MultiTaskMLP]     = None
_encoder: Optional[SentenceTransformer] = None
_loaded:  bool                       = False


def _load_model():
    """Carica encoder e MLP dal disco (lazy, prima chiamata a predict())."""
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

    # Log metriche del checkpoint
    print(f"[NN_CLASSIFIER] Test F1-macro domain : {ckpt.get('test_f1_domain', 'N/A'):.4f}")
    print(f"[NN_CLASSIFIER] Test difficulty acc  : {ckpt.get('test_diff_acc', 'N/A'):.4f}")
    print(f"[NN_CLASSIFIER] Test is_followup F1  : {ckpt.get('test_followup_f1', 'N/A'):.4f}")

    _loaded = True


def _build_input_str(query: str, history: list) -> str:
    """
    Replica esatta di precompute_embeddings.build_input_str.
    Formato: "[HISTORY] q_{-2} | q_{-1} [QUERY] <query>"
    Se history vuota: solo <query>.
    """
    if history:
        user_turns = [
            m['content'] for m in history
            if m.get('role') == 'user'
        ][-_HISTORY_TURNS:]
        if user_turns:
            hist_str = " | ".join(user_turns)
            return f"[HISTORY] {hist_str} [QUERY] {query}"
    return query


def _derive_class_id(
    domain_probs: torch.Tensor,          # shape [4], sigmoid applicata
    pipeline_threshold: float = PIPELINE_PAIR_THRESHOLD,
) -> Tuple[int, float]:
    """
    Da domain_probs [coding, math, rights, general] → (class_id, confidence).

    LOGICA PIPELINE:
      1. Trova quali domini TECNICI (coding, math, rights) superano la soglia
      2. Se >= 2 domini tecnici attivi → cerca la coppia nella _PIPELINE_ORDER
         - Se 3 attivi: usa i 2 con probabilità più alta
      3. Altrimenti → mono-domain (argmax di tutti e 4)

    CONFIDENCE:
      - Pipeline:    min(prob_a, prob_b) — riflette l'affidabilità del link più debole
      - Mono-domain: prob del dominio vincente
      - General:     prob_general (invariato, segnala incertezza bassa)
    """
    probs_np = domain_probs.cpu().numpy()  # [coding, math, rights, general]
    names_4  = ['coding', 'math', 'rights', 'general']

    # Domini tecnici attivi (indici 0=coding, 1=math, 2=rights)
    tech_active = [
        (names_4[i], float(probs_np[i]))
        for i in range(3)
        if probs_np[i] >= pipeline_threshold
    ]

    if len(tech_active) >= 2:
        # Ordina per probabilità decrescente, prendi i top-2
        tech_active_sorted = sorted(tech_active, key=lambda x: x[1], reverse=True)
        top2 = tech_active_sorted[:2]
        pair = frozenset({top2[0][0], top2[1][0]})

        if pair in _PIPELINE_ORDER:
            class_id   = _PIPELINE_ORDER[pair]
            confidence = min(top2[0][1], top2[1][1])
            return class_id, confidence

    # Mono-domain: argmax su tutti e 4
    class_id   = int(domain_probs.argmax().item())
    confidence = float(probs_np[class_id])
    return class_id, confidence


# ─── INTERFACCIA PUBBLICA ────────────────────────────────────────────────────

def predict(
    text: str,
    last_domain: str = '',
    history: list = None,
) -> Tuple[int, float, dict, int, bool]:
    """
    Classifica la query con il MultiTaskMLP.

    Returns:
        (class_id, confidence, domain_scores, difficulty, is_followup)

        class_id    : 0=coding, 1=math, 2=rights, 3=general,
                      4=math->coding, 5=rights->coding, 6=rights->math
                      -1 → modello non disponibile (main.py attiva fallback keyword)
        confidence  : probabilità del dominio / coppia vincente  [0.0–1.0]
        domain_scores: {'coding': p, 'math': p, 'rights': p, 'general': p}
        difficulty  : 1 (semplice) | 2 (media) | 3 (complessa)
        is_followup : True se la query continua l'output precedente

    Note:
        - Il parametro last_domain NON è usato direttamente dal NN
          (il contesto è già catturato via build_input_str).
          Viene preservato nella firma per compatibilità con main.py.
        - history: lista di dict {role, content} — stessa struttura di main.py.
    """
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

        # 1. Build input
        input_str = _build_input_str(text, history)

        # 2. Encode (L2-normalizzato, identico a precompute)
        with torch.no_grad():
            emb = _encoder.encode(
                [input_str],
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            x = torch.from_numpy(emb).float()   # [1, 384]

        # 3. Forward pass
        with torch.no_grad():
            _model.eval()
            logits_dom, logits_diff, logit_fu = _model(x)

        # 4. Attivazioni
        domain_probs = torch.sigmoid(logits_dom.squeeze(0))     # [4]
        diff_probs   = torch.softmax(logits_diff.squeeze(0), dim=0)  # [3]
        fu_prob      = torch.sigmoid(logit_fu.squeeze()).item()  # scalar

        # 5. Derivazione output
        class_id, confidence = _derive_class_id(domain_probs)

        domain_scores = {
            'coding':  round(float(domain_probs[0]), 4),
            'math':    round(float(domain_probs[1]), 4),
            'rights':  round(float(domain_probs[2]), 4),
            'general': round(float(domain_probs[3]), 4),
        }

        difficulty  = int(diff_probs.argmax().item()) + 1    # 0/1/2 → 1/2/3
        is_followup = fu_prob >= 0.5

        ms = (time.time() - t0) * 1000
        label = _CLASS_TO_NAME[class_id]
        scores_str = ' | '.join(f"{k}:{v:.3f}" for k, v in domain_scores.items())
        print(f"[NN_CLASSIFIER] {label.upper()} | conf={confidence:.3f} | "
              f"diff={difficulty} | followup={is_followup} | "
              f"scores=[{scores_str}] | {ms:.0f}ms")

        return class_id, confidence, domain_scores, difficulty, is_followup

    except Exception as e:
        print(f"[NN_CLASSIFIER] Errore inference ({e}) → fallback keyword")
        return -1, 0.0, {}, 2, False


def unload_router():
    """
    Compatibilità con llm_router.py: il NN non occupa RAM GPU,
    quindi non serve un unload esplicito. No-op.
    """
    pass
