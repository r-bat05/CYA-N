"""
    VECTOR STORE V1.0 — LanceDB k-NN Engine

    Sostituisce il PrototypeStore a centroide (semantic_router.py V2.0) con un
    database vettoriale su disco e ricerca k-Nearest Neighbors esatti.

    Problema risolto — Effetto Centroide:
    La media vettoriale schiacciava lo spazio semantico verso il centro, rendendo
    ogni dominio denso "attrattivo" per query estranee. Il vettore medio di ~40
    frasi legali finiva per catturare parole ambigue come "ordine", "costanti",
    "risolvi" presenti anche in query puramente matematiche, generando falsi ibridi.

    Soluzione — k-NN Voting:
    Ogni frase è un punto separato nello spazio. Una query trova i suoi K vicini
    reali. Se tutti e 10 i vicini di "risolvi l'equazione differenziale" sono
    frasi matematiche, il dominio MATH ottiene 10/10 voti. RIGHTS ottiene 0/10 e
    non può mai attivare l'arco ibrido, indipendentemente da qualsiasi soglia.

    Logica di ibridazione (doppia condizione):
    Un secondo dominio viene attivato SOLO SE raggiunge ENTRAMBE:
    - knn_min_abs_votes  : voti assoluti minimi (es. >= 3 su 10)
    - knn_min_vote_ratio : % voti su combinato top+second (es. >= 30%)
    Questo azzera i falsi positivi perché un secondo dominio con 0 voti non
    supererà mai min_abs_votes, indipendentemente dal ratio.

    Normalizzazione L2:
    I vettori vengono normalizzati a lunghezza unitaria prima di essere salvati
    e prima di ogni ricerca. Con vettori normalizzati, la distanza L2 è
    monotonicamente equivalente alla distanza coseno:
        L2(a,b)^2 = 2 - 2*cos(a,b)
    Questo permette di usare la metrica L2 predefinita di LanceDB ottenendo
    semanticamente una ricerca per similarità coseno.

    Gestione del ciclo di vita:
    - Primo avvio: il DB non esiste -> initialize_store() lo costruisce (minuti)
    - Avvii successivi: il DB esiste -> caricamento istantaneo da disco
    - Per forzare una ricostruzione: eseguire `python vector_store.py`
"""

import os
import sys
import math
import ollama
from typing import List, Dict, Tuple, Optional

try:
    import lancedb
except ImportError as e:
    raise ImportError(
        "VectorStore richiede lancedb. Installalo con: pip install lancedb"
    ) from e

import config

# ---------------------------------------------------------------------------
# COSTANTI
# ---------------------------------------------------------------------------

DB_PATH    = os.path.join(config.BASE_DIR, "vector_db")
TABLE_NAME = "intent_vectors"
VECTOR_DIM = 768  # dimensione output di nomic-embed-text

# Valori di default per i parametri k-NN (sovrascrivibili da config.SEMANTIC_SETTINGS)
_DEFAULT_K              = 10
_DEFAULT_MIN_VOTE_RATIO = 0.30
_DEFAULT_MIN_ABS_VOTES  = 3

# Riferimento globale alla tabella LanceDB.
# Viene impostato da initialize_store() e usato da _get_table() per evitare
# riconnessioni ad ogni query.
_table = None


# ---------------------------------------------------------------------------
# INTENT SENTENCES
# ---------------------------------------------------------------------------
# Dizionario di frasi di intento per i 4 domini.
# Ogni frase e' un punto indipendente nello spazio vettoriale.
# NON concatenare frasi: ogni voce contribuisce come un singolo vicino k-NN.
#
# Criteri di bilanciamento per aggiungere frasi:
# - Casi puri: rendono il cluster del dominio coeso e discriminativo
# - Casi ibridi reali: il dominio e' quello che "governa" la richiesta
# - Edge cases: frasi che coprono trappole lessicali dai test di stress
# ---------------------------------------------------------------------------

