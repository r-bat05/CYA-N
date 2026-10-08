1. migliorare criteri d'arresto training
Considerazioni: interrompendomi verso l'epoca 20, il modello non alza la sua loss. Questo comporta che il modello diventa molto più bravo a identificare le query mono dominio e non confonderle come false pipeline. Tuttavia, il modello non è ancora abbastanza bravo a identificare le pipe, quindi le pipeline vengono classificate come query mono dominio 

Questo vuol dire che in realtà il vantaggio apportato corrisponde ad una mancata capacità della rete di generalizzare e identificare le pipeline

Inoltre , nonostante la loss aumenti, il modello ha prestazioni migliori nell'evaluationù
LOG: 

<pre style="background-color: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 8px; font-family: Consolas, 'Courier New', monospace; line-height: 1.4; overflow-x: auto;">
## INTERRUZIONE QUANDO NON SI AUMENTA PER PATIENCE EPOCHE
================================================================================
  RIEPILOGO PER CATEGORIA
================================================================================
  mono_domain     : 128/145 corretti | domain=133/145 | followup=140/145
  followup        : 24/40 corretti | domain=33/40 | followup=30/40
  domain_switch   : 13/30 corretti | domain=21/30 | followup=21/30
  edge_case       : 26/32 corretti | domain=26/32 | followup=31/32
  pipeline        : 20/39 corretti | domain=20/39 | followup=39/39
  false_pipeline  : 20/23 corretti | domain=20/23 | followup=23/23

  TOTALE (domain+followup): 231/309 =  74.8%  [IC95 69.6–79.3]
  Dettaglio errori: wrong_query_TESTING.md

================================================================================
  CONFUSIONE DOMINIO (righe=atteso, colonne=ottenuto)
  0=coding | 1=math | 2=rights | 3=general | 4=math->coding | 5=rights->coding | 6=rights->math
          0    1    2    3    4    5    6
    0    <span style="color: red;">53</span>    2    0    4    0    3    0
    1     2   <span style="color: red;">50</span>    0    3    0    0    3
    2     0    1   <span style="color: red;">53</span>    9    0    0    1
    3     2    2    4   <span style="color: red;">72</span>    0    0    0
    4     5    4    0    0    <span style="color: deepskyblue;">6</span>    <span style="color: deepskyblue;">0</span>    <span style="color: deepskyblue;">0</span>
    5     2    0    4    1    <span style="color: deepskyblue;">0</span>    <span style="color: deepskyblue;">8</span>    <span style="color: deepskyblue;">0</span>
    6     0    2    2    0    <span style="color: deepskyblue;">0</span>    <span style="color: deepskyblue;">0</span>   <span style="color: deepskyblue;">11</span>

  PER CLASSE            recall                              precision
  coding           53/62 =  85.5%  [IC95 74.7–92.2]       53/64 =  82.8%
  math             50/58 =  86.2%  [IC95 75.1–92.8]       50/61 =  82.0%
  rights           53/64 =  82.8%  [IC95 71.8–90.1]       53/63 =  84.1%
  general          72/80 =  90.0%  [IC95 81.5–94.8]       72/89 =  80.9%
  math->coding     6/15 =  40.0%  [IC95 19.8–64.3]        6/6 = 100.0%
  rights->coding   8/15 =  53.3%  [IC95 30.1–75.2]        8/11 =  72.7%
  rights->math     11/15 =  73.3%  [IC95 48.0–89.1]       11/15 =  73.3%

  FALSE-PIPELINE rate (mono → pipeline): 7/264 =   2.7%  [IC95  1.3– 5.4]
  PIPELINE-MISS rate (pipeline non riconosciuta): 20/45 =  44.4%  [IC95 30.9–58.8]

  PER TAG (domain accuracy)
  -            60/66 =  90.9%  [IC95 81.6–95.8]
  clean        121/149 =  81.2%  [IC95 74.2–86.7]
  codeswitch   4/5 =  80.0%  [IC95 37.6–96.4]
  colloquial   6/9 =  66.7%  [IC95 35.4–87.9]
  long         2/4 =  50.0%  [IC95 15.0–85.0]
  short        16/20 =  80.0%  [IC95 58.4–91.9]
  trap         25/30 =  83.3%  [IC95 66.4–92.7]
  verbose      19/26 =  73.1%  [IC95 53.9–86.3]

  CONFUSIONE DIFFICULTY (righe=atteso, colonne=ottenuto)
  exp=1:    79   25    2
  exp=2:    41   50    4
  exp=3:    10   19   13
  TIER errato (fallback↔primary): 78/243 =  32.1%  [IC95 26.5–38.2]

  ─── DIAGNOSI PIPELINE ────────────────────────────────────
  ⚠ FALSE PIPELINE (2): ['VTR-083', 'VTR-095']
    → le soglie si tarano sul VAL (train_nn.py), non su questo eval.
