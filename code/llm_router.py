"""
LLM ROUTER V1.2
Micro-LLM (qwen2.5:3b) come router semantico.
Drop-in replacement di neural_classifier.py — stessa interfaccia pubblica.

Fix V1.2:
- [F1] Output JSON esteso: domain + scores + difficulty + is_followup
- [F2] predict() restituisce Tuple[int, float, dict, int, bool]
- [F3] System prompt arricchito con esempi negativi per DOMINIO ATTIVO per ridurre falsi sticky
- [F4] num_predict 40→100, num_ctx 1024→2048 per nuovo formato JSON

Fix V1.1:
- [B1] num_ctx 1024→2048
- [B2] num_predict 12→20
- [B3] confidence=0.7 su 'general'
- [B4] last_domain iniettato come hint
- [B5] Output JSON obbligatorio + doppio fallback parsing
"""

import json
import ollama
import config
from typing import Tuple

# ---------------------------------------------------------------------------
# COSTANTI PUBBLICHE (identiche a neural_classifier.py)
# ---------------------------------------------------------------------------

DOMAIN_NAMES = ['coding', 'math', 'rights', 'general',
                'math->coding', 'rights->coding', 'rights->math']

PIPELINE_CLASSES: dict = {
    4: ('math',   'coding'),
    5: ('rights', 'coding'),
    6: ('rights', 'math'),
}

_CLASS_TO_ID        = {c: i for i, c in enumerate(DOMAIN_NAMES)}
_VALID_SORTED       = sorted(DOMAIN_NAMES, key=len, reverse=True)  # pipeline prima

# ---------------------------------------------------------------------------
# CONFIGURAZIONE
# ---------------------------------------------------------------------------

_ROUTER_MODEL      = config.SYSTEM_SETTINGS.get('router_model',      'qwen2.5:1.5b')
_ROUTER_KEEP_ALIVE = config.SYSTEM_SETTINGS.get('router_keep_alive',  '10m')

# ---------------------------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """\
Sei un classificatore di dominio. Restituisci SOLO questo JSON (nessun testo prima o dopo):
{"domain": "<etichetta>", "scores": {"coding": 0.0, "math": 0.0, "rights": 0.0, "general": 0.0}, "difficulty": 1, "is_followup": false}

CAMPI:
- domain    : etichetta più probabile (vedi lista sotto)
- scores    : probabilità per i 4 domini base (somma = 1.0)
- difficulty: 1=semplice (saluti, calcoli banali), 2=media, 3=complessa (dimostrazioni, pipeline multi-step)
- is_followup: true SOLO se la query si riferisce direttamente all'output precedente (chiarimento, modifica, continuazione)

ETICHETTE VALIDE:
coding | math | rights | general | math->coding | rights->coding | rights->math

DEFINIZIONI:
- coding     : riguarda tutta la parte relativa all'informatica, alle reti, AI. Tutto ciò che si interfaccia con il tech
- math       : modulo relativo a coprire ogni aspetto della matematica applicata
- rights     : diritto, leggi, normative, GDPR, contratti, sentenze, tutele legali
- general    : tutto il resto — cucina, viaggi, saluti, sport, filosofia, shopping, opinioni, domande esistenziali
- math->coding    : richiede ESPLICITAMENTE sia matematica sia codice
- rights->coding  : richiede ESPLICITAMENTE sia diritto sia codice
- rights->math    : richiede ESPLICITAMENTE sia diritto sia calcoli

════════════════════════════════════════════
REGOLA DOMINIO ATTIVO
════════════════════════════════════════════
Se è presente un DOMINIO ATTIVO, impostare is_followup=true e mantenere il dominio SOLO se
la query è un follow-up diretto (chiarimento su output precedente, modifica, continuazione).
Per qualsiasi argomento NUOVO o NON CORRELATO: classifica liberamente e imposta is_followup=false.

CRITERI PER is_followup=true:
- La query fa riferimento esplicito all'output precedente ("rispiega", "ottimizza", "il codice sopra")
- La query è ambigua/breve e continua naturalmente il topic attivo ("e quindi?", "esempio?", "perché?")
- La query chiede di modificare qualcosa appena prodotto

