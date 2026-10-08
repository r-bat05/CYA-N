
frase: Spiegami le differenze tra nullità e annullabilità di un contratto.
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (exp: >=2) tier=FALLBACK ❌ DIFF_ERR  conf=0.955

frase: Da quando è entrato in vigore il GDPR ne sento parlare ovunque e non ho mai capito bene i dettagli, quindi ti chiedo: cosa prevede il GDPR per la notifica di un data breach entro 72 ore? Spiegamelo come se lo spiegassi a qualcuno alle prime armi.
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=2 (exp: >=1) tier=PRIMARY ✅  conf=0.465

frase: Studiando storia dell'arte mi sono imbattuto in un concetto che ricorre spesso, quello della proporzione tra le parti di un'opera, e mi chiedevo se ci fosse una vera e propria equazione dietro alla prospettiva lineare usata dai pittori rinascimentali.
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (exp: >=1) tier=PRIMARY ✅  conf=0.500

frase: Ci sono momenti della vita in cui ci si ferma a riflettere su quanto la conoscenza umana sia frutto di secoli di tentativi, errori, intuizioni geniali e pura ostinazione, e più ci penso più mi convinco che dietro ogni piccola cosa che diamo per scontata ci sia una storia lunghissima fatta di persone che hanno dedicato la vita a capire come funziona il mondo, ed è proprio con questo spirito, quasi di gratitudine verso chi è venuto prima di noi, che oggi ti volevo chiedere una cosa piccola ma per me significativa: quicksort complessità O(n log n)
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (exp: >=1) tier=FALLBACK ✅  conf=0.909

frase: Onestamente sto strugglando parecchio con questo assignment, il deadline è domani e non ho capito come si fa il refactoring di questa function per renderla più clean, tipo separare la business logic dalla UI.
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: >=1) tier=PRIMARY ✅  conf=0.490

frase: Allora dunque, cerco di essere il più chiaro possibile anche se so che a volte mi perdo un po' quando scrivo, comunque il punto è che sto lavorando a un piccolo progetto per conto mio nel tempo libero, niente di che, giusto per tenermi allenato, e mi sono bloccato su una parte che riguarda la gestione degli errori quando leggo un file che potrebbe non esistere, quindi la domanda vera alla fine di tutto questo giro di parole è: come si gestiscono le eccezioni try except in Python quando apro un file?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: >=1) tier=FALLBACK ✅  conf=0.756

frase: Sto leggendo un libro di divulgazione sull'intelligenza artificiale e parla spesso di reti neurali e gradiente, argomenti affascinanti ma difficili: mi consigli altri libri di divulgazione scientifica scritti bene per chi non ha basi tecniche?
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=3 (exp: >=1) tier=PRIMARY ✅  conf=0.407

frase: A lezione di economia il professore ha usato un sacco di formule e integrali per spiegare la curva di domanda e offerta, ed è stato interessante ma un po' ostico: mi consigli un modo semplice, non matematico, per capire il concetto base di domanda e offerta?
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (exp: >=1) tier=PRIMARY ✅  conf=0.520

frase: Sto seguendo un corso serale di diritto per cultura personale, niente di professionale, e mi ha incuriosito molto come nascono le leggi in generale: mi racconti un po' la storia del diritto romano e come ha influenzato i sistemi giuridici moderni, giusto per curiosità?
❌ DOMAIN_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (exp: >=1) tier=PRIMARY ✅  conf=0.516

frase: Qual è l'equazione perfetta tra amore e libertà in una relazione secondo la filosofia stoica?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: >=2) tier=FALLBACK ❌ DIFF_ERR  conf=0.620

frase: che ore sono?
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (exp: >=1) tier=FALLBACK ✅  conf=0.508

frase: Sto strugglando con questo bug nel mio codebase, il debugger non mi da nessun hint utile, help me capire cosa non va.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: >=2) tier=FALLBACK ❌ DIFF_ERR  conf=0.913

frase: Scrivi una funzione in Go che legge un file riga per riga e conta le parole.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.937

frase: Spiega come funziona l'ereditarietà prototipale in JavaScript.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.896

frase: Come si mappa una relazione molti-a-molti in SQLAlchemy?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.838

frase: Scrivi un decorator Python che misura il tempo di esecuzione di una funzione.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.693

frase: Come si integra Elasticsearch per la ricerca full-text in un'app Python?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.886

frase: Come si scrive un lexer per un linguaggio di programmazione giocattolo?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.894

frase: Come si aggiunge un campo a un modello Django e si applica la migrazione?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.828

