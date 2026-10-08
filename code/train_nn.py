"""
train_nn.py — CYA N | Step 3: training di 3 reti INDIPENDENTI
==============================================================
Input : classifier/embeddings_v2.pkl  (richiede 'class_labels')
Output: classifier/nn_weights.pt  (1 file, 3 state_dict + parametri di decisione)
        classifier/training_curves.png (loss train/val e score di selezione, per task)

Ogni task ha loss, metrica di selezione, scheduler ed early stopping PROPRI:

  DOMAIN     CE a 7 classi (pesi di classe ∝ 1/√freq, label smoothing 0.05).
             Decisione: argmax + bias scalare sui logit pipeline (decide_domain).
             Selezione: macro-F1(7 classi) con bias tarato OGNI epoca sul VAL,
             penalizzata se la false-pipeline rate (mono→pipeline) supera
             config.NEURAL_CLASSIFIER_SETTINGS['max_false_pipeline_rate'].
  DIFFICULTY CORAL ordinale (BCE su [d>1, d>2]).
             Decisione: soglia su P(d>1) per il tier fallback (decide_difficulty).
             Selezione: 0.6·tier-score + 0.4·acc3, tier-score = 0.4·recall(facile) + 0.6·recall(difficile)
             (errore costoso = query difficile mandata al modello piccolo).
  FOLLOWUP   BCE con pos_weight √(neg/pos) ≤ 3. Soglia tarata sul VAL.
             Selezione: 0.5·AP + 0.5·F1(soglia ottimale).

Le loss riportate (train e val) sono entrambe: modalità eval, senza pesi né smoothing,
quindi direttamente confrontabili (gap di overfitting).

Env: CYA_SEED (default 42) | CYA_SAVE=0 per NON sovrascrivere i pesi.
Esecuzione: python train_nn.py
"""

import os
import pickle
import random

import numpy as np
import torch
import torch.nn.functional as F
import torch.optim as optim
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import (f1_score, average_precision_score, precision_score,
                             recall_score, confusion_matrix)
from torch.utils.data import DataLoader, TensorDataset

SEED = int(os.environ.get("CYA_SEED", 42))
SAVE = os.environ.get("CYA_SAVE", "1") == "1"

import config
from domains import DOMAIN_NAMES
from classifier_config import EMBEDDINGS_PATH, WEIGHTS_PATH
from model_architecture import (
    DomainMLP, DifficultyMLP, FollowupMLP, N_MONO, N_CLASSES,
    decide_domain, decide_difficulty,
    CKPT_VERSION, CKPT_VERSION_KEY, CKPT_STATE_KEY, CKPT_PARAMS_KEY,
    CKPT_METRICS_KEY, CKPT_CONFIG_KEY,
)

# ─── CONFIG ───────────────────────────────────────────────────────────────────
PKL_PATH       = EMBEDDINGS_PATH
LR             = 2.5e-4
WEIGHT_DECAY   = 1e-2
EPOCHS         = 300            # tetto; è l'early stopping a fermare
BATCH_SIZE     = 64
PATIENCE       = 15             # epoche senza miglioramento > MIN_DELTA
SCHED_PATIENCE = 4              # < PATIENCE: il LR scende PRIMA dello stop
MIN_DELTA      = 1e-3

LABEL_SMOOTHING = 0.05
CLASS_W_POWER   = 0.5           # peso classe = (1/freq)^0.5
CLASS_W_CAP     = 5.0
MAX_FP_RATE     = config.NEURAL_CLASSIFIER_SETTINGS['max_false_pipeline_rate']
FP_PENALTY      = 3.0           # score = F1 - 3·max(0, fp - MAX_FP_RATE)

DIFF_W_TIER     = 0.6           # peso del tier-score nello score difficulty
TIER_W_HARD     = 0.6           # peso recall(difficile) nel tier-score
FU_MAX_POS_W    = 3.0

_srt = lambda grid, c: sorted([float(g) for g in grid], key=lambda g: abs(g - c))   # preferisce il centro
DOM_BIAS_GRID = _srt(np.arange(-3.0, 3.01, 0.25), 0.0)
DIFF_THR_GRID = _srt(np.arange(0.20, 0.71, 0.05), 0.5)
FU_THR_GRID   = _srt(np.arange(0.20, 0.81, 0.05), 0.5)
# ──────────────────────────────────────────────────────────────────────────────


def set_seed(s: int):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)


def load_pkl(path) -> dict:
    with open(path, 'rb') as f:
        return pickle.load(f)


