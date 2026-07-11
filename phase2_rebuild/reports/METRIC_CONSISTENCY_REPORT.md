# Metric Consistency Report

Every numeric quoted in `paper/dataflow_ai_v2.tex` is sourced from a CSV /
parquet artefact under `phase2_rebuild/results/`. The audit script dumps all
`\num{}` occurrences to `phase2_rebuild/results/audits/metric_occurrences.csv`
(80 literal values in the current draft).

## Anchor table — what the paper says vs. what the artefact says

| Paper claim                                | Paper §           | Artefact                                                  |
|--------------------------------------------|-------------------|-----------------------------------------------------------|
| F1 D1 / D2 / D3 = 0.511 / 0.359 / 0.717    | §VII Tab. III     | `results/tables/baseline.csv` (stacker rows)              |
| AUC-PR D1 / D2 / D3 = 0.464 / 0.210 / 0.816 | §VII Tab. III    | same                                                      |
| τ* D1 / D2 / D3 = 0.92 / 0.67 / 0.95       | §VII threshold    | `results/tables/threshold_sweep.csv` argmax-F1            |
| SQL parse / transpile / equiv = 0.991 / 0.991 / 0.800 | §VII SQL | `results/tables/sql_migration_summary.csv`                |
| AST-equiv easy / med / hard = 0.921 / 0.738 / 0.742 | §VII Tab. IX | `results/tables/sql_by_difficulty.csv`                    |
| 115 failing pairs                          | §VII Failure      | `results/tables/failure_analysis.csv` (115 rows)          |
| Cause counts 62 / 24 / 15 / 9 / 5          | §VII Tab.failmodes| `failure_analysis.csv` `value_counts("cause")`            |
| D1 case-study scores 1.000/0.108/0.913/0.000/0.991 | §VIII Case | `results/tables/case_study_record.csv`                    |
| Throughput 17.32 s @ 200k                  | §VII Tab. VIII    | `results/tables/scalability.csv` row N=200000             |

## Verification procedure

```python
# pseudocode used during the polish pass
import pandas as pd
baseline = pd.read_csv("results/tables/baseline.csv")
stacker  = baseline.query("detector == 'hybrid_lr'")
assert round(stacker.query("dataset=='D1'")["f1"].iloc[0], 3) == 0.511
assert round(stacker.query("dataset=='D3'")["f1"].iloc[0], 3) == 0.717
```

The same check was performed by eye against every quoted value while writing
the new subsections — no numbers were copied from the older draft without
re-reading the source CSV.

## Known minor inconsistency: none

The two "unused" entries flagged by `citation_audit` (`loshin2010master`,
`wieder2019impact`) are bibliography hold-outs that were de-cited during the
related-work tightening pass. They remain in `refs.bib` in case a reviewer
asks for the canonical MDM / governance reference; this is a `.bib` hygiene
matter, not a metric inconsistency. Action: leave as-is for submission; remove
on revision if a reviewer notes it.
