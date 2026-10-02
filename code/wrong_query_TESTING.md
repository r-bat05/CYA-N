
frase: Spiegami le differenze tra nullità e annullabilità di un contratto.
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.996

frase: Codice Python per busta paga conforme CCNL con calcolo IRPEF e detrazioni.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 3) → tier=FALLBACK ❌ DIFF_ERR  conf=0.953

frase: Implementa in Python un registro automatico dei trattamenti Art. 30 GDPR che tracci operazioni CRUD.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.952

frase: Dio esiste?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.989

frase: come si calcola l'IVA su una fattura?
❌ BOTH_ERR
  → GENERAL (exp: RIGHTS->MATH) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.992

frase: Ci sono momenti della vita in cui ci si ferma a riflettere su quanto la conoscenza umana sia frutto di secoli di tentativi, errori, intuizioni geniali e pura ostinazione, e più ci penso più mi convinco che dietro ogni piccola cosa che diamo per scontata ci sia una storia lunghissima fatta di persone che hanno dedicato la vita a capire come funziona il mondo, ed è proprio con questo spirito, quasi di gratitudine verso chi è venuto prima di noi, che oggi ti volevo chiedere una cosa piccola ma per me significativa: quicksort complessità O(n log n)
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.992

frase: Allora dunque, cerco di essere il più chiaro possibile anche se so che a volte mi perdo un po' quando scrivo, comunque il punto è che sto lavorando a un piccolo progetto per conto mio nel tempo libero, niente di che, giusto per tenermi allenato, e mi sono bloccato su una parte che riguarda la gestione degli errori quando leggo un file che potrebbe non esistere, quindi la domanda vera alla fine di tutto questo giro di parole è: come si gestiscono le eccezioni try except in Python quando apro un file?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.994

frase: Sto leggendo un libro di divulgazione sull'intelligenza artificiale e parla spesso di reti neurali e gradiente, argomenti affascinanti ma difficili: mi consigli altri libri di divulgazione scientifica scritti bene per chi non ha basi tecniche?
❌ DOMAIN_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=3 (min atteso: 1) → tier=PRIMARY ✅  conf=0.843

frase: Sto seguendo un corso serale di diritto per cultura personale, niente di professionale, e mi ha incuriosito molto come nascono le leggi in generale: mi racconti un po' la storia del diritto romano e come ha influenzato i sistemi giuridici moderni, giusto per curiosità?
❌ DOMAIN_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.977

frase: Qual è l'equazione perfetta tra amore e libertà in una relazione secondo la filosofia stoica?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.991

frase: Dio esiste?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.989

frase: Sto strugglando con questo bug nel mio codebase, il debugger non mi da nessun hint utile, help me capire cosa non va.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.995

frase: Ho sempre avuto un debole per le sfide intellettuali fin da bambino, mi affascina il modo in cui la tecnologia risolve problemi complessi: potresti implementare in C++ l'algoritmo A* per la ricerca del cammino minimo su una griglia con ostacoli, gestendo anche l'euristica ammissibile?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (min atteso: 3) → tier=PRIMARY ❌ DIFF_ERR  conf=0.990
