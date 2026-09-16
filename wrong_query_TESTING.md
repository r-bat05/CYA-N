
frase: Scrivi una funzione Python che calcola il fattoriale in modo ricorsivo.
❌ DOMAIN_ERR
  → MATH->CODING (exp: CODING) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.862

frase: Spiegami come funziona il Virtual DOM in React rispetto al DOM reale.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.998

frase: Studia il carattere della serie numerica usando il criterio del rapporto.
⚠ FOLLOWUP_ERR
  → MATH (exp: MATH) 
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 2) → tier=PRIMARY ✅  conf=0.997

frase: Spiegami le differenze tra nullità e annullabilità di un contratto.
✅ OK
  → RIGHTS (exp: RIGHTS) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.999

frase: Implementa in Python la FFT e dimostra il teorema di Nyquist-Shannon con derivazione matematica.
❌ DOMAIN_ERR
  → MATH (exp: MATH->CODING) ← WRONG
  followup=False (exp: False)   diff=3 (min atteso: 3) → tier=PRIMARY ✅  conf=0.998

frase: gradiente coniugato Python sparse
✅ OK
  → MATH->CODING (exp: MATH->CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=0.927

frase: Implementa in Python un registro automatico dei trattamenti Art. 30 GDPR che tracci operazioni CRUD.
✅ OK
  → RIGHTS->CODING (exp: RIGHTS->CODING) 
  followup=False (exp: False)   diff=2 (min atteso: 3) → tier=PRIMARY ❌ DIFF_ERR  conf=0.985

frase: consigliami un ristorante a Roma
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.908

frase: cosa mangio stasera?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.994

frase: Dio esiste?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 (min atteso: 1) → tier=FALLBACK ✅  conf=0.805

frase: come si calcola l'IVA su una fattura?
❌ BOTH_ERR
  → RIGHTS (exp: MATH) ← WRONG
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.851
