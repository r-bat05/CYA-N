"""
train_nn.py — CYA N | Step 3: Training MultiTaskMLP
====================================================
Input:  classifier/embeddings_v2.pkl  (richiede 'class_labels' → rieseguire precompute_embeddings.py)
Output: classifier/nn_weights.pt

Architettura: vedi model_architecture.py (384→200→100 | domain 32→4 | difficulty 50→3 | followup 50→1).
Loss: 0.70*L_domain(BCE, senza pos_weight) + 0.30*L_diff(CE) + 0.15*L_followup(BCE, pos_weight clampato).

Protocollo v3:
  - Selezione checkpoint + early stopping: UNICO criterio = macro-F1 sulle 7 classi derivate con la STESSA
    regola a due stadi dell'inferenza (nn_classifier._derive_class_id), soglie da config.
  - Soglie tarate sul VAL a fine training (stampate, da riportare a mano in config.NEURAL_CLASSIFIER_SETTINGS).
  - Report finale per split (train/val/test) per misurare il gap di overfitting.
  - Env: CYA_SEED (default 42) | CYA_SAVE=0 per NON sovrascrivere i pesi (run diagnostici multi-seed).

Storico LR (log completo in git): lr=1e-5 converge troppo lentamente, lr=1e-2 va subito in overfitting → 2.5e-4.
Esecuzione: python train_nn.py
"""

import os
import pickle
import random

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader, TensorDataset
from matplotlib.pyplot import plot, show, savefig #plot e salvataggio del grafico della loss

SEED = int(os.environ.get("CYA_SEED", 42))
SAVE = os.environ.get("CYA_SAVE", "1") == "1"
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)

import config
from domains import DOMAIN_NAMES
from classifier_config import EMBEDDINGS_PATH, WEIGHTS_PATH
from nn_classifier import _derive_class_id
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
PKL_PATH         = EMBEDDINGS_PATH
LR               = 0.00025       # 2.5 * 1e-4
WEIGHT_DECAY     = 1e-2          # era 1e-4: con AdamW lr*wd ≈ 2.5e-8/step = nessun effetto
EPOCHS           = 100
BATCH_SIZE       = 64
PATIENCE         = 10
SCHED_PATIENCE   = 10

LOSS_W_DOMAIN    = 0.70
LOSS_W_DIFF      = 0.30
LOSS_W_FOLLOWUP  = 0.15

DOMAIN_THRESHOLD = 0.5           # solo per F1 per-dominio nei log
MAX_POS_WEIGHT   = 5.0           # solo head followup

CAND_THR   = config.NEURAL_CLASSIFIER_SETTINGS['threshold_mono']
PIPE_THR   = config.NEURAL_CLASSIFIER_SETTINGS['threshold_pipeline']
N_CLASSES  = len(DOMAIN_NAMES)
# ──────────────────────────────────────────────────────────────────────────────


def load_pkl(path) -> dict:
    with open(path, 'rb') as f:
        return pickle.load(f)


def compute_pos_weight_scalar(labels: torch.Tensor) -> torch.Tensor:
    pos = labels.sum().clamp(min=1.0)
    neg = float(labels.shape[0]) - pos
    return (neg / pos).clamp(max=MAX_POS_WEIGHT).float().unsqueeze(0)


def f1_domain_macro(logits: torch.Tensor, labels: torch.Tensor) -> float:
    preds = (torch.sigmoid(logits) >= DOMAIN_THRESHOLD).int().cpu().numpy()
    return float(f1_score(labels.int().cpu().numpy(), preds, average='macro', zero_division=0))


def class_preds(logits: torch.Tensor, cand: float, pipe: float) -> list:
    return [_derive_class_id(p, cand, pipe)[0] for p in torch.sigmoid(logits)]


def class_f1_macro(logits: torch.Tensor, y_cls: torch.Tensor, cand: float = CAND_THR, pipe: float = PIPE_THR) -> float:
    return float(f1_score(y_cls.cpu().numpy(), class_preds(logits, cand, pipe), average='macro', zero_division=0))


def f1_binary(logits: torch.Tensor, labels: torch.Tensor) -> float:
    preds = (torch.sigmoid(logits.squeeze(1)) >= 0.5).int().cpu().numpy()
    return float(f1_score(labels.int().cpu().numpy(), preds, average='binary', zero_division=0))


