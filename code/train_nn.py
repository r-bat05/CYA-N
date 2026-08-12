"""
train_nn.py — CYA N | Step 3: Training MultiTaskMLP
====================================================
Input:  code/classifier/embeddings_v2.pkl
Output: code/classifier/nn_weights.pt

Architettura backbone + 3 teste:
  384 → 256 (LN, ReLU, Drop0.3) → 128 (LN, ReLU, Drop0.2)
  Domain head:      128 → 64 → 4   | BCEWithLogitsLoss, multi-label
  Difficulty head:  128 → 32 → 3   | CrossEntropyLoss,  3-class
  is_followup head: 128 → 1        | BCEWithLogitsLoss, binary

Loss composita: 0.70*L_domain + 0.30*L_diff + 0.15*L_followup
Early stopping: F1-macro domain sul val set (patience=25).

NOTE: tutti gli head restituiscono logit grezzi.
  - Sigmoid/Softmax NON applicati nel forward → training usa
    BCEWithLogitsLoss / CrossEntropyLoss (numericamente stabili).
  - Le attivazioni vengono applicate SOLO a inference time (nn_classifier.py).

Esecuzione (dalla root del progetto):
  python code/train_nn.py
"""

import pickle
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import f1_score

# ─── CONFIG ───────────────────────────────────────────────────────────────────
# [M4 FIX] Ancorato a Path(__file__).resolve().parent invece che relativo
# alla cwd — stesso pattern già usato da nn_classifier.py, coerente con
# precompute_embeddings.py (patchato allo stesso modo).
_BASE_DIR        = Path(__file__).resolve().parent
PKL_PATH         = _BASE_DIR / 'classifier' / 'embeddings_v2.pkl'
WEIGHTS_PATH     = _BASE_DIR / 'classifier' / 'nn_weights.pt'

LR               = 1e-3        # Lr iniziale (serve per l'ottimizzatore dei pesi Adam)
WEIGHT_DECAY     = 1e-4        # regolarizzazione L2. Non ci saranno pesi troppo grandi
EPOCHS           = 200         # epoche massime
BATCH_SIZE       = 64          # utile per fare il batch stochastic gradient descent
PATIENCE         = 25          # numero di epoche per cui se non c'è miglioramento viene interrotto il training --> DA TOGLIERE
SCHED_PATIENCE   = 10          # ReduceLROnPlateau: abbassa il lr quando una metrica smette di migliorare

LOSS_W_DOMAIN    = 0.70
LOSS_W_DIFF      = 0.30
LOSS_W_FOLLOWUP  = 0.15

DOMAIN_THRESHOLD = 0.5         # soglia sigmoid per binarizzare le predizioni domain
# ──────────────────────────────────────────────────────────────────────────────


# ─── ARCHITETTURA ─────────────────────────────────────────────────────────────
class MultiTaskMLP(nn.Module):
    """
    Backbone condiviso + 3 teste specializzate.
    Forward restituisce LOGIT GREZZI (nessuna attivazione finale).
    """

    def __init__(self):
        super().__init__()

        # Backbone condiviso --> prima parte della rete neurale
        self.backbone = nn.Sequential(
            #strato di input: 384 input (dovuti dall'embedding)
            #1° strato hidden
            nn.Linear(384, 256),
            #standardizzo gli input dei neuroni in modo che assumnano valori bassi
            nn.LayerNorm(256), 
            nn.ReLU(),
            #disattivo il 30% dei neuroni dello strato hidden ad ogni input DURANTE IL TRAINING
            #utile per prevenire overfitting nel training
            nn.Dropout(0.3),
            #2° strato hidden
            nn.Linear(256, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Dropout(0.2), #come sopra
        )

        # Domain head: 128 → 64 → 4  (multi-label, BCEWithLogitsLoss)
        self.domain_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 4),
        )

        # Difficulty head: 128 → 32 → 3  (3-class, CrossEntropyLoss)
        self.difficulty_head = nn.Sequential(
            nn.Linear(128, 32),
            nn.ReLU(),
            nn.Linear(32, 3),
        )

        # is_followup head: 128 → 1  (binary, BCEWithLogitsLoss)
        self.followup_head = nn.Linear(128, 1)

    def forward(self, x: torch.Tensor):
        h = self.backbone(x)                       # [B, 128]
        return (
            self.domain_head(h),                   # [B, 4]
            self.difficulty_head(h),               # [B, 3]
            self.followup_head(h),                 # [B, 1]
        )


