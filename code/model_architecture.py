"""
model_architecture.py — CYA N | 3 reti INDIPENDENTI (dominio / difficoltà / follow-up),
funzioni di decisione condivise da training e inferenza, contratto delle chiavi del checkpoint.

Ogni rete è un piccolo MLP che parte dall'embedding MiniLM (384 numeri) e restituisce LOGIT
GREZZI: sigmoid/softmax si applicano fuori, così loss e decisione restano separate.

  DomainMLP     384→256→128→7   softmax: classi 0-3 mono-dominio, 4-6 pipeline (ordine DOMAIN_NAMES)
  DifficultyMLP 384→180→45→1    regressione ordinale CORAL → 2 logit [P(d>1), P(d>2)]
  FollowupMLP   384→180→64→1    sigmoid → P(follow-up)

Struttura di ogni MLP: Linear → LayerNorm → ReLU → Dropout, ripetuta per ogni livello nascosto.
LayerNorm (e non BatchNorm) perché funziona identica con 1 solo campione, come a runtime.

[v4] Rimossi rispetto alla v3: testa multi-label (tau_pair), scala del dropout, ensemble di modelli
e descrittore 'arch' nel checkpoint. Erano opzioni spente di default e rendevano il checkpoint e il
loader più complessi di quanto servisse.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from classifier_config import EMBEDDING_DIM
from domains import MONO_DOMAINS, DOMAIN_NAMES

N_MONO    = len(MONO_DOMAINS)   # 4
N_CLASSES = len(DOMAIN_NAMES)   # 7


def _mlp(d_in: int, hidden: tuple, d_out: int, drops: tuple) -> nn.Sequential:
    layers, prev = [], d_in
    for h, p in zip(hidden, drops):
        layers += [nn.Linear(prev, h), nn.LayerNorm(h), nn.ReLU(), nn.Dropout(p)]
        prev = h
    layers.append(nn.Linear(prev, d_out))
    return nn.Sequential(*layers)


class DomainMLP(nn.Module):
    """384→256→128→7. Loss: cross-entropy con pesi di classe (vedi train_nn.py)."""
    def __init__(self):
        super().__init__()
        self.net = _mlp(EMBEDDING_DIM, (256, 128), N_CLASSES, (0.3, 0.2))

    def forward(self, x):                       # [N,384] → [N,7]
        return self.net(x)


class DifficultyMLP(nn.Module):
    """
    Regressione ordinale (CORAL): la rete produce un solo punteggio latente z ("quanto è difficile"),
    e due bias ORDINATI trasformano z in due probabilità:
        P(d>1) = sigmoid(z + b1)      P(d>2) = sigmoid(z + b2)      con b2 = b1 - softplus(gap) < b1
    Poiché b2 < b1, vale sempre P(d>2) ≤ P(d>1): le previsioni non possono contraddirsi.
    Output [N,2] = i due logit. Loss: BCE sui due target [d>1, d>2].
    """
    def __init__(self):
        super().__init__()
        self.net = _mlp(EMBEDDING_DIM, (180, 45), 1, (0.3, 0.2))
        self.b1  = nn.Parameter(torch.tensor(0.0))
        self.gap = nn.Parameter(torch.tensor(0.0))

    def forward(self, x):
        z  = self.net(x)                                         # [N,1]
        b2 = self.b1 - F.softplus(self.gap)
        return z + torch.stack([self.b1, b2]).unsqueeze(0)       # [N,1]+[1,2] → [N,2]


class FollowupMLP(nn.Module):
    """384→180→64→1. Loss: BCE. Addestrata e valutata solo sui record con history."""
    def __init__(self):
        super().__init__()
        self.net = _mlp(EMBEDDING_DIM, (180, 64), 1, (0.3, 0.2))

    def forward(self, x):                       # [N,384] → [N,1]
        return self.net(x)


MODEL_CLASSES = {'domain': DomainMLP, 'difficulty': DifficultyMLP, 'followup': FollowupMLP}


def build_model(task: str) -> nn.Module:
    return MODEL_CLASSES[task]()


# ─── Decisione (UNICA fonte di verità: train_nn.py e nn_classifier.py importano da qui) ───

def decide_domain(logits: torch.Tensor, bias_pipe: float = 0.0) -> torch.Tensor:
    """
    argmax sui 7 logit dopo aver sommato `bias_pipe` ai logit delle classi pipeline (4-6).
    bias>0 → più pipeline (meno miss, più false-pipeline); bias<0 → l'opposto.
    Accetta [7] o [N,7]. Il bias è tarato una volta sul VAL a fine training.
    """
    adj = logits.clone()
    adj[..., N_MONO:] += bias_pipe
    return adj.argmax(dim=-1)


def decide_difficulty(logits: torch.Tensor, thr_fallback: float = 0.5) -> torch.Tensor:
    """
    Accetta [2] o [N,2]. Restituisce 1/2/3.
    P(d>1) < thr_fallback → 1 (tier FALLBACK). Abbassare thr = meno query al modello piccolo.
    Altrimenti 3 se P(d>2) ≥ 0.5, altrimenti 2.
    """
    p    = torch.sigmoid(logits)
    tier = (p[..., 0] >= thr_fallback).long()
    hard = (p[..., 1] >= 0.5).long() * tier
    return 1 + tier + hard


# ─── Contratto checkpoint (train_nn.py scrive, nn_classifier.py legge) ───
CKPT_VERSION      = 4                      # v4: un solo state_dict per task, niente 'arch'
CKPT_VERSION_KEY  = 'version'
CKPT_TASKS        = ('domain', 'difficulty', 'followup')   # chiavi di primo livello
CKPT_STATE_KEY    = 'state_dict'
CKPT_PARAMS_KEY   = 'params'      # domain: bias_pipe | difficulty: thr_fallback | followup: thr
CKPT_METRICS_KEY  = 'metrics'
CKPT_CONFIG_KEY   = 'config'
