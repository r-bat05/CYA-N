"""
domains.py — CYA N | Unica fonte di verità per domini e pipeline
==================================================================
[report_patch.md DUP-2, DUP-3] Sostituisce le liste/mapping duplicati in
nn_classifier.py, precompute_embeddings.py, train_nn.py,
step4_evaluation.py, build_dataset_v2.py. Zero dipendenze pesanti.
"""

# Domini mono (ordine canonico — class_id 0-3, ordine output domain_head NN)
MONO_DOMAINS = ['coding', 'math', 'rights', 'general']

# Pipeline canoniche: class_id -> (domain_a, domain_b).
# domain_a = agente draft (primo), domain_b = agente integratore (finale).
# L'ORDINE è semantico (vedi main.py Fase 1/2/3), non derivabile da un
# insieme non ordinato di domini.
PIPELINE_CLASSES = {
    4: ('math',   'coding'),
    5: ('rights', 'coding'),
    6: ('rights', 'math'),
}

# class_id -> nome esteso (es. 'math->coding'). Derivato.
DOMAIN_NAMES = MONO_DOMAINS + [
    f"{a}->{b}" for a, b in PIPELINE_CLASSES.values()
]

# frozenset({domain_a, domain_b}) -> class_id. Derivato (era mantenuto a
# mano come _PIPELINE_ORDER in nn_classifier.py).
PIPELINE_ORDER = {
    frozenset(pair): class_id for class_id, pair in PIPELINE_CLASSES.items()
}

# Coppie bridge NON-pipeline usate in db_query.py::BRIDGE_SENTENCES
# (general+math, general+rights — esempi negativi, non pipeline vere).
_NON_PIPELINE_BRIDGES = [
    ('general', 'math'), ('math', 'general'),
    ('general', 'rights'), ('rights', 'general'),
]


def _build_bridge_map():
    """
    (d1, d2) -> (nome_pipeline | None, is_pipeline: bool), entrambe le
    direzioni. Derivato da PIPELINE_CLASSES — era BRIDGE_MAP in
    build_dataset_v2.py, 10 entry mantenute a mano indipendentemente.
    """
    m = {}
    for class_id, (a, b) in PIPELINE_CLASSES.items():
        name = DOMAIN_NAMES[class_id]
        m[(a, b)] = (name, True)
        m[(b, a)] = (name, True)
    for pair in _NON_PIPELINE_BRIDGES:
        m[pair] = (None, False)
    return m


BRIDGE_MAP = _build_bridge_map()