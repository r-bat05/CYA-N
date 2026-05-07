"""
LLM ROUTER V1.1
Micro-LLM (qwen2.5:0.5b) come router semantico.
Drop-in replacement di neural_classifier.py — stessa interfaccia pubblica.

Fix V1.1:
- [B1] num_ctx 1024→2048: evita troncamento system prompt
- [B2] num_predict 12→20: margine per output JSON
- [B3] confidence=0.7 su 'general': mantiene sticky routing safety nets
- [B4] last_domain iniettato come hint nel contesto
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

_ROUTER_MODEL      = config.SYSTEM_SETTINGS.get('router_model',      'qwen2.5:3b')
_ROUTER_KEEP_ALIVE = config.SYSTEM_SETTINGS.get('router_keep_alive',  '10m')

# ---------------------------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """\
Sei un classificatore di dominio. Restituisci SOLO JSON: {"domain": "<etichetta>"}

ETICHETTE VALIDE:
coding | math | rights | general | math->coding | rights->coding | rights->math

DEFINIZIONI:
- coding          : codice, algoritmi, debug, shell, SQL, regex, API, comandi OS, machine learning e deep learning, giochi, AI, sistemi e reti, cybersecurity
- math            : equazioni, dimostrazioni, integrali, probabilità, fisica matematica, calcolo numerico, albegra lineare, analisi matematica
- rights          : diritto, leggi, normative, GDPR, contratti, sentenze, tutele legali, tutte le tipologie di diritto (privato, sportivo, etc...)
- general         : tutto il resto — cucina, viaggi, saluti, sport, consigli, filosofia
- math->coding    : richiede ESPLICITAMENTE sia matematica sia codice
- rights->coding  : richiede ESPLICITAMENTE sia diritto sia codice
- rights->math    : richiede ESPLICITAMENTE sia diritto sia calcoli

════════════════════════════════════════════
REGOLA PRIORITARIA — DOMINIO ATTIVO
════════════════════════════════════════════
Se è presente un DOMINIO ATTIVO, restituiscilo INVARIATO a meno che la query
richieda ESPLICITAMENTE un argomento diverso (es. "cambia argomento", "invece parlami di").

Mantieni il dominio attivo per:
- Query brevi o ambigue
- Riferimenti all'output precedente, che quindi va a completamento della risposta precedente per correzioni,
spiegazioni o chiarimenti

════════════════════════════════════════════
REGOLA PIPELINE
════════════════════════════════════════════
Usa pipeline (math->coding, rights->coding, rights->math) SOLO se entrambi i domini
sono ESPLICITAMENTE richiesti nella stessa query. In caso di dubbio, usa mono-dominio.

Se nella richiesta ci potrebbero essere più di 2 domini, scegli i due più dominanti, quelli su cui
si basa la struttura della domanda e la conseguente risposta. 

════════════════════════════════════════════
ESEMPI — SENZA DOMINIO ATTIVO
════════════════════════════════════════════
"scrivi codice Python per ordinare lista"                     → {"domain": "coding"}
"calcola l'integrale di sin(x) da 0 a pi"                    → {"domain": "math"}
"quali sono i miei diritti come lavoratore?"                  → {"domain": "rights"}
"come si fa la carbonara?"                                    → {"domain": "general"}
"Dio esiste?"                                                 → {"domain": "general"}
"comando Linux per trovare dispositivi a blocchi"             → {"domain": "coding"}
"implementa la FFT in Python e dimostra il teorema"          → {"domain": "math->coding"}
"script Python che calcola TFR rispettando D.Lgs."           → {"domain": "rights->coding"}
"calcola matematicamente il piano di ammortamento sec. legge" → {"domain": "rights->math"}

════════════════════════════════════════════
ESEMPI — CON DOMINIO ATTIVO
════════════════════════════════════════════
[DOMINIO ATTIVO: coding]
"aggiungi commenti"             → {"domain": "coding"}
"rispiega meglio"               → {"domain": "coding"}
"grazie della risposta"         → {"domain": "coding"}
"e quindi?"                     → {"domain": "coding"}
"esempio?"                      → {"domain": "coding"}
"perché?"                       → {"domain": "coding"}
"ottimizzalo"                   → {"domain": "coding"}
"puoi farlo in C++?"            → {"domain": "coding"}
"ok grazie, invece qual è il concetto più importante del diritto sportivo?" → {"domain": "rights"}
"ricetta sacher?"               → {"domain": "general"}

