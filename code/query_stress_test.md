### 🩸 Categoria 1: Semantic Bleed (Parole con doppio significato)

Queste query usano termini che significano una cosa nella vita quotidiana, ma un'altra nell'informatica o nella matematica. Il k-NN dovrà capire il contesto.

1. **"Voglio creare una classe per i miei alunni delle elementari, come gestisco l'ereditarietà dei loro voti storici?" *(Coding vs General)***
2. "Come si calcola il volume di un tronco d'albero tagliato in giardino per capire quanta legna ho fatto?" *(Math vs General)*
3. "Qual è la ricetta migliore per pulire il codice della lavatrice che continua a darmi errore E20?" *(General vs Coding)*
4. "Mio figlio ha rotto il vetro del vicino tirando una palla con una parabola perfetta, chi paga i danni?" *(General vs Math vs Rights)*
5. "Sto scrivendo un romanzo giallo. Se l'assassino inietta del veleno, in quanto tempo decade la concentrazione nel sangue secondo le leggi della farmacocinetica?" *(General vs Math)*

### 🧩 Categoria 2: Ibridi Estremi (Non Mappati nel DB)

Combiniamo domini in modi plausibili ma mai inseriti esplicitamente in `BRIDGE_SENTENCES`.
6. "Spiegami il teorema di Nash sull'equilibrio dei giochi e scrivi le clausole legali per applicarlo a un contratto di appalto aziendale." *(Math vs Rights)*
7. "Quali sono le responsabilità legali se il mio algoritmo di machine learning sbaglia a calcolare il limite di una funzione per il dosaggio di un farmaco medico?" *(Rights vs Coding vs Math)*
8. "Se un hacker mi ruba i bitcoin craccando la mia chiave RSA privata, come dimostro matematicamente in tribunale che la colpa è del generatore di numeri pseudo-casuali?" *(Coding vs Math vs Rights)*
**9. "Come si programma in C uno smart contract per dividere un'eredità in parti inversamente proporzionali al reddito degli eredi?" *(Coding vs Math vs Rights)***
10. "Qual è l'impatto del GDPR sullo sviluppo di interfacce utente (UI/UX) progettate per manipolare psicologicamente l'utente (i cosiddetti dark patterns)?" *(Rights vs Coding vs General)*

### 🗣️ Categoria 3: Colloquiali e Implicite

L'intento tecnico è nascosto dietro un linguaggio estremamente colloquiale, lamentoso o discorsivo.
**11. "Non riesco a far parlare il mio computer col database, continua a dirmi che non ha i permessi, che cavolo devo scrivere sul terminale per sbloccarlo?" *(Coding vs General)***
12. "Il mio capo non mi paga gli straordinari da tre mesi, quanti soldi mi deve esattamente se guadagno 15 euro l'ora e ne ho fatte 40 in più col 10% di interesse di mora?" *(Rights vs Math)*
13. "Aiutami a scrivere una poesia in rima baciata che spieghi in modo divertente il funzionamento della blockchain e della crittografia asimmetrica." *(General vs Coding)*
14. "Come si monta un mobile dell'IKEA se ho perso le istruzioni ma mi sono accorto che i pezzi seguono una sequenza di Fibonacci?" *(General vs Math)*
15. "Dimmi i trucchi matematici per vincere a poker Texas Hold'em calcolando le carte che rimangono nel mazzo senza farmi scoprire." *(General vs Math)*

### 🌌 Categoria 4: Nicchie Assolute e Astrazioni

Concetti molto specifici o paradossali che spingono lo spazio vettoriale ai suoi limiti estremi.
**16. "Esiste una dimostrazione matematica rigorosa dell'esistenza di Dio o del libero arbitrio tramite la logica formale e i teoremi di incompletezza?" *(Math vs General)***
17. "Cosa succede legalmente se un astronauta commette un omicidio sulla Stazione Spaziale Internazionale? Quale giurisdizione terrestre si applica?" *(Rights vs General)*
**18. "Ho un problema con i ragni in casa, esiste un algoritmo in Python per mappare i loro movimenti sui muri usando una matrice di adiacenza?" *(General vs Coding)***
19. "Spiegami perché il gatto cade sempre in piedi usando le equazioni del momento angolare, i tensori di inerzia e la fisica conservativa." *(General vs Math)*
20. "Qual è l'iter legislativo per presentare un disegno di legge che dichiari incostituzionale la legge di gravità di Newton sul suolo italiano?" *(Rights vs Math - Nonsense test)*

