"""
NEURAL CLASSIFIER V1.0
MLP su embedding nomic-embed-text frozen (768d).

Classi:
  0: coding          4: math->coding   (pipeline)
  1: math            5: rights->coding (pipeline)
  2: rights          6: rights->math   (pipeline)
  3: general

Inferenza CPU < 5ms. Nessun LanceDB, nessun k-NN.
Pipeline detection integrata nell'output: nessuna logica esterna necessaria.

Uso training: python neural_classifier.py
"""

import os
import sys
import json
import pickle
import ollama
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from typing import Optional, Tuple
from collections import Counter

import config

# ---------------------------------------------------------------------------
# COSTANTI
# ---------------------------------------------------------------------------

CLASSIFIER_DIR = os.path.join(config.BASE_DIR, 'classifier')
MODEL_PATH     = os.path.join(CLASSIFIER_DIR, 'model.pt')
CONFIG_PATH    = os.path.join(CLASSIFIER_DIR, 'classifier_config.json')
DATASET_PATH   = os.path.join(config.BASE_DIR,  'dataset.pkl')

DOMAIN_NAMES = ['coding', 'math', 'rights', 'general',
                'math->coding', 'rights->coding', 'rights->math']

# Lookup fisso pipeline: sostituisce pipeline_order_matrix per il routing principale
PIPELINE_CLASSES: dict = {
    4: ('math',   'coding'),
    5: ('rights', 'coding'),
    6: ('rights', 'math'),
}

DEFAULT_CONFIG = {
    'threshold_mono':     0.45,  # soglia confidenza per classi 0-3
    'threshold_pipeline': 0.60,  # soglia più alta per classi 4-6 (FP pipeline costosi)
    'embedding_model':    'nomic-embed-text',
    'vector_dim':         768,
    'n_classes':          7,
}


# ---------------------------------------------------------------------------
# ARCHITETTURA MLP
# ---------------------------------------------------------------------------

