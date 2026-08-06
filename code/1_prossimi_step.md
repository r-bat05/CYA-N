1. migliorare il dataset, soprattutto per le query followup

2) modificare la rete neurale propria per la classificazione
    - eliminare l'early stopping per l'addestramento della rete   
    - capire come esportare il modello (come salvare i parametri) --> file nn_weights

3) rivedere i criteri di attivazione della pipeline --> solo per compiti complessi e da rivedere quali criteri devono essere soddisfatti (opzione: in base alle probabilità e alla difficoltà della richiesta, basando tutto sugli output del modello)

4) migliorare i prompt

   - per i modelli piccoli di coding, deve solo scrivere codice e commentarlo, senza spiegazioni teoriche perchè altrimenti le sbaglia. Gli altri devono attenersi a dare risposte brevi, senza argomentare troppo per evitare errori o allucinazioni
   - per i modelli grossi, bisogna assecondare le richieste dell'utente. Se non ci sono informazioni riguardante lo stile, imposterò come prompt di default quello di instagram

In generale, se un modello non ha dati sufficienti per rispondere (es: si è pulita la chat history ma domandiamo una query follow up rispetto ad una risposta precedente di cui però il sistema non ha più traccia) deve dire che informazioni mancano.

5) attivazione dei modelli rispetto alla difficoltà della domanda; se una domanda è semplice (1) non ha senso attivare un modello con tanti parametri
