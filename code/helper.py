import re
import threading
import time
import sys
import itertools
import config as _config

# ---------------------------------------------------------------------------
# Dizionario di sostituzione simboli LaTeX con simboli Unicode (ESPANSO)
# ---------------------------------------------------------------------------
latex_to_unicode = {
    # --- Casi Speciali ---
    r"\frac{d}{dx}": "d/dx", r"\,dx": " dx",

    # --- Lettere Greche (Minuscole) ---
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ", r"\epsilon": "ε",
    r"\varepsilon": "ε", r"\zeta": "ζ", r"\eta": "η", r"\theta": "θ", r"\vartheta": "ϑ",
    r"\iota": "ι", r"\kappa": "κ", r"\lambda": "λ", r"\mu": "μ", r"\nu": "ν",
    r"\xi": "ξ", r"\pi": "π", r"\rho": "ρ", r"\varrho": "ϱ", r"\sigma": "σ",
    r"\varsigma": "ς", r"\tau": "τ", r"\upsilon": "υ", r"\phi": "φ", r"\varphi": "φ",
    r"\chi": "χ", r"\psi": "ψ", r"\omega": "ω",

    # --- Lettere Greche (Maiuscole) ---
    r"\Gamma": "Γ", r"\Delta": "Δ", r"\Theta": "Θ", r"\Lambda": "Λ",
    r"\Xi": "Ξ", r"\Pi": "Π", r"\Sigma": "Σ", r"\Upsilon": "Υ",
    r"\Phi": "Φ", r"\Psi": "Ψ", r"\Omega": "Ω",

    # --- Operatori Matematici ---
    r"\times": "×", r"\cdot": "·", r"\div": "÷", r"\pm": "±", r"\mp": "∓",
    r"\ast": "*", r"\star": "⋆", r"\circ": "∘", r"\bullet": "•",
    r"\sqrt": "√", r"\sum": "Σ", r"\prod": "∏", r"\coprod": "∐",
    r"\int": "∫", r"\oint": "∮", r"\iint": "∬", r"\iiint": "∭",
    r"\partial": "∂", r"\nabla": "∇", r"\infty": "∞", r"\lim": "lim",
    r"\to": "→", r"\mapsto": "↦", r"\implies": "⇒", r"\iff": "⇔",

    # --- Relazioni e Confronto ---
    r"\leq": "≤", r"\geq": "≥", r"\neq": "≠", r"\approx": "≈",
    r"\equiv": "≡", r"\sim": "∼", r"\simeq": "≃", r"\cong": "≅",
    r"\propto": "∝", r"\ll": "≪", r"\gg": "≫", r"\perp": "⊥", r"\parallel": "∥",

    # --- Insiemi e Logica ---
    r"\in": "∈", r"\notin": "∉", r"\ni": "∋", r"\subset": "⊂",
    r"\subseteq": "⊆", r"\supset": "⊃", r"\supseteq": "⊇",
    r"\cup": "∪", r"\cap": "∩", r"\setminus": "\\", r"\emptyset": "∅",
    r"\forall": "∀", r"\exists": "∃", r"\nexists": "∄",
    r"\neg": "¬", r"\land": "∧", r"\lor": "∨",

    # --- Insiemi Numerici ---
    r"\mathbb{N}": "ℕ", r"\mathbb{Z}": "ℤ", r"\mathbb{Q}": "ℚ",
    r"\mathbb{R}": "ℝ", r"\mathbb{C}": "ℂ", r"\mathbb{H}": "ℍ",

    # --- Funzioni e Accenti ---
    r"\sin": "sin", r"\cos": "cos", r"\tan": "tan", r"\cot": "cot",
    r"\arcsin": "arcsin", r"\arccos": "arccos", r"\arctan": "arctan",
    r"\sinh": "sinh", r"\cosh": "cosh", r"\tanh": "tanh",
    r"\log": "log", r"\ln": "ln", r"\det": "det", r"\dim": "dim",
    r"\hat": "^", r"\vec": "→", r"\bar": "¯",

    # --- Pulizia Simboli LaTeX rimasti ---
    r"\[": "", r"\]": "", r"\(": "", r"\)": "", r"**": ""
}

