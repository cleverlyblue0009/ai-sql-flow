# R4.2: Downstream Experiments — hybrid_xgb

## A. Calibration

Key question: is Platt scaling still needed for hybrid_xgb?

| dataset   | detector   |   ece_raw |   brier_raw |   ece_platt |   brier_platt | platt_necessary   |
|:----------|:-----------|----------:|------------:|------------:|--------------:|:------------------|
| D1        | hybrid_xgb |   0.37393 |     0.0858  |     0.07182 |       0.03002 | True              |
| D1        | hybrid_lr  |   0.38248 |     0.11159 |     0.11339 |       0.03305 | True              |
| D2        | hybrid_xgb |   0.37154 |     0.11324 |     0.11749 |       0.03241 | True              |
| D2        | hybrid_lr  |   0.42853 |     0.16267 |     0.05201 |       0.0426  | True              |
| D3        | hybrid_xgb |   0.2962  |     0.02894 |     0.12496 |       0.0189  | True              |
| D3        | hybrid_lr  |   0.39499 |     0.03726 |     0.18829 |       0.02261 | True              |

Mean raw ECE: hybrid_xgb=0.34722  hybrid_lr=0.40200. Platt scaling still beneficial.

## B. Joint gate with hybrid_xgb

### Analyst cost comparison: hybrid_xgb vs hybrid_lr

| dataset   | detector                  |    tau |   n_quarantined |   n_tp |   n_fp |   n_fn |   fp_fraction |
|:----------|:--------------------------|-------:|----------------:|-------:|-------:|-------:|--------------:|
| D2        | hybrid_xgb                | 0.8534 |            8825 |   5380 |   3445 |   4620 |        0.3904 |
| D2        | hybrid_lr (F1b reference) | 0.671  |           24803 |    nan |  18556 |    nan |        0.7481 |
| D3        | hybrid_xgb                | 0.8867 |            1937 |   1307 |    630 |    193 |        0.3252 |
| D3        | hybrid_lr (F1b reference) | 0.9539 |            1788 |    nan |    609 |    nan |        0.3406 |

### Relative-error magnitude (median) by condition

| condition        | stratum   |   n |   median |      p90 |      max |
|:-----------------|:----------|----:|---------:|---------:|---------:|
| dirty_src        | all       |  35 | 0.010477 | 1        | 2.47e+11 |
| clean_xgb_src    | all       |  35 | 0.061433 | 1        | 1        |
| repaired_xgb_src | all       |  35 | 0.002157 | 0.740909 | 1        |

## C. Modern baselines vs hybrid_xgb

| detector            |     D1 |     D2 |     D3 |
|:--------------------|-------:|-------:|-------:|
| COPOD               | 0.3718 | 0.2414 | 0.4914 |
| DataFlow_hybrid_xgb | 0.6012 | 0.5717 | 0.7605 |
| ECOD                | 0.4165 | 0.2432 | 0.5956 |
| HBOS                | 0.4428 | 0.2937 | 0.4906 |
| KNN                 | 0.5236 | 0.3333 | 0.391  |
| LODA                | 0.249  | 0.3805 | 0.394  |

### Verdicts per dataset

- **D1**: DataFlow_hybrid_xgb F1=0.6012. Better: none. Worse: ['KNN', 'HBOS', 'ECOD', 'COPOD', 'LODA'].
- **D2**: DataFlow_hybrid_xgb F1=0.5717. Better: none. Worse: ['LODA', 'KNN', 'HBOS', 'ECOD', 'COPOD'].
- **D3**: DataFlow_hybrid_xgb F1=0.7605. Better: none. Worse: ['ECOD', 'COPOD', 'HBOS', 'LODA', 'KNN'].

## D. Extended stacker (XGB)

| dataset   | base_set   |       f1 |   auc_pr | detectors                            |
|:----------|:-----------|---------:|---------:|:-------------------------------------|
| D1        | Base4      |   0.6012 |   0.5402 | rule,stat,iforest,lof                |
| D1        | Base4+ECOD |   0.6281 |   0.632  | rule,stat,iforest,lof,ecod           |
| D1        | Base6      | nan      | nan      | rule,stat,iforest,lof,ecod,deep_svdd |
| D2        | Base4      |   0.5717 |   0.5228 | rule,stat,iforest,lof                |
| D2        | Base4+ECOD |   0.5999 |   0.5705 | rule,stat,iforest,lof,ecod           |
| D2        | Base6      | nan      | nan      | rule,stat,iforest,lof,ecod,deep_svdd |
| D3        | Base4      |   0.7605 |   0.8736 | rule,stat,iforest,lof                |
| D3        | Base4+ECOD |   0.8123 |   0.9198 | rule,stat,iforest,lof,ecod           |
| D3        | Base6      | nan      | nan      | rule,stat,iforest,lof,ecod,deep_svdd |

### XGB feature importances

| feature   |     D1 |     D2 |     D3 |
|:----------|-------:|-------:|-------:|
| iforest   | 0.3283 | 0.5694 | 0.0092 |
| lof       | 0.0684 | 0.0394 | 0.01   |
| rule      | 0.5131 | 0.27   | 0.9725 |
| stat      | 0.0901 | 0.1212 | 0.0084 |


---
Generated in 83.1s
