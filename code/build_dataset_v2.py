"""
build_dataset_v2.py — CYA N | Generatore Unificato Dataset Neurale
==================================================================
Questo script sostituisce i vecchi build_dataset_v2.py ed expand_dataset_v2.py.
Genera il dataset completo in un'unica passata, assegnando correttamente
le etichette 'is_followup' e garantendo uno split 70/15/15 stratificato.

Sorgenti:
  1. code/old_files/db_query.py  → INTENT_SENTENCES + BRIDGE_SENTENCES
  2. EDGE_CASES manuali          → follow-up, switch dominio, false/true pipeline
  3. Augmentation lessicale      → sinonimi per bilanciare le classi
  4. Augmentation di rumore      → framing narrativo / stile-risposta (Opzione A)

Output: code/dataset_v2.jsonl

Novità (Query Noise Augmentation — Opzione A, report_query_noise_augmentation.md):
- [NOISE-AUG] Nuova augment_noise(): contrasta il bias di diluizione per
  mean-pooling di MiniLM (media aritmetica di tutti i token embeddings,
  pesata solo dall'attention mask, mai dalla rilevanza semantica). Frasi
  tecniche terse "annegate" in testo di contorno narrativo/motivazionale/di
  specifica-stile venivano spinte verso GENERAL con alta confidence, perché
  la rete aveva imparato la scorciatoia "registro lungo/discorsivo →
  GENERAL" (GENERAL nel dataset contiene nativamente molte frasi lunghe).
  Caso riprodotto: "risolvi le equazioni di Navier-Stokes" → MATH (1.000)
  vs stessa frase con contorno storico-filosofico → GENERAL (1.000).
  Stesso pattern architetturale di augment_class()/augment_query() (wrapping
  di frase intera anziché sostituzione di singola parola), chiamata in
  FASE 2bis, SEMPRE dopo stratified_split() (ogni variante eredita lo split
  del sorgente — mai splittata indipendentemente, altrimenti si reintroduce
  esattamente il leakage train/test già risolto per l'augmentation a
  sinonimi, vedi [FIX LEAKAGE] più sotto). Applicata SOLO a
  INTENT_SENTENCES/BRIDGE_SENTENCES (intent+bridge): MANUAL_RECORDS
  (follow-up/domain-switch/edge-case) ha semantica legata alla brevità e
  alla history che il wrapping romperebbe, e resta intenzionalmente escluso.
  Copertura simmetrica sui 4 domini + 3 pipeline + classi bridge
  non-pipeline (pool di template topic-agnostic, mai un "sapore" di rumore
  legato a un dominio specifico), diversità di posizione
  (prefisso/suffisso/wrap) e di sapore (storico-culturale, filosofico,
  curiosità personale, utilità/motivazionale, specifica di stile risposta),
  incluse varianti ad alto rapporto rumore/segnale (~80%+) che replicano il
  caso reale osservato. Validata in sandbox (ast.parse + dry-run funzionale
  su dataset stub): output JSONL valido riga per riga, split ereditato
  correttamente dal sorgente, conteggio varianti coerente con
  NOISE_INJECTION_RATIO per class-key.

Novità (Difficulty Manuale — report_difficulty_manual.md):
- [DIFFICULTY] Rimossa l'euristica estimate_difficulty() (marker lessicali
  _HARD_MARKERS + floor fisso per dominio: livello 3/2 per query tecniche,
  mai validata su larga scala e strutturalmente cieca su casi come
  "trasformata di Fourier", corta ma concettualmente difficile). Rimossa
  anche get_dominant_domain(), usata esclusivamente da estimate_difficulty()
  per calcolare il dominio dominante di un bridge — nessun altro call site.
- [DIFFICULTY] Sostituita da get_difficulty_label(query): lookup fail-fast
  su difficulty_labels.json, file esterno con etichetta manuale (1/2/3) per
  ciascuna delle 1010 query esatte di INTENT_SENTENCES/BRIDGE_SENTENCES
  (724 + 286, verificato — vedi report §5). Lo script NON gira finché il
  file non è completo al 100%: get_difficulty_label() solleva ValueError
  con la query esatta mancante, stesso pattern fail-fast già in uso per
  is_followup in precompute_embeddings.py::load_dataset(). Comportamento
  intenzionale: impedisce la generazione silenziosa di un dataset con
  etichette parziali.
- [DIFFICULTY] MANUAL_RECORDS invariato e FUORI SCOPE: _r()/_fu()/_cd()
  prendono già 'diff' come parametro esplicito passato a mano, mai
  derivato da estimate_difficulty(). Nessuna modifica necessaria.

Novità (Fix da report_bugs.md):
- [A2] Nuova dedup_records(): rimuove query duplicate verbatim PRIMA dello
  split stratificato, prevenendo leakage train/val/test da record clonati.
- [M1] Warning esplicito se augment_class() non raggiunge il target
  richiesto per una classe (copertura SYNONYMS insufficiente).
- [M2] Le classi bridge non-pipeline (general+math, general+rights) non
  sono più escluse dall'augmentation: nuovo target dedicato TARGET_BRIDGE_NEG.
- [M3] stratified_split() logga un warning per ogni classe con split
  val e/o test vuoto.
"""

import json, random, hashlib
from collections import defaultdict, Counter
from db_query import INTENT_SENTENCES, BRIDGE_SENTENCES
from domains import BRIDGE_MAP
from classifier_config import DATASET_PATH, DIFFICULTY_LABELS_PATH

random.seed(42)

# ── Costanti ───────────────────────────────────────────────────────────────────
TARGET_MONO = 250   # min esempi per ogni dominio mono
TARGET_PIPE = 80    # min esempi per ogni tipo pipeline
# [M2 FIX] Target esplicito per le classi bridge NON-pipeline (general+math,
# general+rights, cioè '+' in k ma '->' non in k): prima erano ESCLUSE
# dall'augmentation (`if '+' in k and '->' not in k: continue`), restando a
# 7/9 esempi grezzi contro i 250 dei mono-domain e gli 80 delle pipeline —
# uno sbilanciamento marcato proprio sugli esempi che insegnano alla NN a
# NON promuovere 'general' a pipeline (segnale statisticamente debole).
# Valore intermedio (non TARGET_PIPE: sono esempi negativi, non pattern
# positivi da massimizzare quanto le pipeline vere).
TARGET_BRIDGE_NEG = 40

# [HARD-NEG FIX — wrong_query_TESTING.md rev.2] Target dedicati per
# sottoinsiemi di record "difficili" (hard negatives) che altrimenti NON
# riceverebbero MAI augmentation dal loop generico per class-key in main():
# quel loop confronta `len(group) < target` sul BUCKET INTERO della classe
# mono-dominio (es. 'coding'), che satura TARGET_MONO=250 ben prima che
# questi pochi record mirati vengano anche solo notati — restano 1:1
# indipendentemente da quanti se ne aggiungono a mano (bug diagnosticato
# su A-C1: 10 record "calcola X in Python" rimasti verbatim, fix
# precedente inefficace anche dopo retrain). Ogni sottoinsieme riceve
# quindi un rinforzo ESPLICITO in FASE 2ter, fuori dal loop generico.
TARGET_FALSE_PIPELINE_NEG     = 70  # "calcola/implementa X in Python" mono-coding
FALSE_PIPELINE_NOISE_VARIANTS = 2   # varianti wrapping narrativo per record base
KEYWORD_TRAP_NOISE_VARIANTS   = 3   # varianti wrapping narrativo per record base

OUTPUT_PATH = DATASET_PATH   # [CFG-2 FIX] condiviso con precompute_embeddings.py

# [DUP-3 FIX] BRIDGE_MAP importato da domains.py: unica fonte di verità
# derivata da PIPELINE_CLASSES, non più mantenuto a mano qui.

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
    "cos'è":      ['cosa si intende per', 'che cosa rappresenta', 'in cosa consiste'],  # [FIX]
}

# ── Shortcut label sets ────────────────────────────────────────────────────────
_C  = {"coding":1,"math":0,"rights":0,"general":0}
_M  = {"coding":0,"math":1,"rights":0,"general":0}
_R  = {"coding":0,"math":0,"rights":1,"general":0}
_G  = {"coding":0,"math":0,"rights":0,"general":1}
_CM = {"coding":1,"math":1,"rights":0,"general":0}
_RC = {"coding":1,"math":0,"rights":1,"general":0}
_RM = {"coding":0,"math":1,"rights":1,"general":0}

def _r(query, labels, diff, is_pipe=False, pipe_type=None, hist=None, is_followup=False):
    """Costruttore record unificato per tutto il dataset."""
    return {
        "query": query, 
        "history": hist or [],
        "domain_labels": dict(labels), 
        "is_pipeline": is_pipe,
        "pipeline_type": pipe_type, 
        "difficulty": diff, 
        "is_followup": is_followup,
        "split": None
    }

# Shortcut specifici per semplificare l'inserimento manuale
def _fu(query, labels, diff, hist):
    """Crea un record di Follow-up vero (history presente + is_followup=True)."""
    return _r(query, labels, diff, hist=hist, is_followup=True)

def _cd(query, labels, diff, hist):
    """Crea un record di Cambio Dominio (history presente ma is_followup=False)."""
    return _r(query, labels, diff, hist=hist, is_followup=False)


