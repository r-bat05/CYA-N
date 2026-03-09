"""
    SEMANTIC ROUTER V1.2

    Routing semantico basato su embedding vettoriali.
    Converte la query utente e i prototipi di dominio in vettori tramite
    nomic-embed-text (via Ollama), poi seleziona il/i dominio/i con la
    massima similarità coseno.

    Fix V1.1:
    - [BUG] Prototipi costruiti da keyword alfabetiche → scarsa rappresentazione
      dell'intento utente. Sostituiti con frasi di intento in linguaggio naturale.

    Novità V1.2:
    - [FEATURE] Supporto multi-dominio: classify() ora restituisce una lista
      di domini invece di uno solo. Se il secondo classificato è abbastanza
      vicino al primo (spread ≤ multi_domain_spread) E ha un punteggio minimo
      sufficiente (score ≥ multi_domain_min_score), entrambi vengono restituiti
      e la query viene inviata a più agenti in parallelo.
      Questo risolve query genuinamente ibride come:
        "scrivi uno script per scraping ma dimmi se viola il copyright"
        → [coding, rights] → entrambi gli agenti rispondono ✅

    - [FIX] Intent sentences di coding arricchite con scenari ibridi espliciti
      (coding+math, coding+rights) per gestire query come:
        "scrivi uno script Python con l'eliminazione di Gauss" → [coding] ✅
        "sviluppa uno smart contract con clausole del codice civile" → [coding, rights] ✅

    Fix V1.2.1:
    - [BUG] Type hint 'list | None' valido solo da Python 3.10+.
      Sostituito con 'Optional[List]' da typing per garantire
      compatibilità con Python 3.8+ dichiarata nel README.
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


# ---------------------------------------------------------------------------
# PROTOTYPE STORE (Singleton + Lazy Init)
# ---------------------------------------------------------------------------

class PrototypeStore:
    """
    Costruisce e memorizza i vettori prototipo per ogni dominio.

    I prototipi vengono calcolati una sola volta al primo utilizzo
    (lazy initialization) tramite nomic-embed-text.

    APPROCCIO — Intent Sentences:
    I prototipi sono costruiti da frasi in linguaggio naturale che descrivono
    l'INTENTO dell'utente. Questo allinea lo spazio vettoriale del prototipo
    con quello delle query reali.

    Le intent sentences coprono tre categorie di casi:
    1. Casi puri   → "scrivi il codice per fare X"
    2. Ibridi      → "scrivi il codice per calcolare questa formula matematica"
    3. Edge cases  → "implementa un sistema che rispetti norme legali"
    """

    _instance = None

    # ---------------------------------------------------------------------------
    # Intent sentences per dominio.
    # La sezione "ibrida" di ogni dominio è deliberatamente sbilanciata verso
    # l'azione principale: se l'utente dice "scrivi codice" su contenuto
    # matematico, l'AZIONE definisce il dominio, non il contenuto.
    # ---------------------------------------------------------------------------
    INTENT_SENTENCES = {
        'coding': (
            # --- Azioni base di programmazione ---
            "Scrivi il codice per fare questo. "
            "Implementa una funzione che calcola. "
            "Crea un algoritmo per risolvere il problema. "
            "Fammi un programma in Python che esegue questa operazione. "
            "Correggi questo bug nel codice sorgente. "
            "Come si scrive questa funzione in JavaScript o TypeScript? "
            "Sviluppa uno script che elabora e trasforma i dati. "
            "Mostrami come implementare questa struttura dati in codice. "
            "Scrivi una classe orientata agli oggetti con questi metodi. "
            "Come faccio il debug di questo errore nel programma? "
            "Crea un'API REST con Flask o FastAPI. "
            "Refactoring e ottimizzazione di questo codice sorgente. "
            # --- Azioni di coding su contenuto matematico (ibrido) ---
            "Scrivi il codice Python per calcolare questa formula matematica. "
            "Implementa in Python l'algoritmo di eliminazione di Gauss per matrici. "
            "Crea una funzione che calcoli la norma di un vettore o una matrice. "
            "Scrivi uno script che calcola la matrice inversa di un tensore. "
            "Implementa il calcolo della derivata numerica di una funzione matematica. "
            "Scrivi in C++ l'algoritmo di Dijkstra per trovare il cammino minimo in un grafo. "
            "Implementa la successione di Fibonacci con programmazione dinamica e memoization. "
            "Ottimizza il codice che calcola serie matematiche per evitare stack overflow. "
            "Scrivi una funzione JavaScript per calcolare l'ammortamento a rate costanti. "
            "Crea uno script per il calcolo numerico di integrali o derivate parziali. "
            "Qual è la complessità Big O di questa funzione che esegue calcoli matematici? "
            # --- Azioni di coding su contenuto legale/normativo (ibrido) ---
            "Sviluppa uno smart contract in Solidity con clausole contrattuali automatiche. "
            "Scrivi codice che rispetti le normative GDPR per la gestione dei database. "
            "Implementa un sistema di logging su server Linux usabile come prova legale. "
            "Crea un'architettura software conforme alle normative europee sulla privacy. "
            "Scrivi uno script per web scraping rispettando le leggi sul copyright. "
            "Progetta un database SQL per dati sanitari seguendo le direttive normative. "
        ),
        'math': (
            # --- Calcolo e risoluzione pura ---
            "Calcola il risultato di questa espressione matematica. "
            "Dimostra questo teorema passo per passo. "
            "Risolvi questa equazione differenziale. "
            "Trova il limite di questa funzione analitica. "
            "Calcola l'integrale definito o indefinito di questa funzione. "
            "Qual è la derivata parziale di questa espressione? "
            "Spiega questo concetto matematico in modo teorico e rigoroso. "
            "Risolvi questo sistema di equazioni lineari con Gauss. "
            "Calcola il determinante e il rango di questa matrice. "
            "Dimostra per induzione matematica questa proprietà. "
            "Trova gli autovalori e autovettori di questa matrice. "
            "Studia la convergenza di questa serie numerica o successione. "
            "Applica il teorema di Taylor per sviluppare questa funzione. "
            "Calcola la probabilità di questo evento con la distribuzione statistica. "
            "Risolvi questo esercizio di algebra lineare o geometria differenziale. "
            # --- Casi ibridi math puri, senza azione di coding ---
            "Mostrami la formula matematica esatta per calcolare un risarcimento. "
            "Qual è la formula statistica per stimare la probabilità in un contesto legale? "
            "Calcola la ripartizione in frazioni e percentuali di una quota ereditaria. "
            "Qual è la complessità asintotica Big O di questo algoritmo teorico? "
        ),
        'rights': (
            # --- Diritto puro ---
            "Cosa dice la legge italiana su questo argomento giuridico? "
            "Qual è la normativa vigente in materia di diritto sportivo? "
            "Spiegami questo istituto giuridico del diritto italiano. "
            "Cosa prevede il codice civile italiano in questo caso specifico? "
            "Quali sono i diritti e doveri secondo la costituzione italiana? "
            "Come funziona il processo penale in Italia per questo reato? "
            "Cosa si intende per questo termine giuridico legale? "
            "Spiega il DASPO e la normativa sportiva italiana. "
            "Quali sanzioni prevede il codice di giustizia sportiva? "
            "Come funziona il ricorso al tribunale amministrativo regionale? "
            "Cosa dice la giurisprudenza su questo caso legale? "
            "Quali sono le fonti del diritto nell'ordinamento giuridico italiano? "
            "Spiega il significato di questo articolo di legge o decreto. "
            "Come si applica questa norma giuridica nella pratica legale? "
            "Qual è la differenza tra questi due istituti del diritto civile? "
            # --- Casi ibridi rights+tech (la norma è il focus) ---
            "Quali direttive GDPR si applicano quando si progetta un sistema informatico? "
            "Il web scraping di un sito viola le leggi sul diritto d'autore o il copyright? "
            "Come garantire che i log informatici siano prove valide in un processo penale? "
            "Quali norme del codice civile regolano la nullità di un contratto software? "
            "Come si tutelano i dati sanitari secondo la normativa europea sulla privacy? "
            "Qual è la penale legale per violazione di un contratto di licenza software? "
            "Quali sono le quote legittime di un'eredità secondo le norme giuridiche? "
            "Qual è la probabilità di vincere un ricorso in Corte di Cassazione? "
        ),
        'general': (
            "Dimmi qualcosa su questo argomento di cultura generale. "
            "Spiegami questo fenomeno storico, geografico o scientifico. "
            "Cosa pensi di questa situazione di attualità? "
            "Raccontami come funziona questo nella vita quotidiana. "
            "Dammi informazioni su questo personaggio storico o evento. "
            "Qual è la tua opinione su questo tema generico? "
            "Spiegami questo concetto in modo semplice e accessibile. "
            "Hai consigli pratici su questo argomento di vita comune? "
            "Come si fa questa cosa nella vita di tutti i giorni? "
            "Puoi aiutarmi con questa domanda di carattere generale?"
        )
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
            print(f"⚠️  PrototypeStore: embedding fallito → {e}")
            return None

    def _build_prototypes(self):
        """Costruisce i prototipi per i 4 domini usando le INTENT_SENTENCES."""
        model = config.SEMANTIC_SETTINGS['embedding_model']
        print("\n⚙️   Costruzione prototipi semantici in corso...")
        self._prototypes: Dict[str, Optional[List[float]]] = {}
        for domain, intent_text in self.INTENT_SENTENCES.items():
            vec    = self._embed(intent_text, model)
            self._prototypes[domain] = vec
            status = "✅" if vec else "❌"
            print(f"   {status}  Prototipo [{domain}] — intent sentences")
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

    classify() restituisce (List[str], float):
    - List[str]: uno o più domini. Più domini vengono restituiti quando la
      query è genuinamente ibrida (es. coding + rights), permettendo al
      dispatcher di attivare più agenti in parallelo.
    - float: confidenza del dominio principale (margin-based).

    Logica multi-dominio:
      Se il secondo classificato ha uno score entro 'multi_domain_spread'
      dal primo E supera 'multi_domain_min_score', viene incluso nella lista.

    In caso di errore restituisce (['general'], 0.0) → fallback al keyword matcher.
    """

    def __init__(self):
        self.store = PrototypeStore()
        self.model = config.SEMANTIC_SETTINGS['embedding_model']

    def classify(self, text: str) -> Tuple[List[str], float]:
        """
        Classifica il testo e restituisce (list[domini], confidenza).

        Returns:
            Tuple[List[str], float]:
                - Lista di domini (1 o 2 in caso di query ibrida)
                - Confidenza = score_1° - score_2° (margin-based)
        """
        prototypes = self.store.get()

        valid = {d: v for d, v in prototypes.items() if v is not None}
        if not valid:
            return ['general'], 0.0

        # Embedding della query
        try:
            response  = ollama.embeddings(model=self.model, prompt=text)
            query_vec = response['embedding']
        except Exception as e:
            print(f"⚠️  SemanticRouter: embedding query fallito → {e}")
            return ['general'], 0.0

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
        confidence    = top_score - second_score

        # --- LOGICA MULTI-DOMINIO ---
        # Attiva il secondo dominio solo se è genuinamente vicino al primo
        # E supera uno score minimo assoluto (evita di attivare 'general'
        # su query specialistiche dove è strutturalmente sempre basso).
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
                  f"confidence={confidence:.4f}  "
                  f"soglia={config.SEMANTIC_SETTINGS.get('confidence_threshold', 0.06):.4f}")

        return domains, confidence


# ---------------------------------------------------------------------------
# ISTANZA GLOBALE (Singleton applicativo)
# ---------------------------------------------------------------------------

semantic_router = SemanticRouter()
