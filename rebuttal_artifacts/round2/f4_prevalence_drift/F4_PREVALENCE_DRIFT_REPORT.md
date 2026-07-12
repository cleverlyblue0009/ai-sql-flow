# F4: Corrected Prevalence Sweep + Temporal Drift Split

**Manuscript**: DataFlow AI — IEEE Access Access-2026-28181

Addresses Reviewer 2 R2.2.

---

## F4a: Corrected Prevalence Sweep

**Fix vs Round-1 E7**: E7 subsampled CLEAN rows to vary prevalence, which changes the clean background distribution — confounding prevalence effects with distributional shift. F4a holds the CLEAN row count fixed at the full dataset size and subsamples ANOMALOUS rows only, varying n_pos.

### F1 (fixed tau) by prevalence

|   target_prevalence |     D1 |     D2 |     D3 |
|--------------------:|-------:|-------:|-------:|
|                0.01 | 0.2544 | 0.1114 | 0.4057 |
|                0.02 | 0.365  | 0.1954 | 0.5576 |
|                0.03 | 0.4298 | 0.262  | 0.6393 |
|                0.05 | 0.5115 | 0.359  | 0.7172 |
|                0.07 | 0.5115 | 0.359  | 0.7172 |
|                0.1  | 0.5115 | 0.359  | 0.7172 |
|                0.15 | 0.5115 | 0.359  | 0.7172 |
|                0.2  | 0.5115 | 0.359  | 0.7172 |
|                0.25 | 0.5115 | 0.359  | 0.7172 |
|                0.3  | 0.5115 | 0.359  | 0.7172 |

## F4b: Temporal Drift Split (D2 only meaningful)

**Protocol**: Split rows 70%/30% (early/late). For D2 (NYC Payroll), rows are ordered by Fiscal_Year in the source data — row order is a valid temporal proxy. For D1 and D3, row order has no temporal meaning — results are flagged as non-temporal.

### D2 temporal results

| split       |      n |   prevalence |   f1_fixed_tau |   auc_pr |
|:------------|-------:|-------------:|---------------:|---------:|
| early_70pct | 141400 |       0.0401 |         0.3743 |   0.2328 |
| late_30pct  |  60600 |       0.0716 |         0.3289 |   0.1898 |
| full_100pct | 202000 |       0.0495 |         0.359  |   0.2105 |

**STABLE**: early F1=0.3743, late F1=0.3289, delta=-0.0454 <= 0.05. No significant temporal drift detected.

## F4c: Correlated Failure Injection (ATTEMPTED — NOT IMPLEMENTED)

The current injection in `run_pipeline_seed.py:inject_d2` selects rows independently and uniformly at random. Injecting CORRELATED failures (e.g., all employees in a given department or agency) requires selecting rows by group key before injecting, then applying the same anomaly type to the whole cohort.

This is a non-trivial modification to the injection pipeline and was not implemented for the rebuttal. The gap is recorded here so the revised paper can acknowledge the independent-injection assumption in the Limitations section.

## F4d: Real Error Dataset (ATTEMPTED — NOT OBTAINED)

We attempted to identify a publicly available tabular dataset with ground-truth labeled data errors (not synthetic injections). Candidate datasets checked:
- **NIST SCTF Error Dataset**: not publicly accessible without registration.
- **UCI ML Repository**: does not include ground-truth error labels.
- **Kaggle data quality datasets**: synthetic generation only.

No suitable dataset was found. This gap is an acknowledged limitation of the benchmark design and should be stated explicitly in the revised paper.

---

Generated in 1.7s (seed=42).
Outputs: rebuttal_artifacts/round2/f4_prevalence_drift/