### 🌍 Categoria 5: Barriere Linguistiche e Formattazione

Testano la tolleranza degli embedding a lingue diverse, gerghi tecnici mischiati (Itanglish) o query lunghissime.
21. "What is the penalty for breaching an NDA (Non-Disclosure Agreement) under Italian civil law and how do I calculate the damages?" *(Rights vs Math - In Inglese)*
22. "Come si esegue il drop di una table su Postgres senza droppare a cascata anche i trigger e le foreign keys associate?" *(Coding - Puro Itanglish)*
23. "Devo fare il parsing di un corpus di testi antichi in latino medievale per trovare le radici etimologiche e le ricorrenze, che libreria uso e come la ottimizzo?" *(General vs Coding)*
24. "Sto progettando un videogioco in Unity. Mi serve la formula matematica per calcolare il rimbalzo di una sfera su un piano inclinato tenendo conto dell'attrito dell'aria, e poi mi serve capire se posso brevettare questa meccanica di gioco in Europa." *(Coding vs Math vs Rights - Lunghezza estrema)*
**25. "La badante di mia nonna si è licenziata senza preavviso. Se le trattengo l'ultimo stipendio per compensare i danni, sto violando l'articolo 2118 del codice civile o posso applicare la compensazione matematica dei crediti liquidi ed esigibili?" *(Rights vs Math - Caso studio specifico)***


### 💻 CODING: Sviluppo Mobile, Cloud, Game Dev e QA

*Nel DB attuale mancano quasi del tutto le tecnologie Cloud/Serverless, lo sviluppo per smartphone, i motori grafici e i test automatizzati E2E.*

1. Come si gestisce lo stato di un'applicazione mobile sviluppata in Flutter usando Riverpod o BLoC?
2. Spiegami come configurare e implementare una funzione Serverless su AWS Lambda usando il framework Serverless in Node.js.
3. Quali sono i design pattern più utilizzati per strutturare l'architettura di un videogioco in Unity3D con C#?
4. Scrivi il codice per implementare il raycasting in un motore grafico 3D usando l'API WebGL.
5. Come si configura un ambiente di test End-to-End (E2E) per un'applicazione web usando Cypress o Playwright?
6. Spiegami i concetti di ownership e borrowing in Rust con un esempio pratico di gestione della memoria.
7. Come si implementa l'architettura a micro-frontend utilizzando Module Federation in Webpack?
8. Scrivi un contratto intelligente in Vyper per implementare una lotteria decentralizzata su blockchain Ethereum.
9. Come si ottimizza un'app Android nativa in Kotlin per ridurre il consumo di batteria in background?
10. Spiegami come utilizzare le coroutine di Kotlin per effettuare chiamate di rete asincrone senza bloccare il thread principale.
11. Qual è la differenza tra l'uso di WebSocket e Server-Sent Events (SSE) per un'applicazione di chat in tempo reale?
12. Scrivi un'espressione regolare complessa per fare il parsing e l'estrazione di dati strutturati da un file di log server Apache.

### 📐 MATH: Topologia, Analisi Complessa, Teoria dei Grafi e Code

*Il DB ha molta analisi reale e algebra, ma manca di topologia, calcolo sui complessi, ricerca operativa avanzata (teoria delle code) e geometria differenziale astratta.*

13. Calcola l'integrale di linea lungo una curva chiusa nel piano complesso utilizzando il Teorema dei Residui di Cauchy.
14. Dimostra il Piccolo Teorema di Fermat e spiegami la sua utilità nell'aritmetica modulare e nella crittografia.
15. Spiega i concetti base della topologia generale: insiemi aperti, chiusi, intorni e spazi di Hausdorff.
16. Dimostra che il gruppo fondamentale del cerchio S1 è isomorfo al gruppo additivo dei numeri interi.
17. Calcola la probabilità di stato stazionario per un sistema di code M/M/1 utilizzando la teoria delle catene di Markov a tempo continuo.
18. Enuncia e dimostra il Teorema dei quattro colori per la colorazione dei grafi planari in teoria dei grafi.
19. Trova il polinomio cromatico di un grafo bipartito completo e spiegane il significato combinatorio.
20. Spiega la differenza tra geometria iperbolica, ellittica ed euclidea e il ruolo del quinto postulato di Euclide.
21. Definisci il concetto di varietà differenziabile e spiega come si calcola lo spazio tangente in un punto nella geometria differenziale.
22. Applica la trasformazione conforme (o mappa conforme) per risolvere un problema di potenziale elettrostatico nel piano complesso.
23. Risolvi un problema di programmazione dinamica utilizzando le equazioni di Bellman per un processo decisionale di Markov.
24. Definisci i numeri p-adici e spiega la loro costruzione a partire dalla metrica p-adica sui numeri razionali.
25. Enuncia la Congettura di Poincaré (ora teorema di Perelman) e spiegane l'importanza nella topologia delle varietà tridimensionali.

