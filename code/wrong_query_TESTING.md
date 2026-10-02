
frase: Implementa in Python la FFT e dimostra il teorema di Nyquist-Shannon con derivazione matematica.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (min atteso: 3) → tier=PRIMARY ✅  conf=0.969

frase: Implementa regressione lineare multipla in Python e dimostra la teoria dei minimi quadrati.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (min atteso: 2) → tier=PRIMARY ✅  conf=0.963

frase: Codice Python per busta paga conforme CCNL con calcolo IRPEF e detrazioni.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 3) → tier=FALLBACK ❌ DIFF_ERR  conf=0.818

frase: Implementa in Python un registro automatico dei trattamenti Art. 30 GDPR che tracci operazioni CRUD.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.842

frase: aggiungi la gestione degli errori
✅ OK
  → CODING (exp: CODING) 
  followup=True (exp: True)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.946

frase: cosa mangio stasera?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.905

frase: Dio esiste?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.872

frase: consigliami scarpe uomo
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.970

frase: come si calcola l'IVA su una fattura?
❌ BOTH_ERR
  → GENERAL (exp: RIGHTS->MATH) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.963

frase: implementa il login con JWT in Flask
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 2) → tier=PRIMARY ✅  conf=0.952

frase: Da tempo mi affascina come la matematica pura sia finita dentro cose che usiamo tutti i giorni senza saperlo, tipo la musica digitale o le chiamate audio: implementa in Python la FFT e dimostra il teorema di Nyquist-Shannon con derivazione matematica. Vorrei capire bene sia la parte teorica che il codice.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (min atteso: 3) → tier=PRIMARY ✅  conf=0.964

frase: Lavoro part-time in uno studio e il titolare mi ha chiesto di dare un'occhiata a come automatizzare certi calcoli, quindi: scrivi script Python per calcolo TFR rispettando D.Lgs. 66/2003 con calcolo normativo. Non ho fretta, spiegami con calma.
❌ DOMAIN_ERR
  → CODING (exp: RIGHTS->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (min atteso: 2) → tier=PRIMARY ✅  conf=0.953

frase: Ci sono momenti della vita in cui ci si ferma a riflettere su quanto la conoscenza umana sia frutto di secoli di tentativi, errori, intuizioni geniali e pura ostinazione, e più ci penso più mi convinco che dietro ogni piccola cosa che diamo per scontata ci sia una storia lunghissima fatta di persone che hanno dedicato la vita a capire come funziona il mondo, ed è proprio con questo spirito, quasi di gratitudine verso chi è venuto prima di noi, che oggi ti volevo chiedere una cosa piccola ma per me significativa: quicksort complessità O(n log n)
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.969

frase: Allora dunque, cerco di essere il più chiaro possibile anche se so che a volte mi perdo un po' quando scrivo, comunque il punto è che sto lavorando a un piccolo progetto per conto mio nel tempo libero, niente di che, giusto per tenermi allenato, e mi sono bloccato su una parte che riguarda la gestione degli errori quando leggo un file che potrebbe non esistere, quindi la domanda vera alla fine di tutto questo giro di parole è: come si gestiscono le eccezioni try except in Python quando apro un file?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.959

frase: A lezione di economia il professore ha usato un sacco di formule e integrali per spiegare la curva di domanda e offerta, ed è stato interessante ma un po' ostico: mi consigli un modo semplice, non matematico, per capire il concetto base di domanda e offerta?
❌ BOTH_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.735

frase: Qual è l'equazione perfetta tra amore e libertà in una relazione secondo la filosofia stoica?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.968

frase: E quindi qual è la conclusione?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.950

frase: Dio esiste?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.872

frase: Sto strugglando con questo bug nel mio codebase, il debugger non mi da nessun hint utile, help me capire cosa non va.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.968
