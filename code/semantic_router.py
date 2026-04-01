"""
    SEMANTIC ROUTER V2.0

    Routing semantico basato su embedding vettoriali.
    Converte la query utente e i prototipi di dominio in vettori tramite
    nomic-embed-text (via Ollama), poi seleziona il/i dominio/i con la
    massima similarità coseno.

    Novità V2.0 — Ottimizzazione Prototipi e Architettura:
    - [BREAKING] classify() restituisce ora Tuple[List[str], float, bool].
      Il terzo elemento (bool) segnala se l'embedding ha funzionato,
      permettendo a main.py di distinguere "query con confidenza bassa ma
      embedding riuscito" da "servizio embedding non disponibile".
      Solo nel secondo caso viene attivato il fallback a keyword.
    - [FIX CRITICO] Prototipi calcolati come centroide (media vettoriale)
      di embedding per singola frase, invece di un unico embedding del
      blocco testuale concatenato. Il vecchio approccio produceva un vettore
      medio rumoroso che perdeva la discriminazione tra intent simili.
      Il centroide è il punto equidistante da tutto il cluster del dominio.
    - [FEATURE] INTENT_SENTENCES ristrutturate come List[str] invece di str
      concatenato. Ogni frase contribuisce equamente al centroide.
    - [FEATURE] Sentence list arricchita con casi edge dai test di stress:
      docker/deploy per coding, prove teoriche per math, procedure legali
      per rights.

    Fix V1.2.1:
    - [BUG] Type hint 'list | None' valido solo da Python 3.10+.
      Sostituito con 'Optional[List]' da typing.

    Novità V1.2:
    - [FEATURE] Supporto multi-dominio in classify().

    Fix V1.1:
    - [BUG] Prototipi costruiti da keyword alfabetiche → sostituiti con
      frasi di intento in linguaggio naturale.
"""

from typing import Optional, List, Tuple, Dict
import math
import ollama
import config


