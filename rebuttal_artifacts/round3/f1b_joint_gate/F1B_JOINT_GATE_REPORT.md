# F1b: Joint Gate — Magnitude Metric, Repaired Condition, Coupled Gate

**Manuscript**: DataFlow AI — IEEE Access Access-2026-28181

---

## Opening lines (R2.4 deciding comment)

**1. Does coupling reduce relative error vs the better single gate?  NO**  
Median rel-err: dirty=0.010477, cleansed=0.142857, repaired=0.000988, coupled=0.010477. Best single = 0.000988.

**2. Does quarantine-by-deletion introduce measurable selection bias into aggregates over uncorrupted columns?  YES**  
Control queries: cleansed median rel-err = 0.097628 vs dirty median = 0.0. Selection bias magnitude = 0.0976 (cleansed is WORSE than dirty on safe-column queries due to FP row removal).

**3. What does the FP rate cost?**  
D2: 24,803 rows in review queue, 18,556 FPs (74.8%). FP-induced cleansed bias on control queries: 0.097628.  
D3: 1,788 rows in review queue, 609 FPs (34.1%).  

---

## Fixes applied vs F1 and E6

| Fix | F1b change |
|---|---|
| Binary metric (F1 flaw) | Replaced with rel-err magnitude; stored per (query, condition) |
| Repaired condition missing | Added C5/C6: quarantined rows restored to TRUE values |
| Coupled gate not tested | Added C7: column-provenance-aware reinstatement |
| 2-hop transpilation | Now single-hop postgres→duckdb |

## Conditions

| Code | Data | SQL | Gate |
|---|---|---|---|
| C0 | true | source | REFERENCE |
| C1 | dirty | source | SQL_GATE |
| C2 | dirty | transpiled | NO_GATE |
| C3 | cleansed (deletion) | source | JOINT_GATE |
| C4 | cleansed (deletion) | trans | DATA_GATE |
| C5 | repaired (analyst review) | source | REPAIRED |
| C6 | repaired | trans | REPAIRED_TRANS |
| C7 | coupled (col-aware) | source | COUPLED_GATE |

## Dataset context

**D2**: true=200,000  dirty=202,000  cleansed=177,197  repaired=201,817  quarantined=24,803 (tp=6247, fp=18556, fn=3753)

**D3**: true=30,000  dirty=30,000  cleansed=28,212  repaired=30,000  quarantined=1,788 (tp=1179, fp=609, fn=321)

## Median relative error by condition and stratum

| condition         | stratum   |   median |      p90 |      max |
|:------------------|:----------|---------:|---------:|---------:|
| C1_dirty_src      | all       | 0.010477 | 1        | 2.47e+11 |
| C1_dirty_src      | targeted  | 0.250824 | 3.26564  | 2.47e+11 |
| C1_dirty_src      | control   | 0        | 0.824421 | 1        |
| C2_dirty_trans    | all       | 0.010477 | 1        | 2.47e+11 |
| C2_dirty_trans    | targeted  | 0.250824 | 3.26564  | 2.47e+11 |
| C2_dirty_trans    | control   | 0        | 0.789333 | 1        |
| C3_clean_src      | all       | 0.142857 | 1        | 3        |
| C3_clean_src      | targeted  | 0.160817 | 1        | 1        |
| C3_clean_src      | control   | 0.097628 | 1        | 3        |
| C4_clean_trans    | all       | 0.142857 | 1        | 3        |
| C4_clean_trans    | targeted  | 0.160817 | 1        | 1        |
| C4_clean_trans    | control   | 0.097628 | 1        | 3        |
| C5_repaired_src   | all       | 0.000988 | 0.750118 | 1        |
| C5_repaired_src   | targeted  | 0.004029 | 0.64     | 1        |
| C5_repaired_src   | control   | 0        | 0.750118 | 1        |
| C6_repaired_trans | all       | 0.000988 | 0.824421 | 1        |
| C6_repaired_trans | targeted  | 0.004029 | 0.64     | 1        |
| C6_repaired_trans | control   | 0        | 0.824421 | 1        |
| C7_coupled_src    | all       | 0.010477 | 1        | 2.47e+11 |
| C7_coupled_src    | targeted  | 0.247085 | 3.26001  | 2.47e+11 |
| C7_coupled_src    | control   | 0        | 0.706    | 1        |

## Materiality sensitivity (% queries exceeding threshold)

