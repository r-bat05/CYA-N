
frase: consigliami un ristorante a Roma
❌ BOTH_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 conf=0.723

frase: cosa mangio stasera?
⚠ FOLLOWUP_ERR
  → GENERAL (exp: GENERAL) 
  followup=True (exp: False) ← WRONG  diff=1 conf=0.991

frase: Dio esiste?
❌ BOTH_ERR
  → CODING (exp: GENERAL) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 conf=0.889

frase: rispiega il passaggio 2
❌ DOMAIN_ERR
  → CODING (exp: MATH) ← WRONG
  followup=True (exp: True)   diff=1 conf=0.772

frase: come si calcola l'IVA su una fattura?
❌ BOTH_ERR
  → RIGHTS (exp: MATH) ← WRONG
  followup=True (exp: False) ← WRONG  diff=1 conf=0.478
