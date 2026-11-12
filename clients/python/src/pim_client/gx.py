"""Great Expectations (GX Core 1.x) expectation backed by the PIM API.

    import great_expectations as gx
    from pim_client.gx import ExpectColumnValuesToFollowARule   # importing registers it

    suite.add_expectation(ExpectColumnValuesToFollowARule(column="invoice_no"))

The batch must already be in the column's natural order (sort it in the batch
definition or the query); PIM checks values in the order it receives them.
The API key comes from PIM_API_KEY (and PIM_API_URL if self-hosted).

Result: ``observed_value`` is the rule (or None); ``details`` lists breaks with
row positions within the batch, their kind (value / jump) and expected values.
"""

from __future__ import annotations

from typing import ClassVar

from great_expectations.execution_engine import PandasExecutionEngine
from great_expectations.expectations.expectation import ColumnAggregateExpectation
from great_expectations.expectations.metrics import ColumnAggregateMetricProvider, column_aggregate_value

from . import PIMClient


class ColumnPimCheck(ColumnAggregateMetricProvider):
    metric_name = "column.pim_check"
    value_keys = ("max_break_fraction",)

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column, max_break_fraction=0.2, **kwargs):
        chunks = PIMClient().check_long(column.dropna().tolist(), max_break_fraction)
        breaks = [b for _, r in chunks for b in r.breaks]
        first = chunks[0][1]
        return {"status": "rule_with_breaks" if breaks else first.status, "rule": first.rule,
                "explanation": first.explanation, "n": len(column),
                "breaks": [{"position": b.index, "kind": b.kind, "actual": b.actual,
                            "expected": str(b.expected)} for b in breaks]}


class ExpectColumnValuesToFollowARule(ColumnAggregateExpectation):
    """Expect an ordered numeric column to follow a single rule (arithmetic, geometric,
    polynomial, linear recurrence, periodic, ...), with at most ``max_breaks`` rows breaking it.

    ``max_breaks=0`` (default) fails on any break; ``require_rule=False`` also passes
    columns where no rule is found (useful when only breaks of known rules matter).
    """

    max_break_fraction: float = 0.2
    max_breaks: int = 0
    require_rule: bool = True

    metric_dependencies: ClassVar[tuple[str, ...]] = ("column.pim_check",)
    success_keys: ClassVar[tuple[str, ...]] = ("max_break_fraction", "max_breaks", "require_rule")
    domain_keys: ClassVar[tuple[str, ...]] = ("batch_id", "table", "column", "row_condition", "condition_parser")

    def _validate(self, metrics, runtime_configuration=None, execution_engine=None):
        r = metrics["column.pim_check"]
        if r["status"] == "no_rule":
            success = not self.require_rule
        else:
            success = len(r["breaks"]) <= self.max_breaks
        return {"success": success,
                "result": {"observed_value": r["rule"], "details": r}}
