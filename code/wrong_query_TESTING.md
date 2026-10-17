
frase: Dio esiste?
❌ BOTH_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (runtime=1) (exp: >=1) tier=FALLBACK ✅  conf=0.455

frase: Da quando è entrato in vigore il GDPR ne sento parlare ovunque e non ho mai capito bene i dettagli, quindi ti chiedo: cosa prevede il GDPR per la notifica di un data breach entro 72 ore? Spiegamelo come se lo spiegassi a qualcuno alle prime armi.
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=2 (runtime=2) (exp: >=1) tier=PRIMARY ✅  conf=0.443

frase: Cambiando completamente argomento, ma è da stamattina che ci penso e non trovo pace: consigliami un ristorante a Roma, magari qualcosa di tipico, non il solito posto turistico.
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (runtime=1) (exp: >=1) tier=FALLBACK ✅  conf=0.943

frase: Ci sono momenti della vita in cui ci si ferma a riflettere su quanto la conoscenza umana sia frutto di secoli di tentativi, errori, intuizioni geniali e pura ostinazione, e più ci penso più mi convinco che dietro ogni piccola cosa che diamo per scontata ci sia una storia lunghissima fatta di persone che hanno dedicato la vita a capire come funziona il mondo, ed è proprio con questo spirito, quasi di gratitudine verso chi è venuto prima di noi, che oggi ti volevo chiedere una cosa piccola ma per me significativa: quicksort complessità O(n log n)
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: >=1) tier=FALLBACK ✅  conf=0.921

frase: Sto leggendo un libro di divulgazione sull'intelligenza artificiale e parla spesso di reti neurali e gradiente, argomenti affascinanti ma difficili: mi consigli altri libri di divulgazione scientifica scritti bene per chi non ha basi tecniche?
❌ DOMAIN_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=3 (runtime=3) (exp: >=1) tier=PRIMARY ✅  conf=0.322

frase: A lezione di economia il professore ha usato un sacco di formule e integrali per spiegare la curva di domanda e offerta, ed è stato interessante ma un po' ostico: mi consigli un modo semplice, non matematico, per capire il concetto base di domanda e offerta?
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (runtime=2) (exp: >=1) tier=PRIMARY ✅  conf=0.580

frase: Sto seguendo un corso serale di diritto per cultura personale, niente di professionale, e mi ha incuriosito molto come nascono le leggi in generale: mi racconti un po' la storia del diritto romano e come ha influenzato i sistemi giuridici moderni, giusto per curiosità?
❌ DOMAIN_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (runtime=2) (exp: >=1) tier=PRIMARY ✅  conf=0.664

frase: Come funziona la tecnologia del VAR nel calcio e quanti replay controlla l'arbitro?
❌ DOMAIN_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: >=1) tier=FALLBACK ✅  conf=0.453

frase: Qual è l'equazione perfetta tra amore e libertà in una relazione secondo la filosofia stoica?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: >=2) tier=FALLBACK ❌ DIFF_ERR  conf=0.428

frase: che ore sono?
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: >=1) tier=FALLBACK ✅  conf=0.535

frase: grazie mille
❌ BOTH_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=2 (runtime=2) (exp: >=1) tier=PRIMARY ✅  conf=0.873

frase: Sto strugglando con questo bug nel mio codebase, il debugger non mi da nessun hint utile, help me capire cosa non va.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: >=2) tier=FALLBACK ❌ DIFF_ERR  conf=0.924

frase: Il mio prof di computer science vuole che faccia il deployment su un cloud provider entro stasera, non ho la minima idea di come iniziare.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: >=2) tier=FALLBACK ❌ DIFF_ERR  conf=0.818

frase: Spiega come funziona l'ereditarietà prototipale in JavaScript.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.853

frase: Come si mappa una relazione molti-a-molti in SQLAlchemy?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.852

frase: Cosa significa che una funzione è pura in programmazione funzionale?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.350