================================================================================



## INTERRUZIONE A EPOCA 20
================================================================================
  RIEPILOGO PER CATEGORIA
================================================================================
  mono_domain     : 133/145 corretti | domain=138/145 | followup=140/145
  followup        : 23/40 corretti | domain=34/40 | followup=27/40
  domain_switch   : 7/30 corretti | domain=17/30 | followup=18/30
  edge_case       : 27/32 corretti | domain=27/32 | followup=31/32
  pipeline        : 4/39 corretti | domain=4/39 | followup=39/39
  false_pipeline  : 20/23 corretti | domain=20/23 | followup=23/23

  TOTALE (domain+followup): 214/309 =  69.3%  [IC95 63.9–74.1]
  Dettaglio errori: wrong_query_TESTING.md

================================================================================
  CONFUSIONE DOMINIO (righe=atteso, colonne=ottenuto)
  0=coding | 1=math | 2=rights | 3=general | 4=math->coding | 5=rights->coding | 6=rights->math
          0    1    2    3    4    5    6
    0    <span style="color: deepskyblue;">56</span>    2    0    4    <span style="color: deepskyblue;">0</span>    <span style="color: deepskyblue;">0</span>    <span style="color: deepskyblue;">0</span>
    1     2   <span style="color: deepskyblue;">54</span>    1    1    <span style="color: deepskyblue;">0</span>    <span style="color: deepskyblue;">0</span>    <span style="color: deepskyblue;">0</span>
    2     0    1   <span style="color: deepskyblue;">54</span>    8    <span style="color: deepskyblue;">0</span>    <span style="color: deepskyblue;">0</span>    <span style="color: deepskyblue;">1</span>
    3     3    2    3   <span style="color: deepskyblue;">72</span>    0    0    0
    4     8    6    0    0    <span style="color: red;">1</span>    <span style="color: red;">0</span>    <span style="color: red;">0</span>
    5     6    0    8    1    <span style="color: red;">0</span>    <span style="color: red;">0</span>    <span style="color: red;">0</span>
    6     0    6    6    0    <span style="color: red;">0</span>    <span style="color: red;">0</span>    <span style="color: red;">3</span>

  PER CLASSE            recall                              precision
  coding           56/62 =  90.3%  [IC95 80.5–95.5]       56/75 =  74.7%
  math             54/58 =  93.1%  [IC95 83.6–97.3]       54/71 =  76.1%
  rights           54/64 =  84.4%  [IC95 73.6–91.3]       54/72 =  75.0%
  general          72/80 =  90.0%  [IC95 81.5–94.8]       72/86 =  83.7%
  math->coding     1/15 =   6.7%  [IC95  1.2–29.8]        1/1 = 100.0%
  rights->coding   0/15 =   0.0%  [IC95  0.0–20.4]           n/d
  rights->math     3/15 =  20.0%  [IC95  7.0–45.2]        3/4 =  75.0%

  FALSE-PIPELINE rate (mono → pipeline): 1/264 =   0.4%  [IC95  0.1– 2.1]
  PIPELINE-MISS rate (pipeline non riconosciuta): 41/45 =  91.1%  [IC95 79.3–96.5]

  PER TAG (domain accuracy)
  -            61/66 =  92.4%  [IC95 83.5–96.7]
  clean        112/149 =  75.2%  [IC95 67.7–81.4]
  codeswitch   5/5 = 100.0%  [IC95 56.6–100.0]
  colloquial   7/9 =  77.8%  [IC95 45.3–93.7]
  long         2/4 =  50.0%  [IC95 15.0–85.0]
  short        13/20 =  65.0%  [IC95 43.3–81.9]
  trap         25/30 =  83.3%  [IC95 66.4–92.7]
  verbose      15/26 =  57.7%  [IC95 38.9–74.5]

  CONFUSIONE DIFFICULTY (righe=atteso, colonne=ottenuto)
  exp=1:    81   24    1
  exp=2:    38   53    4
  exp=3:     6   24   12
  TIER errato (fallback↔primary): 69/243 =  28.4%  [IC95 23.1–34.4]

  ─── DIAGNOSI PIPELINE ────────────────────────────────────
  ⚠ FALSE PIPELINE (1): ['VTR-083']
    → le soglie si tarano sul VAL (train_nn.py), non su questo eval.
================================================================================
</pre>

2. sistemare i file della cartella code/
3. generare documentazione aggiornata