CRITERI PER is_followup=false (anche con DOMINIO ATTIVO):
- La query introduce un argomento completamente diverso dal dominio attivo
- La query è una domanda generale su un topic non correlato
- La query inizia con frasi tipo "invece", "a proposito di", "ti chiedo un'altra cosa"

════════════════════════════════════════════
ESEMPI — CON DOMINIO ATTIVO: coding
════════════════════════════════════════════
"aggiungi commenti"          → {"domain":"coding",  "scores":{"coding":0.95,"math":0.02,"rights":0.01,"general":0.02}, "difficulty":1, "is_followup":true}
"rispiega meglio"            → {"domain":"coding",  "scores":{"coding":0.90,"math":0.05,"rights":0.01,"general":0.04}, "difficulty":1, "is_followup":true}
"ottimizzalo"                → {"domain":"coding",  "scores":{"coding":0.95,"math":0.02,"rights":0.01,"general":0.02}, "difficulty":2, "is_followup":true}
"puoi farlo in C++?"         → {"domain":"coding",  "scores":{"coding":0.95,"math":0.02,"rights":0.01,"general":0.02}, "difficulty":2, "is_followup":true}
"e quindi?"                  → {"domain":"coding",  "scores":{"coding":0.80,"math":0.10,"rights":0.05,"general":0.05}, "difficulty":1, "is_followup":true}
"Dio esiste?"                → {"domain":"general", "scores":{"coding":0.02,"math":0.03,"rights":0.05,"general":0.90}, "difficulty":1, "is_followup":false}
"rispondi sì o no: Dio esiste?" → {"domain":"general","scores":{"coding":0.02,"math":0.02,"rights":0.04,"general":0.92},"difficulty":1,"is_followup":false}
"consiglio scarpe uomo"      → {"domain":"general", "scores":{"coding":0.01,"math":0.01,"rights":0.02,"general":0.96}, "difficulty":1, "is_followup":false}
"ricetta sacher?"            → {"domain":"general", "scores":{"coding":0.01,"math":0.01,"rights":0.01,"general":0.97}, "difficulty":1, "is_followup":false}
"dammi una risposta integrale sul tema a tua scelta" → {"domain":"general","scores":{"coding":0.05,"math":0.10,"rights":0.05,"general":0.80},"difficulty":2,"is_followup":false}
"ok grazie, invece qual è il concetto più importante del diritto sportivo?" → {"domain":"rights","scores":{"coding":0.02,"math":0.03,"rights":0.90,"general":0.05},"difficulty":2,"is_followup":false}

════════════════════════════════════════════
ESEMPI — CON DOMINIO ATTIVO: math
════════════════════════════════════════════
"rispiega meglio"                   → {"domain":"math",        "scores":{"coding":0.05,"math":0.85,"rights":0.02,"general":0.08}, "difficulty":1, "is_followup":true}
"il passaggio 3 non è chiaro"      → {"domain":"math",        "scores":{"coding":0.05,"math":0.88,"rights":0.02,"general":0.05}, "difficulty":1, "is_followup":true}
"dimostralo"                        → {"domain":"math",        "scores":{"coding":0.05,"math":0.88,"rights":0.02,"general":0.05}, "difficulty":3, "is_followup":true}
"scrivi il codice Python per questo algoritmo" → {"domain":"math->coding","scores":{"coding":0.45,"math":0.45,"rights":0.05,"general":0.05},"difficulty":2,"is_followup":true}

════════════════════════════════════════════
ESEMPI — CON DOMINIO ATTIVO: rights
════════════════════════════════════════════
"esempio?"                   → {"domain":"rights", "scores":{"coding":0.02,"math":0.02,"rights":0.90,"general":0.06}, "difficulty":1, "is_followup":true}
"approfondisci il punto 2"  → {"domain":"rights", "scores":{"coding":0.02,"math":0.03,"rights":0.90,"general":0.05}, "difficulty":2, "is_followup":true}

