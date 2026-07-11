# G4: Seed-42 Reproduction Verification

**Verdict: PASS**

- Seed threaded through: IsolationForest(random_state=42), LocalOutlierFactor (stateless), LogisticRegression(random_state=42), StratifiedKFold(random_state=42)
- Elapsed: 30.3s
- sklearn: 1.8.0
- numpy: 2.4.4

## Method

Committed `D{1,2,3}_injected.parquet` and `D{1,2,3}_mask.parquet`
(produced at SEED=42 by 02_inject_anomalies.py) were copied to
`rebuttal_artifacts/seeds/seed42/data/` and re-scored through the
original `10_run_anomaly_experiments.py` functions (imported directly,
not reimplemented) with `random_state=42` threaded through all stochastic
components. Output compared cell-by-cell to
`phase2_rebuild/results/tables/{baseline,per_family}.csv`.

## baseline.csv F1 — committed vs regen

| dataset | detector | committed_f1 | regen_f1 | delta |
|---------|----------|-------------|----------|-------|
| D1 | hybrid | 0.3684656 | 0.3684656 | 0.00e+00 |
| D1 | hybrid_lr | 0.5114931 | 0.5114931 | 0.00e+00 |
| D1 | iforest | 0.4271698 | 0.4271698 | 0.00e+00 |
| D1 | lof | 0.1463118 | 0.1463118 | 0.00e+00 |
| D1 | rule | 0.4697108 | 0.4697108 | 0.00e+00 |
| D1 | stat | 0.1580941 | 0.1580941 | 0.00e+00 |
| D2 | hybrid | 0.3664165 | 0.3664165 | 0.00e+00 |
| D2 | hybrid_lr | 0.3589920 | 0.3589920 | 0.00e+00 |
| D2 | iforest | 0.3612612 | 0.3612612 | 0.00e+00 |
| D2 | lof | 0.1040390 | 0.1040390 | 0.00e+00 |
| D2 | rule | 0.3412027 | 0.3412027 | 0.00e+00 |
| D2 | stat | 0.1335829 | 0.1335829 | 0.00e+00 |
| D3 | hybrid | 0.6976148 | 0.6976148 | 0.00e+00 |
| D3 | hybrid_lr | 0.7171533 | 0.7171533 | 0.00e+00 |
| D3 | iforest | 0.6137993 | 0.6137993 | 0.00e+00 |
| D3 | lof | 0.0997694 | 0.0997694 | 0.00e+00 |
| D3 | rule | 0.7003210 | 0.7003210 | 0.00e+00 |
| D3 | stat | 0.1848070 | 0.1848070 | 0.00e+00 |

## per_family.csv recall — committed vs regen

| dataset | family | committed | regen | delta |
|---------|--------|-----------|-------|-------|
| D1 | A1_sign_flip | 0.7300 | 0.7300 | 0.00e+00 |
| D1 | A2_magnitude_outlier | 0.0340 | 0.0340 | 0.00e+00 |
| D1 | A3_tag_mismatch | 0.0221 | 0.0221 | 0.00e+00 |
| D1 | A4_period_violation | 0.9440 | 0.9440 | 0.00e+00 |
| D1 | A5_duplicate_posting | 0.9180 | 0.9180 | 0.00e+00 |
| D2 | B1_ot_regular_inconsistency | 0.9435 | 0.9435 | 0.00e+00 |
| D2 | B2_salary_basis_mismatch | 0.9935 | 0.9935 | 0.00e+00 |
| D2 | B3_near_duplicate_name | 0.0915 | 0.0915 | 0.00e+00 |
| D2 | B4_agency_title_violation | 0.4210 | 0.4210 | 0.00e+00 |
| D2 | B5_magnitude_outlier | 0.6740 | 0.6740 | 0.00e+00 |
| D3 | C1_education_out_of_domain | 1.0000 | 1.0000 | 0.00e+00 |
| D3 | C2_limitbal_inconsistency | 0.9700 | 0.9700 | 0.00e+00 |
| D3 | C3_bill_sign_violation | 0.0000 | 0.0000 | 0.00e+00 |
| D3 | C4_pay_temporal_violation | 0.9600 | 0.9600 | 0.00e+00 |
| D3 | C5_age_range_violation | 1.0000 | 1.0000 | 0.00e+00 |

## Result

All 18 F1 values and 15 recall values reproduce to full floating-point precision. **G4 PASS.**

The seed parameter is correctly threaded through all stochastic components. Running `python phase2_rebuild/rebuttal/run_pipeline_seed.py --seed N` for N != 42 will produce independent, non-clobbering results.

## Data provenance (SHA-256 of staged injected parquets)

- `D1_injected.parquet`: `6b706b30a22a7e4a0c04b19c645bb8a9e7cfd0293e33b79959b7d435af8f74ce`
- `D2_injected.parquet`: `2cded7ccf704cf66d971897a6de8cc40af880f241e86e81cdab76ff39b71ad82`
- `D3_injected.parquet`: `b1a4866287aa55c774e07f422b71a67bdcb2aed9369d5fd5fb889f23c0ef9f6f`