# Pre-compilazione: chiavi ordinate per lunghezza decrescente (evita sostituzioni parziali)
_SORTED_LATEX_KEYS = sorted(latex_to_unicode.keys(), key=len, reverse=True)

# [O2 FIX] Pattern unico pre-compilato al posto di ~100 .replace() sequenziali
# per segmento (era O(segmenti × chiavi), ora O(1 passata regex) per segmento).
# L'ordine (chiavi più lunghe prima) è preservato dall'alternanza, che in
# Python prova le alternative nell'ordine in cui compaiono nel pattern.
# Equivalente comportamentale garantito: nessun VALORE del dizionario
# (es. "α", "×", "→") combacia con nessuna CHIAVE (sempre prefissata da
# backslash o parentesi letterali), quindi non esiste rischio di
# ri-sostituzione a catena che il vecchio approccio sequenziale avrebbe
# potuto (per costruzione) introdurre.
_LATEX_PATTERN = re.compile(
    '|'.join(re.escape(k) for k in _SORTED_LATEX_KEYS)
) if _SORTED_LATEX_KEYS else None


def _latex_replace_match(match: re.Match) -> str:
    return latex_to_unicode[match.group(0)]

# Regex per isolare i blocchi di codice Markdown (triple e singolo backtick).
_CODE_BLOCK_RE = re.compile(r'(```[\s\S]*?```|`[^`\n]*`)')

# Regex CJK pre-compilata (usata solo se cjk_filter_enabled=True in config)
_CJK_RE = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]')


class SpinnerContext:
    """
    Gestisce lo spinner di caricamento.
    Supporta sia l'uso come Context Manager (with...) sia start/stop manuale.
    """
    def __init__(self, message="Generazione risposta"):
        self.message    = message
        self.stop_event = threading.Event()
        self.thread     = threading.Thread(target=self._spin, args=(self.stop_event,), daemon=True)
        self._running   = False

    def _spin(self, stop_event):
        spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        while not self.stop_event.is_set():
            sys.stdout.write(f"\r{next(spinner)} {self.message}")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(self.message) + 5) + "\r")
        sys.stdout.flush()

    def start(self):
        if not self._running:
            self._running = True
            self.thread.start()

    def stop(self):
        if self._running:
            self.stop_event.set()
            self.thread.join()
            self._running = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# ---------------------------------------------------------------------------
# Funzioni comuni per la pulizia del testo e la visualizzazione
# ---------------------------------------------------------------------------