### ⚖️ RIGHTS: Cyber Law, Diritto Tributario, Sanitario e Militare

*Siamo coperti su civile/penale/GDPR, ma ci mancano le nuove leggi tech europee, il diritto sanitario (malpractice), il diritto degli animali e il diritto militare/marittimo.*

26. Cosa prevede il nuovo Regolamento Europeo sull'Intelligenza Artificiale (AI Act) riguardo ai sistemi ad alto rischio?
27. Quali sono gli obblighi normativi previsti dal Digital Services Act (DSA) per le piattaforme online di grandissime dimensioni?
28. Spiega la giurisdizione e le normative del Diritto della Navigazione per i soccorsi in mare in acque internazionali.
29. Quali sono le sanzioni e le procedure previste dal Codice Penale Militare di Pace per il reato di insubordinazione?
30. Come funziona il meccanismo dell'inversione contabile (Reverse Charge) nell'applicazione dell'IVA in edilizia per il diritto tributario?
31. Quali sono i requisiti legali e le procedure per l'ottenimento della certificazione di B-Corp o Società Benefit in Italia?
32. Cosa prevede la legislazione italiana in materia di tutela del benessere animale e maltrattamento di animali domestici (L. 189/2004)?
33. Spiega la responsabilità civile e penale del medico in caso di errore diagnostico e colpa medica secondo la Legge Gelli-Bianco.
34. Qual è la procedura legale per la dichiarazione di morte presunta e quali sono i suoi effetti giuridici sui beni dello scomparso?
35. Come viene regolamentato il diritto d'autore per le opere create da dipendenti durante l'orario di lavoro o su commissione aziendale?
36. Spiega la disciplina del trasferimento d'azienda e le tutele previste per i crediti dei lavoratori secondo l'art. 2112 del codice civile.
37. Quali sono i presupposti giuridici e le procedure processuali per richiedere l'interdizione perpetua dai pubblici uffici?
38. Cosa stabilisce il Codice del Terzo Settore (D.Lgs. 117/2017) riguardo alle agevolazioni fiscali per le ONLUS e le associazioni di volontariato?

### 🌍 GENERAL: Macroeconomia, Linguistica, Agronomia e Musica Avanzata

*General ha molte ricette e fai-da-te, ma mancano l'economia (inflazione, borsa), l'agricoltura/botanica pratica, l'analisi logica/linguistica e la teoria musicale armonica.*

39. Spiegami le cause e le conseguenze dell'inflazione economica e come le banche centrali usano i tassi di interesse per controllarla.
40. Qual è la differenza strutturale tra lingue agglutinanti, flessive e isolanti nella linguistica generale?
41. Come funziona il meccanismo del Quantitative Easing e in che modo impatta sul debito pubblico di un Paese?
42. Spiegami i principi della permacultura e come progettare un orto sinergico sostenibile partendo da zero.
43. Quali sono le regole dell'armonia tonale e come si costruisce una progressione di accordi II-V-I nel jazz?
44. Come si effettua l'analisi logica e grammaticale di una frase complessa con proposizioni subordinate relative e causali?
45. Quali sono i fondamenti dell'apicoltura e come si gestisce un'arnia per la produzione di miele nel primo anno?
46. Spiegami le regole di composizione fotografica, come la regola dei terzi, le linee guida e la profondità di campo.
47. Qual è la differenza chimica e di sapore tra i vari metodi di estrazione del caffè come espresso, moka, V60 e Aeropress?
48. Spiegami le basi della teoria dei colori: cos'è il cerchio di Itten, la saturazione e la luminosità?
49. Come si legge un bilancio aziendale di base? Spiegami la differenza tra stato patrimoniale e conto economico.
50. Quali sono le tecniche base per la rilegatura artigianale di un libro a mano con copertina rigida?
