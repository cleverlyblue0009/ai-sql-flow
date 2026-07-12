# Round-2 Rebuttal Summary — Access-2026-28181

**Status**: F1 complete. F2–F6 pending.

---

## ONE-LINE VERDICTS (required by task spec)

**F1 (Joint gate, R2.4 deciding comment)**:
> **NO** — the joint gate does NOT provide measurable value over the better single gate.
> Joint gate error = 91.4%; best single gate (SQL gate) = 74.3%; joint-required cases = 0.
> The joint gate is actually *worse* than the SQL gate for control (safe-column) queries
> because FP over-quarantine (14,803 false-positive removals in D2) biases all aggregates.

**F2 (GBDT vs LR, R2.1)**: PENDING — not yet run.

---

## Reviewer named-but-unrun asks

| Reviewer ask | Status |
|---|---|
| Deep SVDD (R2.3) | PENDING (F3) |
| Correlated failures (R2.2) | PENDING (F4) |
| Temporal drift (R2.2) | PENDING (F4) |
| XGBoost / LightGBM (R2.1) | PENDING (F2) |

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

*F2–F6 sections will be added as each experiment completes.*
