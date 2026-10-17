"""
train_nn.py — CYA N | Step 3: training di 3 reti INDIPENDENTI (dominio, difficoltà, follow-up)
=====================================================================================
Input : classifier/embeddings_v2.pkl   (prodotto da precompute_embeddings.py)
Output: classifier/nn_weights.pt       (checkpoint v4: pesi + soglie di decisione)
        classifier/training_curves.png (loss train/val per task)

Uso:  python train_nn.py                 addestra e salva
      python train_nn.py --no-save       prova senza sovrascrivere i pesi
      python train_nn.py --seed 43       altro seme (per controllare la stabilità)

IDEA GENERALE
  Ogni task ha una propria rete e una propria loss. Il training segue SEMPRE lo stesso schema:

    1. Si addestra con AdamW. A ogni epoca si misura la loss su train e su val con la STESSA
       formula, in modalità eval (niente dropout), così i due numeri sono confrontabili:
       se la val loss sale mentre la train loss scende, la rete sta memorizzando (overfitting).
    2. Il learning rate si dimezza quando la val loss smette di scendere (ReduceLROnPlateau),
       ma non scende mai sotto LR_MIN.
    3. Early stopping: ci si ferma quando la val loss non migliora per PATIENCE epoche e si
       ripristinano i pesi dell'epoca migliore.
    4. Solo ORA, a rete ferma, si tarano UNA VOLTA sul val le soglie di decisione
       (bias pipeline, soglia fallback, soglia follow-up). Il test non partecipa a nulla.

  Perché la val loss come criterio unico: è una misura continua e poco rumorosa. Una metrica come
  la macro-F1 cambia a salti con pochi record (le classi pipeline in val ne hanno 24-40) e, se
  calcolata a ogni epoca con una ricerca di soglie, finirebbe per "adattarsi" al val. Una rete con
  val loss minima ha inoltre probabilità ben calibrate, e le soglie si tarano su probabilità sensate.
"""

import argparse
import pickle
import random

import numpy as np
import torch
import torch.nn.functional as F
import torch.optim as optim
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score
from torch.utils.data import DataLoader, TensorDataset

import config
from domains import DOMAIN_NAMES
from classifier_config import EMBEDDINGS_PATH, WEIGHTS_PATH
from model_architecture import (
    build_model, N_MONO, N_CLASSES, decide_domain, decide_difficulty,
    CKPT_VERSION, CKPT_VERSION_KEY, CKPT_STATE_KEY, CKPT_PARAMS_KEY, CKPT_METRICS_KEY, CKPT_CONFIG_KEY,
)

# ═════════════════════════════ IPERPARAMETRI ═════════════════════════════
# Ogni valore ha il suo range ragionevole: se esci dal range, di solito ottieni un sintomo preciso.

# LR (learning rate iniziale), range 1e-4 … 1e-3.
# È la dimensione del passo di AdamW. Troppo alto (>5e-3): la val loss oscilla e non converge.
# Troppo basso (<1e-4): servono centinaia di epoche e l'early stopping scatta prima della convergenza.
# Valore scelto con 3 semi (42-44) tra 1e-4, 3e-4, 1e-3, 3e-3: 3e-4 dà la val loss più bassa e la
# selezione dell'epoca più stabile (con 1e-3 la rete è già al minimo alla 2ª epoca). Viene dimezzato
# da solo quando serve (vedi LR_PATIENCE).
LR = 3e-4

# LR_MIN (pavimento del learning rate), fissato a 1e-6 come da requisito.
# Sotto questo valore un passo è così piccolo che i pesi non cambiano più in modo utile.
LR_MIN = 1e-6

# LR_FACTOR (di quanto si riduce il LR), range 0.2 … 0.5.
# 0.5 = si dimezza a ogni stallo: scende con gradualità e consente di raffinare la soluzione.
LR_FACTOR = 0.5

# LR_PATIENCE (epoche di stallo prima di ridurre il LR), range 3 … 6, SEMPRE minore di PATIENCE.
# Deve essere più corto dell'early stopping, altrimenti la rete si ferma prima di aver provato
# un LR più basso. Con 5 e PATIENCE 15 il LR ha il tempo di scendere due volte prima dello stop.
LR_PATIENCE = 5

# WEIGHT_DECAY (regolarizzazione L2 di AdamW), range 1e-3 … 1e-1.
# Spinge i pesi verso zero: riduce l'overfitting. Se il gap train-val resta alto, alzalo;
# se anche la train loss resta alta (la rete non impara), abbassalo.
WEIGHT_DECAY = 1e-2

