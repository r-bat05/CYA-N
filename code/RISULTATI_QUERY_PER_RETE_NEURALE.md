Inserisci la tua richiesta (o 'exit' per uscire): ciao, come stai?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'general': '16.12', 'rights': '4.94'}
   [k-NN DEBUG] Domini=['general'] | Confidence=0.77 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'rights': score=4.94, ratio=4.94/21.05 = 0.23, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['general']  |  Confidence k-NN: 0.77
🔍 [DEBUG SEMANTICO] Dominio: GENERAL

╭── 🧠 MODULO [GENERAL] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.39 GB < Richiesti: 12.00 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
ok, sono il programmatore e sto testando il sistema per verificare la correttezza del routing.
(Tempo impiegato: 11.328s)

Inserisci la tua richiesta (o 'exit' per uscire): posso chiederti qualsiasi cosa?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...
   [k-NN SOFT ZONE] 'rights' ratio=0.29 in soft zone, 0 keyword hit. Mono-dominio.

   [k-NN DEBUG] Score: {'general': '9.74', 'rights': '4.07'}
   [k-NN DEBUG] Domini=['general'] | Confidence=0.71 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'rights': score=4.07, ratio=4.07/13.81 = 0.29, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['general']  |  Confidence k-NN: 0.71
🔍 [DEBUG SEMANTICO] Dominio: GENERAL

╭── 🧠 MODULO [GENERAL] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.82 GB < Richiesti: 12.00 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
ok, sono il programmatore e sto testando il sistema per verificare la correttezza del routing.
(Tempo impiegato: 11.202s)


Inserisci la tua richiesta (o 'exit' per uscire): scrivi un codice in un linguaggio a tua scelta per risolvere un sistema non lineare. Usa il metodo che vuoi tu, sei libero. Il codice che scrivi dovrà essere completo e corretto, non scrivere commenti ma spiegami le istruzioni che hai scritto

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'coding': '12.14', 'math': '4.06', 'general': '1.91', 'rights': '1.87'}
   [k-NN DEBUG] Domini=['coding'] | Confidence=0.61 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'math': score=4.06, ratio=4.06/16.20 = 0.25, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['coding']  |  Confidence k-NN: 0.61
🔍 [DEBUG SEMANTICO] Dominio: CODING

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.07 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
ok, sono il programmatore e sto testando il sistema per verificare la correttezza del routing
(Tempo impiegato: 14.467s)


Inserisci la tua richiesta (o 'exit' per uscire): aggiungi dei commenti ad ogni istruzione

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'rights': '6.46', 'general': '3.89', 'math': '1.32', 'coding': '1.30'}
   [k-NN DEBUG] Domini=['rights', 'general'] | Confidence=0.50 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'general': score=3.89, ratio=3.89/10.35 = 0.38, ibrido=SI
🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: query troppo corta (6 < 12 parole).
🔍 [DEBUG SEMANTICO] Domini: ['rights']  |  Confidence k-NN: 0.50
📎 [STICKY] Domain Retention attivo: routing forzato → CODING (last='coding', k-NN top='rights', conf=0.50, trigger='query_corta')

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.11 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
ok, sono il programmatore e sto testando il sistema per verificare la correttezza del routing.
(Tempo impiegato: 7.482s)


Inserisci la tua richiesta (o 'exit' per uscire): rispiegalo meglio

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...
   [k-NN TOP GUARD] Query breve (2 parole): guardiano bypassato, fiducia al k-NN puro → 'rights'.

   [k-NN DEBUG] Score: {'rights': '7.32', 'general': '2.49', 'coding': '1.25', 'math': '1.22'}
   [k-NN DEBUG] Domini=['rights'] | Confidence=0.60 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'general': score=2.49, ratio=2.49/9.80 = 0.25, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['rights']  |  Confidence k-NN: 0.60
📎 [STICKY] Domain Retention attivo: routing forzato → CODING (last='coding', k-NN top='rights', conf=0.60, trigger='pattern_match("rispiega")')

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 2.09 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠹ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): grazie della risposta

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'rights': '5.74', 'general': '3.38', 'math': '2.51'}
   [k-NN DEBUG] Domini=['rights', 'general'] | Confidence=0.49 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'general': score=3.38, ratio=3.38/9.13 = 0.37, ibrido=SI
🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: query troppo corta (3 < 12 parole).
🔍 [DEBUG SEMANTICO] Domini: ['rights']  |  Confidence k-NN: 0.49
📎 [STICKY] Domain Retention attivo: routing forzato → CODING (last='coding', k-NN top='rights', conf=0.49, trigger='query_corta')

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.36 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
ok, sono il programmatore e sto testando il sistema per verificare la correttezza del routing.
(Tempo impiegato: 4.949s)


Inserisci la tua richiesta (o 'exit' per uscire): stavo pensando di prenotare una vacanza alle Maldive, secondo te qual è il periodo migliore? Dammi un planning completo riguardo ciò che potrei fare in una vacanza di o 5 o 7 giorni. Sii completo e non essere superficiale, affidiamo il compito a te

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'general': '6.85', 'coding': '4.79', 'rights': '3.24', 'math': '1.73'}
   [k-NN DEBUG] Domini=['general', 'coding'] | Confidence=0.41 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'coding': score=4.79, ratio=4.79/11.63 = 0.41, ibrido=SI
🔍 [DEBUG SEMANTICO] Domini: ['general', 'coding']  |  Confidence k-NN: 0.41
🔍 [DEBUG SEMANTICO] Arco Ibrido confermato (min_score=3.00, min_vote_ratio=0.3).
🔍 [DEBUG SEMANTICO] Coppia non in matrice. Ordine da score k-NN: GENERAL → CODING
🔍 [P0 GENERAL GUARD] Downgrade ibrido: GENERAL isolato. Routing mono-dominio → GENERAL

╭── 🧠 MODULO [GENERAL] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.65 GB < Richiesti: 12.00 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠙ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): rieffettua l'analisi, deve essere ancora più dettagliata

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'math': '7.97', 'coding': '5.15', 'general': '3.42'}
   [k-NN DEBUG] Domini=['math', 'coding'] | Confidence=0.48 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'coding': score=5.15, ratio=5.15/13.12 = 0.39, ibrido=SI
🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: query troppo corta (7 < 12 parole).
🔍 [DEBUG SEMANTICO] Domini: ['math']  |  Confidence k-NN: 0.48
📎 [STICKY] Domain Retention attivo: routing forzato → CODING (last='coding', k-NN top='math', conf=0.48, trigger='query_corta')

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.92 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠸ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): risolvi il seguente integrale definito da -pigreco a 2 di arctan(sinx): spiega il procedimento della risoluzione passo passo, non perdere nessun passaggio e non sbagliare nel procedimento

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'math': '5.67', 'rights': '4.14', 'coding': '2.75', 'general': '1.37'}
   [k-NN DEBUG] Domini=['math', 'rights'] | Confidence=0.41 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'rights': score=4.14, ratio=4.14/9.81 = 0.42, ibrido=SI
🔍 [DEBUG SEMANTICO] Domini: ['math', 'rights']  |  Confidence k-NN: 0.41
🔀 [SWITCH] Context switch rilevato: CODING → MATH (conf=0.41)

╭── 🧠 MODULO [MATH] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────
⠦ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): sto facendo una tesi di ricerca per la mia laurea triennale riguardo il GDPR che regola le normative in merito alla privacy. Come posso strutturarla? Quali sono le informazioni più importanti che devo aggiungere? Prova a darmi una bozza tu riguardo questo argomento. Dovrà essere schematica, deve contenere solo le cose più importanti

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'rights': '8.87', 'coding': '7.09', 'math': '1.70'}
   [k-NN DEBUG] Domini=['rights', 'coding'] | Confidence=0.50 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'coding': score=7.09, ratio=7.09/15.96 = 0.44, ibrido=SI
🔍 [DEBUG SEMANTICO] Domini: ['rights', 'coding']  |  Confidence k-NN: 0.50
🔍 [DEBUG SEMANTICO] Arco Ibrido confermato (min_score=3.00, min_vote_ratio=0.3).
🔍 [DEBUG SEMANTICO] Ordine da pipeline_order_matrix: RIGHTS → CODING

