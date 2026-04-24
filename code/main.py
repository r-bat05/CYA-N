"""
    CYA N - AI LOCAL DISPATCHER V6.8.0
    Entry Point dell'applicazione.

    Novità V6.8.0:
    - [STICKY_FIX2] _should_sticky_route() riceve original_sem_domains (pre-declassificazione).
      L'override controlla tutti i domini della lista originale, non solo il top finale.
      Questo sblocca il context switch per query brevi ibride (es. Q43 "Teorema di Pitagora"
      classificato ['rights','math'] declassificato a ['rights']: ora l'override vede 'math'
      e scatta correttamente verso di esso).
    - [STICKY_FIX2] _should_sticky_route() restituisce 4-tuple:
      (should_stick, sticky_domain, reason, override_target).
      override_target è il dominio tecnico target del context switch (None se sticky attivo).
    - [STICKY_FIX2] Trigger 1 (is_short): aggiunta eccezione per query corte su dominio
      'general' con bassa confidenza e 0 keyword del last_domain → topic change genuino,
      non follow-up. Risolve Q45 "orchidee in casa" che restava sticky su 'coding'.
    - [STICKY_FIX2] Trigger 2 (weak_general): aggiunto gate su keyword: se nessuna keyword
      del last_domain è presente nella query, non è un follow-up → sticky non si attiva.
    - [STICKY_FIX2] Aggiunta _has_domain_keywords() per verificare presenza keyword di dominio.
    - [STICKY_FIX2] Routing: aggiunto branch elif override_target per instradare il context
      switch verso il dominio corretto senza passare per la pipeline ibrida.
    - Tutti i call site di _should_sticky_route aggiornati al 4-tuple.

    Novità V6.7.4:
    - [STICKY_FIX] _should_sticky_route() estesa con 2 nuovi trigger:
      * Weak-General Trigger: k-NN → 'general' con confidenza < sticky_weak_general_conf
        durante sessione tecnica attiva → Domain Retention forzato.
      * Pattern Trigger: substring italiane di follow-up esplicite (config:
        sticky_followup_triggers) attivano sticky indipendentemente dalla lunghezza.
      Risolve il "Conversational Boundary Problem" segnalato da Gemini.
    - [STICKY_FIX] Aggiunto campo 'reason' al return di _should_sticky_route()
      per debug log granulare. Tutti i call site aggiornati di conseguenza.

    Novità V6.7.3:
    - [BUG1] _ERROR_PREFIXES: "ATTENZIONE:" sostituito con "__SYS_WARN__:".
    - [REFACTOR] Eliminato il layer di astrazione semantic_router.py.

    Novità V6.7.2:
    - [BUG2] Rimosso Override A da _should_sticky_route(): era dead code.

    Novità V6.7.0:
    - [STICKY] Implementazione Domain Retention (Sticky Routing).

    Novità V6.6.0:
    - [CHAT] chat_history: lista globale di sessione (sliding window).
    - [CHAT] Comando '/reset' per svuotare history.

    Novità V6.5.0:
    - [P0] GENERAL isolation: downgrade ibrido se un dominio è 'general'.
    - [P4] timeout_sincronizzazione letto da config.PIPELINE_SETTINGS.
"""

import re as _re
import sys
import time
import psutil
import config
import dispatcher_request
from ai_engine import get_ai_model, ResourceExhaustedError
from vector_store import classify_knn
from vector_store import initialize_store
from dispatcher_request import keyword_loader, _count_hits

_ERROR_PREFIXES    = ("Errore Ollama:", "Errore Generico:", "__SYS_WARN__:")
_TECHNICAL_DOMAINS = {'coding', 'math', 'rights'}


def print_banner():
    print("\n" + "=" * 60)
    print("      CYA N  |  AI LOCAL DISPATCHER V6.8.0    ")
    print("      (Coding • Math • Rights • General)      ")
    print("=" * 60 + "\n")


def _update_history(history: list, user_input: str, response: str, max_messages: int):
    """[CHAT] Aggiunge il turno corrente alla history e applica la sliding window."""
    history.append({'role': 'user',      'content': user_input})
    history.append({'role': 'assistant', 'content': response})
    if len(history) > max_messages:
        del history[:len(history) - max_messages]