# ─── UTILITY ──────────────────────────────────────────────────────────────────
def load_pkl(path: Path) -> dict:
    with open(path, 'rb') as f:
        return pickle.load(f)


# [FIX Report Gemini #1] Cap anti-distorsione: un pos_weight troppo alto
# spinge i logit artificialmente in alto anche su esempi ambigui/negativi,
# causando falsi positivi is_followup=True sia su switch di dominio sia
# su query mono-dominio senza history (vedi wrong_query.md). Abbassato da
# 8.0 a 5.0: preserva parte del beneficio del pos_weight (recall sui
# followup corti tipo "perché?") riducendo la distorsione sistemica sul
# resto della distribuzione.
MAX_POS_WEIGHT = 5.0


def compute_pos_weights_domain(labels: torch.Tensor) -> torch.Tensor:
    """pos_weight[i] = min((N-pos_i)/pos_i, MAX_POS_WEIGHT) per dominio."""
    pos = labels.sum(dim=0).clamp(min=1.0)
    neg = float(labels.shape[0]) - pos
    return (neg / pos).clamp(max=MAX_POS_WEIGHT).float()


def compute_pos_weight_scalar(labels: torch.Tensor) -> torch.Tensor:
    """pos_weight scalare per is_followup, cappato a MAX_POS_WEIGHT."""
    pos = labels.sum().clamp(min=1.0)
    neg = float(labels.shape[0]) - pos
    return (neg / pos).clamp(max=MAX_POS_WEIGHT).float().unsqueeze(0)

#calcola la metrica f1 per ogni dominio
def f1_domain_macro(logits: torch.Tensor, labels: torch.Tensor) -> float:
    """F1-macro su 4 classi domain (multi-label). Input: logit grezzi."""
    preds = (torch.sigmoid(logits) >= DOMAIN_THRESHOLD).int().cpu().numpy()
    trues = labels.int().cpu().numpy()
    return float(f1_score(trues, preds, average='macro', zero_division=0))


def f1_binary(logits: torch.Tensor, labels: torch.Tensor) -> float:
    preds = (torch.sigmoid(logits.squeeze(1)) >= 0.5).int().cpu().numpy()
    trues = labels.int().cpu().numpy()
    return float(f1_score(trues, preds, average='binary', zero_division=0))


def accuracy(preds_idx: torch.Tensor, labels: torch.Tensor) -> float:
    return float((preds_idx == labels).float().mean().item())