╭── 🧠 PIPELINE IBRIDA [RIGHTS → CODING] in azione...
│ Agente A (Draft): qwen2.5-coder:1.5b
│ Agente B (Merge): qwen2.5-coder:1.5b
╰──────────────────────────────────────────

⚙️  Fase 1/3 — Elaborazione contesto [RIGHTS] in corso...

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.05 GB < Richiesti: 12.00 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠴ Elaborazione in background [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): ora, sulla base dello schema che mi hai appena scritto, scrivi uan possibile tesi completa. Devi essere super preciso in quello che fai, non dovranno esserci errori

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'coding': '13.25', 'math': '3.13'}
   [k-NN DEBUG] Domini=['coding'] | Confidence=0.81 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'math': score=3.13, ratio=3.13/16.38 = 0.19, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['coding']  |  Confidence k-NN: 0.81
🔍 [DEBUG SEMANTICO] Dominio: CODING

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.63 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠴ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): La regressione lineare è un modello predittivo basato su un dataset di dati, in cui il sistema utilizza il concetto di gradiente per essere addestrato". Il mio prof mi ha spiegato questi concetti, ma non ho capito niente. Rispiegali

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'math': '14.51', 'coding': '4.77'}
   [k-NN DEBUG] Domini=['math'] | Confidence=0.75 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'coding': score=4.77, ratio=4.77/19.28 = 0.25, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['math']  |  Confidence k-NN: 0.75
🔀 [SWITCH] Context switch rilevato: CODING → MATH (conf=0.75)

╭── 🧠 MODULO [MATH] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────
⠇ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): scrivi il codice python per il teorema di pitagora allegando anche la dimostrazione passo-passo del perchè la formula finale è cosi. Sii preciso, non sbagliare l'analisi

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'coding': '8.50', 'math': '8.50'}
   [k-NN DEBUG] Domini=['coding', 'math'] | Confidence=0.50 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'math': score=8.50, ratio=8.50/16.99 = 0.5, ibrido=SI
🔍 [DEBUG SEMANTICO] Domini: ['coding', 'math']  |  Confidence k-NN: 0.50
🔀 [SWITCH] Context switch rilevato: MATH → CODING (conf=0.50)

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.92 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠼ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): Qual è la procedura per il CID e l'attribuzione delle responsabilità civili in un tamponamento a catena?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...
   [k-NN TOP GUARD] 'rights' ha 0 keyword hit. Fallback → GENERAL.

   [k-NN DEBUG] Score: {'rights': '17.27', 'general': '3.52'}
   [k-NN DEBUG] Domini=['general'] | Confidence=0.83 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'general': score=3.52, ratio=3.52/20.79 = 0.17, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['general']  |  Confidence k-NN: 0.83
🔍 [DEBUG SEMANTICO] Dominio: GENERAL

╭── 🧠 MODULO [GENERAL] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.12 GB < Richiesti: 12.00 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠴ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): Stavo studiando economia alle superiori e mi chiedevo come potesse essere dimostrata la formulache calcola il patrimonio netto. Fallo e dammi anche un esempio pratico in cui è applicabile

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'math': '8.50', 'rights': '5.25', 'general': '3.34'}
   [k-NN DEBUG] Domini=['math', 'rights'] | Confidence=0.50 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'rights': score=5.25, ratio=5.25/13.75 = 0.38, ibrido=SI
🔍 [DEBUG SEMANTICO] Domini: ['math', 'rights']  |  Confidence k-NN: 0.50
🔀 [SWITCH] Context switch rilevato: CODING → MATH (conf=0.50)

╭── 🧠 MODULO [MATH] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────
⠇ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): scrivi un codice Python commentato in cui viene calcolato il patrimonio netto e lordo di un'azienda qualsiasi. Nel codice inventa tu i dati, non hai limitazioni. Nei commenti metti i riferimenti anche a eventuali decreti e obblighi

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'coding': '12.02', 'rights': '5.79', 'math': '2.10'}
   [k-NN DEBUG] Domini=['coding', 'rights'] | Confidence=0.60 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'rights': score=5.79, ratio=5.79/17.82 = 0.33, ibrido=SI