class MLPClassifier(nn.Module):
    def __init__(self, input_dim: int = 768, n_classes: int = 7):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 256), nn.ReLU(), nn.Dropout(0.45),  # era 0.3
            nn.Linear(256, 64),        nn.ReLU(), nn.Dropout(0.30),  # era 0.2
            nn.Linear(64, n_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


# ---------------------------------------------------------------------------
# EMBEDDING (L2-normalizzato, identico a build_dataset.py)
# ---------------------------------------------------------------------------

def _embed(text: str, model: str) -> Optional[torch.Tensor]:
    try:
        vec = ollama.embeddings(model=model, prompt=text)['embedding']
        t   = torch.tensor(vec, dtype=torch.float32)
        n   = t.norm()
        return t / n if n > 0 else t
    except Exception as e:
        print(f"WARN neural_classifier: embedding fallito → {e}")
        return None


# ---------------------------------------------------------------------------
# CACHE SINGLETON
# ---------------------------------------------------------------------------

_model: Optional[MLPClassifier] = None
_cfg:   Optional[dict]          = None


def load_model() -> bool:
    """
    Carica model.pt e classifier_config.json.
    Ritorna True se riuscito, False se i file non esistono o sono corrotti.
    """
    global _model, _cfg
    if not os.path.exists(MODEL_PATH) or not os.path.exists(CONFIG_PATH):
        return False
    try:
        with open(CONFIG_PATH) as f:
            _cfg = json.load(f)
        m = MLPClassifier(
            input_dim=_cfg.get('vector_dim', 768),
            n_classes=_cfg.get('n_classes',  7)
        )
        # weights_only=True richiede PyTorch >= 2.0; fallback per versioni precedenti
        try:
            state = torch.load(MODEL_PATH, map_location='cpu', weights_only=True)
        except TypeError:
            state = torch.load(MODEL_PATH, map_location='cpu')
        m.load_state_dict(state)
        m.eval()
        _model = m
        return True
    except Exception as e:
        print(f"WARN neural_classifier: load_model fallito → {e}")
        return False


# ---------------------------------------------------------------------------
# PREDICT
# ---------------------------------------------------------------------------

def predict(text: str) -> Tuple[int, float]:
    """
    Classifica il testo.

    Returns:
        (class_id, confidence)
        class_id = -1  → classifier non disponibile, main.py usa fallback keyword.
        class_id 0-3   → mono-domain.
        class_id 4-6   → pipeline (vedi PIPELINE_CLASSES).

    Se la confidenza non supera la soglia di dominio:
        - Pipeline (4-6) con conf < threshold_pipeline: degrada al miglior mono-domain [0-3].
        - Mono (0-3) con conf < threshold_mono: degrada a general (3).
    """
    global _model, _cfg
    if _model is None:
        if not load_model():
            return -1, 0.0

    cfg       = _cfg or DEFAULT_CONFIG
    emb_model = cfg.get('embedding_model', 'nomic-embed-text')

    emb = _embed(text, emb_model)
    if emb is None:
        return -1, 0.0

    with torch.no_grad():
        probs = torch.softmax(_model(emb.unsqueeze(0)), dim=1).squeeze()  # (7,)

    class_id   = int(probs.argmax().item())
    confidence = float(probs[class_id].item())

    thr_pipeline = cfg.get('threshold_pipeline', DEFAULT_CONFIG['threshold_pipeline'])
    thr_mono     = cfg.get('threshold_mono',     DEFAULT_CONFIG['threshold_mono'])

    if class_id in PIPELINE_CLASSES:
        if confidence < thr_pipeline:
            # Degrada al miglior mono-domain
            mono_id    = int(probs[:4].argmax().item())
            confidence = float(probs[mono_id].item())
            class_id   = mono_id if confidence >= thr_mono else 3
            confidence = float(probs[class_id].item())
    else:
        if confidence < thr_mono:
            class_id   = 3  # general
            confidence = float(probs[3].item())

    return class_id, confidence


# ---------------------------------------------------------------------------
# TRAINING
# ---------------------------------------------------------------------------

def train(
    dataset_path: str = DATASET_PATH,
    epochs:       int   = 120,
    lr:           float = 1e-3,
    batch_size:   int   = 32,
    patience:     int   = 35,
) -> float:
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(
            f"Dataset non trovato: {dataset_path}\n"
            f"Esegui prima: python build_dataset.py"
        )

    with open(dataset_path, 'rb') as f:
        raw = pickle.load(f)

    print(f"Dataset caricato: {len(raw)} campioni")
    cnt = Counter(d['label'] for d in raw)
    print(f"Distribuzione: { {DOMAIN_NAMES[i]: cnt.get(i, 0) for i in range(7)} }\n")

    X = torch.stack([torch.tensor(d['embedding'], dtype=torch.float32) for d in raw])
    y = torch.tensor([d['label'] for d in raw], dtype=torch.long)

    X = X / X.norm(dim=1, keepdim=True).clamp(min=1e-8)

    from sklearn.model_selection import train_test_split
    from sklearn.metrics import f1_score, confusion_matrix

    idx_all = list(range(len(raw)))
    try:
        idx_tr, idx_te = train_test_split(
            idx_all, test_size=0.20, random_state=42, stratify=y.numpy()
        )
    except ValueError:
        print("WARN: stratified split fallito, uso split casuale.")
        idx_tr, idx_te = train_test_split(idx_all, test_size=0.20, random_state=42)

    X_tr, y_tr = X[idx_tr], y[idx_tr]
    X_te, y_te = X[idx_te], y[idx_te]
    print(f"Train: {len(idx_tr)} | Test: {len(idx_te)}\n")

    n_cls  = DEFAULT_CONFIG['n_classes']
    cnt_tr = torch.zeros(n_cls)
    for lbl in y_tr:
        cnt_tr[lbl.item()] += 1
    weights = cnt_tr.sum() / (n_cls * cnt_tr.clamp(min=1))
    print("Class weights:")
    for i in range(n_cls):
        print(f"  [{i}] {DOMAIN_NAMES[i]:15s}: {weights[i]:.3f}  (n_train={int(cnt_tr[i])})")
    print()

    dl = DataLoader(TensorDataset(X_tr, y_tr), batch_size=batch_size, shuffle=True)

    model     = MLPClassifier(DEFAULT_CONFIG['vector_dim'], n_cls)
    criterion = nn.CrossEntropyLoss(weight=weights, label_smoothing=0.08)
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=50)

    best_acc         = 0.0
    best_f1_macro    = 0.0
    best_state       = None
    best_ep          = 0
    patience_counter = 0

    for ep in range(1, epochs + 1):
        model.train()
        loss_sum = 0.0
        for xb, yb in dl:
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
            loss_sum += loss.item() * len(xb)
        scheduler.step()

        # Valuta ogni epoca
        model.eval()
        with torch.no_grad():
            preds    = model(X_te).argmax(dim=1)
            acc      = (preds == y_te).float().mean().item()

        preds_np     = preds.numpy()
        y_te_np      = y_te.numpy()
        f1_macro_cur = f1_score(y_te_np, preds_np, average='macro',    zero_division=0)
        f1_weighted  = f1_score(y_te_np, preds_np, average='weighted', zero_division=0)
        f1_per       = f1_score(y_te_np, preds_np, average=None,       zero_division=0)

        # Best model basato su F1 macro (più robusto di acc su classi sbilanciate)
        if f1_macro_cur > best_f1_macro:
            best_f1_macro    = f1_macro_cur
            best_acc         = acc
            best_ep          = ep
            patience_counter = 0
            best_state       = {k: v.clone() for k, v in model.state_dict().items()}
        elif ep % 5 == 0:
            patience_counter += 1

        if ep % 10 == 0 or ep == epochs or patience_counter >= patience:
            p_report = []
            for cls_id in PIPELINE_CLASSES:
                tp = int(((preds == cls_id) & (y_te == cls_id)).sum())
                fp = int(((preds == cls_id) & (y_te != cls_id)).sum())
                fn = int(((preds != cls_id) & (y_te == cls_id)).sum())
                p  = tp / (tp + fp + 1e-8)
                r  = tp / (tp + fn + 1e-8)
                p_report.append(f"cls{cls_id}[P={p:.2f} R={r:.2f} F1={f1_per[cls_id]:.2f}]")
            print(f"Ep {ep:3d}/{epochs}  loss={loss_sum/len(idx_tr):.4f}  "
                  f"val_acc={acc:.3f}  F1_macro={f1_macro_cur:.3f}  F1_w={f1_weighted:.3f}  "
                  f"patience={patience_counter}/{patience}  " + "  ".join(p_report))

        if patience_counter >= patience:
            print(f"\n⏹  Early stop a ep {ep} — best F1_macro={best_f1_macro:.3f} @ ep {best_ep}")
            break

    # --- Report finale sul best model ---
    if best_state:
        model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        preds_final = model(X_te).argmax(dim=1).numpy()
    y_final = y_te.numpy()

    f1_per_final = f1_score(y_final, preds_final, average=None,       zero_division=0)
    cm           = confusion_matrix(y_final, preds_final)

    print(f"\nBest val_acc: {best_acc:.3f}  F1_macro: {best_f1_macro:.3f}  (ep {best_ep})")

    print("\n--- F1 per classe (best model) ---")
    for i in range(n_cls):
        bar = '█' * int(f1_per_final[i] * 20)
        print(f"  [{i}] {DOMAIN_NAMES[i]:15s}: F1={f1_per_final[i]:.3f}  {bar}")
    print(f"\n  F1 macro:    {f1_score(y_final, preds_final, average='macro',    zero_division=0):.3f}")
    print(f"  F1 weighted: {f1_score(y_final, preds_final, average='weighted', zero_division=0):.3f}")

    print("\n--- Confusion Matrix (righe=reale, colonne=predetto) ---")
    header = "       " + "".join(f"{DOMAIN_NAMES[i][:6]:>8}" for i in range(n_cls))
    print(header)
    for i, row in enumerate(cm):
        print(f"  [{i}] {DOMAIN_NAMES[i][:6]:<6}" + "".join(f"{v:>8}" for v in row))
    print()

    if best_state is None:
        best_state = {k: v.clone() for k, v in model.state_dict().items()}

    os.makedirs(CLASSIFIER_DIR, exist_ok=True)
    torch.save(best_state, MODEL_PATH)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)

    print(f"Modello salvato : {MODEL_PATH}")
    print(f"Config salvata  : {CONFIG_PATH}")
    return best_f1_macro


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    acc = train()
    # Exit code 0 se accuracy >= 80%, 1 altrimenti
    sys.exit(0 if acc >= 0.80 else 1)
