"""
expand_dataset_v2.py — CYA N | Step 1b: Espansione dataset con is_followup
============================================================================
Legge code/dataset_v2.jsonl, aggiunge il campo is_followup a tutti i record
esistenti e appende ~280 nuovi esempi (follow-up + cambio-dominio).
Riscrive code/dataset_v2.jsonl con split ricalcolato.

Esecuzione (dalla root del progetto):
    python code/expand_dataset_v2.py

Dopo: eseguire precompute_embeddings.py per rigenerare embeddings_v2.pkl.
"""

import json, random
from pathlib import Path
from collections import defaultdict, Counter

DATASET_PATH = Path('code/dataset_v2.jsonl')
random.seed(42)

# ── Label shortcuts ────────────────────────────────────────────────────────────
_C  = {"coding":1,"math":0,"rights":0,"general":0}
_M  = {"coding":0,"math":1,"rights":0,"general":0}
_R  = {"coding":0,"math":0,"rights":1,"general":0}
_G  = {"coding":0,"math":0,"rights":0,"general":1}

def _fu(query, labels, diff, hist):
    """Follow-up record: is_followup=True, history non vuota."""
    return {"query":query,"history":hist,"domain_labels":dict(labels),
            "is_pipeline":False,"pipeline_type":None,"difficulty":diff,
            "is_followup":True,"split":None}

def _cd(query, labels, diff, hist):
    """Cambio dominio: history presente ma is_followup=False."""
    return {"query":query,"history":hist,"domain_labels":dict(labels),
            "is_pipeline":False,"pipeline_type":None,"difficulty":diff,
            "is_followup":False,"split":None}

def _base(query, labels, diff):
    """Record standard senza history: is_followup=False."""
    return {"query":query,"history":[],"domain_labels":dict(labels),
            "is_pipeline":False,"pipeline_type":None,"difficulty":diff,
            "is_followup":False,"split":None}

# ── Queries cambio-dominio ESISTENTI (da riconoscere per label corretta) ───────
KNOWN_CAMBIO_DOMINIO = {
    "cosa mangio stasera?",
    "qual è la capitale della Francia?",
    "chi ha vinto il mondiale 2022?",
    "consigliami un ristorante a Roma",
    "consigliami un libro",
    "dammi una barzelletta",
    "consigliami scarpe uomo",
}

# ══════════════════════════════════════════════════════════════════════════════
# NUOVI ESEMPI DI FOLLOW-UP
# ══════════════════════════════════════════════════════════════════════════════