def _is_error(result: str) -> bool:
    """Controlla se il risultato è un messaggio d'errore di sistema."""
    return not result or any(result.startswith(p) for p in _ERROR_PREFIXES)


def _has_domain_keywords(query: str, domain: str) -> bool:
    """
    [V6.8.0] Restituisce True se la query contiene almeno una keyword del dominio dato.
    Usato come gate per i trigger sticky che potrebbero sparare su topic change genuini.
    """
    kw_map = {
        'coding': keyword_loader.CODING,
        'math':   keyword_loader.MATH,
        'rights': keyword_loader.RIGHTS,
    }
    if domain not in kw_map:
        return False
    s_lower = query.lower()
    tokens  = set(_re.findall(r'[a-zA-Z0-9_+#]+', s_lower))
    return _count_hits(tokens, s_lower, kw_map[domain]) > 0


def _should_sticky_route(
    query: str,
    sem_domains: list,       # Domini ORIGINALI pre-declassificazione
    sem_confidence: float,
    last_domain: str
) -> tuple:
    """
    [STICKY V5 / V6.8.0] Domain Retention con 3 trigger indipendenti.

    sem_domains deve essere la lista ORIGINALE prima della declassificazione.
    Questo permette all'override di rilevare context switch anche su query brevi
    ibride (es. ['rights','math'] declassificata a ['rights']: 'math' rimane
    visibile nell'override e può innescare il context switch corretto).

    Trigger 1 — Query corta: follow-up pattern classico (< sticky_short_words).
                Eccezione: top='general' + bassa conf + 0 keyword last_domain
                → topic change genuino, non follow-up.
    Trigger 2 — Weak-General: k-NN → 'general' con bassa confidenza su sessione
                tecnica E presenza di keyword del last_domain nella query.
    Trigger 3 — Pattern espliciti: substring italiane di follow-up presenti nella
                query → sticky forzato indipendentemente da lunghezza e confidenza.

    Override: se qualsiasi dominio tecnico != last_domain è presente in sem_domains
    con confidenza >= tech_switch_min → context switch (sticky non applicato).
    override_target = top domain della lista originale se candidato, altrimenti
    il primo dominio switching trovato.

    Returns:
        (should_stick: bool, sticky_domain: str, reason: str, override_target: str|None)
        override_target: dominio verso cui instradare in caso di context switch.
    """
    if not last_domain or last_domain not in _TECHNICAL_DOMAINS:
        return False, last_domain, '', None

    tech_switch_min   = config.SYSTEM_SETTINGS.get('sticky_tech_switch_min',   0.45)
    short_threshold   = config.SYSTEM_SETTINGS.get('sticky_short_words',        7)
    weak_gen_conf     = config.SYSTEM_SETTINGS.get('sticky_weak_general_conf',  0.65)
    followup_triggers = config.SYSTEM_SETTINGS.get('sticky_followup_triggers',  [])

    top_domain = sem_domains[0] if sem_domains else 'general'
    is_short   = len(query.split()) < short_threshold

    # --- Override: context switch verso dominio tecnico diverso ---
    # [V6.8.0] Usa la lista ORIGINALE pre-declassificazione: anche il secondo dominio
    # di un ibrido declassificato è visibile e può innescare il context switch.
    switching_domains = [
        d for d in sem_domains
        if d in _TECHNICAL_DOMAINS and d != last_domain
    ]
    if switching_domains and sem_confidence >= tech_switch_min:
        # Preferisce il top k-NN se è candidato al switch, altrimenti il primo trovato
        override_target = top_domain if top_domain in switching_domains else switching_domains[0]
        return False, last_domain, '', override_target

    # --- Trigger 1: query corta ---
    if is_short:
        # [V6.8.0] Eccezione: k-NN → general con bassa confidenza + 0 keyword last_domain
        # → cambio argomento reale (es. "orchidee in casa" dopo sessione coding)
        if (top_domain == 'general'
                and sem_confidence < weak_gen_conf
                and not _has_domain_keywords(query, last_domain)):
            return False, last_domain, 'short_no_kw_general', None
        return True, last_domain, 'query_corta', None

    # --- Trigger 2: Weak-General (confidenza bassa su general) ---
    if top_domain == 'general' and sem_confidence < weak_gen_conf:
        # [V6.8.0] Gate: se nessuna keyword del last_domain è presente nella query,
        # si tratta di un cambio topic genuino, non di un follow-up discorsivo.
        if _has_domain_keywords(query, last_domain):
            return True, last_domain, f'weak_general(conf={sem_confidence:.2f}<{weak_gen_conf})', None
        return False, last_domain, '', None

    # --- Trigger 3: Pattern espliciti di follow-up ---
    query_lower = query.lower()
    for trigger in followup_triggers:
        if trigger in query_lower:
            return True, last_domain, f'pattern_match("{trigger}")', None

    return False, last_domain, '', None


