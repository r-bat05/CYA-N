
frase: Cosa prevede il GDPR per la notifica di un data breach entro 72 ore?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.996

frase: Spiegami le differenze tra nullità e annullabilità di un contratto.
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.998

frase: Codice Python per busta paga conforme CCNL con calcolo IRPEF e detrazioni.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 3) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Implementa in Python un registro automatico dei trattamenti Art. 30 GDPR che tracci operazioni CRUD.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: spiega meglio
❌ DOMAIN_ERR
  → MATH (exp: CODING) ← WRONG
  followup=True (exp: True)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.980

frase: Dio esiste?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.989

frase: come si calcola l'IVA su una fattura?
❌ BOTH_ERR
  → GENERAL (exp: RIGHTS->MATH) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.998

frase: Sai, ci penso da un po': risolvi le equazioni di Navier-Stokes per un flusso incomprimibile, una delle scoperte più importanti mai fatte nella storia dell'umanità, con un che di filosofico nel suo significato ancora oggi.
✅ OK
  → MATH (exp: MATH) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Da quando è entrato in vigore il GDPR ne sento parlare ovunque e non ho mai capito bene i dettagli, quindi ti chiedo: cosa prevede il GDPR per la notifica di un data breach entro 72 ore? Spiegamelo come se lo spiegassi a qualcuno alle prime armi.
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.999

frase: Da tempo mi affascina come la matematica pura sia finita dentro cose che usiamo tutti i giorni senza saperlo, tipo la musica digitale o le chiamate audio: implementa in Python la FFT e dimostra il teorema di Nyquist-Shannon con derivazione matematica. Vorrei capire bene sia la parte teorica che il codice.
✅ OK
  → MATH->CODING (exp: MATH->CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 3) → tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Lavoro part-time in uno studio e il titolare mi ha chiesto di dare un'occhiata a come automatizzare certi calcoli, quindi: scrivi script Python per calcolo TFR rispettando D.Lgs. 66/2003 con calcolo normativo. Non ho fretta, spiegami con calma.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Mi capita spesso di pensare a come l'informatica abbia cambiato il nostro modo di vivere le relazioni, tipo quando litighi con qualcuno e ripensi a come hai gestito male la comunicazione: come si fa il debug delle proprie emozioni per gestire meglio un conflitto con un amico?
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.046

frase: Implementa un algoritmo di ricerca binaria in python, argomento su cui torno spesso perché mi piace vedere come cambia l'efficienza cambiando approccio.
❌ DOMAIN_ERR
  → MATH->CODING (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.809

frase: Onestamente sto strugglando parecchio con questo assignment, il deadline è domani e non ho capito come si fa il refactoring di questa function per renderla più clean, tipo separare la business logic dalla UI.
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.999

frase: Allora dunque, cerco di essere il più chiaro possibile anche se so che a volte mi perdo un po' quando scrivo, comunque il punto è che sto lavorando a un piccolo progetto per conto mio nel tempo libero, niente di che, giusto per tenermi allenato, e mi sono bloccato su una parte che riguarda la gestione degli errori quando leggo un file che potrebbe non esistere, quindi la domanda vera alla fine di tutto questo giro di parole è: come si gestiscono le eccezioni try except in Python quando apro un file?
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=1.000

frase: Durante l'allenamento di baseball un compagno mi ha colpito per sbaglio con un lancio, posso chiedere un risarcimento?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.971

frase: Mio figlio ha rotto qualcosa in casa per un lancio sbagliato, chi è responsabile verso il vicino?
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.997

frase: Qual è l'equazione perfetta tra amore e libertà in una relazione secondo la filosofia stoica?
✅ OK
  → GENERAL (exp: GENERAL) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Dopo la lite ho fatto un po' di debug della situazione con la mia ragazza per capire cosa non aveva funzionato.
❌ DOMAIN_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.998

frase: Puoi farmi un esempio pratico?
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.615

frase: Dio esiste?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.989

frase: grazie mille
❌ BOTH_ERR
  → RIGHTS (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.997

frase: Sto strugglando con questo bug nel mio codebase, il debugger non mi da nessun hint utile, help me capire cosa non va.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: Il mio prof di computer science vuole che faccia il deployment su un cloud provider entro stasera, non ho la minima idea di come iniziare.
❌ DOMAIN_ERR
  → GENERAL (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 2) → tier=PRIMARY ✅  conf=0.827

frase: Ho sempre avuto un debole per le sfide intellettuali fin da bambino, mi affascina il modo in cui la tecnologia risolve problemi complessi: potresti implementare in C++ l'algoritmo A* per la ricerca del cammino minimo su una griglia con ostacoli, gestendo anche l'euristica ammissibile?
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=2 (min atteso: 3) → tier=PRIMARY ❌ DIFF_ERR  conf=0.999