# ═════════════════════════ DOMAIN ═════════════════════════
def domain_metrics(lg, y, bias):
    yn, pred = y.numpy(), decide_domain(lg, bias).numpy()
    f1   = float(f1_score(yn, pred, labels=list(range(N_CLASSES)), average='macro', zero_division=0))
    mono = yn < N_MONO
    fp   = float(((pred >= N_MONO) & mono).sum() / max(int(mono.sum()), 1))
    return f1, fp, pred


def domain_select(lg, y):
    best = None
    for b in DOM_BIAS_GRID:
        f1, fp, _ = domain_metrics(lg, y, b)
        s = f1 - FP_PENALTY * max(0.0, fp - MAX_FP_RATE)
        if best is None or s > best[0] + 1e-9:
            best = (s, b, f1, fp)
    s, b, f1, fp = best
    return s, {'bias_pipe': float(b)}, f"f1={f1:.3f} fp={fp:.3f} bias={b:+.2f}"


def domain_losses(y_train):
    cnt = torch.bincount(y_train, minlength=N_CLASSES).float().clamp(min=1)
    w   = (cnt.sum() / (N_CLASSES * cnt)) ** CLASS_W_POWER
    w   = (w / w.mean()).clamp(max=CLASS_W_CAP)
    print(f"      pesi classe: " + " ".join(f"{n}={v:.2f}" for n, v in zip(DOMAIN_NAMES, w.tolist())))
    return (lambda lg, y: F.cross_entropy(lg, y, weight=w, label_smoothing=LABEL_SMOOTHING),
            lambda lg, y: F.cross_entropy(lg, y))


# ═════════════════════════ DIFFICULTY ═════════════════════════
def _ord_targets(y):                       # y∈{0,1,2} → [d>1, d>2]
    return torch.stack([(y >= 1), (y >= 2)], dim=1).float()


def diff_loss(lg, y):
    return F.binary_cross_entropy_with_logits(lg, _ord_targets(y))


def diff_metrics(lg, y, thr):
    yn   = y.numpy()
    pred = decide_difficulty(lg, thr).numpy() - 1
    easy, p_easy = (yn == 0), (pred == 0)
    rec_easy = float((p_easy & easy).sum() / max(int(easy.sum()), 1))
    rec_hard = float((~p_easy & ~easy).sum() / max(int((~easy).sum()), 1))
    tier = (1 - TIER_W_HARD) * rec_easy + TIER_W_HARD * rec_hard
    return float(tier), float((pred == yn).mean()), pred


def diff_select(lg, y):
    best = None
    for t in DIFF_THR_GRID:
        tier, acc3, _ = diff_metrics(lg, y, t)
        s = DIFF_W_TIER * tier + (1 - DIFF_W_TIER) * acc3
        if best is None or s > best[0] + 1e-9:
            best = (s, t, tier, acc3)
    s, t, tier, acc3 = best
    return s, {'thr_fallback': float(t)}, f"tier={tier:.3f} acc3={acc3:.3f} thr={t:.2f}"


# ═════════════════════════ FOLLOWUP ═════════════════════════
def fu_metrics(lg, y, thr):
    yn = y.numpy().astype(int)
    p  = torch.sigmoid(lg.squeeze(1)).numpy()
    pred = (p >= thr).astype(int)
    return (float(f1_score(yn, pred, zero_division=0)),
            float(average_precision_score(yn, p)),
            float(precision_score(yn, pred, zero_division=0)),
            float(recall_score(yn, pred, zero_division=0)))


def fu_select(lg, y):
    best = None
    for t in FU_THR_GRID:
        f1 = fu_metrics(lg, y, t)[0]
        if best is None or f1 > best[0] + 1e-9:
            best = (f1, t)
    f1, t = best
    ap = fu_metrics(lg, y, t)[1]
    return 0.5 * ap + 0.5 * f1, {'thr': float(t)}, f"f1={f1:.3f} ap={ap:.3f} thr={t:.2f}"


def fu_losses(y_train):
    pos = y_train.sum().clamp(min=1.0)
    neg = float(y_train.shape[0]) - pos
    pw  = (neg / pos).sqrt().clamp(max=FU_MAX_POS_W).float().unsqueeze(0)
    print(f"      pos_weight followup: {pw.item():.2f}")
    return (lambda lg, y: F.binary_cross_entropy_with_logits(lg.squeeze(1), y, pos_weight=pw),
            lambda lg, y: F.binary_cross_entropy_with_logits(lg.squeeze(1), y))