def clean_response(text: str) -> str:
    """
    Pulisce la risposta da tag di ragionamento, simboli LaTeX e (opzionalmente)
    caratteri orientali.

    [BUG6 FIX] I tag di ragionamento sono letti dinamicamente da config.

    [BUG5 FIX] La sostituzione LaTeX è "code-block aware": agisce esclusivamente
    sul testo discorsivo, escludendo i blocchi delimitati da backtick.

    [CJK FIX] Il filtro CJK è ora controllato dal flag config.SYSTEM_SETTINGS
    'cjk_filter_enabled' (default True). Impostare a False per abilitare la
    gestione di stringhe asiatiche nel codice generato (es. array con caratteri
    giapponesi). Il filtro viene applicato DOPO lo split code-block per coerenza
    con la protezione BUG5, applicandosi solo al testo discorsivo.
    """
    # 1. [BUG6] Rimozione tag di ragionamento con pattern dinamico da config
    open_tag  = re.escape(_config.SYSTEM_SETTINGS.get('think_open_tag',  '<think>'))
    close_tag = re.escape(_config.SYSTEM_SETTINGS.get('think_close_tag', '</think>'))
    text = re.sub(f'{open_tag}.*?{close_tag}', '', text, flags=re.DOTALL)

    # [M7 FIX] Guardia per code fence ``` non chiuso: una risposta troncata
    # a metà blocco di codice (limite token) lascia un numero DISPARI di
    # occorrenze di ```. Senza questa guardia, lo split code-block-aware
    # sottostante tratterebbe l'intero residuo (fence di apertura + codice
    # non ancora chiuso) come testo discorsivo, esponendolo a sostituzione
    # LaTeX/filtro CJK e mutilando codice legittimo. Isoliamo tutto ciò che
    # segue l'ultima occorrenza di ``` come blocco protetto, non filtrato,
    # e lo riattacchiamo invariato a fine funzione.
    unclosed_fence_tail = ""
    if text.count('```') % 2 == 1:
        last_fence_idx = text.rfind('```')
        unclosed_fence_tail = text[last_fence_idx:]
        text = text[:last_fence_idx]

    # 2. Split code-block aware: separa testo discorsivo da blocchi di codice.
    #    Indici PARI  → testo discorsivo  (applicare filtri)
    #    Indici DISPARI → blocchi codice  (preservare intatti)
    parts = _CODE_BLOCK_RE.split(text)

    cjk_enabled = _config.SYSTEM_SETTINGS.get('cjk_filter_enabled', True)
    removed_cjk_chars = []  # [A3 FIX] traccia rimozioni non vuote per il log

    for i in range(0, len(parts), 2):  # solo indici pari = testo discorsivo
        segment = parts[i]

        # [CJK FIX] Applicato solo sul testo discorsivo e solo se abilitato.
        # Spostato dentro il loop per evitare di agire sui code block.
        if cjk_enabled:
            matches = _CJK_RE.findall(segment)
            if matches:
                removed_cjk_chars.extend(matches)
            segment = _CJK_RE.sub('', segment)

        # [BUG5 / O2 FIX] Sostituzione LaTeX solo sulle parti non-codice, ora
        # con un'unica regex pre-compilata invece di ~100 .replace()
        # sequenziali (vedi _LATEX_PATTERN sopra).
        if _LATEX_PATTERN is not None:
            segment = _LATEX_PATTERN.sub(_latex_replace_match, segment)

        parts[i] = segment

    result = ''.join(parts)
    if unclosed_fence_tail:
        result += unclosed_fence_tail

    # [A3 FIX] Il filtro CJK è globale e attivo di default per TUTTI i
    # domini (incluso 'general', che tratta anche cultura/lingue: galateo
    # giapponese, ecc.). Se un carattere CJK legittimo viene rimosso,
    # l'utente riceveva prima una risposta silenziosamente incompleta senza
    # alcuna indicazione. Non disabilitiamo il filtro per dominio (avrebbe
    # richiesto propagare 'category' in ogni call-site di clean_response()
    # dentro ai_engine.py::generate(), toccando anche quel file) ma
    # rendiamo la rimozione osservabile per il debug, come da opzione B
    # proposta in report_bugs.md (A3).
    if removed_cjk_chars:
        preview = ''.join(removed_cjk_chars[:20])
        print(f"⚠️  [CJK_FILTER] Rimossi {len(removed_cjk_chars)} caratteri CJK "
              f"dalla risposta (preview: '{preview}'). Se il contenuto era "
              f"intenzionale, disabilita 'cjk_filter_enabled' in config.py.")

    return result


def print_time_elapsed(start_time: float):
    """
    Calcola e stampa il tempo trascorso formattato.
    """
    elapsed = time.time() - start_time
    if elapsed >= 60:
        print(f"\n(Tempo impiegato: {elapsed:.3f}s, {elapsed / 60:.3f} min)\n")
    else:
        print(f"\n(Tempo impiegato: {elapsed:.3f}s)\n")
