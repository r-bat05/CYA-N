
frase: Dio esiste?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=2 (exp: >=1) tier=PRIMARY ✅  conf=0.900

frase: Lavoro part-time in uno studio e il titolare mi ha chiesto di dare un'occhiata a come automatizzare certi calcoli, quindi: scrivi script Python per calcolo TFR rispettando D.Lgs. 66/2003 con calcolo normativo. Non ho fretta, spiegami con calma.
❌ DOMAIN_ERR
  → CODING (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (exp: >=2) tier=PRIMARY ✅  conf=0.999

frase: Ci sono momenti della vita in cui ci si ferma a riflettere su quanto la conoscenza umana sia frutto di secoli di tentativi, errori, intuizioni geniali e pura ostinazione, e più ci penso più mi convinco che dietro ogni piccola cosa che diamo per scontata ci sia una storia lunghissima fatta di persone che hanno dedicato la vita a capire come funziona il mondo, ed è proprio con questo spirito, quasi di gratitudine verso chi è venuto prima di noi, che oggi ti volevo chiedere una cosa piccola ma per me significativa: quicksort complessità O(n log n)
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (exp: >=1) tier=FALLBACK ✅  conf=0.997

frase: Allora dunque, cerco di essere il più chiaro possibile anche se so che a volte mi perdo un po' quando scrivo, comunque il punto è che sto lavorando a un piccolo progetto per conto mio nel tempo libero, niente di che, giusto per tenermi allenato, e mi sono bloccato su una parte che riguarda la gestione degli errori quando leggo un file che potrebbe non esistere, quindi la domanda vera alla fine di tutto questo giro di parole è: come si gestiscono le eccezioni try except in Python quando apro un file?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=2 (exp: >=1) tier=PRIMARY ✅  conf=0.998

frase: Sto leggendo un libro di divulgazione sull'intelligenza artificiale e parla spesso di reti neurali e gradiente, argomenti affascinanti ma difficili: mi consigli altri libri di divulgazione scientifica scritti bene per chi non ha basi tecniche?
❌ DOMAIN_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (exp: >=1) tier=PRIMARY ✅  conf=0.769

frase: A lezione di economia il professore ha usato un sacco di formule e integrali per spiegare la curva di domanda e offerta, ed è stato interessante ma un po' ostico: mi consigli un modo semplice, non matematico, per capire il concetto base di domanda e offerta?
❌ BOTH_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=2 (exp: >=1) tier=PRIMARY ✅  conf=0.987

frase: Sto seguendo un corso serale di diritto per cultura personale, niente di professionale, e mi ha incuriosito molto come nascono le leggi in generale: mi racconti un po' la storia del diritto romano e come ha influenzato i sistemi giuridici moderni, giusto per curiosità?
❌ DOMAIN_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (exp: >=1) tier=PRIMARY ✅  conf=0.995

frase: Qual è l'equazione perfetta tra amore e libertà in una relazione secondo la filosofia stoica?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: >=2) tier=FALLBACK ❌ DIFF_ERR  conf=0.994

frase: Puoi farmi un esempio pratico?
❌ DOMAIN_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (exp: >=1) tier=FALLBACK ✅  conf=0.666

frase: Sto strugglando con questo bug nel mio codebase, il debugger non mi da nessun hint utile, help me capire cosa non va.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: >=2) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Ho sempre avuto un debole per le sfide intellettuali fin da bambino, mi affascina il modo in cui la tecnologia risolve problemi complessi: potresti implementare in C++ l'algoritmo A* per la ricerca del cammino minimo su una griglia con ostacoli, gestendo anche l'euristica ammissibile?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (exp: >=3) tier=PRIMARY ❌ DIFF_ERR  conf=0.998

frase: Scrivi una funzione in Go che legge un file riga per riga e conta le parole.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Come si ottimizza una query SQL lenta usando EXPLAIN ANALYZE?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.843

