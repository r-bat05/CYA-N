1. integrare un modo per rendere tutte le AI consapevoli del momento storico
2. implementazione di una grafica. Idea: stile prompt dei comandi user friendly con belle animazioni
   * creare delle opzioni che modificano il linguaggio: professore (modo formale) o amico (tono più amichevole)
   * creare un manuale per poter lanciare i comandi giusti ed utilizzare il prompt
   * consigliare di pulire la chat history in caso di errore

3. Persistenza sessioni (SQLite leggero) — chat_history oggi vive solo in RAM, persa al riavvio. Propedeutico anche alla GUI futura (che dovrà caricare conversazioni salvate).

4. 🎯 IDEA PRINCIPALE — Verification Layer per dominio

Oggi system_prompt di rights dice esplicitamente "NON INVENTARE LEGGI" — ma è un vincolo solo dichiarativo, il modello può comunque allucinare articoli. Stesso discorso implicito per math (calcoli sbagliati) e coding (codice non sintatticamente valido). Idea: affiancare a ogni agente un motore di verifica esterno, deterministico, a costo RAM quasi nullo (nessun modello aggiuntivo):

Dominio	Verifica proposta	Costo	Punto d'innesto
rights	**RAG** su corpus normativo (FAISS/Chroma + retrieval top-k iniettato nel prompt)	Basso — riusa l'encoder MiniLM già caricato per il routing	Tra classificazione e resolve(): se class_id∈rights, retrieval prima della chiamata Ollama
math	Verifica simbolica con SymPy (calcolo esatto in parallelo/post al draft LLM)	Trascurabile — pure CPU, no rete	Prima della critic pass: SymPy come "secondo giudice" oggettivo
coding	Syntax check statico (ast.parse per Python; estendibile)	Zero	Post-generazione, prima di mostrare output: retry automatico se fallisce