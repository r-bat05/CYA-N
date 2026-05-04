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

DOMAIN_ONEHOT = {
    'coding':  [1, 0, 0, 0],
    'math':    [0, 1, 0, 0],
    'rights':  [0, 0, 1, 0],
    'general': [0, 0, 0, 1],
}

# Per ogni classe: i contesti last_domain simulati durante l'augmentation
# [context_followup, context_switch] → produce 3 copie totali (+ neutral)
_AUGMENT_CONTEXTS = {
    0: [[1,0,0,0], [0,0,0,1]],  # coding:         last=coding,  last=general
    1: [[0,1,0,0], [0,0,0,1]],  # math:           last=math,    last=general
    2: [[0,0,1,0], [0,0,0,1]],  # rights:         last=rights,  last=general
    3: [[0,0,0,1], [0,0,0,0]],  # general:        last=general, neutral
    4: [[0,1,0,0], [1,0,0,0]],  # math->coding:   last=math,    last=coding
    5: [[0,0,1,0], [1,0,0,0]],  # rights->coding: last=rights,  last=coding
    6: [[0,0,1,0], [0,1,0,0]],  # rights->math:   last=rights,  last=math
}

DEFAULT_CONFIG = {
    'threshold_mono':     0.35,   # [P2] abbassato da 0.45: riduce false-general su query brevi
    'threshold_pipeline': 0.60,
    'embedding_model':    'nomic-embed-text',
    'vector_dim':         772,
    'n_classes':          7,
}

# ---------------------------------------------------------------------------
# ARCHITETTURA MLP
# ---------------------------------------------------------------------------

class MLPClassifier(nn.Module):
    def __init__(self, input_dim: int = 772, n_classes: int = 7):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 256), nn.ReLU(), nn.Dropout(0.45),
            nn.Linear(256, 64),        nn.ReLU(), nn.Dropout(0.30),
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

def _augment(X_raw: torch.Tensor, y: torch.Tensor) -> tuple:
    """
    Data augmentation contestuale: per ogni campione genera 3 copie (772d)
    con last_domain simulato diverso:
      1. neutral  → [0,0,0,0]  (inizio sessione)
      2. followup → contesto compatibile con la classe
      3. switch   → contesto di provenienza alternativo

    Input:  X_raw (N, 768), y (N,)
    Output: X_aug (3N, 772), y_aug (3N,)
    """
    X_list, y_list = [], []

    # Copia 1: neutral context per tutti
    neutral_ctx = torch.zeros(len(X_raw), 4)
    X_list.append(torch.cat([X_raw, neutral_ctx], dim=1))
    y_list.append(y)

    # Copie 2 e 3: contesti specifici per classe
    for cls_id, (ctx_followup, ctx_switch) in _AUGMENT_CONTEXTS.items():
        mask = (y == cls_id)
        if not mask.any():
            continue
        X_cls = X_raw[mask]

        ctx_f = torch.tensor(ctx_followup, dtype=torch.float32).unsqueeze(0).expand(len(X_cls), -1)
        X_list.append(torch.cat([X_cls, ctx_f], dim=1))
        y_list.append(y[mask])

        ctx_s = torch.tensor(ctx_switch, dtype=torch.float32).unsqueeze(0).expand(len(X_cls), -1)
        X_list.append(torch.cat([X_cls, ctx_s], dim=1))
        y_list.append(y[mask])

    return torch.cat(X_list), torch.cat(y_list)


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
            input_dim=_cfg.get('vector_dim', 772),
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

