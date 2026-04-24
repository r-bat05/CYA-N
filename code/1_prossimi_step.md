1. testare chat history tramite le query (vedi Gemini) a mano

#### Sessione 1: flusso ideale

1. `Scrivi una funzione in Python per calcolare i numeri primi fino a N.` *(Inizia Coding)*
2. `Ottimizzala per consumare meno memoria.` *(Corto: si aspetta Sticky su Coding)*
3. `E se volessi farla in C++ usando i vector?` *(Corto: si aspetta Sticky su Coding)*
4. `Qual è la differenza giuridica tra dolo e colpa cosciente?` *(Context Switch: Override su Rights perché confidenza > 0.65)*
5. `Fammi un esempio pratico di questo reato.` *(Corto: si aspetta Sticky su Rights)*


🟢 #### Sessione 2: La Trappola della Brevità (Test dell'Override) 2

Qui testiamo il Bug #1. L'utente fa domande brevissime ma cambia radicalmente dominio.
6. `Spiegami il teorema di Lagrange sulle derivate.` *(Inizia Math)*
7. `E per gli integrali?` *(Corto: Sticky su Math)*
8. `Legge sulla privacy?` *(Context Switch estremo: 3 parole. Il k-NN DEVE superare 0.65 su Rights per non rimanere bloccato su Math)*
9. `Sanzioni previste?` *(Corto: Sticky su Rights)*
10. `Array in Java?` *(Context Switch estremo: 3 parole. Deve saltare a Coding)*

🟢 #### Sessione 3: L'Eredità della Pipeline (Domain_B Retention)

Testiamo se la pipeline ibrida passa correttamente il testimone al dominio finale.
11. `Quali sono le norme del GDPR sul trattamento dati e scrivi uno script Python per offuscarli nel DB.` *(Pipeline: Rights -> Coding. Il `last_active_domain` deve diventare Coding)*
12. `Aggiungi i commenti al codice.` *(Corto: si aspetta Sticky su Coding. Se va a Rights, il passaggio di stato ha fallito)*
13. `Salva l'output in un file CSV.` *(Corto: Sticky su Coding)*
14. `Ma questa procedura mi mette al riparo da sanzioni penali?` *(Context Switch: Ritorno a Rights)*
15. `Spiega meglio il concetto giuridico.` *(Corto: Sticky su Rights)*

🟢 #### Sessione 4: Il Semantic Bleed e lo Sticky

Testiamo come le parole ambigue vengono gestite dalla continuità di conversazione.
16. `Mostrami come implementare l'algoritmo di Dijkstra in Rust.` *(Inizia Coding)*
17. `Esiste un modo migliore?` *(Corto, molto ambiguo. Il k-NN darebbe General, ma lo Sticky lo forza su Coding. Corretto).*
18. `Aggiungi una classe per i nodi.` *(Corto. "Classe" è ambiguo. Sticky salva la situazione su Coding).*
19. `Risolvi l'equazione differenziale lineare associata a questo problema.` *(Context Switch netto su Math)*
20. `Disegnami la parabola.` *(Corto. "Parabola" è ambiguo. Sticky lo forza su Math. Corretto).*

#### Sessione 5: Il "General" Debole (Test del Bug #2)

