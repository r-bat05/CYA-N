# SCEGLIERE MODELLO GIUSTO QWEN --> VEDI SU OLLAMA LE VERSIONI



1. testare chat history con una sessione che copra tutti i casi

#### SESSIONE LUNGA (domanda --> modulo che dovrebbe attivarsi)

<!-- domande molto umane -->

- ciao, come stai? --> **general** 🟢
- posso chiederti qualsiasi cosa? --> **general** 🟢

<!-- domanda specifica con istruzioni -->

- scrivi un codice in un linguaggio a tua scelta per risolvere un sistema non lineare. Usa il metodo che vuoi tu, sei libero. Il codice che scrivi dovrà essere completo e corretto, non scrivere commenti ma spiegami le istruzioni che hai scritto 
  --> **coding/math->coding, accettabili entrambi**  🟢

<!-- domanda che va a completamento di quella precedente -->

- aggiungi dei commenti ad ogni istruzione --> **coding + sticky routing** 
- rispiegalo meglio --> **coding + sticky routing** 
- grazie della risposta --> **va bene o coding o general** 

<!-- domanda personali riguardo cose non tecniche -->

- stavo pensando di prenotare una vacanza alle Maldive, secondo te qual è il periodo migliore? Dammi un planning completo riguardo ciò che potrei fare in una vacanza di o 5 o 7 giorni. Sii completo e non essere superficiale, affidiamo il compito a te --> **general** 
- rieffettua l'analisi, deve essere ancora più dettagliata --> **general + sticky routing**
- risolvi il seguente integrale definito da -pigreco a 2 di arctan(sinx): spiega il procedimento della risoluzione passo passo, non perdere nessun passaggio e non sbagliare nel procedimento --> **math**
- sto facendo una tesi di ricerca per la mia laurea triennale riguardo il GDPR che regola le normative in merito alla privacy. Come posso strutturarla? Quali sono le informazioni più importanti che devo aggiungere? Prova a darmi una bozza tu riguardo questo argomento. Dovrà essere schematica, deve contenere solo le cose più importanti --> **rights**
- ora, sulla base dello schema che mi hai appena scritto, scrivi uan possibile tesi completa. Devi essere super preciso in quello che fai, non dovranno esserci errori.
  --> **rights + sticky routing**
- "La regressione lineare è un modello predittivo basato su un dataset di dati, in cui il sistema utilizza il concetto di gradiente per essere addestrato". Il mio prof mi ha spiegato questi concetti, ma non ho capito niente. Rispiegali --> **math / math->conding, accettabili entrambi**

<!-- cambiamento radicale della richiesta + dover attivare una pipeline -->

- scrivi il codice python per il teorema di pitagora allegando anche la dimostrazione passo-passo del perchè la formula finale è cosi. Sii preciso, non sbagliare l'analisi --> **math->coding**
- Qual è la procedura per il CID e l'attribuzione delle responsabilità civili in un tamponamento a catena? --> **rights / general**
- Stavo studiando economia alle superiori e mi chiedevo come potesse essere dimostrata la formula
  che calcola il patrimonio netto. Fallo e dammi anche un esempio pratico in cui è applicabile.
  --> **rights->math / math, accettabili entrambi**
- scrivi un codice Python commentato in cui viene calcolato il patrimonio netto e lordo di un'azienda qualsiasi. Nel codice inventa tu i dati, non hai limitazioni. Nei commenti metti i riferimenti anche a eventuali decreti e obblighi --> **rights->coding**
- riscrivi gli obblighi, sono errati. **coding + sticky routing**
- Ho comprato delle scarpe da Pittarello a 50 euro, mi hanno fatto 20% di sconto. Quanto era il prezzo originale? dimostra anche la formula matematica --> **general->math / math / general, vanno bene tutti**

<!-- scrivere domande che attivino tutti i tipi di pipeline, mischiare con query monodominio-->

- comando per trovare dispositivi a blocchi in Linux --> **coding**
- fammi un esempio di come usarlo --> **coding + sticky routing**
- nel messaggio qui allegato è presente il mio codice C che calcola l'entropia di un sistema, però è errato. Non capisco l'errore. Dopo aver corretto il codice dimostra la formula --> **math->coding**
- riscrivi la dimostrazione, spiega meglio i passaggi --> **math**
- non voglio il codice, solo la spiegazione teorica --> **coding / math->coding, accettabili entrambi**
- Esiste un regolamento europea che tuteli i lavoratori? --> **rights**
- consiglio scarpe uomo --> **general**
- scrivi un codice Python che calcola il TFR rispettando il D.Lgs. 47/2000 e dimostra la formula matematica --> **query con 3 domini possibili, va bene math->coding perchè qwen può agire su alcuni aspetti del diritto**

<!-- query di follow up molto corte in risposta a quelle precedenti -->

- rispondi si o no: Dio esiste? --> **general**
- perchè? --> **general + sticky routing**
- e quindi? --> **general + sticky routing**

<!-- cambio repetino del dominio -->

- ok grazie, invece qual è il concetto più importante del diritto sportivo? --> **rights**
- esempio? --> **rights + sticky routing**
- codice C++ calcolo traiettoria proiettile --> **coding**
- ricetta sacher? --> **general**

<!-- frasi ambigue - keyword in contesti diversi-->

- dammi una risposta integrale sul tema a tua scelta --> **general**
- esiste un algoritmo che mi permetta di lavorare meglio? --> **general**
- cosa prevede il codice in merito al furto? --> **rights**
- quante piastrelle servono per 12 m^2? --> **general / math**
- il mio padrone di casa non mi ridà il deposito, come fare --> **rights**

<!-- domande senza richiesta-->

- "public class StackTraceDemo {
  public static void main(String[] args) {
  System.out.println("Avvio del programma...");
  // Chiamata al metodo che causerà l'errore
  metodoRicorsivo(1);
  }

  public static void metodoRicorsivo(int contatore) {
  System.out.println("Livello ricorsione: " + contatore);

  // ERRORE: Non esiste una condizione di uscita (base case).
  // Il metodo continua a chiamare se stesso all'infinito.
  metodoRicorsivo(contatore + 1);
  }
  }" --> **coding** 🟢
- qual è il risultato? --> **coding + sticky routing**
- COMANDO /reset
- è possibile ottimizzare il codice di prima? --> **coding + sticky routing, ma avendo pulito la history bisogna vedere il comportamento**

<!-- richieste assurde e domande sull'AI stessa-->

- chi sei? --> **general**
- comprami un biglietto aereo --> **general**
- dimmi su che siti posso andare --> **general + sticky routing**
- ma cosa cazzo dici --> **general**

2) costruire una rete neurale per riconoscere ed instradare le richieste (vedi report Claude). Verifica i file necessari
3) migliorare i prompt

   - per i modelli piccoli di coding, deve solo scrivere codice e commentarlo, senza spiegazioni teoriche perchè altrimenti le sbaglia. Gli altri devono attenersi a dare risposte brevi, senza argomentare troppo per evitare errori o allucinazioni
   - per i modelli grossi, bisogna assecondare le richieste dell'utente. Se non ci sono informazioni riguardante lo stile, imposterò come prompt di default quello di instagram

In generale, se un modello non ha dati sufficienti per rispondere (es: si è pulita la chat history ma domandiamo una query follow up rispetto ad una risposta precedente di cui però il sistema non ha più traccia) deve dire che informazioni mancano.
