"""
build_dataset_v2.py — Step 1 del branch build_classifier_NN

Sorgenti:
  1. code/old_files/db_query.py  → INTENT_SENTENCES + BRIDGE_SENTENCES (~900 frasi seed)
  2. EDGE_CASES hardcoded        → follow-up, switch dominio, false/true pipeline, ambigue
  3. Augmentation lessicale      → sinonimi su classi sotto TARGET

Output: code/dataset_v2.jsonl  (una riga JSON per record, con campo "split")

Esecuzione (dalla root del progetto):
    python code/build_dataset_v2.py
"""

import sys, json, random
from collections import defaultdict, Counter
from pathlib import Path

# ── Path setup ─────────────────────────────────────────────────────────────────
CODE_DIR = Path(__file__).resolve().parent          # .../code/
sys.path.insert(0, str(CODE_DIR / 'old_files'))
from db_query import INTENT_SENTENCES, BRIDGE_SENTENCES

random.seed(42)

# ── Costanti ───────────────────────────────────────────────────────────────────
TARGET_MONO = 250   # min esempi per ogni dominio mono (coding/math/rights/general)
TARGET_PIPE = 80    # min esempi per ogni tipo pipeline
OUTPUT_PATH = CODE_DIR / 'dataset_v2.jsonl'

# Mapping chiavi BRIDGE_SENTENCES → (pipeline_type, is_pipeline)
# Le 3 pipeline supportate dal sistema; le coppie con "general" NON sono pipeline
BRIDGE_MAP = {
    ('coding', 'rights'):  ('rights->coding', True),
    ('rights', 'coding'):  ('rights->coding', True),
    ('coding', 'math'):    ('math->coding',   True),
    ('math', 'coding'):    ('math->coding',   True),
    ('math', 'rights'):    ('rights->math',   True),
    ('rights', 'math'):    ('rights->math',   True),
    ('general', 'math'):   (None, False),
    ('math', 'general'):   (None, False),
    ('general', 'rights'): (None, False),
    ('rights', 'general'): (None, False),
}

# Keyword per stima automatica difficulty dal testo
KW_D3 = {'implementa','dimostra','analizza','ottimizza','algoritmo','teorema',
          'normativa','decomposizione','convergenza','architettura','derivazione',
          'simulazione','distribuzione','formalizza'}
KW_D2 = {'scrivi','crea','sviluppa','configura','spiega','calcola',
          'risolvi','costruisci','gestisci','verifica','codice'}

# Sinonimi per augmentation lessicale (solo verbi all'imperativo, forma usata nel seed)
SYNONYMS = {
    'implementa': ['sviluppa', 'crea', 'realizza', 'costruisci'],
    'scrivi':     ['realizza', 'crea', 'produci'],
    'spiega':     ['descrivi', 'illustra', 'chiarisci'],
    'calcola':    ['determina', 'trova', 'computa'],
    'sviluppa':   ['implementa', 'crea', 'costruisci'],
    'crea':       ['sviluppa', 'implementa', 'costruisci'],
    'analizza':   ['esamina', 'valuta', 'studia'],
    'dimostra':   ['prova', 'verifica', 'argomenta'],
    'ottimizza':  ['migliora', 'potenzia', 'perfeziona'],
    'configura':  ['imposta', 'predisponi'],
    'verifica':   ['controlla', 'valida', 'accerta'],
}

# ── Shortcut label sets ────────────────────────────────────────────────────────
_C  = {"coding":1,"math":0,"rights":0,"general":0}
_M  = {"coding":0,"math":1,"rights":0,"general":0}
_R  = {"coding":0,"math":0,"rights":1,"general":0}
_G  = {"coding":0,"math":0,"rights":0,"general":1}
_CM = {"coding":1,"math":1,"rights":0,"general":0}   # math->coding
_RC = {"coding":1,"math":0,"rights":1,"general":0}   # rights->coding
_RM = {"coding":0,"math":1,"rights":1,"general":0}   # rights->math

def _r(query, labels, diff, is_pipe=False, pipe_type=None, hist=None):
    return {"query": query, "history": hist or [],
            "domain_labels": dict(labels), "is_pipeline": is_pipe,
            "pipeline_type": pipe_type, "difficulty": diff, "split": None}