def accuracy(preds_idx: torch.Tensor, labels: torch.Tensor) -> float:
    return float((preds_idx == labels).float().mean().item())


def tune_thresholds(logits: torch.Tensor, y_cls: torch.Tensor, top: int = 3) -> list:
    res = []
    for c in (0.35, 0.40, 0.45, 0.50, 0.55, 0.60):
        for p in (0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90):
            res.append((class_f1_macro(logits, y_cls, c, p), c, p))
    return sorted(res, reverse=True)[:top]


def train():

    print(f"[1/4] Caricamento: {PKL_PATH}  (seed={SEED}, save={SAVE})")
    data = load_pkl(PKL_PATH)
    if 'class_labels' not in data:
        raise KeyError("embeddings_v2.pkl privo di 'class_labels': rieseguire precompute_embeddings.py")

    emb, d_lbl, df_lbl, fu_lbl, c_lbl = (data['embeddings'], data['domain_labels'],
                                         data['difficulty_labels'], data['is_followup_labels'],
                                         data['class_labels'])
    splits = data['splits']
    S = {k: splits[k] for k in ('train', 'val', 'test')}
    X     = {k: emb[S[k]]    for k in S}
    Y_dom = {k: d_lbl[S[k]]  for k in S}
    Y_dif = {k: df_lbl[S[k]] for k in S}
    Y_fu  = {k: fu_lbl[S[k]] for k in S}
    Y_cls = {k: c_lbl[S[k]]  for k in S}
    n_tr = len(S['train'])
    print(f"      Split  →  train={n_tr} | val={len(S['val'])} | test={len(S['test'])}")

    pw_followup = compute_pos_weight_scalar(Y_fu['train'])
    print(f"      pos_weight is_followup : {pw_followup.item():.2f}")

    loss_domain   = nn.BCEWithLogitsLoss()
    loss_diff     = nn.CrossEntropyLoss()
    loss_followup = nn.BCEWithLogitsLoss(pos_weight=pw_followup)

    model     = MultiTaskMLP()
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', patience=SCHED_PATIENCE, factor=0.5)

    print(f"\n[2/4] Modello: {sum(p.numel() for p in model.parameters()):,} parametri | "
          f"epoche max={EPOCHS} | patience={PATIENCE} | soglie selezione cand/pipe={CAND_THR}/{PIPE_THR}\n")

    train_dl = DataLoader(TensorDataset(X['train'], Y_dom['train'], Y_dif['train'], Y_fu['train'].unsqueeze(1)),
                          batch_size=BATCH_SIZE, shuffle=True)

    best_f1, best_state, no_improve = -1.0, None, 0
    loss_val_training = [] #lista per plottare la loss del testing

    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        for X_b, y_dom_b, y_dif_b, y_fu_b in train_dl:
            optimizer.zero_grad()
            l_dom_o, l_dif_o, l_fu_o = model(X_b)
            loss = (LOSS_W_DOMAIN * loss_domain(l_dom_o, y_dom_b)
                    + LOSS_W_DIFF * loss_diff(l_dif_o, y_dif_b)
                    + LOSS_W_FOLLOWUP * loss_followup(l_fu_o, y_fu_b))
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(X_b)
        avg_loss = total_loss / n_tr

        model.eval()
        with torch.no_grad():
            lv_dom, lv_dif, lv_fu = model(X['val'])
            val_loss = (LOSS_W_DOMAIN * loss_domain(lv_dom, Y_dom['val'])
                        + LOSS_W_DIFF * loss_diff(lv_dif, Y_dif['val'])
                        + LOSS_W_FOLLOWUP * loss_followup(lv_fu, Y_fu['val'].unsqueeze(1))).item()
            val_f1 = class_f1_macro(lv_dom, Y_cls['val'])

            #inserisco la loss in quell'epoca
            loss_val_training.append(val_loss)

        scheduler.step(val_f1)
        if val_f1 > best_f1:
            best_f1, best_state, no_improve, marker = val_f1, {k: v.clone() for k, v in model.state_dict().items()}, 0, " ★"
        else:
            no_improve, marker = no_improve + 1, ""

        print(f"  ep={epoch:4d} | tr_loss={avg_loss:.4f} | vl_loss={val_loss:.4f} | "
              f"vl_clsF1={val_f1:.4f} | best={best_f1:.4f} | no_impr={no_improve}/{PATIENCE} | "
              f"lr={optimizer.param_groups[0]['lr']:.2e}{marker}")


        #da migliorare i criteri d'arresto 
        if no_improve >= PATIENCE:
            print(f"\n  ⏹  Early stopping a epoca {epoch}")
            break

    print(f"\n[3/4] Training completato. Miglior macro-F1 classi (val): {best_f1:.4f}")

    #stampo il valore della loss (asse x = epoche, asse y = valore loss)
    x = np.linspace(1, epoch, num=epoch) #vettore delle epoche

    #preparo il grafio
    plot(x, loss_val_training) 
    #salvo il grafico
    savefig('./code/classifier/grafico_loss_training.png') 
    #mostro i grafici preparati
    show()

    #salvo la loss come png

    model.load_state_dict(best_state)
    model.eval()
    R = {}
    with torch.no_grad():
        for k in ('train', 'val', 'test'):
            ld, lf, lu = model(X[k])
            R[k] = {
                'dom_f1':  f1_domain_macro(ld, Y_dom[k]),
                'cls_f1':  class_f1_macro(ld, Y_cls[k]),
                'diff_acc': accuracy(lf.argmax(dim=1), Y_dif[k]),
                'fu_f1':   f1_binary(lu, Y_fu[k]),
                'logits':  ld,
            }

    print(f"\n  ── GAP train / val / test ────────────────────────────")
    print(f"  {'':10s}{'domain-F1':>11s}{'class-F1':>10s}{'diff-acc':>10s}{'fu-F1':>8s}")
    for k in ('train', 'val', 'test'):
        r = R[k]
        print(f"  {k:10s}{r['dom_f1']:11.4f}{r['cls_f1']:10.4f}{r['diff_acc']:10.4f}{r['fu_f1']:8.4f}")
    print(f"  gap train-val: class-F1={R['train']['cls_f1']-R['val']['cls_f1']:+.4f} | "
          f"diff-acc={R['train']['diff_acc']-R['val']['diff_acc']:+.4f}   (soglie: 0.05 / 0.10)")

    per_cls = f1_score(Y_cls['test'].numpy(), class_preds(R['test']['logits'], CAND_THR, PIPE_THR),
                       labels=list(range(N_CLASSES)), average=None, zero_division=0)
    print(f"\n  F1 per classe (test): " + " | ".join(f"{n}={v:.3f}" for n, v in zip(DOMAIN_NAMES, per_cls)))

    tuned = tune_thresholds(R['val']['logits'], Y_cls['val'])
    print(f"\n  Soglie ottimali su VAL (class-F1, cand, pipe):")
    for f1v, c, p in tuned:
        t_f1 = class_f1_macro(R['test']['logits'], Y_cls['test'], c, p)
        print(f"    val={f1v:.4f}  cand={c:.2f}  pipe={p:.2f}  → test={t_f1:.4f}")

    print(f"\nSEEDRESULT seed={SEED} val_cls={R['val']['cls_f1']:.4f} test_cls={R['test']['cls_f1']:.4f} "
          f"gap_cls={R['train']['cls_f1']-R['val']['cls_f1']:.4f} gap_diff={R['train']['diff_acc']-R['val']['diff_acc']:.4f}")

    if SAVE:
        print(f"\n[4/4] Salvataggio: {WEIGHTS_PATH}")
        WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            CKPT_STATE_DICT_KEY:       best_state,
            CKPT_BEST_VAL_F1_KEY:      best_f1,
            CKPT_TEST_F1_DOMAIN_KEY:   R['test']['dom_f1'],
            CKPT_TEST_DIFF_ACC_KEY:    R['test']['diff_acc'],
            CKPT_TEST_FOLLOWUP_F1_KEY: R['test']['fu_f1'],
            CKPT_CONFIG_KEY: {
                'lr': LR, 'weight_decay': WEIGHT_DECAY, 'batch_size': BATCH_SIZE, 'seed': SEED,
                'select_cand_thr': CAND_THR, 'select_pipe_thr': PIPE_THR,
                'pos_weight_followup': float(pw_followup.item()),
            },
        }, WEIGHTS_PATH)
        print(f"  ✅  Salvato → {WEIGHTS_PATH}  ({WEIGHTS_PATH.stat().st_size / 1024:.1f} KB)")
    else:
        print("\n[4/4] CYA_SAVE=0: pesi NON salvati (run diagnostico).")


if __name__ == '__main__':
    train()