INTENT_SENTENCES: Dict[str, List[str]] = {
    'coding': [
        # --- Azioni base di programmazione ---
        "Scrivi il codice per fare questo.",
        "Implementa una funzione che calcola.",
        "Crea un algoritmo per risolvere il problema.",
        "Fammi un programma in Python che esegue questa operazione.",
        "Correggi questo bug nel codice sorgente.",
        "Come si scrive questa funzione in JavaScript o TypeScript?",
        "Sviluppa uno script che elabora e trasforma i dati.",
        "Mostrami come implementare questa struttura dati in codice.",
        "Scrivi una classe orientata agli oggetti con questi metodi.",
        "Come faccio il debug di questo errore nel programma?",
        "Crea un'API REST con Flask o FastAPI.",
        "Refactoring e ottimizzazione di questo codice sorgente.",
        # --- Azioni di coding su contenuto matematico (ibridi C+M) ---
        "Scrivi il codice Python per calcolare questa formula matematica.",
        "Implementa in Python l'algoritmo di eliminazione di Gauss per matrici.",
        "Crea una funzione che calcoli la norma di un vettore o una matrice.",
        "Scrivi uno script che calcola la matrice inversa di un tensore.",
        "Implementa il calcolo della derivata numerica di una funzione matematica.",
        "Scrivi in C++ l'algoritmo di Dijkstra per trovare il cammino minimo in un grafo.",
        "Implementa la successione di Fibonacci con programmazione dinamica e memoization.",
        "Ottimizza il codice che calcola serie matematiche per evitare stack overflow.",
        "Scrivi una funzione JavaScript per calcolare l'ammortamento a rate costanti.",
        "Crea uno script per il calcolo numerico di integrali o derivate parziali.",
        "Qual e' la complessita' Big O di questa funzione che esegue calcoli matematici?",
        "Implementa in C++ un algoritmo efficiente per calcolare la FFT di un segnale.",
        "Scrivi una funzione che calcola la distanza euclidea tra due vettori in JavaScript.",
        "Implementa in codice la formula per la distanza tra punti in uno spazio n-dimensionale.",
        # --- Azioni di coding su contenuto legale/normativo (ibridi C+R) ---
        "Sviluppa uno smart contract in Solidity con clausole contrattuali automatiche.",
        "Scrivi codice che rispetti le normative GDPR per la gestione dei database.",
        "Implementa un sistema di logging su server Linux usabile come prova legale.",
        "Crea un'architettura software conforme alle normative europee sulla privacy.",
        "Scrivi uno script per web scraping rispettando le leggi sul copyright.",
        "Progetta un database SQL per dati sanitari seguendo le direttive normative.",
        "Scrivi uno script Python che anonimizza dati in un database SQL con conformita' GDPR.",
        "Configura un server di log in Linux per file con validita' probatoria in tribunale.",
        # --- Edge cases: infrastruttura/DevOps ---
        "Scrivimi un file docker-compose per il deploy di un'applicazione cloud.",
        "Configura le foreign key e relazioni di integrita' referenziale in SQL.",
        "Come si integra una licenza open source MIT in un container Docker?",
        "Scrivi uno script bash per automatizzare il deployment e il monitoring.",
        # --- Kubernetes/orchestrazione (copertura Q15 stress test) ---
        "Come configuro un cluster Kubernetes per il bilanciamento del carico tra i pod in produzione?",
        "Gestisci i deployment, i service e gli ingress con kubectl su un cluster Kubernetes.",
        "Come si configura un'applicazione su Kubernetes con replica set e autoscaling?",
        "Crea un componente React che gestisce uno stato globale usando la Context API.",
    ],
    'math': [
        # --- Calcolo e risoluzione pura ---
        "Calcola il risultato di questa espressione matematica.",
        "Dimostra questo teorema passo per passo.",
        "Trova il limite di questa funzione analitica.",
        "Calcola l'integrale definito o indefinito di questa funzione.",
        "Qual e' la derivata parziale di questa espressione?",
        "Spiega questo concetto matematico in modo teorico e rigoroso.",
        "Risolvi questo sistema di equazioni lineari con Gauss.",
        "Calcola il determinante e il rango di questa matrice.",
        "Dimostra per induzione matematica questa proprieta'.",
        "Trova gli autovalori e autovettori di questa matrice.",
        "Studia la convergenza di questa serie numerica o successione.",
        "Applica il teorema di Taylor per sviluppare questa funzione.",
        "Calcola la probabilita' di questo evento con la distribuzione statistica.",
        "Risolvi questo esercizio di algebra lineare o geometria differenziale.",
        "Dimostra il teorema di Lagrange e le sue applicazioni nello studio di funzione.",
        "Quali sono gli autovalori e gli autovettori della matrice identita' 3x3?",
        # --- Equazioni differenziali (rinforzo diretto: questo era il bug case) ---
        "Risolvi questa equazione differenziale.",
        "Risolvi l'equazione differenziale lineare del secondo ordine a coefficienti costanti.",
        "Trova la soluzione generale di questa equazione differenziale omogenea.",
        "Applica il metodo caratteristico per risolvere equazioni differenziali lineari.",
        "Studia l'equazione differenziale con condizioni iniziali al contorno.",
        "Qual e' la soluzione particolare di questa ODE con coefficienti costanti?",
        "Risolvi il problema di Cauchy per questa equazione differenziale ordinaria.",
        # --- Integrali e calcolo ---
        "Calcola l'integrale definito da 0 a pi greco di questa funzione.",
        "Calcola l'integrale definito da 0 a pi greco di x moltiplicato per il seno di x.",
        "Risolvi l'integrale usando il metodo di integrazione per parti.",
        "Calcola la trasformata di Fourier di questo segnale discreto.",
        # --- Rafforzamento segnale dimostrativo ---
        "Dimostrami questo teorema con un ragionamento logico strutturato passo per passo.",
        "Qual e' il procedimento manuale per calcolare questo valore matematico esatto?",
        "Calcola a mano l'intersezione tra due funzioni esponenziali mostrando i passaggi.",
        # --- Casi ibridi math con lessico informatico ---
        "Qual e' la complessita' asintotica Big O di questo algoritmo teorico?",
        "Come ottimizzo la complessita' asintotica di un algoritmo di moltiplicazione tra matrici sparse?",
        "Scrivi lo script Python per trovare le radici di un polinomio con Newton-Raphson.",
    ],
    'rights': [
        # --- Diritto puro ---
        "Cosa dice la legge italiana su questo argomento giuridico?",
        "Qual e' la normativa vigente in materia di diritto sportivo?",
        "Spiegami questo istituto giuridico del diritto italiano.",
        "Cosa prevede il codice civile italiano in questo caso specifico?",
        "Quali sono i diritti e doveri secondo la costituzione italiana?",
        "Come funziona il processo penale in Italia per questo reato?",
        "Cosa si intende per questo termine giuridico legale?",
        "Spiega il DASPO e la normativa sportiva italiana.",
        "Quali sanzioni prevede il codice di giustizia sportiva?",
        "Come funziona il ricorso al tribunale amministrativo regionale?",
        "Cosa dice la giurisprudenza su questo caso legale?",
        "Quali sono le fonti del diritto nell'ordinamento giuridico italiano?",
        "Spiega il significato di questo articolo di legge o decreto.",
        "Come si applica questa norma giuridica nella pratica legale?",
        "Qual e' la differenza tra questi due istituti del diritto civile?",
        "Quali sono i requisiti normativi per richiedere la cittadinanza italiana per residenza?",
        "Come funziona l'istituto del patteggiamento e in quali casi non puo' essere richiesto?",
        "Spiegami la differenza tra dolo, colpa cosciente e preterintenzione nel codice penale.",
        "Quali sono le tutele legali previste dallo Statuto dei Lavoratori contro il licenziamento?",
        # --- Casi ibridi rights+tech (la norma e' il focus) ---
        "Quali direttive GDPR si applicano quando si progetta un sistema informatico?",
        "Il web scraping di un sito viola le leggi sul diritto d'autore o il copyright?",
        "Come garantire che i log informatici siano prove valide in un processo penale?",
        "Quali norme del codice civile regolano la nullita' di un contratto software?",
        "Come si tutelano i dati sanitari secondo la normativa europea sulla privacy?",
        "Qual e' la penale legale per violazione di un contratto di licenza software?",
        # --- Edge cases: procedure legali con contesto tecnologico ---
        "Qual e' la procedura legale prevista dalla normativa italiana per questo caso?",
        "Quali sono le implicazioni giuridiche dell'uso di algoritmi automatizzati?",
        "Come funziona la gerarchia delle fonti del diritto italiano?",
        "Quali requisiti giuridici devono soddisfare i log di un server per essere prove in tribunale?",
        "Come garantisce la normativa italiana la validita' probatoria dei file informatici?",
        # --- Formula/calcolo stabilito dalla legge (copertura Q7, Q19, Q25 stress test) ---
        "Qual e' il metodo di calcolo stabilito dalla normativa italiana per il TFR?",
        "Come prevede la legge di calcolare questa indennita' economica spettante al lavoratore?",
        "Qual e' la formula legale per il calcolo dell'assegno di mantenimento dei figli?",
        "Come si applica l'adeguamento ISTAT agli assegni divorzili secondo la legge?",
        "Metodo di calcolo numerico previsto dalla giurisprudenza per la rivalutazione monetaria.",
        "Parametri del tribunale per la determinazione della quota di mantenimento.",
        "Quali sono i criteri normativi per il calcolo delle sanzioni tributarie e amministrative?",
        "Calcolo della quota disponibile in presenza di legittimari secondo l'ordinamento.",
        "Norme del codice civile sul calcolo della collazione e della riduzione ereditaria.",
        "Come si applica il calcolo attuariale secondo le direttive assicurative vigenti?",
        "Quali normative regolano la valutazione del rischio nelle assicurazioni?",
        "Quale metodo di calcolo prevede la giurisprudenza per l'adeguamento ISTAT degli assegni?",
        # --- Successione ereditaria ---
        "Spiegami come si calcolano le quote di legittima e la quota disponibile in una successione.",
        "Quali sono le quote legittime di un'eredita' secondo le norme giuridiche?",
        # --- Smart contract con focus normativo ---
        "Quali clausole contrattuali automatiche prevede la legge per l'inadempimento?",
    ],
    'general': [
        # --- Cultura generale e domande aperte ---
        "Dimmi qualcosa su questo argomento di cultura generale.",
        "Spiegami questo fenomeno storico, geografico o scientifico.",
        "Cosa pensi di questa situazione di attualita'?",
        "Raccontami come funziona questo nella vita quotidiana.",
        "Dammi informazioni su questo personaggio storico o evento.",
        "Qual e' la tua opinione su questo tema generico?",
        "Spiegami questo concetto in modo semplice e accessibile.",
        "Hai consigli pratici su questo argomento di vita comune?",
        "Come si fa questa cosa nella vita di tutti i giorni?",
        "Puoi aiutarmi con questa domanda di carattere generale?",
        # --- Storia e civilta' ---
        "Quali furono le cause economiche e sociali del crollo dell'Impero Romano d'Occidente?",
        "Spiegami le origini e le conseguenze storiche della Prima Guerra Mondiale.",
        "Come si sviluppo' la civilta' egizia lungo il corso del Nilo?",
        "Quali fattori storici hanno portato alla Rivoluzione Francese del 1789?",
        "Raccontami la storia dell'Impero Ottomano e le ragioni del suo declino.",
        "Chi era Napoleone Bonaparte e qual e' stato il suo impatto sulla storia europea?",
        "Quali furono le conseguenze geopolitiche della Seconda Guerra Mondiale?",
        # --- Filosofia e pensiero ---
        "Spiegami la filosofia stoica e i suoi principi fondamentali sulla vita.",
        "Qual e' la differenza tra etica deontologica e utilitarismo in filosofia morale?",
        "Cosa intendeva Platone con la sua teoria delle idee e delle forme?",
        "Come si differenziano le grandi correnti del pensiero filosofico occidentale?",
        # --- Biologia e scienze naturali ---
        "Come funziona la fotosintesi clorofilliana nelle piante a foglia larga?",
        "Spiega il meccanismo dell'evoluzione darwiniana e della selezione naturale.",
        "Come funziona il sistema immunitario umano in risposta a un'infezione?",
        "Cosa sono le cellule staminali e come vengono utilizzate nella medicina moderna?",
        # --- Questioni sociali e attualita' ---
        "Quali sono i pro e i contro psicologici e sociali di vivere in una grande metropoli rispetto alla campagna?",
        "Come influisce il cambiamento climatico sugli ecosistemi globali e sulla biodiversita'?",
        "Quali sono le principali cause storiche della disuguaglianza economica nel mondo?",
        # --- Letteratura, arte e cultura ---
        "Spiegami i temi principali e la struttura della Divina Commedia di Dante Alighieri.",
        "Quali sono le caratteristiche principali del Romanticismo letterario europeo?",
        "Come si distingue il periodo Barocco dal Rinascimento nell'arte italiana?",
        # --- Ricette e cucina (copertura Q18 stress test) ---
        "Dammi una ricetta tradizionale con i dosaggi esatti degli ingredienti.",
        "Come si prepara questo piatto tipico della cucina italiana?",
        "Dammi una ricetta tradizionale per preparare la carbonara romana.",
    ]
}


