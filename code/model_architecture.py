"""
model_architecture.py — CYA N | Architettura NN condivisa (training +
inference) e contratto delle chiavi del checkpoint.
[report_patch.md DUP-1, CFG-5]
"""

import torch.nn as nn
from classifier_config import EMBEDDING_DIM


class MultiTaskMLP(nn.Module):
    """
    Backbone condiviso + 3 teste specializzate.
    Forward restituisce LOGIT GREZZI (nessuna attivazione finale):
    training usa BCEWithLogitsLoss/CrossEntropyLoss, le attivazioni
    (sigmoid/softmax) vengono applicate solo a inference time.
    """
    def __init__(self):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(EMBEDDING_DIM, 256),
            nn.LayerNorm(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Dropout(0.2),
        )
        self.domain_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 4),
        )
        self.difficulty_head = nn.Sequential(
            nn.Linear(128, 32),
            nn.ReLU(),
            nn.Linear(32, 3),
        )
        self.followup_head = nn.Linear(128, 1)

    def forward(self, x):
        h = self.backbone(x)
        return (
            self.domain_head(h),
            self.difficulty_head(h),
            self.followup_head(h),
        )


# --- Contratto chiavi checkpoint (CFG-5) ---
# Unica fonte di verità: train_nn.py scrive, nn_classifier.py legge.
# Un typo su un solo lato produceva un .get() silenzioso -> None/'N/A'
# invece di un errore chiaro.
CKPT_STATE_DICT_KEY       = 'model_state_dict'
CKPT_BEST_VAL_F1_KEY      = 'best_val_f1_domain'
CKPT_TEST_F1_DOMAIN_KEY   = 'test_f1_domain'
CKPT_TEST_DIFF_ACC_KEY    = 'test_diff_acc'
CKPT_TEST_FOLLOWUP_F1_KEY = 'test_followup_f1'
CKPT_CONFIG_KEY           = 'config'