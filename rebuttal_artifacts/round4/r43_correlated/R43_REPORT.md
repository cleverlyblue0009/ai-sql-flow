# R4.3: Correlated Failure Injection
## Research question
Does hybrid_xgb performance degrade under CLUSTERED or CO-OCCURRING injection?
INDEPENDENT = uniform random (baseline). CLUSTERED = one family per cohort. CO-OCCURRING = multiple families per row.

## Summary (hybrid_xgb F1 by dataset × mode)

| mode        |   D2_50k |     D3 |
|:------------|---------:|-------:|
| clustered   |   0.5991 | 0.7207 |
| cooccurring |   0.6095 | 1      |
| independent |   0.6717 | 0.7349 |

## Anomaly counts by mode

| dataset   | mode        |   n_rows |   n_anomalies |
|:----------|:------------|---------:|--------------:|
| D3        | independent |    30000 |          1500 |
| D3        | clustered   |    30000 |          1500 |
| D3        | cooccurring |    30000 |           600 |
| D2_50k    | independent |    50000 |          2500 |
| D2_50k    | clustered   |    50000 |          2500 |
| D2_50k    | cooccurring |    50000 |          2000 |

## AUC-PR by dataset × mode

| mode        |   D2_50k |     D3 |
|:------------|---------:|-------:|
| clustered   |   0.6216 | 0.8248 |
| cooccurring |   0.5337 | 1      |
| independent |   0.6914 | 0.8352 |

## Per-family recall (hybrid_xgb)

| dataset   | mode        | family                      |   n_injected |   recovered |   recall |
|:----------|:------------|:----------------------------|-------------:|------------:|---------:|
| D3        | independent | C1_education_out_of_domain  |          300 |         300 |   1      |
| D3        | independent | C2_limitbal_inconsistency   |          300 |         164 |   0.5467 |
| D3        | independent | C3_bill_sign_violation      |          300 |         165 |   0.55   |
| D3        | independent | C4_pay_temporal_violation   |          300 |         198 |   0.66   |
| D3        | independent | C5_age_range_violation      |          300 |         300 |   1      |
| D3        | clustered   | C1_education_out_of_domain  |          300 |         300 |   1      |
| D3        | clustered   | C2_limitbal_inconsistency   |          300 |         155 |   0.5167 |
| D3        | clustered   | C3_bill_sign_violation      |          300 |         197 |   0.6567 |
| D3        | clustered   | C4_pay_temporal_violation   |          300 |         226 |   0.7533 |
| D3        | clustered   | C5_age_range_violation      |          300 |         300 |   1      |
| D3        | cooccurring | C1+C2+C3_cooccurring        |          300 |         300 |   1      |
| D3        | cooccurring | C4+C5_cooccurring           |          300 |         300 |   1      |
| D2_50k    | independent | B1_ot_regular_inconsistency |          500 |         457 |   0.914  |
| D2_50k    | independent | B2_salary_basis_mismatch    |          500 |         444 |   0.888  |
| D2_50k    | independent | B3_near_duplicate_name      |          500 |          14 |   0.028  |
| D2_50k    | independent | B4_agency_title_violation   |          500 |         368 |   0.736  |
| D2_50k    | independent | B5_magnitude_outlier        |          500 |         398 |   0.796  |
| D2_50k    | clustered   | B1_ot_regular_inconsistency |          500 |          57 |   0.114  |
| D2_50k    | clustered   | B2_salary_basis_mismatch    |          500 |         408 |   0.816  |
| D2_50k    | clustered   | B3_near_duplicate_name      |          500 |           5 |   0.01   |
| D2_50k    | clustered   | B4_agency_title_violation   |          500 |         390 |   0.78   |
| D2_50k    | clustered   | B5_magnitude_outlier        |          500 |         477 |   0.954  |
| D2_50k    | cooccurring | B1+B5_cooccurring           |          500 |         459 |   0.918  |
| D2_50k    | cooccurring | B2+B4_cooccurring           |          500 |         489 |   0.978  |
| D2_50k    | cooccurring | B3_near_duplicate_name      |         1000 |           3 |   0.003  |

---
Generated in 37.5s