| condition         | stratum   |   0.001 |   0.01 |   0.05 |
|:------------------|:----------|--------:|-------:|-------:|
| C1_dirty_src      | all       |    65.7 |   57.1 |   42.9 |
| C1_dirty_src      | control   |    33.3 |   33.3 |   20   |
| C1_dirty_src      | targeted  |    90   |   75   |   60   |
| C2_dirty_trans    | all       |    65.7 |   57.1 |   42.9 |
| C2_dirty_trans    | control   |    33.3 |   33.3 |   20   |
| C2_dirty_trans    | targeted  |    90   |   75   |   60   |
| C3_clean_src      | all       |    91.4 |   82.9 |   68.6 |
| C3_clean_src      | control   |    93.3 |   86.7 |   66.7 |
| C3_clean_src      | targeted  |    90   |   80   |   70   |
| C4_clean_trans    | all       |    91.4 |   82.9 |   68.6 |
| C4_clean_trans    | control   |    93.3 |   86.7 |   66.7 |
| C4_clean_trans    | targeted  |    90   |   80   |   70   |
| C5_repaired_src   | all       |    48.6 |   31.4 |   22.9 |
| C5_repaired_src   | control   |    33.3 |   20   |   20   |
| C5_repaired_src   | targeted  |    60   |   40   |   25   |
| C6_repaired_trans | all       |    48.6 |   31.4 |   22.9 |
| C6_repaired_trans | control   |    33.3 |   20   |   20   |
| C6_repaired_trans | targeted  |    60   |   40   |   25   |
| C7_coupled_src    | all       |    65.7 |   51.4 |   42.9 |
| C7_coupled_src    | control   |    33.3 |   20   |   20   |
| C7_coupled_src    | targeted  |    90   |   75   |   60   |

## Coupled gate vs other conditions

| stratum   |   n_queries |   median_dirty_rel_err |   median_cleansed_rel_err |   median_repaired_rel_err |   median_coupled_rel_err |   best_single_median | coupled_beats_best_single   |   avg_n_reinstated |
|:----------|------------:|-----------------------:|--------------------------:|--------------------------:|-------------------------:|---------------------:|:----------------------------|-------------------:|
| all       |          35 |               0.010477 |                  0.142857 |                  0.000988 |                 0.010477 |             0.000988 | False                       |            13530.2 |
| targeted  |          20 |               0.250824 |                  0.160817 |                  0.004029 |                 0.247085 |             0.004029 | False                       |            13204   |
| control   |          15 |               0        |                  0.097628 |                  0        |                 0        |             0        | False                       |            13965.1 |

## Analyst cost

| dataset   |   n_quarantined |   n_tp_in_queue |   n_fp_in_queue |   fp_fraction |   n_fn_escaped |   n_pos_total |
|:----------|----------------:|----------------:|----------------:|--------------:|---------------:|--------------:|
| D2        |           24803 |            6247 |           18556 |        0.7481 |           3753 |         10000 |
| D3        |            1788 |            1179 |             609 |        0.3406 |            321 |          1500 |

## Interpretation

### Why F1's 91.4% error rate was void

F1 used a binary `is_error` flag. Under row-deleting quarantine, ANY aggregate over 28,212 rows (cleansed D3) differs from the same aggregate over 30,000 rows (true D3), even with a perfect detector. The binary metric guaranteed near-100% error for the cleansed condition regardless of detector quality. F1b replaces this with relative error: a 0.86% AVG(BILL_AMT2) deviation is now measured as 0.0086, not 'wrong'.

### The selection-bias finding

Quarantine-by-deletion introduces measurable selection bias into aggregates over columns that were NEVER corrupted. On control queries, the cleansed condition (median rel-err = 0.097628) is WORSE than the dirty condition (median rel-err = 0.0). This is FP over-quarantine: 609 innocent D3 rows were removed, biasing every aggregate — including safe-column aggregates the detector never intended to affect.

### The repaired condition

C5/C6 (repaired) models the deployment the paper actually claims: quarantined rows are sent to an audit queue, an analyst reviews each one, confirmed errors are corrected (TP: restore true value), and false alarms are cleared (FP: row restored unchanged). Under this model, FP bias disappears. The residual error in C5 comes only from false negatives (corrupted rows that escaped the detector and remain in the table).

### The coupled gate

C7 (coupled gate) achieves median rel-err = 0.010477. This does NOT beat the best single gate (median = 0.000988). The honest conclusion: simple column-provenance-based reinstatement does not provide a measurable advantage over the better single gate in this corpus. The coupling mechanism is technically sound but the practical gain is small. The manuscript should not claim multiplicative error reduction from coupling; a shared-audit-contract framing is more defensible.

---

Generated in 18.5s. Outputs: rebuttal_artifacts/round3/f1b_joint_gate/
