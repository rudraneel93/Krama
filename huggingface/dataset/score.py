"""Score BreakBench predictions.

    python score.py --answers practice.jsonl --predictions my_practice.jsonl

Predictions: one JSON object per line, {"id": ..., "status": ..., "breaks": [...]}, where status is
"follows_rule", "rule_with_breaks" or "no_rule" and breaks are 0-based indices. Missing items count as wrong.
Test answers are withheld; submit test predictions via a Discussion on the dataset page.
"""
import argparse
import json

CATEGORIES = ("clean", "value", "gap", "duplicate", "noise", "beyond")
STATUSES = {"follows_rule", "rule_with_breaks", "no_rule"}


def read(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def score(answers, preds):
    by_cat = {c: [] for c in CATEGORIES}
    tp = fp = fn = phantom = noise = false_alarm = clean = 0
    for a in answers:
        p = preds.get(a["id"], {"status": "missing", "breaks": []})
        status = p.get("status")
        pb, ab = set(p.get("breaks") or []), set(a["breaks"])
        if status == "no_rule":
            pb = set()
        by_cat[a["category"]].append(status == a["status"] and pb == ab)
        tp, fp, fn = tp + len(pb & ab), fp + len(pb - ab), fn + len(ab - pb)
        if a["category"] == "noise":
            noise += 1
            phantom += status != "no_rule"
        if a["category"] == "clean":
            clean += 1
            false_alarm += bool(pb) or status != "follows_rule"
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    allx = [x for v in by_cat.values() for x in v]
    return {
        "exact_accuracy": round(sum(allx) / len(allx), 4),
        "phantom_pattern_rate": round(phantom / noise, 4) if noise else None,
        "break_precision": round(prec, 4), "break_recall": round(rec, 4),
        "break_f1": round(2 * prec * rec / (prec + rec), 4) if prec + rec else 0.0,
        "clean_false_alarm_rate": round(false_alarm / clean, 4) if clean else None,
        "by_category": {c: round(sum(v) / len(v), 4) for c, v in by_cat.items() if v},
        "n": len(answers),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", required=True)
    ap.add_argument("--predictions", required=True)
    a = ap.parse_args()
    preds = {}
    for p in read(a.predictions):
        if p.get("status") not in STATUSES:
            raise SystemExit(f"{p.get('id')}: status must be one of {sorted(STATUSES)}")
        if not all(isinstance(i, int) for i in p.get("breaks") or []):
            raise SystemExit(f"{p.get('id')}: breaks must be a list of 0-based integer indices")
        preds[p["id"]] = p
    print(json.dumps(score(read(a.answers), preds), indent=2))


if __name__ == "__main__":
    main()