🔍 [DEBUG SEMANTICO] Domini: ['coding', 'rights']  |  Confidence k-NN: 0.60
🔀 [SWITCH] Context switch rilevato: MATH → CODING (conf=0.60)

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 2.16 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠏ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): riscrivi gli obblighi, sono errati

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...
   [k-NN TOP GUARD] Query breve (5 parole): guardiano bypassato, fiducia al k-NN puro → 'rights'.

   [k-NN DEBUG] Score: {'rights': '8.58', 'general': '2.74', 'math': '1.38', 'coding': '1.33'}
   [k-NN DEBUG] Domini=['rights'] | Confidence=0.61 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'general': score=2.74, ratio=2.74/11.31 = 0.24, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['rights']  |  Confidence k-NN: 0.61
📎 [STICKY] Domain Retention attivo: routing forzato → CODING (last='coding', k-NN top='rights', conf=0.61, trigger='query_corta')

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 2.53 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠋ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): Ho comprato delle scarpe da Pittarello a 50 euro, mi hanno fatto 20% di sconto. Quanto era il prezzo originale? dimostra anche la formula matematica

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'math': '6.48', 'rights': '6.33', 'general': '3.23'}
   [k-NN DEBUG] Domini=['math', 'rights'] | Confidence=0.40 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'rights': score=6.33, ratio=6.33/12.81 = 0.49, ibrido=SI
🔍 [DEBUG SEMANTICO] Domini: ['math', 'rights']  |  Confidence k-NN: 0.40
🔀 [SWITCH] Context switch rilevato: CODING → MATH (conf=0.40)

╭── 🧠 MODULO [MATH] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────
⠋ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): comando per trovare dispositivi a blocchi in Linux

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'coding': '7.66', 'math': '4.45', 'rights': '3.03'}
   [k-NN DEBUG] Domini=['coding', 'math'] | Confidence=0.51 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'math': score=4.45, ratio=4.45/12.10 = 0.37, ibrido=SI
🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: query troppo corta (8 < 12 parole).
🔍 [DEBUG SEMANTICO] Domini: ['coding']  |  Confidence k-NN: 0.51
📎 [STICKY] Domain Retention attivo: routing forzato → MATH (last='math', k-NN top='coding', conf=0.51, trigger='query_corta')

╭── 🧠 MODULO [MATH] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────
⠏ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): nel messaggio qui allegato è presente il mio codice C che calcola l'entropia di un sistema, però è errato. Non capisco l'errore. Dopo aver corretto il codice dimostra la formula

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'coding': '15.55', 'math': '4.00'}
   [k-NN DEBUG] Domini=['coding'] | Confidence=0.80 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'math': score=4.00, ratio=4.00/19.55 = 0.2, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['coding']  |  Confidence k-NN: 0.80
🔀 [SWITCH] Context switch rilevato: MATH → CODING (conf=0.80)

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.21 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠋ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): riscrivi la dimostrazione, spiega meglio i passaggi

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'math': '7.07', 'general': '3.02', 'rights': '2.73', 'coding': '1.37'}
   [k-NN DEBUG] Domini=['math', 'general'] | Confidence=0.50 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'general': score=3.02, ratio=3.02/10.09 = 0.3, ibrido=SI
🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: query troppo corta (7 < 12 parole).
🔍 [DEBUG SEMANTICO] Domini: ['math']  |  Confidence k-NN: 0.50
📎 [STICKY] Domain Retention attivo: routing forzato → CODING (last='coding', k-NN top='math', conf=0.50, trigger='query_corta')

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.15 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠹ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): non voglio il codice, solo la spiegazione teorica

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...
   [k-NN TOP GUARD] Query breve (8 parole): guardiano bypassato, fiducia al k-NN puro → 'coding'.

   [k-NN DEBUG] Score: {'coding': '9.19', 'rights': '3.10', 'math': '3.00'}
   [k-NN DEBUG] Domini=['coding'] | Confidence=0.60 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'rights': score=3.10, ratio=3.10/12.29 = 0.25, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['coding']  |  Confidence k-NN: 0.60