def predict(text: str, last_domain: str = '') -> Tuple[int, float]:
    """
    Classifica il testo tenendo conto del dominio attivo nella sessione.

    Args:
        text:        query dell'utente
        last_domain: ultimo dominio tecnico attivo ('coding','math','rights','general','')

    Returns:
        (class_id, confidence)
        class_id = -1  → classifier non disponibile
        class_id 0-3   → mono-domain
        class_id 4-6   → pipeline (vedi PIPELINE_CLASSES)
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

    # Appendi one-hot last_domain (4 feature) → 772d
    onehot = DOMAIN_ONEHOT.get(last_domain, [0, 0, 0, 0])
    ctx    = torch.tensor(onehot, dtype=torch.float32)
    feat   = torch.cat([emb, ctx]).unsqueeze(0)  # (1, 772)

    with torch.no_grad():
        probs = torch.softmax(_model(feat), dim=1).squeeze()  # (7,)

    class_id   = int(probs.argmax().item())
    confidence = float(probs[class_id].item())

    thr_pipeline = cfg.get('threshold_pipeline', DEFAULT_CONFIG['threshold_pipeline'])
    thr_mono     = cfg.get('threshold_mono',     DEFAULT_CONFIG['threshold_mono'])

    if class_id in PIPELINE_CLASSES:
        if confidence < thr_pipeline:
            mono_id    = int(probs[:4].argmax().item())
            confidence = float(probs[mono_id].item())
            class_id   = mono_id if confidence >= thr_mono else 3
            confidence = float(probs[class_id].item())
    else:
        if confidence < thr_mono:
            class_id   = 3
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

    print(f"Dataset caricato: {len(raw)} campioni (pre-augmentation)")
    cnt = Counter(d['label'] for d in raw)
    print(f"Distribuzione: { {DOMAIN_NAMES[i]: cnt.get(i, 0) for i in range(7)} }\n")

    # Embedding raw (768d) e label
    X_raw = torch.stack([torch.tensor(d['embedding'], dtype=torch.float32) for d in raw])
    y_raw = torch.tensor([d['label'] for d in raw], dtype=torch.long)
    X_raw = X_raw / X_raw.norm(dim=1, keepdim=True).clamp(min=1e-8)

    from sklearn.model_selection import train_test_split
    from sklearn.metrics import f1_score, confusion_matrix

    # Split PRIMA dell'augmentation per evitare data leakage
    idx_all = list(range(len(raw)))
    try:
        idx_tr, idx_te = train_test_split(
            idx_all, test_size=0.20, random_state=42, stratify=y_raw.numpy()
        )
    except ValueError:
        print("WARN: stratified split fallito, uso split casuale.")
        idx_tr, idx_te = train_test_split(idx_all, test_size=0.20, random_state=42)

    X_tr_raw, y_tr = X_raw[idx_tr], y_raw[idx_tr]
    X_te_raw, y_te = X_raw[idx_te], y_raw[idx_te]

    # Augmentation solo su train — test set rimane raw (neutral context)
    # per valutare la robustezza del modello sul caso peggiore (no context)
    X_tr, y_tr = _augment(X_tr_raw, y_tr)

    # Test set: neutral context (caso peggiore — nessun contesto disponibile)
    X_te = torch.cat([X_te_raw, torch.zeros(len(X_te_raw), 4)], dim=1)

    print(f"Post-augmentation — Train: {len(X_tr)} | Test: {len(X_te)}")
    cnt_aug = Counter(y_tr.tolist())
    print(f"Distribuzione train augmentata: { {DOMAIN_NAMES[i]: cnt_aug.get(i, 0) for i in range(7)} }\n")

    n_cls  = DEFAULT_CONFIG['n_classes']
    cnt_tr = torch.zeros(n_cls)
    for lbl in y_tr:
        cnt_tr[lbl.item()] += 1
    weights = cnt_tr.sum() / (n_cls * cnt_tr.clamp(min=1))
    print("Class weights (post-augmentation):")
    for i in range(n_cls):
        print(f"  [{i}] {DOMAIN_NAMES[i]:15s}: {weights[i]:.3f}  (n_train={int(cnt_tr[i])})")
    print()

    dl = DataLoader(TensorDataset(X_tr, y_tr), batch_size=batch_size, shuffle=True)

    input_dim = DEFAULT_CONFIG['vector_dim']  # 772
    model     = MLPClassifier(input_dim, n_cls)
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

        model.eval()
        with torch.no_grad():
            preds = model(X_te).argmax(dim=1)
            acc   = (preds == y_te).float().mean().item()

        preds_np     = preds.numpy()
        y_te_np      = y_te.numpy()
        f1_macro_cur = f1_score(y_te_np, preds_np, average='macro',    zero_division=0)
        f1_weighted  = f1_score(y_te_np, preds_np, average='weighted', zero_division=0)
        f1_per       = f1_score(y_te_np, preds_np, average=None,       zero_division=0)

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
            print(f"Ep {ep:3d}/{epochs}  loss={loss_sum/len(X_tr):.4f}  "
                  f"val_acc={acc:.3f}  F1_macro={f1_macro_cur:.3f}  F1_w={f1_weighted:.3f}  "
                  f"patience={patience_counter}/{patience}  " + "  ".join(p_report))

        if patience_counter >= patience:
            print(f"\n⏹  Early stop a ep {ep} — best F1_macro={best_f1_macro:.3f} @ ep {best_ep}")
            break

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
    
    # Formattazione dinamica per le intestazioni delle colonne
    col_headers = "".join(f"{DOMAIN_NAMES[i][:6]:>8}" for i in range(n_cls))
    print(f"       {col_headers}")
    print("       " + "-" * (n_cls * 8))

    for i, row in enumerate(cm):
        # Nome della classe reale (riga)
        row_label = f"[{i}] {DOMAIN_NAMES[i][:6]:<6}|"
        
        # Valori della matrice formattati
        row_values = "".join(f"{v:>8}" for v in row)
        
        print(f"{row_label}{row_values}")
        
    # Calcolo extra per identificare le principali confusioni (opzionale ma utile)
    print("\n--- Analisi Errori Principali ---")
    for i in range(n_cls):
        for j in range(n_cls):
            if i != j and cm[i][j] > 0:
                print(f"Reale: {DOMAIN_NAMES[i]} -> Predetto: {DOMAIN_NAMES[j]} ({cm[i][j]} volte)")
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