frase: Come si progetta un sistema di notifiche push scalabile con una coda di messaggi?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.929

frase: Come si integra Elasticsearch per la ricerca full-text in un'app Python?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.761

frase: Come si scrive un lexer per un linguaggio di programmazione giocattolo?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.870

frase: Come si aggiunge un campo a un modello Django e si applica la migrazione?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.936

frase: Come si configura un tunnel VPN WireGuard su un server Linux?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.936

frase: Implementa un thread pool minimale in C++ con std::thread.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.930

frase: Come si carica un modulo solo quando serve in React con il code splitting?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.951

frase: Determina la derivata della funzione f(x) = x·ln(x) - x.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.910

frase: Trova la soluzione di y'' - 3y' + 2y = 0 con y(0) = 0 e y'(0) = 1.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.934

frase: Quanti anagrammi ha la parola MATEMATICA?
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.748

frase: Calcola l'area della regione compresa tra y = x^2 e y = 2x.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.953

frase: Risolvi la disequazione |2x - 1| < 5.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.927

frase: Verifica se la funzione f(x,y) = x^2 y è differenziabile nell'origine.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.887

frase: Spiega la differenza tra limite destro e limite sinistro con un esempio.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.800

frase: Calcola l'integrale improprio di e^(-x) da 0 a infinito.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.881

frase: Trova x sapendo che 2^(x+1) = 32.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.916

frase: Dimostra che la composizione di due funzioni iniettive è iniettiva.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.912

frase: Applica il teorema di Cayley-Hamilton per calcolare l'inversa di una matrice 2x2.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.935

frase: Quali sono gli elementi costitutivi del reato di corruzione?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.916

frase: Quali garanzie ha il lavoratore in caso di trasferimento d'azienda?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.951

frase: È legale registrare una telefonata senza avvisare l'altra persona?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.938

frase: Che cos'è una S.a.s. e come rispondono i soci accomandanti?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.902

frase: Cosa succede legalmente se un condomino non paga le spese condominiali?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.917

frase: Qual è la differenza tra reclusione e arresto nell'ordinamento penale?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.955

frase: Cos'è la clausola compromissoria e quando è valida?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.957

frase: Cosa prevede la normativa sulla responsabilità del produttore per i prodotti difettosi?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.927

frase: Cosa si intende per giusta causa di dimissioni?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.945

frase: Quali sono i libri più importanti della letteratura russa dell'Ottocento?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.935

frase: Come funziona una centrale fotovoltaica?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.733

frase: Qual è la differenza tra un film d'autore e un film commerciale?
❌ DOMAIN_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 2) tier=PRIMARY ✅  conf=0.717

frase: Quali sono i pianeti con gli anelli e perché?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.943

frase: Che cos'è l'effetto placebo?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.892

frase: Mia cugina mi ha regalato un libro di programmazione per il compleanno e vorrei sfogliarlo con calma, però mi serve una mano su un punto: cos'è una variabile globale in JavaScript e perché è considerata rischiosa?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.671

frase: ragazzi oggi sono proprio in palla col pc, qualcuno sa dirmi come faccio a far girare uno script python all'avvio del raspberry senza accendere niente a mano?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.919

frase: Sto strugglando con il merge di due feature branch, il lead vuole la PR entro domani e continuo a beccare conflitti sullo stesso file di config, quale approccio conviene per risolverli senza rompere la build?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.765

