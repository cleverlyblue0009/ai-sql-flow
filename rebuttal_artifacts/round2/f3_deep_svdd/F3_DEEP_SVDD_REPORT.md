# F3: Deep SVDD + Extended Stacker Ablation

**Manuscript**: DataFlow AI — IEEE Access Access-2026-28181

Addresses Reviewer 2 R2.3 (deep anomaly detectors).

---

## Q1: Standalone F1 — all detectors

| dataset   | detector   |   f1_oracle |   contamination | note           |
|:----------|:-----------|------------:|----------------:|:---------------|
| D1        | rule       |      0.4697 |          0.0495 | paper_baseline |
| D1        | stat       |      0.1581 |          0.0495 | paper_baseline |
| D1        | iforest    |      0.4272 |          0.0495 | paper_baseline |
| D1        | lof        |      0.1463 |          0.0495 | paper_baseline |
| D1        | hybrid     |      0.3685 |          0.0495 | paper_baseline |
| D1        | hybrid_lr  |      0.5115 |          0.0495 | paper_baseline |
| D1        | ecod       |      0.4165 |          0.0495 | ok             |
| D1        | deep_svdd  |      0.432  |          0.0495 | ok             |
| D2        | rule       |      0.3412 |          0.0495 | paper_baseline |
| D2        | stat       |      0.1336 |          0.0495 | paper_baseline |
| D2        | iforest    |      0.3613 |          0.0495 | paper_baseline |
| D2        | lof        |      0.104  |          0.0495 | paper_baseline |
| D2        | hybrid     |      0.3664 |          0.0495 | paper_baseline |
| D2        | hybrid_lr  |      0.359  |          0.0495 | paper_baseline |
| D2        | ecod       |      0.2432 |          0.0495 | ok             |
| D2        | deep_svdd  |      0.3914 |          0.0495 | ok             |
| D3        | rule       |      0.7003 |          0.05   | paper_baseline |
| D3        | stat       |      0.1848 |          0.05   | paper_baseline |
| D3        | iforest    |      0.6138 |          0.05   | paper_baseline |
| D3        | lof        |      0.0998 |          0.05   | paper_baseline |
| D3        | hybrid     |      0.6976 |          0.05   | paper_baseline |
| D3        | hybrid_lr  |      0.7172 |          0.05   | paper_baseline |
| D3        | ecod       |      0.5307 |          0.05   | ok             |
| D3        | deep_svdd  |      0.7392 |          0.05   | ok             |

## Q2: Stacker ablation — does adding ECOD + Deep SVDD help?

| dataset   | config     | detectors                            |   f1_oracle | note           |
|:----------|:-----------|:-------------------------------------|------------:|:---------------|
| D1        | Base4      | rule,stat,iforest,lof                |      0.5115 | paper_baseline |
| D1        | Base4+ECOD | rule,stat,iforest,lof,ecod           |      0.5285 | ok             |
| D1        | Base6      | rule,stat,iforest,lof,ecod,deep_svdd |      0.5283 | ok             |
| D2        | Base4      | rule,stat,iforest,lof                |      0.359  | paper_baseline |
| D2        | Base4+ECOD | rule,stat,iforest,lof,ecod           |      0.3664 | ok             |
| D2        | Base6      | rule,stat,iforest,lof,ecod,deep_svdd |      0.4198 | ok             |
| D3        | Base4      | rule,stat,iforest,lof                |      0.7172 | paper_baseline |
| D3        | Base4+ECOD | rule,stat,iforest,lof,ecod           |      0.7143 | ok             |
| D3        | Base6      | rule,stat,iforest,lof,ecod,deep_svdd |      0.7684 | ok             |

**D1**: Base4=0.5115, Base6=0.5283, delta=+0.0168 (improvement)

**D2**: Base4=0.3590, Base6=0.4198, delta=+0.0608 (improvement)

**D3**: Base4=0.7172, Base6=0.7684, delta=+0.0512 (improvement)

## Interpretation

If delta (Base6 - Base4) <= 0.01 on all datasets: the paper's choice of [rule, stat, iforest, lof] as the base detector set is defensible — adding ECOD and Deep SVDD does not materially improve the stacker.

If delta > 0.05 on any dataset: flag for manuscript discussion — the paper should explain why it chose rule/stat/iforest/lof over richer base sets.

**VERDICT: MANUSCRIPT DISCUSSION REQUIRED** — max delta = +0.0608 > 0.05. Add a paragraph explaining the base-detector selection rationale.

---

Generated in 57.4s (seed=42, DeepSVDD max=120s per dataset).
Outputs: rebuttal_artifacts/round2/f3_deep_svdd/