# BATCH_SIZE (record per aggiornamento dei pesi), range 32 … 128.
# Batch piccoli = gradiente più rumoroso (aiuta a non memorizzare) ma più lento; grandi = più stabile.
BATCH_SIZE = 64

# MAX_EPOCHS (tetto massimo di epoche), range 100 … 300.
# È solo una rete di sicurezza: a fermare il training deve essere l'early stopping.
MAX_EPOCHS = 200

# PATIENCE (epoche senza miglioramento della val loss prima di fermarsi), range 10 … 25.
# Troppo bassa: ci si ferma su un plateau passeggero. Troppo alta: si allena inutilmente.
PATIENCE = 15

# MIN_DELTA (miglioramento minimo della val loss per contare come "miglioramento"), range 1e-4 … 1e-2.
# Evita di prendere per progresso le fluttuazioni nella terza cifra decimale.
MIN_DELTA = 1e-3

# MAX_FP_RATE (vincolo sul bias pipeline): quota massima di query mono-dominio che il modello può
# promuovere a pipeline per errore. Vive in config.py perché è una scelta di prodotto: una
# false-pipeline costa due chiamate ai modelli grandi invece di una.
MAX_FP_RATE = config.NEURAL_CLASSIFIER_SETTINGS['max_false_pipeline_rate']

# HARD_RECALL_WEIGHT (costo asimmetrico per la soglia fallback), range 0.5 … 0.8.
# Mandare una query difficile al modello piccolo (risposta scadente) costa più che mandarne una
# facile al modello grande (solo più lento). 0.7 = una query difficile pesa il 70% del punteggio.
HARD_RECALL_WEIGHT = 0.7

SEED = 42   # fissa pesi iniziali, ordine dei batch e dropout: due run con lo stesso seme coincidono
# ═════════════════════════════════════════════════════════════════════════

# Griglie di calibrazione. Ordinate per vicinanza al valore neutro: a parità di punteggio
# vince la soglia meno estrema.
def _centered(grid, center):
    return sorted((float(g) for g in grid), key=lambda g: abs(g - center))

BIAS_GRID    = _centered(np.arange(-3.0, 3.01, 0.25), 0.0)    # bias sui logit pipeline
FALLBACK_GRID = _centered(np.arange(0.20, 0.71, 0.05), 0.5)   # soglia su P(d>1)
FOLLOWUP_GRID = _centered(np.arange(0.20, 0.81, 0.05), 0.5)   # soglia su P(follow-up)


def set_seed(s: int):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)


# ═════════════════════════════ LOSS (una per task, identica su train e val) ═════════════════════════════
def make_domain_loss(y_train):
    """
    Cross-entropy a 7 classi con pesi di classe.

        CE = - peso[y] · log softmax(logit)[y]        peso[c] ∝ 1 / √(numero di esempi di c)

    Le classi pipeline hanno 94-198 esempi in train contro i ~880 di general: senza pesi la rete
    imparerebbe a ignorarle. La radice quadrata è una via di mezzo: 1/freq pareggerebbe del tutto
    le classi ma amplificherebbe il rumore dei pochi esempi rari. I pesi hanno media 1, così la
    scala della loss resta confrontabile. Si calcolano SOLO sul train.
    """
    cnt = torch.bincount(y_train, minlength=N_CLASSES).float().clamp(min=1)
    w = (cnt.sum() / (N_CLASSES * cnt)).sqrt()
    w = w / w.mean()
    print("      pesi classe: " + " ".join(f"{n}={v:.2f}" for n, v in zip(DOMAIN_NAMES, w.tolist())))
    return lambda lg, y: F.cross_entropy(lg, y, weight=w)


def difficulty_loss(lg, y):
    """
    CORAL: due domande binarie indipendenti, "d>1?" e "d>2?", ciascuna con BCE; la loss è la media.
    Esempio: y=2 (difficoltà 3) → target [1,1]; y=1 (difficoltà 2) → [1,0]; y=0 → [0,0].
    """
    target = torch.stack([(y >= 1), (y >= 2)], dim=1).float()
    return F.binary_cross_entropy_with_logits(lg, target)


def followup_loss(lg, y):
    """BCE binaria: -[y·log σ(z) + (1-y)·log(1-σ(z))], media sui record. Rapporto pos:neg ≈ 1:1."""
    return F.binary_cross_entropy_with_logits(lg.squeeze(1), y)


