# R4.1: XGBoost Adoption — Full Pipeline Regeneration

**Decision**: XGBoost (hybrid_xgb) adopted as primary stacker, replacing hybrid_lr.

> XGB beats LR by +0.16 (D1), +0.16 (D2), +0.02 (D3) under nested threshold with Holm-corrected p ~ 0 on all three (F2 evidence, 10 seeds). XGB raw ECE 0.003/0.006/0.001 vs LR 0.261/0.325/0.040. Adopted.

---

## Baseline F1 (oracle threshold, seed=42)

| detector   |     D1 |     D2 |     D3 |
|:-----------|-------:|-------:|-------:|
| hybrid     | 0.3685 | 0.3664 | 0.6976 |
| hybrid_lr  | 0.5115 | 0.359  | 0.7172 |
| hybrid_xgb | 0.6012 | 0.5717 | 0.7605 |
| iforest    | 0.4272 | 0.3613 | 0.6138 |
| lof        | 0.1463 | 0.104  | 0.0998 |
| rule       | 0.4697 | 0.3412 | 0.7003 |
| stat       | 0.1581 | 0.1336 | 0.1848 |

## Baseline AUC-PR (seed=42)

| detector   |     D1 |     D2 |     D3 |
|:-----------|-------:|-------:|-------:|
| hybrid     | 0.1845 | 0.2199 | 0.6819 |
| hybrid_lr  | 0.4642 | 0.2105 | 0.8164 |
| hybrid_xgb | 0.5402 | 0.5228 | 0.8736 |
| iforest    | 0.2459 | 0.2144 | 0.5559 |
| lof        | 0.0833 | 0.052  | 0.0627 |
| rule       | 0.2589 | 0.1534 | 0.7587 |
| stat       | 0.0768 | 0.0676 | 0.0981 |

## tau* (best-F1 threshold) per dataset

| detector   |     D1 |     D2 |     D3 |
|:-----------|-------:|-------:|-------:|
| hybrid     | 0.3283 | 0.5266 | 0.3436 |
| hybrid_lr  | 0.9216 | 0.671  | 0.9539 |
| hybrid_xgb | 0.8891 | 0.8534 | 0.8867 |
| iforest    | 0.593  | 0.4537 | 0.4245 |
| lof        | 0      | 0      | 0.0508 |
| rule       | 0.6    | 0.6    | 0.6    |
| stat       | 0.0879 | 0.254  | 0.1275 |

## CV (5-fold, nested threshold, seed=42)

| dataset   | detector   |   f1_mean |   f1_std |
|:----------|:-----------|----------:|---------:|
| D1        | hybrid_xgb |    0.5987 |   0.0077 |
| D2        | hybrid_xgb |    0.5704 |   0.005  |
| D3        | hybrid_xgb |    0.7506 |   0.0213 |

## Leave-one-detector-out ablation (hybrid_xgb)

| dataset   | leave_out   |     f1 |   auc_pr |
|:----------|:------------|-------:|---------:|
| D1        | none        | 0.6012 |   0.5402 |
| D1        | rule        | 0.5961 |   0.5417 |
| D1        | stat        | 0.5602 |   0.49   |
| D1        | iforest     | 0.556  |   0.5003 |
| D1        | lof         | 0.5818 |   0.5205 |
| D2        | none        | 0.5717 |   0.5228 |
| D2        | rule        | 0.5102 |   0.4762 |
| D2        | stat        | 0.454  |   0.4224 |
| D2        | iforest     | 0.5067 |   0.4065 |
| D2        | lof         | 0.5724 |   0.5188 |
| D3        | none        | 0.7605 |   0.8736 |
| D3        | rule        | 0.7179 |   0.7329 |
| D3        | stat        | 0.7413 |   0.8451 |
| D3        | iforest     | 0.7494 |   0.8599 |
| D3        | lof         | 0.7273 |   0.8554 |

## Threshold sweep — tau* per dataset (hybrid_xgb)

| dataset   |   threshold |     f1 |   precision |   recall |   review_workload_pct |
|:----------|------------:|-------:|------------:|---------:|----------------------:|
| D1        |      0.8644 | 0.5965 |      0.5884 |   0.6049 |                  5.09 |
| D2        |      0.797  | 0.5629 |      0.5556 |   0.5705 |                  5.08 |
| D3        |      0.8418 | 0.7543 |      0.6417 |   0.9147 |                  7.13 |

## Scalability (D2, hybrid_xgb)

| dataset   | detector   |   n_rows |   elapsed_sec |   rows_per_sec |     f1 |   precision |   recall |
|:----------|:-----------|---------:|--------------:|---------------:|-------:|------------:|---------:|
| D2        | hybrid_xgb |    10000 |         0.683 |          14644 | 0.5431 |      0.5767 |   0.5132 |
| D2        | hybrid_xgb |    50000 |         1.413 |          35397 | 0.5641 |      0.587  |   0.543  |
| D2        | hybrid_xgb |   100000 |         2.369 |          42208 | 0.5752 |      0.6298 |   0.5293 |
| D2        | hybrid_xgb |   200000 |         4.341 |          46072 | 0.5716 |      0.6116 |   0.5364 |

## Multi-seed mean F1 (nested threshold, seeds 42-51)

| dataset   |   hybrid_fixed |   hybrid_lr |   hybrid_xgb |
|:----------|---------------:|------------:|-------------:|
| D1        |         0.3453 |      0.4501 |       0.6076 |
| D2        |         0.3402 |      0.372  |       0.5295 |
| D3        |         0.5013 |      0.7766 |       0.801  |

## Significance (XGB vs LR and XGB vs hybrid_fixed)

| dataset   | comparison                 |   mean_xgb |   mean_baseline |   mean_delta |   t_p |   wilcoxon_p |   n_seeds |   holm_p |
|:----------|:---------------------------|-----------:|----------------:|-------------:|------:|-------------:|----------:|---------:|
| D1        | hybrid_xgb vs hybrid_lr    |     0.6076 |          0.4501 |       0.1575 |     0 |        0.002 |        10 |        0 |
| D1        | hybrid_xgb vs hybrid_fixed |     0.6076 |          0.3453 |       0.2623 |     0 |        0.002 |        10 |        0 |
| D2        | hybrid_xgb vs hybrid_lr    |     0.5295 |          0.372  |       0.1575 |     0 |        0.002 |        10 |        0 |
| D2        | hybrid_xgb vs hybrid_fixed |     0.5295 |          0.3402 |       0.1893 |     0 |        0.002 |        10 |        0 |
| D3        | hybrid_xgb vs hybrid_lr    |     0.801  |          0.7766 |       0.0244 |     0 |        0.002 |        10 |        0 |
| D3        | hybrid_xgb vs hybrid_fixed |     0.801  |          0.5013 |       0.2997 |     0 |        0.002 |        10 |        0 |


---
Generated in 157.7s
