
frase: Studia il carattere della serie numerica usando il criterio del rapporto.
⚠ FOLLOWUP_ERR
  → MATH (exp: MATH) 
  followup=True (exp: False) ← WRONG  diff=2 conf=0.989

frase: Calcola matematicamente il piano di ammortamento alla francese secondo normativa bancaria italiana.
❌ DOMAIN_ERR
  → RIGHTS (exp: RIGHTS->MATH) ← WRONG
  followup=False (exp: False)   diff=3 conf=0.998

frase: consigliami un ristorante a Roma
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 conf=0.977

frase: cosa mangio stasera?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 conf=0.979

frase: Dio esiste?
❌ BOTH_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 conf=0.700

frase: consigliami scarpe uomo
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 conf=0.935

frase: chi ha vinto il mondiale 2022?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 conf=0.977

frase: Mio figlio ha rotto qualcosa in casa per un lancio sbagliato, chi è responsabile verso il vicino?
❌ DOMAIN_ERR
  → GENERAL (exp: RIGHTS) ← WRONG
  followup=False (exp: False)   diff=1 conf=0.984

frase: rispiega il passaggio 2
❌ DOMAIN_ERR
  → CODING (exp: MATH) ← WRONG
  followup=True (exp: True)   diff=2 conf=0.615

frase: come si calcola l'IVA su una fattura?
❌ BOTH_ERR
  → RIGHTS (exp: MATH) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 conf=0.314

frase: implementa il login con JWT in Flask
⚠ FOLLOWUP_ERR
  → CODING (exp: CODING) 
  followup=True (exp: False) ← WRONG  diff=2 conf=0.986