📎 [STICKY] Domain Retention attivo: routing forzato → CODING (last='coding', k-NN top='coding', conf=0.60, trigger='query_corta')

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.36 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠇ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): Esiste un regolamento europea che tuteli i lavoratori?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...
   [k-NN TOP GUARD] Query breve (8 parole): guardiano bypassato, fiducia al k-NN puro → 'rights'.

   [k-NN DEBUG] Score: {'rights': '14.73', 'general': '3.38'}
   [k-NN DEBUG] Domini=['rights'] | Confidence=0.81 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'general': score=3.38, ratio=3.38/18.11 = 0.19, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['rights']  |  Confidence k-NN: 0.81
🔀 [SWITCH] Context switch rilevato: CODING → RIGHTS (conf=0.81)

╭── 🧠 MODULO [RIGHTS] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 2.12 GB < Richiesti: 12.00 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠦ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): consiglio scarpe uomo

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'general': '7.02', 'rights': '2.34', 'math': '1.17', 'coding': '1.16'}
   [k-NN DEBUG] Domini=['general'] | Confidence=0.60 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'rights': score=2.34, ratio=2.34/9.36 = 0.25, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['general']  |  Confidence k-NN: 0.60
📎 [STICKY] Domain Retention attivo: routing forzato → RIGHTS (last='rights', k-NN top='general', conf=0.60, trigger='query_corta')

╭── 🧠 MODULO [RIGHTS] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.10 GB < Richiesti: 12.00 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠏ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): scrivi un codice Python che calcola il TFR rispettando il D.Lgs. 47/2000 e dimostra la formula matematica

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'coding': '14.57', 'math': '6.37'}
   [k-NN DEBUG] Domini=['coding', 'math'] | Confidence=0.70 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'math': score=6.37, ratio=6.37/20.93 = 0.3, ibrido=SI
🔍 [DEBUG SEMANTICO] Domini: ['coding', 'math']  |  Confidence k-NN: 0.70
🔀 [SWITCH] Context switch rilevato: RIGHTS → CODING (conf=0.70)

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.06 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠼ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): rispondi si o no: Dio esiste?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'coding': '5.28', 'general': '5.27', 'rights': '2.67'}
   [k-NN DEBUG] Domini=['coding', 'general'] | Confidence=0.40 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'general': score=5.27, ratio=5.27/10.55 = 0.5, ibrido=SI
🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: query troppo corta (6 < 12 parole).
🔍 [DEBUG SEMANTICO] Domini: ['coding']  |  Confidence k-NN: 0.40
📎 [STICKY] Domain Retention attivo: routing forzato → CODING (last='coding', k-NN top='coding', conf=0.40, trigger='query_corta')

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.29 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠴ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): perchè?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...
   [k-NN TOP GUARD] Query breve (1 parole): guardiano bypassato, fiducia al k-NN puro → 'rights'.

   [k-NN DEBUG] Score: {'rights': '6.04', 'general': '2.39', 'math': '2.37', 'coding': '1.17'}
   [k-NN DEBUG] Domini=['rights'] | Confidence=0.50 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'general': score=2.39, ratio=2.39/8.43 = 0.28, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['rights']  |  Confidence k-NN: 0.50
📎 [STICKY] Domain Retention attivo: routing forzato → CODING (last='coding', k-NN top='rights', conf=0.50, trigger='query_corta')

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 2.45 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
ok, sono il programmatore e sto testando il sistema per verificare la correttezza del routing.
(Tempo impiegato: 17.143s)


Inserisci la tua richiesta (o 'exit' per uscire): e quindi?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...
   [k-NN TOP GUARD] Query breve (2 parole): guardiano bypassato, fiducia al k-NN puro → 'rights'.

   [k-NN DEBUG] Score: {'rights': '7.97', 'math': '2.28', 'general': '1.15'}
   [k-NN DEBUG] Domini=['rights'] | Confidence=0.70 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'math': score=2.28, ratio=2.28/10.26 = 0.22, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['rights']  |  Confidence k-NN: 0.70
