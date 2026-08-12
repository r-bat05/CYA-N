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

Output: code/dataset_v2.jsonl

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

import json, random, re
from collections import defaultdict, Counter
from db_query import INTENT_SENTENCES, BRIDGE_SENTENCES
from pathlib import Path

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
OUTPUT_PATH = Path(__file__).resolve().parent / 'dataset_v2.jsonl'

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
    _cd("come si calcola l'IVA su una fattura?", _M, 1, ["Come funziona la partita IVA?"]),
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

    # ── FALSE pipeline (sembrano multi-domain ma sono mono) ──
    _r("codice Python per sommare una lista di numeri", _C, 1),
    _r("scrivi una funzione Python che calcola la media",_C, 1),
    _r("codice per stampare i numeri da 1 a 100",       _C, 1),
    _r("Python per leggere un file CSV",                _C, 1),
    _r("cosa dice la legge sul codice fiscale?",        _R, 1),
    _r("spiegami la normativa sui contratti di lavoro", _R, 2),
    _r("qual è il codice penale per il furto?",         _R, 1),
    _r("cos'è la media geometrica?",                    _M, 1),

    # ── TRUE pipeline ESPLICITE (segnale diretto) ──
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
]

# ── Helper functions ───────────────────────────────────────────────────────────

_HARD_MARKERS = {
    'coding': [
        'algoritmo genetico', 'programmazione dinamica', 'rete neurale',
        'crittografia', 'ellittica', 'distribuit', 'concorren',
        'compilatore', 'kernel', 'simplesso', 'trasformata',
        'fattorizzazione', 'complessità', 'automa cellulare',
        'omomorfic', 'frattal', 'gestore di memoria', 'interrupt',
    ],
    'math': [
        'dimostra', 'dimostrazione', 'teorema', 'per induzione', 'per assurdo',
        'spazio di hilbert', 'spazio di banach', 'convergenza', 'topologia',
        'varietà differenziabile', 'decomposizione spettrale',
        'equazione differenziale', 'trasformata', 'funzione zeta',
        'gödel', 'lebesgue', 'markov', 'mcmc', 'diagonalizza',
    ],
    'rights': [
        'costituzional', 'diritto internazionale', 'giurisdizione extraterritoriale',
        'corte penale internazionale', 'immunità diplomatica',
        'responsabilità internazionale', "crimini contro l'umanità",
    ],
    'general': [
        'paradosso', 'meccanica quantistica', 'filosofia', 'teoria delle idee',
        'relatività', 'buco nero', 'principio di indeterminazione',
    ],
}


def estimate_difficulty(query: str, is_pipeline: bool, dominant_domain: str) -> int:
    """
    [FIX — Opzione B, Report Gemini] Sostituita la costante fissa per
    dominio (Livello 2 per ogni query tecnica, 1 per general): non
    forniva alla difficulty_head alcun segnale reale, riducendola a un
    proxy del domain-label. Ora il livello 3 (tecnici) / 2 (general)
    scatta solo in presenza di marker lessicali di complessità teorica
    o strutturale. Preferita a un criterio basato sulla lunghezza della
    query, che penalizzerebbe ingiustamente le molte query tecniche
    short-form presenti nel dataset (fix P2 anti-degradazione).
    Euristica non validata empiricamente su larga scala: da verificare
    con uno smoke test dedicato prima di considerarla definitiva.
    """
    if is_pipeline:
        return 3

    q_lower = query.lower()
    has_hard_marker = any(m in q_lower for m in _HARD_MARKERS.get(dominant_domain, []))

    if dominant_domain == 'general':
        return 2 if has_hard_marker else 1
    return 3 if has_hard_marker else 2


def get_dominant_domain(domain_labels: dict) -> str:
    """Restituisce il dominio con valore 1 più alto (o il primo se pari)."""
    return max(domain_labels, key=domain_labels.get)

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
                diff=estimate_difficulty(s, False, domain),
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
        dominant = get_dominant_domain(labels)
        for s in sentences:
            records.append(_r(
                query=s, 
                labels=labels, 
                diff=estimate_difficulty(s, is_pipe, dominant),
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
        norm = r['query'].strip().lower()
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


def stratified_split(records: list) -> list:
    groups = defaultdict(list)
    for r in records:
        groups[get_class_key(r)].append(r)

    result = []
    empty_splits = []  # [M3 FIX] classi con split val/test vuoto (n troppo piccolo)
    for key, group in groups.items():
        random.shuffle(group)
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

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 58)
    print("  build_dataset_v2.py — CYA N Classifier Dataset Builder (Unified)")
    print("=" * 58)

    intent  = build_intent_records()
    bridge  = build_bridge_records()
    all_rec = intent + bridge + MANUAL_RECORDS

    # [A2 FIX] Dedup PRIMA di split/augmentation: vedi dedup_records().
    all_rec = dedup_records(all_rec)

    print(f"\n[FASE 1] Dati base unificati:")
    print(f"  INTENT_SENTENCES : {len(intent)}")
    print(f"  BRIDGE_SENTENCES : {len(bridge)}")
    print(f"  Manual Cases     : {len(MANUAL_RECORDS)}")
    print(f"  TOTALE           : {len(all_rec)}")

    # [FIX LEAKAGE] Split PRIMA dell'augmentation: augment_class() genera
    # varianti quasi-identiche (un solo sinonimo sostituito) della stessa
    # frase base. Splittando DOPO l'augmentation, frase originale e sua
    # variante possono finire l'una in train e l'altra in test/val: il
    # modello "vede" in valutazione una quasi-copia di un esempio di
    # training, gonfiando artificialmente le metriche. Ogni record
    # sintetico eredita ora lo split del proprio record sorgente (già
    # avviene gratis: augment_class() copia tutti i campi di r, incluso
    # 'split', prima di sovrascrivere solo 'query').
    all_rec = stratified_split(all_rec)

    class_map = defaultdict(list)
    for r in all_rec:
        class_map[get_class_key(r)].append(r)

    print(f"\n[FASE 2] Augmentation:")
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
            # pattern positivi da massimizzare).
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
    print(f"  Totale dopo augmentation: {len(all_rec)}")

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