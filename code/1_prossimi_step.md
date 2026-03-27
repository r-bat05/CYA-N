0) FAR ANALIZZARE A CLAUDE I FILE MODIFICATI DA GEMINI (TUTTI)
1) EFFETTUARE STRESS TEST PER LE QUERY MONO-MODELLO CHE PERO' UTILIZZANO CONCETTI DI ALTRI MODULI

💻 Programmazione travestita da Matematica (Target: Coding)
L'utente vuole codice eseguibile, ma descrive il problema usando un lessico fortemente matematico. L'arco di instradamento deve puntare solo a qwen3.5:9b.

"Scrivi una funzione ricorsiva in C++ per calcolare la successione di Fibonacci, ottimizzando la memoria per non sforare la complessità asintotica Big O." (Insidia: successione, calcolare, asintotica).

"Come posso implementare l'algoritmo del polinomio di Taylor in uno script Python senza causare un'eccezione di stack overflow?" (Insidia: polinomio, Taylor, algoritmo).

"Crea una classe Java che rappresenti uno spazio vettoriale a 3 dimensioni e implementa un metodo per estrarre la norma del vettore." (Insidia: spazio vettoriale, dimensioni, norma, vettore).

📐 Matematica travestita da Programmazione (Target: Math)
L'utente vuole una dimostrazione o un calcolo teorico, ma usa termini informatici per descrivere il processo mentale. L'arco deve chiudersi esclusivamente su deepseek-r1:7b.
4. "Dimostrami il teorema di Lagrange sulle derivate utilizzando un ragionamento logico strutturato ad albero binario." (Insidia: albero binario, strutturato).
5. "Qual è l'algoritmo matematico per calcolare a mano l'intersezione esatta tra due domini di funzioni esponenziali?" (Insidia: algoritmo, domini, funzioni).
6. "Calcola l'integrale definito di questa equazione complessa, mostrando ogni singola iterazione e variabile del tuo ragionamento." (Insidia: iterazione, variabile, complessa).

⚖️ Diritto travestita da Tech (Target: Rights)
L'utente fa una domanda prettamente legale, ma usa contesti digitali. L'arco di esecuzione deve attivare solo gpt-oss:20b senza interpellare il programmatore.
7. "Qual è la procedura legale esatta per fare ricorso al TAR contro un algoritmo di profilazione automatizzata che ha elaborato i miei dati?" (Insidia: algoritmo, elaborato, automatizzata).
8. "Spiegami la gerarchia delle fonti del diritto italiano schematizzandola come se fosse la struttura di un database relazionale o un albero gerarchico." (Insidia: database relazionale, struttura, albero).
9. "Secondo il codice civile, qual è la formula per calcolare le frazioni e le percentuali della quota di legittima in una successione?" (Insidia: formula, calcolare, frazioni, percentuali).

⚙️ Programmazione travestita da Diritto (Target: Coding)
L'utente chiede di configurare sistemi informatici usando parole che richiamano regole e normative, ma non sta chiedendo una consulenza legale.
10. "Devo fare il deploy di un'applicazione cloud. Scrivimi un file docker-compose che applichi le policy di sicurezza standard e integri una licenza open source MIT nel container." (Insidia: policy, licenza, open source).
11. "Spiegami come configurare le foreign key in un database SQL in modo da garantire l'integrità referenziale come se fosse un contratto blindato tra le tabelle." (Insidia: garanzia, integrità, contratto).

2) TESTARE PIPELINE LLM

1. Archi Ibridi Netti (Test del Flusso A $\rightarrow$ B e Handoff)Queste query devono superare agevolmente la soglia del $30\%$ di hit esclusivi e innescare la pipeline sequenziale. L'obiettivo qui è verificare che l'Agente B riesca a fondere organicamente il suo sapere con l'output dell'Agente A.Coding $\rightarrow$ Rights: "Scrivi uno smart contract in Solidity per la compravendita di un software, ma includi un commento testuale che spieghi se questa transazione automatizzata rispetta i requisiti di forma e nullità del contratto previsti dal codice civile italiano."Math $\rightarrow$ Coding: "Spiegami la teoria matematica dietro il calcolo della matrice inversa tramite l'eliminazione di Gauss, e poi scrivimi uno script in Python che implementi esattamente questo algoritmo."Rights $\rightarrow$ Coding: "Quali sono le direttive esatte del GDPR sulla conservazione dei log degli utenti? Una volta spiegate, forniscimi un esempio di architettura di un database SQL per essere a norma."2. Trappole Lessicali (Test dell'Arco SHARED_TECH)Queste query contengono le parole ambigue (funzione, sistema, variabile) individuate da Claude. Lo scopo è verificare che l'intersezione dinamica funzioni e che il sistema tracci un arco mono-dominio, senza farsi ingannare dai falsi positivi.Coding Isolato: "Spiegami come si dichiara una variabile globale all'interno di una funzione ricorsiva in JavaScript per evitare eccezioni di runtime." (Non deve attivare la matematica).Math Isolato: "Risolvi questo sistema di equazioni lineari a tre incognite per determinare il valore esatto della variabile $x$ e della funzione derivata." (Non deve attivare la programmazione).3. Asimmetria di Lunghezza (Test della Soglia Proponzionale $30\%$)Queste query servono a validare se la percentuale dinamica è migliore del vecchio $N=1$ fisso.Diluizione (Deve restare mono-dominio): "Ho questo enorme script in Python [immagina di incollare 50 righe di codice per il web scraping] che usa BeautifulSoup. Ho un errore di indentazione alla riga 12 e un memory leak sulla variabile iteratore. Puoi correggere il codice? Ah, un'ultima cosa, pensi che fare scraping su questo sito violi il copyright?" (L'unico termine legale "copyright" affogato in 20 termini tecnici non deve raggiungere il $30\%$).Condensazione (Deve attivare la pipeline): "Crea un array C++ per la privacy." (Pochissime parole, ma un rapporto 1:1 tra programmazione e diritto. Deve superare il $30\%$ e attivarsi).4. Stress-Test del Critic Pass (L'Arco di Autovalutazione)Queste query contengono una "trappola" fattuale per indurre in errore il primo agente (Coding). L'Agente B (Rights) deve usare il Critic Pass per rilevare l'errore e non fidarsi ciecamente.Trappola Legale: "Scrivi una funzione in Python per calcolare le ferie maturate di un dipendente. Considera come base di partenza che la legge italiana garantisce un minimo di 10 giorni all'anno per tutti." (In Italia sono 4 settimane. L'Agente B dovrà smentire l'assunto dell'utente e correggere il codice dell'Agente A).