Mettiamo alla prova l'innesco `is_weak_general` con query lunghe ma di cultura generale.
21. `Spiegami i requisiti per il divorzio consensuale in Italia.` *(Inizia Rights)*
22. `Quanto costa mediamente un avvocato per questa pratica?` *(Corto/Lungo, ma semantica Rights. Rimane Rights).*
23. `Quali furono le cause esatte e le dinamiche sociali che portarono allo scoppio della Prima Guerra Mondiale?` *(Query lunga 17 parole. Il k-NN darà General. Se la confidenza è < 0.65, l'Agente Legale risponderà sulla guerra Mondiale. Errore da monitorare).*
24. `Dammi la ricetta per fare la carbonara tradizionale romana con le dosi.` *(Lunga. Idem come sopra).*
25. `Qual è la differenza tra array e liste in Javascript?` *(Context Switch netto su Coding).*

#### Sessione 6: L'Amnesia da Finestra (Sliding Window Test)

Saturiamo la cronologia (`max_history_turns = 3`) per vedere come reagisce il modello.
26. `Scrivi una query SQL con INNER JOIN per unire Utenti e Ordini.` *(Turno 1 - Coding)*
27. `Aggiungi un raggruppamento per data.` *(Turno 2 - Coding)*
28. `Filtra solo quelli con importo maggiore di 100.` *(Turno 3 - Coding. Finestra piena).*
29. `Ordina i risultati in modo decrescente.` *(Turno 4 - Coding. La domanda 26 viene eliminata dalla history).*
30. `Che tabelle avevamo usato nella primissima richiesta che ti ho fatto?` *(Il modello dovrebbe allucinare o chiedere scusa, poiché le tabelle Utenti e Ordini non sono più nel prompt).*

#### Sessione 7: Il Disastro dell'Offline (Simulazione Fallback)

*Nota: Spegni il demone Ollama prima di questa sessione, oppure inserisci parole inesistenti.*
31. `qxjzkw regex parsing log` *(Dovrebbe attivare il Fallback a Keyword su Coding).*
32. `fallo case insensitive` *(Senza embedding, questa frase non ha keyword di coding. Andrebbe su General, ma lo Sticky Routing lo salverà forzandolo su Coding).*
33. `aggiungi blocco try catch` *(Sticky su Coding).*
34. `k-nn autovalori autovettori xkwq` *(Fallback Keyword su Math. Spezza lo sticky).*
35. `matrice inversa` *(Sticky su Math).*

#### Sessione 8: Inneschi Multipli e Traduzioni

Mettiamo alla prova richieste spurie e conversioni.
36. `Scrivi uno smart contract in Solidity per un'asta.` *(Inizia Coding)*
37. `Traduci tutto in italiano.` *(Corto. Sticky su Coding)*
38. `Convertilo in linguaggio Vyper.` *(Corto. Sticky su Coding)*
39. `Qual è la normativa europea sulle criptovalute (MiCA)?` *(Context Switch -> Rights)*
40. `Riassumila in 3 punti.` *(Corto. Sticky su Rights)*

#### Sessione 9: Ambivalenza P0 Guard e Sticky

41. `Scrivi un codice Python per gestire i permessi degli utenti e fai un parallelo con la storia di Roma.` *(P0 Guard interviene e isola General. Rimane Coding).*
42. `Approfondisci la parte storica.` *(Essendo corta e `last_domain` = Coding, lo sticky forzerà l'Agente Programmatore a spiegare la storia di Roma).*
43. `Lascia stare, dimostrami il Teorema di Pitagora.` *(Context switch -> Math).*
44. `Applicalo a un triangolo con lati 3 e 4.` *(Corto -> Sticky su Math).*
45. `Come si coltivano le orchidee in casa?` *(Lunga, General. Test del Bug #2 sull'Agente Matematico).*

🟢 #### Sessione 10: Stress-Test finale di Resistenza

46. `Spiegami come bilanciare un albero AVL.` *(Coding)*
47. `E per i Red-Black tree?` *(Sticky Coding)*
48. `Definisci l'usucapione nel diritto privato.` *(Context Switch -> Rights)*
49. `Calcola l'integrale di x al cubo.` *(Context Switch -> Math)*
50. `Scrivi il codice per risolverlo.` *(Context Switch -> Coding. Fine)

2) migliorare i prompt
   - per i modelli piccoli di coding, deve solo scrivere codice e commentarlo, senza spiegazioni teoriche perchè altrimenti le sbaglia. Gli altri devono attenersi a dare risposte brevi, senza argomentare troppo per evitare errori o allucinazioni
   - per i modelli grossi, usare lo stile su instagram

