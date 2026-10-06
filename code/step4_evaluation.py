"""
step4_evaluation.py — CYA N | Step 4: Valutazione NN classifier
================================================================
Uso (dalla cartella del codice):
    python step4_evaluation.py              # set dev (default): si itera SOLO su questo
    python step4_evaluation.py --set test   # set bloccato: solo ai checkpoint
    python step4_evaluation.py --set all

Schema eval_dataset.jsonl: id, category, query, history, expected_domain, expected_followup,
  expected_diff_min  (soglia, record storici)  |  expected_diff (esatto 1/2/3, preferito),
  set (dev|test, default dev), tag (opz.: clean/verbose/short/long/colloquial/codeswitch/trap)
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from nn_classifier import predict, DOMAIN_NAMES, PIPELINE_CLASSES
from classifier_config import EVAL_DATASET_PATH

_BASE_DIR = Path(__file__).resolve().parent
_REQUIRED_FIELDS = {'id', 'category', 'query', 'expected_domain', 'expected_followup'}
_VALID_CATEGORIES = {'mono_domain', 'pipeline', 'false_pipeline', 'followup', 'domain_switch', 'edge_case'}
_PIPE_NAMES = {DOMAIN_NAMES[i] for i in PIPELINE_CLASSES}


def _load_eval_dataset(path: Path) -> list:
    """Fail-fast su record malformati."""
    if not path.exists():
        raise FileNotFoundError(f"Dataset di evaluation non trovato: {path}")
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
            if 'expected_diff' not in r and 'expected_diff_min' not in r:
                raise ValueError(f"Record {r['id']!r}: serve expected_diff o expected_diff_min")
            if r['expected_domain'] not in DOMAIN_NAMES:
                raise ValueError(f"Record {r['id']!r} (riga {line_num}): expected_domain "
                                 f"{r['expected_domain']!r} non valido ({DOMAIN_NAMES}).")
            if r['category'] not in _VALID_CATEGORIES:
                raise ValueError(f"Record {r['id']!r} (riga {line_num}): category {r['category']!r} non riconosciuta.")
            if r.get('set', 'dev') not in ('dev', 'test'):
                raise ValueError(f"Record {r['id']!r}: set deve essere dev|test.")
            if 'expected_diff' in r and r['expected_diff'] not in (1, 2, 3):
                raise ValueError(f"Record {r['id']!r}: expected_diff deve essere 1/2/3.")
            r.setdefault('history', [])
            r.setdefault('set', 'dev')
            records.append(r)
    return records


def _class_id_to_domain(class_id: int) -> str:
    return DOMAIN_NAMES[class_id] if 0 <= class_id < len(DOMAIN_NAMES) else "???"


def _is_pipeline(class_id: int) -> bool:
    return class_id in PIPELINE_CLASSES


def _wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return max(0.0, c - h), min(1.0, c + h)


def _fmt_ci(k: int, n: int) -> str:
    lo, hi = _wilson(k, n)
    return f"{k}/{n} = {k / max(n, 1) * 100:5.1f}%  [IC95 {lo * 100:4.1f}–{hi * 100:4.1f}]"


def run_evaluation(sets=('dev',)):
    tests = [t for t in _load_eval_dataset(EVAL_DATASET_PATH) if t['set'] in sets]
    results = []

    print("\n" + "=" * 80)
    print(f"  CYA N — STEP 4: VALUTAZIONE NN CLASSIFIER  | set={'+'.join(sets)} | query={len(tests)}")
    print("=" * 80)

    file_wrong_queries = _BASE_DIR / "wrong_query_TESTING.md"
    if file_wrong_queries.exists():
        file_wrong_queries.unlink()

    for tc in tests:
        try:
            class_id, confidence, domain_scores, difficulty, is_followup = predict(
                tc['query'], history=tc.get('history', []))
        except Exception as e:
            print(f"  ⚠ ERRORE [{tc['id']}]: {e}")
            results.append({**tc, "status": "ERROR", "actual_class_id": -1, "actual_domain": "???",
                            "actual_followup": False, "actual_diff": -1, "confidence": 0.0,
                            "ok_domain": False, "ok_followup": False, "ok_diff": False, "actual_tier": "???"})
            continue

        actual_domain = _class_id_to_domain(class_id)
        exp_domain, exp_followup = tc['expected_domain'], tc['expected_followup']
        exp_diff = tc.get('expected_diff')
        exp_diff_min = tc.get('expected_diff_min', exp_diff)

        ok_domain   = actual_domain == exp_domain
        ok_followup = is_followup == exp_followup
        ok_diff     = (difficulty == exp_diff) if exp_diff else (difficulty >= exp_diff_min)
        actual_tier = 'FALLBACK' if difficulty == 1 else 'PRIMARY'

        if ok_domain and ok_followup:
            status, errore = "✅ OK", 0
        elif ok_domain:
            status, errore = "⚠ FOLLOWUP_ERR", 1
        elif ok_followup:
            status, errore = "❌ DOMAIN_ERR", 1
        else:
            status, errore = "❌ BOTH_ERR", 1

        if errore or not ok_diff:
            with open(file_wrong_queries, "a", encoding="utf-8") as fw:
                fw.write(f"\nfrase: {tc['query']}\n{status}\n"
                         f"  → {actual_domain.upper()} (exp: {exp_domain.upper()}) {'' if ok_domain else '← WRONG'}\n"
                         f"  followup={is_followup} (exp: {exp_followup}) {'' if ok_followup else '← WRONG'}"
                         f"  diff={difficulty} (exp: {exp_diff or '>=' + str(exp_diff_min)}) "
                         f"tier={actual_tier} {'✅' if ok_diff else '❌ DIFF_ERR'}  conf={confidence:.3f}\n")

        results.append({**tc, "status": status, "actual_class_id": class_id, "actual_domain": actual_domain,
                        "actual_followup": is_followup, "actual_diff": difficulty, "confidence": confidence,
                        "ok_domain": ok_domain, "ok_followup": ok_followup, "ok_diff": ok_diff,
                        "actual_tier": actual_tier})

    _print_summary(results)
    _print_metrics(results)
    _diagnose_thresholds(results)
    return results


def _print_summary(results: list):
    by_cat = defaultdict(list)
    for r in results:
        by_cat[r['category']].append(r)

    print("=" * 80)
    print("  RIEPILOGO PER CATEGORIA")
    print("=" * 80)
    total_ok = 0
    for cat, items in by_cat.items():
        n = len(items)
        dom_ok = sum(1 for r in items if r.get('ok_domain'))
        fu_ok = sum(1 for r in items if r.get('ok_followup'))
        full_ok = sum(1 for r in items if r.get('ok_domain') and r.get('ok_followup'))
        total_ok += full_ok
        print(f"  {cat:16s}: {full_ok}/{n} corretti | domain={dom_ok}/{n} | followup={fu_ok}/{n}")
    print(f"\n  TOTALE (domain+followup): {_fmt_ci(total_ok, len(results))}")
    print("  Dettaglio errori: wrong_query_TESTING.md")


def _print_metrics(results: list):
    ok = [r for r in results if r.get('actual_class_id', -1) >= 0]
    k = len(DOMAIN_NAMES)
    conf = [[0] * k for _ in range(k)]
    for r in ok:
        conf[DOMAIN_NAMES.index(r['expected_domain'])][r['actual_class_id']] += 1

    print("\n" + "=" * 80)
    print("  CONFUSIONE DOMINIO (righe=atteso, colonne=ottenuto)")
    print("  " + " | ".join(f"{i}={n}" for i, n in enumerate(DOMAIN_NAMES)))
    print("      " + "".join(f"{j:5d}" for j in range(k)))
    for i in range(k):
        print(f"  {i:3d} " + "".join(f"{conf[i][j]:5d}" for j in range(k)))

    print("\n  PER CLASSE            recall                              precision")
    for i, name in enumerate(DOMAIN_NAMES):
        sup = sum(conf[i])
        pred = sum(conf[j][i] for j in range(k))
        tp = conf[i][i]
        prec = f"{tp}/{pred} = {tp / pred * 100:5.1f}%" if pred else "   n/d"
        print(f"  {name:16s} {_fmt_ci(tp, sup):38s} {prec}")

    mono = [r for r in ok if r['expected_domain'] not in _PIPE_NAMES]
    pipe = [r for r in ok if r['expected_domain'] in _PIPE_NAMES]
    fp = sum(1 for r in mono if r['actual_class_id'] in PIPELINE_CLASSES)
    miss = sum(1 for r in pipe if not r['ok_domain'])
    print(f"\n  FALSE-PIPELINE rate (mono → pipeline): {_fmt_ci(fp, len(mono))}")
    print(f"  PIPELINE-MISS rate (pipeline non riconosciuta): {_fmt_ci(miss, len(pipe))}")

    by_tag = defaultdict(list)
    for r in ok:
        by_tag[r.get('tag', '-')].append(r)
    if len(by_tag) > 1 or '-' not in by_tag:
        print("\n  PER TAG (domain accuracy)")
        for t, items in sorted(by_tag.items()):
            print(f"  {t:12s} {_fmt_ci(sum(1 for r in items if r['ok_domain']), len(items))}")

    ex = [r for r in ok if r.get('expected_diff')]
    if ex:
        dc = [[0] * 3 for _ in range(3)]
        for r in ex:
            dc[r['expected_diff'] - 1][r['actual_diff'] - 1] += 1
        tier_err = sum(1 for r in ex if (r['actual_diff'] == 1) != (r['expected_diff'] == 1))
        print("\n  CONFUSIONE DIFFICULTY (righe=atteso, colonne=ottenuto)")
        for i in range(3):
            print(f"  exp={i + 1}: " + "".join(f"{dc[i][j]:5d}" for j in range(3)))
        print(f"  TIER errato (fallback↔primary): {_fmt_ci(tier_err, len(ex))}")
    else:
        nd = sum(1 for r in results if not r.get('ok_diff', True))
        print(f"\n  DIFFICULTY (soglia minima, record storici): {nd} sottostime su {len(results)}")


def _diagnose_thresholds(results: list):
    print("\n  ─── DIAGNOSI PIPELINE ────────────────────────────────────")
    fp = [r for r in results if r['category'] == 'false_pipeline' and _is_pipeline(r.get('actual_class_id', -1))]
    if fp:
        print(f"  ⚠ FALSE PIPELINE ({len(fp)}): {[r['id'] for r in fp]}")
        print("    → le soglie si tarano sul VAL (train_nn.py), non su questo eval.")
    else:
        print("  ✓ Nessuna false pipeline nella categoria false_pipeline")
    print("=" * 80)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--set', choices=['dev', 'test', 'all'], default='dev')
    a = ap.parse_args()
    run_evaluation(('dev', 'test') if a.set == 'all' else (a.set,))