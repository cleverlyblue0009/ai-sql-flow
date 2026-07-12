# Round-2 Rebuttal Summary — Access-2026-28181

**Status**: F1 complete. F2–F6 pending.

---

## ONE-LINE VERDICTS (required by task spec)

**F1 (Joint gate, R2.4 deciding comment)**:
> **NO** — the joint gate does NOT provide measurable value over the better single gate.
> Joint gate error = 91.4%; best single gate (SQL gate) = 74.3%; joint-required cases = 0.
> The joint gate is actually *worse* than the SQL gate for control (safe-column) queries
> because FP over-quarantine (14,803 false-positive removals in D2) biases all aggregates.

**F2 (GBDT vs LR, R2.1)**: **MAJOR REVISION TRIGGER** — LGB beats LR by +0.1795 on D2 (10-seed mean, nested threshold, Holm p=0.0000). Full pipeline re-run required with LGB/XGB meta-learner before resubmission.

---

## Reviewer named-but-unrun asks

| Reviewer ask | Status |
|---|---|
| Deep SVDD (R2.3) | PENDING (F3) |
| Correlated failures (R2.2) | PENDING (F4) |
| Temporal drift (R2.2) | PENDING (F4) |
| XGBoost / LightGBM (R2.1) | COMPLETE (F2) — MAJOR REVISION TRIGGER confirmed (10 seeds, Holm p=0.0000) |

---

## Claims in current manuscript CONTRADICTED by round-2 evidence

| Claim | Contradicted by | Detail |
|---|---|---|
| "The joint gate catches downstream errors that neither single gate can address independently" | F1: 0 joint-required cases out of 35 queries | Neither the SQL gate nor the data gate needed the other to reduce error; FP over-quarantine makes joint worse overall |
| "Coupling the anomaly detection and SQL migration gates reduces downstream query error" | F1: joint gate error 91.4% > SQL gate error 74.3% | Applying the data gate (cleansing) INCREASES error for safe-column queries due to FP removal |

---

## F1 — Joint Gate (COMPLETE)

**Script**: `phase2_rebuild/rebuttal/f1_joint_gate_v2.py`
**Outputs**: `rebuttal_artifacts/round2/f1_joint_gate/`
**Supersedes**: `rebuttal_artifacts/e6/` (see `SUPERSEDED.md`)

### The fix

Round-1 E6 set `pct_wrong_joint_gate = 0.0` as a literal and `wrong_joint = False`
unconditionally. The reference was defined as `(cleansed, source)` — identical to the joint
gate — making joint gate 0% error by construction.

F1 uses `REFERENCE = query(TRUE_TABLE, SOURCE_SQL)` where `TRUE_TABLE` is the
pre-injection parquet, independent of any gate.

### Key numbers

35 queries (20 targeted, 15 control), 6 conditions each, all results persisted.

| Condition | Targeted error | Control error | Overall error |
|---|---|---|---|
| true + transpiled (SQL-drift baseline) | 5.0% | 6.7% | 5.7% |
| dirty + source (SQL_GATE) | 95.0% | 46.7% | 74.3% |
| dirty + transpiled (NO_GATE) | 95.0% | 46.7% | 74.3% |
| **clean + source (JOINT_GATE)** | **90.0%** | **93.3%** | **91.4%** |
| clean + transpiled (DATA_GATE) | 90.0% | 93.3% | 91.4% |
| joint-required cases | 0 | 0 | 0 |

### Error mechanism

**Why joint gate > SQL gate for control queries**:
D3 in-place modifications leave safe columns (SEX, MARRIAGE, BILL_AMT2–6, etc.) unchanged
in the dirty table → SQL gate is 0% wrong for D3 control.
The cleansed D3 table has 288 fewer rows (FP quarantines), changing all aggregate statistics
even on unperturbed columns. Verified: `AVG(BILL_AMT2)` = 49,603.71 (clean) vs 49,179.08
(true). SQL gate is CORRECT; joint gate is WRONG.

**Why transpilation is rarely the binding constraint**:
SQL transpilation drift (postgres→tsql→duckdb) caused errors in only 5.7% of queries
on the clean reference table. Joint-required cases require BOTH data corruption AND
transpilation drift simultaneously — this combination never occurred in 35 queries.