# ---------------------------------------------------------------------------
# UTILITA' VETTORIALI
# ---------------------------------------------------------------------------

def l2_normalize(vec: List[float]) -> List[float]:
    """
    Normalizza un vettore alla lunghezza unitaria (norma L2 = 1).
    Con vettori normalizzati, la distanza L2 di LanceDB e' monotonicamente
    equivalente alla distanza coseno, senza richiedere una metrica specifica.
    """
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return vec
    return [x / norm for x in vec]


def _embed(text: str, model: str) -> Optional[List[float]]:
    """Chiama ollama.embeddings e restituisce il vettore grezzo, o None in caso di errore."""
    try:
        response = ollama.embeddings(model=model, prompt=text)
        return response['embedding']
    except Exception as e:
        print(f"WARNING VectorStore: embedding fallito -> {e}")
        return None


# ---------------------------------------------------------------------------
# INIZIALIZZAZIONE E ACCESSO AL DB
# ---------------------------------------------------------------------------

def initialize_store() -> bool:
    """
    Inizializza il Vector Store su disco (LanceDB).

    Comportamento:
    - Se il DB esiste gia': apre la tabella e carica il riferimento globale.
      Nessun re-embedding, avvio istantaneo.
    - Se il DB non esiste: embedda tutte le INTENT_SENTENCES, normalizza i
      vettori L2, e salva su disco. Operazione one-shot (qualche minuto).
    - Se la tabella esiste ma e' corrotta (apertura fallisce): ricrea da zero
      sovrascrivendo con mode="overwrite".

    Per forzare una ricostruzione completa: eseguire `python vector_store.py`.

    Returns:
        bool: True se il VectorStore e' pronto per le query, False in caso di
              errore bloccante (es. Ollama non raggiungibile durante la build).
    """
    global _table

    model = config.SEMANTIC_SETTINGS['embedding_model']

    try:
        db = lancedb.connect(DB_PATH)
    except Exception as e:
        print(f"ERRORE VectorStore: impossibile connettersi al DB in '{DB_PATH}' -> {e}")
        return False

    # --- Caso 1: tabella gia' esistente ---
    if TABLE_NAME in db.table_names():
        try:
            _table = db.open_table(TABLE_NAME)
            count = _table.count_rows()
            print(f"   OK  VectorStore caricato da disco: {count} vettori in '{DB_PATH}'.")
            return True
        except Exception as e:
            # Tabella corrotta o incompatibile: si ricade nel percorso di ricostruzione
            print(f"   WARN VectorStore: tabella esistente non apribile ({e}). Ricostruzione...")
            _table = None

    # --- Caso 2: costruzione da zero ---
    total_sentences = sum(len(v) for v in INTENT_SENTENCES.values())
    print(f"\nCostruzione Vector Store ({total_sentences} frasi totali, salvataggio su disco)...")
    print(f"   Percorso DB: {DB_PATH}")
    print(f"   Questo avviene solo al primo avvio. Gli avvii successivi saranno istantanei.\n")

    records = []
    all_ok = True

    for domain, sentences in INTENT_SENTENCES.items():
        embedded_count = 0
        for sentence in sentences:
            vec = _embed(sentence, model)
            if vec is None:
                all_ok = False
                continue
            norm_vec = l2_normalize(vec)
            records.append({
                "vector": norm_vec,
                "domain": domain,
                "sentence": sentence
            })
            embedded_count += 1

        status = "OK" if embedded_count == len(sentences) else "WARN"
        print(f"   {status}  [{domain:7s}] {embedded_count}/{len(sentences)} frasi embeddate")

    if not records:
        print("\nERRORE VectorStore: nessun vettore generato.")
        print("   Verifica che Ollama sia attivo e che il modello 'nomic-embed-text' sia installato.")
        print("   Comando: ollama pull nomic-embed-text")
        return False

    try:
        _table = db.create_table(TABLE_NAME, data=records, mode="overwrite")
        print(f"\n   OK  VectorStore creato: {len(records)}/{total_sentences} vettori salvati su disco.\n")
        if not all_ok:
            print("   WARN Alcune frasi non sono state embeddate. Il routing potrebbe essere meno preciso.")
        return True
    except Exception as e:
        print(f"\nERRORE VectorStore: errore durante la creazione della tabella -> {e}")
        _table = None
        return False