# ── Edge cases manuali ─────────────────────────────────────────────────────────
# Questi esempi coprono i pattern che db_query.py NON ha:
#   - follow-up corti (query senza contesto proprio, senso solo col dominio precedente)
#   - cambio dominio (storia tecnica → query completamente diversa, NO sticky routing)
#   - false pipeline (sembra multi-domain ma NON lo è)
#   - true pipeline esplicite corte (per rafforzare il segnale pipeline)
#   - query ambigue/di sistema (→ general)

EDGE_CASES = [

    # ── Follow-up dopo CODING ─────────────────────────────────────────────────
    _r("perché?",                 _C, 1, hist=["Come funziona la ricorsione in Python?"]),
    _r("e quindi?",               _C, 1, hist=["Spiega la differenza tra TCP e UDP."]),
    _r("non ho capito",           _C, 1, hist=["Come si implementa una coda con priorità in Python?"]),
    _r("puoi fare un esempio?",   _C, 1, hist=["Spiega cos'è il polimorfismo in OOP."]),
    _r("spiega meglio",           _C, 1, hist=["Come funziona l'algoritmo di Dijkstra?"]),
    _r("e il caso peggiore?",     _C, 2, hist=["Implementa quicksort e analizza la complessità."]),
    _r("riesci a farlo in Java?", _C, 1, hist=["Scrivi codice Python per ordinare una lista."]),
    _r("c'è un modo più efficiente?", _C, 2, hist=["Come cerco un elemento in una lista Python?"]),
    _r("fammi vedere il codice",  _C, 1, hist=["Come funziona il pattern Observer?"]),
    _r("e il testing?",           _C, 2, hist=["Come si struttura un'architettura microservizi?"]),

    # ── Follow-up dopo MATH ───────────────────────────────────────────────────
    _r("perché?",                       _M, 1, hist=["Dimostra il teorema fondamentale del calcolo."]),
    _r("e quindi?",                     _M, 1, hist=["Calcola la derivata di f(x) = x^3 + 2x - 1."]),
    _r("non ho capito la dimostrazione",_M, 1, hist=["Dimostra il teorema di Cauchy."]),
    _r("puoi fare un esempio numerico?",_M, 1, hist=["Spiega come si calcola la covarianza."]),
    _r("rispiega il passaggio 2",       _M, 1, hist=["Dimostra per induzione la somma dei primi n numeri."]),
    _r("e nel caso 3D?",                _M, 2, hist=["Calcola il gradiente di f(x,y) = x^2 + 3xy."]),
    _r("perché si usa il logaritmo?",   _M, 2, hist=["Spiega la discesa del gradiente."]),
    _r("come mai converge?",            _M, 2, hist=["Spiega il metodo delle potenze per gli autovalori."]),

    # ── Follow-up dopo RIGHTS ─────────────────────────────────────────────────
    _r("e nel mio caso?",       _R, 1, hist=["Cosa prevede il GDPR per i dati personali?"]),
    _r("cosa significa?",       _R, 1, hist=["Il D.Lgs. 231/2001 prevede la responsabilità degli enti."]),
    _r("e le sanzioni?",        _R, 1, hist=["Come funziona la violazione del GDPR per una PMI?"]),
    _r("rispiega meglio",       _R, 1, hist=["Qual è la differenza tra contratto a termine e indeterminato?"]),
    _r("quindi posso farlo?",   _R, 1, hist=["Cosa prevede la legge per il licenziamento?"]),
    _r("e la multa quanto è?",  _R, 1, hist=["Quali infrazioni del GDPR sono più comuni?"]),
    _r("è sempre così?",        _R, 1, hist=["Quando si applica la responsabilità solidale nell'appalto?"]),

    # ── Follow-up dopo GENERAL ────────────────────────────────────────────────
    _r("perché?",       _G, 1, hist=["Ciao! Come stai?"]),
    _r("e quindi?",     _G, 1, hist=["Consigliami un film di fantascienza."]),
    _r("ne conosci altri?", _G, 1, hist=["Dammi una ricetta per la pasta al pomodoro."]),
    _r("spiega meglio", _G, 1, hist=["Cos'è la fotosintesi clorofilliana?"]),
    _r("come mai?",     _G, 1, hist=["L'acqua bolle a 100 gradi a livello del mare."]),
    _r("non ho capito", _G, 1, hist=["Spiega la differenza tra DNA e RNA."]),
    _r("davvero?",      _G, 1, hist=["Il ghiaccio si forma a 0 gradi Celsius."]),

    # ── Query ambigue SENZA history (→ general) ───────────────────────────────
    _r("ciao, come stai?", _G, 1),
    _r("grazie!",          _G, 1),
    _r("ok",               _G, 1),
    _r("Dio esiste?",      _G, 1),
    _r("chi sei?",         _G, 1),
    _r("cosa ne pensi?",   _G, 1),
    _r("mi aiuti?",        _G, 1),
    _r("buongiorno",       _G, 1),
    _r("non so",           _G, 1),
    _r("2+2",              _M, 1),   # unica eccezione: math
    _r("chi ti ha creato?",_G, 1),
    _r("cosa sai fare?",   _G, 1),
    _r("aiuto",            _G, 1),

    # ── Cambio DOMINIO: storia tecnica → query completamente diversa ──────────
    # (il classificatore NON deve fare sticky routing su questi)
    _r("consigliami un ristorante a Roma",  _G, 1, hist=["Implementa server REST in Flask."]),
    _r("consigliami scarpe uomo",           _G, 1, hist=["Come funziona la fattorizzazione LU?"]),
    _r("cosa mangio stasera?",              _G, 1, hist=["Qual è la normativa GDPR sulla data retention?"]),
    _r("dammi una barzelletta",             _G, 1, hist=["Implementa il metodo di Runge-Kutta 4."]),
    _r("qual è la capitale della Francia?", _G, 1, hist=["Come configuro Kubernetes per il load balancing?"]),
    _r("consigliami un libro",              _G, 1, hist=["Dimostra il teorema di Pitagora con geometria euclidea."]),
    _r("chi ha vinto il mondiale 2022?",    _G, 1, hist=["Implementa la firma digitale RSA in Python."]),

    # ── FALSE pipeline: sembrano multi-domain ma sono mono ───────────────────
    # "codice" e "Python" NON attivano pipeline se la query è concettualmente semplice
    _r("codice Python per sommare una lista di numeri", _C, 1),
    _r("scrivi una funzione Python che calcola la media",_C, 1),
    _r("codice per stampare i numeri da 1 a 100",       _C, 1),
    _r("Python per leggere un file CSV",                _C, 1),
    _r("cosa dice la legge sul codice fiscale?",        _R, 1),  # "codice" ≠ coding
    _r("spiegami la normativa sui contratti di lavoro", _R, 2),
    _r("qual è il codice penale per il furto?",         _R, 1),  # "codice" ≠ coding
    _r("cos'è la media geometrica?",                    _M, 1),

    # ── TRUE pipeline ESPLICITE (segnale diretto) ─────────────────────────────
    _r("scrivi codice C++ per Pitagora con dimostrazione matematica completa",
       _CM, 3, True, "math->coding"),
    _r("implementa in Python Kruskal e dimostra correttezza con teoria dei grafi",
       _CM, 3, True, "math->coding"),
    _r("implementa regressione lineare multipla in Python e dimostra teoria minimi quadrati",
       _CM, 3, True, "math->coding"),
    _r("scrivi codice Python che implementa FFT e dimostra il teorema di Nyquist-Shannon",
       _CM, 3, True, "math->coding"),
    _r("scrivi script Python per TFR rispettando D.Lgs. 66/2003 con calcolo normativo",
       _RC, 3, True, "rights->coding"),
    _r("codice Python per busta paga conforme CCNL con calcolo IRPEF",
       _RC, 3, True, "rights->coding"),
    _r("codice per firma digitale eIDAS con RSA e normativa ETSI",
       _RC, 3, True, "rights->coding"),
    _r("script Python per calcolo TFR con applicazione normativa previdenziale INPS",
       _RC, 3, True, "rights->coding"),
    _r("qual è la formula matematica per calcolare l'indennità Jobs Act?",
       _RM, 3, True, "rights->math"),
    _r("dimostra matematicamente la soglia di usura secondo la Banca d'Italia",
       _RM, 3, True, "rights->math"),
    _r("calcola matematicamente il piano di ammortamento secondo normativa bancaria italiana",
       _RM, 3, True, "rights->math"),
]