🔀 [SWITCH] Context switch rilevato: CODING → RIGHTS (conf=0.70)

╭── 🧠 MODULO [RIGHTS] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 2.53 GB < Richiesti: 12.00 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠦ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): ok grazie, invece qual è il concetto più importante del diritto sportivo?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'rights': '11.58', 'general': '3.41', 'math': '1.76'}
   [k-NN DEBUG] Domini=['rights'] | Confidence=0.69 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'general': score=3.41, ratio=3.41/14.99 = 0.23, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['rights']  |  Confidence k-NN: 0.69
🔍 [DEBUG SEMANTICO] Dominio: RIGHTS

╭── 🧠 MODULO [RIGHTS] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.36 GB < Richiesti: 12.00 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠙ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): esempio?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...
   [k-NN TOP GUARD] Query breve (1 parole): guardiano bypassato, fiducia al k-NN puro → 'rights'.

   [k-NN DEBUG] Score: {'rights': '4.70', 'general': '2.85', 'math': '1.90'}
   [k-NN DEBUG] Domini=['rights'] | Confidence=0.50 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'general': score=2.85, ratio=2.85/7.55 = 0.38, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['rights']  |  Confidence k-NN: 0.50
📎 [STICKY] Domain Retention attivo: routing forzato → RIGHTS (last='rights', k-NN top='rights', conf=0.50, trigger='query_corta')

╭── 🧠 MODULO [RIGHTS] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.38 GB < Richiesti: 12.00 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
Ecco un esempio di come si applica il diritto sportivo:


Inserisci la tua richiesta (o 'exit' per uscire): codice C++ calcolo traiettoria proiettile

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...
   [k-NN TOP GUARD] Query breve (5 parole): guardiano bypassato, fiducia al k-NN puro → 'coding'.

   [k-NN DEBUG] Score: {'coding': '14.60', 'math': '1.89', 'rights': '1.72'}
   [k-NN DEBUG] Domini=['coding'] | Confidence=0.80 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'math': score=1.89, ratio=1.89/16.50 = 0.11, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['coding']  |  Confidence k-NN: 0.80
🔀 [SWITCH] Context switch rilevato: RIGHTS → CODING (conf=0.80)

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 2.48 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠹ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): ricetta sacher?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'general': '6.88', 'math': '2.05', 'rights': '0.95'}
   [k-NN DEBUG] Domini=['general'] | Confidence=0.70 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'math': score=2.05, ratio=2.05/8.93 = 0.23, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['general']  |  Confidence k-NN: 0.70
📎 [STICKY] Domain Retention attivo: routing forzato → CODING (last='coding', k-NN top='general', conf=0.70, trigger='query_corta')

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.29 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠏ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): dammi una risposta integrale sul tema a tua scelta

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...
   [k-NN TOP GUARD] Query breve (9 parole): guardiano bypassato, fiducia al k-NN puro → 'math'.

   [k-NN DEBUG] Score: {'math': '13.39'}
   [k-NN DEBUG] Domini=['math'] | Confidence=1.00 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
🔍 [DEBUG SEMANTICO] Domini: ['math']  |  Confidence k-NN: 1.00
🔀 [SWITCH] Context switch rilevato: CODING → MATH (conf=1.00)

╭── 🧠 MODULO [MATH] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────
⠦ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): esiste un algoritmo che mi permetta di lavorare meglio?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'general': '7.53', 'rights': '6.36', 'coding': '1.49'}
   [k-NN DEBUG] Domini=['general', 'rights'] | Confidence=0.49 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'rights': score=6.36, ratio=6.36/13.89 = 0.46, ibrido=SI
🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: query troppo corta (9 < 12 parole).
🔍 [DEBUG SEMANTICO] Domini: ['general']  |  Confidence k-NN: 0.49
🔍 [DEBUG SEMANTICO] Dominio: GENERAL

