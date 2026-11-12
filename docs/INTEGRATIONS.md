# Integrations

All integrations call the hosted API's `POST /v1/check`: send an ordered column
and get back the rule it follows and the rows that break it. Each break has a
`kind`:

- `value`: one wrong row. For example, a fee of 999 where the ladder says 700.
- `jump`: the sequence continues from a new value. For example, a missing
  invoice number, a repeated block, or a level shift.

Set `PIM_API_KEY` (get one at [pim-rules.vercel.app/app](https://pim-rules.vercel.app/app)); `PIM_API_URL` is only needed for an enterprise self-hosted deployment.

## Python client (`clients/python`, package `pim-client`)

Standard library only. Python 3.10+.

```python
from pim_client import PIMClient
pim = PIMClient()                       # reads PIM_API_KEY / PIM_API_URL
r = pim.check(invoice_numbers)          # up to 1,000 values per call
r.status, r.rule, r.breaks              # "rule_with_breaks", "a[n] = a[n-1] + 1", [Break(index=47, kind="jump", ...)]
pim.check_long(values)                  # longer columns, overlapping chunks; each break reported once
pim.usage()                             # plan, calls used this month
```

Retries 503 (`server_busy`) and per-minute 429s with backoff. It does not
retry `quota_exceeded`.

## Command line and CI: `pim-check`

```bash
pim-check invoices.csv --column invoice_no --order-by invoice_no --group-by branch
pim-check fees.csv --column fee --order-by effective_date --fail-on-breaks   # exit 1 on any break
some_export_command | pim-check - --column amount --json
```

Exit codes: 0 ok; 1 breaks found (with `--fail-on-breaks`) or no rule (with
`--fail-on-no-rule`); 2 usage or API error. Output gives CSV line numbers.

## pandas

```python
from pim_client.pandas import check_column
summary, broken_rows = check_column(df, "invoice_no", order_by="invoice_no", group_by="branch")
```

`broken_rows` holds the original rows plus `pim_expected` and `pim_break_kind`.

## Great Expectations (GX Core 1.x)

```python
from pim_client.gx import ExpectColumnValuesToFollowARule   # importing registers it
suite.add_expectation(ExpectColumnValuesToFollowARule(column="invoice_no"))           # fail on any break
suite.add_expectation(ExpectColumnValuesToFollowARule(column="fee", max_breaks=2))    # tolerate 2
```

- The batch must be sorted in the column's natural order (in the batch
  definition or query).
- Pandas execution engine only. For SQL sources, load the batch into pandas or
  use `pim-check`.
- Tested with GX 1.24.1.

## dbt

There is no native dbt package yet: dbt tests are SQL, and the check needs the
API. Two working patterns:

1. **CI step after `dbt build`.** Export the model and fail the pipeline on breaks:
   ```bash
   dbt build --select invoices
   psql "$DB_URL" -c "\copy (select invoice_no from analytics.invoices order by invoice_no) to stdout csv header" \
     | pim-check - --column invoice_no --fail-on-breaks
   ```
2. **Python model** (Snowflake, Databricks, BigQuery): `import pim_client` inside
   the model and write breaks to a table. On Snowflake this needs an external
   access integration allowing the API host.

A Snowflake external function and a dbt package are on the roadmap. Build them
when a customer asks for them.

## Excel add-in (`integrations/excel`)

A task pane with a **Check column** button on the Home tab:

1. Select a column of numbers.
2. PIM shows the rule, lists the breaking cells with links, and highlights
   them in red.
3. **Clear highlights** restores the original fills.

Behaviour:
- A text header in the first cell is skipped.
- Blank cells are skipped and reported.
- Any other non-numeric cell is an error. It is never silently ignored.

Setup:
- Download [`integrations/excel/manifest.xml`](../integrations/excel/manifest.xml) (it points at the
  hosted add-in on `pim-rules.vercel.app`).
- Excel on the web / Microsoft 365: **Home → Add-ins → My add-ins → Upload my add-in**. Organisation
  admins can deploy it to everyone from the Microsoft 365 admin centre.
- Excel for Mac: copy it to `~/Library/Containers/com.microsoft.Excel/Data/Documents/wef/` and restart Excel.
- Each user pastes their API key under Settings. It is stored in the add-in's local storage on that computer.
- Developing the add-in: `python integrations/excel/dev_server.py` serves it at `https://localhost:3000`
  (needs `npx office-addin-dev-certs install`); sideload `manifest.dev.xml`.

Status:
- The logic (cell parsing, row mapping, messages) is unit-tested with Node, and
  the manifest is well-formed XML.