NEW_EXAMPLES = [

    # ─── CODING follow-up ────────────────────────────────────────────────────
    # history: Python

    _fu("e in JavaScript come si fa?",          _C, 1, ["Come si crea una classe in Python?"]),
    _fu("e con la programmazione funzionale?",   _C, 2, ["Spiega l'uso dei decoratori in Python."]),
    _fu("mostrami un esempio concreto",          _C, 1, ["Cos'è la comprensione di lista in Python?"]),
    _fu("e se la lista fosse vuota?",            _C, 1, ["Come si ordina una lista in Python?"]),
    _fu("aggiungi la gestione degli errori",     _C, 2, ["Scrivi un parser JSON in Python."]),
    _fu("e lo stesso con i dizionari?",          _C, 1, ["Come si usa zip() in Python?"]),
    _fu("perché non funziona con i float?",      _C, 1, ["Come si confrontano due valori in Python?"]),
    _fu("e su Python 2?",                        _C, 1, ["Cosa cambia in Python 3 rispetto a print?"]),
    _fu("come lo rendo più veloce?",             _C, 2, ["Implementa la ricerca binaria in Python."]),
    _fu("e con asyncio?",                        _C, 2, ["Come funziona il multithreading in Python?"]),
    _fu("e il tipo di ritorno?",                 _C, 1, ["Come si usano le type hints in Python?"]),
    _fu("e se avessi milioni di righe?",         _C, 2, ["Come leggo un file CSV riga per riga in Python?"]),
    _fu("mostrami il codice completo",           _C, 1, ["Come si connette Python a un database SQLite?"]),
    _fu("e con PostgreSQL?",                     _C, 2, ["Come eseguo una query SQL da Python?"]),

    # history: OOP e design pattern

    _fu("e il pattern Decorator?",               _C, 2, ["Spiega il pattern Strategy in OOP."]),
    _fu("e in un linguaggio senza classi?",      _C, 2, ["Come si implementa l'ereditarietà in Java?"]),
    _fu("puoi riscriverlo senza ereditarietà?",  _C, 2, ["Spiega la differenza tra extends e implements in Java."]),
    _fu("e la versione thread-safe?",            _C, 2, ["Implementa il pattern Singleton in Java."]),
    _fu("e i test unitari come si scrivono?",    _C, 2, ["Spiega il pattern Factory in Python."]),
    _fu("dammi un esempio reale",                _C, 1, ["Cos'è il principio di inversione delle dipendenze?"]),
    _fu("e il liskov substitution principle?",   _C, 2, ["Spiega il principio Open/Closed."]),
    _fu("come si usa con React?",                _C, 2, ["Spiega il pattern MVC."]),

    # history: algoritmi e strutture dati

    _fu("e la complessità spaziale?",            _C, 2, ["Analizza la complessità di MergeSort."]),
    _fu("e con un grafo pesato?",                _C, 2, ["Come funziona BFS su un grafo?"]),
    _fu("e se il grafo ha cicli?",               _C, 2, ["Implementa DFS su un albero binario."]),
    _fu("e la versione iterativa?",              _C, 2, ["Scrivi la versione ricorsiva di QuickSort."]),
    _fu("e l'albero AVL?",                       _C, 3, ["Spiega gli alberi rosso-neri."]),
    _fu("mostrami l'inserimento",                _C, 2, ["Come funziona un heap binario?"]),
    _fu("e su una lista linkata?",               _C, 2, ["Come si inverte un array in O(1) spazio?"]),
    _fu("e il caso medio?",                      _C, 2, ["Qual è il caso peggiore di QuickSort?"]),
    _fu("spiega meglio la parte del pivot",      _C, 2, ["Implementa QuickSort e analizza la complessità."]),

    # history: web, API, reti

    _fu("e con GraphQL?",                        _C, 2, ["Come si progetta un'API REST?"]),
    _fu("e l'autenticazione JWT?",               _C, 2, ["Come funziona OAuth 2.0?"]),
    _fu("e se l'API è lenta?",                   _C, 2, ["Come si implementa il caching in un'API?"]),
    _fu("e il rate limiting?",                   _C, 2, ["Come si gestisce la sicurezza in un'API REST?"]),
    _fu("e con WebSocket?",                      _C, 2, ["Spiega la differenza tra HTTP e HTTPS."]),
    _fu("e il load balancing?",                  _C, 2, ["Come funziona un reverse proxy?"]),
    _fu("e Docker Compose?",                     _C, 2, ["Spiega come si crea un Dockerfile."]),
    _fu("e Kubernetes?",                         _C, 3, ["Come funziona il networking in Docker?"]),
    _fu("e se il container crasha?",             _C, 2, ["Come si gestisce il restart di un container?"]),
    _fu("e i log come si gestiscono?",           _C, 2, ["Come si monitora un'applicazione in produzione?"]),

    # history: errori e debug

    _fu("come lo debuggo?",                      _C, 1, ["Cos'è un NullPointerException in Java?"]),
    _fu("e in produzione come lo trovo?",        _C, 2, ["Come si usa un debugger in Python?"]),
    _fu("e se l'errore è in un thread?",         _C, 2, ["Come si gestiscono le eccezioni in Java?"]),
    _fu("e con i test di integrazione?",         _C, 2, ["Come si scrivono unit test in Python con pytest?"]),
    _fu("e il mocking?",                         _C, 2, ["Come si usa unittest.mock in Python?"]),
    _fu("e la coverage?",                        _C, 1, ["Come si misura la qualità del codice?"]),

    # history: git, DevOps

    _fu("e il rebase?",                          _C, 1, ["Spiega la differenza tra git merge e git rebase."]),
    _fu("e i conflitti?",                        _C, 1, ["Come si fa un git cherry-pick?"]),
    _fu("e con GitHub Actions?",                 _C, 2, ["Come si configura una CI/CD pipeline?"]),
    _fu("e il rollback?",                        _C, 2, ["Come si fa il deploy di un'applicazione Flask?"]),

    # ─── MATH follow-up ──────────────────────────────────────────────────────
    # history: analisi

    _fu("spiega il passaggio algebrico",         _M, 1, ["Calcola la derivata di f(x) = e^x * sin(x)."]),
    _fu("e la derivata seconda?",                _M, 1, ["Calcola la derivata di x^3 - 3x + 2."]),
    _fu("e nel punto x=0?",                      _M, 1, ["Trova i punti critici di f(x) = x^4 - 4x^2."]),
    _fu("e l'integrale indefinito?",             _M, 2, ["Calcola l'integrale di 1/(1+x^2)."]),
    _fu("e con il metodo per parti?",            _M, 2, ["Spiega come si risolve un integrale per sostituzione."]),
    _fu("e se il limite non esiste?",            _M, 2, ["Calcola il limite di (e^x - 1)/x per x→0."]),
    _fu("e la forma indeterminata 0/0?",         _M, 2, ["Quando si usa la regola di De l'Hôpital?"]),
    _fu("mostrami un controesempio",             _M, 2, ["Dimostra il teorema di Lagrange."]),
    _fu("e le ipotesi sono sempre necessarie?",  _M, 2, ["Enuncia il teorema di Rolle."]),
    _fu("e la serie di Taylor?",                 _M, 2, ["Spiega cos'è uno sviluppo in serie di MacLaurin."]),
    _fu("e la convergenza?",                     _M, 2, ["Cos'è il raggio di convergenza di una serie?"]),
    _fu("e in più variabili?",                   _M, 3, ["Calcola il gradiente di f(x,y) = x^2*y + y^3."]),
    _fu("e il laplaciano?",                      _M, 3, ["Spiega cos'è la derivata direzionale."]),

    # history: algebra lineare

    _fu("e la sua inversa?",                     _M, 2, ["Come si calcola il determinante di una matrice 3x3?"]),
    _fu("e il rango?",                           _M, 2, ["Quando un sistema lineare ha infinite soluzioni?"]),
    _fu("e gli autovettori?",                    _M, 2, ["Come si calcolano gli autovalori di una matrice?"]),
    _fu("e la diagonalizzazione?",               _M, 3, ["Spiega la decomposizione spettrale."]),
    _fu("e la SVD?",                             _M, 3, ["Cos'è la decomposizione LU?"]),
    _fu("e in spazi di dimensione infinita?",    _M, 3, ["Cos'è uno spazio di Hilbert?"]),
    _fu("e la norma euclidea?",                  _M, 1, ["Come si calcola la distanza tra due vettori?"]),
    _fu("e la proiezione ortogonale?",           _M, 2, ["Spiega il metodo di Gram-Schmidt."]),

    # history: probabilità e statistica

    _fu("e la varianza?",                        _M, 1, ["Come si calcola la media di una distribuzione?"]),
    _fu("e la distribuzione normale?",           _M, 2, ["Spiega la distribuzione di Poisson."]),
    _fu("e il test chi-quadro?",                 _M, 2, ["Cos'è il p-value in un test statistico?"]),
    _fu("e l'intervallo di confidenza?",         _M, 2, ["Come si calcola l'errore standard?"]),
    _fu("e la correlazione di Spearman?",        _M, 2, ["Cos'è la correlazione di Pearson?"]),
    _fu("e la regressione non lineare?",         _M, 3, ["Spiega la regressione lineare multipla."]),
    _fu("e il bias-variance tradeoff?",          _M, 3, ["Cos'è l'overfitting in un modello statistico?"]),
    _fu("e con variabili categoriali?",          _M, 2, ["Come si gestiscono i valori mancanti in un dataset?"]),

    # history: metodi numerici

    _fu("e la convergenza è garantita?",         _M, 2, ["Spiega il metodo di bisezione."]),
    _fu("e il metodo di Newton?",                _M, 2, ["Come funziona il metodo delle secanti?"]),
    _fu("e l'errore di troncamento?",            _M, 2, ["Spiega il metodo di Eulero per le ODE."]),
    _fu("e Runge-Kutta 4?",                      _M, 3, ["Come funziona il metodo di Eulero implicito?"]),

    # ─── RIGHTS follow-up ────────────────────────────────────────────────────
    # history: GDPR e privacy

    _fu("e per i minori?",                       _R, 1, ["Cosa prevede il GDPR sul consenso dei dati?"]),
    _fu("e il responsabile del trattamento?",    _R, 2, ["Chi è il titolare del trattamento nel GDPR?"]),
    _fu("e le sanzioni massime?",                _R, 1, ["Come funziona la notifica di un data breach nel GDPR?"]),
    _fu("e se i dati vengono trasferiti fuori EU?",_R,2,["Cosa dice il GDPR sulle clausole standard?"]),
    _fu("e il diritto all'oblio?",               _R, 1, ["Spiega il diritto di accesso previsto dal GDPR."]),
    _fu("e il DPO è obbligatorio?",              _R, 2, ["Quando si nomina un Data Protection Officer?"]),
    _fu("e per le startup?",                     _R, 2, ["Quali obblighi GDPR ha una piccola impresa?"]),
    _fu("e i cookie?",                           _R, 1, ["Cosa prevede il GDPR per il marketing digitale?"]),
    _fu("e le app mobile?",                      _R, 2, ["Come si raccolgono i dati personali rispettando il GDPR?"]),
    _fu("vale anche per i dati anonimi?",        _R, 1, ["Quando un dato è considerato personale per il GDPR?"]),

    # history: diritto del lavoro

    _fu("e per il lavoro part-time?",            _R, 1, ["Come funziona il contratto a tempo determinato?"]),
    _fu("e i contributi INPS?",                  _R, 2, ["Come si calcola il TFR?"]),
    _fu("e se il datore non paga?",              _R, 2, ["Quali sono i diritti del lavoratore in caso di ritardo dello stipendio?"]),
    _fu("e per i lavoratori autonomi?",          _R, 2, ["Cosa prevede lo Statuto dei Lavoratori?"]),
    _fu("e il mobbing come si prova?",           _R, 3, ["Cosa si intende per demansionamento?"]),
    _fu("e la giusta causa?",                    _R, 2, ["Spiega il licenziamento per giustificato motivo."]),
    _fu("entro quanto posso fare ricorso?",      _R, 1, ["Come si impugna un licenziamento illegittimo?"]),
    _fu("e il contratto collettivo?",            _R, 2, ["Cosa disciplina il CCNL Metalmeccanici?"]),
    _fu("e per i lavoratori stranieri?",         _R, 2, ["Quali permessi servono per lavorare in Italia?"]),
    _fu("e le ferie non godute?",                _R, 1, ["Il datore può rifiutare le ferie?"]),
    _fu("e il periodo di prova?",                _R, 1, ["Come si interrompe il rapporto di lavoro durante il preavviso?"]),

    # history: contratti e civile

    _fu("e se una parte è incapace?",            _R, 2, ["Quando un contratto è nullo per il codice civile?"]),
    _fu("e la clausola penale?",                 _R, 2, ["Cosa si intende per inadempimento contrattuale?"]),
    _fu("e l'exceptio non adimpleti contractus?",_R, 3, ["Spiega la risoluzione del contratto per inadempimento."]),
    _fu("e per i contratti online?",             _R, 2, ["Cosa prevede il Codice del Consumo?"]),
    _fu("entro quando posso recedere?",          _R, 1, ["Il consumatore ha diritto di recesso?"]),
    _fu("e il silenzio vale accettazione?",      _R, 2, ["Come si forma un contratto per corrispondenza?"]),
    _fu("e la responsabilità del venditore?",    _R, 2, ["Cosa copre la garanzia legale di conformità?"]),
    _fu("e i danni morali?",                     _R, 2, ["Come si quantificano i danni in un incidente stradale?"]),

    # history: penale

    _fu("e la recidiva?",                        _R, 2, ["Quali circostanze aggravano il reato di furto?"]),
    _fu("e la prescrizione?",                    _R, 2, ["Quando si estingue un reato per prescrizione?"]),
    _fu("e per i minori?",                       _R, 2, ["Come funziona il processo penale minorile?"]),
    _fu("e la messa alla prova?",                _R, 2, ["Cos'è la sospensione condizionale della pena?"]),
    _fu("e la querela?",                         _R, 1, ["Come si denuncia un reato?"]),

    # history: fisco e tributario

    _fu("e la partita IVA a regime forfettario?",_R, 2, ["Quali sono le detrazioni IRPEF disponibili?"]),
    _fu("e le plusvalenze?",                     _R, 2, ["Come si dichiarano i redditi da investimenti?"]),
    _fu("e l'IVA sulle prestazioni digitali?",   _R, 2, ["Come funziona il reverse charge IVA?"]),
    _fu("e il ravvedimento operoso?",            _R, 2, ["Cosa succede in caso di dichiarazione tardiva?"]),

    # ─── GENERAL follow-up ───────────────────────────────────────────────────
    # history: scienza

    _fu("e gli animali lo fanno anche?",         _G, 1, ["Spiega il ciclo del sonno negli esseri umani."]),
    _fu("e su Marte?",                           _G, 1, ["Come funziona l'atmosfera terrestre?"]),
    _fu("e in assenza di gravità?",              _G, 1, ["Come funziona il sistema circolatorio umano?"]),
    _fu("e le piante?",                          _G, 1, ["Spiega la respirazione cellulare."]),
    _fu("e i batteri?",                          _G, 1, ["Come funziona il sistema immunitario?"]),
    _fu("e i virus?",                            _G, 1, ["Cosa sono gli anticorpi?"]),
    _fu("e il cervello umano?",                  _G, 1, ["Spiega come funziona la memoria."]),
    _fu("e nello spazio?",                       _G, 1, ["Come si propaga il suono nell'aria?"]),
    _fu("e per i daltonici?",                    _G, 1, ["Come vediamo i colori?"]),
    _fu("e i sogni?",                            _G, 1, ["Cosa succede al cervello durante il sonno REM?"]),
    _fu("e a temperature altissime?",            _G, 1, ["Spiega la differenza tra fusione e solidificazione."]),
    _fu("e il campo magnetico terrestre?",       _G, 1, ["Come funziona una bussola?"]),

    # history: storia e cultura

    _fu("e le conseguenze?",                     _G, 1, ["Cosa causò la Prima Guerra Mondiale?"]),
    _fu("e gli USA?",                            _G, 1, ["Come nacque l'Unione Europea?"]),
    _fu("e la Russia?",                          _G, 1, ["Spiega la Rivoluzione Francese."]),
    _fu("e oggi come è cambiato?",               _G, 1, ["Cos'è il colonialismo?"]),
    _fu("e le vittime?",                         _G, 1, ["Spiega cos'è l'Olocausto."]),
    _fu("e la Cina?",                            _G, 1, ["Spiega la Guerra Fredda."]),
    _fu("ci sono ancora oggi?",                  _G, 1, ["Cosa sono le aristocrazie?"]),
    _fu("e in Italia?",                          _G, 1, ["Come funziona il sistema parlamentare?"]),

    # history: cucina e lifestyle

    _fu("e se sono intollerante al glutine?",    _G, 1, ["Dammi una ricetta per la pasta alla carbonara."]),
    _fu("e quanto tempo di cottura?",            _G, 1, ["Come si prepara il risotto alla milanese?"]),
    _fu("e varianti vegane?",                    _G, 1, ["Come si fa la lasagna al forno?"]),
    _fu("e senza forno?",                        _G, 1, ["Dammi una ricetta per la pizza napoletana."]),
    _fu("e se ho solo 15 minuti?",               _G, 1, ["Cosa posso cucinare con uova e pane?"]),
    _fu("e il vino abbinato?",                   _G, 1, ["Quale taglio di carne è migliore per una grigliata?"]),
    _fu("e il giorno dopo?",                     _G, 1, ["Come si conserva il tiramisù?"]),

    # history: consigli e domande esistenziali

    _fu("e se non funziona?",                    _G, 1, ["Come si affronta un colloquio di lavoro?"]),
    _fu("e online?",                             _G, 1, ["Come si impara una nuova lingua velocemente?"]),
    _fu("e se non ho soldi da investire?",       _G, 1, ["Come si inizia a investire in borsa?"]),
    _fu("e i rischi?",                           _G, 1, ["Cos'è il crowdfunding?"]),
    _fu("e per gli anziani?",                    _G, 1, ["Quali sono i benefici della meditazione?"]),
    _fu("e i bambini?",                          _G, 1, ["Spiega i benefici dello sport per la salute."]),
    _fu("ma funziona davvero?",                  _G, 1, ["Cosa si intende per pensiero positivo?"]),
    _fu("e la memoria a lungo termine?",         _G, 1, ["Come si studia in modo efficace?"]),
    _fu("e se ho ansia?",                        _G, 1, ["Come si gestisce lo stress da lavoro?"]),
    _fu("e le relazioni a distanza?",            _G, 1, ["Quali sono i fattori che rendono una relazione duratura?"]),
    _fu("e i social media?",                     _G, 1, ["Come si riconosce la manipolazione psicologica?"]),

    # ─── CAMBIO DOMINIO aggiuntivi (is_followup=False, history presente) ─────
    # Tecnico → General

    _cd("che film mi consigli?",                 _G, 1, ["Implementa un sistema di cache LRU in Python."]),
    _cd("dove vado in vacanza?",                 _G, 1, ["Come si calcola la trasformata di Laplace?"]),
    _cd("cosa faccio questo weekend?",           _G, 1, ["Spiega il pattern Command in Java."]),
    _cd("hai una barzelletta?",                  _G, 1, ["Implementa un grafo orientato con lista di adiacenza."]),
    _cd("raccontami qualcosa di interessante",   _G, 1, ["Come funziona la regressione logistica?"]),
    _cd("qual è il tuo colore preferito?",       _G, 1, ["Spiega la normalizzazione in un database SQL."]),
    _cd("dimmi una curiosità sul mondo",         _G, 1, ["Come si implementa un algoritmo genetico?"]),
    _cd("mi suggerisci un podcast?",             _G, 1, ["Spiega il teorema di Bayes con un esempio."]),
    _cd("cosa pensi dell'intelligenza artificiale?",_G,1,["Implementa una rete neurale ricorrente in PyTorch."]),
    _cd("fammi un complimento",                  _G, 1, ["Come si gestisce la memoria in C++?"]),

    # General → Tecnico (switch verso dominio tecnico)

    _cd("implementa un algoritmo per calcolare la traiettoria",
        _C, 3, ["Consigliami un libro di fisica."]),
    _cd("scrivi un programma che simula il lancio di una moneta",
        _C, 2, ["Spiega la teoria della probabilità."]),
    _cd("qual è la formula per calcolare gli interessi composti?",
        _M, 2, ["Cosa mi consigli per risparmiare?"]),
    _cd("quali norme regolano il telelavoro in Italia?",
        _R, 2, ["Cosa cambierà nel mondo del lavoro con l'AI?"]),
    _cd("come si calcola l'IVA su una fattura?",
        _M, 1, ["Come funziona la partita IVA?"]),

    # Rights → Coding (switch dominio tecnico)

    _cd("scrivi una funzione Python per la validazione dell'email",
        _C, 1, ["Cosa prevede il GDPR sul consenso?"]),
    _cd("implementa il login con JWT in Flask",
        _C, 2, ["Come funziona l'autenticazione a due fattori?"]),

    # Math → Rights

    _cd("è legale vendere dati statistici anonimi?",
        _R, 2, ["Come funziona l'analisi della varianza ANOVA?"]),
    _cd("quali norme regolano le scommesse sportive in Italia?",
        _R, 2, ["Spiega la probabilità condizionata."]),
]

