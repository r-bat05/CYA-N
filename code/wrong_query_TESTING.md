
frase: Spiegami le differenze tra nullità e annullabilità di un contratto.
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Implementa in Python un registro automatico dei trattamenti Art. 30 GDPR che tracci operazioni CRUD.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.997

frase: come si calcola l'IVA su una fattura?
❌ BOTH_ERR
  → GENERAL (exp: RIGHTS->MATH) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=1.000

frase: Mi capita spesso di pensare a come l'informatica abbia cambiato il nostro modo di vivere le relazioni, tipo quando litighi con qualcuno e ripensi a come hai gestito male la comunicazione: come si fa il debug delle proprie emozioni per gestire meglio un conflitto con un amico?
❌ DOMAIN_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.990

frase: C'è qualcosa di profondamente umano nel modo in cui torniamo sempre alle stesse domande semplici quando abbiamo bisogno di conforto o di distrazione, che sia un piatto che ci ricorda casa o un ricordo d'infanzia, ed è proprio pensando a questo che mi è venuta voglia di riprovare a farla come si deve, dopo tanti tentativi falliti: ricetta carbonara originale
❌ DOMAIN_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.881

frase: Onestamente sto strugglando parecchio con questo assignment, il deadline è domani e non ho capito come si fa il refactoring di questa function per renderla più clean, tipo separare la business logic dalla UI.
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.980

frase: Allora dunque, cerco di essere il più chiaro possibile anche se so che a volte mi perdo un po' quando scrivo, comunque il punto è che sto lavorando a un piccolo progetto per conto mio nel tempo libero, niente di che, giusto per tenermi allenato, e mi sono bloccato su una parte che riguarda la gestione degli errori quando leggo un file che potrebbe non esistere, quindi la domanda vera alla fine di tutto questo giro di parole è: come si gestiscono le eccezioni try except in Python quando apro un file?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.999

frase: Il mio ragazzo lavora come sviluppatore e passa le giornate a fare debug e a parlare di algoritmi, e onestamente un po' mi manca passare del tempo insieme: hai qualche idea per un'attività da fare in coppia questo weekend che non abbia niente a che fare con i computer?
❌ DOMAIN_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.621

frase: A lezione di economia il professore ha usato un sacco di formule e integrali per spiegare la curva di domanda e offerta, ed è stato interessante ma un po' ostico: mi consigli un modo semplice, non matematico, per capire il concetto base di domanda e offerta?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.986

frase: Durante l'allenamento di baseball un compagno mi ha colpito per sbaglio con un lancio, posso chiedere un risarcimento?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.994

frase: Qual è l'equazione perfetta tra amore e libertà in una relazione secondo la filosofia stoica?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Dopo la lite ho fatto un po' di debug della situazione con la mia ragazza per capire cosa non aveva funzionato.
❌ DOMAIN_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.970

frase: Puoi farmi un esempio pratico?
❌ DOMAIN_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.948

frase: grazie mille
❌ BOTH_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.999

frase: Sto strugglando con questo bug nel mio codebase, il debugger non mi da nessun hint utile, help me capire cosa non va.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Il mio prof di computer science vuole che faccia il deployment su un cloud provider entro stasera, non ho la minima idea di come iniziare.
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 2) → tier=PRIMARY ✅  conf=0.946

frase: Ho sempre avuto un debole per le sfide intellettuali fin da bambino, mi affascina il modo in cui la tecnologia risolve problemi complessi: potresti implementare in C++ l'algoritmo A* per la ricerca del cammino minimo su una griglia con ostacoli, gestendo anche l'euristica ammissibile?
❌ DOMAIN_ERR
  → MATH->CODING (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 3) → tier=PRIMARY ❌ DIFF_ERR  conf=0.933