frase: Come si configura un tunnel VPN WireGuard su un server Linux?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.902

frase: Implementa un thread pool minimale in C++ con std::thread.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.928

frase: Come si carica un modulo solo quando serve in React con il code splitting?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.953

frase: Determina la derivata della funzione f(x) = x·ln(x) - x.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.938

frase: Calcola l'integrale di x·sin(x) tra 0 e π.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.948

frase: Trova la soluzione di y'' - 3y' + 2y = 0 con y(0) = 0 e y'(0) = 1.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.938

frase: Dimostra la disuguaglianza di Cauchy-Schwarz.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.779

frase: Quanti anagrammi ha la parola MATEMATICA?
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.755

frase: Calcola l'area della regione compresa tra y = x^2 e y = 2x.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.964

frase: Verifica se la funzione f(x,y) = x^2 y è differenziabile nell'origine.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.923

frase: Spiega la differenza tra limite destro e limite sinistro con un esempio.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.952

frase: Qual è la durata massima del contratto di apprendistato?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.692

frase: Quali garanzie ha il lavoratore in caso di trasferimento d'azienda?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.953

frase: È legale registrare una telefonata senza avvisare l'altra persona?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.928

frase: Che cos'è una S.a.s. e come rispondono i soci accomandanti?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.873

frase: Cosa succede legalmente se un condomino non paga le spese condominiali?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.908

frase: Cos'è la clausola compromissoria e quando è valida?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.950

frase: Che cosa sono le azioni di classe (class action) in Italia?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.501

frase: Cosa prevede la normativa sulla responsabilità del produttore per i prodotti difettosi?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.943

frase: Che valore ha una scrittura privata non autenticata in tribunale?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.922

frase: Quali sono i libri più importanti della letteratura russa dell'Ottocento?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.902

frase: Come funziona una centrale fotovoltaica?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.895

frase: Qual è la differenza tra un film d'autore e un film commerciale?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.499

frase: Quali sono i pianeti con gli anelli e perché?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.940

frase: Che cos'è l'effetto placebo?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.886

frase: Mia cugina mi ha regalato un libro di programmazione per il compleanno e vorrei sfogliarlo con calma, però mi serve una mano su un punto: cos'è una variabile globale in JavaScript e perché è considerata rischiosa?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.693

frase: Il mio gatto ha camminato sulla tastiera e ha chiuso il terminale mentre lavoravo, perdendo la sessione: come si tiene attivo un processo in background con tmux dopo la disconnessione SSH?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.608

frase: ragazzi oggi sono proprio in palla col pc, qualcuno sa dirmi come faccio a far girare uno script python all'avvio del raspberry senza accendere niente a mano?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.725

