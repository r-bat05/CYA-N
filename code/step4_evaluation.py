"""
step4_evaluation.py — CYA N | Step 4: Valutazione qualitativa NN classifier
=============================================================================
[REFACTOR — report_patch.md §4] Il dataset di valutazione non è più
hardcoded (SMOKE_TESTS): vive in eval_dataset.jsonl, caricato con lo
stesso pattern fail-fast già in uso per difficulty_labels.json.
Aggiungere un caso di test = aggiungere una riga JSON, zero tocchi qui.

Rimossi DEAD-1 (last_domain, mai letto) e DEAD-2 (expected_class_id, mai
confrontato: solo expected_domain viene verificato).
[ARCH-1 FIX] wrong_query_TESTING.md ora ancorato a _BASE_DIR invece che
alla cwd.

Esecuzione:
    cd <root_progetto>
    python code/step4_evaluation.py
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from nn_classifier import predict, DOMAIN_NAMES, PIPELINE_CLASSES
from classifier_config import EVAL_DATASET_PATH

_BASE_DIR = Path(__file__).resolve().parent
_REQUIRED_FIELDS = {'id', 'category', 'query', 'expected_domain',
                     'expected_followup', 'expected_diff_min'}
_VALID_CATEGORIES = {
    'mono_domain', 'pipeline', 'false_pipeline',
    'followup', 'domain_switch', 'edge_case',
}


def _load_eval_dataset(path: Path) -> list:
    """Fail-fast: record malformato o dominio atteso sconosciuto fa fallire subito."""
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset di evaluation non trovato: {path}\n"
            f"Vedi report_patch.md §4 per lo schema atteso."
        )
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            missing = _REQUIRED_FIELDS - r.keys()
            if missing:
                raise ValueError(f"Record riga {line_num} privo dei campi {missing}: {r}")
            if r['expected_domain'] not in DOMAIN_NAMES:
                raise ValueError(
                    f"Record {r['id']!r} (riga {line_num}): expected_domain "
                    f"{r['expected_domain']!r} non è un dominio valido ({DOMAIN_NAMES})."
                )
            if r['category'] not in _VALID_CATEGORIES:
                raise ValueError(
                    f"Record {r['id']!r} (riga {line_num}): category "
                    f"{r['category']!r} non riconosciuta ({_VALID_CATEGORIES})."
                )
            r.setdefault('history', [])
            records.append(r)
    return records


def _class_id_to_domain(class_id: int) -> str:
    return DOMAIN_NAMES[class_id] if 0 <= class_id < len(DOMAIN_NAMES) else "???"


def _is_pipeline(class_id: int) -> bool:
    return class_id in PIPELINE_CLASSES


def run_evaluation():
    tests = _load_eval_dataset(EVAL_DATASET_PATH)
    results = []

    print("\n" + "=" * 80)
    print("  CYA N — STEP 4: SMOKE TEST NN CLASSIFIER")
    print("=" * 80)
    print(f"  Query totali: {len(tests)}\n")

    file_wrong_queries = _BASE_DIR / "wrong_query_TESTING.md"  # [ARCH-1 FIX]
    if file_wrong_queries.exists():
        file_wrong_queries.unlink()

    for tc in tests:
        # print(f"  [{tc['id']}] {tc['query'][:65]}{'...' if len(tc['query']) > 65 else ''}")

        try:
            class_id, confidence, domain_scores, difficulty, is_followup = predict(
                tc['query'],
                history=tc.get('history', []),
            )
        except Exception as e:
            print(f"         ⚠ ERRORE: {e}")
            results.append({**tc, "status": "ERROR", "actual_class_id": -1,
                            "actual_domain": "???", "actual_followup": False,
                            "actual_diff": -1, "confidence": 0.0,
                            "ok_diff": False, "actual_tier": "???"})
            continue

        actual_domain = _class_id_to_domain(class_id)
        exp_domain    = tc['expected_domain']
        exp_followup  = tc['expected_followup']
        exp_diff_min  = tc['expected_diff_min']

        ok_domain   = actual_domain == exp_domain
        ok_followup = is_followup   == exp_followup
        ok_diff     = difficulty >= exp_diff_min
        actual_tier = 'FALLBACK' if difficulty == 1 else 'PRIMARY'

        errore = 0
        if ok_domain and ok_followup:
            status = "✅ OK"
        elif ok_domain and not ok_followup:
            status = "⚠ FOLLOWUP_ERR"
            errore = 1
        elif not ok_domain and ok_followup:
            status = "❌ DOMAIN_ERR"
            errore = 1
        else:
            status = "❌ BOTH_ERR"
            errore = 1

        dom_str = (f"  → {actual_domain.upper()} "
                   f"(exp: {exp_domain.upper()}) {'' if ok_domain else '← WRONG'}")
        fu_str  = (f"  followup={is_followup} "
                   f"(exp: {exp_followup}) {'' if ok_followup else '← WRONG'}")
        d_str   = (f"  diff={difficulty} (min atteso: {exp_diff_min}) → "
                   f"tier={actual_tier} {'✅' if ok_diff else '❌ DIFF_ERR'}  conf={confidence:.3f}")

        '''print(f"     {status}")
        print(f"     {dom_str}")
        print(f"     {fu_str}")
        print(f"     {d_str}")
        if 'note' in tc:
            print(f"     📝 {tc['note']}")
        print()'''

        if errore == 1 or not ok_diff:
            with open(file_wrong_queries, "a", encoding="utf-8") as file:
                file.write(f"\nfrase: {tc['query']}\n{status}\n{dom_str}\n{fu_str}{d_str}\n")

        results.append({
            **tc,
            "status":           status,
            "actual_class_id":  class_id,
            "actual_domain":    actual_domain,
            "actual_followup":  is_followup,
            "actual_diff":      difficulty,
            "confidence":       confidence,
            "ok_domain":        ok_domain,
            "ok_followup":      ok_followup,
            "ok_diff":          ok_diff,
            "actual_tier":      actual_tier,
        })

    _print_summary(results)
    _diagnose_thresholds(results)
    return results


def _print_summary(results: list):
    by_cat = {}
    for r in results:
        cat = r['category']
        by_cat.setdefault(cat, []).append(r)

    print("=" * 80)
    print("  RIEPILOGO PER CATEGORIA")
    print("=" * 80)

    total_ok = 0
    for cat, items in by_cat.items():
        dom_ok = sum(1 for r in items if r.get('ok_domain', False))
        fu_ok  = sum(1 for r in items if r.get('ok_followup', True))
        n      = len(items)
        full_ok = sum(1 for r in items if r.get('ok_domain') and r.get('ok_followup'))
        total_ok += full_ok
        print(f"  {cat:20s}: {full_ok}/{n} completamente corretti | "
              f"domain={dom_ok}/{n} | followup={fu_ok}/{n}")

    total = len(results)
    print(f"\n  TOTALE: {total_ok}/{total} ({total_ok/total*100:.1f}%)")

    errors = [r for r in results if "❌" in r.get('status', '')]
    warnings = [r for r in results if "⚠" in r.get('status', '')]

    if errors:
        print(f"\n  ─── ERRORI CRITICI ({len(errors)}) ───────────────────────")
        for r in errors:
            print(f"  [{r['id']}] atteso={r['expected_domain'].upper()} "
                  f"→ ottenuto={r['actual_domain'].upper()} | "
                  f"query: {r['query'][:55]}...")

    if warnings:
        print(f"\n  ─── AVVERTENZE followup ({len(warnings)}) ──────────────────")
        for r in warnings:
            print(f"  [{r['id']}] followup atteso={r['expected_followup']} "
                  f"→ ottenuto={r['actual_followup']} | "
                  f"query: {r['query'][:55]}...")

    diff_ok_n  = sum(1 for r in results if r.get('ok_diff', False))
    diff_total = len(results)
    print(f"\n  ─── VERIFICA DIFFICULTY / TIER ROUTING ({diff_ok_n}/{diff_total}) ─────")
    diff_errors = [r for r in results if not r.get('ok_diff', True)]
    if diff_errors:
        for r in diff_errors:
            print(f"  [{r['id']}] diff={r.get('actual_diff')} < atteso_min={r['expected_diff_min']} "
                  f"→ tier={r.get('actual_tier')} | query: {r['query'][:55]}...")
    else:
        print(f"  ✓ Tutte le query rispettano la soglia difficulty attesa.")


def _diagnose_thresholds(results: list):
    print(f"\n  ─── DIAGNOSI SOGLIE PIPELINE ────────────────────────────────")

    pipeline_correct = [r for r in results if r['category'] == 'pipeline' and r.get('ok_domain')]
    pipeline_wrong   = [r for r in results if r['category'] == 'pipeline' and not r.get('ok_domain')]
    false_pipe       = [r for r in results if r['category'] == 'false_pipeline' and
                        _is_pipeline(r.get('actual_class_id', -1))]

    if pipeline_correct:
        confs = [r['confidence'] for r in pipeline_correct]
        print(f"  Pipeline corrette ({len(pipeline_correct)}): "
              f"conf min={min(confs):.3f} mean={sum(confs)/len(confs):.3f}")

    if pipeline_wrong:
        print(f"  Pipeline mancate  ({len(pipeline_wrong)}): "
              f"IDs = {[r['id'] for r in pipeline_wrong]}")

    if false_pipe:
        print(f"  ⚠ FALSE PIPELINE  ({len(false_pipe)}): "
              f"IDs = {[r['id'] for r in false_pipe]}")
        confs_fp = [r['confidence'] for r in false_pipe]
        print(f"    → Alzare PIPELINE_PAIR_THRESHOLD sopra {max(confs_fp):.3f}")
    else:
        print(f"  ✓ Nessuna false pipeline rilevata")

    print("=" * 80)


if __name__ == '__main__':
    run_evaluation()