# ─── TRAINING ─────────────────────────────────────────────────────────────────
def train():

    # ── 1. Caricamento dati ───────────────────────────────────────────────────
    print(f"[1/4] Caricamento: {PKL_PATH}")
    data = load_pkl(PKL_PATH)

    emb    = data['embeddings']          # [N, 384]  float32
    d_lbl  = data['domain_labels']       # [N, 4]    float32  multi-label
    df_lbl = data['difficulty_labels']   # [N]       int64    (0/1/2)
    fu_lbl = data['is_followup_labels']  # [N]       float32  (0/1)
    splits = data['splits']              # dict: 'train'/'val'/'test' → LongTensor

    idx_tr  = splits['train']
    idx_val = splits['val']
    idx_te  = splits['test']

    X_tr,  y_dom_tr,  y_dif_tr,  y_fu_tr  = (
        emb[idx_tr],  d_lbl[idx_tr],  df_lbl[idx_tr],  fu_lbl[idx_tr]
    )
    X_val, y_dom_val, y_dif_val, y_fu_val = (
        emb[idx_val], d_lbl[idx_val], df_lbl[idx_val], fu_lbl[idx_val]
    )
    X_te,  y_dom_te,  y_dif_te,  y_fu_te  = (
        emb[idx_te],  d_lbl[idx_te],  df_lbl[idx_te],  fu_lbl[idx_te]
    )

    print(f"      Split  →  train={len(idx_tr)} | val={len(idx_val)} | test={len(idx_te)}")

    # ── 2. pos_weight ─────────────────────────────────────────────────────────
    pw_domain   = compute_pos_weights_domain(y_dom_tr)          # [4]
    pw_followup = compute_pos_weight_scalar(y_fu_tr)            # [1]

    print(f"      pos_weight domain (C/M/R/G) : {[round(v, 2) for v in pw_domain.tolist()]}")
    print(f"      pos_weight is_followup       : {pw_followup.item():.2f}")
    fu_pos_tr = int(y_fu_tr.sum())
    print(f"      is_followup positivi (train) : {fu_pos_tr}/{len(idx_tr)} "
          f"({fu_pos_tr/len(idx_tr)*100:.1f}%)")

    # ── 3. Loss functions ─────────────────────────────────────────────────────
    loss_domain   = nn.BCEWithLogitsLoss(pos_weight=pw_domain)
    loss_diff     = nn.CrossEntropyLoss()
    loss_followup = nn.BCEWithLogitsLoss(pos_weight=pw_followup)

    # ── 4. Modello, ottimizzatore, scheduler ──────────────────────────────────
    model     = MultiTaskMLP()
    optimizer = optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    # [minor FIX] Rimosso verbose=False: parametro deprecato nelle versioni
    # recenti di PyTorch (rimosso in favore di get_last_lr()/logging
    # manuale). Nessun impatto comportamentale: il default è già "nessun
    # print automatico", identico a verbose=False.
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', patience=SCHED_PATIENCE, factor=0.5
    )

    n_params = sum(p.numel() for p in model.parameters())
    print(f"\n[2/4] Modello: {n_params:,} parametri")
    print(f"      Loss weights: {LOSS_W_DOMAIN}/{LOSS_W_DIFF}/{LOSS_W_FOLLOWUP} "
          f"(domain/diff/followup)")
    print(f"      Epoche max={EPOCHS} | patience={PATIENCE} | batch={BATCH_SIZE}\n")

    # DataLoader (mini-batch, shuffle solo sul train)
    # y_fu_tr.unsqueeze(1) → [N,1] per BCEWithLogitsLoss
    train_ds = TensorDataset(X_tr, y_dom_tr, y_dif_tr, y_fu_tr.unsqueeze(1))
    train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)

    best_f1    = -1.0
    best_state = None
    no_improve = 0

    # ── Loop di training ──────────────────────────────────────────────────────
    for epoch in range(1, EPOCHS + 1):

        # TRAIN
        model.train()
        total_loss = 0.0
        for X_b, y_dom_b, y_dif_b, y_fu_b in train_dl:
            optimizer.zero_grad()

            #FORWARD PASS: calcolo output modello per un input + build del grafo computazionale
            logits_dom, logits_dif, logits_fu = model(X_b)

            #calcolo quanto vale la loss
            l_dom = loss_domain(logits_dom, y_dom_b)
            l_dif = loss_diff(logits_dif, y_dif_b)
            l_fu  = loss_followup(logits_fu, y_fu_b)
            loss  = LOSS_W_DOMAIN * l_dom + LOSS_W_DIFF * l_dif + LOSS_W_FOLLOWUP * l_fu

            #BACKWARD PASS: calcolo delle derivate parziali della loss rispetto ai pesi 
            #pesi salvati in model.parameters come tensori
            loss.backward()

            #UPDATE PESI: calcolato il gradiente della loss rispetto ai pesi si aggiornano 
            #i parametri
            optimizer.step()
            total_loss += loss.item() * len(X_b)

        avg_loss = total_loss / len(idx_tr)

        # VAL: valuto il modello dopo aver aggiornato i parametri per ogni input 
        model.eval() #non aggiorno più niente (eval + no_grad())
        with torch.no_grad():
            logits_dom_v, logits_dif_v, logits_fu_v = model(X_val)

            val_f1 = f1_domain_macro(logits_dom_v, y_dom_val)

            val_loss = (
                LOSS_W_DOMAIN   * loss_domain(logits_dom_v, y_dom_val)
              + LOSS_W_DIFF     * loss_diff(logits_dif_v, y_dif_val)
              + LOSS_W_FOLLOWUP * loss_followup(logits_fu_v, y_fu_val.unsqueeze(1))
            ).item()

        scheduler.step(val_f1) #valuto se conviene cambiare il lr (se f1 non è migliorato)
        current_lr = optimizer.param_groups[0]['lr'] #prendo il lr modificato

        # Early stopping check
        if val_f1 > best_f1:
            best_f1    = val_f1
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            no_improve = 0
            marker = " ★"
        else: #se f1 non è migliorato...
            no_improve += 1
            marker = ""

        if epoch % 10 == 0 or epoch == 1:
            # [minor FIX] {marker} era calcolato ogni epoca ma mai
            # effettivamente stampato (il vecchio "#{marker}" era un
            # commento, non un'interpolazione f-string). Riattivato: mostra
            # "★" quando l'epoca corrente ha migliorato il best F1-macro.
            print(f"  ep={epoch:4d} | tr_loss={avg_loss:.4f} | vl_loss={val_loss:.4f} | "
                  f"vl_f1={val_f1:.4f} | best={best_f1:.4f} | "
                  f"no_impr={no_improve}/{PATIENCE} | lr={current_lr:.2e}{marker}")

        #se ho avuto 0 migliorati nelle ultime PATIENCE iterazioni...
        if no_improve >= PATIENCE:
            print(f"\n  ⏹  Early stopping a epoca {epoch} "
                  f"(nessun miglioramento per {PATIENCE} epoche consecutive)")
            break

    print(f"\n[3/4] Training completato. Miglior F1-macro val (domain): {best_f1:.4f}")

    # ── Valutazione sul test set - FASE DI TESTING ───────────────────────────────────────────────
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        logits_dom_te, logits_dif_te, logits_fu_te = model(X_te)

        test_f1_domain = f1_domain_macro(logits_dom_te, y_dom_te)
        test_diff_acc  = accuracy(logits_dif_te.argmax(dim=1), y_dif_te)
        test_fu_f1     = f1_binary(logits_fu_te, y_fu_te)

        # F1 per classe domain sul test
        preds_dom = (torch.sigmoid(logits_dom_te) >= DOMAIN_THRESHOLD).int().cpu().numpy()
        trues_dom = y_dom_te.int().cpu().numpy()
        per_class_f1 = f1_score(trues_dom, preds_dom, average=None, zero_division=0)

    print(f"\n  ── RISULTATI TEST SET ─────────────────────────────────")
    print(f"  Domain  F1-macro   : {test_f1_domain:.4f}")
    for i, name in enumerate(['coding', 'math', 'rights', 'general']):
        print(f"    {name:8s}  F1  : {per_class_f1[i]:.4f}")
    print(f"  Difficulty accuracy: {test_diff_acc:.4f}")
    print(f"  is_followup F1-bin : {test_fu_f1:.4f}")

    # ── Salvataggio checkpoint ────────────────────────────────────────────────
    '''SALVA I PESI DEL MODELLO PER POTERLI ESPORTARE'''
    print(f"\n[4/4] Salvataggio: {WEIGHTS_PATH}")
    WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    checkpoint = {
        # Pesi migliori (caricati da nn_classifier.py con model.load_state_dict)
        'model_state_dict': best_state,

        # Metriche training
        'best_val_f1_domain': best_f1,
        'test_f1_domain':     test_f1_domain,
        'test_diff_acc':      test_diff_acc,
        'test_followup_f1':   test_fu_f1,

        # Config usata (utile per reproducibility e per nn_classifier.py)
        'config': {
            'lr':               LR,
            'weight_decay':     WEIGHT_DECAY,
            'batch_size':       BATCH_SIZE,
            'domain_threshold': DOMAIN_THRESHOLD,
            'pos_weight_domain':   pw_domain.tolist(),
            'pos_weight_followup': float(pw_followup.item()),
        },
    }

    torch.save(checkpoint, WEIGHTS_PATH)

    size_kb = WEIGHTS_PATH.stat().st_size / 1024
    print(f"  ✅  Salvato → {WEIGHTS_PATH}  ({size_kb:.1f} KB)")
    print(f"\n  Prossimo step: python code/precompute_embeddings.py  (se dataset aggiornato)")
    print(f"  Poi Step 5:    costruire nn_classifier.py che carica nn_weights.pt")


if __name__ == '__main__':
    train()