════════════════════════════════════════════
ESEMPI — SENZA DOMINIO ATTIVO
════════════════════════════════════════════
"scrivi codice Python per ordinare una lista"           → {"domain":"coding",        "scores":{"coding":0.90,"math":0.05,"rights":0.02,"general":0.03}, "difficulty":1, "is_followup":false}
"calcola l'integrale di sin(x) da 0 a pi"              → {"domain":"math",          "scores":{"coding":0.05,"math":0.88,"rights":0.02,"general":0.05}, "difficulty":2, "is_followup":false}
"quali sono i miei diritti come lavoratore?"            → {"domain":"rights",        "scores":{"coding":0.02,"math":0.03,"rights":0.88,"general":0.07}, "difficulty":2, "is_followup":false}
"come si fa la carbonara?"                              → {"domain":"general",       "scores":{"coding":0.01,"math":0.01,"rights":0.01,"general":0.97}, "difficulty":1, "is_followup":false}
"comando Linux per trovare dispositivi a blocchi"       → {"domain":"coding",        "scores":{"coding":0.90,"math":0.03,"rights":0.02,"general":0.05}, "difficulty":1, "is_followup":false}
"implementa FFT in Python e dimostra il teorema"        → {"domain":"math->coding",  "scores":{"coding":0.45,"math":0.45,"rights":0.02,"general":0.08}, "difficulty":3, "is_followup":false}
"script Python che calcola TFR rispettando D.Lgs."     → {"domain":"rights->coding","scores":{"coding":0.40,"math":0.10,"rights":0.40,"general":0.10}, "difficulty":3, "is_followup":false}
"calcola matematicamente piano ammortamento sec. legge" → {"domain":"rights->math",  "scores":{"coding":0.05,"math":0.45,"rights":0.45,"general":0.05}, "difficulty":3, "is_followup":false}
"2+2"                                                   → {"domain":"general",       "scores":{"coding":0.02,"math":0.15,"rights":0.01,"general":0.82}, "difficulty":1, "is_followup":false}
"cosa prevede il codice in merito al furto?"            → {"domain":"rights",        "scores":{"coding":0.05,"math":0.02,"rights":0.88,"general":0.05}, "difficulty":2, "is_followup":false}
"Non ho capito il concetto di OOP"                     → {"domain":"coding",        "scores":{"coding":0.88,"math":0.05,"rights":0.02,"general":0.05}, "difficulty":1, "is_followup":false}
"consiglio scarpe uomo"                                → {"domain":"general",       "scores":{"coding":0.01,"math":0.01,"rights":0.02,"general":0.96}, "difficulty":1, "is_followup":false}
"Esiste un regolamento europeo che tuteli i lavoratori?" → {"domain":"rights",      "scores":{"coding":0.02,"math":0.02,"rights":0.90,"general":0.06}, "difficulty":2, "is_followup":false}

════════════════════════════════════════════
REGOLA PIPELINE
════════════════════════════════════════════
Usa pipeline (math->coding, rights->coding, rights->math) SOLO se ENTRAMBI i domini
sono ESPLICITAMENTE richiesti nella stessa query, quindi ci sono dei riferimenti
diretti a concetti di moduli diversi. In caso di dubbio attiva il mono-dominio