frase: Il mio code review è stato brutale: mi hanno scritto che devo fare il refactor di questa class perché viola il single responsibility principle, come la splitto in due senza cambiare le API pubbliche?
❌ DOMAIN_ERR
  → RIGHTS->CODING (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.714

frase: Da quando ho cambiato casa passo molto più tempo davanti allo schermo, la sera, e ho scoperto che programmare mi tranquillizza più di qualsiasi serie televisiva, anche se faccio una fatica enorme con i concetti più astratti e mi serve sempre qualcuno che me li spieghi con calma, senza darli per scontati, e quindi arrivo al punto: come si usa il blocco try/finally in Java e a cosa serve la parte finally?
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.601

frase: Domani ho un colloquio in cui mi chiederanno di fare dei conti a mente e vorrei prepararmi con metodo, partendo dalle basi: come si calcola la probabilità di estrarre un asso da un mazzo di quaranta carte?
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.337

frase: Tempo fa ho abbandonato gli studi di ingegneria e adesso, per pura soddisfazione personale, sto riprendendo in mano i vecchi appunti, ma mi sono bloccato su un passaggio: come si calcola l'integrale di x per e^x per parti?
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.857

frase: Sto strugglando con l'exam di analisi 1 e il prof ha detto che uscirà un problema sugli integrali impropri, help me a capire come si stabilisce se l'integrale di 1/x^2 da 1 a infinito converge.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.932

frase: Sto per comprare la mia prima casa insieme al mio compagno e tra mutui, agenzie e notai ho un po' di confusione, quindi chiedo a te per cominciare: che cos'è il compromesso e che differenza c'è con il rogito?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.490

frase: Ho appena aperto un piccolo negozio online e tra mille adempimenti non so da dove partire, ma uno alla volta: quali informazioni obbligatorie deve riportare un sito di e-commerce secondo la legge?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.693

frase: scusate ma tipo se prendo una multa all'estero con l'auto a noleggio la devo pagare lo stesso?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.806

frase: vabbè però il datore di lavoro può davvero obbligarmi a fare gli straordinari la domenica
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.946

frase: qualcuno sa dirmi se un prof può bocciarmi per colpa di una frase detta in classe? ho paura di aver esagerato
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.877

frase: Ho fatto un freelance project per un cliente che non mi paga l'invoice da tre mesi, help me a capire quali strumenti legali ho per recuperare il credito.
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.828

frase: Con il mio compagno discutiamo da giorni, tra un conto da pagare e una bolletta da dividere, su dove andare in vacanza quest'estate: quali sono le mete più belle e poco costose in Europa a luglio?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.949

frase: scusate ma perché il caffè mi fa venire sonno invece di svegliarmi?? succede solo a me
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.952

frase: Per anni ho pensato che viaggiare fosse un lusso per altri e che la mia vita fosse destinata a restare tra casa e ufficio, ma una conversazione con un vecchio amico mi ha fatto cambiare idea e adesso sogno ogni sera di partire, magari con zaino in spalla e senza una meta precisa, ecco perché oggi ti chiedo: come si pianifica un viaggio in Interrail attraverso l'Europa?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.935

frase: In una sera di pioggia, rimasto solo in casa, ho ripensato alla musica che ascoltavo da ragazzo, ai concerti e ai dischi consumati, e a quanto certe canzoni siano capaci di riportare in vita interi periodi, e questo mi ha fatto venire voglia di approfondire la storia del rock, partendo da una domanda precisa: quali sono le caratteristiche del rock progressivo e quali band lo hanno reso famoso?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.948

frase: Kotlin coroutine
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.919

frase: contratto preliminare
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.924

frase: storia di Roma antica
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.934

frase: Heun Python ordine convergenza
✅ OK
  → MATH->CODING (exp: MATH->CODING) 
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.829

frase: Simpson Python stima errore
⚠ FOLLOWUP_ERR
  → MATH->CODING (exp: MATH->CODING) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.760

frase: Python informativa privacy automatica
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.928

frase: Python conservazione sostitutiva documenti
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.890

frase: dimostra rata mutuo normativa
❌ DOMAIN_ERR
  → RIGHTS (exp: RIGHTS->MATH) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.947

frase: modello matematico sanzione proporzionale
❌ DOMAIN_ERR
  → MATH (exp: RIGHTS->MATH) ← WRONG
  followup=False (exp: False)   diff=3 (exp: 3) tier=PRIMARY ✅  conf=0.288

frase: Implementa in Python l'algoritmo di Euclide esteso e dimostra l'identità di Bézout.
❌ DOMAIN_ERR
  → CODING (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.780

frase: Scrivi in Python un integratore di Gauss-Legendre a tre punti e mostra perché è esatto per polinomi fino al quinto grado.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.217

frase: Implementa un generatore di numeri pseudocasuali lineare congruenziale e dimostra la condizione di periodo massimo.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (exp: 3) tier=PRIMARY ✅  conf=0.769

frase: Implementa il gradiente coniugato precondizionato e dimostra la coniugazione delle direzioni di ricerca.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (exp: 3) tier=PRIMARY ✅  conf=0.809

frase: Implementa il metodo di Jacobi per gli autovalori e dimostra perché le rotazioni riducono la norma dei termini fuori diagonale.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (exp: 3) tier=PRIMARY ✅  conf=0.922

frase: Sono sempre stato colpito da quanto la matematica spieghi i giochi d'azzardo, perciò scrivi uno script Python che simula la rovina del giocatore e dimostra la probabilità di rovina con le catene di Markov.
❌ DOMAIN_ERR
  → CODING (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.374

frase: Il mio professore sostiene che chi non sa dimostrare non sa programmare, quindi ci provo davvero: implementa in Python la ricerca binaria sui reali per approssimare una radice quadrata e dimostra che l'errore si dimezza a ogni iterazione.
✅ OK
  → MATH->CODING (exp: MATH->CODING) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.867

frase: Quando ho scoperto che gli scacchi si analizzano con la teoria dei giochi mi si è aperto un mondo, quindi scrivi un programma Python per il minimax con potatura alfa-beta e dimostra che non cambia il risultato rispetto al minimax semplice.
❌ DOMAIN_ERR
  → CODING (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.418

frase: Scrivi un plugin WordPress che gestisce il banner dei cookie secondo le linee guida del Garante.
❌ DOMAIN_ERR
  → CODING (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.756

frase: Implementa un sistema di gestione ferie che rispetti il minimo di quattro settimane annuali previsto dalla normativa.
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.803

frase: Scrivi uno script che verifica la presenza della clausola di recesso di quattordici giorni nei contratti online dei consumatori.
❌ DOMAIN_ERR
  → RIGHTS (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.543

frase: Codice per un sistema di prenotazione ferie che impedisce di superare i limiti previsti dal CCNL del turismo.
❌ DOMAIN_ERR
  → RIGHTS (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.366

frase: Sviluppa un tool in Python che confronta le licenze delle librerie usate con quelle consentite dalla policy legale dell'azienda.
❌ DOMAIN_ERR
  → RIGHTS (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.226

frase: Il titolare di un piccolo hotel mi ha chiesto una mano con le schedine degli ospiti e non voglio sbagliare niente: sviluppa un modulo Python che invia i dati alla Questura nel rispetto della normativa di pubblica sicurezza.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.869

frase: Dopo l'ultima ispezione la mia azienda vuole mettersi in regola con tutto e a me tocca la parte software: implementa un sistema Python che traccia le ore lavorate per rispettare i riposi minimi previsti dalla legge.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.869

frase: Sono il responsabile IT di un comune di provincia e dobbiamo pubblicare i dati degli appalti: sviluppa uno script che pubblica gli atti in formato aperto rispettando gli obblighi di trasparenza del D.Lgs. 33/2013.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.872

frase: Qual è la formula matematica per determinare il deposito cauzionale commisurato al canone secondo la legge sulle locazioni?
✅ OK
  → RIGHTS->MATH (exp: RIGHTS->MATH) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.880

frase: Dimostra matematicamente il calcolo della quota indisponibile in presenza di due figli e un coniuge superstite.
❌ DOMAIN_ERR
  → MATH (exp: RIGHTS->MATH) ← WRONG
  followup=False (exp: False)   diff=3 (exp: 3) tier=PRIMARY ✅  conf=0.842

frase: Dimostra matematicamente la formula dell'ammortamento a quote costanti dei beni strumentali e i limiti fiscali di deducibilità.
✅ OK
  → RIGHTS->MATH (exp: RIGHTS->MATH) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.954

frase: Scrivi un programma Python che calcola la distanza euclidea tra due punti del piano.
❌ DOMAIN_ERR
  → MATH->CODING (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.767

frase: Cosa prevede il codice della strada per il sorpasso in curva?
❌ DOMAIN_ERR
  → MATH (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.779

frase: Quali sanzioni prevede il codice deontologico forense per un avvocato?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.958

frase: Cosa dice il codice penale sulle pene per il falso in bilancio?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.901

frase: Che cos'è il codice rosso nei casi di violenza domestica?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.805

frase: Spiega la formula della varianza campionaria e perché si divide per n-1.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.909

frase: La sentenza finale del talent show ha diviso il pubblico: perché le giurie sbagliano spesso?
❌ DOMAIN_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.870

frase: Come si calcola l'indennità di preavviso in caso di licenziamento?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=3 (exp: 2) tier=PRIMARY ❌ DIFF_ERR  conf=0.684

frase: Come si calcola l'imposta di bollo su un contratto di locazione?
❌ DOMAIN_ERR
  → RIGHTS->MATH (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=3 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.787

frase: Come si determina l'aliquota IRPEF applicabile a un reddito di 40.000 euro?
❌ DOMAIN_ERR
  → RIGHTS->MATH (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.915

frase: Come si calcola l'imposta dovuta con la cedolare secca sull'affitto?
❌ DOMAIN_ERR
  → RIGHTS->MATH (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.946

frase: Come si calcola l'indennità di maternità obbligatoria?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.339

frase: Qual è il prezzo finale di un articolo da 60 euro con uno sconto del 15%?
❌ DOMAIN_ERR
  → GENERAL (exp: MATH) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.549

frase: Calcola il valore finale di 5000 euro con interesse semplice del 2% annuo per 4 anni.
❌ DOMAIN_ERR
  → GENERAL (exp: MATH) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.284

frase: Qual è la rata mensile di un prestito di 3000 euro restituito in 12 rate senza interessi?
❌ DOMAIN_ERR
  → RIGHTS->MATH (exp: MATH) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.887

frase: puoi gestire anche il caso del file inesistente?
✅ OK
  → CODING (exp: CODING) 
  followup=True (exp: True)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.915

frase: e se una delle promise fallisce?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=False (exp: True) ← WRONG  diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.711

frase: mostrami un esempio con un'eccezione
❌ DOMAIN_ERR
  → MATH (exp: CODING) ← WRONG
  followup=True (exp: True)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.575

frase: potresti riscriverlo in Kotlin?
✅ OK
  → CODING (exp: CODING) 
  followup=True (exp: True)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.824

frase: e se i record sono milioni?
❌ DOMAIN_ERR
  → RIGHTS->CODING (exp: CODING) ← WRONG
  followup=True (exp: True)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.886

frase: puoi aggiungere la gestione degli errori?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=False (exp: True) ← WRONG  diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.447

frase: puoi fare un esempio numerico con 30 anni di contributi?
❌ BOTH_ERR
  → RIGHTS->MATH (exp: MATH) ← WRONG
  followup=False (exp: True) ← WRONG  diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.907

frase: non mi è chiaro il passaggio 3
❌ BOTH_ERR
  → RIGHTS->MATH (exp: MATH) ← WRONG
  followup=False (exp: True) ← WRONG  diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.890

frase: e se il discriminante fosse negativo?
⚠ FOLLOWUP_ERR
  → MATH (exp: MATH) 
  followup=False (exp: True) ← WRONG  diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.942

frase: funziona anche per la radice di 4?
✅ OK
  → MATH (exp: MATH) 
  followup=True (exp: True)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.602

frase: perché non si può sostituire direttamente?
✅ OK
  → MATH (exp: MATH) 
  followup=True (exp: True)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.959

frase: quando posso chiederne l'anticipo?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=True (exp: True)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.607

frase: e chi paga le tasse?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=True (exp: True)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.662

frase: e se non le godo entro l'anno?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=True (exp: True)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.786

frase: Capita la regola generale, ma nel mio caso specifico mi hanno rinnovato il contratto quattro volte di fila e vorrei sapere se la cosa è regolare o se posso pretendere l'assunzione a tempo indeterminato
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=True (exp: True)   diff=1 (exp: 3) tier=FALLBACK ❌ DIFF_ERR  conf=0.851

frase: da dove comincio se sono sedentario?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=False (exp: True) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.953

frase: vorrei qualcosa di meno turistico
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=False (exp: True) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.962

frase: Come si legge un file di testo in Python?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.936

frase: Come si crea un repository remoto su GitHub?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.897

frase: Come si configura un server Express con TypeScript?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.920

frase: Quanti modi ci sono di scegliere 3 elementi tra 10?
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.824

frase: Trova il volume di una sfera di raggio 3.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.908

frase: Quali sono le regole per registrare un'auto acquistata da un privato?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.871

frase: Chi può essere nominato tutore di un minore?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.795

frase: Chi ha inventato il cinema?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.961

frase: come si fa la cacio e pepe?
❌ BOTH_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.650

frase: come si dice grazie in giapponese?
❌ BOTH_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.543

frase: chi ha dipinto La notte stellata?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.931

frase: Trova la dimensione dell'immagine della matrice [[1,0,1],[0,1,1],[1,1,2]].
❌ DOMAIN_ERR
  → CODING (exp: MATH) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.445

frase: Cosa succede se non si paga l'affitto per tre mesi?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 2) tier=PRIMARY ✅  conf=0.614

frase: Come vengono pagati i giorni di ferie non usati quando si lascia il lavoro?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.889

frase: Come si usa il comando chmod in Linux?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=2 (exp: 1) tier=PRIMARY ❌ DIFF_ERR  conf=0.591

frase: Come si fa a denunciare un vicino rumoroso?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.958

frase: Quanto dura la prescrizione dei crediti da lavoro?
❌ DOMAIN_ERR
  → RIGHTS->MATH (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.636

frase: Come si calcola la media dei valori di una lista in Python?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.837

frase: Calcola l'integrale di x^3 da 0 a 2.
⚠ FOLLOWUP_ERR
  → MATH (exp: MATH) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 1) tier=FALLBACK ✅  conf=0.955

frase: Trova l'inversa della matrice [[2,1],[1,1]].
⚠ FOLLOWUP_ERR
  → MATH (exp: MATH) 
  followup=True (exp: False) ← WRONG  diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.938

frase: Scrivi uno script Python che verifica la conformità GDPR di un modulo di raccolta dati.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (exp: 2) tier=FALLBACK ❌ DIFF_ERR  conf=0.884

frase: Scrivi il codice per cifrare i dati sensibili dei clienti come previsto dal GDPR.
❌ DOMAIN_ERR
  → CODING (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=2 (exp: 3) tier=PRIMARY ❌ DIFF_ERR  conf=0.198
