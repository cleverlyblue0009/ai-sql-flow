# Final Experiment Report — DataFlow AI Phase-2 Polish Pass

This document records the experiments that already underpin the IEEE Access
submission, plus the small set of post-hoc analyses added in this polish pass.
**No new ML training was performed**; the additions are derived from existing
on-disk artefacts to avoid fabrication.

## 1. Pre-existing experiments (Phase 2 + Phase 3)

| Experiment            | Script                                      | Output                                       |
|-----------------------|---------------------------------------------|----------------------------------------------|
| Dataset extraction    | `01_extract_and_sample.py`                  | `data/processed/D{1,2,3}_*.parquet`          |
| Anomaly injection     | `02_inject_anomalies.py`                    | `data/processed/D{1,2,3}_injected.parquet`   |
| Per-detector baseline | `10_run_anomaly_experiments.py`             | `results/tables/baseline.csv`                |
| Stacker (5-fold OOF)  | `10_run_anomaly_experiments.py`             | `results/scores/D{1,2,3}_scores.parquet`     |
| Per-family recall     | `10_run_anomaly_experiments.py`             | `results/tables/per_family.csv`              |
| Cross-validation      | `10_run_anomaly_experiments.py`             | `results/tables/cv.csv`                      |
| Ablation              | `10_run_anomaly_experiments.py`             | `results/tables/ablation.csv`                |
| Threshold sweep       | `10_run_anomaly_experiments.py`             | `results/tables/threshold_sweep.csv`         |
| Scalability           | `10_run_anomaly_experiments.py`             | `results/tables/scalability.csv`             |
| SQL transpilation     | `30_run_sql_migration.py`                   | `results/tables/sql_migration_*.csv`         |

## 2. Polish-pass additions

| Addition                       | Script                          | Output                                                            |
|--------------------------------|---------------------------------|-------------------------------------------------------------------|
| Failure-mode classification    | `23_failure_confidence_case.py` | `results/tables/failure_analysis.csv`, `fig9_failure_analysis.*`  |
| Confidence-score distribution  | `23_failure_confidence_case.py` | `fig10_confidence_dist.*`                                          |
| Enterprise case study          | `23_failure_confidence_case.py` | `results/tables/case_study_record.csv`, `fig11_case_study.*`      |
| Standalone architecture figure | `22_generate_architecture.py`   | `fig1_architecture.*` (Panel A + Panel B)                          |

## 3. Headline numbers

| Metric                                         | Value                          |
|------------------------------------------------|--------------------------------|
| Stacker F1 (D1 / D2 / D3)                      | 0.511 / 0.359 / 0.717          |
| Stacker AUC-PR (D1 / D2 / D3)                  | 0.464 / 0.210 / 0.816          |
| Best base detector vs stacker delta (D1 / D3)  | +0.043 / +0.017                |
| D2 throughput @ 200 k rows                     | 17.32 s (≈ 87 μs/row, linear)  |
| SQL parse / transpile / AST-equiv (575 pairs)  | 0.991 / 0.991 / 0.800          |
| SQL AST-equiv on easy / medium / hard          | 0.921 / 0.738 / 0.742          |
| Dominant SQL failure cause                     | Decorator drift (62 / 115)     |

## 4. What was *not* added (intentionally)

The brief listed 14 candidate figures. Several were skipped because the project
does not implement them and fabricating them would violate the brief's own
no-fabrication rule:

- *Semantic Account Mapping Pipeline* — DataFlow AI is not an
  account-mapping system; there is no such stage to draw.
- *Multiple disjoint case studies* — one grounded study is reported instead;
  inventing additional scenarios would be synthetic narrative.
- *Security / adversarial validation figure* — no adversarial robustness
  experiments have been run.

## 5. Reproducibility

```powershell
.\venv\Scripts\Activate.ps1
python phase2_rebuild\scripts\10_run_anomaly_experiments.py
python phase2_rebuild\scripts\30_run_sql_migration.py
python phase2_rebuild\scripts\21_generate_large_figures.py
python phase2_rebuild\scripts\22_generate_architecture.py
python phase2_rebuild\scripts\23_failure_confidence_case.py
python phase2_rebuild\scripts\40_audit_paper.py
```

All scripts read from `phase2_rebuild/results/...` and write under
`phase2_rebuild/results/...` and `paper/images/...`. Seed = 42 throughout.