OUTPUT: SOLO il JSON. Zero testo prima o dopo.
"""

# ---------------------------------------------------------------------------
# BUILD MESSAGES
# ---------------------------------------------------------------------------

def _build_messages(query: str, last_domain: str, history: list) -> list:
    recent_queries = [
        m['content'][:120]
        for m in history
        if m['role'] == 'user'
    ][-4:]

    lines = []

    if last_domain:
        lines.append(f"⚠️  DOMINIO ATTIVO: {last_domain}  ⚠️")
        lines.append("(Applica la REGOLA DOMINIO ATTIVO: mantieni SOLO se follow-up diretto)")
        lines.append("")

    if recent_queries:
        lines.append("STORICO ULTIME QUERY:")
        lines.extend(f"  [{i+1}] {q}" for i, q in enumerate(recent_queries))
        lines.append("")

    lines.append(f"QUERY DA CLASSIFICARE: {query}")

    return [
        {'role': 'system', 'content': _SYSTEM_PROMPT},
        {'role': 'user',   'content': "\n".join(lines)},
    ]

# ---------------------------------------------------------------------------
# PARSING ROBUSTO
# ---------------------------------------------------------------------------

def _parse_output(raw: str) -> dict:
    """
    Parsa l'output JSON esteso del router.
    Ritorna dict con: domain, scores, difficulty, is_followup.
    """
    result = {
        'domain':      '',
        'scores':      {},
        'difficulty':  2,
        'is_followup': False,
    }

    try:
        start = raw.find('{')
        end   = raw.rfind('}')
        if start != -1 and end != -1:
            data = json.loads(raw[start:end+1])

            candidate = str(data.get('domain', '')).lower().strip()
            if candidate in _CLASS_TO_ID:
                result['domain'] = candidate

            raw_scores = data.get('scores', {})
            if isinstance(raw_scores, dict):
                result['scores'] = {
                    k: float(v)
                    for k, v in raw_scores.items()
                    if k in ('coding', 'math', 'rights', 'general')
                }

            diff = data.get('difficulty', 2)
            if isinstance(diff, (int, float)) and 1 <= int(diff) <= 3:
                result['difficulty'] = int(diff)

            result['is_followup'] = bool(data.get('is_followup', False))

            if result['domain']:
                return result

    except (json.JSONDecodeError, AttributeError, TypeError, ValueError):
        pass

    # Fallback substring (solo domain)
    raw_lower = raw.lower()
    for cls in _VALID_SORTED:
        if cls in raw_lower:
            result['domain'] = cls
            return result

    return result

# ---------------------------------------------------------------------------
# PREDICT (interfaccia pubblica)
# ---------------------------------------------------------------------------

def predict(text: str, last_domain: str = '', history: list = None) -> Tuple[int, float, dict, int, bool]:
    """
    Classifica la query con il micro-LLM router.

    Returns:
        (class_id, confidence, domain_scores, difficulty, is_followup)
        class_id=-1 → router non disponibile, main.py attiva fallback keyword
        class_id 0-3 → mono-domain
        class_id 4-6 → pipeline (vedi PIPELINE_CLASSES)

    Note:
        confidence: general=0.7, altri=1.0 (per safety net sticky)
        domain_scores: dict {coding, math, rights, general} con probabilità
        difficulty: 1=semplice, 2=media, 3=complessa
        is_followup: True se il LLM ritiene la query un follow-up
    """
    history = history or []

    try:
        response = ollama.chat(
            model=_ROUTER_MODEL,
            messages=_build_messages(text, last_domain, history),
            stream=False,
            keep_alive=_ROUTER_KEEP_ALIVE,
            format="json",
            options={
                'temperature': 0.0,
                'num_ctx':     4096,   # era 2048: necessario per prompt lungo su 1.5b
                'num_predict': 100,
                'num_gpu':     99,
                'num_thread':  4,
                'num_batch':   512,
                'f16_kv':      True,
                'flash_attn':  True,
            }
        )

        raw    = response['message']['content'].strip()
        parsed = _parse_output(raw)
        cls    = parsed['domain']

        if cls:
            class_id    = _CLASS_TO_ID[cls]
            confidence  = 0.7 if cls == 'general' else 1.0
            scores      = parsed['scores']
            difficulty  = parsed['difficulty']
            is_followup = parsed['is_followup']

            scores_str = ', '.join(f"{k}:{v:.2f}" for k, v in scores.items()) if scores else 'n/a'
            print(f"[ROUTER] {cls.upper()} | conf={confidence} | diff={difficulty} | "
                  f"followup={is_followup} | scores=[{scores_str}]")
            return class_id, confidence, scores, difficulty, is_followup

        print(f"[ROUTER] Nessuna etichetta valida in: '{raw}' → fallback keyword")
        return -1, 0.0, {}, 2, False

    except Exception as e:
        print(f"[ROUTER] Errore ({e}) → fallback keyword")
        return -1, 0.0, {}, 2, False


def unload_router():
    """Scarica esplicitamente il router prima del caricamento dei modelli generativi."""
    try:
        ollama.generate(model=_ROUTER_MODEL, prompt="", keep_alive=0)
    except Exception:
        pass
