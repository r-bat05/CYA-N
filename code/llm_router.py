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

_ROUTER_MODEL      = config.SYSTEM_SETTINGS.get('router_model',      'qwen2.5:0.5b')
_ROUTER_KEEP_ALIVE = config.SYSTEM_SETTINGS.get('router_keep_alive',  '10m')

# ---------------------------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
Sei un classificatore di dominio. Devi restituire SOLO un oggetto JSON, niente altro.

FORMATO OUTPUT OBBLIGATORIO:
{"domain": "<etichetta>"}

ETICHETTE VALIDE (esattamente queste, minuscolo, con trattino se pipeline):
- coding
- math
- rights
- general
- math->coding
- rights->coding
- rights->math

DEFINIZIONI:
- coding          : programmazione, codice, algoritmi, script, debug, comandi shell/OS, regex, SQL, API
- math            : matematica, calcoli, dimostrazioni, equazioni, analisi, probabilità, fisica matematica
- rights          : diritto, leggi, normative, decreti legislativi, contratti, sentenze, GDPR, tutele legali
- general         : tutto il resto — cucina, viaggi, storia, sport, saluti, consigli pratici, psicologia
- math->coding    : richiede SIA matematica SIA codice insieme (es. "implementa FFT con dimostrazione")
- rights->coding  : richiede SIA diritto SIA codice insieme (es. "script Python conforme GDPR")
- rights->math    : richiede SIA diritto SIA calcoli insieme (es. "calcola TFR secondo normativa")

REGOLE NON DEROGABILI:
1. Il tuo output è ESCLUSIVAMENTE {"domain": "..."} — zero parole prima o dopo.
2. Usa SOLO le etichette elencate sopra. Nessuna variante, nessuna traduzione.
3. Ignora convenevoli ("ciao", "grazie", "per favore") — classifica l'INTENTO reale.
4. Query breve senza dominio esplicito → guarda il DOMINIO ATTIVO e le ultime query: è follow-up.
5. Contenuto tecnico misto senza codice richiesto → mono-domain (math o rights), non pipeline.
6. Pipeline SOLO se entrambi i domini sono esplicitamente necessari nella risposta.

ESEMPI VINCOLANTI:
Input: "scrivi codice Python per ordinare lista"               → {"domain": "coding"}
Input: "calcola l'integrale di sin(x) da 0 a pi"              → {"domain": "math"}
Input: "quali sono i miei diritti come lavoratore?"            → {"domain": "rights"}
Input: "come si fa la carbonara?"                              → {"domain": "general"}
Input: "ciao come stai?"                                       → {"domain": "general"}
Input: "aggiungi commenti" [ultima query era coding]           → {"domain": "coding"}
Input: "rispiega meglio" [ultima query era math]               → {"domain": "math"}
Input: "grazie della risposta" [ultima query era math]         → {"domain": "math"}
Input: "e quindi?" [ultima query era rights]                   → {"domain": "rights"}
Input: "implementa la FFT in Python e dimostra il teorema"     → {"domain": "math->coding"}
Input: "script Python che calcola TFR rispettando D.Lgs."      → {"domain": "rights->coding"}
Input: "calcola matematicamente il piano di ammortamento sec. legge" → {"domain": "rights->math"}
Input: "comando Linux per trovare dispositivi a blocchi"       → {"domain": "coding"}
Input: "Dio esiste?" [dopo qualsiasi turno]                    → {"domain": "general"}
Input: "perché?" [ultima query era general]                    → {"domain": "general"}
Input: "esempio?" [ultima query era rights]                    → {"domain": "rights"}

OUTPUT NON VALIDI (non fare MAI così):
❌ "La classificazione è coding"
❌ "coding"
❌ {"domain": "Coding"}
❌ {"domain": "programming"}
❌ {"domain": "math->coding", "reason": "..."}
✅ {"domain": "coding"}
"""

# ---------------------------------------------------------------------------
# BUILD MESSAGES
# ---------------------------------------------------------------------------

def _build_messages(query: str, last_domain: str, history: list) -> list:
    recent_queries = [
        m['content'][:100]          # 150→100
        for m in history
        if m['role'] == 'user'
    ][-3:]                         

    lines = []
    if recent_queries:
        lines.append("STORICO ULTIME QUERY (per rilevare follow-up):")
        lines.extend(f"[{i+1}] {q}" for i, q in enumerate(recent_queries))
    if last_domain:
        lines.append(f"DOMINIO ATTIVO: {last_domain}")
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
            options={
                'temperature': 0.0,
                'num_ctx':     2048,
                'num_predict': 35,  
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