╭── 🧠 MODULO [GENERAL] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.46 GB < Richiesti: 12.00 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠇ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): cosa prevede il codice in merito al furto?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'coding': '8.01', 'rights': '6.92', 'general': '1.55'}
   [k-NN DEBUG] Domini=['coding', 'rights'] | Confidence=0.49 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'rights': score=6.92, ratio=6.92/14.93 = 0.46, ibrido=SI
🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: query troppo corta (8 < 12 parole).
🔍 [DEBUG SEMANTICO] Domini: ['coding']  |  Confidence k-NN: 0.49
📎 [STICKY] Domain Retention attivo: routing forzato → MATH (last='math', k-NN top='coding', conf=0.49, trigger='query_corta')

╭── 🧠 MODULO [MATH] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────
⠼ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): quante piastrelle servono per 12 m^2?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...
   [k-NN TOP GUARD] Query breve (6 parole): guardiano bypassato, fiducia al k-NN puro → 'math'.

   [k-NN DEBUG] Score: {'math': '6.53', 'rights': '2.69', 'general': '2.67', 'coding': '1.33'}
   [k-NN DEBUG] Domini=['math'] | Confidence=0.49 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'rights': score=2.69, ratio=2.69/9.22 = 0.29, ibrido=NO
🔍 [DEBUG SEMANTICO] Domini: ['math']  |  Confidence k-NN: 0.49
🔍 [DEBUG SEMANTICO] Dominio: MATH

╭── 🧠 MODULO [MATH] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────
⠋ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): il mio padrone di casa non mi ridà il deposito, come fare

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'general': '7.10', 'rights': '4.22', 'math': '1.38', 'coding': '1.35'}
   [k-NN DEBUG] Domini=['general', 'rights'] | Confidence=0.51 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'rights': score=4.22, ratio=4.22/11.32 = 0.37, ibrido=SI
🔍 [DEBUG SEMANTICO] Domini: ['general', 'rights']  |  Confidence k-NN: 0.51
🔀 [SWITCH] Context switch rilevato: MATH → RIGHTS (conf=0.51)

╭── 🧠 MODULO [RIGHTS] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.13 GB < Richiesti: 12.00 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
ok, sono il programmatore e sto testando il sistema per verificare la correttezza del routing
(Tempo impiegato: 4.295s)


Inserisci la tua richiesta (o 'exit' per uscire): "public class StackTraceDemo {  public static void main(String[] args) {  System.out.println("Avvio del programma...");  // Chiamata al metodo che causerà l'errore  metodoRicorsivo(1);  }  public static void metodoRicorsivo(int contatore) {  System.out.println("Livello ricorsione: " + contatore);  // ERRORE: Non esiste una condizione di uscita (base case).  // Il metodo continua a chiamare se stesso all'infinito.  metodoRicorsivo(contatore + 1);  }  }"

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'coding': '6.48', 'math': '3.78', 'rights': '2.54'}
   [k-NN DEBUG] Domini=['coding', 'math'] | Confidence=0.51 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'math': score=3.78, ratio=3.78/10.26 = 0.37, ibrido=SI
🔍 [DEBUG SEMANTICO] Domini: ['coding', 'math']  |  Confidence k-NN: 0.51
🔀 [SWITCH] Context switch rilevato: RIGHTS → CODING (conf=0.51)

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 2.16 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠧ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): qual è il risultato?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'rights': '11.96', 'math': '5.02'}
   [k-NN DEBUG] Domini=['rights', 'math'] | Confidence=0.70 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'math': score=5.02, ratio=5.02/16.97 = 0.3, ibrido=SI
🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: query troppo corta (4 < 12 parole).
🔍 [DEBUG SEMANTICO] Domini: ['rights']  |  Confidence k-NN: 0.70
🔀 [SWITCH] Context switch rilevato: CODING → RIGHTS (conf=0.70)

╭── 🧠 MODULO [RIGHTS] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.05 GB < Richiesti: 12.00 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
ok, sono il programmatore e sto testando il sistema per verificare la correttezza del routing
(Tempo impiegato: 10.307s)