# ── Edge cases manuali e Follow-ups ────────────────────────────────────────────
MANUAL_RECORDS = [

    # ── Follow-up dopo CODING ──
    _fu("perché?",                 _C, 1, ["Come funziona la ricorsione in Python?"]),
    _fu("e quindi?",               _C, 1, ["Spiega la differenza tra TCP e UDP."]),
    _fu("non ho capito",           _C, 1, ["Come si implementa una coda con priorità in Python?"]),
    _fu("puoi fare un esempio?",   _C, 1, ["Spiega cos'è il polimorfismo in OOP."]),
    _fu("spiega meglio",           _C, 1, ["Come funziona l'algoritmo di Dijkstra?"]),
    _fu("e il caso peggiore?",     _C, 2, ["Implementa quicksort e analizza la complessità."]),
    _fu("riesci a farlo in Java?", _C, 1, ["Scrivi codice Python per ordinare una lista."]),
    _fu("c'è un modo più efficiente?", _C, 2, ["Come cerco un elemento in una lista Python?"]),
    _fu("fammi vedere il codice",  _C, 1, ["Come funziona il pattern Observer?"]),
    _fu("e il testing?",           _C, 2, ["Come si struttura un'architettura microservizi?"]),
    _fu("e in JavaScript come si fa?",          _C, 1, ["Come si crea una classe in Python?"]),
    _fu("e con la programmazione funzionale?",  _C, 2, ["Spiega l'uso dei decoratori in Python."]),
    _fu("mostrami un esempio concreto",         _C, 1, ["Cos'è la comprensione di lista in Python?"]),
    _fu("e se la lista fosse vuota?",           _C, 1, ["Come si ordina una lista in Python?"]),
    _fu("aggiungi la gestione degli errori",    _C, 2, ["Scrivi un parser JSON in Python."]),
    _fu("e lo stesso con i dizionari?",         _C, 1, ["Come si usa zip() in Python?"]),
    _fu("perché non funziona con i float?",     _C, 1, ["Come si confrontano due valori in Python?"]),
    _fu("e su Python 2?",                       _C, 1, ["Cosa cambia in Python 3 rispetto a print?"]),
    _fu("come lo rendo più veloce?",            _C, 2, ["Implementa la ricerca binaria in Python."]),
    _fu("e con asyncio?",                       _C, 2, ["Come funziona il multithreading in Python?"]),
    _fu("e il tipo di ritorno?",                _C, 1, ["Come si usano le type hints in Python?"]),
    _fu("e se avessi milioni di righe?",        _C, 2, ["Come leggo un file CSV riga per riga in Python?"]),
    _fu("mostrami il codice completo",          _C, 1, ["Come si connette Python a un database SQLite?"]),
    _fu("e con PostgreSQL?",                    _C, 2, ["Come eseguo una query SQL da Python?"]),
    _fu("e il pattern Decorator?",              _C, 2, ["Spiega il pattern Strategy in OOP."]),
    _fu("e in un linguaggio senza classi?",     _C, 2, ["Come si implementa l'ereditarietà in Java?"]),
    _fu("puoi riscriverlo senza ereditarietà?", _C, 2, ["Spiega la differenza tra extends e implements in Java."]),
    _fu("e la versione thread-safe?",           _C, 2, ["Implementa il pattern Singleton in Java."]),
    _fu("e i test unitari come si scrivono?",   _C, 2, ["Spiega il pattern Factory in Python."]),
    _fu("dammi un esempio reale",               _C, 1, ["Cos'è il principio di inversione delle dipendenze?"]),
    _fu("e il liskov substitution principle?",  _C, 2, ["Spiega il principio Open/Closed."]),
    _fu("come si usa con React?",               _C, 2, ["Spiega il pattern MVC."]),
    _fu("e la complessità spaziale?",           _C, 2, ["Analizza la complessità di MergeSort."]),
    _fu("e con un grafo pesato?",               _C, 2, ["Come funziona BFS su un grafo?"]),
    _fu("e se il grafo ha cicli?",              _C, 2, ["Implementa DFS su un albero binario."]),
    _fu("e la versione iterativa?",             _C, 2, ["Scrivi la versione ricorsiva di QuickSort."]),
    _fu("e l'albero AVL?",                      _C, 3, ["Spiega gli alberi rosso-neri."]),
    _fu("mostrami l'inserimento",               _C, 2, ["Come funziona un heap binario?"]),
    _fu("e su una lista linkata?",              _C, 2, ["Come si inverte un array in O(1) spazio?"]),
    _fu("spiega meglio la parte del pivot",     _C, 2, ["Implementa QuickSort e analizza la complessità."]),
    _fu("e con GraphQL?",                       _C, 2, ["Come si progetta un'API REST?"]),
    _fu("e l'autenticazione JWT?",              _C, 2, ["Come funziona OAuth 2.0?"]),
    _fu("e se l'API è lenta?",                  _C, 2, ["Come si implementa il caching in un'API?"]),
    _fu("e il rate limiting?",                  _C, 2, ["Come si gestisce la sicurezza in un'API REST?"]),
    _fu("e con WebSocket?",                     _C, 2, ["Spiega la differenza tra HTTP e HTTPS."]),
    _fu("e il load balancing?",                 _C, 2, ["Come funziona un reverse proxy?"]),
    _fu("e Docker Compose?",                    _C, 2, ["Spiega come si crea un Dockerfile."]),
    _fu("e Kubernetes?",                        _C, 3, ["Come funziona il networking in Docker?"]),
    _fu("e se il container crasha?",            _C, 2, ["Come si gestisce il restart di un container?"]),
    _fu("e i log come si gestiscono?",          _C, 2, ["Come si monitora un'applicazione in produzione?"]),
    _fu("come lo debuggo?",                     _C, 1, ["Cos'è un NullPointerException in Java?"]),
    _fu("e in produzione come lo trovo?",       _C, 2, ["Come si usa un debugger in Python?"]),
    _fu("e se l'errore è in un thread?",        _C, 2, ["Come si gestiscono le eccezioni in Java?"]),
    _fu("e con i test di integrazione?",        _C, 2, ["Come si scrivono unit test in Python con pytest?"]),
    _fu("e il mocking?",                        _C, 2, ["Come si usa unittest.mock in Python?"]),
    _fu("e la coverage?",                       _C, 1, ["Come si misura la qualità del codice?"]),
    _fu("e il rebase?",                         _C, 1, ["Spiega la differenza tra git merge e git rebase."]),
    _fu("e i conflitti?",                       _C, 1, ["Come si fa un git cherry-pick?"]),
    _fu("e con GitHub Actions?",                _C, 2, ["Come si configura una CI/CD pipeline?"]),
    _fu("e il rollback?",                       _C, 2, ["Come si fa il deploy di un'applicazione Flask?"]),

    # ── Follow-up dopo MATH ──
    _fu("perché?",                       _M, 1, ["Dimostra il teorema fondamentale del calcolo."]),
    _fu("e quindi?",                     _M, 1, ["Calcola la derivata di f(x) = x^3 + 2x - 1."]),
    _fu("non ho capito la dimostrazione",_M, 1, ["Dimostra il teorema di Cauchy."]),
    _fu("puoi fare un esempio numerico?",_M, 1, ["Spiega come si calcola la covarianza."]),
    _fu("rispiega il passaggio 2",       _M, 1, ["Dimostra per induzione la somma dei primi n numeri."]),
    _fu("e nel caso 3D?",                _M, 2, ["Calcola il gradiente di f(x,y) = x^2 + 3xy."]),
    _fu("perché si usa il logaritmo?",   _M, 2, ["Spiega la discesa del gradiente."]),
    _fu("come mai converge?",            _M, 2, ["Spiega il metodo delle potenze per gli autovalori."]),
    _fu("spiega il passaggio algebrico",        _M, 1, ["Calcola la derivata di f(x) = e^x * sin(x)."]),
    _fu("e la derivata seconda?",               _M, 1, ["Calcola la derivata di x^3 - 3x + 2."]),
    _fu("e nel punto x=0?",                     _M, 1, ["Trova i punti critici di f(x) = x^4 - 4x^2."]),
    _fu("e l'integrale indefinito?",            _M, 2, ["Calcola l'integrale di 1/(1+x^2)."]),
    _fu("e con il metodo per parti?",           _M, 2, ["Spiega come si risolve un integrale per sostituzione."]),
    _fu("e se il limite non esiste?",           _M, 2, ["Calcola il limite di (e^x - 1)/x per x→0."]),
    _fu("e la forma indeterminata 0/0?",        _M, 2, ["Quando si usa la regola di De l'Hôpital?"]),
    _fu("mostrami un controesempio",            _M, 2, ["Dimostra il teorema di Lagrange."]),
    _fu("e le ipotesi sono sempre necessarie?", _M, 2, ["Enuncia il teorema di Rolle."]),
    _fu("e la serie di Taylor?",                _M, 2, ["Spiega cos'è uno sviluppo in serie di MacLaurin."]),
    _fu("e la convergenza?",                    _M, 2, ["Cos'è il raggio di convergenza di una serie?"]),
    _fu("e in più variabili?",                  _M, 3, ["Calcola il gradiente di f(x,y) = x^2*y + y^3."]),
    _fu("e il laplaciano?",                     _M, 3, ["Spiega cos'è la derivata direzionale."]),
    _fu("e la sua inversa?",                    _M, 2, ["Come si calcola il determinante di una matrice 3x3?"]),
    _fu("e il rango?",                          _M, 2, ["Quando un sistema lineare ha infinite soluzioni?"]),
    _fu("e gli autovettori?",                   _M, 2, ["Come si calcolano gli autovalori di una matrice?"]),
    _fu("e la diagonalizzazione?",              _M, 3, ["Spiega la decomposizione spettrale."]),
    _fu("e la SVD?",                            _M, 3, ["Cos'è la decomposizione LU?"]),
    _fu("e in spazi di dimensione infinita?",   _M, 3, ["Cos'è uno spazio di Hilbert?"]),
    _fu("e la norma euclidea?",                 _M, 1, ["Come si calcola la distanza tra due vettori?"]),
    _fu("e la proiezione ortogonale?",          _M, 2, ["Spiega il metodo di Gram-Schmidt."]),
    _fu("e la varianza?",                       _M, 1, ["Come si calcola la media di una distribuzione?"]),
    _fu("e la distribuzione normale?",          _M, 2, ["Spiega la distribuzione di Poisson."]),
    _fu("e il test chi-quadro?",                _M, 2, ["Cos'è il p-value in un test statistico?"]),
    _fu("e l'intervallo di confidenza?",        _M, 2, ["Come si calcola l'errore standard?"]),
    _fu("e la correlazione di Spearman?",       _M, 2, ["Cos'è la correlazione di Pearson?"]),
    _fu("e la regressione non lineare?",        _M, 3, ["Spiega la regressione lineare multipla."]),
    _fu("e il bias-variance tradeoff?",         _M, 3, ["Cos'è l'overfitting in un modello statistico?"]),
    _fu("e con variabili categoriali?",         _M, 2, ["Come si gestiscono i valori mancanti in un dataset?"]),
    _fu("e la convergenza è garantita?",        _M, 2, ["Spiega il metodo di bisezione."]),
    _fu("e il metodo di Newton?",               _M, 2, ["Come funziona il metodo delle secanti?"]),
    _fu("e l'errore di troncamento?",           _M, 2, ["Spiega il metodo di Eulero per le ODE."]),
    _fu("e Runge-Kutta 4?",                     _M, 3, ["Come funziona il metodo di Eulero implicito?"]),

    # ── Follow-up dopo RIGHTS ──
    _fu("e nel mio caso?",       _R, 1, ["Cosa prevede il GDPR per i dati personali?"]),
    _fu("cosa significa?",       _R, 1, ["Il D.Lgs. 231/2001 prevede la responsabilità degli enti."]),
    _fu("e le sanzioni?",        _R, 1, ["Come funziona la violazione del GDPR per una PMI?"]),
    _fu("rispiega meglio",       _R, 1, ["Qual è la differenza tra contratto a termine e indeterminato?"]),
    _fu("quindi posso farlo?",   _R, 1, ["Cosa prevede la legge per il licenziamento?"]),
    _fu("e la multa quanto è?",  _R, 1, ["Quali infrazioni del GDPR sono più comuni?"]),
    _fu("è sempre così?",        _R, 1, ["Quando si applica la responsabilità solidale nell'appalto?"]),
    _fu("e per i minori?",                      _R, 1, ["Cosa prevede il GDPR sul consenso dei dati?"]),
    _fu("e il responsabile del trattamento?",   _R, 2, ["Chi è il titolare del trattamento nel GDPR?"]),
    _fu("e le sanzioni massime?",               _R, 1, ["Come funziona la notifica di un data breach nel GDPR?"]),
    _fu("e se i dati vengono trasferiti fuori EU?", _R, 2, ["Cosa dice il GDPR sulle clausole standard?"]),
    _fu("e il diritto all'oblio?",              _R, 1, ["Spiega il diritto di accesso previsto dal GDPR."]),
    _fu("e il DPO è obbligatorio?",             _R, 2, ["Quando si nomina un Data Protection Officer?"]),
    _fu("e per le startup?",                    _R, 2, ["Quali obblighi GDPR ha una piccola impresa?"]),
    _fu("e i cookie?",                          _R, 1, ["Cosa prevede il GDPR per il marketing digitale?"]),
    _fu("e le app mobile?",                     _R, 2, ["Come si raccolgono i dati personali rispettando il GDPR?"]),
    _fu("vale anche per i dati anonimi?",       _R, 1, ["Quando un dato è considerato personale per il GDPR?"]),
    _fu("e per il lavoro part-time?",           _R, 1, ["Come funziona il contratto a tempo determinato?"]),
    _fu("e i contributi INPS?",                 _R, 2, ["Come si calcola il TFR?"]),
    _fu("e se il datore non paga?",             _R, 2, ["Quali sono i diritti del lavoratore in caso di ritardo dello stipendio?"]),
    _fu("e per i lavoratori autonomi?",         _R, 2, ["Cosa prevede lo Statuto dei Lavoratori?"]),
    _fu("e il mobbing come si prova?",          _R, 3, ["Cosa si intende per demansionamento?"]),
    _fu("e la giusta causa?",                   _R, 2, ["Spiega il licenziamento per giustificato motivo."]),
    _fu("entro quanto posso fare ricorso?",     _R, 1, ["Come si impugna un licenziamento illegittimo?"]),
    _fu("e il contratto collettivo?",           _R, 2, ["Cosa disciplina il CCNL Metalmeccanici?"]),
    _fu("e per i lavoratori stranieri?",        _R, 2, ["Quali permessi servono per lavorare in Italia?"]),
    _fu("e le ferie non godute?",               _R, 1, ["Il datore può rifiutare le ferie?"]),
    _fu("e il periodo di prova?",               _R, 1, ["Come si interrompe il rapporto di lavoro durante il preavviso?"]),
    _fu("e se una parte è incapace?",           _R, 2, ["Quando un contratto è nullo per il codice civile?"]),
    _fu("e la clausola penale?",                _R, 2, ["Cosa si intende per inadempimento contrattuale?"]),
    _fu("e l'exceptio non adimpleti contractus?",_R, 3, ["Spiega la risoluzione del contratto per inadempimento."]),
    _fu("e per i contratti online?",            _R, 2, ["Cosa prevede il Codice del Consumo?"]),
    _fu("entro quando posso recedere?",         _R, 1, ["Il consumatore ha diritto di recesso?"]),
    _fu("e il silenzio vale accettazione?",     _R, 2, ["Come si forma un contratto per corrispondenza?"]),
    _fu("e la responsabilità del venditore?",   _R, 2, ["Cosa copre la garanzia legale di conformità?"]),
    _fu("e i danni morali?",                    _R, 2, ["Come si quantificano i danni in un incidente stradale?"]),
    _fu("e la recidiva?",                       _R, 2, ["Quali circostanze aggravano il reato di furto?"]),
    _fu("e la prescrizione?",                   _R, 2, ["Quando si estingue un reato per prescrizione?"]),
    _fu("e per i minori?",                      _R, 2, ["Come funziona il processo penale minorile?"]),
    _fu("e la messa alla prova?",               _R, 2, ["Cos'è la sospensione condizionale della pena?"]),
    _fu("e la querela?",                        _R, 1, ["Come si denuncia un reato?"]),
    _fu("e la partita IVA a regime forfettario?",_R, 2, ["Quali sono le detrazioni IRPEF disponibili?"]),
    _fu("e le plusvalenze?",                    _R, 2, ["Come si dichiarano i redditi da investimenti?"]),
    _fu("e l'IVA sulle prestazioni digitali?",  _R, 2, ["Come funziona il reverse charge IVA?"]),
    _fu("e il ravvedimento operoso?",           _R, 2, ["Cosa succede in caso di dichiarazione tardiva?"]),

    # ── Follow-up dopo GENERAL ──
    _fu("perché?",       _G, 1, ["Ciao! Come stai?"]),
    _fu("e quindi?",     _G, 1, ["Consigliami un film di fantascienza."]),
    _fu("ne conosci altri?", _G, 1, ["Dammi una ricetta per la pasta al pomodoro."]),
    _fu("spiega meglio", _G, 1, ["Cos'è la fotosintesi clorofilliana?"]),
    _fu("come mai?",     _G, 1, ["L'acqua bolle a 100 gradi a livello del mare."]),
    _fu("non ho capito", _G, 1, ["Spiega la differenza tra DNA e RNA."]),
    _fu("davvero?",      _G, 1, ["Il ghiaccio si forma a 0 gradi Celsius."]),
    _fu("e gli animali lo fanno anche?",        _G, 1, ["Spiega il ciclo del sonno negli esseri umani."]),
    _fu("e su Marte?",                          _G, 1, ["Come funziona l'atmosfera terrestre?"]),
    _fu("e in assenza di gravità?",             _G, 1, ["Come funziona il sistema circolatorio umano?"]),
    _fu("e le piante?",                         _G, 1, ["Spiega la respirazione cellulare."]),
    _fu("e i batteri?",                         _G, 1, ["Come funziona il sistema immunitario?"]),
    _fu("e i virus?",                           _G, 1, ["Cosa sono gli anticorpi?"]),
    _fu("e il cervello umano?",                 _G, 1, ["Spiega come funziona la memoria."]),
    _fu("e nello spazio?",                      _G, 1, ["Come si propaga il suono nell'aria?"]),
    _fu("e per i daltonici?",                   _G, 1, ["Come vediamo i colori?"]),
    _fu("e i sogni?",                           _G, 1, ["Cosa succede al cervello durante il sonno REM?"]),
    _fu("e a temperature altissime?",           _G, 1, ["Spiega la differenza tra fusione e solidificazione."]),
    _fu("e il campo magnetico terrestre?",      _G, 1, ["Come funziona una bussola?"]),
    _fu("e le conseguenze?",                    _G, 1, ["Cosa causò la Prima Guerra Mondiale?"]),
    _fu("e gli USA?",                           _G, 1, ["Come nacque l'Unione Europea?"]),
    _fu("e la Russia?",                         _G, 1, ["Spiega la Rivoluzione Francese."]),
    _fu("e oggi come è cambiato?",              _G, 1, ["Cos'è il colonialismo?"]),
    _fu("e le vittime?",                        _G, 1, ["Spiega cos'è l'Olocausto."]),
    _fu("e la Cina?",                           _G, 1, ["Spiega la Guerra Fredda."]),
    _fu("ci sono ancora oggi?",                 _G, 1, ["Cosa sono le aristocrazie?"]),
    _fu("e in Italia?",                         _G, 1, ["Come funziona il sistema parlamentare?"]),
    _fu("e se sono intollerante al glutine?",   _G, 1, ["Dammi una ricetta per la pasta alla carbonara."]),
    _fu("e quanto tempo di cottura?",           _G, 1, ["Come si prepara il risotto alla milanese?"]),
    _fu("e varianti vegane?",                   _G, 1, ["Come si fa la lasagna al forno?"]),
    _fu("e senza forno?",                       _G, 1, ["Dammi una ricetta per la pizza napoletana."]),
    _fu("e se ho solo 15 minuti?",              _G, 1, ["Cosa posso cucinare con uova e pane?"]),
    _fu("e il vino abbinato?",                  _G, 1, ["Quale taglio di carne è migliore per una grigliata?"]),
    _fu("e il giorno dopo?",                    _G, 1, ["Come si conserva il tiramisù?"]),
    _fu("e se non funziona?",                   _G, 1, ["Come si affronta un colloquio di lavoro?"]),
    _fu("e online?",                            _G, 1, ["Come si impara una nuova lingua velocemente?"]),
    _fu("e se non ho soldi da investire?",      _G, 1, ["Come si inizia a investire in borsa?"]),
    _fu("e i rischi?",                          _G, 1, ["Cos'è il crowdfunding?"]),
    _fu("e per gli anziani?",                   _G, 1, ["Quali sono i benefici della meditazione?"]),
    _fu("e i bambini?",                         _G, 1, ["Spiega i benefici dello sport per la salute."]),
    _fu("ma funziona davvero?",                 _G, 1, ["Cosa si intende per pensiero positivo?"]),
    _fu("e la memoria a lungo termine?",        _G, 1, ["Come si studia in modo efficace?"]),
    _fu("e se ho ansia?",                       _G, 1, ["Come si gestisce lo stress da lavoro?"]),
    _fu("e le relazioni a distanza?",           _G, 1, ["Quali sono i fattori che rendono una relazione duratura?"]),
    _fu("e i social media?",                    _G, 1, ["Come si riconosce la manipolazione psicologica?"]),

    # ── Cambio DOMINIO (storia presente, ma is_followup=False) ──
    _cd("consigliami un ristorante a Roma",  _G, 1, ["Implementa server REST in Flask."]),
    _cd("consigliami scarpe uomo",           _G, 1, ["Come funziona la fattorizzazione LU?"]),
    _cd("cosa mangio stasera?",              _G, 1, ["Qual è la normativa GDPR sulla data retention?"]),
    _cd("dammi una barzelletta",             _G, 1, ["Implementa il metodo di Runge-Kutta 4."]),
    _cd("qual è la capitale della Francia?", _G, 1, ["Come configuro Kubernetes per il load balancing?"]),
    _cd("consigliami un libro",              _G, 1, ["Dimostra il teorema di Pitagora con geometria euclidea."]),
    _cd("chi ha vinto il mondiale 2022?",    _G, 1, ["Implementa la firma digitale RSA in Python."]),
    _cd("che film mi consigli?",             _G, 1, ["Implementa un sistema di cache LRU in Python."]),
    _cd("dove vado in vacanza?",             _G, 1, ["Come si calcola la trasformata di Laplace?"]),
    _cd("cosa faccio questo weekend?",       _G, 1, ["Spiega il pattern Command in Java."]),
    _cd("hai una barzelletta?",              _G, 1, ["Implementa un grafo orientato con lista di adiacenza."]),
    _cd("raccontami qualcosa di interessante",_G, 1, ["Come funziona la regressione logistica?"]),
    _cd("qual è il tuo colore preferito?",   _G, 1, ["Spiega la normalizzazione in un database SQL."]),
    _cd("dimmi una curiosità sul mondo",     _G, 1, ["Come si implementa un algoritmo genetico?"]),
    _cd("mi suggerisci un podcast?",         _G, 1, ["Spiega il teorema di Bayes con un esempio."]),
    _cd("cosa pensi dell'intelligenza artificiale?",_G,1,["Implementa una rete neurale ricorrente in PyTorch."]),
    _cd("fammi un complimento",              _G, 1, ["Come si gestisce la memoria in C++?"]),
    _cd("implementa un algoritmo per calcolare la traiettoria", _C, 3, ["Consigliami un libro di fisica."]),
    _cd("scrivi un programma che simula il lancio di una moneta", _C, 2, ["Spiega la teoria della probabilità."]),
    _cd("qual è la formula per calcolare gli interessi composti?", _M, 2, ["Cosa mi consigli per risparmiare?"]),
    _cd("quali norme regolano il telelavoro in Italia?", _R, 2, ["Cosa cambierà nel mondo del lavoro con l'AI?"]),
    # [FIX label-consistency] Era _M (mono-math): contraddiceva
    # expected_domain="rights" in eval_dataset.jsonl (F-EC7), causando un
    # test case auto-contraddittorio. Query bridge fiscale genuina
    # (calcolo + normativa IVA): ora rights->math esplicito.
    _r("come si calcola l'IVA su una fattura?", _RM, 1, is_pipe=True, pipe_type="rights->math",
       hist=["Come funziona la partita IVA?"], is_followup=False),
    _cd("scrivi una funzione Python per la validazione dell'email", _C, 1, ["Cosa prevede il GDPR sul consenso?"]),
    _cd("implementa il login con JWT in Flask", _C, 2, ["Come funziona l'autenticazione a due fattori?"]),
    _cd("è legale vendere dati statistici anonimi?", _R, 2, ["Come funziona l'analisi della varianza ANOVA?"]),
    _cd("quali norme regolano le scommesse sportive in Italia?", _R, 2, ["Spiega la probabilità condizionata."]),

    # ── SWITCH VERSO CODING (Da General, Math, Rights) ──
    _cd("scrivi uno script in Python per fare web scraping", _C, 2, ["Come faccio a coltivare i pomodori in balcone?"]),
    _cd("implementa un'architettura microservizi in Node.js", _C, 3, ["Qual è l'integrale definito di x al quadrato?"]),
    _cd("come si risolve un merge conflict su Git?", _C, 1, ["Cosa prevede l'articolo 2043 del codice civile sui danni?"]),
    _cd("configura un cluster Kubernetes con Terraform", _C, 3, ["Qual è il miglior film di Quentin Tarantino?"]),
    _cd("scrivi una funzione C++ per invertire una stringa", _C, 1, ["Spiega il teorema di Bayes sulla probabilità condizionata."]),

    # ── SWITCH VERSO MATH (Da General, Coding, Rights) ──
    _cd("calcola gli autovalori di questa matrice 3x3", _M, 2, ["Come si centra verticalmente un div in CSS?"]),
    _cd("dimostra per induzione che la somma dei primi n numeri è n(n+1)/2", _M, 2, ["Quali sono i requisiti per ottenere il divorzio breve?"]),
    _cd("qual è lo sviluppo in serie di Taylor del seno?", _M, 2, ["Come si prepara la vera carbonara romana?"]),
    _cd("risolvi questa equazione differenziale di secondo ordine", _M, 3, ["Implementa un'API REST in linguaggio Go."]),
    _cd("calcola la probabilità di ottenere due sei lanciando due dadi", _M, 1, ["Dove posso andare in vacanza ad agosto spendendo poco?"]),

    # ── SWITCH VERSO RIGHTS (Da General, Coding, Math) ──
    _cd("cosa rischia penalmente chi commette il reato di diffamazione online?", _R, 2, ["Come funziona il garbage collector in Java?"]),
    _cd("quali sono i diritti di un lavoratore licenziato senza giusta causa?", _R, 2, ["Qual è il limite per x che tende a zero di sin(x)/x?"]),
    _cd("come funziona l'affidamento congiunto dei figli in caso di separazione?", _R, 2, ["Consigliami un buon libro fantasy da leggere."]),
    _cd("quali sanzioni prevede il GDPR per la perdita di dati sanitari?", _R, 2, ["Spiega la scomposizione ai valori singolari (SVD) di una matrice."]),
    _cd("come si fa ricorso al TAR contro l'esito di un concorso pubblico?", _R, 2, ["Configura un database PostgreSQL utilizzando un file docker-compose."]),


    # ── Query ambigue SENZA history (→ general) ──
    _r("ciao, come stai?", _G, 1),
    _r("grazie!",          _G, 1),
    _r("ok",               _G, 1),
    _r("Dio esiste?",      _G, 1),
    _r("chi sei?",         _G, 1),
    _r("cosa ne pensi?",   _G, 1),
    _r("mi aiuti?",        _G, 1),
    _r("buongiorno",       _G, 1),
    _r("non so",           _G, 1),
    _r("2+2",              _M, 1),   # eccezione: math
    _r("chi ti ha creato?",_G, 1),
    _r("cosa sai fare?",   _G, 1),
    _r("aiuto",            _G, 1),
    _r("mi fai un esempio pratico?",         _G, 1),
    _r("puoi spiegarmelo più semplice?",     _G, 1),
    _r("quindi qual è la conclusione?",      _G, 1),

    # ── FALSE pipeline (sembrano multi-domain ma sono mono) ──
    _r("codice Python per sommare una lista di numeri", _C, 1),
    _r("scrivi una funzione Python che calcola la media",_C, 1),
    _r("codice per stampare i numeri da 1 a 100",       _C, 1),
    _r("Python per leggere un file CSV",                _C, 1),
    _r("cosa dice la legge sul codice fiscale?",        _R, 1),
    _r("spiegami la normativa sui contratti di lavoro", _R, 2),
    _r("qual è il codice penale per il furto?",         _R, 1),
    _r("cos'è la media geometrica?",                    _M, 1),
    _r("Quali sono gli obblighi di notifica al Garante Privacy in caso di violazione dei dati personali secondo il GDPR?", _R, 2),
    _r("Entro quanto tempo un'azienda deve segnalare una fuga di dati personali secondo la normativa europea?", _R, 1),
    _r("Premetto che tendo a essere prolisso quando scrivo, quindi abbi pazienza: sto scrivendo un piccolo tool per uso personale e mi sono impantanato in una parte dove devo gestire in modo sicuro l'apertura di un file che potrebbe non esistere sul disco, come si struttura correttamente il blocco try except in Python in questo caso?", _C, 2),
    # [FIX A-C1 rev.2] Il vecchio blocco di 10 record "calcola X in Python"
    # è stato spostato in FALSE_PIPELINE_HARD_NEGATIVES (fuori da
    # MANUAL_RECORDS, sotto): qui restava sommerso nel bucket 'coding' già
    # saturo (TARGET_MONO raggiunto solo da INTENT_SENTENCES/BRIDGE_SENTENCES)
    # e non riceveva MAI augmentation — retest post-retrain ha confermato il
    # fallimento persistente (conf 0.831/0.918 verso MATH->CODING).

    # ── TRUE pipeline ESPLICITE (segnale diretto) ──
    _r("scrivi codice C++ per Pitagora con dimostrazione matematica completa",
       _CM, 3, True, "math->coding"),
    _r("implementa in Python Kruskal e dimostra correttezza con teoria dei grafi",
       _CM, 3, True, "math->coding"),
    _r("implementa regressione lineare multipla in Python e dimostra teoria minimi quadrati",
       _CM, 3, True, "math->coding"),
    _r("scrivi codice Python che implementa FFT e dimostra il teorema di Nyquist-Shannon",
       _CM, 3, True, "math->coding"),
     _r("Fin da ragazzo trovavo affascinante il modo in cui la matematica pura finisce per nascondersi dentro le tecnologie che usiamo ogni giorno, dalla musica in streaming alle videochiamate: partendo da questa curiosità, dimostra il teorema di Nyquist-Shannon e poi implementa in Python la trasformata di Fourier veloce per campionare correttamente un segnale audio.",
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

    # ── [FIX WRONG_QUERY] RIGHTS colloquiale — responsabilità civile ──
    _r("Mio figlio ha rotto il vetro del vicino giocando a pallone: devo pagare io i danni?", _R, 2),
    _r("Il mio cane ha morso un passante per strada, chi paga le spese mediche?", _R, 2),
    _r("Sono scivolato in un negozio per il pavimento bagnato, posso chiedere un risarcimento?", _R, 2),

    # ── [FIX WRONG_QUERY] MATH — calcoli percentuali/fiscali ──
    _r("Come si calcola la percentuale di sconto applicata a un prezzo?", _M, 1),
    _r("Qual è la formula per calcolare l'IVA al 22% su un importo?", _M, 1),

    # ── [FIX WRONG_QUERY] CODING — ricorsione/algoritmi (NON identiche a
    #    step4_evaluation.py: evitare leakage sul test set) ──
    _r("Crea una funzione ricorsiva in Python per calcolare il fattoriale di un numero.", _C, 1),
    _r("Come si implementa il calcolo dei numeri di Fibonacci con la ricorsione in Python?", _C, 1),
    _r("Scrivi in Python l'algoritmo di Dijkstra per il cammino minimo su un grafo pesato.", _C, 2),
    _r("Implementa la ricerca binaria in versione ricorsiva usando Python.", _C, 1),

    # ── [FIX WRONG_QUERY] Rinforzo negative-class is_followup su switch di
    #    dominio — contrasta sbilanciamento _fu:_cd ~7.5:1 (Report Gemini #1) ──
    _cd("quanto costa un biglietto aereo per Tokyo?",              _G, 1, ["Spiega il pattern Observer in OOP."]),
    _cd("che tempo fa domani?",                                    _G, 1, ["Dimostra il teorema di Lagrange."]),
    _cd("mi consigli una serie tv?",                               _G, 1, ["Cosa prevede il GDPR sul diritto all'oblio?"]),
    _cd("qual è il senso della vita secondo te?",                  _G, 1, ["Implementa un algoritmo di clustering K-means."]),
    _cd("come si allena la resistenza per una maratona?",          _G, 1, ["Spiega la differenza tra nullità e annullabilità."]),
    _cd("quanto è alto il Monte Everest?",                         _G, 1, ["Calcola l'integrale di 1/(1+x^2)."]),
    _cd("mi spieghi le regole del tennis?",                        _G, 1, ["Come si implementa OAuth 2.0?"]),
    _cd("qual è il miglior modo per risparmiare energia in casa?", _G, 1, ["Quali sono le tutele per il whistleblowing?"]),
    _cd("hai un consiglio per smettere di fumare?",                _G, 1, ["Spiega la decomposizione LU di una matrice."]),
    _cd("cosa vedo stasera al cinema?",                            _G, 1, ["Implementa il pattern Factory in Java."]),
    _cd("in che anno è caduto il Muro di Berlino?",                _G, 1, ["Come funziona la crittografia a curva ellittica?"]),
    _cd("qual è il modo migliore per organizzare un trasloco?",    _G, 1, ["Cosa prevede il Codice del Consumo sul recesso?"]),
    _cd("come si fa il nodo alla cravatta?",                       _G, 1, ["Dimostra il teorema di Bayes con un esempio."]),
    _cd("mi dai un consiglio per dormire meglio?",                 _G, 1, ["Spiega il funzionamento di un container Docker."]),
    _cd("qual è la differenza tra tè verde e tè nero?",            _G, 1, ["Quali sanzioni prevede il GDPR per una violazione grave?"]),

    # ── [FIX wrong_query.md] Ulteriore rinforzo negative-class is_followup:
    #    i test falliti su domain_switch corrispondono a query IDENTICHE già
    #    presenti sopra ma comunque misclassificate a is_followup=True → il
    #    problema non è copertura dati ma calibrazione (vedi MAX_POS_WEIGHT).
    #    Questi 15 record ampliano comunque la diversità lessicale/tematica
    #    della classe negativa per dare più segnale al training. ──
    _cd("mi consigli un buon vino per la cena?",                   _G, 1, ["Come si implementa un web scraper con BeautifulSoup?"]),
    _cd("che ore sono a New York adesso?",                         _G, 1, ["Spiega la differenza tra TCP e UDP."]),
    _cd("qual è la canzone più ascoltata quest'anno?",             _G, 1, ["Come si scrive un decoratore in Python?"]),
    _cd("mi consigli un buon profumo da regalare?",                _G, 1, ["Implementa un Dockerfile multi-stage per Node.js."]),
    _cd("come si gioca a burraco?",                                _G, 1, ["Come funziona il garbage collector in Java?"]),
    _cd("quanti pianeti ci sono nel sistema solare?",              _G, 1, ["Calcola l'integrale improprio di 1/x^2 da 1 a infinito."]),
    _cd("mi consigli uno sport da iniziare a 30 anni?",            _G, 1, ["Dimostra il teorema di Rolle."]),
    _cd("qual è il fiume più lungo del mondo?",                    _G, 1, ["Calcola gli autovalori di una matrice 4x4."]),
    _cd("come si prepara un buon caffè con la moka?",              _G, 1, ["Spiega la distribuzione di Poisson."]),
    _cd("mi racconti una barzelletta sui matematici?",             _G, 1, ["Risolvi l'equazione differenziale del secondo ordine."]),
    _cd("cosa mi consigli per un regalo di compleanno economico?", _G, 1, ["Cosa prevede il Codice del Consumo sulla garanzia legale?"]),
    _cd("quali sono le migliori app per imparare l'inglese?",      _G, 1, ["Come funziona il ricorso al TAR?"]),
    _cd("mi dai qualche consiglio per un colloquio da remoto?",    _G, 1, ["Quali sono le tutele per il whistleblowing aziendale?"]),
    _cd("qual è il modo migliore per fare amicizia in una nuova città?", _G, 1, ["Cosa prevede la Costituzione sul referendum abrogativo?"]),
    _cd("come si fa a togliere una macchia di grasso da una giacca?",    _G, 1, ["Spiega la differenza tra dolo e colpa nel diritto penale."]),

    # ── [FIX report_16errors] Domain-switch corto dopo history tecnica ──
    _cd("che giorno è oggi?",                _G, 1, ["Implementa la ricerca binaria ricorsiva in C++."]),
    _cd("a che ora chiude il supermercato?", _G, 1, ["Dimostra il teorema di Talete con la relativa costruzione geometrica."]),
    _cd("grazie di tutto, alla prossima",    _G, 1, ["Quali sono gli obblighi del titolare del trattamento secondo il GDPR?"]),

    # ── [T1 report_espansione §9.2-P1] Domain-switch verso GENERAL: query brevissime/varie dopo history tecnica ──
    # 60 record = 20 per dominio della history (coding / math / rights), query TUTTE uniche (nessun near-duplicate
    # tra split), tutte con: general=1, is_followup=False, difficulty=1, history di 1 query utente.
    # Categorie query per blocco: cortesia/chiusura/saluto, esistenziali, sull'assistente, vita quotidiana, giochi/creativo.
    # History mescolate lunghe (>=14 parole) e corte: il fallimento osservato e' "query corta + history tecnica lunga".

    # -- history CODING -> general --
    _cd("buonanotte",                                    _G, 1, ["Come si struttura un progetto Django con più app e un database PostgreSQL condiviso tra tutti i servizi?"]),
    _cd("ti ringrazio, a presto",                        _G, 1, ["Scrivi una funzione in Rust che legge un file di log riga per riga e conta le occorrenze di ogni messaggio di errore."]),
    _cd("ciao ciao, a dopo",                             _G, 1, ["Come si configura un cluster Redis con replica e failover automatico usando Sentinel in un ambiente Docker?"]),
    _cd("cos'è la felicità?",                            _G, 1, ["Implementa in TypeScript un sistema di eventi con tipi generici e sottoscrizioni che si annullano automaticamente."]),
    _cd("come ti chiami?",                               _G, 1, ["Spiegami la differenza tra stack e heap nella gestione della memoria in C e quando conviene usare malloc."]),
    _cd("siamo soli nell'universo?",                     _G, 1, ["Scrivi un workflow GitHub Actions che esegue i test, costruisce l'immagine Docker e la pubblica su un registry privato."]),
    _cd("dimmi una battuta sui gatti",                   _G, 1, ["Come si inverte una stringa in Java?"]),
    _cd("qual è la montagna più alta d'Europa?",         _G, 1, ["Come si usa async/await in C#?"]),
    _cd("mi consigli una canzone per correre?",          _G, 1, ["Come funziona il pattern Repository?"]),
    _cd("sei un robot?",                                 _G, 1, ["Come si crea un array di oggetti in JavaScript?"]),
    _cd("che colore sta bene con il blu?",               _G, 1, ["Differenza tra INNER JOIN e LEFT JOIN?"]),
    _cd("buon weekend!",                                 _G, 1, ["Come si scrive un unit test per una funzione che chiama un'API esterna?"]),
    _cd("come si fa il bucato a mano?",                  _G, 1, ["Come faccio a debuggare un segmentation fault in un programma C++?"]),
    _cd("quanti anni hai?",                              _G, 1, ["Come si implementa una lista doppiamente concatenata in C?"]),
    _cd("dove si può vedere l'aurora boreale?",          _G, 1, ["Scrivi un endpoint FastAPI che restituisce una lista paginata di utenti."]),
    _cd("salve, ci sei?",                                _G, 1, ["Come si gestisce l'autenticazione con refresh token in un'applicazione React che parla con un backend Node.js?"]),
    _cd("esiste il libero arbitrio?",                    _G, 1, ["Vorrei capire come funziona il meccanismo di ereditarietà multipla in Python e come viene risolto l'ordine dei metodi."]),
    _cd("hai un indovinello per me?",                    _G, 1, ["Come si fa il rollback di un commit già pubblicato su un branch condiviso?"]),
    _cd("come si prepara il tè freddo in casa?",         _G, 1, ["Cos'è un semaforo in programmazione concorrente?"]),
    _cd("sei stato molto gentile",                       _G, 1, ["Scrivi uno script Bash che scorre tutte le cartelle di un progetto e sostituisce una stringa in ogni file di configurazione."]),

    # -- history MATH -> general --
    _cd("buona serata a te!",                            _G, 1, ["Calcola l'integrale definito di x al quadrato per il seno di x tra zero e pi greco usando l'integrazione per parti."]),
    _cd("grazie per la pazienza",                        _G, 1, ["Dimostra che la successione definita per ricorrenza converge alla radice quadrata di due partendo da un valore positivo."]),
    _cd("ora vado a fare una pausa",                     _G, 1, ["Determina la forma canonica di Jordan di una matrice 4x4 con un autovalore triplo e uno semplice."]),
    _cd("il destino esiste o ce lo costruiamo?",         _G, 1, ["Risolvi il sistema di equazioni differenziali lineari a coefficienti costanti usando la matrice esponenziale."]),
    _cd("che lingue sai parlare?",                       _G, 1, ["Enuncia e dimostra il teorema di Bolzano-Weierstrass per successioni limitate in R^n."]),
    _cd("qual è il piatto tipico della Sicilia?",        _G, 1, ["Spiega come si costruisce un intervallo di confidenza per la proporzione di una popolazione con un campione grande."]),
    _cd("raccontami una favola breve",                   _G, 1, ["Come si calcola il prodotto vettoriale?"]),
    _cd("come si allevia il mal di schiena da scrivania?", _G, 1, ["Cos'è un autovalore?"]),
    _cd("buon pranzo!",                                  _G, 1, ["Derivata di ln(x^2+1)"]),
    _cd("ottima giornata!",                              _G, 1, ["Come si risolve una disequazione di secondo grado?"]),
    _cd("cosa succede dopo la morte?",                   _G, 1, ["Trova il dominio e gli asintoti della funzione f(x) = (x^2 - 1)/(x - 2)."]),
    _cd("come si tiene in ordine un armadio piccolo?",   _G, 1, ["Calcola la probabilità di estrarre due carte rosse consecutive da un mazzo da 52 carte."]),
    _cd("ti annoi mai?",                                 _G, 1, ["Come si dimostra che la radice quadrata di tre è irrazionale?"]),
    _cd("mi dai un'idea per un regalo di nozze?",        _G, 1, ["Qual è la differenza tra convergenza puntuale e convergenza uniforme?"]),
    _cd("fammi ridere",                                  _G, 1, ["Cos'è il rango di una matrice?"]),
    _cd("l'amore esiste davvero?",                       _G, 1, ["Studia il segno della derivata seconda per determinare la concavità e i punti di flesso della funzione."]),
    _cd("torno più tardi, ciao",                         _G, 1, ["Applica la disuguaglianza di Cauchy-Schwarz per dimostrare la disuguaglianza triangolare in uno spazio euclideo."]),
    _cd("in che stagione conviene visitare Lisbona?",    _G, 1, ["Come si calcola la somma di una serie geometrica?"]),
    _cd("cantami una ninna nanna",                       _G, 1, ["Trova la distribuzione della somma di due variabili aleatorie normali indipendenti."]),
    _cd("come faccio a svegliarmi presto la mattina?",   _G, 1, ["Calcola la trasformata di Fourier della funzione gaussiana e spiega perché resta una gaussiana."]),

    # -- history RIGHTS -> general --
    _cd("ci sentiamo domani",                            _G, 1, ["Quali sono i requisiti per impugnare un licenziamento per giusta causa e quali sono i termini di decadenza?"]),
    _cd("arrivederci e grazie ancora",                   _G, 1, ["Come funziona la successione legittima in assenza di testamento quando ci sono figli e coniuge superstite?"]),
    _cd("che cos'è la coscienza?",                       _G, 1, ["Quali obblighi ha il titolare di un sito web che utilizza cookie di profilazione secondo la normativa europea?"]),
    _cd("hai mai sognato?",                              _G, 1, ["Spiega la differenza tra dolo eventuale e colpa cosciente nei reati commessi alla guida di un veicolo."]),
    _cd("che fiori si piantano a primavera sul balcone?", _G, 1, ["Come si presenta un ricorso al giudice di pace contro una sanzione amministrativa per divieto di sosta?"]),
    _cd("cosa fai quando nessuno ti scrive?",            _G, 1, ["Cosa prevede il codice civile sulla responsabilità del condominio per i danni causati dalle infiltrazioni d'acqua?"]),
    _cd("quanto tempo ci vuole in treno da Milano a Venezia?", _G, 1, ["Cos'è la prescrizione in ambito civile?"]),
    _cd("qual è il gelato più venduto in Italia?",       _G, 1, ["Come funziona il patto di non concorrenza?"]),
    _cd("vale la pena essere gentili con tutti?",        _G, 1, ["Quando scatta il reato di stalking?"]),
    _cd("chi ha dipinto la Cappella Sistina?",           _G, 1, ["Come si registra un contratto di locazione?"]),
    _cd("come si impara a nuotare da adulti?",           _G, 1, ["Quali diritti ha il consumatore in caso di ritardo nella consegna di un acquisto online?"]),
    _cd("ti piace la musica?",                           _G, 1, ["Come si dividono i beni in caso di separazione con comunione legale?"]),
    _cd("inventa un nome per un gattino nero",           _G, 1, ["Chi risponde civilmente dei danni causati da un minore a scuola?"]),
    _cd("che animale domestico è più adatto a un appartamento piccolo?", _G, 1, ["Cosa rischia un datore di lavoro che non versa i contributi previdenziali?"]),
    _cd("dimmi una frase motivante per iniziare la giornata", _G, 1, ["Cos'è il diritto di prelazione?"]),
    _cd("buonasera",                                     _G, 1, ["Quali sono le tutele previste per una lavoratrice madre durante la gravidanza e nei primi mesi di vita del bambino?"]),
    _cd("scrivimi una poesia sul mare",                  _G, 1, ["Come funziona la mediazione obbligatoria prima di una causa civile?"]),
    _cd("qual è il paese più grande del mondo?",         _G, 1, ["Come si impugna un testamento?"]),
    _cd("per oggi può bastare, grazie",                  _G, 1, ["Quali sono le pene previste per il reato di truffa aggravata?"]),
    _cd("come si cura un basilico che ingiallisce?",     _G, 1, ["Come funziona la caparra confirmatoria in un preliminare di compravendita immobiliare?"]),

    # ── [FIX report_16errors] Diluizione estrema (~90%+ rumore) — CODING/MATH ──
    _r("Ripenso spesso a quanto il sapere umano sia il risultato di secoli di tentativi ed errori, di persone che hanno dedicato la vita intera a capire meccanismi che oggi diamo per scontati, ed è proprio con questo spirito di gratitudine verso chi è venuto prima di noi che oggi ti volevo chiedere una cosa piccola ma per me significativa: merge sort complessità O(n log n)", _C, 1),
    _r("Non so se hai presente quella sensazione quando leggi un romanzo storico e ti accorgi che i grandi passi avanti della civiltà sono spesso partiti da domande semplici fatte da persone curiose che non si accontentavano delle risposte facili, ed è un po' con questo spirito che ti scrivo oggi, senza fretta e senza un vero motivo pratico: determinante matrice 3x3", _M, 1),

    # ── [FIX report_16errors] Code-switch IT/EN — CODING ──
    _r("Il mio professore di ingegneria del software vuole il deployment del progetto su un cloud provider entro venerdì e onestamente non ho la più pallida idea di come iniziare, mi aiuti a capire i primi passi?", _C, 2),

    # ══════════════════════════════════════════════════════════════════════
    # [T2 — report_espansione §9.3 / piano_lavoro T2] Espansione is_followup
    # ------------------------------------------------------------------------
    # Applicata la decisione D1-C (HISTORY_MAX_TURNS=1 in history_utils.py):
    # ogni nuovo record qui sotto usa al massimo 1 query di history, coerente
    # col mismatch training/inferenza descritto nel piano di lavoro §2.6.
    # Tre blocchi, ciascuno mirato a una causa di errore specifica già
    # diagnosticata (mai bulk generico):
    #   T2-A: follow-up verbosi/lunghi con history (oggi 1 solo → D-FU7-verbose)
    #   T2-B: marcatori brevi diversificati dopo history general/varia (D-FU4)
    #   T2-C: negativi ellittici SENZA history (A-M5: falso positivo a vuoto)
    # ══════════════════════════════════════════════════════════════════════

    # ── T2-A: Follow-up verbosi/lunghi (8 per dominio) ──
    _fu("Scusami se te lo richiedo in un altro modo, ma la spiegazione di prima non mi è entrata bene in testa: potresti rifare lo stesso ragionamento con parole più semplici, magari con un esempio concreto?", _C, 2, ["Come funziona il garbage collector in Java?"]),
    _fu("Capito il concetto generale, però mi manca ancora un pezzo: cosa succede esattamente nello stack di chiamate quando la funzione richiama se stessa più volte di seguito?", _C, 2, ["Come funziona il pattern Iterator in programmazione a oggetti?"]),
    _fu("Va bene, funziona, ma prima di segnarmelo da qualche parte vorrei capire il rovescio della medaglia: in quali situazioni questo approccio smette di essere la scelta migliore rispetto alle alternative?", _C, 2, ["Come funziona il pattern Singleton?"]),
    _fu("Prima di andare avanti volevo essere sicuro di aver capito questo passaggio: perché serve proprio quella condizione di uscita e cosa succederebbe in pratica se la togliessi?", _C, 2, ["Implementa DFS su un albero binario."]),
    _fu("C'è una cosa che mi lascia perplesso nella soluzione che mi hai proposto: non rischia di comportarsi in modo strano se in input arriva una lista vuota o con un solo elemento?", _C, 2, ["Scrivi una funzione Python che ordina una lista di numeri."]),
    _fu("Mi rendo conto solo adesso di non aver capito un dettaglio importante: quando dici che l'operazione è veloce, intendi sempre, anche nel caso peggiore possibile?", _C, 2, ["Qual è la complessità di inserimento in una tabella hash?"]),
    _fu("Grazie, ci sono quasi, ma vorrei un ultimo chiarimento pratico prima di applicarlo davvero: come mi comporto se due elementi finiscono per avere esattamente la stessa priorità?", _C, 2, ["Implementa una coda con priorità in Python."]),
    _fu("Rileggendo con calma quello che mi hai scritto mi è venuto un dubbio che non avevo considerato prima: cosa cambierebbe se dovessi far girare questo stesso codice su più thread contemporaneamente?", _C, 3, ["Scrivi una classe orientata agli oggetti con ereditarietà e polimorfismo."]),

    _fu("Ho riletto due volte il passaggio ma continuo a perdermi in un punto preciso: come si giustifica il fatto che si possa scambiare l'ordine tra limite e sommatoria proprio in quel punto della dimostrazione?", _M, 3, ["Dimostra la convergenza dell'integrale improprio utilizzando i criteri del confronto."]),
    _fu("Va bene il risultato finale, ma vorrei capire meglio il ragionamento intermedio: perché a un certo punto hai potuto trascurare quel termine senza che cambiasse il risultato complessivo?", _M, 2, ["Calcola il limite per x che tende a infinito di questa funzione razionale."]),
    _fu("Mi rendo conto solo ora di non aver capito una cosa di base che probabilmente davi per scontata: quando applichi quella sostituzione, come cambiano di conseguenza anche gli estremi di integrazione?", _M, 2, ["Usa il metodo di sostituzione per risolvere questo integrale irrazionale."]),
    _fu("Scusa se insisto proprio su questo punto, ma prima di proseguire con l'esercizio successivo vorrei essere sicuro: quella condizione sugli autovalori vale sempre o solo nel caso di matrici simmetriche?", _M, 2, ["Verifica se la matrice è diagonalizzabile confrontando la molteplicità algebrica e geometrica."]),
    _fu("C'è un dettaglio che non mi torna proprio nel passaggio dove applichi quel criterio: cosa cambierebbe nella conclusione se la serie non fosse a termini tutti positivi?", _M, 2, ["Determina la convergenza di una serie a termini positivi tramite il criterio del confronto asintotico."]),
    _fu("Prima di passare all'esercizio successivo vorrei un chiarimento su un'ipotesi che hai usato: il teorema richiede che la funzione sia definita su tutto l'intervallo o basta che lo sia quasi ovunque?", _M, 2, ["Applica il teorema di Rolle, Lagrange o Cauchy per dimostrare l'enunciato."]),
    _fu("Mi era sembrato tutto chiaro finché non ho provato a rifarlo da solo: nel passaggio in cui isoli la variabile, perché è lecito dividere per quel termine senza discutere il caso in cui sia nullo?", _M, 2, ["Risolvi il seguente sistema di equazioni lineari a tre incognite."]),
    _fu("Avrei bisogno di un chiarimento su un'assunzione implicita del ragionamento: questa proprietà vale solo nello spazio euclideo oppure si generalizza anche a spazi vettoriali qualsiasi?", _M, 3, ["Dimostra che questi vettori formano una base ortogonale per lo spazio vettoriale R3."]),

    _fu("Ti seguo fin qui, ma resta un dubbio molto pratico che mi interessa parecchio: cosa cambia concretamente se il rapporto di lavoro è a tempo determinato invece che indeterminato?", _R, 2, ["Spiega la differenza tra licenziamento per giusta causa e giustificato motivo oggettivo."]),
    _fu("Va bene la regola generale, ma vorrei capire anche un caso limite che mi riguarda piuttosto da vicino: cosa succede se il preavviso non viene rispettato da nessuna delle due parti coinvolte?", _R, 2, ["Come funziona la disciplina del contratto a tempo determinato e le causali di rinnovo."]),
    _fu("C'è un aspetto che non avevo considerato e che invece adesso mi sta particolarmente a cuore: questa tutela vale anche per chi lavora part-time oppure cambia qualcosa nel calcolo?", _R, 2, ["Quali sono i diritti del lavoratore subordinato in tema di ferie, malattia e permessi retribuiti?"]),
    _fu("Grazie, molto chiaro, ma vorrei capire meglio anche un passaggio più procedurale che mi serve per davvero: entro quanto tempo dalla notifica bisogna muoversi per non perdere questo diritto?", _R, 2, ["Come funziona il ricorso gerarchico e il ricorso al TAR nel diritto amministrativo?"]),
    _fu("Mi è tornato in mente solo ora un dettaglio del mio caso specifico che potrebbe cambiare tutto: la regola che mi hai spiegato cambia se una delle parti coinvolte è minorenne?", _R, 2, ["Spiega le differenze tra risoluzione per inadempimento, impossibilità sopravvenuta ed eccessiva onerosità."]),
    _fu("Prima di chiudere l'argomento vorrei un ultimo chiarimento molto concreto: chi si occupa materialmente di far rispettare questa norma, e cosa succede se in pratica nessuno interviene?", _R, 2, ["Quali sono gli obblighi di sicurezza sul lavoro previsti dal D.Lgs. 81/08?"]),
    _fu("Capisco il principio generale, ma nella pratica di tutti i giorni mi resta un dubbio che vorrei toglierti: chi deve dimostrare che le cose sono andate davvero in quel modo, io o l'altra parte?", _R, 2, ["Quali sono le tutele per il consumatore contro le clausole vessatorie secondo il Codice del Consumo?"]),
    _fu("Riflettendoci meglio dopo la tua risposta mi è venuto un dubbio che riguarda proprio il mio caso: questa procedura cambia in qualche modo se una delle parti si trova all'estero?", _R, 3, ["Come si articola il contenzioso tributario e quali sono i gradi di giudizio delle Commissioni Tributarie?"]),

    _fu("Mi hai incuriosito parecchio con questa cosa, quindi vorrei approfondire ancora un po': come mai proprio in quel periodo storico è successo tutto questo e non prima o dopo?", _G, 1, ["Come si è evoluto il ruolo della donna nella società europea del dopoguerra?"]),
    _fu("Ok, buono a sapersi, ma mi resta una curiosità collegata a quello che mi hai appena detto: funziona allo stesso modo anche negli altri animali o è una cosa tipicamente umana?", _G, 1, ["Spiega il meccanismo dell'evoluzione darwiniana, la genetica e la selezione naturale."]),
    _fu("Interessante, non lo sapevo affatto, ma mi chiedo se c'entri qualcosa anche con quello che si sente dire spesso online: è collegato in qualche modo oppure sono in realtà due cose distinte?", _G, 1, ["Spiegami il fenomeno della globalizzazione e l'impatto dei social media sulla comunicazione di massa."]),
    _fu("Grazie, adesso è più chiaro, però mi resta un dubbio molto pratico che vorrei toglierti volentieri: nella vita di tutti i giorni come faccio a riconoscere quando succede davvero?", _G, 1, ["Come si riconosce la manipolazione psicologica?"]),
    _fu("Bella questa cosa che mi hai appena raccontato, mi fa venire in mente una domanda collegata: c'entra qualcosa col motivo per cui certe usanze sono rimaste praticamente uguali nei secoli?", _G, 1, ["Come ci si comporta a tavola in Giappone e quali sono le usanze del galateo locale?"]),
    _fu("Non ci avevo mai pensato in questi termini, quindi mi lasci con una curiosità in più: cambia qualcosa se si applica la stessa logica su una scala molto più piccola, tipo dentro una famiglia?", _G, 1, ["Come funziona il mercato azionario e quali sono i concetti base per chi vuole iniziare a investire?"]),
    _fu("Molto utile, grazie, ma mi resta un dubbio pratico legato al mio caso specifico: cambia qualcosa se lo faccio in un appartamento piccolo invece che in una casa con giardino?", _G, 1, ["Come si coltivano le piante da appartamento e quanto spesso vanno annaffiate?"]),
    _fu("Riflettendoci un attimo dopo aver letto la tua risposta mi è venuto un dubbio più ampio che mi incuriosisce parecchio: si può dire che sia successo qualcosa di simile anche in altre epoche storiche?", _G, 2, ["Come è cambiata la televisione con l'avvento delle piattaforme di streaming come Netflix?"]),

    # ── T2-B: Marcatori brevi diversificati dopo history general/varia (D-FU4) ──
    _fu("ah ok, e poi?", _G, 1, ["Come è cambiata la televisione con l'avvento delle piattaforme di streaming come Netflix?"]),
    _fu("davvero? raccontami di più", _G, 1, ["Quali sono i generi musicali più popolari del ventesimo secolo e come sono nati?"]),
    _fu("capito, e come si fa in pratica?", _G, 1, ["Quali sono i principi di una dieta equilibrata per chi pratica sport a livello amatoriale?"]),
    _fu("interessante, continua pure", _G, 1, ["Quali sono le principali disparità economiche nel mondo e le loro radici storiche?"]),
    _fu("ok ma perché proprio così?", _G, 1, ["Come funziona il ciclo dell'acqua sulla Terra e quali sono le sue fasi meteorologiche?"]),
    _fu("e se invece fosse il contrario?", _G, 1, ["Quali sono i pro e i contro psicologici e culturali di vivere in una grande metropoli rispetto alla campagna?"]),
    _fu("aspetta, quindi come funziona esattamente?", _G, 1, ["Cosa sono gli esopianeti e quali sono i metodi attuali per scoprirli nello spazio?"]),
    _fu("wow, e quindi cosa comporta?", _G, 1, ["Come influisce il cambiamento climatico sugli ecosistemi globali e sull'economia moderna?"]),
    _fu("giusto, e dopo cosa succede?", _G, 1, ["Quali furono le trasformazioni politiche, i movimenti sociali e i personaggi storici legati all'introduzione del suffragio universale in Italia?"]),
    _fu("ah, non lo sapevo, e quindi?", _G, 1, ["Qual è l'impatto della musica streaming sull'industria discografica?"]),
    _fu("ok, ma nella pratica?", _G, 1, ["Quali sono i benefici della meditazione mindfulness per la salute mentale a lungo termine?"]),
    _fu("e come mai proprio così?", _G, 1, ["Come funziona il sistema immunitario umano in risposta a un'infezione batterica o virale?"]),
    _fu("davvero, in che senso?", _G, 1, ["Cosa sono le cellule staminali e come vengono utilizzate nella medicina moderna rigenerativa?"]),
    _fu("ah interessante, e in Italia?", _G, 1, ["Quali sono le principali catene montuose del mondo, come si sono formate geologicamente e come influenzano il clima locale?"]),
    _fu("e quanto ci vuole di solito?", _G, 1, ["Come faccio a organizzare un viaggio economico di due settimane in Giappone?"]),
    _fu("capito, e se sbaglio?", _G, 1, ["Spiegami come strutturare un curriculum vitae efficace per trovare lavoro rapidamente."]),
    _fu("ok, ma è sempre vero?", _G, 1, ["Quali sono le differenze tra le varie generazioni sociologiche come Boomer, Millennial e Gen Z?"]),
    _fu("e come si nota dall'esterno?", _G, 1, ["Qual è il linguaggio del corpo e come si possono interpretare le microespressioni facciali umane?"]),
    _fu("interessante, e da cosa dipende?", _G, 1, ["Quali sono i principali festival culturali e musicali nel mondo che vale la pena visitare?"]),
    _fu("ah ecco, e quindi conviene farlo?", _G, 1, ["Qual è il processo decisionale migliore per scegliere lo stile e l'arredamento di un piccolo soggiorno?"]),
    _fu("giusto, ma quanto costa in media?", _G, 1, ["Quali sono le usanze e le buone maniere da rispettare durante una cena di gala formale?"]),
    _fu("capito, e vale per tutti?", _G, 1, ["Come influisce lo stile di vita sedentario sulla salute a lungo termine?"]),
    _fu("ah davvero, e chi lo decide?", _G, 1, ["Come funziona il sistema di punteggio nel bowling e come si calcola il risultato finale?"]),
    _fu("ok, e a cosa serve realmente?", _G, 1, ["Illustrami il concetto danese dell'Hygge e come applicarlo nella vita quotidiana e in casa."]),
    _fu("interessante, e quanto è diffuso?", _G, 1, ["Quali sono le differenze tra lo yoga Hatha e lo yoga Vinyasa?"]),
    _fu("ah capito, e nel resto del mondo?", _G, 1, ["Come ci si organizza per affrontare un trasloco senza stressarsi?"]),
    _fu("e succede spesso una cosa così?", _G, 1, ["Qual è il significato allegorico del romanzo 1984 di George Orwell?"]),
    _fu("ok, ma è una regola fissa?", _G, 1, ["Come funziona il vantaggio e il fuorigioco nel rugby moderno?"]),
    _fu("davvero interessante, e da dove nasce?", _G, 1, ["Come si crea una palette cromatica e qual è il metodo visivo per abbinare i vestiti in modo elegante?"]),
    _fu("giusto, e chi se ne accorge di solito?", _G, 1, ["Come si addestra efficacemente un cucciolo di cane nei primi mesi di vita?"]),
    _fu("ah, e in che modo cambia le cose?", _G, 1, ["Spiegami il concetto di economia circolare e come può ridurre l'impatto ambientale dei rifiuti."]),
    _fu("capito, ma è consigliato per tutti?", _G, 1, ["Dammi una routine di esercizi di stretching da fare a casa per migliorare la flessibilità."]),
    _fu("interessante, e i risultati si vedono subito?", _G, 1, ["In cosa consiste il protocollo di allenamento Tabata e come si implementa a corpo libero?"]),
    _fu("ok, e serve un'attrezzatura particolare?", _G, 1, ["Come si organizza un allenamento funzionale a corpo libero per aumentare la forza?"]),
    _fu("ah ok, e quanto dura in genere?", _G, 1, ["Qual è il processo creativo che usa un regista per decidere il montaggio di un film?"]),
    _fu("giusto, e con che criterio si sceglie?", _G, 1, ["Quali sono i principi estetici fondamentali per scattare una fotografia di ritratto con luce naturale?"]),
    _fu("davvero, e come si spiega il fenomeno?", _G, 1, ["Come si formano i terremoti e i vulcani secondo la teoria della tettonica a placche?"]),
    _fu("ok, e vale anche di notte?", _G, 1, ["Quali sono le caratteristiche fisiche della Luna e come influenzano le maree terrestri?"]),
    _fu("interessante, ma è recente come scoperta?", _G, 1, ["Spiegami la formazione dei buchi neri supermassicci e i concetti base dell'astronomia moderna."]),
    _fu("ah capito, e a chi conviene di più?", _G, 1, ["Cosa sono i titoli di stato, le obbligazioni e come funziona il mercato obbligazionario?"]),
    _fu("giusto, e la differenza si sente davvero?", _G, 1, ["Come si legge un bilancio aziendale di base e qual è la differenza tra stato patrimoniale e conto economico?"]),
    _fu("ok, e cosa comporta nel concreto?", _G, 1, ["Spiegami le cause e le conseguenze dell'inflazione e come le banche centrali usano i tassi d'interesse."]),
    _fu("davvero, e come me ne accorgo?", _G, 1, ["Quali sono le dinamiche psicologiche e i fattori chiave per mantenere viva l'intesa in un matrimonio?"]),
    _fu("interessante, e cambia da paese a paese?", _G, 1, ["Quali sono le differenze stilistiche tra la musica classica di Mozart e quella di Beethoven?"]),
    _fu("ah, e questo cosa spiega esattamente?", _G, 1, ["Spiega il paradosso del gatto di Schrödinger e le sue implicazioni base per capire i quanti."]),
    _fu("ok, ma è un fenomeno raro?", _G, 1, ["Cosa intendeva Platone con la sua teoria delle idee e il mito della caverna?"]),
    _fu("giusto, e serve tanta pratica?", _G, 1, ["Quali sono le tecniche migliori per imparare a suonare la chitarra classica da autodidatta?"]),
    _fu("capito, e conviene farlo da soli o in gruppo?", _G, 1, ["Come si organizza un torneo di tennis a eliminazione diretta e il calcolo delle teste di serie?"]),
    _fu("interessante, e c'è un modo per allenarsi?", _G, 1, ["Qual è il linguaggio dei fiori e qual è il significato storico di regalare una rosa gialla?"]),

    _fu("ok, e in pratica come lo scrivo?", _C, 2, ["Come si gestisce lo stato in un'app Flutter usando Riverpod o il pattern BLoC?"]),
    _fu("capito il senso, ma quanto pesa sulle prestazioni?", _C, 2, ["Come si ottimizza un'app Android nativa per ridurre il consumo di batteria in background?"]),
    _fu("ah ok, e se il file è molto grande?", _C, 2, ["Scrivi uno script Node.js per elaborare stream di dati binari e salvarli su file."]),
    _fu("giusto, e come lo testo prima di andare in produzione?", _C, 2, ["Configura un reverse proxy con Nginx per gestire il traffico SSL/TLS."]),
    _fu("interessante, ma cambia qualcosa su Windows?", _C, 1, ["Come faccio un rebase interattivo dei miei commit in un repository Git?"]),
    _fu("ok, e quanto è sicuro davvero?", _C, 2, ["Scrivi il codice per generare un hash sicuro di una password usando bcrypt o argon2."]),

    _fu("ok, ma vale anche fuori da quell'intervallo?", _M, 2, ["Trova gli asintoti obliqui, orizzontali e verticali di questa funzione iperbolica."]),
    _fu("capito, e cambia qualcosa se il dominio è discreto?", _M, 2, ["Enuncia e spiega il teorema del limite centrale e la legge dei grandi numeri."]),
    _fu("giusto, e questo vale in ogni dimensione?", _M, 2, ["Trova i massimi e minimi vincolati della funzione utilizzando il metodo dei moltiplicatori di Lagrange."]),
    _fu("ah ok, e se i coefficienti non sono costanti?", _M, 2, ["Risolvi l'equazione differenziale lineare del secondo ordine a coefficienti costanti."]),
    _fu("interessante, ma è sempre univoca la soluzione?", _M, 2, ["Risolvi il problema di Cauchy determinando la soluzione particolare dell'equazione."]),
    _fu("ok, e come cambia se la matrice non è quadrata?", _M, 2, ["Calcola il prodotto matriciale tra matrici non quadrate e verificane la compatibilità dimensionale."]),

    _fu("capito, ma vale anche per i contratti già firmati?", _R, 2, ["Cosa prevede la normativa civile per l'acquisto della proprietà tramite usucapione?"]),
    _fu("ok, e se una delle parti non risponde più?", _R, 2, ["Spiega il funzionamento della caparra confirmatoria e della clausola penale nei contratti."]),
    _fu("giusto, e cambia qualcosa se siamo parenti?", _R, 2, ["Come funziona l'azione di rivendicazione a tutela della proprietà privata?"]),
    _fu("ah ok, e i tempi tecnici quanto sono lunghi di solito?", _R, 2, ["Quali sono le fasi del procedimento amministrativo e l'obbligo di motivazione."]),
    _fu("interessante, ma serve sempre un avvocato per questo?", _R, 1, ["Come si presenta un ricorso al giudice di pace contro una sanzione amministrativa?"]),
    _fu("ok, e se il danno è solo economico e non fisico?", _R, 2, ["Quali sono le differenze tra responsabilità contrattuale ed extracontrattuale (art. 2043 c.c.)?"]),

    # ── T2-C: Negativi ellittici SENZA history (A-M5: falso positivo a vuoto) ──
    # Fraseggio che "suona" da continuazione (rimandi impliciti: "come prima",
    # "anche qui", "ripeti", "allo stesso modo") ma senza alcuna history
    # allegata: deve restare is_followup=False. Insegna alla rete che l'assenza
    # di history è dirimente, non solo un indizio lessicale di superficie.
    _r("Applica lo stesso ragionamento visto per la convergenza puntuale al caso della convergenza uniforme.", _M, 2),
    _r("Ripeti il calcolo del determinante ma questa volta con il metodo dei cofattori.", _M, 2),
    _r("Rifai la dimostrazione di prima usando però il principio di induzione forte.", _M, 2),
    _r("Come nel caso precedente, calcola anche qui la varianza della distribuzione.", _M, 2),
    _r("Studia allo stesso modo la convergenza di questa nuova serie numerica.", _M, 2),
    _r("Anche in questo caso, verifica se la matrice risulta diagonalizzabile.", _M, 2),
    _r("Procedi come sempre e trova gli autovalori di questa matrice 4x4.", _M, 1),
    _r("Ancora una volta, applica il teorema di Bayes a questo nuovo problema.", _M, 2),
    _r("Ripeti il procedimento standard per risolvere questo sistema lineare.", _M, 2),
    _r("Come al solito, calcola prima la derivata e poi studia il segno.", _M, 1),
    _r("Fai la stessa cosa di sempre ma questa volta in linguaggio Rust.", _C, 2),
    _r("Applica lo stesso pattern visto di solito a questo nuovo problema.", _C, 2),
    _r("Ripeti l'implementazione standard, però gestendo anche gli errori.", _C, 2),
    _r("Come al solito, ottimizza il codice riducendo la complessità temporale.", _C, 2),
    _r("Applica lo stesso ragionamento visto di solito anche a questo contratto.", _R, 2),
    _r("Come nei casi analoghi, verifica se sussiste responsabilità civile.", _R, 2),
    _r("Ripeti l'analisi standard su questo nuovo caso di licenziamento.", _R, 2),
    _r("Fammi come sempre un riassunto breve di questo argomento.", _G, 1),
    _r("Come al solito, dammi qualche consiglio pratico su questo tema.", _G, 1),
    _r("Ripeti la stessa spiegazione ma con parole più semplici.", _G, 1),

    # ── T2-B (rinforzo) — ulteriori marcatori brevi per portare il rapporto
    # is_followup train nel range 12-15% richiesto dal piano di lavoro ──
    _fu("ok, e come si distingue dagli altri casi simili?", _G, 1, ["Come è cambiata la televisione con l'avvento delle piattaforme di streaming come Netflix?"]),
    _fu("interessante, e da quanto tempo si fa così?", _G, 1, ["Quali sono le principali disparità economiche nel mondo e le loro radici storiche?"]),
    _fu("ah capito, e nella pratica cosa cambia per me?", _G, 1, ["Quali sono i principi di una dieta equilibrata per chi pratica sport a livello amatoriale?"]),
    _fu("giusto, e questo vale anche per i principianti?", _G, 1, ["Quali sono le tecniche migliori per imparare a suonare la chitarra classica da autodidatta?"]),
    _fu("ok, e quanto spesso conviene rifarlo?", _G, 1, ["Come si coltivano le piante da appartamento e quanto spesso vanno annaffiate?"]),
    _fu("davvero, e questo si può notare a occhio nudo?", _G, 1, ["Come si formano i terremoti e i vulcani secondo la teoria della tettonica a placche?"]),
    _fu("interessante, e in che occasioni conviene farlo?", _G, 1, ["Come ci si comporta a tavola in Giappone e quali sono le usanze del galateo locale?"]),
    _fu("ah ok, e serve esperienza per farlo bene?", _G, 1, ["Come si organizza un allenamento funzionale a corpo libero per aumentare la forza?"]),
    _fu("giusto, e come si spiega ai bambini?", _G, 1, ["Spiega il paradosso del gatto di Schrödinger e le sue implicazioni base per capire i quanti."]),
    _fu("ok, ma quanto è affidabile questo metodo?", _G, 1, ["Come si legge un bilancio aziendale di base e qual è la differenza tra stato patrimoniale e conto economico?"]),
    _fu("interessante, e cosa lo rende diverso dagli altri?", _G, 1, ["Quali sono le differenze tra lo yoga Hatha e lo yoga Vinyasa?"]),
    _fu("ah, e questo succede anche in altre culture?", _G, 1, ["Come si addestra efficacemente un cucciolo di cane nei primi mesi di vita?"]),
    _fu("ok, e c'è un modo per evitarlo del tutto?", _G, 1, ["Come influisce il cambiamento climatico sugli ecosistemi globali e sull'economia moderna?"]),
    _fu("giusto, e quanto incide realmente sul risultato finale?", _G, 1, ["Qual è il processo decisionale migliore per scegliere lo stile e l'arredamento di un piccolo soggiorno?"]),
    _fu("davvero interessante, e come si è arrivati a scoprirlo?", _G, 1, ["Cosa sono gli esopianeti e quali sono i metodi attuali per scoprirli nello spazio?"]),
    _fu("ok, e conviene farlo la mattina o la sera?", _G, 1, ["Dammi una routine di esercizi di stretching da fare a casa per migliorare la flessibilità."]),
    _fu("interessante, e quanto è comune come situazione?", _G, 1, ["Quali sono le dinamiche psicologiche e i fattori chiave per mantenere viva l'intesa in un matrimonio?"]),
    _fu("ah capito, e cosa succede se non lo si fa?", _G, 1, ["Quali sono i benefici della meditazione mindfulness per la salute mentale a lungo termine?"]),
    _fu("giusto, e da cosa dipende principalmente?", _G, 1, ["Quali sono le principali catene montuose del mondo, come si sono formate geologicamente e come influenzano il clima locale?"]),
    _fu("ok, e come faccio a sapere se lo sto facendo bene?", _G, 1, ["In cosa consiste il protocollo di allenamento Tabata e come si implementa a corpo libero?"]),
    _fu("interessante, ma cambia qualcosa se il progetto è grande?", _C, 2, ["Come si gestisce lo stato in un'app Flutter usando Riverpod o il pattern BLoC?"]),
    _fu("ok, e vale anche per le versioni più vecchie del linguaggio?", _C, 2, ["Come si ottimizza un'app Android nativa per ridurre il consumo di batteria in background?"]),
    _fu("giusto, e in un ambiente con poca RAM cosa cambia?", _C, 2, ["Configura un reverse proxy con Nginx per gestire il traffico SSL/TLS."]),
    _fu("ah ok, e come faccio a verificarlo prima del deploy?", _C, 2, ["Come faccio un rebase interattivo dei miei commit in un repository Git?"]),
    _fu("ok, ma cambia qualcosa se i dati sono in virgola mobile?", _M, 2, ["Calcola il prodotto matriciale tra matrici non quadrate e verificane la compatibilità dimensionale."]),
    _fu("giusto, e nel caso limite cosa succede esattamente?", _M, 2, ["Trova gli asintoti obliqui, orizzontali e verticali di questa funzione iperbolica."]),
    _fu("ah ok, e serve verificarlo anche numericamente?", _M, 2, ["Risolvi l'equazione differenziale lineare del secondo ordine a coefficienti costanti."]),
    _fu("interessante, e cosa cambia se il campione è piccolo?", _M, 2, ["Enuncia e spiega il teorema del limite centrale e la legge dei grandi numeri."]),
    _fu("ok, e questa procedura vale anche in appello?", _R, 2, ["Come funziona il ricorso gerarchico e il ricorso al TAR nel diritto amministrativo?"]),
    _fu("giusto, e chi paga le spese in questi casi?", _R, 2, ["Quali sono le fasi del procedimento amministrativo e l'obbligo di motivazione."]),
    _fu("ah ok, e serve comunque un atto scritto?", _R, 2, ["Come si presenta un ricorso al giudice di pace contro una sanzione amministrativa?"]),
    _fu("interessante, e vale anche per i contratti verbali?", _R, 2, ["Cosa prevede la normativa civile per l'acquisto della proprietà tramite usucapione?"]),

]

# ── False-Pipeline Hard Negatives (ex-FIX A-C1, ampliato) ────────────────────
# [FIX A-C1 rev.2] "calcola/implementa X in Python" su operazioni CS
# elementari con vocabolario numerico/matematico (fattoriale, primo, MCD,
# permutazioni, ecc.): il rischio è l'attivazione della testa MATH per
# associazione lessicale pura, che porta il classificatore a due stadi a
# promuovere erroneamente a pipeline math->coding. Isolato in una lista
# dedicata (fuori da MANUAL_RECORDS) per ricevere un rinforzo di
# augmentation ESPLICITO in FASE 2ter — vedi TARGET_FALSE_PIPELINE_NEG.
# Ogni riga inizia con un verbo imperativo presente in SYNONYMS
# (scrivi/calcola/implementa), condizione necessaria perché
# augment_hard_negatives_synonyms() possa generare varianti.
FALSE_PIPELINE_HARD_NEGATIVES = [
    _r("Scrivi una funzione Python che calcola il fattoriale di un numero in modo ricorsivo.", _C, 1),
    _r("Calcola la somma dei numeri di Fibonacci fino all'ennesimo termine in Python.", _C, 1),
    _r("Scrivi una funzione Python che calcola se un numero è primo.", _C, 1),
    _r("Calcola il massimo comun divisore tra due numeri in Python.", _C, 1),
    _r("Scrivi il codice Python che calcola la somma delle cifre di un numero.", _C, 1),
    _r("Calcola se una stringa è palindroma con una funzione Python.", _C, 1),
    _r("Scrivi una funzione Python che calcola il massimo e il minimo di una lista.", _C, 1),
    _r("Calcola la somma dei numeri pari in una lista usando Python.", _C, 1),
    _r("Scrivi il codice per calcolare quante vocali ci sono in una stringa Python.", _C, 1),
    _r("Calcola il numero di occorrenze di un elemento in una lista Python.", _C, 1),
    _r("Scrivi una funzione Python che verifica se un numero è pari o dispari.", _C, 1),
    _r("Calcola la mediana di una lista di numeri usando Python.", _C, 1),
    _r("Scrivi il codice Python per calcolare la potenza n-esima di un numero senza usare l'operatore **.", _C, 1),
    _r("Implementa in Python un controllo che verifichi se un numero è un quadrato perfetto.", _C, 1),
    _r("Scrivi una funzione Python che calcola la somma dei divisori propri di un numero.", _C, 1),
    _r("Calcola il numero di permutazioni possibili di una stringa usando Python.", _C, 2),
    _r("Implementa in Python la Torre di Hanoi con ricorsione.", _C, 2),
    _r("Scrivi una funzione Python che genera i numeri triangolari fino a un limite dato.", _C, 1),
    _r("Calcola la radice quadrata intera di un numero senza usare la libreria math in Python.", _C, 1),
    _r("Scrivi il codice Python che verifica la validità di una carta di credito con l'algoritmo di Luhn.", _C, 2),
    _r("Implementa in Python una funzione che conta le combinazioni possibili di k elementi presi da n.", _C, 2),
    _r("Scrivi una funzione Python che ordina una lista di numeri in ordine decrescente senza usare sorted().", _C, 1),
    _r("Calcola il fattoriale di un numero in Python usando un ciclo invece della ricorsione.", _C, 1),
    _r("Scrivi il codice Python che trova il numero primo successivo a un intero dato.", _C, 1),
    _r("Implementa in Python il calcolo iterativo della sequenza di Fibonacci fino all'n-esimo termine.", _C, 1),
]

# ── Keyword-Trap Negatives ────────────────────────────────────────────────────
# [FIX keyword-trap — wrong_query_TESTING.md rev.2] Token isolati fortemente
# associati a un dominio tecnico nel corpus (VAR→rights->math/"Value at
# Risk", lancio→coding/math/"lancio moneta o dadi", equazione/debug/
# informatica/algoritmo/ottimizza/formula→coding o math) usati qui in
# contesto general/rights genuino, non tecnico. Zero copertura precedente
# di questi token fuori dal loro dominio "nativo" — la rete non ha mai
# visto un controesempio. Fraseggio discorsivo/interrogativo (NESSUN verbo
# imperativo): augment_query() non trova match in SYNONYMS per queste frasi
# (stesso fenomeno già noto per general+math/general+rights, M1 WARNING),
# quindi il rinforzo in FASE 2ter usa SOLO augment_hard_negatives_noise()
# (wrapping narrativo, non dipende da SYNONYMS).
KEYWORD_TRAP_NEGATIVES = [
    # VAR (calcistico) — vs "VAR (Value at Risk)" in rights->math
    _r("Il VAR è stato introdotto nel calcio per ridurre gli errori arbitrali, ma continua a far discutere i tifosi.", _G, 1),
    _r("Quanto tempo impiega mediamente il VAR a controllare un episodio dubbio durante una partita di Serie A?", _G, 1),
    _r("Secondo te il VAR ha reso il calcio più giusto o ha solo rallentato troppo il gioco?", _G, 1),
    # lancio — vs "lancio di una moneta/dadi" in coding/math (probabilità)
    _r("Qual è il record mondiale nel lancio del giavellotto e chi lo detiene attualmente?", _G, 1),
    _r("Mentre giocavamo a freccette in giardino un lancio è finito sulla macchina del vicino, chi deve pagare i danni?", _R, 2),
    _r("Durante un allenamento di atletica il lancio del peso di un compagno mi ha colpito per errore, posso fare causa?", _R, 2),
    _r("Quali sono le tecniche di base per migliorare la precisione nel lancio a canestro nella pallacanestro?", _G, 1),
    # equazione figurativa — vs uso matematico letterale
    _r("Qual è l'equazione giusta tra vita privata e carriera per essere davvero felici?", _G, 1),
    _r("Gli chef dicono che la cucina perfetta è un'equazione tra tecnica, ingredienti freschi e un pizzico di fantasia.", _G, 1),
    _r("C'è un'equazione emotiva dietro ogni grande amicizia, fatta di fiducia e tempo condiviso?", _G, 2),
    # debug / informatica figurativi — vs uso tecnico letterale
    _r("Ho passato la serata a fare debug della mia giornata storta, cercando di capire dove avevo sbagliato con i colleghi.", _G, 1),
    _r("Non ho mai studiato informatica, ma stasera vorrei solo rilassarmi guardando una serie tv leggera.", _G, 1),
    _r("Mio nonno lavorava in un'azienda di informatica negli anni '80, mi racconti come si viveva la vita d'ufficio in quell'epoca?", _G, 2),
    _r("A volte serve fare debug dei propri pensieri prima di dormire per non portarsi dietro lo stress della giornata.", _G, 1),
    # algoritmo / ottimizzare figurativi
    _r("Qual è l'algoritmo segreto per convincere un bambino a mangiare le verdure senza fare i capricci?", _G, 1),
    _r("Come posso ottimizzare le mie serate per leggere di più senza rinunciare al sonno?", _G, 1),
    _r("Esiste un algoritmo infallibile per scegliere il regalo di compleanno perfetto per un amico?", _G, 1),
    _r("Vorrei ottimizzare il mio armadio per avere più spazio senza buttare via i vestiti a cui tengo.", _G, 1),
    # formula figurativa
    _r("Qual è la formula segreta per un matrimonio felice e duraturo secondo gli psicologi?", _G, 1),
    _r("C'è una formula magica per superare la timidezza durante un colloquio di lavoro?", _G, 1),

    # diritto/scienza/economia in contesto divulgativo — [FIX N-CONF/G-NOISE4]
    _r("Studiando la storia della pittura fiamminga mi sono imbattuto nel concetto di equazione compositiva tra luce e ombra, cosa intendevano gli artisti rinascimentali con questo termine?", _G, 2),
    _r("Sto leggendo un saggio di divulgazione che parla spesso di reti neurali, gradiente e backpropagation, argomenti affascinanti ma ostici: mi consigli altri saggi di divulgazione scientifica scritti in modo semplice?", _G, 2),
    _r("Il professore di microeconomia ha riempito la lavagna di formule e integrali per spiegare l'equilibrio di mercato, ma io vorrei solo capire il concetto base senza tutta quella matematica, come funziona in parole semplici?", _G, 2),
    _r("Frequento un corso serale di storia del diritto per pura passione, senza alcun fine professionale, e mi affascina scoprire come nacquero le prime codificazioni: mi racconti brevemente le origini del diritto romano?", _G, 2),
]

# ── Difficulty Labels (manuale) ──────────────────────────────────────────────
# [DIFFICULTY MANUALE] Sostituisce l'euristica estimate_difficulty() rimossa.
# [CFG-2 FIX] DIFFICULTY_LABELS_PATH importato da classifier_config.py
# (era definito qui in modo indipendente).


def _load_difficulty_labels() -> dict:
    if not DIFFICULTY_LABELS_PATH.exists():
        raise FileNotFoundError(
            f"File etichette difficoltà non trovato: {DIFFICULTY_LABELS_PATH}\n"
            f"Vedi report_difficulty_manual.md §4.1 per lo schema atteso "
            f"({{'<query esatta>': 1|2|3|null}})."
        )
    with open(DIFFICULTY_LABELS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


DIFFICULTY_LABELS: dict = _load_difficulty_labels()


def get_difficulty_label(query: str) -> int:
    """
    Lookup fail-fast della difficoltà manuale (1/2/3) per una query ESATTA
    (verbatim, come compare in INTENT_SENTENCES/BRIDGE_SENTENCES — 0
    duplicati verificati, chiave univoca garantita).

    Solleva ValueError se:
      - la query non è presente come chiave nel JSON (drift tra
        db_query.py e difficulty_labels.json — es. una frase modificata
        dopo la generazione dello skeleton);
      - il valore è ancora null (non etichettata);
      - il valore non è un intero in {1, 2, 3}.

    Stesso pattern fail-fast già in uso per is_followup in
    precompute_embeddings.py::load_dataset(): un dataset con etichette
    mancanti non deve MAI essere generato silenziosamente.
    """
    value = DIFFICULTY_LABELS.get(query)
    if value not in (1, 2, 3):
        raise ValueError(
            f"Difficulty mancante o non valida per la query: {query!r} "
            f"(valore letto: {value!r}). Etichettarla in "
            f"'{DIFFICULTY_LABELS_PATH.name}' con un intero in {{1,2,3}} "
            f"prima di rigenerare il dataset."
        )
    return value


# ── Helper functions ───────────────────────────────────────────────────────────

def get_class_key(record: dict) -> str:
    if record['is_pipeline'] and record['pipeline_type']:
        return record['pipeline_type']
    active = [d for d, v in record['domain_labels'].items() if v == 1]
    return active[0] if len(active) == 1 else '+'.join(sorted(active))

def augment_query(query: str) -> str:
    words = query.split()
    for i, word in enumerate(words):
        clean = word.lower().rstrip('.,!?;:')
        if clean in SYNONYMS:
            synonym = random.choice(SYNONYMS[clean])
            if word[0].isupper():
                synonym = synonym[0].upper() + synonym[1:]
            suffix = word[len(clean):]
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
            records.append(_r(
                query=s, 
                labels=labels, 
                diff=get_difficulty_label(s),
                is_followup=False # Garantiamo che le frasi base abbiano flag a False
            ))
    return records

def build_bridge_records() -> list:
    """Converte BRIDGE_SENTENCES in record JSONL multi-label."""
    records = []
    for (d1, d2), sentences in BRIDGE_SENTENCES.items():
        labels = {"coding": 0, "math": 0, "rights": 0, "general": 0}
        labels[d1] = 1
        labels[d2] = 1
        pipeline_type, is_pipe = BRIDGE_MAP.get((d1, d2), (None, False))
        for s in sentences:
            records.append(_r(
                query=s, 
                labels=labels, 
                diff=get_difficulty_label(s),
                is_pipe=is_pipe,
                pipe_type=pipeline_type,
                is_followup=False # Garantiamo flag a False
            ))
    return records

def augment_class(group: list, target: int) -> list:
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
            new_r = {k: (dict(v) if isinstance(v, dict) else v) for k, v in r.items()}
            new_r['query'] = new_q
            # is_followup resta invariato (solitamente False nei dati base)
            extra.append(new_r)
    return extra

def dedup_records(records: list) -> list:
    """
    [A2 FIX] Rete di sicurezza strutturale: rimuove record con query
    duplicata (normalizzata: strip + lowercase), tenendo il primo
    occorrente. Va chiamata PRIMA di stratified_split() — un duplicato non
    rimosso può finire per metà in train e per metà in val/test dopo lo
    shuffle interno allo split, reintroducendo esattamente il tipo di data
    leakage che il fix "split prima di augmentation" (vedi main()) doveva
    eliminare, ma a monte, nei dati sorgente stessi (causa concreta: la
    frase Prim/Kruskal duplicata in db_query.py — già rimossa alla fonte,
    ma questa funzione previene ricadute future in INTENT_SENTENCES,
    BRIDGE_SENTENCES o MANUAL_RECORDS).
    """
    seen = set()
    deduped = []
    duplicates_found = []
    for r in records:
        norm = (r['query'].strip().lower(), tuple(h.strip().lower() for h in r.get('history', [])))
        if norm in seen:
            duplicates_found.append(r['query'])
            continue
        seen.add(norm)
        deduped.append(r)

    if duplicates_found:
        print(f"\n⚠️  [A2 WARNING] {len(duplicates_found)} query duplicate rimosse dal dataset:")
        for q in duplicates_found:
            print(f"     - {q[:70]}{'...' if len(q) > 70 else ''}")

    return deduped


# [D2-B FIX — piano_lavoro_espansione_dataset.md §3] Split deterministico.
# random.shuffle(group) rimescolava l'INTERO gruppo ad ogni rebuild: bastava
# aggiungere anche solo pochi record altrove nel file (nuovo seed, nuovo
# MANUAL_RECORDS) per cambiare l'ordine di iterazione dei dict e quindi il
# punto di partenza dello shuffle, spostando migliaia di record preesistenti
# tra train/val/test in modo silenzioso — rendendo qualunque confronto tra
# due run di step4_evaluation.py non affidabile (vedi caso T2: nessun modo
# di distinguere "regressione causata dal contenuto nuovo" da "record finito
# per caso in un altro split"). hashlib.sha256 (non il built-in hash(), che
# è salato per processo da PYTHONHASHSEED e quindi NON deterministico tra
# run diversi) ordina i record in modo stabile e puramente content-based:
# la posizione relativa di un record già esistente non cambia quando se ne
# aggiungono altri altrove nello stesso gruppo, quindi lo split resta stabile
# tra rebuild successivi (piccoli spostamenti restano possibili solo per i
# pochissimi record vicini al confine 70/85%, effetto inevitabile di
# qualunque split percentuale, non un rimescolamento globale).
def _stable_sort_key(record: dict) -> str:
    payload = record['query'] + '|' + '|'.join(record.get('history') or [])
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def stratified_split(records: list) -> list:
    groups = defaultdict(list)
    for r in records:
        groups[get_class_key(r)].append(r)

    result = []
    empty_splits = []  # [M3 FIX] classi con split val/test vuoto (n troppo piccolo)
    for key, group in groups.items():
        group.sort(key=_stable_sort_key)  # [D2-B FIX] era random.shuffle(group)
        n  = len(group)
        t1 = max(1, int(n * 0.70))
        t2 = max(t1 + 1, int(n * 0.85))
        train_slice, val_slice, test_slice = group[:t1], group[t1:t2], group[t2:]
        for r in train_slice: r['split'] = 'train'
        for r in val_slice:   r['split'] = 'val'
        for r in test_slice:  r['split'] = 'test'
        if not val_slice or not test_slice:
            empty_splits.append((key, n, len(train_slice), len(val_slice), len(test_slice)))
        result.extend(group)

    if empty_splits:
        print(f"\n⚠️  [M3 WARNING] Classi con split val e/o test VUOTO (n troppo piccolo "
              f"per lo split 70/15/15 — punto cieco nella valutazione per-classe):")
        for key, n, tr, va, te in empty_splits:
            print(f"     {key:25s}: n={n:3d} → train={tr} val={va} test={te}")

    return result


# ── [NOISE-AUG] Query Noise Augmentation — Opzione A ─────────────────────────
# (report_query_noise_augmentation.md §4)
#
# Contrasta il bias di diluizione per mean-pooling: MiniLM fa la media
# aritmetica di tutti i token embeddings (pesata solo da attention mask, mai
# da rilevanza semantica). Frasi tecniche terse "annegate" in testo di
# contorno narrativo/motivazionale/di specifica-stile vengono spinte verso
# GENERAL con alta confidence, perché la rete ha imparato la scorciatoia
# "registro lungo/discorsivo -> GENERAL" (GENERAL nel dataset contiene
# nativamente molte frasi lunghe/narrative — vedi §2.3 del report).
#
# Stessa filosofia di augment_query()/augment_class() ma a livello di frase
# intera: il record augmentato eredita TUTTI i campi dal sorgente (§4.5),
# solo 'query' viene sovrascritta — zero nuovo labeling manuale.
#
# Decisioni prese sui parametri aperti in §4.8 del report:
#   - Applicata SOLO a intent+bridge (non a MANUAL_RECORDS: follow-up/
#     domain-switch hanno semantica legata a brevità/history che il
#     wrapping romperebbe).
#   - Selezione per class-key (get_class_key), stessa granularità di
#     augment_class(), con ratio fisso NOISE_INJECTION_RATIO — non un
#     target assoluto come TARGET_MONO/TARGET_PIPE, perché il rumore deve
#     scalare proporzionalmente alla popolazione già esistente di ogni
#     classe, non colmare un minimo.
#   - 2 varianti per record selezionato (NOISE_VARIANTS_PER_SEED), a
#     copertura di posizione/sapore diversi senza esplosione combinatoria.

NOISE_INJECTION_RATIO   = 0.35   # frazione selezionata per ogni class-key (get_class_key)
NOISE_VARIANTS_PER_SEED = 2      # varianti generate per ogni record selezionato

# Pool "framing narrativo": topic-agnostic per costruzione — nessuna voce
# menziona coding/math/rights/general, riutilizzabile su qualunque frase base
# di qualunque dominio (requisito §4.3.1: copertura simmetrica sui 4 domini,
# mai un "sapore" di rumore legato a un dominio specifico). Sapori coperti:
# storico/culturale, filosofico, curiosità personale, utilità/motivazionale.
# Le entry terminano con ": " per agganciarsi alla frase base (minuscolizzata).
NOISE_FRAME_PREFIXES = [
    "Ci penso spesso ultimamente, quindi ti chiedo: ",
    "Una delle cose che trovo più affascinanti nella storia umana è come si sia arrivati a capire certe cose, quindi vorrei sapere: ",
    "Ne parlavo proprio ieri con un amico di quanto certe scoperte abbiano un che di filosofico, e mi chiedevo: ",
    "Sono sempre stato incuriosito da come nel corso dei secoli si siano affrontati problemi come questo, quindi: ",
    "Al di là dell'utilità pratica, trovo ci sia qualcosa di profondamente umano dietro domande come questa, quindi: ",
    "Mi capita spesso di riflettere su come si sia evoluto il sapere nel tempo, e mi chiedo: ",
    "Premesso che non è urgente, ma mi piacerebbe capire meglio una cosa che mi frulla in testa da un po': ",
    "Diciamo che è più curiosità personale che necessità reale, ma vorrei approfondire: ",
    "Ho letto qualcosa che parlava di come certi argomenti abbiano cambiato il corso della storia, quindi mi chiedo: ",
    "Per motivi che non sto qui a spiegare per intero, mi servirebbe capire bene una cosa: ",
]

# Continuazioni a virgola (stessa frase, non frase a sé): riproducono
# fedelmente il pattern del caso reale osservato in §1 del report
# ("risolvi le equazioni di Navier stokes, una delle più importanti
# scoperte fatte nella storia dell'umanità..."). Nel codice viene aggiunto
# un punto finale.
NOISE_FRAME_SUFFIXES = [
    ", una delle scoperte più importanti mai fatte nella storia dell'umanità, con un che di filosofico nel suo significato ancora oggi",
    ", argomento che trovo affascinante dal punto di vista storico e culturale, al di là della pura utilità pratica",
    ", tema a cui penso spesso perché ha quasi un che di filosofico",
    ", cosa che secondo me racconta molto di come ragiona la mente umana quando affronta problemi complessi",
    ", questione che mi interessa più per curiosità personale che per reale necessità",
    ", tema su cui vorrei tornare perché lo trovo rilevante anche nella vita di tutti i giorni",
    ", cosa che può sembrare strana da chiedere ma per me ha un valore che va oltre il puro tecnicismo",
    ", argomento che secondo me meriterebbe più attenzione di quella che gli diamo di solito",
]

# Coppie (prefisso, suffisso) per il wrapping "spezzato attorno" al nucleo
# tecnico (requisito §4.3.5: il rumore va variato in posizione, non solo
# appeso in coda, altrimenti si copre solo il caso opposto a quello per cui
# l'Opzione B è stata scartata in §3.2).
NOISE_WRAP_PAIRS = [
    ("Da tempo mi affascina come nel corso della storia si sia arrivati a soluzioni per problemi come questo, quindi vorrei capire bene: ",
     ", perché credo che dietro ci sia qualcosa di più profondo della semplice utilità pratica"),
    ("Non so se è la domanda giusta da fare qui, ma da un po' mi frulla in testa e vorrei togliermi il dubbio: ",
     ", diciamo che è più curiosità che reale necessità immediata"),
    ("Parto un po' alla lontana, scusami, ma trovo ci sia un legame interessante tra come affrontiamo certe domande e la nostra cultura, quindi: ",
     ", argomento su cui rifletto spesso anche fuori da un contesto puramente tecnico"),
    ("Premessa lunga, portami pazienza: sono sempre stato convinto che capire certe cose ci renda persone migliori, quindi ",
     ", cosa che per me ha un peso che va oltre la semplice risposta tecnica"),
]

# Pool "specifica di stile risposta": separato dal pool narrativo,
# componibile insieme ad esso (requisito §4.4). Frasi a sé stanti
# (spazio + maiuscola iniziale), appese dopo la punteggiatura originale
# della frase base.
NOISE_STYLE_SUFFIXES = [
    " Spiegamelo in modo semplice, come se lo spiegassi a un bambino.",
    " Rispondimi in modo super sintetico, senza fronzoli.",
    " Se puoi, aggiungi anche un po' di contesto in più, mi piace capire il quadro generale.",
    " Cerca di non essere troppo tecnico nella risposta, per favore.",
    " Vorrei una risposta bella dettagliata, con tutti i passaggi spiegati per bene.",
    " Fammi un riassunto breve, tanto per farmi un'idea.",
    " Scrivimi la risposta come se dovessi spiegarla a qualcuno alle prime armi.",
]


def _lowered(text: str) -> str:
    return text[0].lower() + text[1:] if text else text


def _stripped(text: str) -> str:
    return text.rstrip('?.! ')


def _compose_noise_variant(base_query: str, rng: random.Random) -> str:
    """
    Compone una singola variante rumorosa pescando a random posizione
    (prefisso / suffisso-continuazione / wrap / suffisso ad alto rumore /
    solo specifica di stile) e sapore dai pool topic-agnostic sopra.
    'suffix_heavy' combina framing narrativo + stile risposta per coprire
    varianti ad alto rapporto rumore/segnale (~80%+, requisito §4.3.6),
    replicando il caso reale osservato in §1 del report.
    """
    mode = rng.choice(['prefix', 'suffix', 'wrap', 'suffix_heavy', 'style'])

    if mode == 'prefix':
        frame = rng.choice(NOISE_FRAME_PREFIXES)
        return f"{frame}{_lowered(base_query)}"

    if mode == 'wrap':
        pre, post = rng.choice(NOISE_WRAP_PAIRS)
        core = _lowered(_stripped(base_query))
        return f"{pre}{core}{post}."

    if mode == 'suffix_heavy':
        core  = _stripped(base_query)
        frame = rng.choice(NOISE_FRAME_SUFFIXES)
        style = rng.choice(NOISE_STYLE_SUFFIXES)
        return f"{core}{frame}.{style}"

    if mode == 'style':
        style = rng.choice(NOISE_STYLE_SUFFIXES)
        return f"{base_query}{style}"

    # suffix (continuazione a virgola, pattern del caso reale osservato)
    core  = _stripped(base_query)
    frame = rng.choice(NOISE_FRAME_SUFFIXES)
    return f"{core}{frame}."


def augment_noise(records: list, ratio: float = NOISE_INJECTION_RATIO,
                   variants_per_seed: int = NOISE_VARIANTS_PER_SEED) -> list:
    """
    Genera varianti "rumorose" di record già etichettati, per insegnare
    alla rete l'invarianza al registro/lunghezza della query (vedi §1-2 del
    report: mean pooling di MiniLM diluisce il nucleo tecnico
    proporzionalmente al volume di testo di contorno).

    Va chiamata SEMPRE dopo stratified_split() sui record passati: ogni
    variante eredita `split` dal sorgente — se un sorgente non ha ancora
    `split` assegnato (es. rimosso da dedup_records() prima dello split)
    va escluso dal chiamante PRIMA di passarlo qui (vedi filtro in main()),
    altrimenti si reintroduce esattamente il leakage train/test già
    risolto per l'augmentation a sinonimi, vedi [FIX LEAKAGE] in main().

    Selezione: `ratio` di record per ogni class-key (get_class_key) — stessa
    granularità di augment_class(), a garanzia di copertura simmetrica sui
    4 domini/3 pipeline/classi bridge non-pipeline (requisito §4.3.1). Ogni
    record selezionato genera `variants_per_seed` varianti indipendenti
    (posizione e sapore pescati a random) per coprire diversità di
    posizione senza esplosione combinatoria (requisito §4.3.5).

    Rng dedicato e deterministico (seed fisso, indipendente dallo stato
    globale di `random` già usato da augment_class()/stratified_split()):
    single responsibility, nessun effetto collaterale sull'ordine di
    generazione delle altre augmentation.
    """
    by_class = defaultdict(list)
    for r in records:
        by_class[get_class_key(r)].append(r)

    rng = random.Random(1337)
    extra = []
    seen_queries = {r['query'] for r in records}

    for group in by_class.values():
        if not group:
            continue
        n_select = max(1, round(len(group) * ratio))
        selected = rng.sample(group, min(n_select, len(group)))

        for src in selected:
            for _ in range(variants_per_seed):
                new_q = _compose_noise_variant(src['query'], rng)
                if new_q in seen_queries:
                    continue
                seen_queries.add(new_q)
                new_r = {k: (dict(v) if isinstance(v, dict) else v) for k, v in src.items()}
                new_r['query'] = new_q
                # Tutti gli altri campi (domain_labels, is_pipeline,
                # pipeline_type, difficulty, is_followup, split) ereditati
                # invariati dal sorgente (§4.5 del report).
                extra.append(new_r)

    return extra


def augment_hard_negatives_synonyms(records: list, target: int, label: str) -> list:
    """
    [HARD-NEG FIX] Rinforzo via augment_class()/SYNONYMS per sottoinsiemi di
    record "difficili" che il loop generico per class-key in main() non
    raggiungerebbe mai (dominio mono già saturo prima che l'augmentation
    parta). Richiede un verbo imperativo matchabile in SYNONYMS come prima
    parola utile della query — adatta a FALSE_PIPELINE_HARD_NEGATIVES.
    """
    for r in records:
        if r.get('split') is None:
            raise ValueError(
                f"[FASE 2ter] Record senza split assegnato (probabile duplicato "
                f"scartato da dedup_records prima dello split): {r['query']!r}"
            )
    
    aug = augment_class(records, target)
    total = len(records) + len(aug)
    print(f"  {label:28s}: base={len(records):3d} +{len(aug):3d} augmentati (tot={total}/{target})")
    return aug


def augment_hard_negatives_noise(records: list, variants_per_record: int,
                                  label: str, rng_seed: int) -> list:
    """
    [HARD-NEG FIX] Rinforzo via wrapping narrativo (riusa
    _compose_noise_variant(), stesso meccanismo di augment_noise()) per
    sottoinsiemi con fraseggio discorsivo/interrogativo privo di verbi
    imperativi, dove augment_query() non trova mai un match in SYNONYMS
    (stesso fenomeno già osservato per general+math/general+rights, vedi
    M1 WARNING). A differenza di augment_noise() non è vincolata a
    intent+bridge: qui il wrapping narrativo È la robustezza da insegnare.
    """
    for r in records:
        if r.get('split') is None:
            raise ValueError(
                f"[FASE 2ter] Record senza split assegnato (probabile duplicato "
                f"scartato da dedup_records prima dello split): {r['query']!r}"
            )
    
    rng = random.Random(rng_seed)
    seen = {r['query'] for r in records}
    extra = []
    for src in records:
        for _ in range(variants_per_record):
            new_q = _compose_noise_variant(src['query'], rng)
            if new_q in seen:
                continue
            seen.add(new_q)
            new_r = {k: (dict(v) if isinstance(v, dict) else v) for k, v in src.items()}
            new_r['query'] = new_q
            extra.append(new_r)
    print(f"  {label:28s}: base={len(records):3d} +{len(extra):3d} (noise-wrap x{variants_per_record})")
    return extra


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 58)
    print("  build_dataset_v2.py — CYA N Classifier Dataset Builder (Unified)")
    print("=" * 58)

    intent  = build_intent_records()
    bridge  = build_bridge_records()
    # [HARD-NEG FIX] I due pool entrano in all_rec fin da subito (stesso
    # trattamento di dedup/split di tutto il resto): la loro augmentation
    # dedicata avviene però FUORI dal loop generico per class-key, in
    # FASE 2ter — vedi commento sopra TARGET_FALSE_PIPELINE_NEG. Sono gli
    # STESSI oggetti dict referenziati più sotto: dopo stratified_split()
    # avranno già 'split' popolato, nessuna ricerca per id/contenuto serve.
    all_rec = intent + bridge + MANUAL_RECORDS + FALSE_PIPELINE_HARD_NEGATIVES + KEYWORD_TRAP_NEGATIVES

    # [A2 FIX] Dedup PRIMA di split/augmentation: vedi dedup_records().
    all_rec = dedup_records(all_rec)

    print(f"\n[FASE 1] Dati base unificati:")
    print(f"  INTENT_SENTENCES         : {len(intent)}")
    print(f"  BRIDGE_SENTENCES         : {len(bridge)}")
    print(f"  Manual Cases             : {len(MANUAL_RECORDS)}")
    print(f"  False-Pipeline Hard Neg  : {len(FALSE_PIPELINE_HARD_NEGATIVES)}")
    print(f"  Keyword-Trap Hard Neg    : {len(KEYWORD_TRAP_NEGATIVES)}")
    print(f"  TOTALE                   : {len(all_rec)}")

    # [FIX LEAKAGE] Split PRIMA dell'augmentation: augment_class() genera
    # varianti quasi-identiche (un solo sinonimo sostituito) della stessa
    # frase base. Splittando DOPO l'augmentation, frase originale e sua
    # variante possono finire l'una in train e l'altra in test/val: il
    # modello "vede" in valutazione una quasi-copia di un esempio di
    # training, gonfiando artificialmente le metriche. Ogni record
    # sintetico eredita ora lo split del proprio record sorgente (già
    # avviene gratis: augment_class() copia tutti i campi di r, incluso
    # 'split', prima di sovrascrivere solo 'query'). Stesso principio vale
    # per augment_noise() più sotto (vedi [NOISE-AUG]).
    all_rec = stratified_split(all_rec)

    class_map = defaultdict(list)
    for r in all_rec:
        class_map[get_class_key(r)].append(r)

    print(f"\n[FASE 2] Augmentation (sinonimi):")
    extra = []
    below_target = []  # [M1 FIX] classi che restano sotto il target richiesto
    for k, group in class_map.items():
        if '->' in k:
            target = TARGET_PIPE
        elif '+' in k:
            # [M2 FIX] Bridge non-pipeline (general+math, general+rights):
            # prima escluse del tutto dall'augmentation (`continue`), ora
            # portate a un target esplicito e più basso di TARGET_PIPE
            # (sono esempi negativi che insegnano il NO-pipeline, non
            # pattern positivi da massimizzare quanto le pipeline vere).
            target = TARGET_BRIDGE_NEG
        else:
            target = TARGET_MONO

        if len(group) < target:
            aug = augment_class(group, target)
            total_after = len(group) + len(aug)
            print(f"  {k:25s}: +{len(aug):3d} record augmentati (tot={total_after}/{target})")
            if total_after < target:
                # [M1 FIX] augment_query() sostituisce solo la PRIMA parola
                # che matcha SYNONYMS: una frase sorgente produce al massimo
                # len(SYNONYMS[parola]) varianti uniche, indipendentemente
                # da quante volte viene ripescata dal pool. Se la copertura
                # lessicale di SYNONYMS è scarsa per questa classe, il pool
                # si esaurisce e il target NON viene raggiunto — prima
                # nessun warning lo segnalava.
                below_target.append((k, total_after, target))
            extra.extend(aug)

    if below_target:
        print(f"\n⚠️  [M1 WARNING] Classi sotto target dopo augmentation "
              f"(copertura SYNONYMS insufficiente per generare abbastanza varianti uniche):")
        for k, got, target in below_target:
            print(f"     {k:25s}: {got}/{target}  (mancano {target - got})")

    all_rec = all_rec + extra
    print(f"  Totale dopo augmentation sinonimi: {len(all_rec)}")

    # [NOISE-AUG] FASE 2bis — Opzione A (report_query_noise_augmentation.md).
    # Solo su intent+bridge (MANUAL_RECORDS esclusi di proposito, vedi
    # docstring di augment_noise()); filtro su split già assegnato per
    # sicurezza (record eventualmente rimossi da dedup_records() non hanno
    # mai attraversato stratified_split() e non avrebbero uno split valido
    # da ereditare).
    noise_source = [r for r in (intent + bridge) if r.get('split')]
    noise_extra  = augment_noise(noise_source)
    all_rec = all_rec + noise_extra
    print(f"\n[FASE 2bis] Query Noise Augmentation (Opzione A):")
    print(f"  Record sorgente eleggibili (intent+bridge, con split) : {len(noise_source)}")
    print(f"  Varianti rumorose generate                            : {len(noise_extra)}")
    print(f"  Totale dopo noise augmentation                        : {len(all_rec)}")

    # [HARD-NEG FIX] FASE 2ter — Rinforzo mirato hard-negatives,
    # INDIPENDENTE dalla saturazione del dominio mono genitore (vedi
    # commento sopra TARGET_FALSE_PIPELINE_NEG). Due meccanismi distinti
    # per motivi empirici precisi (vedi docstring dei due helper):
    #   - FALSE_PIPELINE_HARD_NEGATIVES: verbo imperativo garantito →
    #     augment_class()/SYNONYMS funziona; riceve ANCHE un passaggio
    #     noise-wrap perché la query di test fallita restava errata pure
    #     nella sua variante con suffisso di stile (wrong_query_TESTING.md).
    #   - KEYWORD_TRAP_NEGATIVES: fraseggio discorsivo, zero match SYNONYMS
    #     → solo noise-wrap, che non dipende da SYNONYMS.
    print(f"\n[FASE 2ter] Rinforzo mirato hard-negatives (bypassano la saturazione del dominio mono):")
    hard_neg_extra = []
    hard_neg_extra += augment_hard_negatives_synonyms(
        FALSE_PIPELINE_HARD_NEGATIVES, TARGET_FALSE_PIPELINE_NEG, "false_pipeline [synonyms]")
    hard_neg_extra += augment_hard_negatives_noise(
        FALSE_PIPELINE_HARD_NEGATIVES, FALSE_PIPELINE_NOISE_VARIANTS, "false_pipeline [noise-wrap]", rng_seed=4201)
    hard_neg_extra += augment_hard_negatives_noise(
        KEYWORD_TRAP_NEGATIVES, KEYWORD_TRAP_NOISE_VARIANTS, "keyword_trap [noise-wrap]", rng_seed=4242)
    all_rec = all_rec + hard_neg_extra
    print(f"  Totale dopo rinforzo hard-negatives: {len(all_rec)}")

    # [FIX LEAKAGE] Split già assegnato in FASE 1, prima dell'augmentation.
    # Questo shuffle è solo per l'ordine di scrittura nel file JSONL — NON
    # tocca lo split, altrimenti si reintroduce il leak.
    random.shuffle(all_rec)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        for r in all_rec:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    # Report finale
    split_c = Counter(r['split'] for r in all_rec)
    diff_c  = Counter(r['difficulty'] for r in all_rec)
    hist_n  = sum(1 for r in all_rec if r['history'])
    fu_n    = sum(1 for r in all_rec if r.get('is_followup'))
    pipe_n  = sum(1 for r in all_rec if r['is_pipeline'])

    print(f"\n[RISULTATI]")
    print(f"  train / val / test : {split_c['train']} / {split_c['val']} / {split_c['test']}")
    print(f"  difficulty 1/2/3   : {diff_c[1]} / {diff_c[2]} / {diff_c[3]}")
    print(f"  record con history : {hist_n}")
    print(f"  is_followup=True   : {fu_n}  ({fu_n/len(all_rec)*100:.1f}%)")
    print(f"  record pipeline    : {pipe_n}")
    print(f"\n✅  Dataset salvato in: {OUTPUT_PATH}\n")


if __name__ == '__main__':
    main()