frase: Come si mappa una relazione molti-a-molti in SQLAlchemy?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Scrivi un decorator Python che misura il tempo di esecuzione di una funzione.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: Come si progetta un sistema di notifiche push scalabile con una coda di messaggi?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: Come si integra Elasticsearch per la ricerca full-text in un'app Python?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.998

frase: Come si implementa il pattern Circuit Breaker in un servizio Node.js?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: Come si scrive un lexer per un linguaggio di programmazione giocattolo?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Implementa un thread pool minimale in C++ con std::thread.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.997

frase: Come si carica un modulo solo quando serve in React con il code splitting?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Determina la derivata della funzione f(x) = x·ln(x) - x.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: Calcola l'integrale di x·sin(x) tra 0 e π.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Trova la soluzione di y'' - 3y' + 2y = 0 con y(0) = 0 e y'(0) = 1.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.998

frase: Calcola il flusso del campo F = (x, y, z) attraverso la sfera di raggio 2.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Dimostra la disuguaglianza di Cauchy-Schwarz.
❌ DOMAIN_ERR
  → GENERAL (exp: MATH) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.989

frase: Quanti anagrammi ha la parola MATEMATICA?
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.998

frase: Calcola l'area della regione compresa tra y = x^2 e y = 2x.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.998

frase: Verifica se la funzione f(x,y) = x^2 y è differenziabile nell'origine.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Calcola l'angolo tra i vettori (1,0,1) e (0,1,1).
❌ DOMAIN_ERR
  → CODING (exp: MATH) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.593

frase: Spiega la differenza tra limite destro e limite sinistro con un esempio.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=3 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.998

frase: Esegui un test di ipotesi sulla media con varianza nota, alfa 5% e campione di 36 osservazioni.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Applica il teorema di Cayley-Hamilton per calcolare l'inversa di una matrice 2x2.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: Quali sono gli elementi costitutivi del reato di corruzione?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=1.000

frase: Quali garanzie ha il lavoratore in caso di trasferimento d'azienda?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Cosa succede legalmente se un condomino non paga le spese condominiali?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=1.000

frase: Qual è la differenza tra reclusione e arresto nell'ordinamento penale?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.991

frase: Cos'è la clausola compromissoria e quando è valida?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: Cosa prevede la normativa sulla responsabilità del produttore per i prodotti difettosi?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: Cosa si intende per giusta causa di dimissioni?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: Che valore ha una scrittura privata non autenticata in tribunale?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=1.000

frase: Clima e meteo sono la stessa cosa?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.997

frase: Quali sono i libri più importanti della letteratura russa dell'Ottocento?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.990

frase: Come si formano le montagne?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.998

frase: Come funziona una centrale fotovoltaica?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.996

frase: Qual è la differenza tra un film d'autore e un film commerciale?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.958

frase: Quali sono i pianeti con gli anelli e perché?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.992

frase: Che cos'è l'effetto placebo?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.880