# ═════════════════════════════ TRAINING GENERICO ═════════════════════════════
def fit(name, model, X, Y, loss_fn):
    """
    Allena `model` con loss_fn. Restituisce i pesi dell'epoca con la val loss più bassa e lo storico.

    Per ogni epoca:
      • fase train: un passaggio sui dati a mini-batch, con dropout attivo, che aggiorna i pesi;
      • fase eval: train loss e val loss sull'INTERO split, dropout spento, stessa loss_fn.
        La train loss "vera" è quella di eval, non la media dei batch (quella è gonfiata dal dropout
        e cambia a ogni batch): solo così il gap train-val misura l'overfitting.
    """
    print(f"\n[{name.upper()}] {sum(p.numel() for p in model.parameters()):,} parametri")
    opt = optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    sched = optim.lr_scheduler.ReduceLROnPlateau(
        opt, mode='min', factor=LR_FACTOR, patience=LR_PATIENCE,
        threshold=MIN_DELTA, threshold_mode='abs', min_lr=LR_MIN)
    loader = DataLoader(TensorDataset(X['train'], Y['train']), batch_size=BATCH_SIZE, shuffle=True)

    hist = {'train': [], 'val': []}
    best = {'val': float('inf'), 'epoch': 0, 'state': None}
    stalled = 0

    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        for xb, yb in loader:
            opt.zero_grad()
            loss_fn(model(xb), yb).backward()
            opt.step()

        model.eval()
        with torch.no_grad():
            tr = loss_fn(model(X['train']), Y['train']).item()
            vl = loss_fn(model(X['val']),   Y['val']).item()
        sched.step(vl)
        hist['train'].append(tr); hist['val'].append(vl)

        if vl < best['val'] - MIN_DELTA:
            best.update(val=vl, epoch=epoch, state={k: v.clone() for k, v in model.state_dict().items()})
            stalled = 0
        else:
            stalled += 1

        if epoch % 10 == 0 or stalled == 0:
            print(f"  ep={epoch:3d} | train={tr:.4f} val={vl:.4f} | best={best['val']:.4f}@{best['epoch']} "
                  f"| lr={opt.param_groups[0]['lr']:.1e}{' ★' if stalled == 0 else ''}")
        if stalled >= PATIENCE:
            print(f"  ⏹  Early stopping a epoca {epoch}")
            break

    model.load_state_dict(best['state'])
    model.eval()
    print(f"  → epoca migliore {best['epoch']} | train={hist['train'][best['epoch'] - 1]:.4f} "
          f"val={best['val']:.4f}")
    return {'model': model, 'state': best['state'], 'epoch': best['epoch'], 'hist': hist}


def logits_of(model, x):
    with torch.no_grad():
        return model(x)


# ═════════════════════════════ CALIBRAZIONE DELLE SOGLIE (una volta, sul val) ═════════════════════════════
def domain_scores(lg, y, bias):
    """(macro-F1 sulle 7 classi, false-pipeline rate = mono classificate come pipeline)."""
    pred = decide_domain(lg, bias).numpy()
    yn   = y.numpy()
    f1   = f1_score(yn, pred, labels=list(range(N_CLASSES)), average='macro', zero_division=0)
    mono = yn < N_MONO
    return float(f1), float(((pred >= N_MONO) & mono).sum() / max(mono.sum(), 1))


def calibrate_domain(lg, y):
    """
    Sceglie il bias pipeline: massima macro-F1 tra i bias con false-pipeline rate ≤ MAX_FP_RATE.
    Se nessun bias rispetta il vincolo, prende quello con meno false pipeline.
    """
    best_key, best_b = None, 0.0
    for b in BIAS_GRID:
        f1, fp = domain_scores(lg, y, b)
        key = (fp <= MAX_FP_RATE, f1 if fp <= MAX_FP_RATE else -fp)   # tupla: prima il vincolo, poi F1
        if best_key is None or key > best_key:
            best_key, best_b = key, b
    return {'bias_pipe': float(best_b)}


def difficulty_scores(lg, y, thr):
    """
    (tier-score, accuratezza a 3 livelli). A runtime conta solo il tier (difficoltà 1 → fallback).
    tier-score = media pesata di due recall: query facili al modello piccolo e query difficili al grande.
    """
    yn   = y.numpy()
    pred = decide_difficulty(lg, thr).numpy() - 1
    easy, p_easy = yn == 0, pred == 0
    rec_easy = (p_easy & easy).sum() / max(easy.sum(), 1)
    rec_hard = (~p_easy & ~easy).sum() / max((~easy).sum(), 1)
    tier = (1 - HARD_RECALL_WEIGHT) * rec_easy + HARD_RECALL_WEIGHT * rec_hard
    return float(tier), float((pred == yn).mean())