# ── Helper functions ───────────────────────────────────────────────────────────

def estimate_difficulty(query: str, is_pipeline: bool, dominant_domain: str) -> int:
    """
    Stima la difficulty con euristiche sul testo.
    Logica:
      - Pipeline → sempre 3 (sono per definizione complesse)
      - General  → sempre 1 (domande generiche, conversazionali)
      - Tecnico corto (<6 parole) → 1
      - Contiene keyword complesse o >25 parole → 3
      - Contiene keyword medie o >10 parole → 2
      - Default tecnico → 2
    """
    if is_pipeline:
        return 3
    if dominant_domain == 'general':
        return 1
    q = query.lower()
    n = len(query.split())
    if n < 6:
        return 1
    if any(kw in q for kw in KW_D3) or n > 25:
        return 3
    if any(kw in q for kw in KW_D2) or n > 10:
        return 2
    return 2

def get_dominant_domain(domain_labels: dict) -> str:
    """Restituisce il dominio con valore 1 più alto (o il primo se pari)."""
    return max(domain_labels, key=domain_labels.get)

def get_class_key(record: dict) -> str:
    """
    Chiave stringa usata per la stratificazione dello split e il conteggio classi.
    Pipeline: usa pipeline_type (es. "math->coding")
    Mono:     usa il nome del dominio (es. "coding")
    Multi non-pipeline: usa domini uniti (es. "general+math")
    """
    if record['is_pipeline'] and record['pipeline_type']:
        return record['pipeline_type']
    active = [d for d, v in record['domain_labels'].items() if v == 1]
    return active[0] if len(active) == 1 else '+'.join(sorted(active))