# ═════════════════════════ TRAINING GENERICO ═════════════════════════
def fit(name, model, X, Y, train_loss, val_loss, select_fn):
    """Allena `model`, ricarica il best checkpoint e restituisce {state, params, score, ep, hist}."""
    print(f"\n[{name.upper()}] {sum(p.numel() for p in model.parameters()):,} parametri")
    opt = optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    sch = optim.lr_scheduler.ReduceLROnPlateau(opt, mode='max', factor=0.5, patience=SCHED_PATIENCE,
                                               threshold=MIN_DELTA, threshold_mode='abs')
    dl  = DataLoader(TensorDataset(X['train'], Y['train']), batch_size=BATCH_SIZE, shuffle=True)

    hist = {'tr': [], 'vl': [], 'score': []}
    best = {'score': -float('inf'), 'state': None, 'params': None, 'ep': 0}
    no_imp = 0

    for ep in range(1, EPOCHS + 1):
        model.train()
        for xb, yb in dl:
            opt.zero_grad()
            train_loss(model(xb), yb).backward()
            opt.step()

        model.eval()
        with torch.no_grad():
            tr = val_loss(model(X['train']), Y['train']).item()
            lv = model(X['val'])
            vl = val_loss(lv, Y['val']).item()
            score, params, info = select_fn(lv, Y['val'])
        sch.step(score)

        improved = score > best['score'] + MIN_DELTA
        if improved:
            best.update(score=score, params=params, ep=ep,
                        state={k: v.clone() for k, v in model.state_dict().items()})
            no_imp = 0
        else:
            no_imp += 1
        hist['tr'].append(tr); hist['vl'].append(vl); hist['score'].append(score)

        if improved or ep % 5 == 0:
            print(f"  ep={ep:3d} | tr={tr:.4f} vl={vl:.4f} | score={score:.4f} [{info}] | "
                  f"best={best['score']:.4f}@{best['ep']} | no_impr={no_imp}/{PATIENCE} | "
                  f"lr={opt.param_groups[0]['lr']:.1e}{' ★' if improved else ''}")
        if no_imp >= PATIENCE:
            print(f"  ⏹  Early stopping a epoca {ep}")
            break

    model.load_state_dict(best['state'])
    model.eval()
    best['hist'] = hist
    print(f"  → best epoca {best['ep']} | score={best['score']:.4f} | params={best['params']}")
    return best


def plot_curves(res: dict, path):
    fig, ax = plt.subplots(2, len(res), figsize=(5 * len(res), 7))
    for j, (name, r) in enumerate(res.items()):
        h = r['hist']; e = range(1, len(h['vl']) + 1)
        ax[0][j].plot(e, h['tr'], label='train'); ax[0][j].plot(e, h['vl'], label='val')
        ax[0][j].axvline(r['ep'], ls='--', c='gray'); ax[0][j].set_title(f'{name} — loss'); ax[0][j].legend()
        ax[1][j].plot(e, h['score']); ax[1][j].axvline(r['ep'], ls='--', c='gray')
        ax[1][j].set_title(f'{name} — score di selezione')
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)


