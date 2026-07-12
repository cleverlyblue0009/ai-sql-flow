# Round-2 Rebuttal Environment

**OS**: Windows 11 Home Single Language 10.0.26200  
**Python**: 3.14.3 (venv at `venv/Scripts/python.exe`)  
**Date recorded**: 2026-07-12

## Core libraries

| Package | Version |
|---|---|
| numpy | 2.4.4 |
| scipy | 1.17.1 |
| pandas | 3.0.2 |
| scikit-learn | 1.8.0 |
| xgboost | 3.3.0 (installed 2026-07-12 via Tsinghua mirror) |
| lightgbm | 4.6.0 (installed 2026-07-12 via Tsinghua mirror) |

## Anomaly detection

| Package | Version |
|---|---|
| pyod | (see F3 — installed for Deep SVDD) |

## SQL

| Package | Version |
|---|---|
| sqlglot | (from committed environment) |
| duckdb | (from committed environment) |

## Notes

- xgboost 3.3.0 and lightgbm 4.6.0 were installed for F2 (meta-learner comparison).
  These were NOT available during Round-1 experiments (E3 ran only LR/RF/GBM/MLP).
- Reviewer 2 (R2.1) named XGBoost and LightGBM explicitly; both are now included.
- All random states are set to the per-experiment seed (42–51); no global seed is set.