def calibrate_difficulty(lg, y):
    best_s, best_t = -1.0, 0.5
    for t in FALLBACK_GRID:
        s = difficulty_scores(lg, y, t)[0]
        if s > best_s:
            best_s, best_t = s, t
    return {'thr_fallback': float(best_t)}


def followup_scores(lg, y, thr):
    """(precision, recall, F1, false-positive rate, AP) sui record passati (solo con history)."""
    yn   = y.numpy().astype(int)
    prob = torch.sigmoid(lg.squeeze(1)).numpy()
    pred = (prob >= thr).astype(int)
    tp = int(((pred == 1) & (yn == 1)).sum()); fp = int(((pred == 1) & (yn == 0)).sum())
    fn = int(((pred == 0) & (yn == 1)).sum()); tn = int(((pred == 0) & (yn == 0)).sum())
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    ap = float(average_precision_score(yn, prob)) if 0 < yn.sum() < len(yn) else 0.0
    return p, r, f1, fp / max(fp + tn, 1), ap


def calibrate_followup(lg, y):
    """Soglia che massimizza la F1 sul val (solo record con history)."""
    best_f1, best_t = -1.0, 0.5
    for t in FOLLOWUP_GRID:
        f1 = followup_scores(lg, y, t)[2]
        if f1 > best_f1:
            best_f1, best_t = f1, t
    return {'thr': float(best_t)}


# ═════════════════════════════ GRAFICO ═════════════════════════════
def plot_curves(results: dict, path):
    fig, axes = plt.subplots(1, len(results), figsize=(5 * len(results), 3.8))
    for ax, (name, r) in zip(axes, results.items()):
        ep = range(1, len(r['hist']['val']) + 1)
        ax.plot(ep, r['hist']['train'], label='train'); ax.plot(ep, r['hist']['val'], label='val')
        ax.axvline(r['epoch'], ls='--', c='gray'); ax.set_title(f'{name} — loss'); ax.set_xlabel('epoca')
        ax.legend()
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)