# ---------------------------------------------------------------------------
# UTILITÀ VETTORIALI
# ---------------------------------------------------------------------------

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    Calcola la similarità coseno tra due vettori.
    Implementazione pura Python, senza dipendenze esterne (numpy-free).
    """
    dot   = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


def _average_vectors(vecs: List[List[float]]) -> Optional[List[float]]:
    """
    Calcola il centroide (media aritmetica componente per componente)
    di una lista di vettori. Restituisce None se la lista è vuota.
    Tutti i vettori devono avere la stessa dimensione (garantito da
    nomic-embed-text che produce sempre 768 dimensioni).
    """
    if not vecs:
        return None
    dim = len(vecs[0])
    return [sum(v[i] for v in vecs) / len(vecs) for i in range(dim)]


# ---------------------------------------------------------------------------
# PROTOTYPE STORE (Singleton + Lazy Init)
# ---------------------------------------------------------------------------

class PrototypeStore:
    """
    Costruisce e memorizza i vettori prototipo per ogni dominio.

    I prototipi vengono calcolati una sola volta al primo utilizzo
    (lazy initialization) tramite nomic-embed-text.

    APPROCCIO — Centroide di Intent Sentences:
    Ogni frase viene embeddata singolarmente; il prototipo del dominio
    è la media vettoriale (centroide) di tutti i vettori frase.
    Questo garantisce che nessuna singola frase domini il prototipo e
    che il vettore risultante sia geometricamente equidistante dall'intero
    cluster semantico del dominio.

    Le frasi coprono tre livelli per ogni dominio:
    1. Casi puri    → l'azione principale è inequivocabile
    2. Ibridi       → azione chiara ma contenuto misto (coding+math, coding+rights)
    3. Edge cases   → trappole lessicali identificate nei test di stress
    """

    _instance = None

    # ---------------------------------------------------------------------------
    # INTENT_SENTENCES: Dict[str, List[str]]
    # Ogni stringa è una frase indipendente embeddata separatamente.
    # NON concatenare le frasi: ogni voce contribuisce equamente al centroide.
    # Per aggiungere copertura a un dominio: aggiungere frasi alla lista.
    # ---------------------------------------------------------------------------
    INTENT_SENTENCES: Dict[str, List[str]] = {
        'coding': [
            # --- Azioni base di programmazione ---
            "Scrivi il codice per fare questo.",
            "Implementa una funzione che calcola.",
            "Crea un algoritmo per risolvere il problema.",
            "Fammi un programma in Python che esegue questa operazione.",
            "Correggi questo bug nel codice sorgente.",
            "Come si scrive questa funzione in JavaScript o TypeScript?",
            "Sviluppa uno script che elabora e trasforma i dati.",
            "Mostrami come implementare questa struttura dati in codice.",
            "Scrivi una classe orientata agli oggetti con questi metodi.",
            "Come faccio il debug di questo errore nel programma?",
            "Crea un'API REST con Flask o FastAPI.",
            "Refactoring e ottimizzazione di questo codice sorgente.",
            # --- Azioni di coding su contenuto matematico (ibrido C+M) ---
            "Scrivi il codice Python per calcolare questa formula matematica.",
            "Implementa in Python l'algoritmo di eliminazione di Gauss per matrici.",
            "Crea una funzione che calcoli la norma di un vettore o una matrice.",
            "Scrivi uno script che calcola la matrice inversa di un tensore.",
            "Implementa il calcolo della derivata numerica di una funzione matematica.",
            "Scrivi in C++ l'algoritmo di Dijkstra per trovare il cammino minimo in un grafo.",
            "Implementa la successione di Fibonacci con programmazione dinamica e memoization.",
            "Ottimizza il codice che calcola serie matematiche per evitare stack overflow.",
            "Scrivi una funzione JavaScript per calcolare l'ammortamento a rate costanti.",
            "Crea uno script per il calcolo numerico di integrali o derivate parziali.",
            "Qual è la complessità Big O di questa funzione che esegue calcoli matematici?",
            # --- Azioni di coding su contenuto legale/normativo (ibrido C+R) ---
            "Sviluppa uno smart contract in Solidity con clausole contrattuali automatiche.",
            "Scrivi codice che rispetti le normative GDPR per la gestione dei database.",
            "Implementa un sistema di logging su server Linux usabile come prova legale.",
            "Crea un'architettura software conforme alle normative europee sulla privacy.",
            "Scrivi uno script per web scraping rispettando le leggi sul copyright.",
            "Progetta un database SQL per dati sanitari seguendo le direttive normative.",
            # --- Edge cases: infrastruttura/DevOps con lessico normativo (stress test) ---
            "Scrivimi un file docker-compose per il deploy di un'applicazione cloud con policy di sicurezza.",
            "Configura le foreign key e le relazioni di integrità referenziale in un database SQL.",
            "Come si integra una licenza open source MIT in un container Docker?",
            "Scrivi uno script bash per automatizzare il deployment e il monitoring dell'applicazione.",
            # --- Kubernetes/orchestrazione (copertura Q15 stress test) ---
            "Come configuro un cluster Kubernetes per il bilanciamento del carico tra i pod in produzione?",
            "Gestisci i deployment, i service e gli ingress con kubectl su un cluster Kubernetes.",
            "Come si configura un'applicazione su Kubernetes con replica set e autoscaling?",
        ],
        'math': [
            # --- Calcolo e risoluzione pura ---
            "Calcola il risultato di questa espressione matematica.",
            "Dimostra questo teorema passo per passo.",
            "Risolvi questa equazione differenziale.",
            "Trova il limite di questa funzione analitica.",
            "Calcola l'integrale definito o indefinito di questa funzione.",
            "Qual è la derivata parziale di questa espressione?",
            "Spiega questo concetto matematico in modo teorico e rigoroso.",
            "Risolvi questo sistema di equazioni lineari con Gauss.",
            "Calcola il determinante e il rango di questa matrice.",
            "Dimostra per induzione matematica questa proprietà.",
            "Trova gli autovalori e autovettori di questa matrice.",
            "Studia la convergenza di questa serie numerica o successione.",
            "Applica il teorema di Taylor per sviluppare questa funzione.",
            "Calcola la probabilità di questo evento con la distribuzione statistica.",
            "Risolvi questo esercizio di algebra lineare o geometria differenziale.",
            # --- Casi ibridi math con lessico informatico (stress test) ---
            "Mostrami la formula matematica esatta per calcolare un risarcimento.",
            "Qual è la formula statistica per stimare la probabilità in un contesto legale?",
            "Calcola la ripartizione in frazioni e percentuali di una quota ereditaria.",
            "Qual è la complessità asintotica Big O di questo algoritmo teorico?",
            # --- Rafforzamento segnale dimostrativo (stress test: math travestita) ---
            "Dimostrami questo teorema con un ragionamento logico strutturato passo per passo.",
            "Qual è il procedimento manuale per calcolare questo valore matematico esatto?",
            "Calcola a mano l'intersezione tra due funzioni esponenziali mostrando i passaggi.",
        ],
        'rights': [
            # --- Diritto puro ---
            "Cosa dice la legge italiana su questo argomento giuridico?",
            "Qual è la normativa vigente in materia di diritto sportivo?",
            "Spiegami questo istituto giuridico del diritto italiano.",
            "Cosa prevede il codice civile italiano in questo caso specifico?",
            "Quali sono i diritti e doveri secondo la costituzione italiana?",
            "Come funziona il processo penale in Italia per questo reato?",
            "Cosa si intende per questo termine giuridico legale?",
            "Spiega il DASPO e la normativa sportiva italiana.",
            "Quali sanzioni prevede il codice di giustizia sportiva?",
            "Come funziona il ricorso al tribunale amministrativo regionale?",
            "Cosa dice la giurisprudenza su questo caso legale?",
            "Quali sono le fonti del diritto nell'ordinamento giuridico italiano?",
            "Spiega il significato di questo articolo di legge o decreto.",
            "Come si applica questa norma giuridica nella pratica legale?",
            "Qual è la differenza tra questi due istituti del diritto civile?",
            # --- Casi ibridi rights+tech (la norma è il focus) ---
            "Quali direttive GDPR si applicano quando si progetta un sistema informatico?",
            "Il web scraping di un sito viola le leggi sul diritto d'autore o il copyright?",
            "Come garantire che i log informatici siano prove valide in un processo penale?",
            "Quali norme del codice civile regolano la nullità di un contratto software?",
            "Come si tutelano i dati sanitari secondo la normativa europea sulla privacy?",
            "Qual è la penale legale per violazione di un contratto di licenza software?",
            "Quali sono le quote legittime di un'eredità secondo le norme giuridiche?",
            "Qual è la probabilità di vincere un ricorso in Corte di Cassazione?",
            # --- Edge cases: procedure legali con contesto tecnologico (stress test) ---
            "Qual è la procedura legale prevista dalla normativa italiana per questo caso specifico?",
            "Quali sono le implicazioni giuridiche dell'uso di algoritmi automatizzati sui dati personali?",
            "Come funziona la gerarchia delle fonti del diritto italiano?",
            # --- Formula/calcolo stabilito dalla legge (fix Q7 stress test) ---
            "Qual è il metodo di calcolo stabilito dalla normativa italiana per il TFR e le indennità dei lavoratori?",
            "Come prevede la legge di calcolare questa indennità economica spettante al lavoratore dipendente?",
            # --- Validità probatoria sistemi informatici (fix Q27 stress test) ---
            "Quali requisiti giuridici devono soddisfare i log di un server Linux per essere prove valide in tribunale?",
            "Come garantisce la normativa italiana la validità probatoria dei file informatici in un processo?",
        ],
        'general': [
            "Dimmi qualcosa su questo argomento di cultura generale.",
            "Spiegami questo fenomeno storico, geografico o scientifico.",
            "Cosa pensi di questa situazione di attualità?",
            "Raccontami come funziona questo nella vita quotidiana.",
            "Dammi informazioni su questo personaggio storico o evento.",
            "Qual è la tua opinione su questo tema generico?",
            "Spiegami questo concetto in modo semplice e accessibile.",
            "Hai consigli pratici su questo argomento di vita comune?",
            "Come si fa questa cosa nella vita di tutti i giorni?",
            "Puoi aiutarmi con questa domanda di carattere generale?",
        ]
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._prototypes = None
        return cls._instance

    def _embed(self, text: str, model: str) -> Optional[List[float]]:
        """Chiama ollama.embeddings e restituisce il vettore, o None in caso di errore."""
        try:
            response = ollama.embeddings(model=model, prompt=text)
            return response['embedding']
        except Exception as e:
            print(f"⚠️  PrototypeStore: embedding fallito per frase → {e}")
            return None

    def _build_prototypes(self):
        """
        Costruisce i prototipi per i 4 domini calcolando il centroide
        degli embedding per singola frase.

        Vantaggi rispetto al vecchio approccio monoblocco:
        - Nessuna frase domina il prototipo: ogni intent contribuisce equamente.
        - Il centroide è il punto geometricamente equidistante dal cluster.
        - Frasi diverse per lunghezza contribuiscono in ugual misura.
        - Aggiungere/rimuovere frasi aggiorna il prototipo in modo predicibile.
        """
        model = config.SEMANTIC_SETTINGS['embedding_model']
        total = sum(len(v) for v in self.INTENT_SENTENCES.values())
        print(f"\n⚙️   Costruzione prototipi semantici ({total} frasi totali, centroide per dominio)...")

        self._prototypes: Dict[str, Optional[List[float]]] = {}

        for domain, sentences in self.INTENT_SENTENCES.items():
            vecs = []
            for sentence in sentences:
                vec = self._embed(sentence, model)
                if vec is not None:
                    vecs.append(vec)

            prototype = _average_vectors(vecs)
            self._prototypes[domain] = prototype

            coverage = f"{len(vecs)}/{len(sentences)}"
            status   = "✅" if prototype else "❌"
            print(f"   {status}  [{domain:7s}] centroide calcolato su {coverage} frasi")

        print()

    def get(self) -> Dict[str, Optional[List[float]]]:
        """Restituisce i prototipi, costruendoli se necessario (lazy init)."""
        if self._prototypes is None:
            self._build_prototypes()
        return self._prototypes


# ---------------------------------------------------------------------------
# SEMANTIC ROUTER
# ---------------------------------------------------------------------------

class SemanticRouter:
    """
    Classifica un testo nei domini più simili usando embedding vettoriali.

    classify() restituisce (List[str], float, bool):
    - List[str]:  uno o più domini. Più domini → query ibrida.
    - float:      confidence = margin tra score del 1° e del 2° classificato.
    - bool:       True se l'embedding ha funzionato; False se il servizio
                  è fisicamente indisponibile → main.py attiva il keyword fallback.

    Il terzo elemento risolve il problema architetturale della V1.x:
    un margin basso non indica un fallimento del router, indica una query
    genuinamente ibrida o ambigua. Il router ha comunque prodotto un risultato
    valido che deve essere rispettato. Il keyword dispatcher subentra solo
    quando il servizio Ollama embedding non risponde.
    """

    def __init__(self):
        self.store = PrototypeStore()
        self.model = config.SEMANTIC_SETTINGS['embedding_model']

    def classify(self, text: str) -> Tuple[List[str], float, bool]:
        """
        Classifica il testo e restituisce (list[domini], confidenza, sem_ok).

        Returns:
            Tuple[List[str], float, bool]:
                - Lista di domini (1 o 2 in caso di query ibrida confermata)
                - Confidenza = top_score - second_score (margin-based)
                - sem_ok: True se il servizio ha risposto; False se down
        """
        prototypes = self.store.get()

        valid = {d: v for d, v in prototypes.items() if v is not None}
        if not valid:
            # Nessun prototipo calcolabile: fallback immediato al keyword
            return ['general'], 0.0, False

        # Embedding della query utente
        try:
            response  = ollama.embeddings(model=self.model, prompt=text)
            query_vec = response['embedding']
        except Exception as e:
            print(f"⚠️  SemanticRouter: embedding query fallito → {e}")
            return ['general'], 0.0, False

        # Calcolo similarità coseno per ogni dominio
        scores = {
            domain: cosine_similarity(query_vec, proto_vec)
            for domain, proto_vec in valid.items()
        }

        ranked        = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_domain    = ranked[0][0]
        top_score     = ranked[0][1]
        second_domain = ranked[1][0] if len(ranked) > 1 else None
        second_score  = ranked[1][1] if len(ranked) > 1 else 0.0
        confidence    = top_score - second_score   # margin tra 1° e 2°

        # --- LOGICA MULTI-DOMINIO ---
        # Il secondo dominio viene attivato solo se è genuinamente vicino al
        # primo (spread ≤ multi_domain_spread) E supera uno score assoluto
        # minimo (evita di attivare 'general' su query specialistiche dove
        # il suo score è strutturalmente basso).
        spread    = config.SEMANTIC_SETTINGS.get('multi_domain_spread',    0.08)
        min_score = config.SEMANTIC_SETTINGS.get('multi_domain_min_score', 0.58)

        domains: List[str] = [top_domain]
        if (second_domain is not None
                and second_score >= min_score
                and confidence   <= spread):
            domains.append(second_domain)

        # --- DEBUG ---
        if config.SEMANTIC_SETTINGS.get('debug', False):
            print(f"\n   🔍 [SEMANTIC DEBUG] scores: "
                  f"{ {d: f'{s:.4f}' for d, s in ranked} }")
            print(f"   🔍 [SEMANTIC DEBUG] domini={domains}  "
                  f"margin={confidence:.4f}  "
                  f"multi_spread={spread}  min_score={min_score}")

        # sem_ok=True: l'embedding ha funzionato, il risultato è affidabile
        return domains, confidence, True


# ---------------------------------------------------------------------------
# ISTANZA GLOBALE (Singleton applicativo)
# ---------------------------------------------------------------------------

semantic_router = SemanticRouter()
