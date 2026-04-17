"""
    DATABASE QUERY — Frasi di training per il Vector Store.

    Novità V2.1:
    - [FIX] Aggiunte frasi math su teoria dei segnali (Nyquist-Shannon, DFT, Fourier)
      e metodi Monte Carlo / convergenza stocastica. Queste aree erano scoperte,
      causando score math troppo bassi (<3.0) su query ibride MATH->CODING e
      mancata attivazione della pipeline.
    - [FIX] Aggiunte frasi bridge ('coding','math') per FFT/campionamento e Monte Carlo.

    Novità V2.0:
    - [P3] Rimossi tutti i cloni manuali ("Trucco del Clone") dai domini.
      Le frasi bridge erano duplicate fisicamente in ogni dominio coinvolto,
      causando debito tecnico e rischio di desincronizzazione.
    - [P3] Aggiunto BRIDGE_SENTENCES: Dict[Tuple[str, str], List[str]].
      Ogni coppia di domini mappa alle frasi condivise. vector_store.py
      le itera, le embeda UNA SOLA VOLTA e crea record per entrambi i domini.
      Questo garantisce un'unica sorgente di verità per le frasi di confine.
"""

from typing import Dict, List, Tuple

# =============================================================================
# INTENT_SENTENCES — Frasi mono-dominio (nessun clone di bridge)
# =============================================================================

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
        "Sviluppa un modulo riutilizzabile in Python seguendo le best practice di packaging.",
        "Implementa un sistema di gestione delle eccezioni personalizzate in Ruby.",

        # Cloud, Serverless, Mobile, Game Dev
        "Come si configura una funzione serverless su AWS Lambda con Node.js usando il framework Serverless?",
        "Come si effettua il deploy di un'applicazione containerizzata su Google Cloud Run o AWS ECS?",
        "Spiegami l'architettura event-driven su cloud con AWS SQS, SNS e Lambda.",
        "Come si gestisce lo stato in un'app Flutter usando Riverpod o il pattern BLoC?",
        "Scrivi il codice Kotlin per effettuare chiamate di rete asincrone usando le coroutine di Android.",
        "Come si ottimizza un'app Android nativa per ridurre il consumo di batteria in background?",
        "Quali design pattern si usano per strutturare l'architettura di un videogioco in Unity con C#?",
        "Come si implementa il raycasting in un motore 3D usando WebGL o OpenGL?",
        "Come si configura un ambiente di test End-to-End con Cypress o Playwright per un'app web?",

        # --- Manipolazione Base dei Dati ---
        "Scrivi una funzione Python che ordina una lista di dizionari in base al valore di una chiave specifica.",
        "Come si filtra una lista in Python usando una list comprehension o la funzione filter?",
        "Scrivi il codice per iterare su tutti i valori di un dizionario Python e stamparne le chiavi.",
        "Come si rimuovono i duplicati da una lista Python preservando l'ordine originale degli elementi?",
        "Implementa una funzione che raggruppa una lista di oggetti per un attributo comune in Python.",
        "Come si accede e si modifica il valore di una chiave specifica all'interno di un dizionario annidato?",
        "Scrivi il codice per unire due liste di dizionari Python usando una chiave comune come identificatore.",
        "Come si ordina un array di stringhe in ordine alfabetico inverso in JavaScript?",
        "Implementa una funzione per trovare e restituire tutti gli elementi duplicati in una lista Python.",
        "Come si converte una lista di tuple in un dizionario Python?",

        # --- Calcolo Numerico e Ricerca Operativa (Implementazione) ---
        "Scrivi uno script Python che utilizza il metodo di Newton-Raphson per trovare le radici di un polinomio.",
        "Implementa l'algoritmo del simplesso in C++ per risolvere problemi di programmazione lineare.",
        "Codice per calcolare la fattorizzazione LU di una matrice sparsa di grandi dimensioni.",
        "Sviluppa una funzione per l'integrazione numerica usando il metodo di Simpson o dei trapezi.",
        "Implementa un algoritmo di ottimizzazione genetica per risolvere il problema del commesso viaggiatore.",
        "Scrivi uno script per la risoluzione numerica di equazioni differenziali col metodo di Runge-Kutta.",
        "Codice per implementare la Trasformata di Fourier Veloce (FFT) in Java senza librerie esterne.",
        "Sviluppa un simulatore Monte Carlo per modellare processi stocastici in Python.",
        "Implementa l'algoritmo di Dijkstra per trovare il cammino minimo in un grafo pesato.",
        "Scrivi il codice per risolvere un sistema di equazioni lineari usando il metodo di Jacobi o Gauss-Seidel.",
        "Implementa la scomposizione ai valori singolari (SVD) in codice Python per la riduzione della dimensionalità.",
        "Sviluppa un algoritmo di programmazione dinamica per ottimizzare l'allocazione delle risorse in un processo.",
        "Scrivi il codice sorgente per una simulazione di fluidodinamica computazionale bidimensionale.",

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
        "Sviluppa un'interfaccia utente reattiva usando Tailwind CSS e componenti Next.js.",
        "Implementa la gestione degli stati complessi in un'app React tramite Redux Toolkit.",
        "Scrivi il codice per il lazy loading delle immagini in una pagina web ad alte prestazioni.",
        "Sviluppa un'applicazione web progressiva (PWA) con Service Workers per l'accesso offline.",
        "Configura il rendering lato server (SSR) per un'applicazione frontend moderna.",

        # Fix Q3: "permessi" bleed RIGHTS
        "Come risolvere l'errore di permessi negati (permission denied) su un database PostgreSQL o MySQL da terminale Linux?",
        "Imposta i permessi corretti su file e directory Linux usando i comandi chmod, chown e chgrp da riga di comando.",
        "Come si configurano i permessi di accesso a un database per un utente specifico con GRANT e REVOKE in SQL?",

        # Fix Q18 + Q23: grafi, teoria, parsing
        "Implementa in Python un grafo orientato usando dizionari e matrici di adiacenza per mappare nodi e archi.",
        "Spiegami l'algoritmo di bilanciamento e rotazione dei nodi in un albero AVL o in un Red-Black tree.",
        "Implementa l'algoritmo di Prim o Kruskal in Python per trovare l'albero di copertura minimo di un grafo.",
        "Scrivi il codice Python per creare un grafo con NetworkX e trovare il percorso minimo tra due nodi.",
        "Come si visita un grafo in Python usando BFS e DFS su una lista di adiacenza?",
        "Implementa l'algoritmo di Prim o Kruskal in Python per trovare l'albero di copertura minimo di un grafo.",
        "Come si fa il parsing di testi con NLTK o spaCy in Python per estrarre token, lemmi e frequenze?",
        "Scrivi uno script Python per analizzare la frequenza delle parole in un corpus di testi usando Counter.",

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
        "Qual è il modo migliore per gestire le variabili d'ambiente in un progetto backend?",
        "Codice per effettuare una chiamata HTTP GET usando la libreria requests in Python.",
        "Come estraggo dati da una pagina HTML facendo web scraping con BeautifulSoup o Puppeteer?",
        "Configura una connessione gRPC tra due microservizi scritti in Go.",
        "Implementa il meccanismo di rate limiting per proteggere le tue API in Node.js.",
        "Scrivi uno script Node.js per elaborare stream di dati binari e salvarli su file.",
        "Sviluppa un sistema di code di messaggi (message broker) usando RabbitMQ o Kafka in Python.",

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
        "Configura un sistema di caching distribuito usando Redis in un'app Python.",
        "Scrivi una query MongoDB complessa usando l'aggregation framework.",
        "Implementa la logica di replica e sharding per un database Cassandra.",
        "Ottimizza lo schema del database per supportare query analitiche (OLAP) in tempo reale.",

        # --- DevOps, Git, Docker e OS ---
        "Qual è il comando Git per fare il merge di un branch ed evitare un fast-forward?",
        "Spiegami passo passo come risolvere un merge conflict su GitHub o GitLab.",
        "Scrivi un file Dockerfile per containerizzare un'applicazione Node.js in produzione.",
        "Scrivi uno script in Bash che cancelli in modo sicuro i file di log da terminale.",
        "Configura una pipeline di CI/CD per il deploy automatico usando GitHub Actions.",
        "Quali sono i comandi per fermare e riavviare un demone systemd in Linux?",
        "Spiega la differenza prestazionale tra un container Docker e una macchina virtuale.",
        "Scrivi uno script PowerShell per rinominare file in massa all'interno di una cartella.",
        "Come faccio un rebase interattivo dei miei commit in un repository Git?",
        "Scrivimi un file docker-compose.yml per il deploy di un server web nginx e database.",
        "Come configuro un cluster Kubernetes per gestire il bilanciamento del carico tra i pod in produzione?",
        "Scrivi uno script Bash per calcolare il TFR o altre voci contabili automatizzando i report.",
        "Configura un reverse proxy con Nginx per gestire il traffico SSL/TLS.",
        "Crea uno script di automazione per il backup periodico del database su Amazon S3.",
        "Sviluppa una configurazione Terraform per istanziare macchine virtuali su Azure o AWS.",
        "Scrivi uno script in Python per monitorare l'utilizzo della CPU e della memoria del server in tempo reale.",

        # --- Cybersecurity e Crittografia Applicata ---
        "Implementa l'algoritmo di crittografia RSA in Python per cifrare messaggi di testo.",
        "Scrivi il codice per generare un hash sicuro di una password usando bcrypt o argon2.",
        "Sviluppa una funzione per la verifica delle firme digitali usando chiavi asimmetriche.",
        "Codice per implementare lo scambio di chiavi Diffie-Hellman in un'app di chat.",
        "Scrivi uno script per rilevare tentativi di brute force analizzando i file di log del server.",
        "Implementa un sistema di crittografia end-to-end per la trasmissione di dati JSON.",
        "Crea una funzione JavaScript che implementa il protocollo OAuth2 per l'autorizzazione.",
        "Scrivi il codice sorgente per un generatore di token di sessione sicuri e casuali.",

        # --- ML/AI, Data Science e Automazione ---
        "Scrivi il codice per l'addestramento di una rete neurale convoluzionale usando PyTorch.",
        "Implementa un modello di regressione lineare da zero usando solo la libreria NumPy.",
        "Codice per visualizzare i risultati di un'analisi dati usando Matplotlib o Seaborn.",
        "Sviluppa una pipeline di pre-processing dei dati per pulire dataset in formato CSV.",
        "Implementa un algoritmo di clustering K-means in Python per segmentare i dati.",
        "Scrivi il codice per il fine-tuning di un modello Transformer usando la libreria HuggingFace.",
        "Crea una funzione per il calcolo della similarità coseno tra due vettori densi in Python.",
        "Sviluppa uno script per l'estrazione di feature testuali (TF-IDF) da un dataset di documenti.",

        # --- Low-Level e Sistemi Embedded ---
        "Scrivi il codice assembly per eseguire una somma tra registri in architettura x86.",
        "Sviluppa un semplice driver per il kernel Linux che scrive messaggi nel buffer di log.",
        "Implementa la gestione degli interrupt hardware in codice C per un microcontrollore Arduino.",
        "Scrivi il codice per comunicare con un sensore tramite protocollo I2C o SPI in C++.",
        "Sviluppa un gestore di memoria custom per allocare blocchi di dati a dimensione fissa.",

        # --- Debugging, Errori e Testing ---
        "Correggi questo bug nel codice sorgente e rimuovi gli errori di compilazione.",
        "Come faccio il debug di questa eccezione o runtime error nel mio programma?",
        "Scrivi uno unit test in Python utilizzando la libreria pytest o unittest.",
        "Spiegami come leggere correttamente uno stack trace per rintracciare un'eccezione in Java.",
        "Come trovo e risolvo un memory leak in un'applicazione Node.js in produzione?",
        "Aggiungi blocchi try-catch-finally per gestire in sicurezza le eccezioni in questo blocco di codice.",
        "Implementa un test di integrazione per verificare la comunicazione tra frontend e API.",
        "Scrivi il codice per il profiling delle prestazioni e l'analisi del consumo di memoria in C#.",
        "Sviluppa un sistema di mock per simulare le risposte di un servizio esterno nei test Jest.",

        # --- Edge Cases e Ibridi Complessi ---
        "Implementa un parser in Rust per estrarre le clausole contrattuali e le scadenze da un file PDF.",
        "Scrivi il codice per un motore fisico 2D che simula la gravità, l'attrito e le collisioni elastiche tra poligoni.",
        "Sviluppa uno script per automatizzare l'invio delle fatture elettroniche tramite chiamate API REST.",
        "Scrivi un programma in Go che calcola la probabilità statistica di vittoria in un gioco d'azzardo simulato.",
        "Configura un firewall iptables da riga di comando per bloccare il traffico in entrata da specifiche nazioni.",
        "Implementa la logica di un carrello e-commerce calcolando dinamicamente l'IVA e i codici sconto in JavaScript.",
        "Scrivi una macro VBA per Excel che generi un report finanziario formattato partendo da dati grezzi in CSV.",
        "Crea un bot in Python che monitora i prezzi e acquista automaticamente i biglietti per i concerti.",
        "Implementa un algoritmo di crittografia omomorfica per eseguire addizioni su dati cifrati in linguaggio C.",
        "Scrivi una query GraphQL complessa per recuperare l'albero genealogico e le relazioni di parentela di un utente.",
        "Implementa in C un simulatore fisico per il calcolo della traiettoria balistica considerando l'attrito dell'aria.",
        "Scrivi uno script in Python per simulare l'evoluzione di un automa cellulare bidimensionale come il Gioco della Vita.",
        "Sviluppa una libreria in Rust per il calcolo tensoriale e la moltiplicazione ottimizzata di matrici sparse.",
        "Codice per calcolare i frattali dell'insieme di Mandelbrot e renderizzarli su una griglia di pixel.",
        "Implementa l'algoritmo di crittografia ellittica (ECC) partendo dalle equazioni algebriche su campi finiti.",
    ],

    'math': [
        # --- Analisi Matematica 1 ---
        "Calcola il limite per x che tende a infinito di questa funzione razionale.",
        "Qual è la derivata prima e seconda di questa funzione trigonometrica?",
        "Trova l'equazione della retta tangente al grafico della funzione nel punto x0.",
        "Applica il teorema di de L'Hôpital per risolvere questa forma indeterminata 0/0.",
        "Trova gli asintoti obliqui, orizzontali e verticali di questa funzione iperbolica.",
        "Dimostra che la funzione è continua e derivabile in tutto il suo dominio di definizione.",
        "Trova i punti di massimo relativo, minimo assoluto e flesso studiando il segno della derivata.",
        "Sviluppa questa funzione in serie di Taylor o Maclaurin centrata nell'origine.",
        "Studia il carattere della serie numerica usando il criterio del rapporto o della radice.",
        "Determina il raggio di convergenza e l'intervallo di questa serie di potenze.",
        "Applica il teorema di Rolle, Lagrange o Cauchy per dimostrare l'enunciato.",
        "Determina la convergenza di una serie a termini positivi tramite il criterio del confronto asintotico.",
        "Verifica l'uniforme continuità di una funzione su un intervallo limitato tramite il teorema di Heine-Cantor.",
        "Calcola l'integrale indefinito applicando il metodo di integrazione per parti.",
        "Calcola l'integrale definito tra zero e pi greco della funzione seno al quadrato.",
        "Usa il metodo di sostituzione per risolvere questo integrale irrazionale.",
        "Applica la scomposizione in fratti semplici per integrare la funzione razionale fratta.",
        "Studia la derivabilità di una funzione definita a tratti verificando il limite del rapporto incrementale.",
        "Calcola il valore di un limite complesso utilizzando gli sviluppi asintotici di Landau (o-piccolo).",
        "Determina la classe di regolarità C^n di una funzione in un intorno di un punto critico.",

        # --- Analisi Matematica 2 e 3 ---
        "Risolvi l'integrale doppio sul dominio D delimitato dalle circonferenze.",
        "Calcola l'integrale triplo passando alle coordinate sferiche o cilindriche.",
        "Dimostra la convergenza dell'integrale improprio utilizzando i criteri del confronto.",
        "Determina il piano tangente alla superficie nel punto di coordinate fornite.",
        "Calcola il rotore e la divergenza del campo vettoriale nello spazio R3.",
        "Verifica se il campo vettoriale è conservativo trovandone il potenziale scalare.",
        "Applica il teorema di Stokes per calcolare la circuitazione lungo la curva chiusa.",
        "Usa il teorema della divergenza (Gauss) per calcolare il flusso attraverso la superficie.",
        "Trova i massimi e minimi vincolati della funzione utilizzando il metodo dei moltiplicatori di Lagrange.",
        "Calcola l'integrale di linea di prima o seconda specie lungo la curva parametrizzata.",
        "Dimostra la completezza dello spazio Lp rispetto alla norma della convergenza in media.",
        "Enuncia il teorema di rappresentazione di Riesz per i funzionali lineari in uno spazio di Hilbert.",
        "Studia la convergenza debole e forte di una successione di elementi in uno spazio di Banach.",
        "Calcola la trasformata di Fourier o di Laplace nel senso delle distribuzioni temperate.",
        "Definisci la misura di Lebesgue e spiega la differenza con l'integrale di Riemann.",
        "Determina la norma di un operatore lineare limitato tra due spazi vettoriali normati.",

        # --- Algebra Lineare e Calcolo Matriciale ---
        "Calcola il determinante e la traccia di questa matrice quadrata 3x3.",
        "Trova gli autovalori e i relativi autovettori associati alla matrice fornita.",
        "Dimostra che questi vettori formano una base ortogonale per lo spazio vettoriale R3.",
        "Applica il processo di ortogonalizzazione di Gram-Schmidt a questo set di vettori.",
        "Risolvi il sistema lineare omogeneo associato usando il metodo di eliminazione di Gauss-Jordan.",
        "Determina la matrice inversa usando il metodo dei cofattori o la matrice aggiunta.",
        "Verifica se la matrice è diagonalizzabile confrontando la molteplicità algebrica e geometrica.",
        "Trova il nucleo (kernel) e l'immagine di questa applicazione o trasformazione lineare.",
        "Calcola il prodotto matriciale tra matrici non quadrate e verificane la compatibilità dimensionale.",
        "Determina il rango di una matrice al variare di un parametro reale tramite il teorema di Kronecker.",
        "Applica la decomposizione QR o la scomposizione ai valori singolari (SVD) a una matrice rettangolare.",
        "Risolvi un sistema lineare sovradeterminato utilizzando il metodo dei minimi quadrati.",
        "Verifica se una forma quadratica è definita positiva analizzando i segni dei minori principali (Criterio di Sylvester).",
        "Calcola la matrice di passaggio tra due basi diverse dello stesso spazio vettoriale.",
        "Dimostra che il prodotto di due matrici ortogonali è ancora una matrice ortogonale.",

        # --- Geometria ---
        "Trova l'equazione del piano passante per tre punti non allineati nello spazio cartesiano.",
        "Determina le coordinate del fuoco, la direttrice e l'eccentricità di questa parabola.",
        "Trasforma questa equazione cartesiana nelle equivalenti coordinate polari.",
        "Calcola la distanza minima tra un punto e una retta o tra due piani sghembi.",
        "Studia la classificazione delle coniche nel piano proiettivo utilizzando la matrice associata.",
        "Determina le coordinate omogenee di un punto all'infinito (punto improprio) nel piano.",
        "Calcola la curvatura gaussiana e la curvatura media di una superficie parametrizzata.",
        "Trova le geodetiche su una superficie di rotazione applicando le equazioni di Eulero-Lagrange.",
        "Spiega la dualità tra punti e rette nel contesto della geometria proiettiva.",
        "Determina l'area di un triangolo sferico utilizzando il teorema di Gauss-Bonnet.",
        "Verifica se due rette nello spazio sono parallele, incidenti o sghembe.",

        #Topologia e Geometria Differenziale
        "Definisci gli insiemi aperti, chiusi e gli intorni in uno spazio topologico generale.",
        "Spiega le proprietà degli spazi di Hausdorff e la separabilità in topologia generale.",
        "Dimostra che ogni spazio metrico è uno spazio topologico di Hausdorff.",
        "Definisci il concetto di compattezza e enuncia il teorema di Heine-Borel per sottoinsiemi di R^n.",
        "Spiega la connessione per archi e la connessione topologica con esempi in spazi metrici.",
        "Definisci una varietà differenziabile e lo spazio tangente in un punto nella geometria differenziale.",
        "Calcola la curvatura di Gauss e la curvatura media di una superficie parametrizzata.",
        "Enuncia il teorema di colorazione dei grafi planari e il relativo argomento combinatorio.",

        # --- Probabilità e Statistica ---
        "Calcola la probabilità condizionata dell'evento A sapendo che si è verificato B col teorema di Bayes.",
        "Determina il valore atteso (media), la varianza e la deviazione standard della distribuzione.",
        "Calcola l'intervallo di confidenza al 95% per la stima della media di una popolazione normale.",
        "Enuncia e spiega il teorema del limite centrale e la legge dei grandi numeri.",
        "Costruisci la funzione di ripartizione e di densità per questa variabile aleatoria continua.",
        "Risolvi il test d'ipotesi z o t-test calcolando il p-value e stabilendo la regione di rifiuto.",
        "Spiega la differenza teorica tra la distribuzione di Poisson e la distribuzione binomiale.",
        "Determina l'efficienza di uno stimatore calcolando il limite inferiore di Cramér-Rao.",
        "Esegui un test del chi-quadrato per verificare l'indipendenza tra due variabili categoriche.",
        "Calcola la retta di regressione lineare minimizzando la somma dei quadrati dei residui.",
        "Definisci la funzione caratteristica di una variabile aleatoria e spiegane l'utilità nei calcoli.",

        # --- Equazioni Differenziali e Fisica Matematica ---
        "Risolvi l'equazione differenziale lineare del secondo ordine a coefficienti costanti.",
        "Trova l'integrale generale dell'equazione differenziale omogenea associata.",
        "Risolvi il problema di Cauchy determinando la soluzione particolare dell'equazione.",
        "Integra l'equazione differenziale del primo ordine a variabili separabili mostrando i passaggi.",
        "Calcola la trasformata di Laplace di questa funzione a gradino o impulso di Dirac.",
        "Studia la stabilità dei punti di equilibrio di un sistema dinamico lineare tramite gli autovalori.",
        "Risolvi l'equazione del calore o delle onde utilizzando il metodo di separazione delle variabili.",
        "Determina la soluzione di un'equazione differenziale esatta trovandone il fattore integrante.",

        # --- Logica, Algebra Astratta e Teoria dei Numeri ---
        "Dimostra per induzione matematica che questa proposizione logica è vera per ogni naturale n.",
        "Dimostra per assurdo l'irrazionalità della radice quadrata del numero due.",
        "Dimostra che l'insieme dei numeri reali non è numerabile applicando l'argomento diagonale di Cantor.",
        "Spiega il teorema di incompletezza di Gödel e perché ha sconvolto i fondamenti della logica formale.",
        "Applica l'algoritmo euclideo delle divisioni successive per calcolare il massimo comun divisore.",
        "Risolvi la congruenza lineare modulo m usando i principi dell'aritmetica modulare.",
        "Verifica se l'insieme fornito costituisce un gruppo abeliano rispetto all'operazione data.",
        "Definisci i concetti di omomorfismo e isomorfismo tra due strutture algebriche o anelli.",

        # --- Teoria dei Segnali, Trasformate e Campionamento [V2.1 NEW] ---
        "Enuncia il teorema di Nyquist-Shannon e calcola la frequenza minima di campionamento per un segnale a banda limitata.",
        "Spiega la teoria matematica della trasformata di Fourier discreta (DFT) e la sua relazione con la DFT continua.",
        "Analizza matematicamente la convergenza della serie di Fourier per funzioni periodiche discontinue (fenomeno di Gibbs).",
        "Calcola la risposta in frequenza di un filtro passa-basso ideale usando la trasformata di Fourier.",
        "Dimostra matematicamente il teorema di Parseval per le serie di Fourier e l'uguaglianza delle norme L2.",
        "Dimostra il teorema del campionamento di Shannon e ricava la formula di ricostruzione tramite sinc interpolation.",
        "Calcola lo spettro di frequenze di un segnale periodico applicando la serie di Fourier complessa.",
        "Spiega la relazione matematica tra trasformata di Fourier, trasformata Z e trasformata di Laplace.",
        "Analizza il fenomeno dell'aliasing matematicamente e determina la condizione per evitarlo.",
        "Dimostra la proprietà di convoluzione della trasformata di Fourier e le sue implicazioni per i filtri lineari.",
        "Calcola la trasformata di Fourier di un segnale rettangolare e interpreta il risultato nel dominio delle frequenze.",
        "Spiega il principio di indeterminazione di Heisenberg nella formulazione matematica di Fourier.",

        # --- Metodi Stocastici, Monte Carlo e Convergenza [V2.1 NEW] ---
        "Analizza la velocità di convergenza del metodo Monte Carlo usando il teorema del limite centrale.",
        "Dimostra matematicamente perché la varianza dell'estimatore Monte Carlo decresce come 1/N al crescere dei campioni.",
        "Calcola l'errore statistico atteso di una stima Monte Carlo in funzione del numero di campioni N e della varianza.",
        "Spiega la teoria matematica dei processi di Markov e la convergenza alla distribuzione stazionaria.",
        "Analizza la complessità statistica del metodo di integrazione Monte Carlo rispetto ai metodi deterministici di quadratura.",
        "Dimostra la consistenza e la non distorsione dello stimatore della media campionaria con la legge dei grandi numeri.",
        "Calcola l'intervallo di confidenza per una stima Monte Carlo dell'integrale di una funzione multivariata.",
        "Spiega il metodo di importance sampling e come riduce matematicamente la varianza dell'estimatore Monte Carlo.",
        "Analizza la convergenza del metodo di campionamento MCMC (Markov Chain Monte Carlo) in termini di mixing time.",
        "Dimostra matematicamente l'errore di quadratura del metodo Monte Carlo rispetto al metodo dei trapezi compositi.",

        # --- Anti-trappola ed Edge Cases ---
        "Quali sono gli autovalori e gli autovettori della matrice identità 3x3?",
        "Descrivi la teoria del calcolo matriciale necessaria per definire un prodotto tra tensori.",
        "Spiegami la derivazione matematica della formula del TFR stabilita dalla normativa.",
        "Analizza la struttura logica e le equazioni necessarie per descrivere un algoritmo di ricerca.",

        # --- Ibridi Complessi ---
        "Dimostra la correttezza formale dell'algoritmo di ordinamento QuickSort tramite il principio di induzione.",
        "Calcola il valore atteso e la varianza teorica del lancio simultaneo di due dadi truccati.",
        "Spiega il modello matematico di Black-Scholes e la sua equazione differenziale per la valutazione dei derivati finanziari.",
        "Analizza la topologia di una rete neurale artificiale dal punto di vista degli spazi metrici e normati.",
        "Trova le soluzioni del sistema di equazioni differenziali non lineari che modella l'andamento di un'epidemia virale.",
        "Dimostra la disuguaglianza isoperimetrica per le curve piane semplici, chiuse e di classe C1.",
        "Spiega la teoria matematica dei giochi e l'equilibrio di Nash applicati al dilemma del prigioniero.",
        "Calcola il limite teorico di compressione di una stringa di dati secondo la formula dell'entropia di Shannon.",
        "Analizza la distribuzione asintotica dei numeri primi utilizzando la funzione zeta di Riemann e il prolungamento analitico.",
        "Determina la metrica di similarità ottimale per calcolare la distanza matematica tra due sequenze di DNA.",
        "Analizza la stabilità numerica e il condizionamento della matrice nel calcolo iterativo della traiettoria balistica.",
        "Spiega la teoria matematica dietro la scomposizione ai valori singolari applicata alla compressione delle immagini.",
    ],

    'rights': [
        # Giurisdizione extraterritoriale / spazio
        "Quale giurisdizione penale si applica a un reato commesso a bordo di una stazione spaziale internazionale o di un aereo?",
        "Spiega le norme di diritto internazionale sulla giurisdizione extraterritoriale per reati commessi oltre i confini nazionali.",
        
        #AI Act, DSA, Diritto Animali
        "Cosa prevede il Regolamento Europeo sull'Intelligenza Artificiale (AI Act) per i sistemi ad alto rischio?",
        "Cosa prevede il Regolamento MiCA (Markets in Crypto-Assets) sulla normativa europea per la gestione e l'emissione delle criptovalute?",
        "Quali obblighi impone il Digital Services Act (DSA) alle piattaforme online di grandi dimensioni?",
        "Spiega la disciplina del Cyber Resilience Act europeo e gli obblighi per i produttori di software.",
        "Cosa prevede la legislazione italiana sulla tutela del benessere animale e il maltrattamento (L. 189/2004)?",
        "Quali sono le sanzioni penali per il reato di maltrattamento e abbandono di animali domestici?",
        "Come si applica la normativa vigente sulla responsabilità civile del proprietario di un animale (art. 2052 c.c.)?",
        
        # --- Diritto Costituzionale e Pubblico ---
        "Qual è l'iter legis per l'approvazione di una legge costituzionale da parte del Parlamento?",
        "Spiegami i limiti e i presupposti per l'emanazione di un decreto legge da parte del Governo.",
        "Cosa prevede la Costituzione italiana in merito al conflitto di attribuzione tra poteri dello Stato?",
        "Quali sono le differenze tra regolamento europeo e direttiva nell'ordinamento giuridico?",
        "Spiega il principio di laicità dello Stato e la libertà di culto secondo la Costituzione.",
        "Quali sono le prerogative del Presidente della Repubblica in merito allo scioglimento delle Camere?",
        "Cosa si intende per riserva di legge assoluta e relativa nell'ordinamento costituzionale?",
        "Spiega il funzionamento del referendum abrogativo e il giudizio di ammissibilità della Consulta.",
        "Quali sono i diritti inviolabili dell'uomo sanciti dall'articolo 2 della Costituzione?",
        "Come funziona il sistema di giustizia costituzionale e l'accesso in via incidentale.",

        # --- Diritto Amministrativo ---
        "Come si compila e si presenta correttamente il modello F24 per pagare le imposte sui redditi all'Agenzia delle Entrate?"
        "Come funziona il ricorso gerarchico e il ricorso al TAR nel diritto amministrativo?",
        "Spiega la differenza tra nullità e annullabilità di un provvedimento amministrativo.",
        "Quali sono i requisiti normativi per richiedere la cittadinanza italiana per residenza?",
        "Cosa si intende per silenzio-assenso e silenzio-rifiuto nella pubblica amministrazione?",
        "Quali sono i presupposti giuridici per l'espropriazione per pubblica utilità?",
        "Spiega il principio di trasparenza amministrativa e il diritto di accesso agli atti (Legge 241/90).",
        "Come viene gestita la responsabilità civile della Pubblica Amministrazione verso i cittadini?",
        "Quali sono le fasi del procedimento amministrativo e l'obbligo di motivazione.",
        "Spiega la disciplina dei contratti pubblici e le procedure di gara d'appalto.",

        # --- Diritto Penale e Procedura Penale ---
        "Spiegami la differenza tra dolo eventuale, colpa cosciente e preterintenzione nel codice penale.",
        "Quali sono le esimenti o cause di giustificazione come la legittima difesa e lo stato di necessità?",
        "Quali sono le responsabilità penali dirette dell'amministratore delegato in caso di bancarotta fraudolenta.",
        "Spiega i presupposti giuridici per il reato di diffamazione a mezzo stampa o via web.",
        "Come funziona l'istituto del patteggiamento e in quali casi non può essere richiesto dall'imputato?",
        "Quali sono i termini e i presupposti per la richiesta di una misura cautelare personale.",
        "Cosa si intende per incidente probatorio e quando può essere richiesto nel processo penale?",
        "Spiega il principio di non colpevolezza fino a sentenza definitiva e il favor rei.",
        "Quali sono le differenze tra reati consumati, delitto tentato e desistenza volontaria?",
        "Cosa prevede il codice penale in merito al concorso di persone nel reato.",
        "Spiegami l'istituto della prescrizione del reato e come vengono calcolati i termini.",
        "Quali sono le pene accessorie e le misure di sicurezza previste dall'ordinamento penale?",

        # --- Diritto Civile ---
        "Quali sono gli elementi essenziali del contratto secondo l'articolo 1325 del codice civile?",
        "Spiega le differenze tra risoluzione per inadempimento, impossibilità sopravvenuta ed eccessiva onerosità.",
        "Quali sono le differenze tra responsabilità contrattuale ed extracontrattuale (art. 2043 c.c.)?",
        "Quali sono le tutele per il consumatore contro le clausole vessatorie secondo il Codice del Consumo?",
        "Cosa prevede la normativa civile per l'acquisto della proprietà tramite usucapione?",
        "Spiega il funzionamento della caparra confirmatoria e della clausola penale nei contratti.",
        "Quali sono i diritti e i doveri derivanti dal contratto di locazione ad uso abitativo?",
        "Come funziona l'azione di rivendicazione a tutela della proprietà privata?",
        "Cosa si intende per obbligazioni pecuniarie e il divieto di anatocismo.",
        "Quali sono i presupposti per la rescissione del contratto per stato di pericolo o bisogno?",

        # --- Diritto di Famiglia e Successioni ---
        "Qual è la procedura legale per la separazione consensuale e il divorzio breve in Italia?",
        "Cosa stabilisce l'ordinamento in merito all'affidamento condiviso e alla responsabilità genitoriale?",
        "Spiegami la differenza tra testamento olografo, pubblico e segreto secondo il codice civile.",
        "Cosa si intende per quota di legittima e chi sono gli eredi legittimari nella successione.",
        "Come funziona l'accettazione dell'eredità con beneficio d'inventario?",
        "Spiega l'istituto dell'amministrazione di sostegno e le differenze con l'interdizione.",
        "Quali sono le conseguenze giuridiche della comunione dei beni rispetto alla separazione dei beni?",
        "Cosa prevede la legge sulle unioni civili e le convivenze di fatto (Legge Cirinnà).",

        # --- Diritto del Lavoro ---
        "Quali sono le tutele legali previste dallo Statuto dei Lavoratori contro il licenziamento discriminatorio?",
        "Spiega la differenza tra licenziamento per giusta causa e giustificato motivo oggettivo.",
        "Quali sono i diritti del lavoratore subordinato in tema di ferie, malattia e permessi retribuiti?",
        "Cosa prevede la giurisprudenza in merito al demansionamento e al mobbing sul posto di lavoro?",
        "Come funziona la disciplina del contratto a tempo determinato e le causali di rinnovo.",
        "Quali sono gli obblighi di sicurezza sul lavoro previsti dal D.Lgs. 81/08?",

        # --- Diritto Commerciale, Societario e Tributario ---
        "Quali sono le differenze di responsabilità tra soci di una S.r.l. e quelli di una S.p.a.?",
        "Spiega il funzionamento dell'assemblea dei soci e le competenze del Consiglio di Amministrazione.",
        "Quali sono i presupposti normativi per la dichiarazione di liquidazione giudiziale (ex fallimento)?",
        "Come si articola il contenzioso tributario e quali sono i gradi di giudizio delle Commissioni Tributarie?",
        "Cosa si intende per elusione fiscale e abuso del diritto secondo la normativa vigente?",
        "Spiega la disciplina della concorrenza sleale e la tutela dei marchi e brevetti.",
        "Quali sono gli obblighi di trasparenza nei bilanci d'esercizio delle società quotate?",

        # --- Diritto Sportivo ---
        "Quali sono le sanzioni previste dal Codice di Giustizia Sportiva per la violazione della lealtà sportiva?",
        "Spiega il funzionamento del DASPO e i poteri del Questore in merito alla sicurezza negli stadi.",
        "Cosa prevede la normativa sul vincolo sportivo e il tesseramento degli atleti dilettanti.",
        "Come si articola il ricorso al Collegio di Garanzia dello Sport presso il CONI?",
        "Spiega la responsabilità oggettiva delle società sportive per il comportamento dei propri tifosi.",
        "Quali sono le norme antidoping previste dal Codice WADA e dal Tribunale Nazionale Antidoping?",

        # --- Lato rights: frasi originali Coding-Rights ---
        "Quali sono gli obblighi legali e le sanzioni del GDPR per la conservazione dei dati in un database?",
        "Cosa prevede la normativa sulla privacy per la cancellazione sicura dei file e il diritto all'oblio?",
        "Quali regole giuridiche deve rispettare un software automatizzato per elaborare dati personali?",
        "Spiega la responsabilità legale del DPO nell'architettura di un sistema informatico aziendale.",
        "Come deve essere strutturato il codice di una app per garantire la conformità alla direttiva ePrivacy?",
        "Qual è la validità probatoria e legale dei file di log generati da un server Linux in un processo?",
        "Cosa succede giuridicamente se un dipendente sottrae il codice sorgente commettendo furto intellettuale?",
        "Quali sono i termini legali e le condizioni standard per la licenza d'uso di un software?",
        "Come si applica la disciplina del diritto d'autore e del copyright al web scraping di siti web?",
        "Come si calcola la prescrizione di un reato informatico o cybercrimine secondo il codice penale?",
        "Quali clausole legali automatiche prevede il diritto civile per l'inadempimento di uno smart contract?",
        "Spiega la disciplina giuridica delle firme elettroniche (semplice, avanzata, qualificata) e del CAD.",

        # --- Lato rights: frasi originali Math-Rights ---
        "Qual è la formula matematica e legale stabilita dalla normativa italiana per calcolare il TFR netto?",
        "Come si calcola matematicamente il piano di ammortamento alla francese per un mutuo secondo la legge?",
        "Qual è il calcolo legale esatto per la ripartizione millesimale delle spese condominiali del tetto?",
        "Cosa prevede la giurisprudenza per il calcolo dell'anatocismo e degli interessi di mora sui debiti?",
        "Spiegami come si calcolano matematicamente le quote di legittima in una successione complessa.",
        "Quale metodo di calcolo numerico prevede la legge italiana per applicare l'adeguamento ISTAT agli assegni di mantenimento?",
        "Come si quantifica il danno biologico permanente usando le tabelle del Tribunale di Milano?",
        "Cosa prevede la normativa europea in merito al calcolo del TAEG nei contratti di finanziamento?",
        "Come si calcola l'imposta di registro e l'IVA per la compravendita immobiliare secondo l'erario.",
        "Quali sono i criteri legali per determinare il superamento del tasso soglia dell'usura bancaria?",

        # --- Edge Cases e Ibridi Complessi ---
        "Di chi è la responsabilità civile e penale se un bot di trading algoritmico autonomo causa un crac finanziario?",
        "Come si applica il diritto fallimentare alla liquidazione coatta di una piattaforma di exchange di criptovalute?",
        "Quali sono le direttive anticipate di trattamento (biotestamento) e i limiti legali dell'eutanasia in Italia?",
        "Cosa prevede il diritto internazionale marittimo e la Convenzione di Montego Bay riguardo al soccorso di naufraghi?",
        "Qual è il procedimento legale e il calcolo esatto per contestare una cartella esattoriale prescritta presso l'Agenzia delle Entrate Riscossione?",
        "Spiega i limiti legali e le sanzioni del Garante Privacy per l'utilizzo del riconoscimento facciale biometrico da parte delle forze dell'ordine.",
        "Qual è la tutela giuridica del software e dei database originali rispetto alla disciplina dei brevetti per invenzioni industriali?",
        "Quali sono i diritti del lavoratore dipendente e i limiti legali sul controllo a distanza tramite software di monitoraggio aziendale?",
        "Come si ricalcolano matematicamente le tabelle millesimali di un condominio se un condomino effettua un ampliamento volumetrico?",
        "Quali sono gli estremi legali per configurare il reato di stalking condominiale e quali prove documentali sono ammissibili in giudizio?",

        # --- Diritto Internazionale ---
        "Quali sono i presupposti giuridici per l'estradizione di un cittadino verso uno Stato extra-europeo?",
        "Spiega il ruolo della Corte Internazionale di Giustizia dell'Aia nella risoluzione delle controversie tra Stati.",
        "Come si applica il principio di reciprocità nei trattati bilaterali sul commercio internazionale?",
        "Cosa prevede la Convenzione di Ginevra in merito allo status e alla protezione dei prigionieri di guerra?",
        "Spiega la differenza formale tra la ratifica di un trattato internazionale e la sua firma.",
        "Quali sono le procedure per il riconoscimento delle sentenze civili straniere nell'ordinamento italiano?",
        "Come interviene il diritto internazionale marittimo nella definizione delle acque territoriali e della zona economica esclusiva?",
        "Spiega il concetto di immunità diplomatica e i casi in cui può essere revocata dallo Stato accreditante.",
        "Quali sono gli strumenti giuridici previsti dall'OMC per sanzionare il dumping commerciale?",
        "Cosa si intende per crimini contro l'umanità secondo lo Statuto di Roma della Corte Penale Internazionale?",
        "Qual è l'iter procedurale per adire la Corte Europea dei Diritti dell'Uomo (CEDU) di Strasburgo?",
        "Spiega l'istituto del riconoscimento degli Stati e l'effetto giuridico sui trattati preesistenti.",
        "Quali sono le conseguenze giuridiche del recesso unilaterale da un'organizzazione internazionale?",
        "Come si applica la clausola della nazione più favorita negli accordi tariffari internazionali?",
        "Cosa stabilisce la giurisprudenza internazionale sul principio di non ingerenza negli affari interni di uno Stato?",
        "Spiega la validità e l'efficacia delle consuetudini internazionali (jus cogens) rispetto ai trattati scritti.",
        "Quali sono i requisiti legali per l'esecuzione di un lodo arbitrale internazionale secondo la Convenzione di New York?",
        "Come si regola la successione degli Stati nei trattati in caso di smembramento o fusione territoriale?",
        "Cosa prevede l'ordinamento internazionale per la tutela giuridica dei rifugiati politici?",
        "Spiega la responsabilità internazionale degli Stati per atti illeciti commessi dai propri organi.",

        # --- Diritto dell'Ambiente e Urbanistica ---
        "Quali sono le sanzioni penali e amministrative per il reato di disastro ambientale e inquinamento delle falde acquifere?",
        "Spiega la procedura per ottenere la Valutazione di Impatto Ambientale (VIA) per la costruzione di un'infrastruttura.",
        "Cosa prevede il Testo Unico dell'Edilizia in caso di abusi edilizi e ordinanza di demolizione?",
        "Come si richiede l'autorizzazione paesaggistica per un intervento edilizio in una zona sottoposta a vincolo?",
        "Spiega il principio europeo 'chi inquina paga' e le responsabilità legali di bonifica dei siti contaminati.",
        "Quali sono gli obblighi giuridici per lo smaltimento dei rifiuti speciali pericolosi e la loro tracciabilità?",
        "Cosa stabilisce il piano regolatore generale (PRG) in merito alla destinazione d'uso dei suoli urbani e agricoli?",
        "Come si calcolano matematicamente gli oneri di urbanizzazione per il rilascio del permesso di costruire?",
        "Spiega il procedimento per l'adozione e l'approvazione del Piano di Governo del Territorio (PGT).",
        "Quali sono le limitazioni legali all'edificabilità nelle zone sottoposte a vincolo idrogeologico?",
        "Cosa prevede la normativa sulle emissioni in atmosfera e il sistema per lo scambio di quote (EU ETS)?",
        "Spiega la procedura di espropriazione per pubblica utilità mirata alla realizzazione di un parco naturale.",
        "Quali tutele legali esistono contro l'inquinamento acustico e le immissioni rumorose intollerabili?",
        "Come viene disciplinato il condono edilizio e quali sono i termini di prescrizione per i reati contravvenzionali in materia?",
        "Cosa si intende per perequazione urbanistica e come avviene il trasferimento dei diritti edificatori?",
        "Spiega le normative per la tutela giuridica del demanio marittimo e i limiti per le concessioni balneari.",
        "Quali sono le responsabilità civili dell'appaltatore in caso di gravi difetti di costruzione dell'immobile ex art. 1669 c.c.?",
        "Come si impugna in tribunale una SCIA (Segnalazione Certificata di Inizio Attività) edilizia ritenuta illegittima?",
        "Cosa stabilisce la direttiva europea per la tutela giuridica della qualità delle acque dei fiumi e dei laghi?",
        "Spiega il funzionamento delle convenzioni urbanistiche e l'impegno dei privati nella realizzazione di opere pubbliche.",

        # --- Diritto dell'Immigrazione ---
        "Quali sono i requisiti anagrafici e reddituali previsti dal Testo Unico per il ricongiungimento familiare?",
        "Spiega l'iter giuridico per presentare la domanda di protezione internazionale e asilo politico.",
        "Quali sono le conseguenze giuridiche e le procedure per l'espulsione amministrativa del cittadino irregolare?",
        "Come funziona il sistema delle quote d'ingresso per lavoratori extracomunitari previsto dal Decreto Flussi?",
        "Spiega la differenza legale tra lo status di rifugiato, la protezione sussidiaria e la protezione speciale.",
        "Quali sono i presupposti per la revoca o il rifiuto del rinnovo del permesso di soggiorno per lavoro subordinato?",
        "Cosa prevede la normativa in merito al trattenimento degli stranieri nei Centri di Permanenza per i Rimpatri (CPR)?",
        "Spiega la procedura legale per la conversione del permesso di soggiorno per motivi di studio in lavoro.",
        "Quali sono le tutele giuridiche specifiche garantite ai minori stranieri non accompagnati (MSNA) in Italia?",
        "Come si presenta ricorso d'urgenza in Tribunale contro un decreto prefettizio di espulsione?",
        "Cosa stabilisce l'Accordo di Schengen in merito all'attraversamento delle frontiere e ai visti di breve durata?",
        "Spiega i requisiti temporali e penali per l'ottenimento del permesso di soggiorno UE di lungo periodo.",
        "Quali sono i doveri del datore di lavoro per l'assunzione di uno straniero e i reati di sfruttamento lavorativo?",
        "Come si articola il reato di favoreggiamento dell'immigrazione clandestina secondo la giurisprudenza penale?",
        "Qual è la procedura per l'ottenimento del visto d'ingresso per investitori stranieri (Investor Visa)?",
        "Spiega i ricorsi legali esperibili in caso di silenzio-inadempimento della Pubblica Amministrazione sulla cittadinanza.",
        "Cosa prevede la normativa per il rilascio del permesso di soggiorno temporaneo per cure mediche o gravidanza?",
        "Quali sono le conseguenze penali per il cittadino che rientra illegalmente nel territorio dopo un rimpatrio forzato?",
        "Spiega il ruolo del Tribunale per i Minorenni nell'autorizzazione all'ingresso dei familiari in deroga alla legge.",
        "Come si applica il Regolamento di Dublino per determinare giuridicamente lo Stato competente per l'asilo?",

        # --- Proprietà Intellettuale e Licenze Digitali ---
        "Quali sono i requisiti di novità e originalità per ottenere la registrazione di un marchio a livello comunitario (EUIPO)?",
        "Spiega la procedura legale per tutelare un brevetto per invenzione industriale e i termini della sua decadenza.",
        "Come si configura il reato di contraffazione di opere dell'ingegno e pirateria digitale sul web?",
        "Qual è la differenza giuridica tra la cessione esclusiva dei diritti di sfruttamento economico e una licenza d'uso?",
        "Spiega come la giurisprudenza accerta il plagio musicale e la violazione del diritto d'autore.",
        "Quali sono i limiti legali dell'eccezione di fair use per la parodia o la critica di materiale coperto da copyright?",
        "Come si struttura legalmente un contratto di sviluppo software con clausola di trasferimento del codice sorgente?",
        "Cosa prevede la normativa sulle licenze Creative Commons e le implicazioni della clausola 'Non opere derivate'?",
        "Spiega le tutele legali previste per il segreto industriale e le clausole di non concorrenza (NDA).",
        "Quali sono le procedure per presentare un ricorso UDRP contro il cybersquatting di un nome a dominio web?",
        "Come si deposita e si tutela legalmente un disegno o modello industriale tramite l'organizzazione WIPO?",
        "Quali sono le direttive europee riguardanti la tutela giuridica del diritto sui generis per le banche dati?",
        "Spiega la responsabilità civile dei fornitori di servizi di hosting (ISP) in caso di contenuti illeciti degli utenti.",
        "Quali sono i confini legali per l'utilizzo commerciale di immagini generate tramite intelligenza artificiale?",
        "Come funziona la tutela del diritto all'immagine e alla voce nell'ambito del deepfake e delle produzioni video?",
        "Cosa si intende per esaurimento del diritto di marchio e quali sono le implicazioni legali per le importazioni parallele?",
        "Spiega la validità giuridica degli smart contract nella gestione automatizzata delle royalties per lo streaming musicale.",
        "Qual è l'iter legale per registrare un formato televisivo originale presso la SIAE per proteggerlo da imitazioni?",
        "Come si configurano le licenze software open source GPL e le obbligazioni legali legate all'effetto copyleft?",
        "Quali sono gli strumenti giuridici cautelari e inibitori d'urgenza per bloccare la diffusione di un'opera contraffatta?",
    ],

    'general': [
        # Fix Q4: "parabola" in contesto fisico quotidiano (non matematico)
        "Mio figlio ha rotto qualcosa in casa per un lancio sbagliato, chi è responsabile dei danni verso il vicino?",
        "Come ci si comporta quando si rompe accidentalmente qualcosa di proprietà altrui durante un'attività sportiva?",

        #Macroeconomia, bilanci, finanza quotidiana
        "Spiegami le cause e le conseguenze dell'inflazione e come le banche centrali usano i tassi d'interesse.",
        "Come si legge un bilancio aziendale di base e qual è la differenza tra stato patrimoniale e conto economico?",
        "Cosa sono i titoli di stato, le obbligazioni e come funziona il mercato obbligazionario?",
        "Spiegami il concetto di PIL, crescita economica e recessione in termini semplici.",
        "Come funziona il Quantitative Easing e qual è il suo impatto sull'economia reale?",
        "Qual è la differenza tra politica monetaria e politica fiscale in un'economia moderna?",
        "Come funziona la borsa valori e cosa determina il prezzo di un'azione quotata?",

        # Fix Q2: volume oggetti in contesto pratico (ancora su GENERAL, non MATH)
        "Come si stima approssimativamente la quantità di legna ricavabile da un albero tagliato in giardino?",
        # --- Ricette, Cucina e Istruzioni Procedurali Quotidiane ---
        "Quali sono gli ingredienti e le istruzioni procedurali esatte per preparare il tiramisù perfetto?",
        "Dammi la ricetta tradizionale esatta e i passaggi procedurali per cucinare la carbonara romana.",
        "Quali sono i passaggi passo-passo per preparare una pizza margherita fatta in casa?",
        "Spiegami i procedimenti corretti per la cottura sottovuoto a bassa temperatura della carne.",
        "Dammi le istruzioni dettagliate su come fare il lievito madre partendo da zero.",
        "Qual è la lista della spesa e il procedimento esatto per cucinare una paella valenciana?",
        "Come si prepara un cocktail Mojito perfetto? Dammi dosi e istruzioni.",
        "Quali sono le tecniche culinarie per sfilettare e preparare correttamente il pesce crudo?",
        "Come si prepara un brodo vegetale saporito partendo da verdure fresche?",
        "Quali sono i segreti per ottenere una frittura di pesce croccante e asciutta?",
        "Spiegami come si fa la pasta frolla e quali sono le proporzioni tra burro e farina.",

        # --- Vita Quotidiana, Fai-da-Te e Consigli Pratici ---
        "Come faccio a organizzare un viaggio economico di due settimane in Giappone?",
        "Quali sono i migliori consigli e tecniche per gestire lo stress e l'ansia quotidiana?",
        "Dammi delle istruzioni procedurali su come cambiare la ruota forata di un'automobile.",
        "Come si coltivano le piante da appartamento e quanto spesso vanno annaffiate?",
        "Quali sono i consigli pratici per coltivare le orchidee in casa e prevenire malattie o marciume delle radici?",
        "Qual è il metodo migliore per pulire le fughe dei pavimenti e rimuovere la muffa?",
        "Spiegami come strutturare un curriculum vitae efficace per trovare lavoro rapidamente.",
        "Quali sono le usanze e le buone maniere da rispettare durante una cena di gala formale?",
        "Dammi dei consigli su come arredare un soggiorno piccolo per ottimizzare gli spazi.",
        "Come si fa la manutenzione ordinaria di una bicicletta da corsa o mountain bike?",
        "Quali sono i passaggi per dipingere una stanza e preparare i muri correttamente?",
        "Come si rimuovono le macchie di vino rosso o caffè dai tessuti delicati?",
        "Quali sono gli attrezzi indispensabili per iniziare a fare piccoli lavori di falegnameria in casa?",
        "Spiegami come montare una mensola a muro usando correttamente i tasselli e il trapano.",
        "Quali sono le tecniche migliori per imparare a suonare la chitarra classica da autodidatta?",

        # --- Storia, Geografia e Scienze Umanistiche ---
        "Quali furono le cause sociali, le dinamiche economiche e le battaglie storiche che portarono alla caduta dell'Impero Romano d'Occidente?",
        "Spiegami le origini storiche, le battaglie decisive e le trasformazioni geopolitiche seguite alla Prima Guerra Mondiale e al trattato di Versailles.",
        "Come si sviluppò la civiltà egizia lungo il corso del Nilo, quali faraoni regnarono e quali monumenti storici costruirono?",
        "Quali fattori storici, culturali e battaglie rivoluzionarie portarono alla Rivoluzione Francese del 1789?",
        "Raccontami la storia dell'Impero Ottomano, le guerre combattute e le ragioni geopolitiche del suo declino storico.",
        "Chi era Napoleone Bonaparte, quali battaglie vinse e qual è stato il suo impatto militare sulla storia europea moderna?",
        "Quali sono i confini geografici, le catene montuose, il clima e le caratteristiche demografiche del continente asiatico?",
        "Spiegami la differenza tra la geografia fisica dei rilievi e dei fiumi e la geografia politica del continente africano.",
        "Quali furono le trasformazioni politiche, i movimenti sociali e i personaggi storici legati all'introduzione del suffragio universale in Italia?",
        "Raccontami la biografia di Giulio Cesare, le sue campagne militari e il passaggio storico dalla Repubblica all'Impero Romano.",
        "Spiegami le tappe storiche della colonizzazione delle Americhe, gli esploratori coinvolti e l'impatto sui popoli nativi precolombiani.",
        "Quali sono le principali catene montuose del mondo, come si sono formate geologicamente e come influenzano il clima locale?",
        "Raccontami la storia della Guerra Fredda, le crisi militari e il ruolo della cortina di ferro nel contesto europeo del Novecento.",

        # --- Filosofia, Letteratura e Arti ---
        "Spiegami la filosofia stoica di Seneca e Marco Aurelio e i suoi principi fondamentali sulla vita.",
        "Qual è la differenza concettuale tra etica deontologica di Kant e l'utilitarismo di Mill?",
        "Cosa intendeva Platone con la sua teoria delle idee e il mito della caverna?",
        "Come si differenziano le grandi correnti del pensiero filosofico orientale dal pensiero occidentale?",
        "Spiegami i temi principali, i personaggi e la struttura della Divina Commedia di Dante Alighieri.",
        "Quali sono le caratteristiche principali del Romanticismo letterario europeo e i suoi autori rappresentativi?",
        "Come si distingue il periodo Barocco dal Rinascimento nell'arte e nell'architettura italiana?",
        "Fai un'analisi dell'opera pittorica 'La Gioconda' di Leonardo da Vinci.",
        "Qual è il significato allegorico del romanzo '1984' di George Orwell?",
        "Spiega le differenze stilistiche tra la musica classica di Mozart e quella di Beethoven.",
        "Quali sono gli elementi chiave della tragedia greca e il concetto di catarsi in Aristotele?",
        "Spiegami l'importanza del Futurismo nell'arte del Novecento e i suoi principali esponenti.",
        "Qual è la trama e il significato del romanzo 'I Promessi Sposi' di Alessandro Manzoni?",

        # --- Scienze Generali, Natura e Astronomia ---
        "Come funziona la fotosintesi clorofilliana nelle piante a foglia larga e negli alberi?",
        "Spiega il meccanismo dell'evoluzione darwiniana, la genetica e la selezione naturale.",
        "Come funziona il sistema immunitario umano in risposta a un'infezione batterica o virale?",
        "Cosa sono le cellule staminali e come vengono utilizzate nella medicina moderna rigenerativa?",
        "Spiegami la formazione dei buchi neri supermassicci e i concetti base dell'astronomia moderna.",
        "Come funziona il ciclo dell'acqua sulla Terra e quali sono le sue fasi meteorologiche?",
        "Spiegami la struttura del sistema solare, i pianeti terrestri e i giganti gassosi.",
        "Qual è la differenza biologica tra un virus, un batterio e un fungo patogeno?",
        "Come si formano i terremoti e i vulcani secondo la teoria della tettonica a placche?",
        "Spiega il paradosso del gatto di Schrödinger e le sue implicazioni base per capire i quanti.",
        "Come si applicano i principi della termodinamica per raffreddare un motore a combustione interna?",
        "Quali sono le caratteristiche fisiche della Luna e come influenzano le maree terrestri?",
        "Spiegami come funziona il sistema nervoso centrale e la trasmissione degli impulsi neuronali.",
        "Cosa sono gli esopianeti e quali sono i metodi attuali per scoprirli nello spazio?",

        # --- Benessere, Sport e Tempo Libero ---
        "Quali sono i benefici della meditazione mindfulness per la salute mentale a lungo termine?",
        "Dammi una routine di esercizi di stretching da fare a casa per migliorare la flessibilità.",
        "Come si gioca a tennis e come funziona il sistema di punteggio dei set?",
        "Quali sono le differenze tra lo yoga Hatha e lo yoga Vinyasa?",
        "Come si gioca a pallavolo? Spiegami i ruoli dei giocatori in campo e i falli principali.",
        "Quali sono i principi di una dieta equilibrata per chi pratica sport a livello amatoriale?",
        "Come funziona il fuorigioco nel calcio moderno e come interviene il VAR durante la partita?",
        "Come funziona il gioco degli scacchi e come si gioca in modo competitivo?",
        "Dammi dei consigli su come iniziare a correre (running) evitando infortuni alle ginocchia.",
        "Come si organizza un allenamento funzionale a corpo libero per aumentare la forza?",

        # --- Società, Cultura Pop e Attualità ---
        "Quali sono i pro e i contro psicologici e culturali di vivere in una grande metropoli rispetto alla campagna?",
        "Come influisce il cambiamento climatico sugli ecosistemi globali e sull'economia moderna?",
        "Quali sono le principali disparità economiche nel mondo e le loro radici storiche?",
        "Raccontami la trama, l'ambientazione e la lore della saga cinematografica di Star Wars.",
        "Quali sono le differenze tra le varie generazioni sociologiche come Boomer, Millennial e Gen Z?",
        "Come funziona il mercato azionario e quali sono i concetti base per chi vuole iniziare a investire?",
        "Quali sono i generi musicali più popolari del ventesimo secolo e come sono nati?",
        "Spiegami il fenomeno della globalizzazione e l'impatto dei social media sulla comunicazione di massa.",
        "Qual è l'impatto della musica streaming (Spotify, Apple Music) sull'industria discografica?",
        "Quali sono stati i film più premiati nella storia degli Oscar e perché sono considerati dei capolavori?",
        "Spiegami il concetto di economia circolare e come può ridurre l'impatto ambientale dei rifiuti.",
        "Quali sono i principali festival culturali e musicali nel mondo che vale la pena visitare?",
        "Come è cambiata la televisione con l'avvento delle piattaforme di streaming come Netflix?",
        "Spiega l'evoluzione dei videogiochi dalle sale arcade fino alle console di ultima generazione.",

        # --- Giochi, Sport e Tempo Libero ---
        "Come funziona il sistema di punteggio nel bowling e come si calcola il risultato finale?",
        "Come funziona il vantaggio e il fuorigioco nel rugby moderno?",
        "Dammi una strategia infallibile per vincere a Risiko valutando le probabilità dei dadi.",
        "Spiega l'organizzazione di un torneo di tennis a eliminazione diretta e il calcolo delle teste di serie.",

        # --- Linguistica, Scrittura e Letteratura ---
        "Come si struttura l'architettura narrativa e lo sviluppo dei personaggi in un romanzo giallo?",
        "Qual è il linguaggio dei fiori e qual è il significato storico di regalare una rosa gialla?",
        "Aiutami a scrivere uno script teatrale o una sceneggiatura per una commedia brillante in tre atti.",
        "Qual è il programma di studio ideale e le tecniche mnemoniche per imparare una nuova lingua in sei mesi?",
        "Fai un'analisi letteraria e una recensione critica del libro 'Il Codice da Vinci' di Dan Brown.",

        # --- Cucina, Dietetica e Fai-da-te ---
        "Dammi l'equazione perfetta e la proporzione tra lievito, farina e idratazione per la pizza.",
        "Come ci si comporta a tavola in Giappone e quali sono le usanze del galateo locale?",
        "Scrivi un programma di allenamento settimanale e la dieta per lo sviluppo della massa muscolare a casa.",
        "Spiegami il processo logico passo-passo per l'assemblaggio e il montaggio di un armadio IKEA.",
        "In cosa consiste il protocollo di allenamento Tabata e come si implementa a corpo libero?",

        # --- Psicologia, Sociologia e Relazioni ---
        "Quali sono le dinamiche psicologiche e i fattori chiave per mantenere viva l'intesa in un matrimonio?",
        "Come si fa il debugging delle proprie emozioni per superare un trauma psicologico o gestire l'ansia?",
        "Illustrami il principio dell'attrazione e come viene applicato nella psicologia motivazionale moderna.",

        # --- Musica, Arte e Cinema ---
        "Spiegami il linguaggio musicale, i tempi e come si leggono le note su uno spartito classico.",
        "Qual è il processo creativo che usa un regista per decidere il montaggio di un film?",
        "Come si calcola la sezione aurea e come è stata applicata nell'architettura e nell'arte rinascimentale?",
        "Quali sono le tecniche prospettiche e geometriche per disegnare un paesaggio urbano in modo realistico?",
        "Quali sono i principi estetici fondamentali per scattare una fotografia di ritratto con luce naturale?",

        # --- Scienze della Terra, Biologia e Natura ---
        "Spiegami il principio di gravitazione universale di Newton e il suo impatto sulla comprensione dell'universo.",
        "Qual è la sequenza del genoma umano e come avviene esattamente il processo di trascrizione e traduzione del DNA?",
        "Come funziona l'ecosistema marino e i meccanismi di sopravvivenza delle specie che lo abitano?",
        "Illustrami il processo geologico di formazione delle rocce ignee, sedimentarie e metamorfiche.",
        "Come si esegue il calcolo approssimativo dell'età di un albero osservando la sezione dei suoi anelli?",

        # --- Economia Domestica e Organizzazione Pratica ---
        "Dammi una strategia pratica e una formula mentale per tagliare le spese e gestire il budget familiare.",
        "Come ci si organizza per affrontare un trasloco senza stressarsi?",
        "Come fare il calcolo veloce a mente dei macronutrienti e delle calorie mentre si fa la spesa al supermercato?",
        "Qual è il processo decisionale migliore per scegliere lo stile e l'arredamento di un piccolo soggiorno?",

        # --- Moda, Design e Stile di Vita ---
        "Come si crea una palette cromatica e qual è il metodo visivo per abbinare i vestiti in modo elegante?",
        "Come bisogna vestirsi in ambito lavorativo e come presentarsi al meglio per un colloquio formale?",
        "Qual è il linguaggio del corpo e come si possono interpretare le microespressioni facciali umane?",
        "Come si sviluppa un proprio stile personale prendendo ispirazione dal design e dall'architettura d'interni?",
        "Illustrami il concetto danese dell'Hygge e come applicarlo nella vita quotidiana e in casa.",

        # --- Curiosità e Scienze Cognitive ---
        "Spiega la matematica nascosta nelle illusioni ottiche e i meccanismi percettivi con cui il cervello viene ingannato.",
        "Come si addestra efficacemente un cucciolo di cane nei primi mesi di vita?",
    ],
}


