# F1: Joint Gate — True Pre-Injection Reference Experiment

**Manuscript**: DataFlow AI — IEEE Access Access-2026-28181

---

## ONE-LINE VERDICT (R2.4 deciding comment)

**Does the joint gate provide measurable value over the better single gate? NO — joint gate error (91.4%) >= better single gate (74.3%)**

---

## Fix applied vs Round-1 E6

Round-1 (E6) defined the reference as (cleansed, source SQL) — identical to the joint gate output. `wrong_joint` was hardcoded to `False`; `pct_wrong_joint_gate = 0.0` was a literal assignment. This experiment replaces that with:

  **REFERENCE = query(TRUE_TABLE, SOURCE_SQL)**

  `TRUE_TABLE` = pre-injection parquet, independent of any gate.

All four gate error rates are now MEASUREMENTS, not assignments.

---

## Dataset context

**D2**: true=200,000  dirty=202,000  clean=177,197  tau=0.67102  quarantined=24,803 (~12.3% of rows)

  Note: quarantined > n_pos means false positives exist — joint gate will have non-zero error even from FP over-removal.

**D3**: true=30,000  dirty=30,000  clean=28,212  tau=0.95394  quarantined=1,788 (~6.0% of rows)

  Note: quarantined > n_pos means false positives exist — joint gate will have non-zero error even from FP over-removal.

## Experimental design

- 35 queries: 20 targeted (touch injected columns) + 15 control (safe columns only)
- 6 execution conditions per query:

  | Condition | Data | SQL | Gate |
  |---|---|---|---|
  | C0 | true | source | REFERENCE |
  | C1 | true | transpiled | SQL-only drift baseline |
  | C2 | dirty | source | SQL_GATE_ONLY |
  | C3 | dirty | transpiled | NO_GATE |
  | C4 | clean | source | JOINT_GATE |
  | C5 | clean | transpiled | DATA_GATE_ONLY |

- Transpilation: postgres → tsql → duckdb (2-hop via sqlglot)
- Float tolerance: abs(a-b) <= max(0.0001, 1e-6*|ref|) → 'within_float_tolerance' — NOT counted as error

## Gate error rates (all queries with executable reference)

| stratum   |   n_queries |   n_ref_executable |   pct_wrong_true_trans |   pct_wrong_sql_gate |   pct_wrong_no_gate |   pct_wrong_joint_gate |   pct_wrong_data_gate |   n_joint_required |
|:----------|------------:|-------------------:|-----------------------:|---------------------:|--------------------:|-----------------------:|----------------------:|-------------------:|
| targeted  |          20 |                 20 |                    5   |                 95   |                95   |                   90   |                  90   |                  0 |
| control   |          15 |                 15 |                    6.7 |                 46.7 |                46.7 |                   93.3 |                  93.3 |                  0 |
| all       |          35 |                 35 |                    5.7 |                 74.3 |                74.3 |                   91.4 |                  91.4 |                  0 |

## Strata comparison

- **Targeted queries** touch anomaly-injected columns; errors reflect both data corruption and detector imperfection.
- **Control queries** touch only safe columns; errors reflect detector FP over-removal and SQL transpilation drift.

| | Targeted | Control |
|---|---|---|
| No gate wrong | 95.0% | 46.7% |
| SQL gate wrong | 95.0% | 46.7% |
| Data gate wrong | 90.0% | 93.3% |
| Joint gate wrong | 90.0% | 93.3% |
| Joint-required | 0 | 0 |

## Interpretation

### On the joint gate's value

The joint gate's measured error rate (91.4%) is NOT lower than the best single gate (74.3%). Within this corpus, the joint gate does not provide additional error reduction beyond applying the better single gate alone.

**For the manuscript**: the paper should not claim the joint gate provides error reduction beyond the best single gate. A defensible and honest contribution is the UNIFIED PIPELINE DESIGN — shared data provenance, reproducible audit trail, and a single deployment surface — rather than a claim that coupling the two gates multiplicatively reduces error.

### On the detector's imperfection

The joint gate error reflects the detector's FP rate: rows that are CLEAN but flagged as anomalous are removed from the cleansed table, creating systematic bias in all aggregates even on safe columns. This is a measurement of the detector quality ceiling, not a gate design flaw.

**D2**: 24,803 quarantined − 10,000 true positives = **14,803 false-positive removals** (7.4% of clean rows wrongly removed). The cleansed D2 table has 177,197 rows vs the true 200,000 — a 11.4% row deficit that affects every aggregate.

**D3**: 1,788 quarantined − 1,500 true positives = **288 false-positive removals** (0.96% of clean rows). Verified: `AVG(BILL_AMT2)` over cleansed D3 = 49,603.71 vs true reference = 49,179.08 (0.86% relative error). This safe column is not perturbed by any injection; the error is entirely from FP row removal.

### Error mechanism breakdown

**Why SQL gate is correct for D3 control queries (0% error)**:
D3 injection is all in-place modification. Safe columns (SEX, MARRIAGE, BILL_AMT2–6, etc.) are
unchanged in the dirty table. `SELECT SEX, COUNT(*) FROM credit_dirty` returns the same result
as the true reference. The SQL gate preserves row count and unperturbed columns.

**Why joint gate is wrong for D3 control queries (100% error)**:
The cleansed D3 table has 28,212 rows (288 FPs removed). All aggregate queries over a subset
of 28,212 produce different values from the 30,000-row true reference, even for unperturbed columns.
The joint gate introduces selection bias by removing clean rows.

**Why joint gate is slightly BETTER than SQL gate for targeted queries**:
Targeted queries touch injected columns. SQL gate (dirty+source) sees injected values → 95% wrong.
Joint gate (clean+source) sees partially cleaned values → 90% wrong. The 5-point improvement
comes from correct TP quarantines (injected values removed). The remaining 90% error comes from
FP quarantines creating aggregate bias (missing legitimate values from removed clean rows).

**The one case where SQL gate is the ONLY wrong gate (T19 — AGE violations)**:
`SELECT COUNT(*) WHERE AGE < 18 OR AGE > 100`: true=0, dirty=247, clean=0.
The detector correctly quarantines all C5 (age-range) injected rows → joint gate and data gate
both return 0 = correct. SQL gate returns 247 = wrong. This is the detector working as intended —
but it is NOT a joint-required case (data gate alone already gives the right answer).

### SQL transpilation drift in this corpus

Transpilation drift (postgres → tsql → duckdb) caused error in only 5.7% of queries
(2/35 on the true table baseline). This is why joint_required = 0: for joint-required
cases to exist, transpilation must fail SIMULTANEOUSLY with data corruption. Transpilation
is rarely the binding constraint in this query corpus.

---

Generated in 2.3s.  Outputs: rebuttal_artifacts/round2/f1_joint_gate/
