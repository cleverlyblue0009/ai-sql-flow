# Manuscript Correction Summary for IEEE Access Resubmission

**Manuscript:** DataFlow AI — Access-2026-28181
**Prepared:** 2026-07-11
**Basis:** Phase 0 gates G1–G4 (see REPORT.md and MANUSCRIPT_AUDIT.csv)

This document provides the exact text corrections needed for each discrepancy found in
DataFlow.tex. Each correction is backed by a specific cell in the committed results files.

---

## Correction C1 — Query count: 109 → 115 (G2 bug)

**Priority: HIGH** — appears 5 times; affects the abstract, contributions, a body section, threats to validity, and Table 7.

**Root cause:** `30_run_sql_migration.py` counted unique query *filenames* (`df["query"].nunique()`)
rather than unique (src_folder, query) pairs. Six filenames recur across dialect folders.
Fixed in commit on `rebuttal/access-2026-28181`.

**Backing file:** `phase2_rebuild/results/tables/sql_migration_summary.csv`
(`n_queries = 115` after fix)

### Five locations to change:

| Location | Line (approx.) | Old text | New text |
|----------|----------------|----------|----------|
| Abstract | 70 | "109 curated queries" | "115 curated queries" |
| Contributions | 283 | "109-query five-dialect SQL corpus" | "115-query five-dialect SQL corpus" |
| Section IV-D body | 680 | "109 queries" | "115 queries" |
| Table 7 caption/row | 913 | "Queries: 109" | "Queries: 115" |
| Threats to Validity | 1138 | "109-query corpus" | "115-query corpus" |

No rates, F1 values, or pair counts change. "575 source-target pairs" remains correct (115 × 5 dialects = 575).

---

## Correction C2 — Absolute gain: 0.043 → 0.042

**Priority: LOW** — minor rounding error; does not change the conclusion.

**Backing file:** `phase2_rebuild/results/tables/baseline.csv`
- hybrid_lr D1 F1 = 0.5114931
- rule D1 F1 = 0.4697108
- Difference = 0.0417823 → rounds to **0.042**, not 0.043

### Two locations to change:

| Location | Line (approx.) | Old text | New text |
|----------|----------------|----------|----------|
| Abstract | 63 | "absolute gain of 0.043 over the strongest single detector" | "absolute gain of 0.042 over the strongest single detector" |
| Section IV-A | 707 | "stacker improves F1 by 0.043" | "stacker improves F1 by 0.042" |

---

## Correction C3 — AST-equivalence difficulty: medium vs. hard

**Priority: MEDIUM** — the abstract currently misattributes the 0.738 value.

**Backing file:** `phase2_rebuild/results/tables/sql_migration_by_difficulty.csv`

| difficulty | ast_equiv_rate |
|------------|---------------|
| easy | 0.9211 |
| medium | **0.7385** |
| hard | **0.7421** |

The abstract says "degrades from 0.921 on easy queries to 0.738 on hard ones."
The value 0.738 is the *medium* rate; the *hard* rate is 0.742 (actually higher than medium).

### Suggested replacement (abstract line 74):

Old: "...degrades from 0.921 on easy queries to 0.738 on hard ones"

New: "...degrades from 0.921 on easy queries to 0.739 on medium-difficulty and 0.742 on hard queries"

(Use 0.739 = round(0.7385, 3) and 0.742 = round(0.7421, 3))

---

## Correction C4 — Per-family recall list: A5 → B1

**Priority: MEDIUM** — the body text incorrectly characterises which families exceed 0.93.

**Backing file:** `phase2_rebuild/results/tables/per_family.csv`

| family | recall | paper claim | status |
|--------|--------|-------------|--------|
| A4_period_violation | 0.9440 | listed as >0.93 | correct |
| A5_duplicate_posting | **0.9180** | listed as >0.93 | **WRONG** — 0.918 < 0.93 |
| B1_ot_regular_inconsistency | **0.9435** | NOT listed | **MISSING** — 0.9435 > 0.93 |
| B2_salary_basis_mismatch | 0.9935 | listed as >0.93 | correct |
| C1_education_out_of_domain | 1.0000 | listed as >0.93 | correct |
| C5_age_range_violation | 1.0000 | listed as >0.93 | correct |

### Location to change:

| Location | Line (approx.) | Old text | New text |
|----------|----------------|----------|----------|
| Section IV-B | 765 | "Five families exceed 0.93 recall: A4, **A5**, B2, C1, C5" | "Five families exceed 0.93 recall: A4, **B1**, B2, C1, C5" |

The count (five families) remains correct. Only A5 is replaced by B1.

---

## Correction C5 — Ablation claim: LOF least damaging "everywhere"

**Priority: LOW** — the claim is true for D1 and D2 but false for D3.

**Backing file:** `phase2_rebuild/results/tables/ablation.csv`

| dataset | leave_out | f1 | delta_from_full |
|---------|-----------|-----|----------------|
| D3 | none | 0.7172 | 0 |
| D3 | lof | 0.7061 | **+0.011** |
| D3 | iforest | 0.7252 | **−0.008** |

On D3, removing LOF raises F1 by 0.011 (LOF hurts slightly on D3), while removing iforest
costs only 0.008 F1. So "least damaging" on D3 is iforest removal, not LOF removal.

### Location to change:

| Location | Line (approx.) | Old text | New text |
|----------|----------------|----------|----------|
| Section IV-D | 817 | "removing LOF is the least damaging everywhere" | "removing LOF is the least damaging on D1 and D2; on D3, IsolationForest contributes only 0.008 F1, marginally less than LOF's 0.011 impact" |

---

## Summary of all corrections

| # | Correction | Priority | Lines affected | Metric change? |
|---|-----------|----------|----------------|----------------|
| C1 | 109 → 115 queries | HIGH | 70, 283, 680, 913, 1138 | No (descriptive only) |
| C2 | 0.043 → 0.042 gain | LOW | 63, 707 | Yes (rounding fix) |
| C3 | 0.738 is medium not hard | MEDIUM | 74 | Yes (attribution fix) |
| C4 | A5 → B1 in recall list | MEDIUM | 765 | No (correct families) |
| C5 | LOF "everywhere" → D1/D2 only | LOW | 817 | No (scope qualification) |

All five corrections are supported by committed files in `phase2_rebuild/results/tables/`
with SHA-256 hashes listed in `MANIFEST.json`. No detection performance metric has changed.