def _get_table():
    """
    Restituisce il riferimento alla tabella LanceDB.
    Se il riferimento globale non e' impostato (es. initialize_store() non e' stato
    chiamato o ha fallito), tenta un'apertura lazy del DB esistente su disco.
    Restituisce None se il DB non e' disponibile.
    """
    global _table
    if _table is not None:
        return _table

    # Apertura lazy (rete di sicurezza)
    try:
        db = lancedb.connect(DB_PATH)
        if TABLE_NAME in db.table_names():
            _table = db.open_table(TABLE_NAME)
            return _table
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# CLASSIFICAZIONE k-NN
# ---------------------------------------------------------------------------

def classify_knn(text: str) -> Tuple[List[str], float, bool]:
    """
    Classifica il testo tramite votazione k-NN sui vettori del database.

    Algoritmo:
    1. Embeddare la query con nomic-embed-text, normalizzare L2.
    2. Cercare i k vicini piu' prossimi (distanza L2 equiv. coseno su vettori norm.).
    3. Contare i voti per dominio dai k risultati.
    4. Determinare mono-dominio o ibrido in base alle soglie configurate.

    Condizione per attivare la pipeline ibrida (entrambe necessarie):
    - second_votes >= knn_min_abs_votes   (es. >= 3 su 10)
    - second_votes / (top + second) >= knn_min_vote_ratio   (es. >= 30%)

    Args:
        text: query dell'utente in linguaggio naturale.

    Returns:
        Tuple[List[str], float, bool]:
            - List[str]: 1 dominio (mono) o 2 domini (ibrido, ordinati per voti).
            - float: confidence = top_votes / k (ratio voti dominio primario).
            - bool: True se il sistema ha risposto; False -> main.py attiva keyword fallback.
    """
    k         = config.SEMANTIC_SETTINGS.get('knn_k',              _DEFAULT_K)
    min_ratio = config.SEMANTIC_SETTINGS.get('knn_min_vote_ratio', _DEFAULT_MIN_VOTE_RATIO)
    min_votes = config.SEMANTIC_SETTINGS.get('knn_min_abs_votes',  _DEFAULT_MIN_ABS_VOTES)
    model     = config.SEMANTIC_SETTINGS['embedding_model']

    # Verifica disponibilita' del DB
    table = _get_table()
    if table is None:
        print("WARN VectorStore non disponibile. Attivazione fallback a keyword.")
        return ['general'], 0.0, False

    # Embedding della query
    query_vec = _embed(text, model)
    if query_vec is None:
        return ['general'], 0.0, False

    query_vec_norm = l2_normalize(query_vec)

    # Ricerca k-NN — nativa LanceDB, senza dipendenza da pandas
    try:
        results = table.search(query_vec_norm).limit(k).to_list()
    except Exception as e:
        print(f"WARN VectorStore: ricerca k-NN fallita -> {e}")
        return ['general'], 0.0, False

    if not results:
        return ['general'], 0.0, False

    # Conteggio voti per dominio iterando sulla lista di dizionari nativa
    vote_counts: Dict[str, int] = {}
    for row in results:
        domain_val = row['domain']
        vote_counts[domain_val] = vote_counts.get(domain_val, 0) + 1

    ranked        = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
    top_domain,   top_votes   = ranked[0]
    second_domain             = ranked[1][0] if len(ranked) > 1 else None
    second_votes              = ranked[1][1] if len(ranked) > 1 else 0

    # confidence: ratio voti del dominio primario sul totale estratto
    total_results = len(results)
    confidence    = top_votes / total_results if total_results > 0 else 0.0

    # Logica ibrida con doppia condizione
    combined = top_votes + second_votes
    domains  = [top_domain]

    if (second_domain is not None
            and second_votes >= min_votes
            and combined > 0
            and (second_votes / combined) >= min_ratio):
        domains.append(second_domain)

    # Debug output
    if config.SEMANTIC_SETTINGS.get('debug', False):
        print(f"\n   [k-NN DEBUG] Voti: { {d: v for d, v in ranked} }")
        print(f"   [k-NN DEBUG] Domini={domains} | Confidence={confidence:.2f} "
              f"| k={k} | min_votes={min_votes} | min_ratio={min_ratio}")
        if second_domain:
            ratio_str = f"{second_votes}/{combined} = {second_votes/combined:.2f}" if combined else "N/A"
            print(f"   [k-NN DEBUG] Secondo dominio '{second_domain}': "
                  f"voti={second_votes}, ratio={ratio_str}, "
                  f"ibrido={'SI' if len(domains) > 1 else 'NO'}")

    return domains, confidence, True


# ---------------------------------------------------------------------------
# ENTRY POINT — Ricostruzione forzata
# ---------------------------------------------------------------------------
# Eseguire `python vector_store.py` per sincronizzare il DB dopo aver
# modificato INTENT_SENTENCES. Elimina la tabella esistente e la ricrea.

if __name__ == "__main__":
    print("Ricostruzione forzata del Vector Store in corso...")
    print(f"   DB path: {DB_PATH}\n")

    try:
        _db = lancedb.connect(DB_PATH)
        if TABLE_NAME in _db.table_names():
            _db.drop_table(TABLE_NAME)
            print(f"   OK  Tabella '{TABLE_NAME}' rimossa.\n")
        else:
            print(f"   INFO Tabella '{TABLE_NAME}' non presente — sara' creata da zero.\n")
    except Exception as _e:
        print(f"   WARN Impossibile rimuovere la tabella esistente: {_e}")
        print("      Tento comunque la ricostruzione con mode='overwrite'...\n")

    # Resetta il riferimento globale per forzare il percorso di build
    _table = None

    ok = initialize_store()
    sys.exit(0 if ok else 1)