def augment_query(query: str) -> str:
    """
    Sostituisce il PRIMO verbo riconoscibile con un sinonimo casuale.
    Restituisce stringa vuota se nessuna sostituzione è possibile.
    Preserva la capitalizzazione e la punteggiatura dell'originale.
    """
    words = query.split()
    for i, word in enumerate(words):
        clean = word.lower().rstrip('.,!?;:')
        if clean in SYNONYMS:
            synonym = random.choice(SYNONYMS[clean])
            if word[0].isupper():
                synonym = synonym[0].upper() + synonym[1:]
            suffix = word[len(clean):]          # punteggiatura finale originale
            words[i] = synonym + suffix
            return ' '.join(words)
    return ""


# ── Builders ───────────────────────────────────────────────────────────────────

def build_intent_records() -> list:
    """Converte INTENT_SENTENCES in record JSONL mono-domain."""
    records = []
    for domain, sentences in INTENT_SENTENCES.items():
        labels = {"coding": 0, "math": 0, "rights": 0, "general": 0}
        labels[domain] = 1
        for s in sentences:
            records.append({
                "query": s, "history": [],
                "domain_labels": dict(labels),
                "is_pipeline": False, "pipeline_type": None,
                "difficulty": estimate_difficulty(s, False, domain),
                "split": None
            })
    return records

def build_bridge_records() -> list:
    """Converte BRIDGE_SENTENCES in record JSONL multi-label (con pipeline flag)."""
    records = []
    for (d1, d2), sentences in BRIDGE_SENTENCES.items():
        labels = {"coding": 0, "math": 0, "rights": 0, "general": 0}
        labels[d1] = 1
        labels[d2] = 1
        pipeline_type, is_pipe = BRIDGE_MAP.get((d1, d2), (None, False))
        dominant = get_dominant_domain(labels)
        for s in sentences:
            records.append({
                "query": s, "history": [],
                "domain_labels": dict(labels),
                "is_pipeline": is_pipe, "pipeline_type": pipeline_type,
                "difficulty": estimate_difficulty(s, is_pipe, dominant),
                "split": None
            })
    return records

def augment_class(group: list, target: int) -> list:
    """
    Genera nuovi record per la classe 'group' finché raggiungiamo 'target'.
    Strategia: moltiplica il pool di partenza e prova augment_query su ognuno.
    Scarta le query già viste (deduplicazione).
    """
    extra = []
    seen  = {r['query'] for r in group}
    pool  = group * 30
    random.shuffle(pool)
    for r in pool:
        if len(group) + len(extra) >= target:
            break
        new_q = augment_query(r['query'])
        if new_q and new_q not in seen:
            seen.add(new_q)
            new_r = {k: (dict(v) if isinstance(v, dict) else v)
                     for k, v in r.items()}
            new_r['query'] = new_q
            extra.append(new_r)
    return extra