### Manuscript recommendation

Do not claim multiplicative error reduction from coupling both gates. The honest contribution
is the unified pipeline design: shared data lineage, single deployment surface, reproducible
audit trail. The coupling claim as currently stated is contradicted by measurement.

---

---

## F2 — Meta-Learner Comparison (COMPLETE — 10 seeds)

**Scripts**: `phase2_rebuild/rebuttal/f2_metalearner_v2.py` + `f2_continue.py` (resumed after task interruption at seed 49 D2)
**Outputs**: `rebuttal_artifacts/round2/f2_metalearner/`

### VERDICT: MAJOR REVISION TRIGGER

**Decision line**: Best GBDT is LGB on D2: 10-seed mean nested F1 delta = **+0.1795**, Holm-corrected p = **0.0000**.

Every GBDT (GBM, XGB, LGB) beats LR by a wide margin on D1 and D2 under the nested threshold, with significance surviving Holm correction on all 6 pairs:

| Meta-learner | D1 delta | D2 delta | Holm p (D1) | Holm p (D2) |
|---|---|---|---|---|
| GBM | +0.1363 | +0.1410 | 0.0000 | 0.0000 |
| XGB | +0.1612 | +0.1626 | 0.0000 | 0.0000 |
| **LGB** | **+0.1627** | **+0.1795** | **0.0000** | **0.0000** |
| MLP | +0.0930 | +0.0924 | — | — |
| RF | +0.0617 | +0.0902 | — | — |

D3 shows only small, insignificant differences (max XGB +0.0214).

### 10-seed mean F1 — nested threshold

| Meta-learner | D1 | D2 | D3 |
|---|---|---|---|
| LR (baseline) | 0.4525 | 0.3718 | 0.7782 |
| GBM | 0.5888 | 0.5129 | 0.7933 |
| XGB | 0.6137 | 0.5345 | 0.7995 |
| **LGB** | **0.6152** | **0.5513** | 0.7871 |
| MLP | 0.5455 | 0.4642 | 0.7863 |
| RF | 0.5142 | 0.4620 | 0.7901 |

### Oracle vs nested gap

All GBDT models show near-zero oracle gap (GBM: +0.002 on D1, LGB: +0.004), confirming the threshold-optimism correction does not inflate their scores. LR's gap is also near-zero. The 16–18 point advantage of LGB over LR is real, not an artifact of threshold selection.

### Action required

**Do not resubmit until the full pipeline is re-run with LGB (or XGB) as the meta-learner.** All numerical claims depending on the stacker F1 (Tables III–V, abstract) must be updated. Manuscript framing must change: the contribution is the pipeline architecture and the anomaly detection + SQL migration integration, not the logistic-regression stacking choice.

---

## F3 — Deep SVDD + Extended Stacker Ablation (COMPLETE)

**Script**: `phase2_rebuild/rebuttal/f3_deep_svdd.py`
**Outputs**: `rebuttal_artifacts/round2/f3_deep_svdd/`
**Addresses**: Reviewer 2 R2.3

### Key numbers (seed=42, oracle threshold)

| Dataset | Base4 stacker | Base4+ECOD | Base6 (Base4+ECOD+DeepSVDD) | Max gain |
|---|---|---|---|---|
| D1 | 0.5115 | 0.5285 | 0.5283 | +0.017 |
| D2 | 0.3590 | 0.3664 | **0.4198** | **+0.061** |
| D3 | 0.7172 | 0.7143 | **0.7684** | **+0.051** |

### Verdict

**MANUSCRIPT DISCUSSION REQUIRED** — Base6 (adding ECOD + Deep SVDD) improves D2 by +0.061 and D3 by +0.051, both > 0.05.

The paper should add a paragraph explaining why it chose [rule, stat, iforest, lof] over the richer base set. Honest framing: the paper's 4-detector base set was selected for interpretability and runtime; a 6-detector set with ECOD+DeepSVDD provides marginal-to-moderate gains at higher computational cost.

