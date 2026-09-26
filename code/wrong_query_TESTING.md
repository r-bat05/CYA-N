
frase: Spiegami come funziona il Virtual DOM in React rispetto al DOM reale.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Implementa in Python la FFT e dimostra il teorema di Nyquist-Shannon con derivazione matematica.
✅ OK
  → MATH->CODING (exp: MATH->CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 3) → tier=FALLBACK ❌ DIFF_ERR  conf=0.920

frase: Codice Python per busta paga conforme CCNL con calcolo IRPEF e detrazioni.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=2 (min atteso: 3) → tier=PRIMARY ❌ DIFF_ERR  conf=0.999

frase: Implementa in Python un registro automatico dei trattamenti Art. 30 GDPR che tracci operazioni CRUD.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: cosa mangio stasera?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.938

frase: Dio esiste?
❌ BOTH_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.970

frase: 2+2
❌ DOMAIN_ERR
  → CODING (exp: MATH) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.786

frase: Come si calcola la sezione aurea e come è stata applicata nell'architettura rinascimentale?
❌ DOMAIN_ERR
  → RIGHTS->MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.930

frase: come si calcola l'IVA su una fattura?
❌ BOTH_ERR
  → RIGHTS (exp: RIGHTS->MATH) ← WRONG
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.948

frase: implementa il login con JWT in Flask
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 2) → tier=PRIMARY ✅  conf=0.981

frase: Ne stavo discutendo con mio fratello ieri sera, lui è più portato per queste cose di me, ma volevo capirci qualcosa anch'io: implementa l'algoritmo di Dijkstra in Python per trovare il cammino minimo. Giuro che non è per un compito, è pura curiosità.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.995

frase: Da tempo mi affascina come la matematica pura sia finita dentro cose che usiamo tutti i giorni senza saperlo, tipo la musica digitale o le chiamate audio: implementa in Python la FFT e dimostra il teorema di Nyquist-Shannon con derivazione matematica. Vorrei capire bene sia la parte teorica che il codice.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (min atteso: 3) → tier=PRIMARY ✅  conf=0.999

frase: Studiando storia dell'arte mi sono imbattuto in un concetto che ricorre spesso, quello della proporzione tra le parti di un'opera, e mi chiedevo se ci fosse una vera e propria equazione dietro alla prospettiva lineare usata dai pittori rinascimentali.
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.998

frase: Ok ma resta un dubbio che mi porto dietro da un po': e la diagonalizzazione, come si collega a quello che mi hai appena spiegato?
⚠ FOLLOWUP_ERR
  → MATH (exp: MATH) 
  followup=False (exp: True) ← WRONG  diff=2 (min atteso: 2) → tier=PRIMARY ✅  conf=0.999

frase: Ci sono momenti della vita in cui ci si ferma a riflettere su quanto la conoscenza umana sia frutto di secoli di tentativi, errori, intuizioni geniali e pura ostinazione, e più ci penso più mi convinco che dietro ogni piccola cosa che diamo per scontata ci sia una storia lunghissima fatta di persone che hanno dedicato la vita a capire come funziona il mondo, ed è proprio con questo spirito, quasi di gratitudine verso chi è venuto prima di noi, che oggi ti volevo chiedere una cosa piccola ma per me significativa: quicksort complessità O(n log n)
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.997

frase: Sto leggendo un libro di divulgazione sull'intelligenza artificiale e parla spesso di reti neurali e gradiente, argomenti affascinanti ma difficili: mi consigli altri libri di divulgazione scientifica scritti bene per chi non ha basi tecniche?
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.841

frase: Come funziona la tecnologia del VAR nel calcio e quanti replay controlla l'arbitro?
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.813

frase: Durante l'allenamento di baseball un compagno mi ha colpito per sbaglio con un lancio, posso chiedere un risarcimento?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.998

frase: Qual è l'equazione perfetta tra amore e libertà in una relazione secondo la filosofia stoica?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Dopo la lite ho fatto un po' di debug della situazione con la mia ragazza per capire cosa non aveva funzionato.
❌ DOMAIN_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.906

frase: Dio esiste?
❌ BOTH_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.970

frase: che ore sono?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.813

frase: grazie mille
❌ BOTH_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=1.000

frase: Sto strugglando con questo bug nel mio codebase, il debugger non mi da nessun hint utile, help me capire cosa non va.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Ho sempre avuto un debole per le sfide intellettuali fin da bambino, mi affascina il modo in cui la tecnologia risolve problemi complessi: potresti implementare in C++ l'algoritmo A* per la ricerca del cammino minimo su una griglia con ostacoli, gestendo anche l'euristica ammissibile?
❌ DOMAIN_ERR
  → MATH->CODING (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=3 (min atteso: 3) → tier=PRIMARY ✅  conf=0.861
