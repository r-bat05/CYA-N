"""
    VECTOR STORE V1.1 — LanceDB k-NN Engine

    Novita' V1.1:
    - [TUNING] Aggiunte 4 frasi anti-trappola a INTENT_SENTENCES per ancorare
      il k-NN su query edge-case identificate durante lo stress test:
      * CODING: "promise/async-await JS" e "server log Linux con validita' probatoria"
      * MATH:   "Newton-Raphson in Python per radici di polinomio"
      * RIGHTS: "formula matematica esatta stabilita dalla legge per TFR"
      Queste frasi coprono i casi in cui termini ambigui ("formula", "calcola",
      "tribunale") distorcevano il vicinato k-NN verso il dominio sbagliato.

    V1.0 — LanceDB k-NN Engine:
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
    - knn_min_abs_votes  : voti assoluti minimi (es. >= 4 su 10 da V6.3.1)
    - knn_min_vote_ratio : % voti su combinato top+second (es. >= 30%)
    Questo azzera i falsi positivi perché un secondo dominio con pochi voti non
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
    IMPORTANTE: dopo ogni modifica a INTENT_SENTENCES eseguire
    `python vector_store.py` per ricostruire il DB su disco.
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

_DEFAULT_K              = 10
_DEFAULT_MIN_VOTE_RATIO = 0.30
_DEFAULT_MIN_ABS_VOTES  = 3

_table = None


# ---------------------------------------------------------------------------
# INTENT SENTENCES
# ---------------------------------------------------------------------------

INTENT_SENTENCES: Dict[str, List[str]] = {
    'coding': [
        # --- Basi di Programmazione e Scripting ---
        "Scrivi il codice sorgente per eseguire questa operazione.",
        "Fammi un programma in Python che automatizza questo processo.",
        "Come si scrive questa funzione in JavaScript o TypeScript?",
        "Sviluppa uno script che elabora e trasforma questi file di testo.",
        "Mostrami come implementare una hashmap o un dizionario in codice.",
        "Scrivi una classe orientata agli oggetti con ereditarietà e polimorfismo.",
        "Qual è la differenza tra passaggio di parametri per valore e per riferimento?",
        "Spiega le differenze tra let, const e var in JavaScript.",
        "Crea una regular expression (regex) per validare un indirizzo email o un URL.",
        "Come utilizzo i puntatori e l'allocazione dinamica della memoria in C++?",
        "Spiegami la differenza tra multithreading e programmazione asincrona.",
        "Come avvio un thread o un processo separato in Java o C#?",
        "Come si usa il costrutto switch-case per valutare molteplici clausole all'interno di un codice in C#?",
        
        # --- Frontend e Web Development ---
        "Crea un componente React che gestisce uno stato globale usando la Context API.",
        "Come si centra un div verticalmente e orizzontalmente usando CSS Flexbox o Grid?",
        "Scrivi una funzione JavaScript per manipolare il DOM e aggiungere un elemento HTML.",
        "Spiegami il ciclo di vita di un componente in Vue.js o React.",
        "Implementa un hook personalizzato in React per gestire il fetch dei dati.",
        "Come configuro Webpack e Babel per un progetto di frontend moderno?",
        "Gestisci gli eventi di click e hover del mouse in un file TypeScript.",
        "Scrivi il codice per un'animazione CSS fluida usando i keyframes.",
        "Come faccio a passare i props da un componente padre a un figlio in React?",
        "Implementa il routing lato client per una single page application usando React Router.",
        "Spiegami come funziona il Virtual DOM rispetto al DOM reale del browser.",
        "Implementa il caricamento di un file (upload) tramite un form HTML FormData.",
        
        # --- Backend, API e Server ---
        "Spiegami la differenza tra promise e async/await in JavaScript con un esempio pratico di codice.",
        "Crea un server backend usando Node.js e il framework Express.",
        "Come gestisco l'autenticazione tramite token JWT in un'API REST?",
        "Scrivi un endpoint in Django o Flask che accetta richieste POST in formato JSON.",
        "Implementa un middleware in Python per il logging delle richieste HTTP.",
        "Spiegami le differenze principali tra un'architettura API RESTful e GraphQL.",
        "Codice Java per creare un'applicazione Spring Boot con un controller REST.",
        "Risolvi l'errore CORS (Cross-Origin Resource Sharing) quando il frontend chiama il backend.",
        "Come si implementa la paginazione dei risultati in un endpoint API?",
        "Scrivi un server WebSocket in Python per abilitare una chat in tempo reale.",
        "Qual è il modo migliore per gestire le variabili d'ambiente in un progetto backend?",
        "Codice per effettuare una chiamata HTTP GET usando la libreria requests in Python.",
        "Come estraggo dati da una pagina HTML facendo web scraping con BeautifulSoup o Puppeteer?",
        "Codice sorgente per inviare un'email tramite protocollo SMTP usando Python.",
        
        # --- Database e SQL ---
        "Scrivi una query SQL con costrutti INNER JOIN e GROUP BY.",
        "Come creo un indice su una tabella PostgreSQL per ottimizzare i tempi di lettura?",
        "Spiega la differenza strutturale tra un database relazionale SQL e uno NoSQL come MongoDB.",
        "Scrivi il codice per connettere in modo sicuro un'app Python a un database MySQL.",
        "Implementa una migrazione dello schema del database usando Entity Framework.",
        "Crea uno schema Mongoose per salvare documenti e oggetti JSON in MongoDB.",
        "Scrivi una stored procedure e un trigger in SQL Server.",
        "Come evito la vulnerabilità di SQL injection quando passo parametri utente a una query?",
        "Usa un ORM come SQLAlchemy o Prisma per fare una query sul database senza scrivere SQL.",
        "Spiega come gestire le transazioni ACID e i lock per evitare problemi di concorrenza in database.",
        "Qual è il modo corretto di chiudere una connessione al database per evitare connection leak?",
        
        # --- DevOps, Git, Docker e OS ---
        "Qual è il comando Git per fare il merge di un branch ed evitare un fast-forward?",
        "Spiegami passo passo come risolvere un merge conflict su GitHub o GitLab.",
        "Scrivi un file Dockerfile per containerizzare un'applicazione Node.js in produzione.",
        "Scrivi uno script in Bash che cancelli in modo sicuro i file di log da terminale.",
        "Configura una pipeline di CI/CD per il deploy automatico usando GitHub Actions.",
        "Quali sono i comandi per fermare e riavviare un demone systemd in Linux?",
        "Spiega la differenza prestazionale tra un container Docker e una macchina virtuale.",
        "Scrivi uno script PowerShell per rinominare file in massa all'interno di una cartella.",
        "Quali comandi devo usare per modificare i permessi dei file in Linux usando chmod e chown?",
        "Come faccio un rebase interattivo dei miei commit in un repository Git?",
        "Scrivimi un file docker-compose.yml per il deploy di un server web nginx e database.",
        "Come configuro un cluster Kubernetes per gestire il bilanciamento del carico tra i pod in produzione?",
        "Scrivi la configurazione per usare Nginx come reverse proxy per un'app backend.",
        "Come configuro un server di log in Linux per far sì che i file generati abbiano validità probatoria incontestabile in tribunale?",
        
        # --- Architettura, Design Patterns e Sicurezza ---
        "Implementa il design pattern Singleton thread-safe in Java.",
        "Scrivi un esempio del pattern Observer o Pub-Sub per gestire eventi disaccoppiati.",
        "Qual è la differenza tra un'architettura software a microservizi e un'applicazione monolite?",
        "Spiegami i principi SOLID applicati nella programmazione orientata agli oggetti.",
        "Scrivi il codice per implementare l'inversione di controllo o dependency injection.",
        "Come strutturo le cartelle di un progetto seguendo rigorosamente l'architettura MVC?",
        "Implementa il pattern Factory Method per la creazione dinamica di istanze di oggetti.",
        "Come criptare in modo sicuro una password usando bcrypt prima di salvarla nel database?",
        "Scrivi uno smart contract in Solidity per creare un token ERC20 sulla blockchain.",
        "Come sviluppo un'applicazione mobile nativa cross-platform utilizzando Flutter e Dart?",
        
        # --- Algoritmi e Strutture Dati (Puro Codice, zero Math) ---
        "Scrivi il codice in C++ per invertire una stringa di testo senza usare librerie esterne.",
        "Implementa una struttura dati coda (queue) utilizzando due stack in Java.",
        "Codice Python per eseguire la ricerca binaria in un array ordinato.",
        "Scrivi un algoritmo di ordinamento Array come Bubble Sort o Quick Sort in C.",
        "Come si itera su un dizionario in Python per stampare tutte le chiavi e i valori?",
        "Implementa una lista concatenata singola (linked list) con metodi di inserimento e rimozione dei nodi.",
        "Scrivi una funzione ricorsiva per attraversare le directory e sottocartelle del file system.",
        "Come faccio il parsing di argomenti da riga di comando passati a uno script Python?",
        "Scrivi un generatore custom o un iteratore in Python usando il costrutto yield.",
        "Implementa un albero binario di ricerca e scrivi un metodo iterativo per visitarne i nodi.",
        
        # --- Debugging, Errori e Testing ---
        "Correggi questo bug nel codice sorgente e rimuovi gli errori di compilazione.",
        "Come faccio il debug di questa eccezione o runtime error nel mio programma?",
        "Scrivi uno unit test in Python utilizzando la libreria pytest o unittest.",
        "Come faccio il mock di una dipendenza esterna o un'API nei test scritti in JavaScript con Jest?",
        "Cosa significa 'Segmentation fault' e come lo risolvo analizzando i puntatori in C?",
        "Spiegami come leggere correttamente uno stack trace per rintracciare un'eccezione in Java.",
        "Spiegami come funziona il garbage collector in Java e come interviene l'algoritmo per prevenire i memory leak.",
        "Come trovo e risolvo un memory leak in un'applicazione Node.js in produzione?",
        "Aggiungi blocchi try-catch-finally per gestire in sicurezza le eccezioni in questo blocco di codice.",
        "Configura ESLint e Prettier in package.json per formattare automaticamente il codice sorgente."
    ],
    'math': [
        # --- Calcolo Differenziale e Analisi Matematica ---
        "Calcola il limite per x che tende a infinito di questa funzione razionale.",
        "Qual è la derivata prima e seconda di questa funzione trigonometrica?",
        "Trova l'equazione della retta tangente al grafico della funzione nel punto x0.",
        "Applica il teorema di de L'Hôpital per risolvere questa forma indeterminata 0/0.",
        "Trova gli asintoti obliqui, orizzontali e verticali di questa funzione iperbolica.",
        "Dimostra che la funzione è continua e derivabile in tutto il suo dominio di definizione.",
        "Trova i punti di massimo relativo, minimo assoluto e flesso studiando il segno della derivata.",
        "Sviluppa questa funzione in serie di Taylor o Maclaurin centrata nell'origine.",
        "Qual è il dominio di esistenza, o campo di esistenza, di questa funzione logaritmica?",
        "Studia il carattere della serie numerica usando il criterio del rapporto o della radice.",
        "Determina il raggio di convergenza e l'intervallo di questa serie di potenze.",
        "Applica il teorema di Rolle, Lagrange o Cauchy per dimostrare l'enunciato.",
        "Calcola il differenziale totale della funzione a due variabili reali.",
        "Calcola il jacobiano e la matrice hessiana per analizzare i punti critici in R2.",
        "Studia la continuità uniforme della funzione sull'intervallo chiuso e limitato.",

        # --- Calcolo Integrale ---
        "Risolvi l'integrale indefinito applicando il metodo di integrazione per parti.",
        "Calcola l'integrale definito tra zero e pi greco della funzione seno al quadrato.",
        "Usa il metodo di sostituzione per risolvere questo integrale irrazionale.",
        "Applica la scomposizione in fratti semplici per integrare la funzione razionale fratta.",
        "Calcola l'area della regione di piano compresa tra i grafici delle due parabole.",
        "Risolvi l'integrale doppio sul dominio D delimitato dalle circonferenze.",
        "Calcola l'integrale triplo passando alle coordinate sferiche o cilindriche.",
        "Determina il volume del solido di rotazione generato attorno all'asse x.",
        "Risolvi l'integrale improprio e dimostra se converge o diverge.",
        "Applica il teorema della divergenza di Gauss per calcolare il flusso del campo vettoriale.",
        "Usa il teorema di Stokes per convertire l'integrale di linea in un integrale di superficie.",

        # --- Algebra Lineare e Matrici ---
        "Calcola il determinante e la traccia di questa matrice quadrata 3x3.",
        "Trova gli autovalori e i relativi autovettori associati alla matrice fornita.",
        "Dimostra che questi vettori formano una base ortogonale per lo spazio vettoriale R3.",
        "Applica il processo di ortogonalizzazione di Gram-Schmidt a questo set di vettori linearmente indipendenti.",
        "Risolvi il sistema lineare omogeneo associato usando il metodo di eliminazione di Gauss-Jordan.",
        "Calcola il rango di questa matrice incompleta al variare del parametro k usando il teorema di Kronecker.",
        "Determina la matrice inversa usando il metodo dei cofattori o la matrice aggiunta.",
        "Verifica se la matrice è diagonalizzabile confrontando la molteplicità algebrica e geometrica.",
        "Trova il nucleo (kernel) e l'immagine di questa applicazione o trasformazione lineare.",
        "Calcola il prodotto scalare e il prodotto vettoriale tra questi vettori nello spazio euclideo.",
        "Dimostra la disuguaglianza di Cauchy-Schwarz per questo spazio pre-hilbertiano.",

        # --- Equazioni Differenziali (ODE/PDE) ---
        "Risolvi l'equazione differenziale lineare del secondo ordine a coefficienti costanti.",
        "Trova l'integrale generale dell'equazione differenziale omogenea associata.",
        "Risolvi il problema di Cauchy determinando la soluzione particolare dell'equazione.",
        "Integra l'equazione differenziale del primo ordine a variabili separabili mostrando i passaggi.",
        "Usa il metodo della variazione delle costanti per trovare la soluzione dell'ODE non omogenea.",
        "Calcola la trasformata di Laplace di questa funzione a gradino o impulso di Dirac.",
        "Dimostra l'esistenza e l'unicità della soluzione locale tramite il teorema di Picard-Lindelöf.",
        "Risolvi il sistema di equazioni differenziali lineari del primo ordine con autovalori complessi.",
        "Trova le traiettorie ortogonali di questa famiglia di curve nel piano xy.",
        "Applica il metodo di Eulero o di Runge-Kutta per l'approssimazione numerica dell'ODE.",
        "Risolvi l'equazione di Laplace in due dimensioni usando la separazione delle variabili.",
        "Calcola la serie di Fourier per questa funzione periodica definendone i coefficienti.",

        # --- Geometria Analitica, Trigonometria e Topologia ---
        "Trova l'equazione del piano passante per tre punti non allineati nello spazio cartesiano.",
        "Calcola la distanza minima tra un punto e una retta nel piano affine.",
        "Determina le coordinate del fuoco, la direttrice e l'eccentricità di questa parabola.",
        "Scrivi l'equazione canonica dell'ellisse o dell'iperbole noti i semiassi.",
        "Trasforma questa equazione cartesiana nelle equivalenti coordinate polari.",
        "Dimostra il teorema di Pitagora o i teoremi di Euclide sui triangoli rettangoli.",
        "Calcola il circumcentro, l'incentro e il baricentro di questo triangolo.",
        "Spiega il concetto di spazio topologico compatto e di connessione per archi.",
        "Dimostra che la somma degli angoli interni di un poligono convesso a n lati è (n-2)*180 gradi.",
        "Applica le formule di prostaferesi o bisezione per semplificare l'espressione goniometrica.",
        "Risolvi il triangolo qualsiasi calcolando lunghezze e angoli col teorema dei seni e del coseno.",
        "Trasforma l'espressione in seno e coseno usando le formule di addizione e sottrazione.",
        "Calcola la curvatura e la torsione di questa curva parametrizzata nello spazio.",

        # --- Probabilità, Statistica e Calcolo Combinatorio ---
        "Calcola la probabilità condizionata dell'evento A sapendo che si è verificato B col teorema di Bayes.",
        "Determina il valore atteso (media), la varianza e la deviazione standard della distribuzione.",
        "Usa il calcolo combinatorio per trovare le permutazioni semplici e le combinazioni con ripetizione.",
        "Calcola l'intervallo di confidenza al 95% per la stima della media di una popolazione normale.",
        "Enuncia e spiega il teorema del limite centrale e la legge dei grandi numeri.",
        "Costruisci la funzione di ripartizione e di densità per questa variabile aleatoria continua.",
        "Calcola il coefficiente binomiale e applica la formula per lo sviluppo del binomio di Newton.",
        "Risolvi il test d'ipotesi z calcolando il p-value e stabilendo la regione di rifiuto.",
        "Applica la distribuzione di Poisson per modellizzare la probabilità di questo evento raro.",
        "Quante sono le disposizioni semplici di n elementi presi a gruppi di k?",

        # --- Algebra Astratta, Aritmetica Modulare e Teoria dei Numeri ---
        "Dimostra per induzione matematica che questa proposizione logica è vera per ogni numero naturale n.",
        "Verifica se l'insieme fornito costituisce un gruppo abeliano rispetto all'operazione di composizione.",
        "Definisci i concetti di omomorfismo e isomorfismo tra due strutture algebriche o anelli.",
        "Applica l'algoritmo euclideo delle divisioni successive per calcolare il massimo comun divisore (MCD).",
        "Risolvi la congruenza lineare modulo m usando i principi dell'aritmetica modulare.",
        "Usa il piccolo teorema di Fermat per semplificare il calcolo di questa congruenza di potenze.",
        "Scomponi questo intero in fattori primi e calcola il risultato della funzione totiente di Eulero.",
        "Spiega la differenza assiomatica tra un anello commutativo, un dominio d'integrità e un campo.",
        "Calcola le radici complesse coniugate di questo polinomio usando la formula di De Moivre.",
        "Risolvi l'equazione diofantea lineare trovando tutte le soluzioni intere possibili.",
        "Trova la decomposizione in fratti semplici del polinomio in un campo finito di Galois.",
        "Verifica che questo polinomio sia irriducibile sui razionali usando il criterio di Eisenstein.",
        "Dimostra che i numeri primi sono infiniti usando la dimostrazione classica di Euclide.",

        # --- Logica e Dimostrazioni Pure ---
        "Dimostra per assurdo l'irrazionalità della radice quadrata del numero due.",
        "Dimostra che l'insieme dei numeri reali non è numerabile applicando l'argomento diagonale di Cantor.",
        "Spiega il paradosso del mentitore o i teoremi di incompletezza di Gödel nella logica formale.",
        "Costruisci la tavola di verità per questa espressione di logica proposizionale.",
        "Usa i quantificatori universale ed esistenziale per negare questa proposizione matematica.",

        # --- Anti-trappola e Ibridi ---
        "Quali sono gli autovalori e gli autovettori della matrice identità 3x3?",
        "Scrivi uno script Python che utilizza il metodo di Newton-Raphson per trovare le radici di un polinomio di terzo grado.",
        "Spiegami la teoria del calcolo matriciale e poi implementa il prodotto tra due matrici in Python."
    ],
    'rights': [
        # --- Diritto Costituzionale e Amministrativo ---
        "Qual è l'iter legis per l'approvazione di una legge costituzionale da parte del Parlamento?",
        "Spiegami i limiti e i presupposti per l'emanazione di un decreto legge da parte del Governo.",
        "Cosa prevede la Costituzione italiana in merito al conflitto di attribuzione tra poteri dello Stato?",
        "Quali sono le differenze tra regolamento europeo e direttiva nell'ordinamento giuridico?",
        "Come funziona il ricorso gerarchico e il ricorso al TAR nel diritto amministrativo?",
        "Quali sono le tutele previste per l'espropriazione per pubblica utilità secondo la giurisprudenza?",
        "Spiega il principio di sussidiarietà verticale e orizzontale tra Enti Locali e Stato.",
        "Quali sono i requisiti normativi per richiedere la cittadinanza italiana per residenza?",
        "Cosa si intende per riserva di legge assoluta e relativa nell'ordinamento costituzionale?",
        "Spiega la differenza tra nullità e annullabilità di un provvedimento amministrativo.",

        # --- Diritto Penale (Reati e Principi) ---
        "Spiegami la differenza tra dolo eventuale, colpa cosciente e preterintenzione nel codice penale italiano.",
        "Quali sono le esimenti o cause di giustificazione come la legittima difesa e lo stato di necessità?",
        "Cosa configura il reato di peculato rispetto alla concussione o alla corruzione per l'esercizio della funzione?",
        "Quali sono le responsabilità penali dirette dell'amministratore delegato in caso di bancarotta fraudolenta documentale?",
        "Spiega i presupposti giuridici per il reato di diffamazione a mezzo stampa o via web.",
        "Cosa prevede l'ordinamento penale per il reato di riciclaggio e autoriciclaggio di capitali illeciti?",
        "Qual è la differenza giuridica tra rapina, estorsione e furto aggravato?",
        "Come si calcola la prescrizione di un reato informatico secondo l'ordinamento penale?",
        "Cosa dice la giurisprudenza riguardo all'abuso d'ufficio dopo le recenti riforme legislative?",
        "Quali sono le pene accessorie previste dal codice penale per l'interdizione dai pubblici uffici?",
        "Spiegami il principio di irretroattività della legge penale sfavorevole e il favor rei.",
        "Cosa succede legalmente se un dipendente ruba il codice sorgente dell'azienda e lo pubblica su GitHub?",

        # --- Procedura Penale ---
        "Come funziona l'istituto del patteggiamento e in quali casi specifici non può assolutamente essere richiesto dall'imputato?",
        "Quali sono i termini e i presupposti per la richiesta di una misura cautelare in carcere o agli arresti domiciliari?",
        "Spiega il ruolo del GIP (Giudice per le Indagini Preliminari) e del GUP nell'ordinamento processuale.",
        "Come si svolge l'udienza preliminare e quali sono le formule di proscioglimento o rinvio a giudizio?",
        "Quali sono le garanzie difensive dell'indagato durante l'interrogatorio o l'arresto in flagranza?",
        "Cosa si intende per incidente probatorio e quando può essere richiesto nel processo penale?",
        "Quali requisiti giuridici devono soddisfare le intercettazioni telefoniche o ambientali per essere prove in tribunale?",

        # --- Diritto Civile (Obbligazioni, Contratti e Diritti Reali) ---
        "Quali sono gli elementi essenziali del contratto secondo l'articolo 1325 del codice civile?",
        "Spiega le differenze tra risoluzione per inadempimento, impossibilità sopravvenuta ed eccessiva onerosità.",
        "Cosa prevede la normativa civile per l'acquisto della proprietà a titolo originario tramite usucapione?",
        "Come si costituisce una servitù prediale e qual è la differenza con il diritto di superficie?",
        "Quali sono le differenze tra responsabilità contrattuale ed extracontrattuale (o aquiliana ex art. 2043)?",
        "Spiega il funzionamento della clausola penale e della caparra confirmatoria in un contratto preliminare.",
        "Quali sono le tutele per il consumatore contro le clausole vessatorie secondo il Codice del Consumo?",
        "Come funziona l'azione revocatoria e l'azione surrogatoria a tutela del creditore?",
        "Cosa prevede la legge per il contratto di mutuo ipotecario e la fideiussione bancaria?",
        "Quali sono i presupposti normativi per lo sfratto per morosità in un contratto di locazione ad uso abitativo?",
        "Cosa prevede il codice civile e il regolamento di condominio per la gestione degli animali domestici negli spazi comuni?",

        # --- Diritto di Famiglia e Successioni ---
        "Qual è la procedura legale per la separazione consensuale e il divorzio breve in Italia?",
        "Quale formula o metodo di calcolo prevede la giurisprudenza italiana per l'adeguamento ISTAT degli assegni di mantenimento?",
        "Cosa stabilisce l'ordinamento in merito all'affidamento condiviso e alla responsabilità genitoriale?",
        "Spiegami come si calcolano matematicamente le quote di legittima e la quota disponibile in una complessa successione ereditaria.",
        "Quali sono le differenze tra testamento olografo, pubblico e segreto nel codice civile?",
        "Come funziona l'accettazione dell'eredità con beneficio d'inventario e la rinuncia all'eredità?",
        "Cosa si intende per collazione e azione di riduzione a tutela degli eredi legittimari?",
        "Spiega l'istituto dell'amministrazione di sostegno e le differenze con interdizione e inabilitazione.",

        # --- Procedura Civile ---
        "Quali sono i termini per proporre opposizione a decreto ingiuntivo?",
        "Spiega la differenza tra competenza per territorio, per materia e per valore del tribunale.",
        "Cosa si intende per litisconsorzio necessario e facoltativo nel processo civile?",
        "Come si articola l'esecuzione forzata, il precetto e il pignoramento immobiliare presso terzi?",
        "Quali sono i motivi per presentare ricorso in Corte di Cassazione in ambito civile?",

        # --- Diritto del Lavoro ---
        "Quali sono le tutele legali previste dallo Statuto dei Lavoratori contro il licenziamento ritenuto discriminatorio?",
        "Spiega la differenza tra licenziamento per giusta causa e giustificato motivo oggettivo o soggettivo.",
        "Quali sono i diritti del lavoratore subordinato in tema di ferie, permessi retribuiti e malattia lavorativa?",
        "Cosa prevede la giurisprudenza in merito al mobbing, al bossing e al demansionamento sul luogo di lavoro?",
        "Come funziona il sistema di tutele INAIL per l'infortunio sul lavoro o l'infortunio in itinere?",

        # --- Diritto Societario, Commerciale e Tributario ---
        "Quali sono le differenze di responsabilità patrimoniale tra i soci di una S.r.l. e quelli di una S.n.c.?",
        "Spiega il funzionamento del patto parasociale e le maggioranze in assemblea per le Società per Azioni (S.p.A.).",
        "Quali sono i presupposti normativi per la dichiarazione di fallimento o liquidazione giudiziale di una società commerciale?",
        "Come si compila e si presenta legalmente il modello F24 per pagare le imposte sui redditi all'Agenzia delle Entrate?",
        "Cosa si intende per elusione fiscale e abuso del diritto nel contenzioso tributario italiano?",
        "Spiega le norme dell'Antitrust in materia di concorrenza sleale e abuso di posizione dominante.",
        "Come si quantificano gli interessi di mora su un debito commerciale scaduto secondo le direttive europee?",

        # --- GDPR, Privacy e Diritto delle Nuove Tecnologie ---
        "Quali sono i compiti legali del Titolare del Trattamento e del DPO (Data Protection Officer) secondo il GDPR?",
        "Cosa prevede la normativa europea per la notifica di un data breach al Garante per la Protezione dei Dati Personali?",
        "Come si esercita il diritto all'oblio e la portabilità dei dati ai sensi della normativa privacy vigente?",
        "Il web scraping di un sito pubblico viola le leggi sul diritto d'autore o la direttiva sul copyright?",
        "Quali sono i termini legali e le condizioni standard per la licenza d'uso di un software open source proprietario?",

        # --- Diritto Sportivo ---
        "Quali sono le sanzioni previste dal Codice di Giustizia Sportiva per la violazione del principio di lealtà sportiva?",
        "Spiega il funzionamento del DASPO (Divieto di Accedere alle manifestazioni Sportive) e i poteri del Questore.",
        "Cosa prevede la normativa sul vincolo sportivo e il tesseramento degli atleti dilettanti o professionisti?",
        "Come si articola il ricorso al Tribunale Arbitrale dello Sport (TAS/CAS) di Losanna?",
        "Qual è la procedura per l'omologazione del risultato e la responsabilità oggettiva della società sportiva?",
        "Spiega la normativa WADA e i regolamenti del Tribunale Nazionale Antidoping (TNA).",

        # --- Anti-Trappola ed Edge Cases (Formule dettate dalla legge) ---
        "Qual è la formula matematica esatta stabilita dalla legge per calcolare il TFR netto di un lavoratore dipendente?",
        "Come si quantifica matematicamente il danno biologico permanente usando le tabelle del Tribunale di Milano?",
        "Qual è il calcolo numerico esatto per la ripartizione millesimale delle spese per il rifacimento del tetto condominiale?",
        "Sviluppa uno script in Bash che cancelli in modo sicuro i file di database per rispettare il diritto all'oblio imposto dal GDPR.",
        "Quali clausole contrattuali automatiche prevede la legge civile per l'inadempimento di uno smart contract in Solidity?"
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
        # --- Ricette e cucina ---
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
    - second_votes >= knn_min_abs_votes   (es. >= 4 su 10 da V6.3.1)
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

    table = _get_table()
    if table is None:
        print("WARN VectorStore non disponibile. Attivazione fallback a keyword.")
        return ['general'], 0.0, False

    query_vec = _embed(text, model)
    if query_vec is None:
        return ['general'], 0.0, False

    query_vec_norm = l2_normalize(query_vec)

    try:
        results = table.search(query_vec_norm).limit(k).to_list()
    except Exception as e:
        print(f"WARN VectorStore: ricerca k-NN fallita -> {e}")
        return ['general'], 0.0, False

    if not results:
        return ['general'], 0.0, False

    vote_counts: Dict[str, int] = {}
    for row in results:
        domain_val = row['domain']
        vote_counts[domain_val] = vote_counts.get(domain_val, 0) + 1

    ranked        = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
    top_domain,   top_votes   = ranked[0]
    second_domain             = ranked[1][0] if len(ranked) > 1 else None
    second_votes              = ranked[1][1] if len(ranked) > 1 else 0

    total_results = len(results)
    confidence    = top_votes / total_results if total_results > 0 else 0.0

    combined = top_votes + second_votes
    domains  = [top_domain]

    if (second_domain is not None
            and second_votes >= min_votes
            and combined > 0
            and (second_votes / combined) >= min_ratio):
        domains.append(second_domain)

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

    _table = None

    ok = initialize_store()
    sys.exit(0 if ok else 1)
