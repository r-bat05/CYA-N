
frase: Spiegami come funziona il Virtual DOM in React rispetto al DOM reale.
✅ OK
  → CODING (exp: CODING) 
  followup=False (exp: False)   diff=1 (min atteso: 2) → tier=FALLBACK ❌ DIFF_ERR  conf=1.000

frase: consigliami un ristorante a Roma
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=3 (min atteso: 1) → tier=PRIMARY ✅  conf=0.935

frase: Dio esiste?
❌ BOTH_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.989

frase: Come si calcola la sezione aurea e come è stata applicata nell'architettura rinascimentale?
❌ DOMAIN_ERR
  → MATH (exp: GENERAL) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.865

frase: Mio figlio ha rotto qualcosa in casa per un lancio sbagliato, chi è responsabile verso il vicino?
❌ DOMAIN_ERR
  → RIGHTS->CODING (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.900

frase: come si calcola l'IVA su una fattura?
⚠ FOLLOWUP_ERR
  → RIGHTS (exp: RIGHTS) 
  followup=True (exp: False) ← WRONG  diff=2 (min atteso: 1) → tier=PRIMARY ✅  conf=0.873