def main():
    print_banner()

    print("⚙️  Inizializzazione Vector Store (Distance-Weighted k-NN su LanceDB)...")
    store_ok = initialize_store()
    if not store_ok:
        print("⚠️  VectorStore non disponibile. Il sistema userà il fallback a keyword per tutto il routing.")

    agents = {
        'coding':  get_ai_model('coding'),
        'math':    get_ai_model('math'),
        'rights':  get_ai_model('rights'),
        'general': get_ai_model('general')
    }

    # [CHAT] Stato globale di sessione
    chat_history: list = []
    max_history_turns  = config.SYSTEM_SETTINGS.get('max_history_turns', 3)
    max_messages       = max_history_turns * 2

    # [STICKY] Dominio primario dell'ultimo turno valido (solo domini tecnici)
    last_active_domain: str = ''

    while True:
        try:
            try:
                user_input = input("Inserisci la tua richiesta (o 'exit' per uscire): ").strip()
            except EOFError:
                break

            if not user_input:
                print("⚠️  Richiesta vuota. Riprova.")
                continue

            if user_input.lower() in ['exit', 'esci', 'quit', 'q']:
                print("\nChiusura sessione. A presto! 👋")
                break

            # [CHAT+STICKY] Comando reset
            if user_input.lower() in ['/reset', '/clear']:
                chat_history.clear()
                last_active_domain = ''
                print("🔄 Chat history e dominio attivo azzerati.\n")
                continue

            # ---------------------------------------------------------
            # FASE 0: ROUTING SEMANTICO VETTORIALE
            # ---------------------------------------------------------
            print("\n⚙️  Fase 0 — Valutazione Arco Semantico Vettoriale (Distance-Weighted k-NN)...")
            sem_domains, sem_confidence, sem_ok = classify_knn(user_input)

            is_hybrid  = False
            domain_a   = domain_b = ""
            categories_segments = {k: [] for k in agents.keys()}

            # =============================================================
            # CASO FALLBACK: servizio embedding non disponibile
            # =============================================================
            if not sem_ok:
                print("⚠️  [FALLBACK] Servizio embedding non disponibile.")
                print("🔄 [FALLBACK] Attivazione instradamento a Keyword come emergenza...")

                is_hybrid, domain_a, domain_b = dispatcher_request.detect_hybrid(user_input)
                if not is_hybrid:
                    winning_domain = dispatcher_request.classify_segment(user_input)
                    if winning_domain == 'general':
                        # Nel fallback sem_ok=False, passiamo confidenza 1.0 per disabilitare
                        # il Weak-General Trigger (senza embedding non conosciamo la confidenza
                        # reale). Lo sticky si affida solo al pattern trigger e alla lunghezza.
                        stick, sticky_domain, reason, override_target = _should_sticky_route(
                            user_input, ['general'], 1.0, last_active_domain
                        )
                        if stick:
                            print(f"📎 [STICKY] Keyword fallback su 'general'. "
                                  f"Domain Retention → {sticky_domain.upper()} [{reason}]")
                            winning_domain = sticky_domain
                        elif override_target:
                            winning_domain = override_target

                    categories_segments[winning_domain if winning_domain in categories_segments
                                        else 'general'] = [user_input]

            else:
                word_count = len(user_input.split())
                min_words  = config.PIPELINE_SETTINGS.get('min_words_for_pipeline', 8)

                # [V6.8.0] Salva i domini ORIGINALI prima della declassificazione.
                # _should_sticky_route li usa per rilevare switch anche su ibridi
                # declassificati (es. ['rights','math'] → ['rights']: 'math' rimane visibile).
                original_sem_domains = list(sem_domains)

                if len(sem_domains) == 2 and word_count < min_words:
                    print(f"🔍 [DEBUG SEMANTICO] Arco Ibrido declassato: "
                          f"query troppo corta ({word_count} < {min_words} parole).")
                    sem_domains = [sem_domains[0]]

                print(f"🔍 [DEBUG SEMANTICO] Domini: {sem_domains}  |  "
                      f"Confidence k-NN: {sem_confidence:.2f}")

                # ---------------------------------------------------------
                # [STICKY] Valutazione Domain Retention
                # Usa original_sem_domains per l'override (lista completa pre-declassificazione)
                # ---------------------------------------------------------
                stick, sticky_domain, reason, override_target = _should_sticky_route(
                    user_input, original_sem_domains, sem_confidence, last_active_domain
                )

                if stick:
                    print(f"📎 [STICKY] Domain Retention attivo: "
                          f"routing forzato → {sticky_domain.upper()} "
                          f"(last='{last_active_domain}', "
                          f"k-NN top='{sem_domains[0]}', conf={sem_confidence:.2f}, "
                          f"trigger='{reason}')")
                    is_hybrid = False
                    categories_segments[sticky_domain] = [user_input]

                elif override_target:
                    # [V6.8.0] Context switch esplicito verso dominio tecnico rilevato
                    # dall'override (anche da domini ibridi pre-declassificazione).
                    print(f"🔀 [SWITCH] Context switch rilevato: "
                          f"{last_active_domain.upper() if last_active_domain else 'NONE'} → "
                          f"{override_target.upper()} "
                          f"(conf={sem_confidence:.2f})")
                    is_hybrid = False
                    categories_segments[override_target if override_target in categories_segments
                                        else 'general'] = [user_input]

                elif len(sem_domains) == 2:
                    print(f"🔍 [DEBUG SEMANTICO] Arco Ibrido confermato "
                          f"(min_score={config.SEMANTIC_SETTINGS.get('knn_min_score', 3.0):.2f}, "
                          f"min_vote_ratio={config.SEMANTIC_SETTINGS.get('knn_min_vote_ratio', 0.30)}).")
                    is_hybrid = True

                    pair   = frozenset(sem_domains)
                    matrix = config.PIPELINE_SETTINGS['pipeline_order_matrix']
                    if pair in matrix:
                        domain_a, domain_b = matrix[pair]
                        print(f"🔍 [DEBUG SEMANTICO] Ordine da pipeline_order_matrix: "
                              f"{domain_a.upper()} → {domain_b.upper()}")
                    else:
                        domain_a, domain_b = sem_domains[0], sem_domains[1]
                        print(f"🔍 [DEBUG SEMANTICO] Coppia non in matrice. "
                              f"Ordine da score k-NN: {domain_a.upper()} → {domain_b.upper()}")

                else:
                    target = sem_domains[0]
                    print(f"🔍 [DEBUG SEMANTICO] Dominio: {target.upper()}")
                    categories_segments[target if target in categories_segments
                                        else 'general'] = [user_input]

            # ---------------------------------------------------------
            # [P0] GUARDIA GENERAL
            # ---------------------------------------------------------
            if is_hybrid and 'general' in (domain_a, domain_b):
                target = 'general' if domain_a == 'general' else domain_a
                print(f"🔍 [P0 GENERAL GUARD] Downgrade ibrido: GENERAL isolato. "
                      f"Routing mono-dominio → {target.upper()}")
                is_hybrid = False
                categories_segments[target] = [user_input]

            # ---------------------------------------------------------
            # ESECUZIONE PIPELINE IBRIDA
            # ---------------------------------------------------------
            if is_hybrid:
                print(f"\n╭── 🧠 PIPELINE IBRIDA [{domain_a.upper()} → {domain_b.upper()}] in azione...")
                print(f"│ Agente A (Draft): {agents[domain_a].model_name}")
                print(f"│ Agente B (Merge): {agents[domain_b].model_name}")
                print(f"╰──────────────────────────────────────────")

                # FASE 1/3: Agente A
                print(f"\n⚙️  Fase 1/3 — Elaborazione contesto [{domain_a.upper()}] in corso...")
                try:
                    output_a = agents[domain_a].resolve_pipeline_a(
                        user_input, domain_b, chat_history
                    )
                except ResourceExhaustedError as e:
                    print(f"\n⛔ OOM — Pipeline interrotta in Fase 1/3: {e}")
                    print("\n" + "_" * 60 + "\n")
                    continue

                if _is_error(output_a):
                    print(output_a)
                    print("\n" + "_" * 60 + "\n")
                    continue

                # Sincronizzazione RAM [P4 + DIFETTO2 FIX]
                print("⚙️  Sincronizzazione — Scaricamento esplicito modello A in corso...")
                agents[domain_a].explicit_unload()

                unload_wait              = config.PIPELINE_SETTINGS.get('ram_unload_wait', 1.5)
                target_ram               = agents[domain_b].primary_ram_req
                timeout_sincronizzazione = config.PIPELINE_SETTINGS.get('ram_sync_timeout', 20.0)
                inizio_attesa            = time.time()
                time.sleep(unload_wait)

                while (time.time() - inizio_attesa) < timeout_sincronizzazione:
                    if psutil.virtual_memory().available >= target_ram:
                        break
                    time.sleep(0.5)
                else:
                    print("⚠️  Timeout sincronizzazione RAM: procedo comunque.")

                # FASE 2/3: Agente B
                print(f"⚙️  Fase 2/3 — Integrazione dominio [{domain_b.upper()}] in corso...")
                try:
                    output_b = agents[domain_b].resolve_pipeline_b(
                        user_input, output_a, domain_a, chat_history
                    )
                except ResourceExhaustedError as e:
                    print(f"\n⛔ OOM — Pipeline interrotta in Fase 2/3: {e}")
                    print("\n" + "_" * 60 + "\n")
                    continue

                if _is_error(output_b):
                    print(output_b)
                    print("\n" + "_" * 60 + "\n")
                    continue

                # FASE 3/3: Critic Pass
                print(f"⚙️  Fase 3/3 — Autovalutazione e sintesi [{domain_b.upper()}]...")
                print("-" * 42)

                try:
                    result = agents[domain_b].execute_critic_pass(output_b, user_input)
                except ResourceExhaustedError as e:
                    print(f"\n⛔ OOM — Pipeline interrotta in Fase 3/3: {e}")
                    print("\n" + "_" * 60 + "\n")
                    continue

                if _is_error(result):
                    print(result)
                else:
                    _update_history(chat_history, user_input, result, max_messages)
                    last_active_domain = domain_b

                print("\n" + "_" * 60 + "\n")
                continue

            # ---------------------------------------------------------
            # ESECUZIONE MONO-DOMINIO
            # ---------------------------------------------------------
            has_tasks = any(segments for segments in categories_segments.values())
            if not has_tasks:
                print("⚠️  Input non processabile o archi non individuati.")
                continue

            for category, segments in categories_segments.items():
                if not segments:
                    continue

                full_query = "\n".join(segments)
                ai_agent   = agents[category]

                print(f"\n╭── 🧠 MODULO [{category.upper()}] in azione...")
                print(f"│ Modello: {ai_agent.model_name}")
                print(f"╰──────────────────────────────────────────")

                try:
                    result = ai_agent.resolve(full_query, chat_history)
                except ResourceExhaustedError as e:
                    print(f"\n⛔ OOM — Esecuzione interrotta: {e}")
                    print("\n" + "_" * 60 + "\n")
                    continue

                if _is_error(result):
                    print(result)
                else:
                    _update_history(chat_history, user_input, result, max_messages)
                    if category in _TECHNICAL_DOMAINS:
                        last_active_domain = category

                print("\n" + "_" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n\n🛑 Interruzione manuale rilevata.")
            print("Chiusura sicura degli archi di sistema...")
            sys.exit(0)

        except Exception as e:
            print(f"\n❌ ERRORE IMPREVISTO: {e}")
            print("Consiglio: Verifica che l'arco di comunicazione con Ollama sia attivo.")


if __name__ == "__main__":
    main()