# ══════════════════════════════════════════════════════════════════════════════
# FUNZIONI
# ══════════════════════════════════════════════════════════════════════════════

def get_class_key(record: dict) -> str:
    if record.get('is_pipeline') and record.get('pipeline_type'):
        return record['pipeline_type']
    active = [d for d, v in record['domain_labels'].items() if v == 1]
    return active[0] if len(active) == 1 else '+'.join(sorted(active))

def stratified_split(records: list) -> list:
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

def add_is_followup_to_existing(record: dict) -> dict:
    """
    Aggiunge is_followup ai record esistenti che non ce l'hanno.
    Logica: history presente + query NON in KNOWN_CAMBIO_DOMINIO → True
    """
    if 'is_followup' in record:
        return record
    if record.get('history') and record['query'] not in KNOWN_CAMBIO_DOMINIO:
        record['is_followup'] = True
    else:
        record['is_followup'] = False
    return record

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  expand_dataset_v2.py — CYA N Dataset Expansion")
    print("=" * 60)

    # ── 1. Carica dataset esistente ──────────────────────────────────────────
    existing = []
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                existing.append(json.loads(line))

    print(f"\n[1] Record esistenti: {len(existing)}")

    # ── 2. Aggiungi is_followup ai record esistenti ──────────────────────────
    existing = [add_is_followup_to_existing(r) for r in existing]
    fu_existing = sum(1 for r in existing if r.get('is_followup'))
    print(f"    is_followup=True esistenti: {fu_existing}")
    print(f"    cambio-dominio riconosciuti: {len(KNOWN_CAMBIO_DOMINIO)}")

    # ── 3. Deduplica nuovi esempi ────────────────────────────────────────────
    existing_queries = {r['query'] for r in existing}
    new_unique = [r for r in NEW_EXAMPLES if r['query'] not in existing_queries]
    duplicates = len(NEW_EXAMPLES) - len(new_unique)
    if duplicates:
        print(f"    ⚠ {duplicates} nuovi record scartati (duplicati)")

    new_fu  = sum(1 for r in new_unique if r.get('is_followup'))
    new_cd  = sum(1 for r in new_unique if not r.get('is_followup') and r.get('history'))
    print(f"\n[2] Nuovi record aggiunti: {len(new_unique)}")
    print(f"    follow-up (is_followup=True): {new_fu}")
    print(f"    cambio-dominio (is_followup=False + history): {new_cd}")

    # ── 4. Merge e re-split ──────────────────────────────────────────────────
    all_records = existing + new_unique
    for r in all_records:
        r['split'] = None     # reset per re-stratificazione uniforme

    random.shuffle(all_records)
    all_records = stratified_split(all_records)

    # ── 5. Salvataggio ───────────────────────────────────────────────────────
    with open(DATASET_PATH, 'w', encoding='utf-8') as f:
        for r in all_records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    # ── 6. Report finale ─────────────────────────────────────────────────────
    n = len(all_records)
    split_c = Counter(r['split']      for r in all_records)
    diff_c  = Counter(r['difficulty'] for r in all_records)
    fu_n    = sum(1 for r in all_records if r.get('is_followup'))
    hist_n  = sum(1 for r in all_records if r.get('history'))
    pipe_n  = sum(1 for r in all_records if r.get('is_pipeline'))

    print(f"\n{'='*60}")
    print(f"DATASET AGGIORNATO → {DATASET_PATH}")
    print(f"{'='*60}")
    print(f"  Record totali      : {n}")
    print(f"  train/val/test     : {split_c['train']}/{split_c['val']}/{split_c['test']}")
    print(f"  difficulty 1/2/3   : {diff_c[1]}/{diff_c[2]}/{diff_c[3]}")
    print(f"  con history        : {hist_n}")
    print(f"  is_followup=True   : {fu_n}  ({fu_n/n*100:.1f}%)")
    print(f"  pipeline           : {pipe_n}")
    print(f"\n  --- DOMAIN COUNTS ---")
    for d in ['coding','math','rights','general']:
        cnt = sum(r['domain_labels'][d] for r in all_records)
        print(f"  {d:8s}: {int(cnt)}")
    print(f"\n✅  Ora esegui: python code/precompute_embeddings.py")


if __name__ == '__main__':
    main()
