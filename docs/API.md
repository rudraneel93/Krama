# PIM pilot API

Base URL: `https://getkrama.vercel.app/api` (the hosted Krama API). JSON in, JSON out. Get a key at [getkrama.vercel.app/app](https://getkrama.vercel.app/app).

## Authentication
Send the API key as `X-API-Key: <key>` or `Authorization: Bearer <key>`.
`/healthz` needs no key. All other endpoints return `401` without a valid key.

## `POST /v1/discover`

Request:

| field | type | default | notes |
|---|---|---|---|
| `values` | array of numbers | required | 1–1000 observations, in order; `|v| ≤ 1e15`; at most 12 decimal places in exact mode; booleans and strings rejected |
| `noise_level` | number ≥ 0 | `0` | known noise standard deviation. `0` = exact rational engine; `> 0` = statistical engine (least squares, BIC, prediction intervals) |
| `holdout` | integer ≥ 0 | about 20% of the observations | trailing observations hidden from selection; the selected rule must also survive them |
| `steps` | 0–64 | `8` | length of the predicted continuation |
| `space` | `"core"` \| `"extended"` | `"extended"` | `core` = 7 families; `extended` adds degree-4/5 polynomials and linear recurrences of order 3–6 |
| `detail` | `"summary"` \| `"full"` | `"summary"` | `full` also returns every candidate hypothesis and its verification report |

Unknown fields are rejected, and types are strict: `"steps": false` or `"holdout": "3"` return 422 rather than being coerced.

Response (`200`):

```json
{
  "request_id": "31bcb1d4…",
  "pim_version": "0.1.0",
  "schema_version": "0.1.0",
  "input_sha256": "…",            // SHA-256 of the canonical request, for audit trails
  "space": "extended",
  "elapsed_ms": 5.2,
  "engine": "exact",              // or "statistical"
  "found": true,                  // false = PIM abstains: no searched family fits
  "explanation": {
    "pattern": "Linear recurrence",
    "explanation": "Each element is a fixed linear combination of the 3 preceding elements …",
    "formal_expression": "a[n] = a[n-1] + a[n-2] + a[n-3]",
    "evidence": [ … one-step checks, holdout result, predicted continuation … ],
    "limitations": [ "Finite observations cannot uniquely determine an unrestricted rule.", … ],
    "verification_status": "consistent_with_observations"
  },
  "verification": {
    "observations_tested": 6, "observations_matched": 6,
    "holdout_tested": 2, "holdout_matches": 2,
    "counterexamples": [],
    "status": "consistent_with_observations",
    "uniqueness_established": false,
    "equivalent_alternatives": [], "competing_alternatives": [], …
  },
  "continuation": [274, 504, 927, …],
  "notes": []
}
```

How to read the result:
- `found: false` is a normal, useful answer: nothing in the search space fits.
  Do not substitute a guess.
- `verification_status` is never a proof: `consistent_with_observations`
  (exact), `consistent_within_tolerance` (noisy), or `underdetermined`
  (no observation was left to test the rule; treat it as weak).
- `competing_alternatives` non-empty means another rule also fits but predicts
  a different continuation. Treat the continuation as uncertain.
- Non-integer exact values are returned as strings like `"3/2"`.

## `POST /v1/check`

Does an ordered column follow a rule, and which rows break it? Use this for
data-quality checks. `discover` abstains if any value is wrong; `check` finds
the rule most rows follow and lists the exceptions.

| field | type | default | notes |
|---|---|---|---|
| `values` | array of numbers | required | 2–1000, in order; exact values (≤ 12 decimals) |
| `max_break_fraction` | number in [0, 0.5) | `0.2` | most rows allowed to break; above this the answer is `no_rule` |
| `space` | `"core"` \| `"extended"` | `"extended"` | rule families searched |

Response (`200`):

```json
{
  "status": "rule_with_breaks",          // or "follows_rule" or "no_rule"
  "n": 119,
  "rule": "a[n] = a[n-1] + 1",
  "family": "arithmetic",
  "explanation": "Each element is the preceding element plus 1.",
  "conforming_fraction": 0.9916,
  "breaks": [{"index": 47, "kind": "jump", "actual": 5048, "expected": 5047}],
  "verification_status": "consistent_with_observations",
  "notes": ["Breaks are jumps: the sequence continues from the new value ..."],
  "request_id": "…", "input_sha256": "…", "elapsed_ms": 41.2
}
```

- `kind: "value"` means one wrong row. Later rows are checked against the
  corrected value.
- `kind: "jump"` means the sequence continues from the new value: a gap, a
  repeated block or a level shift.
- The rule is confirmed by the verified engine on the corrected sequence,
  including its held-out check.
- Very short columns (fewer than about 10 rows) often return `no_rule`: there
  is too little evidence to tell a break from a different rule.

## `GET /v1/usage`
Plan, current period, calls used, and calls and rows per endpoint .

## `GET /v1/info`
Version, the families in each search space, the limits and the behavioural guarantees.

## `GET /healthz`
`{"status": "ok"}`, no auth; for load balancers.

## Errors
Body: `{"error": {"code": "...", "message": "..."}, "request_id": "..."}`. Submitted values are never echoed.

| status | code | when |
|---|---|---|
| 400 | `bad_request` | body is not valid JSON |
| 401 | `unauthorized` | missing or invalid key (checked before the body is parsed) |
| 413 | `payload_too_large` | body over 64 KiB |
| 422 | `invalid_request` | schema violation (wrong types, too many values, unknown fields) |
| 422 | `limit_exceeded` | engine limits that depend on the data: decimal places in exact mode, holdout ≥ number of values |
| 429 | `quota_exceeded` | monthly plan quota used ; see `X-Quota-Remaining` |
| 429 | `rate_limited` | over your plan's per-minute limit |
| 503 | `server_busy` | the service is busy; retry after `Retry-After` seconds |
| 504 | `timeout` | over the per-request time limit |

Every response carries `X-Request-ID` (you may supply your own, alphanumeric, ≤ 64 chars).

## Example

```bash
curl -s https://getkrama.vercel.app/api/v1/discover \
  -H "X-API-Key: $PIM_API_KEY" -H "Content-Type: application/json" \
  -d '{"values": [3, 7, 15, 31, 63, 127, 255]}'
```
