"""pim-check: check columns of a CSV file (or stdin) from the command line or CI.

    pim-check invoices.csv --column invoice_no --order-by issued_at
    pim-check fees.csv --column fee --group-by product --fail-on-breaks   # exit 1 if any breaks

Exit codes: 0 ok, 1 breaks found (with --fail-on-breaks) or no rule (with --fail-on-no-rule),
2 usage or API error.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict

from . import PIMClient, PIMError


def _num(s: str, row: int, col: str):
    s = s.strip().replace(",", "")
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            raise SystemExit(f"row {row}: column {col!r} is not a number: {s!r}") from None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="pim-check", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="CSV file with a header row, or - for stdin")
    ap.add_argument("--column", required=True)
    ap.add_argument("--order-by", default=None, help="sort by this column first (numeric if possible)")
    ap.add_argument("--group-by", default=None, help="check each group separately (e.g. account id)")
    ap.add_argument("--max-break-fraction", type=float, default=0.2)
    ap.add_argument("--fail-on-breaks", action="store_true")
    ap.add_argument("--fail-on-no-rule", action="store_true")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--api-url", default=None)
    a = ap.parse_args(argv)

    fh = sys.stdin if a.file == "-" else open(a.file, newline="", encoding="utf-8-sig")  # noqa: SIM115
    with fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        print("no rows", file=sys.stderr)
        return 2
    for c in filter(None, (a.column, a.order_by, a.group_by)):
        if c not in rows[0]:
            print(f"no column {c!r}; columns are {list(rows[0])}", file=sys.stderr)
            return 2
    groups = defaultdict(list)
    for i, r in enumerate(rows, start=2):  # line 1 is the header
        groups[r[a.group_by] if a.group_by else None].append((i, r))

    def sort_key(item):
        v = item[1][a.order_by]
        try:
            return (0, float(v.replace(",", "")), "")
        except ValueError:
            return (1, 0.0, v)

    try:
        client = PIMClient(base_url=a.api_url)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    report, any_breaks, any_no_rule = [], False, False
    for g, items in groups.items():
        if a.order_by:
            items.sort(key=sort_key)
        vals = [_num(r[a.column], line, a.column) for line, r in items]
        try:
            chunks = client.check_long(vals, a.max_break_fraction)
        except PIMError as e:
            print(f"API error: {e}", file=sys.stderr)
            return 2
        breaks = [b for _, r in chunks for b in r.breaks]
        first = chunks[0][1]
        status = "rule_with_breaks" if breaks else first.status
        any_breaks |= bool(breaks)
        any_no_rule |= status == "no_rule"
        report.append({"group": g, "rows": len(vals), "status": status, "rule": first.rule,
                       "explanation": first.explanation,
                       "breaks": [{"line": items[b.index][0], "kind": b.kind, "actual": b.actual,
                                   "expected": str(b.expected)} for b in breaks]})
    if a.json:
        print(json.dumps(report, indent=2))
    else:
        for r in report:
            head = f"[{r['group']}] " if a.group_by else ""
            if r["status"] == "no_rule":
                print(f"{head}{r['rows']} rows: no rule found")
                continue
            print(f"{head}{r['rows']} rows: {r['rule']}  ({r['explanation']})")
            for b in r["breaks"]:
                what = "sequence jumps" if b["kind"] == "jump" else "wrong value"
                print(f"   line {b['line']}: {b['actual']} but rule expects {b['expected']} ({what})")
            if not r["breaks"]:
                print("   all rows follow the rule")
    if (a.fail_on_breaks and any_breaks) or (a.fail_on_no_rule and any_no_rule):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
