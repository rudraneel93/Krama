"""pandas helpers: check DataFrame columns and get the broken rows back as a DataFrame."""

from __future__ import annotations

from . import PIMClient


def check_column(df, column: str, order_by: str | list[str] | None = None, client: PIMClient | None = None,
                 max_break_fraction: float = 0.2, group_by: str | list[str] | None = None):
    """Check ``df[column]`` (sorted by ``order_by``; within each ``group_by`` group).

    Returns (summary, breaks_df). ``summary`` has one row per group with the rule
    and status; ``breaks_df`` holds the original rows that break the rule, with
    ``pim_expected`` and ``pim_break_kind`` columns added.
    """
    import pandas as pd

    client = client or PIMClient()
    frames = [((), df)] if group_by is None else list(df.groupby(group_by, sort=True))
    summary, broken = [], []
    for key, part in frames:
        part = part.sort_values(order_by, kind="stable") if order_by is not None else part
        res = client.check_long(part[column].tolist(), max_break_fraction)
        for _, r in res:
            for b in r.breaks:
                row = part.iloc[[b.index]].copy()
                row["pim_expected"] = float(b.expected)
                row["pim_break_kind"] = b.kind
                broken.append(row)
        first = res[0][1]
        summary.append({"group": key if group_by is not None else None, "rows": len(part),
                        "status": "rule_with_breaks" if any(r.breaks for _, r in res) else first.status,
                        "rule": first.rule, "breaks": sum(len(r.breaks) for _, r in res)})
    breaks_df = pd.concat(broken) if broken else df.iloc[0:0].assign(pim_expected=[], pim_break_kind=[])
    return pd.DataFrame(summary), breaks_df
