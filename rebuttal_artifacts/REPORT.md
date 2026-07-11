# Phase 0 Rebuttal Gates: Verification Report

**Manuscript:** DataFlow AI — IEEE Access submission Access-2026-28181
**Branch:** rebuttal/access-2026-28181
**Completed:** 2026-07-11
**Overall Phase 0 Verdict:** 3 gates PASS, 0 gates FAIL

---

## G1 — Reproduction

**Verdict: PASS**

All 18 (detector × dataset) F1 values in `baseline.csv` reproduce to full float64 precision
at SEED=42. All 15 per-family recall values in `per_family.csv` reproduce. CV, ablation,
threshold sweep, and scalability tables reproduce.

The full pipeline (01→02→10→30) was re-executed from committed raw data. Logs are in
`rebuttal_artifacts/logs/`. Detailed comparison in `REPRODUCTION_OK.md`.

**No detection-metric discrepancies were found.** The system works as described.

---

## G2 — Query Count Bug Fix

**Verdict: FIXED**

`30_run_sql_migration.py` line 176 originally computed:

```python
"n_queries": df["query"].nunique()   # 109 — counts unique filenames
```

Six query filenames appear in multiple dialect source folders:
`simple_select` (×3), `basic_update`, `limit_offset`, `row_number_pagination`,
`recursive_cte` (×2). The unique-filename count incorrectly collapsed these to 109.

Fixed to:

```python
"n_queries": df[["src_folder", "query"]].drop_duplicates().shape[0]  # 115
```

The correct count is **115 unique (src_folder, query) pairs**. This appears in the
manuscript at **four locations** (abstract line 70, contributions line 283, Section IV-D
line 680, Threats to Validity line 1138) and in Table 7 (line 913). All five occurrences
must be corrected to 115.

**Impact:** Descriptive accuracy only. All parse/transpile/AST-equivalence *rates* are
computed from the per-pair data frame and are unaffected. F1 values and detection metrics
are entirely unaffected.

---

## G3 — Manuscript Audit

**Verdict: 5 discrepancies found** (see `MANUSCRIPT_AUDIT.csv` for all 80 rows)

### D1 — Absolute gain 0.043 (minor rounding)
- **Claim (abstract line 63, Section IV-A line 707):** "absolute gain of 0.043 over the strongest single detector"
- **Backing (baseline.csv):** hybrid_lr D1 F1 = 0.5114931; rule D1 F1 = 0.4697108; difference = 0.0418
- **Correction:** Change "0.043" to "0.042" at both locations.

### D2 — "0.738 on hard queries" conflates medium with hard (abstract line 74)
- **Claim:** "degrades from 0.921 on easy queries to 0.738 on hard ones"
- **Backing (sql_migration_by_difficulty.csv):** easy=0.9211, **medium=0.7385**, **hard=0.7421**
- The value 0.738 belongs to *medium*, not *hard* difficulty. Hard AST-equiv = 0.742.
- **Correction:** "...to 0.738 on medium-difficulty and 0.742 on hard queries." Or rephrase to report the drop monotonically.

### D3 — Per-family recall list (Section IV-B line 765)
- **Claim:** "Five families exceed 0.93 recall: A4, A5, B2, C1, C5"
- **Backing (per_family.csv):** A5 recall = 0.918 (NOT > 0.93); B1 recall = 0.9435 (IS > 0.93, but absent from list)
- **Correction:** Replace A5 with B1: "A4, B1, B2, C1, C5 exceed 0.93 recall" (A5=0.918 should not be in this list).

### D4 — Ablation claim (Section IV-D body line 817)
- **Claim:** "removing LOF is the least damaging everywhere"
- **Backing (ablation.csv):** On D3, |ΔF1(remove LOF)| = +0.011, |ΔF1(remove iforest)| = −0.008. Removing iforest is less damaging on D3.
- **Correction:** "...least damaging on D1 and D2; on D3, removing IsolationForest costs only 0.008 F1, marginally less than LOF's 0.011."

### D5 — G2 query count (4 manuscript locations + Table 7)
- Already documented under G2. All "109" occurrences must become "115".

---

## G4 — Seed Parameterisation

**Verdict: PASS**

A new entry-point `phase2_rebuild/rebuttal/run_pipeline_seed.py` accepts `--seed N` and
writes all outputs to `rebuttal_artifacts/seeds/seedN/`. Runs at different seeds never
clobber each other.

Verification script `phase2_rebuild/rebuttal/g4_gate.py` staged the committed SEED=42
injected parquets into `rebuttal_artifacts/seeds/seed42/` and re-ran the scoring stack
with `random_state=42` threaded through `IsolationForest`, `LogisticRegression`, and
`StratifiedKFold`. All 18 F1 values and 15 recall values reproduced to full float64
precision. Details in `SEED42_VERIFY.md`.

The `run_pipeline_seed.py` script is ready for Experiment E1 (multi-seed variance, seeds
43–51).

---

## Summary table

| Gate | Task | Verdict | Key artifact |
|------|------|---------|--------------|
| G1 | Reproduce all tables at SEED=42 | **PASS** | `REPRODUCTION_OK.md` |
| G2 | Fix query count 109→115 in 30_run_sql_migration.py | **FIXED** | `30_run_sql_migration.py` (line 176, 186) |
| G3 | Audit every numeric claim in DataFlow.tex | **5 discrepancies** | `MANUSCRIPT_AUDIT.csv` |
| G4 | Thread --seed through pipeline, verify seed=42 reproduces | **PASS** | `SEED42_VERIFY.md` |

---

## Next steps: Experiments E1–E8

Pending user approval. Priority order per reviewer comments:
- **E6** (joint gate coupling) — deciding comment R2.4
- **E1** (multi-seed variance, seeds 42–51) — seeds available via `run_pipeline_seed.py`
- **E2** (PyOD modern baselines) — requires `pip install pyod`
- **E3–E8** — see task specification