# ═════════════════════════════ MAIN ═════════════════════════════
def train(seed: int = SEED, save: bool = True) -> dict:
    print(f"[1/4] Caricamento: {EMBEDDINGS_PATH}  (seed={seed}, save={save})")
    with open(EMBEDDINGS_PATH, 'rb') as f:
        data = pickle.load(f)

    splits = ('train', 'val', 'test')
    idx = {k: data['splits'][k] for k in splits}
    X   = {k: data['embeddings'][idx[k]] for k in splits}
    Yc  = {k: data['class_labels'][idx[k]] for k in splits}
    Yd  = {k: data['difficulty_labels'][idx[k]] for k in splits}
    Yf  = {k: data['is_followup_labels'][idx[k]] for k in splits}
    hist_mask = {k: data['has_history'][idx[k]] > 0.5 for k in splits}
    # Il follow-up si allena e si valuta SOLO sui record con history: senza history la risposta è
    # sempre "no" (a runtime lo impone un gate in nn_classifier) e inflazionerebbe le metriche.
    Xh  = {k: X[k][hist_mask[k]] for k in splits}
    Yh  = {k: Yf[k][hist_mask[k]] for k in splits}
    print(f"      train={len(idx['train'])} val={len(idx['val'])} test={len(idx['test'])} | "
          f"follow-up (record con history): {len(Xh['train'])}/{len(Xh['val'])}/{len(Xh['test'])}")

    print("\n[2/4] Training (3 task indipendenti)")
    losses = {'domain': make_domain_loss(Yc['train']), 'difficulty': difficulty_loss, 'followup': followup_loss}
    data_of = {'domain': (X, Yc), 'difficulty': (X, Yd), 'followup': (Xh, Yh)}
    res = {}
    for task in ('domain', 'difficulty', 'followup'):
        set_seed(seed)                       # stesso punto di partenza per ogni task, indipendente dall'ordine
        res[task] = fit(task, build_model(task), *data_of[task], losses[task])

    print("\n[3/4] Calibrazione soglie sul VAL e report finale")
    lg = {t: {k: logits_of(res[t]['model'], data_of[t][0][k]) for k in splits} for t in res}
    params = {
        'domain':     calibrate_domain(lg['domain']['val'], Yc['val']),
        'difficulty': calibrate_difficulty(lg['difficulty']['val'], Yd['val']),
        'followup':   calibrate_followup(lg['followup']['val'], Yh['val']),
    }
    bias, thr_d, thr_f = (params['domain']['bias_pipe'], params['difficulty']['thr_fallback'],
                          params['followup']['thr'])
    print(f"  soglie: bias_pipe={bias:+.2f} | thr_fallback={thr_d:.2f} | thr_followup={thr_f:.2f}")

    M = {}
    print(f"\n  {'':6s}{'loss-dom':>9s}{'loss-dif':>9s}{'loss-fu':>8s} |{'dom-F1':>7s}{'FP':>7s}"
          f"{'tier':>7s}{'acc3':>7s} |{'fu-P':>6s}{'fu-R':>6s}{'fu-F1':>6s}{'fu-FPR':>7s}{'fu-AP':>6s}")
    for k in splits:
        l = [losses[t](lg[t][k], data_of[t][1][k]).item() for t in ('domain', 'difficulty', 'followup')]
        f1, fp = domain_scores(lg['domain'][k], Yc[k], bias)
        tier, acc3 = difficulty_scores(lg['difficulty'][k], Yd[k], thr_d)
        p, r, f1h, fpr, ap = followup_scores(lg['followup'][k], Yh[k], thr_f)
        M[k] = dict(loss_dom=l[0], loss_dif=l[1], loss_fu=l[2], dom_f1=f1, fp=fp, tier=tier, acc3=acc3,
                    fu_p=p, fu_r=r, fu_f1=f1h, fu_fpr=fpr, fu_ap=ap)
        print(f"  {k:6s}{l[0]:9.4f}{l[1]:9.4f}{l[2]:8.4f} |{f1:7.3f}{fp:7.3f}{tier:7.3f}{acc3:7.3f} |"
              f"{p:6.3f}{r:6.3f}{f1h:6.3f}{fpr:7.3f}{ap:6.3f}")
    print("  (le soglie sono tarate sul val: i numeri del val sono ottimistici, il test è il riferimento)")
    gap = lambda key: M['val'][key] - M['train'][key]
    print(f"  gap val-train delle loss: dom={gap('loss_dom'):+.3f} dif={gap('loss_dif'):+.3f} fu={gap('loss_fu'):+.3f}")

    pred = decide_domain(lg['domain']['test'], bias).numpy()
    labels = list(range(N_CLASSES))
    per_cls = f1_score(Yc['test'].numpy(), pred, labels=labels, average=None, zero_division=0)
    print("\n  F1 per classe (test): " + " | ".join(f"{n}={v:.3f}" for n, v in zip(DOMAIN_NAMES, per_cls)))
    print("  Confusione dominio test (righe=atteso):")
    for i, row in enumerate(confusion_matrix(Yc['test'].numpy(), pred, labels=labels)):
        print(f"   {i}={DOMAIN_NAMES[i]:15s}" + "".join(f"{v:5d}" for v in row))

    if save:
        curves = WEIGHTS_PATH.parent / 'training_curves.png'
        curves.parent.mkdir(parents=True, exist_ok=True)
        plot_curves(res, curves)
        T = M['test']
        torch.save({
            CKPT_VERSION_KEY: CKPT_VERSION,
            'domain':     {CKPT_STATE_KEY: res['domain']['state'], CKPT_PARAMS_KEY: params['domain'],
                           CKPT_METRICS_KEY: {'test_f1': T['dom_f1'], 'test_fp_rate': T['fp']}},
            'difficulty': {CKPT_STATE_KEY: res['difficulty']['state'], CKPT_PARAMS_KEY: params['difficulty'],
                           CKPT_METRICS_KEY: {'test_tier': T['tier'], 'test_acc3': T['acc3']}},
            'followup':   {CKPT_STATE_KEY: res['followup']['state'], CKPT_PARAMS_KEY: params['followup'],
                           CKPT_METRICS_KEY: {'test_f1_hist': T['fu_f1'], 'test_fpr_hist': T['fu_fpr'],
                                              'test_ap_hist': T['fu_ap']}},
            CKPT_CONFIG_KEY: {'lr': LR, 'lr_min': LR_MIN, 'weight_decay': WEIGHT_DECAY, 'batch_size': BATCH_SIZE,
                              'patience': PATIENCE, 'max_fp_rate': float(MAX_FP_RATE), 'seed': seed},
        }, WEIGHTS_PATH)
        print(f"\n[4/4] ✅ Salvato → {WEIGHTS_PATH}  ({WEIGHTS_PATH.stat().st_size / 1024:.1f} KB) | curve → {curves}")
    else:
        print("\n[4/4] --no-save: pesi NON salvati.")

    return {'metrics': M, 'params': params, 'epochs': {t: res[t]['epoch'] for t in res}}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=SEED)
    ap.add_argument('--no-save', action='store_true')
    a = ap.parse_args()
    train(a.seed, save=not a.no_save)