frase: Il mio code review è stato brutale: mi hanno scritto che devo fare il refactor di questa class perché viola il single responsibility principle, come la splitto in due senza cambiare le API pubbliche?
❌ DOMAIN_ERR
  → RIGHTS (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.239

frase: Da quando ho cambiato casa passo molto più tempo davanti allo schermo, la sera, e ho scoperto che programmare mi tranquillizza più di qualsiasi serie televisiva, anche se faccio una fatica enorme con i concetti più astratti e mi serve sempre qualcuno che me li spieghi con calma, senza darli per scontati, e quindi arrivo al punto: come si usa il blocco try/finally in Java e a cosa serve la parte finally?
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.492

frase: Domani ho un colloquio in cui mi chiederanno di fare dei conti a mente e vorrei prepararmi con metodo, partendo dalle basi: come si calcola la probabilità di estrarre un asso da un mazzo di quaranta carte?
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.418

frase: Tempo fa ho abbandonato gli studi di ingegneria e adesso, per pura soddisfazione personale, sto riprendendo in mano i vecchi appunti, ma mi sono bloccato su un passaggio: come si calcola l'integrale di x per e^x per parti?
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.907

frase: raga ma l'integrale di 1/x perché fa logaritmo? non l'ho mai capito davvero
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.817

frase: Sto strugglando con l'exam di analisi 1 e il prof ha detto che uscirà un problema sugli integrali impropri, help me a capire come si stabilisce se l'integrale di 1/x^2 da 1 a infinito converge.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.908

frase: Sto per comprare la mia prima casa insieme al mio compagno e tra mutui, agenzie e notai ho un po' di confusione, quindi chiedo a te per cominciare: che cos'è il compromesso e che differenza c'è con il rogito?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.792

frase: scusate ma tipo se prendo una multa all'estero con l'auto a noleggio la devo pagare lo stesso?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.918

frase: vabbè però il datore di lavoro può davvero obbligarmi a fare gli straordinari la domenica
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.740

frase: qualcuno sa dirmi se un prof può bocciarmi per colpa di una frase detta in classe? ho paura di aver esagerato
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.454

frase: Sto per fare il pitch a degli investitori e il mio cofounder vuole una clausola di vesting nello statuto, ma non capisco se sia lecita per una S.r.l.
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.919

frase: Con il mio compagno discutiamo da giorni, tra un conto da pagare e una bolletta da dividere, su dove andare in vacanza quest'estate: quali sono le mete più belle e poco costose in Europa a luglio?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.922

frase: scusate ma perché il caffè mi fa venire sonno invece di svegliarmi?? succede solo a me
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.938

frase: Per anni ho pensato che viaggiare fosse un lusso per altri e che la mia vita fosse destinata a restare tra casa e ufficio, ma una conversazione con un vecchio amico mi ha fatto cambiare idea e adesso sogno ogni sera di partire, magari con zaino in spalla e senza una meta precisa, ecco perché oggi ti chiedo: come si pianifica un viaggio in Interrail attraverso l'Europa?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.904

frase: In una sera di pioggia, rimasto solo in casa, ho ripensato alla musica che ascoltavo da ragazzo, ai concerti e ai dischi consumati, e a quanto certe canzoni siano capaci di riportare in vita interi periodi, e questo mi ha fatto venire voglia di approfondire la storia del rock, partendo da una domanda precisa: quali sono le caratteristiche del rock progressivo e quali band lo hanno reso famoso?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.946

frase: Kotlin coroutine
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.842

frase: numeri complessi forma polare
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.880

frase: contratto preliminare
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.941

frase: obbligo di mantenimento
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.955

frase: storia di Roma antica
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.957

frase: Heun Python ordine convergenza
❌ DOMAIN_ERR
  → CODING (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.630

frase: Simpson Python stima errore
❌ DOMAIN_ERR
  → CODING (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.641

frase: Python informativa privacy automatica
❌ DOMAIN_ERR
  → CODING (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.249

frase: Python conservazione sostitutiva documenti
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.712

frase: dimostra rata mutuo normativa
❌ DOMAIN_ERR
  → RIGHTS (exp: RIGHTS->MATH) ← WRONG
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.933

frase: modello matematico sanzione proporzionale
❌ DOMAIN_ERR
  → MATH (exp: RIGHTS->MATH) ← WRONG
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 3) tier=PRIMARY ✅  conf=0.342

frase: Implementa in Python l'algoritmo di Euclide esteso e dimostra l'identità di Bézout.
❌ DOMAIN_ERR
  → CODING (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.755

frase: Scrivi in Python un integratore di Gauss-Legendre a tre punti e mostra perché è esatto per polinomi fino al quinto grado.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.338

frase: Implementa un generatore di numeri pseudocasuali lineare congruenziale e dimostra la condizione di periodo massimo.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 3) tier=PRIMARY ✅  conf=0.423

frase: Implementa il gradiente coniugato precondizionato e dimostra la coniugazione delle direzioni di ricerca.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 3) tier=PRIMARY ✅  conf=0.295

frase: Implementa il metodo di Jacobi per gli autovalori e dimostra perché le rotazioni riducono la norma dei termini fuori diagonale.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 3) tier=PRIMARY ✅  conf=0.747

frase: Sono sempre stato colpito da quanto la matematica spieghi i giochi d'azzardo, perciò scrivi uno script Python che simula la rovina del giocatore e dimostra la probabilità di rovina con le catene di Markov.
❌ DOMAIN_ERR
  → CODING (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 3) tier=PRIMARY ✅  conf=0.500

frase: Il mio professore sostiene che chi non sa dimostrare non sa programmare, quindi ci provo davvero: implementa in Python la ricerca binaria sui reali per approssimare una radice quadrata e dimostra che l'errore si dimezza a ogni iterazione.
❌ DOMAIN_ERR
  → CODING (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.359

frase: Quando ho scoperto che gli scacchi si analizzano con la teoria dei giochi mi si è aperto un mondo, quindi scrivi un programma Python per il minimax con potatura alfa-beta e dimostra che non cambia il risultato rispetto al minimax semplice.
❌ DOMAIN_ERR
  → CODING (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.450

frase: Dopo aver visto un documentario sul GPS mi sono incuriosito ai calcoli che ci stanno dietro: implementa in Python il metodo di Gauss-Newton per i minimi quadrati non lineari e deriva la formula di aggiornamento.
❌ DOMAIN_ERR
  → CODING (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 3) tier=PRIMARY ✅  conf=0.295

frase: Scrivi un plugin WordPress che gestisce il banner dei cookie secondo le linee guida del Garante.
❌ DOMAIN_ERR
  → CODING (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 2) tier=PRIMARY ✅  conf=0.709

frase: Implementa un sistema di gestione ferie che rispetti il minimo di quattro settimane annuali previsto dalla normativa.
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 2) tier=PRIMARY ✅  conf=0.657

frase: Scrivi uno script che verifica la presenza della clausola di recesso di quattordici giorni nei contratti online dei consumatori.
❌ DOMAIN_ERR
  → RIGHTS (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 2) tier=PRIMARY ✅  conf=0.785

frase: Codice per un sistema di prenotazione ferie che impedisce di superare i limiti previsti dal CCNL del turismo.
❌ DOMAIN_ERR
  → RIGHTS (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.874

frase: Il titolare di un piccolo hotel mi ha chiesto una mano con le schedine degli ospiti e non voglio sbagliare niente: sviluppa un modulo Python che invia i dati alla Questura nel rispetto della normativa di pubblica sicurezza.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (runtime=2) (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.653

frase: Dopo l'ultima ispezione la mia azienda vuole mettersi in regola con tutto e a me tocca la parte software: implementa un sistema Python che traccia le ore lavorate per rispettare i riposi minimi previsti dalla legge.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.821

frase: So che è un tema noioso ma devo consegnare il progetto entro fine mese: sviluppa uno script Python che verifica se un testo contrattuale contiene le clausole obbligatorie previste dal Codice del Consumo.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (runtime=2) (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.894

frase: Sono il responsabile IT di un comune di provincia e dobbiamo pubblicare i dati degli appalti: sviluppa uno script che pubblica gli atti in formato aperto rispettando gli obblighi di trasparenza del D.Lgs. 33/2013.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.839

frase: Qual è la formula matematica per determinare il deposito cauzionale commisurato al canone secondo la legge sulle locazioni?
✅ OK
  → RIGHTS->MATH (exp: RIGHTS->MATH) 
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.850

frase: Dimostra matematicamente il calcolo della quota indisponibile in presenza di due figli e un coniuge superstite.
❌ DOMAIN_ERR
  → MATH (exp: RIGHTS->MATH) ← WRONG
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 3) tier=PRIMARY ✅  conf=0.864

frase: Dimostra matematicamente la formula dell'ammortamento a quote costanti dei beni strumentali e i limiti fiscali di deducibilità.
✅ OK
  → RIGHTS->MATH (exp: RIGHTS->MATH) 
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.909

frase: In C++ come ottengo il valore assoluto di un intero senza usare abs()?
❌ DOMAIN_ERR
  → MATH (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.400

frase: Cosa prevede il codice della strada per il sorpasso in curva?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.323

frase: Spiega la formula della varianza campionaria e perché si divide per n-1.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=3 (runtime=3) (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.809

frase: Risolvi la ricorrenza T(n) = 2T(n/2) + n con il teorema dell'esperto.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.893

frase: Quanto tempo di recupero aggiunge l'arbitro per le interruzioni del VAR?
❌ DOMAIN_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.308

frase: Come posso ottimizzare lo spazio in valigia per un viaggio di due settimane?
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.561

frase: La sentenza finale del talent show ha diviso il pubblico: perché le giurie sbagliano spesso?
❌ DOMAIN_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.897

frase: Come si calcola l'imposta di bollo su un contratto di locazione?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.375

frase: Come si determina l'aliquota IRPEF applicabile a un reddito di 40.000 euro?
❌ DOMAIN_ERR
  → RIGHTS->MATH (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 2) tier=PRIMARY ✅  conf=0.850

frase: Come si calcola l'imposta dovuta con la cedolare secca sull'affitto?
❌ DOMAIN_ERR
  → RIGHTS->MATH (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 2) tier=PRIMARY ✅  conf=0.870

frase: Calcola il valore finale di 5000 euro con interesse semplice del 2% annuo per 4 anni.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.821

frase: Qual è la rata mensile di un prestito di 3000 euro restituito in 12 rate senza interessi?
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.470

frase: puoi gestire anche il caso del file inesistente?
✅ OK
  → CODING (exp: CODING) 
  followup=True (exp: True)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.918

frase: e se una delle promise fallisce?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=False (exp: True) ← WRONG  diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.741

frase: mostrami un esempio con un'eccezione
❌ DOMAIN_ERR
  → MATH (exp: CODING) ← WRONG
  followup=True (exp: True)   diff=2 (runtime=2) (exp: 2) tier=PRIMARY ✅  conf=0.374

frase: e se i record sono milioni?
❌ DOMAIN_ERR
  → RIGHTS->CODING (exp: CODING) ← WRONG
  followup=True (exp: True)   diff=2 (runtime=2) (exp: 2) tier=PRIMARY ✅  conf=0.786

frase: puoi aggiungere la gestione degli errori?
✅ OK
  → CODING (exp: CODING) 
  followup=True (exp: True)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.514

frase: puoi fare un esempio numerico con 30 anni di contributi?
❌ DOMAIN_ERR
  → RIGHTS->MATH (exp: MATH) ← WRONG
  followup=True (exp: True)   diff=3 (runtime=3) (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.765

frase: non mi è chiaro il passaggio 3
⚠ FOLLOWUP_ERR
  → MATH (exp: MATH) 
  followup=False (exp: True) ← WRONG  diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.378

frase: e se il discriminante fosse negativo?
✅ OK
  → MATH (exp: MATH) 
  followup=True (exp: True)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.933

frase: funziona anche per la radice di 4?
✅ OK
  → MATH (exp: MATH) 
  followup=True (exp: True)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.866

frase: e se c'è un figlio che rinuncia?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=True (exp: True)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.882

frase: quando posso chiederne l'anticipo?
⚠ FOLLOWUP_ERR
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: True) ← WRONG  diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.352

frase: e chi paga le tasse?
⚠ FOLLOWUP_ERR
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: True) ← WRONG  diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.773

frase: Capita la regola generale, ma nel mio caso specifico mi hanno rinnovato il contratto quattro volte di fila e vorrei sapere se la cosa è regolare o se posso pretendere l'assunzione a tempo indeterminato
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=True (exp: True)   diff=1 (runtime=1) (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.927

frase: Come si legge un file di testo in Python?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.955

frase: Come si crea un repository remoto su GitHub?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.924

frase: Come si configura un server Express con TypeScript?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.934

frase: Calcola il determinante della matrice [[1,2],[3,4]].
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.942

frase: Quali sono le regole per registrare un'auto acquistata da un privato?
⚠ FOLLOWUP_ERR
  → RIGHTS (exp: RIGHTS) 
  followup=True (exp: False) ← WRONG  diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.936

frase: Chi può essere nominato tutore di un minore?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.807

frase: Chi ha inventato il cinema?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.957

frase: come si fa la cacio e pepe?
❌ DOMAIN_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.848

frase: come si dice grazie in giapponese?
❌ DOMAIN_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.597

frase: è tardi, vado a dormire: a domani!
❌ DOMAIN_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.692

frase: come si prepara la panna cotta?
❌ DOMAIN_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.658

frase: Trova la dimensione dell'immagine della matrice [[1,0,1],[0,1,1],[1,1,2]].
❌ DOMAIN_ERR
  → CODING (exp: MATH) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.493

frase: Cosa succede se non si paga l'affitto per tre mesi?
⚠ FOLLOWUP_ERR
  → RIGHTS (exp: RIGHTS) 
  followup=True (exp: False) ← WRONG  diff=2 (runtime=2) (exp: 2) tier=PRIMARY ✅  conf=0.767

frase: Come vengono pagati i giorni di ferie non usati quando si lascia il lavoro?
❌ BOTH_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.591

frase: Come si usa il comando chmod in Linux?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=2 (runtime=2) (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.566

frase: Come si fa a denunciare un vicino rumoroso?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.734

frase: Quanto dura la prescrizione dei crediti da lavoro?
⚠ FOLLOWUP_ERR
  → RIGHTS (exp: RIGHTS) 
  followup=True (exp: False) ← WRONG  diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.697

frase: Come si calcola la media dei valori di una lista in Python?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=1 (runtime=1) (exp: 1) tier=FALLBACK ✅  conf=0.848

frase: Trova l'inversa della matrice [[2,1],[1,1]].
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (runtime=1) (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.891

frase: Implementa in Python la ricerca delle radici con il metodo delle secanti e dimostra la convergenza superlineare.
⚠ FOLLOWUP_ERR
  → MATH->CODING (exp: MATH->CODING) 
  followup=True (exp: False) ← WRONG  diff=3 (runtime=3) (exp: 3) tier=PRIMARY ✅  conf=0.627

frase: Scrivi uno script Python che verifica la conformità GDPR di un modulo di raccolta dati.
⚠ FOLLOWUP_ERR
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=True (exp: False) ← WRONG  diff=1 (runtime=2) (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.823

frase: Scrivi il codice per cifrare i dati sensibili dei clienti come previsto dal GDPR.
❌ DOMAIN_ERR
  → CODING (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.381

frase: Deriva con un modello matematico il calcolo dell'indennità di fine rapporto previsto dalla legge.
✅ OK
  → RIGHTS->MATH (exp: RIGHTS->MATH) 
  followup=False (exp: False)   diff=2 (runtime=2) (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.901

frase: Qual è il modello matematico per calcolare il danno da perdita di chance secondo la giurisprudenza?
⚠ FOLLOWUP_ERR
  → RIGHTS->MATH (exp: RIGHTS->MATH) 
  followup=True (exp: False) ← WRONG  diff=3 (runtime=3) (exp: 3) tier=PRIMARY ✅  conf=0.688
