"""
train_nn.py — CYA N | Step 3: Training MultiTaskMLP
====================================================
Input:  code/classifier/embeddings_v2.pkl
Output: code/classifier/nn_weights.pt

[REFACTOR — report_patch.md] MultiTaskMLP (DUP-1), path (CFG-1/2) e
chiavi checkpoint (CFG-5) condivise con nn_classifier.py via
model_architecture.py / classifier_config.py. Nessun impatto sul
comportamento numerico → nn_weights.pt esistente resta valido.

Architettura: 384 → 256 (LN, ReLU, Drop0.3) → 128 (LN, ReLU, Drop0.2)
  Domain head:      128 → 64 → 4   | BCEWithLogitsLoss, multi-label
  Difficulty head:  128 → 32 → 3   | CrossEntropyLoss,  3-class
  is_followup head: 128 → 1        | BCEWithLogitsLoss, binary
Loss composita: 0.70*L_domain + 0.30*L_diff + 0.15*L_followup
Early stopping: F1-macro domain sul val set (patience=25).
Tutti gli head restituiscono logit grezzi (attivazioni solo a inference).

Esecuzione (dalla root del progetto): python code/train_nn.py
"""

import pickle

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import f1_score

from domains import MONO_DOMAINS
from classifier_config import EMBEDDINGS_PATH, WEIGHTS_PATH
from model_architecture import (
    MultiTaskMLP,
    CKPT_STATE_DICT_KEY,
    CKPT_BEST_VAL_F1_KEY,
    CKPT_TEST_F1_DOMAIN_KEY,
    CKPT_TEST_DIFF_ACC_KEY,
    CKPT_TEST_FOLLOWUP_F1_KEY,
    CKPT_CONFIG_KEY,
)

# ─── CONFIG ───────────────────────────────────────────────────────────────────
PKL_PATH = EMBEDDINGS_PATH   # [CFG-1/2 FIX]

LR               = 1e-3
WEIGHT_DECAY     = 1e-4
EPOCHS           = 200
BATCH_SIZE       = 64
PATIENCE         = 25
SCHED_PATIENCE   = 10

LOSS_W_DOMAIN    = 0.70
LOSS_W_DIFF      = 0.30
LOSS_W_FOLLOWUP  = 0.15

DOMAIN_THRESHOLD = 0.5
MAX_POS_WEIGHT   = 5.0
# ──────────────────────────────────────────────────────────────────────────────


def load_pkl(path) -> dict:
    with open(path, 'rb') as f:
        return pickle.load(f)


def compute_pos_weights_domain(labels: torch.Tensor) -> torch.Tensor:
    pos = labels.sum(dim=0).clamp(min=1.0)
    neg = float(labels.shape[0]) - pos
    return (neg / pos).clamp(max=MAX_POS_WEIGHT).float()


def compute_pos_weight_scalar(labels: torch.Tensor) -> torch.Tensor:
    pos = labels.sum().clamp(min=1.0)
    neg = float(labels.shape[0]) - pos
    return (neg / pos).clamp(max=MAX_POS_WEIGHT).float().unsqueeze(0)


def f1_domain_macro(logits: torch.Tensor, labels: torch.Tensor) -> float:
    preds = (torch.sigmoid(logits) >= DOMAIN_THRESHOLD).int().cpu().numpy()
    trues = labels.int().cpu().numpy()
    return float(f1_score(trues, preds, average='macro', zero_division=0))


def f1_binary(logits: torch.Tensor, labels: torch.Tensor) -> float:
    preds = (torch.sigmoid(logits.squeeze(1)) >= 0.5).int().cpu().numpy()
    trues = labels.int().cpu().numpy()
    return float(f1_score(trues, preds, average='binary', zero_division=0))


def accuracy(preds_idx: torch.Tensor, labels: torch.Tensor) -> float:
    return float((preds_idx == labels).float().mean().item())


