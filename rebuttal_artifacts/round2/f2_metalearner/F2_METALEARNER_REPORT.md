# F2: Meta-Learner Comparison — Multi-Seed, Nested Threshold

**Manuscript**: DataFlow AI — IEEE Access Access-2026-28181

---

## VERDICT

**MAJOR REVISION TRIGGER**

A GBDT meta-learner beats LR under the nested threshold (significance held after Holm correction). The paper's claim that logistic-regression stacking is the central methodological move is WRONG. The full pipeline must be re-run with the winning meta-learner before resubmission.

- GBM beats LR by +0.1363 on D1 (Holm-corrected p=0.0000)
- XGB beats LR by +0.1612 on D1 (Holm-corrected p=0.0000)
- LGB beats LR by +0.1627 on D1 (Holm-corrected p=0.0000)
- GBM beats LR by +0.1410 on D2 (Holm-corrected p=0.0000)
- XGB beats LR by +0.1626 on D2 (Holm-corrected p=0.0000)
- LGB beats LR by +0.1795 on D2 (Holm-corrected p=0.0000)
**Decision line** (for ROUND2_SUMMARY.md): Best GBDT is LGB on D2: nested delta = +0.1795, Holm p = 0.0000. MAJOR REVISION TRIGGER

---

## Provenance note

Seeds 42–48 (all datasets) and seed 49 D1 (132 rows) were recovered from stdout of an interrupted run. F1 values are exact as computed; calibration metrics (ECE, Brier) are NaN for those rows. Seeds 49 D2/D3 and 50–51 (48 rows) were freshly computed by this continuation script. The significance test uses only f1_nested and f1_oracle, both of which are fully available for all 10 seeds.

---

## Fix applied vs Round-1 E3

1. **Oracle threshold bias** fixed: nested threshold selected on training folds only.
2. **Single seed** fixed: 10 seeds (42–51) with per-seed base detector scores.
3. **Missing models** fixed: XGBoost and LightGBM now included.

## Protocol

- Seeds: [42, 43, 44, 45, 46, 47, 48, 49, 50, 51]
- Base detector features: ['rule', 'stat', 'iforest', 'lof']
- OOF folds: 5-fold StratifiedKFold
- Meta-learners: LR, RF, GBM, XGB, LGB, MLP
- Significance: paired t-test + Wilcoxon + Holm correction, per dataset

## Mean F1 — nested threshold (10-seed mean)

| meta_learner   |     D1 |     D2 |     D3 |
|:---------------|-------:|-------:|-------:|
| GBM            | 0.5888 | 0.5129 | 0.7933 |
| LGB            | 0.6152 | 0.5513 | 0.7871 |
| LR             | 0.4525 | 0.3718 | 0.7782 |
| MLP            | 0.5455 | 0.4642 | 0.7863 |
| RF             | 0.5142 | 0.462  | 0.7901 |
| XGB            | 0.6137 | 0.5345 | 0.7995 |

## Oracle vs nested F1 gap (oracle − nested, 10-seed mean)

| meta_learner   |      D1 |      D2 |     D3 |
|:---------------|--------:|--------:|-------:|
| GBM            |  0.002  | -0.0011 | 0.0066 |
| LGB            |  0.0041 |  0.0006 | 0.0148 |
| LR             | -0.0001 |  0.0005 | 0.0039 |
| MLP            | -0.0153 | -0.0104 | 0.0021 |
| RF             |  0.0081 |  0.0347 | 0.0083 |
| XGB            |  0.0022 |  0.0002 | 0.0054 |

## Significance vs LR (nested threshold)