frase: Mia cugina mi ha regalato un libro di programmazione per il compleanno e vorrei sfogliarlo con calma, però mi serve una mano su un punto: cos'è una variabile globale in JavaScript e perché è considerata rischiosa?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: ragazzi oggi sono proprio in palla col pc, qualcuno sa dirmi come faccio a far girare uno script python all'avvio del raspberry senza accendere niente a mano?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Il mio code review è stato brutale: mi hanno scritto che devo fare il refactor di questa class perché viola il single responsibility principle, come la splitto in due senza cambiare le API pubbliche?
❌ DOMAIN_ERR
  → RIGHTS->CODING (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.970

frase: Da quando ho cambiato casa passo molto più tempo davanti allo schermo, la sera, e ho scoperto che programmare mi tranquillizza più di qualsiasi serie televisiva, anche se faccio una fatica enorme con i concetti più astratti e mi serve sempre qualcuno che me li spieghi con calma, senza darli per scontati, e quindi arrivo al punto: come si usa il blocco try/finally in Java e a cosa serve la parte finally?
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.914

frase: Sto aiutando mio nipote con i compiti e non voglio fargli vedere che ho dimenticato tutto, quindi di nascosto chiedo a te: come si risolve un'equazione di primo grado con le frazioni, tipo (x/2) + 3 = 7?
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.998

frase: Domani ho un colloquio in cui mi chiederanno di fare dei conti a mente e vorrei prepararmi con metodo, partendo dalle basi: come si calcola la probabilità di estrarre un asso da un mazzo di quaranta carte?
❌ DOMAIN_ERR
  → RIGHTS->MATH (exp: MATH) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.931

frase: In treno ho incontrato un professore in pensione che mi ha lasciato una curiosità, e adesso non riesco a pensare ad altro: come si dimostra che la radice quadrata di 5 è irrazionale?
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.997

frase: raga ma l'integrale di 1/x perché fa logaritmo? non l'ho mai capito davvero
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.998

frase: vabbè niente, secondo voi la probabilità condizionata come si calcola quando gli eventi non sono indipendenti
❌ DOMAIN_ERR
  → GENERAL (exp: MATH) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.384

frase: Negli ultimi mesi ho ripreso a leggere saggi di divulgazione scientifica e a guardare video sul funzionamento dell'universo, sull'infinito, sui paradossi dei numeri e sulle dimensioni nascoste, e tutto questo mi ha dato voglia di tornare alle basi con serietà, e quindi parto da una domanda precisa: come si calcola la somma dei primi cento numeri naturali con il trucco di Gauss e come si dimostra in generale?
❌ DOMAIN_ERR
  → GENERAL (exp: MATH) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.866

frase: Sto per comprare la mia prima casa insieme al mio compagno e tra mutui, agenzie e notai ho un po' di confusione, quindi chiedo a te per cominciare: che cos'è il compromesso e che differenza c'è con il rogito?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.693

frase: Ho appena aperto un piccolo negozio online e tra mille adempimenti non so da dove partire, ma uno alla volta: quali informazioni obbligatorie deve riportare un sito di e-commerce secondo la legge?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.470

frase: Da anni mi occupo di volontariato e un giorno vorrei fondare un'associazione con i miei amici, così per cominciare mi informo sulla parte burocratica: che differenza c'è tra associazione riconosciuta e non riconosciuta?
⚠ FOLLOWUP_ERR
  → RIGHTS (exp: RIGHTS) 
  followup=True (exp: False) ← WRONG  diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.999

frase: vabbè però il datore di lavoro può davvero obbligarmi a fare gli straordinari la domenica
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.996

frase: qualcuno sa dirmi se un prof può bocciarmi per colpa di una frase detta in classe? ho paura di aver esagerato
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.992

frase: Sto per fare il pitch a degli investitori e il mio cofounder vuole una clausola di vesting nello statuto, ma non capisco se sia lecita per una S.r.l.
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.998

frase: Con il mio compagno discutiamo da giorni, tra un conto da pagare e una bolletta da dividere, su dove andare in vacanza quest'estate: quali sono le mete più belle e poco costose in Europa a luglio?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.997

frase: scusate ma perché il caffè mi fa venire sonno invece di svegliarmi?? succede solo a me
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.997

frase: Per anni ho pensato che viaggiare fosse un lusso per altri e che la mia vita fosse destinata a restare tra casa e ufficio, ma una conversazione con un vecchio amico mi ha fatto cambiare idea e adesso sogno ogni sera di partire, magari con zaino in spalla e senza una meta precisa, ecco perché oggi ti chiedo: come si pianifica un viaggio in Interrail attraverso l'Europa?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.997

frase: In una sera di pioggia, rimasto solo in casa, ho ripensato alla musica che ascoltavo da ragazzo, ai concerti e ai dischi consumati, e a quanto certe canzoni siano capaci di riportare in vita interi periodi, e questo mi ha fatto venire voglia di approfondire la storia del rock, partendo da una domanda precisa: quali sono le caratteristiche del rock progressivo e quali band lo hanno reso famoso?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.997

frase: puntatori in C
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: Kotlin coroutine
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.996

frase: serie di Fourier
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: storia di Roma antica
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.996

frase: Heun Python ordine convergenza
✅ OK
  → MATH->CODING (exp: MATH->CODING) 
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.952

frase: Simpson Python stima errore
❌ DOMAIN_ERR
  → CODING (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Python informativa privacy automatica
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.964

frase: Python conservazione sostitutiva documenti
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.975

frase: dimostra rata mutuo normativa
❌ DOMAIN_ERR
  → RIGHTS (exp: RIGHTS->MATH) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=1.000

frase: modello matematico sanzione proporzionale
❌ DOMAIN_ERR
  → MATH (exp: RIGHTS->MATH) ← WRONG
  followup=False (exp: False)   diff=3 (exp: 3) tier=PRIMARY ✅  conf=0.998

frase: Implementa in Python l'algoritmo di Euclide esteso e dimostra l'identità di Bézout.
❌ DOMAIN_ERR
  → CODING (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=1.000

frase: Scrivi in Python un integratore di Gauss-Legendre a tre punti e mostra perché è esatto per polinomi fino al quinto grado.
✅ OK
  → MATH->CODING (exp: MATH->CODING) 
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.902

frase: Implementa un generatore di numeri pseudocasuali lineare congruenziale e dimostra la condizione di periodo massimo.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: Implementa il gradiente coniugato precondizionato e dimostra la coniugazione delle direzioni di ricerca.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.992

frase: Implementa il metodo di Jacobi per gli autovalori e dimostra perché le rotazioni riducono la norma dei termini fuori diagonale.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (exp: 3) tier=PRIMARY ✅  conf=0.999

frase: Sono sempre stato colpito da quanto la matematica spieghi i giochi d'azzardo, perciò scrivi uno script Python che simula la rovina del giocatore e dimostra la probabilità di rovina con le catene di Markov.
❌ DOMAIN_ERR
  → CODING (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (exp: 3) tier=PRIMARY ✅  conf=0.997

frase: Il mio professore sostiene che chi non sa dimostrare non sa programmare, quindi ci provo davvero: implementa in Python la ricerca binaria sui reali per approssimare una radice quadrata e dimostra che l'errore si dimezza a ogni iterazione.
❌ DOMAIN_ERR
  → CODING (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.999

frase: Quando ho scoperto che gli scacchi si analizzano con la teoria dei giochi mi si è aperto un mondo, quindi scrivi un programma Python per il minimax con potatura alfa-beta e dimostra che non cambia il risultato rispetto al minimax semplice.
❌ DOMAIN_ERR
  → CODING (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.996

frase: Dopo aver visto un documentario sul GPS mi sono incuriosito ai calcoli che ci stanno dietro: implementa in Python il metodo di Gauss-Newton per i minimi quadrati non lineari e deriva la formula di aggiornamento.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (exp: 3) tier=PRIMARY ✅  conf=0.998

frase: Scrivi un plugin WordPress che gestisce il banner dei cookie secondo le linee guida del Garante.
❌ DOMAIN_ERR
  → CODING (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.999

frase: Implementa un sistema di gestione ferie che rispetti il minimo di quattro settimane annuali previsto dalla normativa.
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.980

frase: Scrivi uno script che verifica la presenza della clausola di recesso di quattordici giorni nei contratti online dei consumatori.
❌ DOMAIN_ERR
  → RIGHTS (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.997

frase: Codice per un sistema di prenotazione ferie che impedisce di superare i limiti previsti dal CCNL del turismo.
❌ DOMAIN_ERR
  → RIGHTS (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.998

frase: Sviluppa un tool in Python che confronta le licenze delle librerie usate con quelle consentite dalla policy legale dell'azienda.
❌ DOMAIN_ERR
  → RIGHTS (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Il titolare di un piccolo hotel mi ha chiesto una mano con le schedine degli ospiti e non voglio sbagliare niente: sviluppa un modulo Python che invia i dati alla Questura nel rispetto della normativa di pubblica sicurezza.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.984

frase: Dopo l'ultima ispezione la mia azienda vuole mettersi in regola con tutto e a me tocca la parte software: implementa un sistema Python che traccia le ore lavorate per rispettare i riposi minimi previsti dalla legge.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.943

frase: Qual è la formula matematica per calcolare l'assegno unico per i figli in funzione dell'ISEE secondo la normativa?
✅ OK
  → RIGHTS->MATH (exp: RIGHTS->MATH) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.900

frase: Dimostra la formula per il calcolo dell'indennità di disoccupazione NASpI in base alla retribuzione media.
✅ OK
  → RIGHTS->MATH (exp: RIGHTS->MATH) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.977

frase: Dimostra matematicamente il calcolo della quota indisponibile in presenza di due figli e un coniuge superstite.
❌ DOMAIN_ERR
  → MATH (exp: RIGHTS->MATH) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Mia sorella lavora in una cooperativa che sta chiudendo e vorrei aiutarla: dimostra con un modello matematico come si determina l'integrazione salariale in base alle ore di sospensione previste dalla normativa.
❌ DOMAIN_ERR
  → RIGHTS (exp: RIGHTS->MATH) ← WRONG
  followup=False (exp: False)   diff=3 (exp: 3) tier=PRIMARY ✅  conf=0.998

frase: Cosa prevede il codice della strada per il sorpasso in curva?
❌ DOMAIN_ERR
  → MATH (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.999

frase: Che cos'è il codice rosso nei casi di violenza domestica?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Spiega la formula della varianza campionaria e perché si divide per n-1.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Risolvi la ricorrenza T(n) = 2T(n/2) + n con il teorema dell'esperto.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: Quanto tempo di recupero aggiunge l'arbitro per le interruzioni del VAR?
❌ DOMAIN_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.941

frase: Dopo il colloquio ho fatto un debug mentale di tutte le risposte che avevo dato.
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.993

frase: Come posso ottimizzare lo spazio in valigia per un viaggio di due settimane?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.995

frase: La sentenza finale del talent show ha diviso il pubblico: perché le giurie sbagliano spesso?
❌ DOMAIN_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.993

frase: Come si calcola l'imposta di bollo su un contratto di locazione?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: Come si calcola l'imposta dovuta con la cedolare secca sull'affitto?
❌ DOMAIN_ERR
  → RIGHTS->MATH (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.968

frase: Qual è la rata mensile di un prestito di 3000 euro restituito in 12 rate senza interessi?
❌ DOMAIN_ERR
  → RIGHTS->MATH (exp: MATH) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.792

frase: e se una delle promise fallisce?
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=True (exp: True)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.859

frase: mostrami un esempio con un'eccezione
❌ DOMAIN_ERR
  → MATH (exp: CODING) ← WRONG
  followup=True (exp: True)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.998

frase: potresti riscriverlo in Kotlin?
✅ OK
  → CODING (exp: CODING) 
  followup=True (exp: True)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.997

frase: e se i record sono milioni?
❌ DOMAIN_ERR
  → RIGHTS->CODING (exp: CODING) ← WRONG
  followup=True (exp: True)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.863

frase: puoi aggiungere la gestione degli errori?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=False (exp: True) ← WRONG  diff=3 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.961

frase: puoi fare un esempio numerico con 30 anni di contributi?
❌ BOTH_ERR
  → RIGHTS->MATH (exp: MATH) ← WRONG
  followup=False (exp: True) ← WRONG  diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.942

frase: non mi è chiaro il passaggio 3
⚠ FOLLOWUP_ERR
  → MATH (exp: MATH) 
  followup=False (exp: True) ← WRONG  diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.997

frase: e se il discriminante fosse negativo?
✅ OK
  → MATH (exp: MATH) 
  followup=True (exp: True)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: funziona anche per la radice di 4?
✅ OK
  → MATH (exp: MATH) 
  followup=True (exp: True)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.628

frase: perché non si può sostituire direttamente?
✅ OK
  → MATH (exp: MATH) 
  followup=True (exp: True)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.998

frase: quando posso chiederne l'anticipo?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=True (exp: True)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.993

frase: e chi paga le tasse?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=True (exp: True)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.934

frase: e se non le godo entro l'anno?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=True (exp: True)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.838

frase: Capita la regola generale, ma nel mio caso specifico mi hanno rinnovato il contratto quattro volte di fila e vorrei sapere se la cosa è regolare o se posso pretendere l'assunzione a tempo indeterminato
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=True (exp: True)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.973

frase: da dove comincio se sono sedentario?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=False (exp: True) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.998

frase: vorrei qualcosa di meno turistico
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=False (exp: True) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.998

frase: Come si legge un file di testo in Python?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.997

frase: Come si crea un repository remoto su GitHub?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.869

frase: Come si configura un server Express con TypeScript?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.973

frase: Calcola il determinante della matrice [[1,2],[3,4]].
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: Quanti modi ci sono di scegliere 3 elementi tra 10?
⚠ FOLLOWUP_ERR
  → MATH (exp: MATH) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.997

frase: Trova il volume di una sfera di raggio 3.
⚠ FOLLOWUP_ERR
  → MATH (exp: MATH) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.977

frase: Come funziona l'indennità di disoccupazione?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.645

frase: Chi può essere nominato tutore di un minore?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.961

frase: Chi ha inventato il cinema?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.998

frase: come si dice grazie in giapponese?
❌ BOTH_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.856

frase: come si prepara un buon tè verde?
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.828

frase: come si prepara la panna cotta?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.719

frase: Calcola la derivata di tan(2x).
⚠ FOLLOWUP_ERR
  → MATH (exp: MATH) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.997

frase: Trova la dimensione dell'immagine della matrice [[1,0,1],[0,1,1],[1,1,2]].
❌ DOMAIN_ERR
  → CODING (exp: MATH) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.534

frase: Cosa succede se non si paga l'affitto per tre mesi?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.939

frase: Come vengono pagati i giorni di ferie non usati quando si lascia il lavoro?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.788

frase: Come si inserisce una riga in una tabella SQLite da Python?
❌ DOMAIN_ERR
  → MATH (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.990

frase: Come si usa il comando chmod in Linux?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.992

frase: Come si fa a denunciare un vicino rumoroso?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.997

frase: Come si calcola la media dei valori di una lista in Python?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.994

frase: Scrivi in C++ una stack con push e pop su vettore dinamico.
❌ DOMAIN_ERR
  → RIGHTS->CODING (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.944

frase: Calcola l'integrale di x^3 da 0 a 2.
⚠ FOLLOWUP_ERR
  → MATH (exp: MATH) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.997

frase: Trova l'inversa della matrice [[2,1],[1,1]].
⚠ FOLLOWUP_ERR
  → MATH (exp: MATH) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Implementa in Python la ricerca delle radici con il metodo delle secanti e dimostra la convergenza superlineare.
⚠ FOLLOWUP_ERR
  → MATH->CODING (exp: MATH->CODING) 
  followup=True (exp: False) ← WRONG  diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.917

frase: Scrivi uno script Python che verifica la conformità GDPR di un modulo di raccolta dati.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.958

frase: Scrivi il codice per cifrare i dati sensibili dei clienti come previsto dal GDPR.
❌ DOMAIN_ERR
  → RIGHTS (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: Deriva con un modello matematico il calcolo dell'indennità di fine rapporto previsto dalla legge.
✅ OK
  → RIGHTS->MATH (exp: RIGHTS->MATH) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.928
