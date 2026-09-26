
frase: Implementa l'algoritmo di Dijkstra in Python per trovare il cammino minimo.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Spiegami come funziona il Virtual DOM in React rispetto al DOM reale.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Scrivi script Python per calcolo TFR rispettando D.Lgs. 66/2003 con calcolo normativo.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: e quindi?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=False (exp: True) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=1.000

frase: Dio esiste?
❌ BOTH_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.893

frase: Come si calcola la sezione aurea e come è stata applicata nell'architettura rinascimentale?
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.999

frase: Sai, ci penso da un po': risolvi le equazioni di Navier-Stokes per un flusso incomprimibile, una delle scoperte più importanti mai fatte nella storia dell'umanità, con un che di filosofico nel suo significato ancora oggi.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Ne stavo discutendo con mio fratello ieri sera, lui è più portato per queste cose di me, ma volevo capirci qualcosa anch'io: implementa l'algoritmo di Dijkstra in Python per trovare il cammino minimo. Giuro che non è per un compito, è pura curiosità.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Studiando storia dell'arte mi sono imbattuto in un concetto che ricorre spesso, quello della proporzione tra le parti di un'opera, e mi chiedevo se ci fosse una vera e propria equazione dietro alla prospettiva lineare usata dai pittori rinascimentali.
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.999

frase: Ok ma resta un dubbio che mi porto dietro da un po': e la diagonalizzazione, come si collega a quello che mi hai appena spiegato?
⚠ FOLLOWUP_ERR
  → MATH (exp: MATH) 
  followup=False (exp: True) ← WRONG  diff=3 (min atteso: 2) → tier=PRIMARY ✅  conf=0.989

frase: Ci sono momenti della vita in cui ci si ferma a riflettere su quanto la conoscenza umana sia frutto di secoli di tentativi, errori, intuizioni geniali e pura ostinazione, e più ci penso più mi convinco che dietro ogni piccola cosa che diamo per scontata ci sia una storia lunghissima fatta di persone che hanno dedicato la vita a capire come funziona il mondo, ed è proprio con questo spirito, quasi di gratitudine verso chi è venuto prima di noi, che oggi ti volevo chiedere una cosa piccola ma per me significativa: quicksort complessità O(n log n)
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.993

frase: Negli ultimi tempi mi capita spesso, magari la sera prima di dormire, di ripensare a quanto le regole che governano la nostra convivenza civile siano il risultato di secoli di conflitti, compromessi e riflessioni di persone che cercavano un equilibrio tra libertà individuale e interesse collettivo, ed è in uno di questi momenti che mi è tornata in mente una domanda specifica che non ho mai approfondito davvero: licenziamento giusta causa differenza
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.986

frase: C'è qualcosa di profondamente umano nel modo in cui torniamo sempre alle stesse domande semplici quando abbiamo bisogno di conforto o di distrazione, che sia un piatto che ci ricorda casa o un ricordo d'infanzia, ed è proprio pensando a questo che mi è venuta voglia di riprovare a farla come si deve, dopo tanti tentativi falliti: ricetta carbonara originale
❌ DOMAIN_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.729

frase: Sto leggendo un libro di divulgazione sull'intelligenza artificiale e parla spesso di reti neurali e gradiente, argomenti affascinanti ma difficili: mi consigli altri libri di divulgazione scientifica scritti bene per chi non ha basi tecniche?
❌ DOMAIN_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.781

frase: A lezione di economia il professore ha usato un sacco di formule e integrali per spiegare la curva di domanda e offerta, ed è stato interessante ma un po' ostico: mi consigli un modo semplice, non matematico, per capire il concetto base di domanda e offerta?
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.790

frase: Sto seguendo un corso serale di diritto per cultura personale, niente di professionale, e mi ha incuriosito molto come nascono le leggi in generale: mi racconti un po' la storia del diritto romano e come ha influenzato i sistemi giuridici moderni, giusto per curiosità?
❌ DOMAIN_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.940

frase: Durante l'allenamento di baseball un compagno mi ha colpito per sbaglio con un lancio, posso chiedere un risarcimento?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 2) → tier=PRIMARY ✅  conf=0.984

frase: Qual è l'equazione perfetta tra amore e libertà in una relazione secondo la filosofia stoica?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Dopo la lite ho fatto un po' di debug della situazione con la mia ragazza per capire cosa non aveva funzionato.
❌ DOMAIN_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.685

frase: Dio esiste?
❌ BOTH_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.893

frase: grazie mille
❌ BOTH_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=1.000

frase: Sto strugglando con questo bug nel mio codebase, il debugger non mi da nessun hint utile, help me capire cosa non va.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Ho sempre avuto un debole per le sfide intellettuali fin da bambino, mi affascina il modo in cui la tecnologia risolve problemi complessi: potresti implementare in C++ l'algoritmo A* per la ricerca del cammino minimo su una griglia con ostacoli, gestendo anche l'euristica ammissibile?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (min atteso: 3) → tier=PRIMARY ❌ DIFF_ERR  conf=0.930