Inserisci la tua richiesta (o 'exit' per uscire): è possibile ottimizzare il codice di prima?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'coding': '9.00', 'rights': '5.25', 'math': '1.85', 'general': '1.72'}
   [k-NN DEBUG] Domini=['coding', 'rights'] | Confidence=0.50 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'rights': score=5.25, ratio=5.25/14.25 = 0.37, ibrido=SI
🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: query troppo corta (7 < 12 parole).
🔍 [DEBUG SEMANTICO] Domini: ['coding']  |  Confidence k-NN: 0.50
🔍 [DEBUG SEMANTICO] Dominio: CODING

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.18 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
ok, sono il programmatore e sto testando il sistema per verificare la correttezza del routing
(Tempo impiegato: 3.915s)


Inserisci la tua richiesta (o 'exit' per uscire): chi sei?

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'general': '5.64', 'rights': '3.21', 'coding': '2.13'}
   [k-NN DEBUG] Domini=['general', 'rights'] | Confidence=0.51 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'rights': score=3.21, ratio=3.21/8.85 = 0.36, ibrido=SI
🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: query troppo corta (2 < 12 parole).
🔍 [DEBUG SEMANTICO] Domini: ['general']  |  Confidence k-NN: 0.51
📎 [STICKY] Domain Retention attivo: routing forzato → CODING (last='coding', k-NN top='general', conf=0.51, trigger='query_corta')

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.21 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): comprami un biglietto aereo

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'general': '4.67', 'coding': '3.55', 'rights': '2.53', 'math': '1.15'}
   [k-NN DEBUG] Domini=['general', 'coding'] | Confidence=0.39 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'coding': score=3.55, ratio=3.55/8.22 = 0.43, ibrido=SI
🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: query troppo corta (4 < 12 parole).
🔍 [DEBUG SEMANTICO] Domini: ['general']  |  Confidence k-NN: 0.39
📎 [STICKY] Domain Retention attivo: routing forzato → CODING (last='coding', k-NN top='general', conf=0.39, trigger='query_corta')

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.49 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠇ Consultando [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): dimmi su che siti posso andare

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'rights': '6.37', 'general': '5.10', 'math': '1.28'}
   [k-NN DEBUG] Domini=['rights', 'general'] | Confidence=0.50 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'general': score=5.10, ratio=5.10/11.47 = 0.44, ibrido=SI
🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: query troppo corta (6 < 12 parole).
🔍 [DEBUG SEMANTICO] Domini: ['rights']  |  Confidence k-NN: 0.50
📎 [STICKY] Domain Retention attivo: routing forzato → CODING (last='coding', k-NN top='rights', conf=0.50, trigger='query_corta')

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.50 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...


Inserisci la tua richiesta (o 'exit' per uscire): ma cosa cazzo dici

⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...

   [k-NN DEBUG] Score: {'general': '7.92', 'rights': '3.92', 'coding': '1.29'}
   [k-NN DEBUG] Domini=['general', 'rights'] | Confidence=0.60 | k=10 | epsilon=0.1 | min_score=3.00 | min_ratio=0.3
   [k-NN DEBUG] Secondo dominio 'rights': score=3.92, ratio=3.92/11.84 = 0.33, ibrido=SI
🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: query troppo corta (4 < 12 parole).
🔍 [DEBUG SEMANTICO] Domini: ['general']  |  Confidence k-NN: 0.60
📎 [STICKY] Domain Retention attivo: routing forzato → CODING (last='coding', k-NN top='general', conf=0.60, trigger='query_corta')

╭── 🧠 MODULO [CODING] in azione...
│ Modello: qwen2.5-coder:1.5b
╰──────────────────────────────────────────

WARN RAM INSUFFICIENTE per qwen2.5-coder:1.5b
   Disponibili: 1.43 GB < Richiesti: 5.50 GB
Downgrade PREVENTIVO a [qwen2.5-coder:1.5b]...
⠋ Consultando [qwen2.5-coder:1.5b]...


Considerazioni: alcune query sono sbagliate a causa del k-NN, mentre altre sono sbagliate perchè le precedenti sono instradate erroneamente (ma il routing è buono). In altre che sono errate è la chat hisotry a dare il problema, non tanto l'attribuzione dei punteggi del k-NN