| dataset   | meta_learner   |   mean_oracle_delta |   mean_nested_delta |   t_p_oracle |   wilcoxon_p_oracle |   t_p_nested |   wilcoxon_p_nested |   n_seeds |   holm_p_nested |
|:----------|:---------------|--------------------:|--------------------:|-------------:|--------------------:|-------------:|--------------------:|----------:|----------------:|
| D1        | RF             |              0.07   |              0.0617 |       0      |               0.002 |       0      |              0.002  |        10 |          0      |
| D1        | GBM            |              0.1384 |              0.1363 |       0      |               0.002 |       0      |              0.002  |        10 |          0      |
| D1        | MLP            |              0.0778 |              0.093  |       0.0001 |               0.002 |       0      |              0.002  |        10 |          0      |
| D1        | XGB            |              0.1635 |              0.1612 |       0      |               0.002 |       0      |              0.002  |        10 |          0      |
| D1        | LGB            |              0.167  |              0.1627 |       0      |               0.002 |       0      |              0.002  |        10 |          0      |
| D2        | RF             |              0.1244 |              0.0902 |       0      |               0.002 |       0      |              0.002  |        10 |          0      |
| D2        | GBM            |              0.1394 |              0.141  |       0      |               0.002 |       0      |              0.002  |        10 |          0      |
| D2        | MLP            |              0.0815 |              0.0924 |       0      |               0.002 |       0      |              0.002  |        10 |          0      |
| D2        | XGB            |              0.1623 |              0.1626 |       0      |               0.002 |       0      |              0.002  |        10 |          0      |
| D2        | LGB            |              0.1796 |              0.1795 |       0      |               0.002 |       0      |              0.002  |        10 |          0      |
| D3        | RF             |              0.0163 |              0.0119 |       0.0008 |               0.002 |       0.0126 |              0.0352 |        10 |          0.0252 |
| D3        | GBM            |              0.0179 |              0.0152 |       0.0001 |               0.002 |       0.0079 |              0.0254 |        10 |          0.0316 |
| D3        | MLP            |              0.0064 |              0.0082 |       0.0004 |               0.002 |       0.0083 |              0.0156 |        10 |          0.0249 |
| D3        | XGB            |              0.0229 |              0.0214 |       0      |               0.002 |       0.0004 |              0.002  |        10 |          0.002  |
| D3        | LGB            |              0.0199 |              0.0089 |       0.0003 |               0.002 |       0.1007 |              0.1055 |        10 |          0.1007 |

## Calibration (10-seed mean ECE and Brier)

Note: calibration is NaN for recovered seeds 42–48.

| meta_learner   | dataset   |   mean_ece_raw |   mean_brier_raw |   mean_ece_platt |   mean_brier_platt |
|:---------------|:----------|---------------:|-----------------:|-----------------:|-------------------:|
| GBM            | D1        |        0.0034  |          0.02871 |          0.0039  |            0.02935 |
| GBM            | D2        |        0.00511 |          0.0342  |          0.00339 |            0.03406 |
| GBM            | D3        |        0.00183 |          0.01212 |          0.00707 |            0.01356 |
| LGB            | D1        |        0.16746 |          0.07408 |          0.01002 |            0.02868 |
| LGB            | D2        |        0.25983 |          0.11415 |          0.0113  |            0.03346 |
| LGB            | D3        |        0.026   |          0.02487 |          0.01481 |            0.01608 |
| LR             | D1        |        0.26064 |          0.12676 |          0.00816 |            0.03876 |
| LR             | D2        |        0.32531 |          0.164   |          0.01151 |            0.04174 |
| LR             | D3        |        0.03962 |          0.03519 |          0.01736 |            0.01811 |
| MLP            | D1        |        0.00645 |          0.03233 |          0.00983 |            0.03348 |
| MLP            | D2        |        0.0035  |          0.0365  |          0.00673 |            0.03698 |
| MLP            | D3        |        0.00729 |          0.01372 |          0.00344 |            0.01463 |
| RF             | D1        |        0.03724 |          0.03928 |          0.00529 |            0.03268 |
| RF             | D2        |        0.07434 |          0.05361 |          0.01262 |            0.03563 |
| RF             | D3        |        0.00615 |          0.01288 |          0.00386 |            0.01436 |
| XGB            | D1        |        0.00302 |          0.02688 |          0.00406 |            0.0275  |
| XGB            | D2        |        0.00554 |          0.03276 |          0.0031  |            0.03261 |
| XGB            | D3        |        0.00122 |          0.01188 |          0.00597 |            0.01321 |

---

Continuation run: 776.5s for 48 newly computed rows. Total rows: 180.
Outputs: rebuttal_artifacts/round2/f2_metalearner/