def train():

    print(f"[1/4] Caricamento: {PKL_PATH}")
    data = load_pkl(PKL_PATH)

    emb    = data['embeddings']
    d_lbl  = data['domain_labels']
    df_lbl = data['difficulty_labels']
    fu_lbl = data['is_followup_labels']
    splits = data['splits']

    idx_tr  = splits['train']
    idx_val = splits['val']
    idx_te  = splits['test']

    X_tr,  y_dom_tr,  y_dif_tr,  y_fu_tr  = (emb[idx_tr],  d_lbl[idx_tr],  df_lbl[idx_tr],  fu_lbl[idx_tr])
    X_val, y_dom_val, y_dif_val, y_fu_val = (emb[idx_val], d_lbl[idx_val], df_lbl[idx_val], fu_lbl[idx_val])
    X_te,  y_dom_te,  y_dif_te,  y_fu_te  = (emb[idx_te],  d_lbl[idx_te],  df_lbl[idx_te],  fu_lbl[idx_te])

    print(f"      Split  →  train={len(idx_tr)} | val={len(idx_val)} | test={len(idx_te)}")

    pw_domain   = compute_pos_weights_domain(y_dom_tr)
    pw_followup = compute_pos_weight_scalar(y_fu_tr)

    print(f"      pos_weight domain (C/M/R/G) : {[round(v, 2) for v in pw_domain.tolist()]}")
    print(f"      pos_weight is_followup       : {pw_followup.item():.2f}")
    fu_pos_tr = int(y_fu_tr.sum())
    print(f"      is_followup positivi (train) : {fu_pos_tr}/{len(idx_tr)} "
          f"({fu_pos_tr/len(idx_tr)*100:.1f}%)")

    loss_domain   = nn.BCEWithLogitsLoss(pos_weight=pw_domain)
    loss_diff     = nn.CrossEntropyLoss()
    loss_followup = nn.BCEWithLogitsLoss(pos_weight=pw_followup)

    model     = MultiTaskMLP()
    optimizer = optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', patience=SCHED_PATIENCE, factor=0.5
    )

    n_params = sum(p.numel() for p in model.parameters())
    print(f"\n[2/4] Modello: {n_params:,} parametri")
    print(f"      Loss weights: {LOSS_W_DOMAIN}/{LOSS_W_DIFF}/{LOSS_W_FOLLOWUP} (domain/diff/followup)")
    print(f"      Epoche max={EPOCHS} | patience={PATIENCE} | batch={BATCH_SIZE}\n")

    train_ds = TensorDataset(X_tr, y_dom_tr, y_dif_tr, y_fu_tr.unsqueeze(1))
    train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)

    best_f1    = -1.0
    best_state = None
    no_improve = 0

    for epoch in range(1, EPOCHS + 1):

        model.train()
        total_loss = 0.0

        for X_b, y_dom_b, y_dif_b, y_fu_b in train_dl:
            optimizer.zero_grad()
            logits_dom, logits_dif, logits_fu = model(X_b)

            l_dom = loss_domain(logits_dom, y_dom_b)
            l_dif = loss_diff(logits_dif, y_dif_b)
            l_fu  = loss_followup(logits_fu, y_fu_b)
            loss  = LOSS_W_DOMAIN * l_dom + LOSS_W_DIFF * l_dif + LOSS_W_FOLLOWUP * l_fu

            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(X_b)

        avg_loss = total_loss / len(idx_tr)

        model.eval()
        with torch.no_grad():
            logits_dom_v, logits_dif_v, logits_fu_v = model(X_val)
            val_f1 = f1_domain_macro(logits_dom_v, y_dom_val)
            val_loss = (
                LOSS_W_DOMAIN   * loss_domain(logits_dom_v, y_dom_val)
              + LOSS_W_DIFF     * loss_diff(logits_dif_v, y_dif_val)
              + LOSS_W_FOLLOWUP * loss_followup(logits_fu_v, y_fu_val.unsqueeze(1))
            ).item()

        scheduler.step(val_f1)
        current_lr = optimizer.param_groups[0]['lr']

        if val_f1 > best_f1:
            best_f1    = val_f1
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            no_improve = 0
            marker = " ★"
        else:
            no_improve += 1
            marker = ""

        if epoch % 10 == 0 or epoch == 1:
            print(f"  ep={epoch:4d} | tr_loss={avg_loss:.4f} | vl_loss={val_loss:.4f} | "
                  f"vl_f1={val_f1:.4f} | best={best_f1:.4f} | "
                  f"no_impr={no_improve}/{PATIENCE} | lr={current_lr:.2e}{marker}")

        if no_improve >= PATIENCE:
            print(f"\n  ⏹  Early stopping a epoca {epoch} (nessun miglioramento per {PATIENCE} epoche consecutive)")
            break

    print(f"\n[3/4] Training completato. Miglior F1-macro val (domain): {best_f1:.4f}")

    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        logits_dom_te, logits_dif_te, logits_fu_te = model(X_te)

        test_f1_domain = f1_domain_macro(logits_dom_te, y_dom_te)
        test_diff_acc  = accuracy(logits_dif_te.argmax(dim=1), y_dif_te)
        test_fu_f1     = f1_binary(logits_fu_te, y_fu_te)

        preds_dom = (torch.sigmoid(logits_dom_te) >= DOMAIN_THRESHOLD).int().cpu().numpy()
        trues_dom = y_dom_te.int().cpu().numpy()
        per_class_f1 = f1_score(trues_dom, preds_dom, average=None, zero_division=0)

    print(f"\n  ── RISULTATI TEST SET ─────────────────────────────────")
    print(f"  Domain  F1-macro   : {test_f1_domain:.4f}")
    for i, name in enumerate(MONO_DOMAINS):   # [DUP-2 FIX]
        print(f"    {name:8s}  F1  : {per_class_f1[i]:.4f}")
    print(f"  Difficulty accuracy: {test_diff_acc:.4f}")
    print(f"  is_followup F1-bin : {test_fu_f1:.4f}")

    print(f"\n[4/4] Salvataggio: {WEIGHTS_PATH}")
    WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    checkpoint = {
        CKPT_STATE_DICT_KEY:       best_state,
        CKPT_BEST_VAL_F1_KEY:      best_f1,
        CKPT_TEST_F1_DOMAIN_KEY:   test_f1_domain,
        CKPT_TEST_DIFF_ACC_KEY:    test_diff_acc,
        CKPT_TEST_FOLLOWUP_F1_KEY: test_fu_f1,
        CKPT_CONFIG_KEY: {
            'lr':                  LR,
            'weight_decay':        WEIGHT_DECAY,
            'batch_size':          BATCH_SIZE,
            'domain_threshold':    DOMAIN_THRESHOLD,
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