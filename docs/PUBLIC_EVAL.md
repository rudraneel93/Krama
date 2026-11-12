# Stand-in pilot evaluation on public labelled data

There is no customer data yet. This evaluation uses free public datasets with
known answers to test the claims a pilot would test: precision on answered
cases, coverage, and abstention on data PIM is not built for. PIM is **not
trained** on any of them. The symbolic engine has no training step, and the
neural model is not in the pilot. They are held-out tests only.

The evaluation scripts live in the (private) engine repository; the data sources below are public and the method is described in full, so the results can be reproduced independently.
Search space: `extended` (the API default).

## Data

| suite | source | licence | size | label |
|---|---|---|---|---|
| deepmind_next | DeepMind Mathematics dataset, `algebra__sequence_next_term` test split ([HF](https://huggingface.co/datasets/deepmind/math_dataset), parquet at `refs/pr/7`) | Apache-2.0 | 10,000 | next term |
| deepmind_nth | same, `algebra__sequence_nth_term` | Apache-2.0 | 10,000 | generating formula; we check 3 future terms |
| nist | NIST StRD Wampler1–5 ([itl.nist.gov](https://www.itl.nist.gov/div898/strd/lls/data/LINKS/DATA/)) | public domain | 5 | certified degree-5 polynomial |
| amortization | loan balances rounded to cents, standard annuity formula (generated; principal 5k–1M, 1–19.5% p.a., 5–30 years, 12–60 observed months) | — | 2,000 | next 6 balances |
| m4 | M4 competition yearly, quarterly and monthly series ([Mcompetitions/M4-methods](https://github.com/Mcompetitions/M4-methods)) | research use; not redistributed | 95,000 | the real future values (horizon 6, 8, 18) |

All datasets are linked above.

## Results

### Exact rules from an independent generator (DeepMind)

| suite | answered | correct | precision | p50 latency |
|---|---|---|---|---|
| next term, default holdout | 10,000 / 10,000 | 10,000 | **100%** | 0.9 ms |
| next term, holdout 0 | 10,000 / 10,000 | 10,000 | 100% | 1.2 ms |
| 3 future terms from the formula, default holdout | 10,000 / 10,000 | 10,000 | **100%** | 0.9 ms |
| same, holdout 0 | 10,000 / 10,000 | 10,000 | 100% | 1.3 ms |

These are polynomials of degree ≤ 3 with 3–8 terms, all inside PIM's search
space. It shows the exact engine is correct and complete on in-space data
from a generator we did not write. It says nothing about out-of-space data.

### Certified reference data (NIST)

| dataset | noise (certified residual SD) | PIM's answer | correct? |
|---|---|---|---|
| Wampler1 | 0 | degree-5 polynomial, exact | yes, matches the certified polynomial exactly |
| Wampler2 | 0 | degree-5 polynomial, exact | yes, exactly |
| Wampler3 | 2,360 | linear recurrence of order 5 | no: 33% off at x = 21–25 |
| Wampler4 | 236,015 | linear recurrence of order 2 | no: 104% off |
| Wampler5 | 23,601,450 | geometric | no: 363% off |

Exact data: right. Noisy data: the statistical engine names a rule that
extrapolates badly instead of abstaining.

### Rounded financial schedules (amortization)

Rounding to cents at every step means no exact rule fits.

| engine | answered | within 1 cent (all 6 steps) | within 5 cents |
|---|---|---|---|
| exact | 2 / 2,000 (abstains) | 0 of 2 | 2 of 2 |
| statistical, noise = rounding SD, before the fix below | 2,000 | 23.6% | 50.5% |
| statistical, after the fix | 2,000 | 39.5% | **81.1%** |

### Real business and economic series (M4)

Exact engine, full forecast horizon, every series (last 1,000 values for long monthly series).

| frequency | series | named a rule | false discoveries | rejected by input limits | p50 / max latency |
|---|---|---|---|---|---|
| yearly | 23,000 | 0 | 0 | 11 | 25 ms / 1.2 s |
| quarterly | 24,000 | 0 | 0 | 3 | 85 ms / 0.9 s |
| monthly | 48,000 | 0 | 0 | 2 | 186 ms / 1.1 s |

PIM abstained on all 95,000 real business and economic series. This is the
"not a forecaster" claim, measured: on noisy real data it says nothing rather
than something wrong. It also means zero coverage on this kind of data.

## Engine change made because of this evaluation

The statistical engine ranked candidates by in-sample BIC. On rounded
schedules, a degree-5 polynomial has a wide prediction interval, so the
holdout cannot refute it. It then wins on BIC and bends away from the true
affine recurrence. Candidates are now ranked by **prequential (one-step-ahead)
error**: refit on each prefix of the last 8 fit positions, predict the next
value, and compare. This is Rissanen's accumulated prediction error. Ties
within one noise variance fall back to BIC.

- The tie band (1.0) was chosen on a separate tuning seed. Bands 1.0, 1.25,
  1.5, 2, 4 and 10 gave 82%, 79%, 76%, 71%, 61% and 54%. The reported
  evaluation uses a different seed.
- A multi-step backtest scored higher on amortization (86%) but broke the
  noisy-exponential unit test, because compounding makes it noisy. It was
  rejected.
- Unaffected: the exact engine (OEIS, DeepMind and every exact result) and all
  63 earlier unit tests. A new regression test covers rounded schedules: the
  old ranking got 17/30, the threshold is 21.

## What this means for the pilot

1. **Exact engine: strong.** 100% precision on 20,000 independent in-space
   items. Abstains on rounded data instead of guessing. On 95,000 real M4 series it named no rule at all: zero false discoveries.
2. **Statistical engine: not ready to sell as reliable.** About 81% on rounded
   schedules even after the fix. On heavily noisy data it names rules that
   extrapolate badly (NIST Wampler3–5). It needs calibrated prediction
   intervals on the continuation and an abstention rule for low
   signal-to-noise. Until then, label `noise_level > 0` results experimental
   in the pilot.
3. Coverage on real data will depend on how rule-like the customer's process
   is. On generic business time series (M4) it is 0%. Pilot use cases must be rule-driven processes, not forecasting.
4. None of this replaces customer data. It narrows what a pilot needs to
   check: whether the customer's sequences are in the search space, and how
   noisy they are.
