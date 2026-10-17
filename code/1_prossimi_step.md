1. migliorare criteri d'arresto training per ogni rete neurale --> basarsi sull'andamento della loss
2. ATTACCARE IL BRANCH PATCH_TRAINING_NN A SET_MANUAL_DIF&PATCH_DS IN MODO DA MERGIARE E CREARE UN UNICO BRANCH CON TUTTE SVOLTO (RETE + DATASET)
3. migliorare dataset con questo prompt

ATTACCARE WRONG_QUERY_FILE
qua ci sono i riepiloghi del testing
"  RIEPILOGO PER CATEGORIA
================================================================================
  mono_domain     : 139/145 corretti | domain=139/145 | followup=145/145
  followup        : 28/40 corretti | domain=36/40 | followup=31/40
  domain_switch   : 15/30 corretti | domain=19/30 | followup=23/30
  edge_case       : 24/32 corretti | domain=24/32 | followup=32/32
  pipeline        : 21/39 corretti | domain=21/39 | followup=39/39
  false_pipeline  : 20/23 corretti | domain=20/23 | followup=23/23".
male sul domain_switch e pipeline; bisogna migliorare su questi due campi inserendo sicuramente più frasi. Inoltre in db query ho messe un po di frasi per la traduzione, ma bisogna aumentarle.
Esegui tutte queste operazioni in modo magistrale, ne va della mia carriera. Dammi solo le frasi da aggiungere ma inseriscile in modo logico nei file già presenti, non aggiungere blocchi distaccati, deve essere un tutt'uno. Non aggiornare la memoria


4. generare documentazione aggiornata su set_manual_diff&patch_ds
5. fare refactoring database; bisogna 
5. Fare merge con main 