def train():
    print(f"[1/4] Caricamento: {PKL_PATH}  (seed={SEED}, save={SAVE})")
    data = load_pkl(PKL_PATH)
    for k in ('class_labels', 'difficulty_labels', 'is_followup_labels'):
        if k not in data:
            raise KeyError(f"embeddings_v2.pkl privo di '{k}': rieseguire precompute_embeddings.py")

    S  = {k: data['splits'][k] for k in ('train', 'val', 'test')}
    X  = {k: data['embeddings'][S[k]] for k in S}
    Yc = {k: data['class_labels'][S[k]] for k in S}
    Yd = {k: data['difficulty_labels'][S[k]] for k in S}
    Yf = {k: data['is_followup_labels'][S[k]] for k in S}
    print(f"      Split → train={len(S['train'])} | val={len(S['val'])} | test={len(S['test'])} "
          f"| max_fp_rate={MAX_FP_RATE}")

    print("\n[2/4] Training (3 task indipendenti)")
    set_seed(SEED);     m_dom = DomainMLP();     tl, vl = domain_losses(Yc['train'])
    r_dom = fit('domain', m_dom, X, Yc, tl, vl, domain_select)
    set_seed(SEED + 1); m_dif = DifficultyMLP()
    r_dif = fit('difficulty', m_dif, X, Yd, diff_loss, diff_loss, diff_select)
    set_seed(SEED + 2); m_fu = FollowupMLP();    tl, vl = fu_losses(Yf['train'])
    r_fu  = fit('followup', m_fu, X, Yf, tl, vl, fu_select)

    print("\n[3/4] Report finale")
    b, t_d, t_f = r_dom['params']['bias_pipe'], r_dif['params']['thr_fallback'], r_fu['params']['thr']
    M, LG = {}, {}
    with torch.no_grad():
        for k in ('train', 'val', 'test'):
            LG[k] = (m_dom(X[k]), m_dif(X[k]), m_fu(X[k]))
            f1, fp, _   = domain_metrics(LG[k][0], Yc[k], b)
            tier, a3, _ = diff_metrics(LG[k][1], Yd[k], t_d)
            ff1, ap, pr, rc = fu_metrics(LG[k][2], Yf[k], t_f)
            M[k] = dict(dom_f1=f1, fp=fp, tier=tier, acc3=a3, fu_f1=ff1, fu_ap=ap, fu_p=pr, fu_r=rc)

    print(f"  {'':7s}{'dom-F1':>9s}{'FP-rate':>9s}{'tier':>8s}{'acc3':>8s}{'fu-F1':>8s}{'fu-AP':>8s}{'fu-P':>7s}{'fu-R':>7s}")
    for k in ('train', 'val', 'test'):
        m = M[k]
        print(f"  {k:7s}{m['dom_f1']:9.4f}{m['fp']:9.4f}{m['tier']:8.4f}{m['acc3']:8.4f}"
              f"{m['fu_f1']:8.4f}{m['fu_ap']:8.4f}{m['fu_p']:7.3f}{m['fu_r']:7.3f}")
    print(f"  gap train-val: dom-F1={M['train']['dom_f1']-M['val']['dom_f1']:+.4f} | "
          f"acc3={M['train']['acc3']-M['val']['acc3']:+.4f} | fu-F1={M['train']['fu_f1']-M['val']['fu_f1']:+.4f}"
          f"   (soglie indicative: 0.05 / 0.10 / 0.10)")

    _, _, pred = domain_metrics(LG['test'][0], Yc['test'], b)
    per_cls = f1_score(Yc['test'].numpy(), pred, labels=list(range(N_CLASSES)), average=None, zero_division=0)
    print("\n  F1 per classe (test): " + " | ".join(f"{n}={v:.3f}" for n, v in zip(DOMAIN_NAMES, per_cls)))
    print("  Confusione dominio test (righe=atteso):")
    cm = confusion_matrix(Yc['test'].numpy(), pred, labels=list(range(N_CLASSES)))
    for i, row in enumerate(cm):
        print(f"   {i}={DOMAIN_NAMES[i]:15s}" + "".join(f"{v:5d}" for v in row))

    curves = WEIGHTS_PATH.parent / 'training_curves.png'
    curves.parent.mkdir(parents=True, exist_ok=True)
    plot_curves({'domain': r_dom, 'difficulty': r_dif, 'followup': r_fu}, curves)
    print(f"\n  Curve salvate → {curves}")

    print(f"\nSEEDRESULT seed={SEED} val_dom={M['val']['dom_f1']:.4f} test_dom={M['test']['dom_f1']:.4f} "
          f"test_fp={M['test']['fp']:.4f} test_tier={M['test']['tier']:.4f} test_acc3={M['test']['acc3']:.4f} "
          f"test_fu_f1={M['test']['fu_f1']:.4f}")

    if SAVE:
        print(f"\n[4/4] Salvataggio: {WEIGHTS_PATH}")
        T = M['test']
        torch.save({
            CKPT_VERSION_KEY: CKPT_VERSION,
            'domain':     {CKPT_STATE_KEY: r_dom['state'], CKPT_PARAMS_KEY: r_dom['params'],
                           CKPT_METRICS_KEY: {'test_f1': T['dom_f1'], 'test_fp_rate': T['fp']}},
            'difficulty': {CKPT_STATE_KEY: r_dif['state'], CKPT_PARAMS_KEY: r_dif['params'],
                           CKPT_METRICS_KEY: {'test_tier': T['tier'], 'test_acc3': T['acc3']}},
            'followup':   {CKPT_STATE_KEY: r_fu['state'],  CKPT_PARAMS_KEY: r_fu['params'],
                           CKPT_METRICS_KEY: {'test_f1': T['fu_f1'], 'test_ap': T['fu_ap']}},
            CKPT_CONFIG_KEY: {'lr': LR, 'weight_decay': WEIGHT_DECAY, 'batch_size': BATCH_SIZE, 'seed': SEED,
                              'label_smoothing': LABEL_SMOOTHING, 'max_fp_rate': float(MAX_FP_RATE)},
        }, WEIGHTS_PATH)
        print(f"  ✅  Salvato → {WEIGHTS_PATH}  ({WEIGHTS_PATH.stat().st_size / 1024:.1f} KB)")
    else:
        print("\n[4/4] CYA_SAVE=0: pesi NON salvati (run diagnostico).")


if __name__ == '__main__':
    train()