[DOMINIO ATTIVO: math]
"rispiega meglio"               → {"domain": "math"}
"e quindi?"                     → {"domain": "math"}
"il passaggio 3 non è chiaro"  → {"domain": "math"}
"dimostralo"                    → {"domain": "math"}
"grazie"                        → {"domain": "math"}
"scrivi il codice Python per questo algoritmo" → {"domain": "math->coding"}

[DOMINIO ATTIVO: rights]
"esempio?"                      → {"domain": "rights"}
"approfondisci il punto 2"     → {"domain": "rights"}
"e quindi?"                     → {"domain": "rights"}

[DOMINIO ATTIVO: general]
"perché?"                       → {"domain": "general"}
"dimmi di più"                  → {"domain": "general"}

OUTPUT: {"domain": "..."} — nient'altro. Zero testo prima o dopo.
"""

# ---------------------------------------------------------------------------
# BUILD MESSAGES
# ---------------------------------------------------------------------------

def _build_messages(query: str, last_domain: str, history: list) -> list:
    recent_queries = [
        m['content'][:120]
        for m in history
        if m['role'] == 'user'
    ][-4:]  # aumentato da 3 a 4

    lines = []

    # Dominio attivo in evidenza PRIMA dello storico
    if last_domain:
        lines.append(f"⚠️  DOMINIO ATTIVO: {last_domain}  ⚠️")
        lines.append("(Applica la REGOLA PRIORITARIA FOLLOW-UP prima di classificare)")
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
# PARSING ROBUSTO (JSON primario + substring fallback)
# ---------------------------------------------------------------------------

def _parse_output(raw: str) -> str:
    """
    Tenta parsing JSON; se fallisce, cerca la prima etichetta valida nel testo.
    Ritorna la classe trovata o '' se nessuna.
    """
    # Tentativo 1: JSON
    try:
        # estrai il primo {...} trovato (il modello potrebbe aggiungere testo attorno)
        start = raw.find('{')
        end   = raw.rfind('}')
        if start != -1 and end != -1:
            data = json.loads(raw[start:end+1])
            candidate = str(data.get('domain', '')).lower().strip()
            if candidate in _CLASS_TO_ID:
                return candidate
    except (json.JSONDecodeError, AttributeError, TypeError):
        pass

    # Tentativo 2: substring (pipeline prima per evitare match parziale)
    raw_lower = raw.lower()
    for cls in _VALID_SORTED:
        if cls in raw_lower:
            return cls

    return ''

# ---------------------------------------------------------------------------
# PREDICT (interfaccia pubblica)
# ---------------------------------------------------------------------------

def predict(text: str, last_domain: str = '', history: list = None) -> Tuple[int, float]:
    """
    Classifica la query con il micro-LLM router.

    Returns:
        (class_id, confidence)
        -1       → router non disponibile, main.py attiva fallback keyword
        0-3      → mono-domain
        4-6      → pipeline (vedi PIPELINE_CLASSES)

    Note confidence:
        general  → 0.7  (permette ai safety net di _should_sticky_route di attivarsi)
        pipeline → 1.0
        altri    → 1.0
    """
    history = history or []

    try:
        response = ollama.chat(
            model=_ROUTER_MODEL,
            messages=_build_messages(text, last_domain, history),
            stream=False,
            keep_alive=_ROUTER_KEEP_ALIVE,
            format="json",           # [V4 FIX] Vincolo strutturale lato llama.cpp
            options={
                'temperature':  0.0,
                'num_ctx':      1024,
                'num_predict':  40,  # [V2 FIX] 20→40: margine per JSON con newline
                'num_gpu':      99,
                'num_thread':   4,
                'num_batch':    512,
                'f16_kv':       True,
                'flash_attn':   True,
            }
        )

        raw = response['message']['content'].strip()
        cls = _parse_output(raw)

        if cls:
            class_id   = _CLASS_TO_ID[cls]
            confidence = 0.7 if cls == 'general' else 1.0
            print(f"[ROUTER] raw='{raw}' → {cls.upper()} (id={class_id}, conf={confidence})")
            return class_id, confidence

        print(f"[ROUTER] Nessuna etichetta valida in: '{raw}' → fallback keyword")
        return -1, 0.0

    except Exception as e:
        print(f"[ROUTER] Errore ({e}) → fallback keyword")
        return -1, 0.0
    

def unload_router():
    """Scarica esplicitamente il router prima del caricamento dei modelli generativi."""
    try:
        ollama.generate(model=_ROUTER_MODEL, prompt="", keep_alive=0)
    except Exception:
        pass