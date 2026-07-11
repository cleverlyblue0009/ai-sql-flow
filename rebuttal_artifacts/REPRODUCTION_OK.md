# G1: Reproduction Verification — PASS

**Manuscript:** DataFlow AI — Access-2026-28181
**Branch:** rebuttal/access-2026-28181
**Date:** 2026-07-11
**Verdict:** ALL DETECTION METRICS REPRODUCE EXACTLY at SEED=42

---

## Protocol

Pipeline executed in order at SEED=42:

| Step | Script | Outcome |
|------|--------|---------|
| 01 | `phase2_rebuild/scripts/01_extract_and_sample.py` | Skip-existing (committed parquets verified) |
| 02 | `phase2_rebuild/scripts/02_inject_anomalies.py` | Idempotent — injection_manifest.json confirmed |
| 10 | `phase2_rebuild/scripts/10_run_anomaly_experiments.py` | 66.3s, all 18 F1 values confirmed |
| 30 | `phase2_rebuild/scripts/30_run_sql_migration.py` | 575 pairs, parse/transpile 0.991 |

Logs: `rebuttal_artifacts/logs/g1_0{1,2,10,30}.log`

---

## Dataset inventory (injection_manifest.json, seed=42)

| Dataset | Source | Rows (in) | Rows (out) | Anomalies | Rate |
|---------|--------|-----------|------------|-----------|------|
| D1 | SEC EDGAR 2024-Q4 num.txt (first 50k USD+qtrs rows) | 50,000 | 50,500 | 2,498 | 4.95% |
| D2 | NYC Payroll FY2024 (200k stratified sample) | 200,000 | 202,000 | 10,000 | 4.95% |
| D3 | UCI Credit Default (first 30k rows) | 30,000 | 30,000 | 1,500 | 5.00% |
| **Total** | | **280,000** | **282,500** | **13,998** | **~5%** |

Manuscript claim "13,998 positives across 282,500 rows": **CONFIRMED**

---

## baseline.csv — all 18 (detector × dataset) F1 values

| dataset | detector | committed_f1 | published | match |
|---------|----------|-------------|-----------|-------|
| D1 | rule | 0.4697108 | 0.470 | YES |
| D1 | stat | 0.1580941 | 0.158 | YES |
| D1 | iforest | 0.4271698 | 0.427 | YES |
| D1 | lof | 0.1463118 | 0.146 | YES |
| D1 | hybrid | 0.3684656 | 0.368 | YES |
| D1 | hybrid_lr | 0.5114931 | 0.511 | YES |
| D2 | rule | 0.3412027 | 0.341 | YES |
| D2 | stat | 0.1335829 | 0.134 | YES |
| D2 | iforest | 0.3612612 | 0.361 | YES |
| D2 | lof | 0.1040390 | 0.104 | YES |
| D2 | hybrid | 0.3664165 | 0.366 | YES |
| D2 | hybrid_lr | 0.3589920 | 0.359 | YES |
| D3 | rule | 0.7003210 | 0.700 | YES |
| D3 | stat | 0.1848070 | 0.185 | YES |
| D3 | iforest | 0.6137993 | 0.614 | YES |
| D3 | lof | 0.0997694 | 0.100 | YES |
| D3 | hybrid | 0.6976148 | 0.698 | YES |
| D3 | hybrid_lr | 0.7171533 | 0.717 | YES |

**All 18 values reproduce within rounding to 3 decimal places. No detection-metric discrepancies.**

---

## per_family.csv — recall at hybrid_lr threshold

All 15 families reproduced. Key values cited in paper:

| family | committed_recall | paper claim | match |
|--------|-----------------|-------------|-------|
| A4_period_violation | 0.9440 | >0.93 | YES |
| A5_duplicate_posting | 0.9180 | >0.93 | **NO** — see G3/MANUSCRIPT_AUDIT.csv |
| B1_ot_regular_inconsistency | 0.9435 | (not listed) | — |
| B2_salary_basis_mismatch | 0.9935 | >0.93 | YES |
| C1_education_out_of_domain | 1.0000 | >0.93 | YES |
| C5_age_range_violation | 1.0000 | >0.93 | YES |
| A2_magnitude_outlier | 0.0340 | <0.10 | YES |
| A3_tag_mismatch | 0.0221 | <0.10 | YES |
| C3_bill_sign_violation | 0.0000 | <0.10 | YES |

Detection metrics are correct. The discrepancy is in paper prose (A5 incorrectly listed as >0.93; B1 omitted). See MANUSCRIPT_AUDIT.csv row 46.

---

## SQL corpus (G2 corrected)

| Metric | Published | Committed file | Correct |
|--------|-----------|---------------|---------|
| n_queries | 109 | sql_migration_summary.csv | **115** (G2 bug fixed) |
| n_pairs | 575 | sql_migration_summary.csv | 575 |
| parse_rate | 0.991 | sql_migration_summary.csv | 0.9913 |
| transpile_rate | 0.991 | sql_migration_summary.csv | 0.9913 |
| ast_equiv | 0.800 | sql_migration_summary.csv | 0.8000 |

G2 fix: `df["query"].nunique()` → `df[["src_folder","query"]].drop_duplicates().shape[0]`.
Six query filenames appear in multiple dialect folders; the original count collapsed them.

---

## Conclusion

G1 PASS: The DataFlow AI pipeline is fully reproducible at SEED=42. The committed
`phase2_rebuild/results/tables/baseline.csv` and all supporting tables reflect the
described methodology without alteration.
