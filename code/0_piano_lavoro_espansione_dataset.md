# Piano di lavoro — Espansione dataset CYA-N (complementare a `report_espansione_dataset.md`)

**Branch:** `build_classifier_NN` · **Rete:** INVARIATA (Opzione B del report) · **Fase 1:** ~5.000 record → **Fase 2:** ~9.000 (solo se Fase 1 OK)
**Regola d'oro:** un task per volta, un solo file toccato, validazione prima di procedere. Le direttive di `report_espansione_dataset.md` restano vincolanti; questo file aggiunge ordine, verifiche e correzioni emerse dall'analisi del codice.

---

## 0. Come riprendere in una nuova chat (Blocco di sicurezza)

Allegare SEMPRE: `report_espansione_dataset.md` + questo file + i file del task (tabella §5).
Dire: "riprendo dal task Tn". Il file di stato più recente è quello che alleghi tu: senza, mi fermo.
Aggiornare la checklist §4 prima di ogni nuova chat.

## 1. Baseline verificata (stato attuale, riproducibile)

| Dato | Valore |
|---|---|
| Record totali / train / val / test | 2.266 / 1.579 / 331 / 356 |
| Seed sorgente (intent/bridge/manual/false_pipe/keyword_trap) | 726 / 286 / 316 / 25 / 24 = 1.377 |
| Difficulty 1/2/3 (tutti) | 965 / 929 / 372 |
| Difficulty test: baseline "classe maggioritaria" | **0,410** (l'accuracy 0,615 va confrontata con questo, non con 0,33) |
| `is_followup` positivi train | 134/1579 (8,5%) — pos_weight reale 10,78, clampato a 5,0 |
| `general` positivi train | 329 (20,8%) — pos_weight 3,80 |
| Record con history | 265, **tutti con history di 1 sola query** |
| Sovrapposizioni seed↔eval (query+history esatte) | **28** (22 train, 2 val, 4 test) |
| Riproducibilità build | stesso contenuto e stessi split del dataset fornito (verificato) |

## 2. Verifiche sul report originale (correzioni / nuovi fatti)

1. **A-M5 esiste** in `eval_dataset.jsonl` (il report §7 dice di no). Query: "Studia il carattere della serie numerica usando il criterio del rapporto." → falso `followup=True` **senza history** (tutti i positivi di training hanno history).
2. **D-FU4 è nello split test**: il modello non l'ha mai visto in training. Il suo fallimento è di generalizzazione, non di segnale contrastante.
3. **D-FU7-verbose**: causa più probabile ≠ report §7/§9.4. `augment_noise()` lavora solo su intent+bridge (mai su `MANUAL_RECORDS`), quindi nessun `_fu` viene wrappato. Nel dataset c'è **1 solo** followup con query ≥8 parole: la rete non ha esempi di followup lunghi, e tutti i wrapped sono negativi → scorciatoia "testo lungo ⇒ non followup". Fix = aggiungere `_fu` verbosi (T2), non "proteggere" il wrapping.
4. **Smoke test non è un hold-out pulito**: 28/124 query eval sono già nei seed. Invariante: il numero di sovrapposizioni **non deve salire oltre 28** (lo verifica `check_dataset_seeds.py`).
5. **Split instabile tra versioni**: aggiungere anche solo 60 record ha cambiato lo split di 410/2.227 record vecchi (18,4%) e varianti di augmentation (RNG globale condiviso). Il test set cambia a ogni rebuild → `test_f1_domain` NON è confrontabile con 0,8887 (vedi D2). Solo `eval_dataset.jsonl` è un banco fisso.
6. **Mismatch history training/inferenza**: training ≤1 query di history; `history_utils.HISTORY_MAX_TURNS = 2` → dal 3° messaggio di una sessione il classificatore riceve un formato mai visto (vedi D1). Invisibile allo smoke test (solo history a 1 turno).
7. `augment_class()` pesca da TUTTI i record della classe, inclusi `_fu`/`_cd` di `MANUAL_RECORDS` → alzare `TARGET_MONO` genera anche varianti sinonimiche di followup/switch. Da verificare in T8 prima di toccare i target.


## 4. CHECKLIST (segna con `x` quando fatto)

**T0 — Preparazione (manuale)**
- [ ] Backup: `nn_weights.pt` → `nn_weights_baseline_2266.pt`; `dataset_v2.jsonl` → `dataset_v2_baseline_2266.jsonl`; `build_dataset_v2.py` → `build_dataset_v2.BACKUP.py`
- [ ] `check_dataset_seeds.py` copiato in `code/` ed eseguito sulla baseline (atteso: seed 1.377, leakage 28, WARN 1, ERRORI 0)
- [ ] Commit git di partenza

**T1 — Domain-switch → `general` (report §9.2-P1)** · file: `build_dataset_v2.py` (blocco unico in `MANUAL_RECORDS`) · **✅ COMPLETATO**
- [x] 60 record `_cd` generati (20 per history coding/math/rights), tutti `general=1, is_followup=False, diff=1`, query tutte uniche
- [x] Validato in sandbox: ast.parse, checker, 0 collisioni con seed/dataset/eval, 0 lessico tecnico/anafore nelle query, dry-run build senza errori
- [x] Blocco incollato prima della riga `# ── [FIX report_16errors] Diluizione estrema` → **file consegnato: `build_dataset_v2.py`**
- [x] `check_dataset_seeds.py` rieseguito sul file finale → manual **376**, totale **1.437**, leakage **28** (invariante rispettata), WARN 1 (`ciao, come stai?`, preesistente in baseline), ERRORI 0
- [x] Dry-run build isolato (cartella pulita) → **2.326** record, split **1610/338/378**, `is_followup`=191 (8,2%) — tutti i valori attesi confermati

→ **Azione tua:** sostituisci `code/build_dataset_v2.py` col file consegnato. Nessuna altra modifica richiesta per T1.

**T2 — `is_followup` (P7, §9.3)** · `build_dataset_v2.py` **✅ COMPLETATO**
- [x] Scegliere modalità (3 opzioni: manuale / generatore a template da history seed / ibrido) dopo D1
- [x] Followup **lunghi/verbosi** con history (oggi 1 solo) — causa D-FU7-verbose
- [x] Marcatori brevi vari su history general/miste (D-FU4)
- [x] Negativi senza history in stile ellittico (A-M5)
- [x] Obiettivo: positivi train ≥12–15% (oggi 8,3%); niente overlap con eval

**T3 — Keyword-trap (P3 + P6)** · `build_dataset_v2.py` → `KEYWORD_TRAP_NEGATIVES` **✅ COMPLETATO**
- [x] ≥6 fraseggi per trap esistente (VAR, lancio, equazione, debug, informatica, algoritmo, ottimizzare, formula, sezione aurea)
- [x] Nuovo trap **"lite"** (litigio personale, contesto non giuridico)
- [x] Trap inverso "lancio": rights genuino con sport/infortunio (baseball, calcio, basket, palestra…)

**T4 — Nuovi seed `general` (P2)** · `db_query.py` + `difficulty_labels.json` (batch da ~40)**✅ COMPLETATO**
- [x] Batch 1 · [ ] Batch 2 · [ ] Batch 3 (registri: colloquiale, culturale, pratico quotidiano)
- [x] Ogni batch = frammento `INTENT_SENTENCES['general']` + frammento JSON con chiavi = query esatte; checker OK

**T5 — Code-switch IT/EN (P4)** · `build_dataset_v2.py` **✅ COMPLETATO**
- [x] Coding (struggling, assignment, deadline, refactoring, bug, debugger, help me…)
- [x] Math (caso N-CS3-like)

**T6 — False pipeline su grafi (P5)** · `build_dataset_v2.py` → `FALSE_PIPELINE_HARD_NEGATIVES` **✅ COMPLETATO**
- [x] Dijkstra, BFS, DFS, componenti connesse, Bellman-Ford… solo "implementa", MAI "dimostra/analizza complessità" (sarebbe pipeline vera); verbo imperativo presente in `SYNONYMS`

**T7 — Difficulty (§8, §9.4)** · `build_dataset_v2.py`
- [ ] `augment_noise()` stratificato per difficulty (diff 2/3 ≥ densità di diff 1)
- [ ] Seed diff 2/3 in forma wrap/slang (stile N-CS3, G-NOISE1)


dopo aver eseguito t6. Tre note da portare a T8/T9:

TARGET_FALSE_PIPELINE_NEG=70 ora è saturo. Con 51 record base, l'augmentation sinonimica scende da +45 a +19 e le vecchie famiglie (fattoriale, MCD, ecc.) perdono varianti. In T8 va alzato, ad esempio a 100–110.
Sbilanciamento grafo-mono vs grafo-pipeline: 99 mono-coding contro circa 5 bridge pipeline su grafi (Floyd-Warshall, Ford-Fulkerson, Tarjan, Bellman-Ford + verifica, più Kruskal+dimostrazione in MANUAL_RECORDS).
Rischio: la rete impara "vocabolario da grafo ⇒ mai pipeline".
eval_dataset.jsonl non ha casi di pipeline su grafi, quindi il rischio non sarebbe visibile.
In T9, dopo il retrain, prova a mano 3-4 query del tipo "implementa Floyd-Warshall e analizza la complessità". Se regrediscono, si riduce il wrap o si aggiungono seed pipeline su grafi.
Lo split è cambiato di nuovo. I 34 record in più hanno spostato i confini 70/85% della classe coding. Il test set non è confrontabile con i run precedenti, come già previsto in D2.

**T8 — Target Fase 1 (~5.000)** · `build_dataset_v2.py`
- [ ] Verificare punto §2.7 (pool `augment_class` include `_fu`/`_cd`)
- [ ] `TARGET_MONO` asimmetrico (general > altri), `TARGET_PIPE`, `TARGET_BRIDGE_NEG`, `TARGET_FALSE_PIPELINE_NEG`
- [ ] Dry-run con conteggi per classe/split/difficulty/followup

**T9 — Cascade e verifica Fase 1**
- [ ] Applicati D1 e D2 (+ retrain baseline se D2-B)
- [ ] `build_dataset_v2 → precompute_embeddings → train_nn → step4_evaluation`
- [ ] Criteri §9.6 del report (vl_loss non risale, F1 general, diff accuracy, ID falliti, nessuna regressione `false_pipeline` 11/11, `followup` 10/12)
- [ ] Sovrapposizioni seed↔eval ≤ 28

**T10 — Fase 2 (~9.000)** solo se T9 OK, altrimenti rollback ai backup di T0.

## 5. File da allegare per task

| Task | File |
|---|---|
| T1–T3, T5–T8 | `build_dataset_v2.py` (aggiornato), `check_dataset_seeds.py`, `eval_dataset.jsonl` |
| T4 | + `db_query.py`, `difficulty_labels.json` |
| T2 | + `history_utils.py` (se D1) |
| T9 | log completi di build/train/step4 + `wrong_query_TESTING.md` |

## 6. Regole di conio frasi (anti-errore, valide per ogni task)

1. Ogni nuova query è **unica** (normalizzata lowercase/spazi) rispetto a seed, `dataset_v2.jsonl` ed eval; nessuna query ripetuta con history diverse (evita quasi-duplicati tra split).
2. `(query, history)` unica; history mai uguale a una history/query di eval.
3. Etichette esplicite e coerenti: `_C/_M/_R/_G`, pipeline solo con `_r(..., True, "x->y")`; `_fu` ⇒ history non vuota; `_cd` ⇒ `is_followup=False`.
4. `_cd`/`_fu` puliti: niente lessico trap (VAR, lancio, equazione, debug, formula, algoritmo, ottimizza, lite…) salvo nei task trap; `_cd` senza anafore/continuazioni ("e…", "perché", "questo").
5. Stringhe Python tra doppi apici, nessun doppio apice interno, niente backslash; caratteri accentati precomposti.
6. Seed in `INTENT_SENTENCES`/`BRIDGE_SENTENCES` ⇒ entry in `difficulty_labels.json` (chiave = query esatta, valore 1/2/3), una alla volta, nessun null.
7. Hard-neg via sinonimi: la frase inizia con verbo di `SYNONYMS`; hard-neg discorsive: nessun match sinonimi (solo noise-wrap).
8. Batch piccoli → `ast.parse` → `check_dataset_seeds.py` → (opz.) dry-run → solo poi task successivo.

## 6-bis. Protocollo di verifica per ogni task (già usato in T1)
`ast.parse` → checker (ERRORI 0, leakage ≤28) → script di collisioni/lessico/anafore → dry-run build in cartella isolata → confronto conteggi attesi.
