---
license: cc-by-4.0
pretty_name: Krama BreakBench
language:
- en
task_categories:
- tabular-classification
tags:
- data-quality
- hallucination
- reasoning
- number-sequences
- anomaly-detection
- benchmark
size_categories:
- 1K<n<10K
configs:
- config_name: default
  data_files:
  - split: practice
    path: practice.jsonl
  - split: test
    path: test.jsonl
---

# Krama BreakBench

**Do AI models see patterns that aren't there?**

Each item is a short sequence of whole numbers. A system has to answer two questions:

1. **Does it follow a rule?** (`follows_rule`, `rule_with_breaks` or `no_rule`)
2. **If so, which positions break it?** (0-based indices)

It sounds easy. In practice, language models often *invent* order in random numbers
([Ishikawa et al., EMNLP 2025](https://preview.aclanthology.org/new-sigs/2025.findings-emnlp.681/)),
and simple spreadsheet checks miss anything that isn't a constant step. BreakBench measures both.

👉 **Try it and play "spot the error":** [huggingface.co/spaces/Rudraneel93/krama](https://huggingface.co/spaces/Rudraneel93/krama)

## The six categories (balanced)

| Category | What it is | Right answer |
|---|---|---|
| `clean` | follows a rule exactly | `follows_rule`, no breaks |
| `value` | 1–2 values are wrong; the sequence carries on as if they were right | `rule_with_breaks`, those positions |
| `gap` | one value is missing; the sequence carries on from the next one | `rule_with_breaks`, the position where it jumps |
| `duplicate` | one value is repeated | `rule_with_breaks`, the repeated position |
| `noise` | random numbers, **no rule** | `no_rule` |
| `beyond` | a real rule *outside* the common families (primes, factorial growth, Catalan numbers, squares of primes) | `follows_rule`, no breaks |

Rules in the first four categories come from six families: constant steps, constant ratios,
quadratics, Fibonacci-like sums, multiply-and-add, and repeating cycles. Gaps and duplicates are
planted only in first-order rules (steps, ratios, multiply-and-add), where the break position is
unambiguous. Noise items are screened *without* using any contestant (no common pattern fits half
of the sequence).

## Splits

| Split | Items | Answers |
|---|---|---|
| `practice` | 360 (60 per category) | included: `status`, `breaks`, `category`, `family` |
| `test` | 1,200 (200 per category) | **withheld**, so models can't be trained on them; scored for the leaderboard |

```python
from datasets import load_dataset
ds = load_dataset("Rudraneel93/krama-breakbench")
ds["practice"][0]   # {'id': 'practice-0000', 'values': [...], 'status': ..., 'breaks': [...], ...}
```

## Metrics

| Metric | Meaning | Better |
|---|---|---|
| **Exact accuracy** | status *and* break positions exactly right | higher |
| **Phantom-pattern rate** | share of pure-noise items where the system claims a rule | **lower** |
| **Break F1** | precision/recall of the reported break positions | higher |
| **Clean false-alarm rate** | share of correct sequences reported as broken | lower |

## Leaderboard (test split)

| System | Exact accuracy | Phantom patterns ↓ | Break F1 | False alarms ↓ | `beyond` |
|---|---:|---:|---:|---:|---:|
| **Krama (PIM engine)** | **83.3%** | **0%** | **0.999** | **0%** | 0% |
| Always says "follows a rule" | 33.3% | 100% | 0.00 | 0% | 100% |
| Constant-step check (spreadsheet-style) | 21.3% | 0% | 0.14 | 86% | 0% |
| *Your model?* | | | | | |

**Read this fairly.** Krama is built for exactly the six rule families above, so it is strong on
them and scores **0% on `beyond`**: it answers "no rule" for primes or Catalan numbers rather than
guess. A model that knows those sequences can beat it there. The headline question is the
phantom-pattern rate: how often does a system invent a rule in random numbers?

## Submit a result

1. Run your system on `test` and write one JSON line per item:
   `{"id": "test-0000", "status": "rule_with_breaks", "breaks": [7]}`
2. Check the format and your practice score: `python score.py --answers practice.jsonl --predictions my_practice.jsonl`
3. Open a **Discussion** on this dataset with your test predictions attached (or email
   rudraneel93@gmail.com). We score it against the hidden answers and add it to the leaderboard.

Please describe the system (model, prompt, tools) so results are comparable.

## Citation

```bibtex
@misc{krama_breakbench_2026,
  title  = {Krama BreakBench: do AI models see patterns that aren't there?},
  author = {Das, Rudraneel},
  year   = {2026},
  url    = {https://huggingface.co/datasets/Rudraneel93/krama-breakbench}
}
```

Made by [Krama](https://getkrama.vercel.app), which finds the rule your numbers follow and every row that
breaks it. Client and integrations: [github.com/rudraneel93/Krama](https://github.com/rudraneel93/Krama).