Note: Deep SVDD training loss did not converge in 20 epochs (oscillating, no downward trend), suggesting the architecture may need tuning. The improvement may understate what a properly tuned DeepSVDD would achieve.

---

## F4 — Corrected Prevalence Sweep + Temporal Drift (COMPLETE)

**Script**: `phase2_rebuild/rebuttal/f4_prevalence_drift.py`
**Outputs**: `rebuttal_artifacts/round2/f4_prevalence_drift/`
**Addresses**: Reviewer 2 R2.2

### F4a: Corrected prevalence sweep

Fix: E7 subsampled CLEAN rows to vary prevalence, changing the background distribution. F4a holds clean count fixed; subsamples ANOMALOUS rows only.

Corrected sweep results saved in `f4a_corrected_prevalence.csv`. Comparison vs E7 in `f4a_vs_e7_comparison.csv`.

### F4b: Temporal drift (D2 only meaningful)

D2 (NYC Payroll — fiscal-year ordered):
- Early 70%: F1=0.3743 (prevalence=4.0%)
- Late 30%: F1=0.3289 (prevalence=7.2%)
- Delta: -0.045 (below the 0.05 threshold, but note prevalence is confounded)

**VERDICT**: No significant temporal drift detected (delta < 0.05). However, the prevalence increase in the later split confounds the comparison — the lower F1 may reflect the higher anomaly concentration rather than distribution drift. Recommend acknowledging this limitation in the paper.

### F4c-d: Correlated failures and real error dataset

- Correlated failures: NOT IMPLEMENTED for rebuttal (requires pipeline modification). Acknowledged as limitation.
- Real error dataset: NOT FOUND (NIST SCTF requires registration; UCI/Kaggle have no labeled error sets). Acknowledged as limitation.

---

## F5 — AST Footprint Validation + Execution Equivalence (COMPLETE)

**Script**: `phase2_rebuild/rebuttal/f5_ast_execution_equiv.py`
**Outputs**: `rebuttal_artifacts/round2/f5_ast_execution/`
**Addresses**: Reviewer 2 E5 follow-up

### Key findings

1. **Perfect reproducibility**: 0/575 pairs differ between recomputed and committed footprint values. The committed `sql_migration_matrix.csv` is fully reproducible.

2. **Metric clarification**: The paper's "strict AST-footprint equivalence" is correctly named — it uses a structural fingerprint (node-type counts + table/column name sets), not string comparison. This is appropriate because cross-dialect transpilation changes SQL text even for semantically equivalent queries. A true string comparison yields 0.0 equivalence everywhere (too strict to be meaningful).

3. **Execution equivalence**: Cannot be computed from the query catalog — queries reference actual table schemas (users, customers, orders) that are not reproduced in the synthetic DuckDB environment.

### Verdict

The `ast_equiv_rate` values in the paper are correct and reproducible. The metric description in the manuscript is appropriate. No material change needed to the SQL migration section.

---

---

## F6 — Print-Scale Figures + Notation Table (COMPLETE)

**Script**: `phase2_rebuild/rebuttal/f6_print_figures.py`
**Outputs**: `rebuttal_artifacts/round2/f6_print_figures/`

### Figures regenerated (vector PDF, IEEE print scale)

| Figure | Width | Status |
|---|---|---|
| `fig_pr_curves.pdf` | 7.16" (double column) | OK |
| `fig_baseline_f1.pdf` | 3.5" (single column) | OK |
| `fig_threshold_sweep.pdf` | 3.5" (single column) | OK |
| `fig_ast_matrix.pdf` | 3.5" (single column) | OK |
| `fig_ablation.pdf` | 3.5" (single column) | OK |
| `fig_per_family.pdf` | 7.16" (double column) | OK |

### Notation table

- `notation_table.md` — Markdown version for review
- `notation_table.tex` — LaTeX table for manuscript appendix

### Legibility spec

- Font sizes: 7pt body, 9pt labels, 10pt titles
- Line width: 0.85pt minimum
- PDF format with embedded TrueType fonts (no raster artifacts)
- Greyscale contrast: blue/orange/green color trio — review greyscale printout before submission