# =============================================================================
# BRIDGE_SENTENCES — Frasi di confine condivise tra domini
#
# Ogni chiave è una tupla di 2 domini. vector_store.py le processa così:
#   1. Embeda la frase UNA SOLA VOLTA (nessun doppio calcolo).
#   2. Crea un record per CIASCUN dominio nella tupla.
# Questo garantisce un'unica sorgente di verità e azzera il debito tecnico
# dei cloni manuali precedentemente presenti in INTENT_SENTENCES.
# =============================================================================

BRIDGE_SENTENCES: Dict[Tuple[str, str], List[str]] = {

    # -------------------------------------------------------------------------
    # CODING <-> RIGHTS (26 frasi uniche)
    # Lato coding: frasi "implementazione + normativa"
    # Lato rights: frasi "normativa + implicazioni sul software"
    # -------------------------------------------------------------------------
    ('coding', 'rights'): [
        # --- Lato coding ---
        "Scrivi uno script Python che anonimizza i dati personali in un database SQL rispettando il GDPR europeo.",
        "Implementa il principio di privacy by design in un'architettura software per la gestione dei dati utente.",
        "Scrivi il codice per garantire la conformità normativa nella raccolta e nel trattamento dei dati personali.",
        "Come si implementa tecnicamente il diritto all'oblio cancellando irreversibilmente i record di un utente dal database?",
        "Sviluppa uno script che genera log firmati digitalmente con validità probatoria ammissibile in sede legale.",
        "Scrivi il codice per uno smart contract Solidity che esegue automaticamente le clausole di un accordo commerciale.",
        "Implementa un sistema di audit trail immutabile per tracciare gli accessi ai dati sensibili rispettando le normative.",
        "Come si struttura il codice di un'app per raccogliere il consenso informato degli utenti secondo la direttiva ePrivacy?",
        "Scrivi il codice per pseudonimizzare i dati personali in un dataset prima di condividerlo con terze parti.",
        "Sviluppa un modulo software che implementi il controllo degli accessi basato su ruoli (RBAC) secondo i requisiti legali.",
        "Come si implementa tecnicamente la portabilità dei dati permettendo all'utente di esportare il proprio profilo in JSON?",
        "Scrivi uno script che verifica automaticamente la conformità GDPR di un database rilevando campi non cifrati.",
        "Implementa in Python la firma digitale di documenti contrattuali usando certificati X.509 validi legalmente.",
        "Scrivi il codice per un sistema di notifica automatica delle violazioni dei dati personali entro 72 ore come previsto dalla legge.",
        # --- Sicurezza, autenticazione e implementazione normativa [FIX] ---
        "Come si implementa tecnicamente un sistema di autenticazione a più fattori conforme alle normative sulla sicurezza informatica?",
        "Quali sono le sanzioni penali per l'accesso abusivo a sistemi informatici ex art. 615-ter e come si implementa tecnicamente la prevenzione?",
        "Come si costruisce un canale di segnalazione anonimo crittografato end-to-end rispettando i requisiti legali del whistleblowing (D.Lgs. 24/2023)?",
        "Scrivi uno script Python che calcola gli interessi di mora su un foglio di debitori secondo la normativa D.Lgs. 231/2002 sui ritardi di pagamento.",
        "Come si implementa tecnicamente la conformità GDPR in un sistema di autenticazione con logging sicuro e validità probatoria legale?",
        "Quali adempimenti normativi deve soddisfare un sistema di crittografia end-to-end per canali di comunicazione riservati in ambito aziendale?",
    ],

    # -------------------------------------------------------------------------
    # CODING <-> MATH (frasi uniche) — V2.1: aggiunte FFT/campionamento e Monte Carlo
    # -------------------------------------------------------------------------
    ('coding', 'math'): [
        "Implementa in C++ l'algoritmo della Trasformata di Fourier Veloce (FFT) per analizzare un segnale discreto.",
        "Scrivi il codice Python che implementa la scomposizione QR di una matrice usando l'algoritmo di Gram-Schmidt.",
        "Sviluppa uno script che calcola numericamente gli autovalori di una matrice con il metodo delle potenze in Python.",
        "Implementa in C++ il metodo di Newton-Raphson per trovare le radici reali di un polinomio di terzo grado.",
        "Scrivi il codice per il calcolo dell'integrale definito usando la quadratura di Gauss-Legendre in Python.",
        "Implementa l'algoritmo di eliminazione di Gauss-Jordan in C++ per risolvere un sistema lineare denso.",
        "Sviluppa uno script Python che calcola la derivata numerica di una funzione usando differenze finite centrate.",
        "Scrivi il codice per risolvere numericamente un'equazione differenziale ordinaria col metodo Runge-Kutta 4.",
        "Implementa in Python la regressione lineare multipla calcolando i coefficienti tramite la formula delle equazioni normali.",
        "Scrivi uno script che calcola la distribuzione di probabilità binomiale e la visualizza con un istogramma in Matplotlib.",
        # --- V2.1 NEW: FFT e campionamento ---
        "Dimostra il teorema di Nyquist-Shannon e scrivi il codice Python per la campionatura e ricostruzione di un segnale audio con FFT.",
        "Implementa in Python la trasformata di Fourier discreta da zero e verifica i risultati confrontandoli con numpy.fft.",
        "Scrivi il codice per applicare un filtro passa-basso nel dominio delle frequenze usando FFT e spiega la base matematica.",
        "Analizza matematicamente il fenomeno dell'aliasing e scrivi uno script Python che lo dimostra visivamente con un segnale sinusoidale.",
        "Implementa il metodo di Cooley-Tukey per la FFT in Python e analizza la sua complessità computazionale O(N log N).",
        # --- V2.1 NEW: Monte Carlo e convergenza ---
        "Scrivi il codice per un simulatore Monte Carlo che stima il valore di π e analizza matematicamente la convergenza statistica al variare di N.",
        "Implementa in Python un integratore Monte Carlo multidimensionale e confronta l'errore con il metodo dei trapezi al variare dei campioni.",
        "Sviluppa uno script che dimostra empiricamente la convergenza 1/sqrt(N) dell'errore Monte Carlo tramite esperimenti numerici.",
        "Scrivi il codice per un simulatore Monte Carlo di cammini aleatori e analizza la distribuzione delle posizioni finali.",
        "Implementa il metodo di importance sampling in Python e mostra la riduzione della varianza rispetto al Monte Carlo standard.",
    ],

    # -------------------------------------------------------------------------
    # MATH <-> RIGHTS (23 frasi uniche)
    # -------------------------------------------------------------------------
    ('math', 'rights'): [
        # --- Lato math ---
        "Qual è la formula matematica esatta stabilita dalla normativa per calcolare il TFR netto di un lavoratore?",
        "Come si calcola matematicamente il piano di ammortamento alla francese secondo quanto previsto dalla legge sul credito?",
        "Qual è il metodo numerico previsto per legge per l'adeguamento ISTAT degli assegni di mantenimento?",
        "Come si quantifica il danno biologico permanente usando le tabelle risarcitorie del Tribunale di Milano?",
        "Qual è il calcolo legale esatto per la ripartizione millesimale delle spese condominiali di rifacimento tetto?",
        "Come si determinano matematicamente i valori soglia del tasso usura secondo le circolari della Banca d'Italia?",
        "Quale procedura di calcolo prevede il codice civile per la rivalutazione monetaria dei crediti risarcitori?",
        "Come si calcolano gli interessi moratori su un debito commerciale secondo le direttive europee sui ritardi di pagamento?",
        "Qual è la formula normativa per determinare il valore fiscale di un immobile ai fini dell'imposta di registro?",
        "Come si calcolano matematicamente le quote di legittima e la quota disponibile in una successione ereditaria complessa?",
        "Quale modello matematico stabilisce la legge per il calcolo dell'equo indennizzo in caso di espropriazione?",
        "Come si determina numericamente il tasso effettivo globale (TAEG) secondo la normativa europea sul credito al consumo?",
        "Qual è il calcolo previsto dalla normativa per la determinazione del valore di avviamento di un'azienda in sede di cessione?",
        # --- Analisi finanziaria e normativa fiscale [FIX] ---
        "Qual è la formula matematica per calcolare il tasso interno di rendimento (TIR) di un investimento e quale normativa fiscale si applica alle plusvalenze?",
        "Come si calcola il valore attuale netto di un piano di investimento e quali obblighi dichiarativi prevede il TUIR per le plusvalenze finanziarie?",
        "Qual è il modello attuariale per la valutazione di una rendita e come la normativa del TUF ne regola la commercializzazione?",
    ],

    # -------------------------------------------------------------------------
    # GENERAL <-> MATH (7 frasi uniche)
    # -------------------------------------------------------------------------
    ('general', 'math'): [
        # --- Lato math (più formale) ---
        "Qual è la proporzione matematica esatta per ricalcolare le dosi di una ricetta passando da 2 a 9 persone?",
        "Come si imposta l'equazione per calcolare il reale tasso di sconto applicato durante i saldi stagionali?",
        "Dimostra matematicamente come il tasso di cambio composto influisce sul costo reale di una vacanza all'estero.",
        "Spiega con formule come calcolare il consumo medio di carburante e l'efficienza energetica di un veicolo su base mensile.",
        # --- Lato general (più pratico) ---
        "Qual è il metodo mentale più veloce per calcolare al volo lo sconto del 30% su un capo d'abbigliamento in negozio?",
        "Come faccio a calcolare esattamente quanta vernice o metri quadri mi servono per dipingere le pareti della mia stanza?",
        "Spiegami come si convertono mentalmente i gradi Fahrenheit in Celsius quando si viaggia negli Stati Uniti.",
    ],

    # -------------------------------------------------------------------------
    # GENERAL <-> RIGHTS (9 frasi uniche)
    # -------------------------------------------------------------------------
    ('general', 'rights'): [
        # --- Lato rights (più formale) ---
        "Quali sono le clausole obbligatorie per registrare un contratto di affitto transitorio per studenti universitari?",
        "Cosa prevede il Codice del Consumo o la Carta dei Diritti del Passeggero per il rimborso di un volo cancellato o in ritardo?",
        "Come si attiva la garanzia legale di conformità per un prodotto difettoso acquistato su un portale e-commerce?",
        "Qual è la procedura per la constatazione amichevole (CID) e l'attribuzione delle responsabilità civili in un tamponamento a catena?",
        "Quali sono le norme esatte del codice civile riguardanti il rispetto delle distanze legali e l'immissione di fumo tra vicini?",
        # --- Lato general (più pratico) ---
        "Quali sono i documenti necessari e i passi pratici da fare al Comune per cambiare la residenza in una nuova città?",
        "Dammi dei consigli pratici su cosa verificare prima di prendere in affitto un appartamento per la prima volta.",
        "Come funziona la procedura pratica per fare il reso gratuito su Amazon e quanti giorni ho per restituire il pacco?",
        "Spiegami cosa fare praticamente e chi chiamare immediatamente subito dopo aver fatto un piccolo incidente in auto.",
    ],
}
