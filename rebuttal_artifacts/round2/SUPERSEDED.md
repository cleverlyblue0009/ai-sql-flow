# Round-2 Supersession Record

All round-1 artefacts under `rebuttal_artifacts/` are PRESERVED unchanged.
Where a round-2 experiment supersedes a round-1 result, the corrected version
is in `rebuttal_artifacts/round2/` and recorded here.

---

## E6 → F1 (CRITICAL SUPERSESSION)

**Round-1 artefact**: `rebuttal_artifacts/e6/`
**Round-2 artefact**: `rebuttal_artifacts/round2/f1_joint_gate/`
**Reviewer comment**: R2.4 (deciding comment)

### What was wrong in E6

`phase2_rebuild/rebuttal/e6_joint_gate.py` defined the reference as
`(cleansed_data, source_SQL)` — the identical pair that the JOINT GATE produces.
This made:

```python
wrong_joint: False,           # hardcoded unconditionally
pct_wrong_joint_gate = 0.0    # literal, not computed
```

The joint gate's 0% error rate was an **assignment**, not a **measurement**.
A reviewer who opened the script would see this immediately.

### What F1 does differently

Reference = `query(TRUE_TABLE, SOURCE_SQL)` where `TRUE_TABLE` is the
pre-injection parquet (D2: `D2_nyc_fy2024.parquet` 200k rows;
D3: `D3_uci_credit.parquet` 30k rows). This is independent of any gate.

Six conditions are executed per query:
- C0: true + source = REFERENCE
- C2: dirty + source = SQL_GATE_ONLY
- C3: dirty + transpiled = NO_GATE
- C4: clean + source = JOINT_GATE
- C5: clean + transpiled = DATA_GATE_ONLY

All four gate error rates are now MEASURED.

### F1 finding

**JOINT GATE DOES NOT ADD VALUE OVER THE BETTER SINGLE GATE.**

- Joint gate error rate: 91.4% (overall), 90.0% (targeted), 93.3% (control)
- Best single gate (SQL gate): 74.3% (overall)
- Joint-required cases (both single gates wrong, joint correct): **0**

The joint gate is actually WORSE than the SQL gate for control queries (93.3% vs 46.7%)
because FP over-quarantine (14,803 FP removals in D2 alone) introduces systematic aggregate
bias even on columns that were never perturbed by any injection.

### Manuscript implication

The paper must not claim the joint gate provides error reduction beyond
the better single gate. The defensible contribution is the **unified pipeline
design** — shared data provenance, a reproducible audit trail, and a single
deployment surface — rather than a multiplicative error reduction claim.

---

## E3 → F2 (PENDING — high priority)

Not yet run. F2 will supersede E3 with: XGBoost + LightGBM included;
10-seed evaluation; nested vs oracle threshold comparison.

## E5 (AST relaxed comparator) → F5 (PENDING)

The E5 `e5_ast_relaxed.csv` strict-rate computation was broken (all 0%).
F5 will fix the bug, validate against committed `sql_migration_matrix.csv`,
and add execution equivalence.