def stratified_split(records: list) -> list:
    """
    Split 70/15/15 stratificato per class_key.
    Imposta il campo 'split' su ogni record (train / val / test).
    Garantisce che ogni classe sia rappresentata in tutti e 3 i set.
    """
    groups = defaultdict(list)
    for r in records:
        groups[get_class_key(r)].append(r)

    result = []
    for group in groups.values():
        random.shuffle(group)
        n  = len(group)
        t1 = max(1, int(n * 0.70))
        t2 = max(t1 + 1, int(n * 0.85))
        for r in group[:t1]:   r['split'] = 'train'
        for r in group[t1:t2]: r['split'] = 'val'
        for r in group[t2:]:   r['split'] = 'test'
        result.extend(group)
    return result


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 58)
    print("  build_dataset_v2.py — CYA N Classifier Dataset Builder")
    print("=" * 58)

    # ── FASE 1: dati base ──────────────────────────────────────────────────────
    intent  = build_intent_records()
    bridge  = build_bridge_records()
    edges   = [dict(r) for r in EDGE_CASES]
    all_rec = intent + bridge + edges

    print(f"\n[FASE 1] Dati base:")
    print(f"  INTENT_SENTENCES : {len(intent)}")
    print(f"  BRIDGE_SENTENCES : {len(bridge)}")
    print(f"  Edge cases       : {len(edges)}")
    print(f"  TOTALE           : {len(all_rec)}")

    # ── FASE 2: conteggio per classe ────────────────────────────────────────────
    class_map = defaultdict(list)
    for r in all_rec:
        class_map[get_class_key(r)].append(r)

    print(f"\n[FASE 2] Conteggio per classe (pre-augmentation):")
    for k in sorted(class_map.keys()):
        t = TARGET_PIPE if '->' in k else TARGET_MONO
        icon = "✓" if len(class_map[k]) >= t else f"⚠  target={t}"
        print(f"  {k:25s}: {len(class_map[k]):4d}  {icon}")

    # ── FASE 3: augmentation classi sotto target ────────────────────────────────
    print(f"\n[FASE 3] Augmentation:")
    extra = []
    for k, group in class_map.items():
        # Le coppie multi-label non-pipeline (es. "general+math") non hanno target
        if '+' in k and '->' not in k:
            continue
        target = TARGET_PIPE if '->' in k else TARGET_MONO
        if len(group) < target:
            aug = augment_class(group, target)
            print(f"  {k:25s}: +{len(aug)} record augmentati")
            extra.extend(aug)

    if not extra:
        print("  Nessuna classe sotto target — augmentation non necessaria.")

    all_rec = all_rec + extra
    print(f"  Totale dopo augmentation: {len(all_rec)}")

    # ── FASE 4: stratified split ────────────────────────────────────────────────
    random.shuffle(all_rec)
    all_rec = stratified_split(all_rec)

    # ── FASE 5: salvataggio ─────────────────────────────────────────────────────
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        for r in all_rec:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    # ── Report finale ───────────────────────────────────────────────────────────
    split_c = Counter(r['split']     for r in all_rec)
    diff_c  = Counter(r['difficulty'] for r in all_rec)
    hist_n  = sum(1 for r in all_rec if r['history'])
    pipe_n  = sum(1 for r in all_rec if r['is_pipeline'])

    print(f"\n[RISULTATI]")
    print(f"  train / val / test : {split_c['train']} / {split_c['val']} / {split_c['test']}")
    print(f"  difficulty 1/2/3   : {diff_c[1]} / {diff_c[2]} / {diff_c[3]}")
    print(f"  record con history : {hist_n}")
    print(f"  record pipeline    : {pipe_n}")
    print(f"\n✅  Dataset salvato in: {OUTPUT_PATH}\n")

    # Conteggio finale per classe
    final_map = defaultdict(list)
    for r in all_rec:
        final_map[get_class_key(r)].append(r)
    print("[CONTEGGIO FINALE PER CLASSE]")
    for k in sorted(final_map.keys()):
        print(f"  {k:25s}: {len(final_map[k])}")


if __name__ == '__main__':
    main()
