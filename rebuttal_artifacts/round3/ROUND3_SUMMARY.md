# Round-3 Rebuttal Summary — Access-2026-28181

**Status**: F1b complete. Round-3 supersedes F1 (round-2) on the joint-gate question.

---

## ONE-LINE VERDICTS

**F1b (Joint gate — magnitude metric, R2.4 deciding comment)**:
> **The analyst-audit (repaired) model dominates all gate configurations.**  
> Median relative error: dirty=0.0105, cleansed=0.1429, repaired=0.0010, coupled=0.0105.  
> Cleansed is 14× worse than dirty (selection bias from FP row removal). Repaired is 11× better than dirty (FP harm reversed by audit). Coupling provides no additional gain over repaired.

---

## Why round-3 exists — what F1 got wrong

F1 (round-2) fixed E6's circular reference by making the reference gate-independent (true pre-injection table). **But F1 scored every condition with a binary `is_error` flag**, which made its verdict an artifact:

Under row-deleting quarantine, ANY aggregate over 28,212 rows ≠ the same aggregate over 30,000 rows, even with a perfect detector. F1's 91.4% "error" rate measured "rows were deleted", not "the gate failed". F1b replaces the binary flag with relative-error magnitude, adds the repaired condition (the deployment the paper actually describes), adds a coupled gate, and fixes the 2-hop transpilation to single-hop.

---

## F1b — Fixes applied

| Fix | Before (F1) | After (F1b) |
|---|---|---|
| Metric | Binary `is_error` → predetermines answer | `rel_err = |a−r|/max(|r|, ε)` per query |
| Repaired condition | Missing | C5/C6: quarantined rows restored to true pre-injection values |
| Coupled gate | Not tested | C7: column-provenance reinstatement per query |
| Transpilation | 2-hop postgres→tsql→duckdb | Single-hop postgres→duckdb |

---

## F1b — Key numbers

**35 queries × 8 conditions. All results in f1b_per_query_all_conditions.csv.**

| Condition | Data | Median rel-err | p90 | Materiality >1% |
|---|---|---|---|---|
| C1 dirty+source (SQL gate) | dirty | 0.010477 | 1.000 | 57.1% |
| C2 dirty+transpiled (no gate) | dirty | 0.010477 | 1.000 | 57.1% |
| C3 cleansed+source (joint gate) | deletion | 0.142857 | 1.000 | 82.9% |
| C4 cleansed+transpiled (data gate) | deletion | 0.142857 | 1.000 | 82.9% |
| **C5 repaired+source** | audit | **0.000988** | 0.750 | **31.4%** |
| C6 repaired+transpiled | audit | 0.000988 | 0.824 | 31.4% |
| C7 coupled+source | col-aware | 0.010477 | 1.000 | 51.4% |

### Selection bias on control queries (safe columns never perturbed)

| Condition | Control median rel-err | vs dirty |
|---|---|---|
| C1 dirty+source | **0.000000** | reference |
| C3 cleansed+source | **0.097628** | **+9.8pp — worse than dirty** |
| C5 repaired+source | **0.000000** | same as dirty |
| C7 coupled+source | **0.000000** | same as dirty |

Cleansed D3 is missing 609 FP rows (16.7% of quarantine is FP, but 609/30,000 = 2.0% of the full table). Even 2% row removal biases all aggregates on uncorrupted columns. Verified on C09 (SEX distribution), C10 (MARRIAGE distribution), C13 (default payment distribution): cleansed Jaccard=0 (row set mismatch), dirty=exact match.

### Analyst cost

| Dataset | Queue size | TPs | FPs | FP fraction | FNs escaped |
|---|---|---|---|---|---|
| D2 (NYC Payroll) | 24,803 | 6,247 | 18,556 | **74.8%** | 3,753 |
| D3 (UCI Credit) | 1,788 | 1,179 | 609 | **34.1%** | 321 |

Three in four rows sent to D2 review are false alarms. Under deletion (C3), these 18,556 phantom removals bias every payroll aggregate.

---

## Three-line verdict for R2.4

**1. Does coupling reduce downstream relative error vs the better single gate?  NO**  
Best single gate is repaired (C5, median=0.000988). Coupled (C7, median=0.010477) does not beat it. Column-provenance reinstatement reinstates ~13,530 rows per query on average — but without true-value restoration, reinstated dirty rows reintroduce the original errors. Coupling alone (without analyst correction) provides no error reduction.

**2. Does quarantine-by-deletion introduce measurable selection bias into uncorrupted column aggregates?  YES**  
Magnitude = 0.097628 median relative error on control queries under cleansed vs 0.0 under dirty. Cleansed is definitively worse than the uncleaned table for queries that do not touch any corrupted column. This is the central factual finding: the paper's joint-gate claim is not only unproven — deletion actively harms downstream analytics on safe columns.

**3. What does the FP rate cost?**  
D2: 18,556 of 24,803 queued rows are innocent (74.8% FP rate). The "cleansed" payroll table has 22,803 fewer rows than the true table, of which 18,556 are phantom deletions. Every aggregate is biased by their absence. The analyst-audit model (C5) eliminates this bias: restoring FP rows to their true (unchanged) values returns safe-column aggregates to exact match, while FN-escaped rows contribute only their residual dirty error (C5 median=0.000988).

---

## Manuscript implications

| Claim | Status |
|---|---|
| "Joint gate reduces downstream query error" | **CONTRADICTED** — cleansed condition is 13.6× worse than dirty (magnitude) |
| "Coupling both gates provides additive benefit" | **NOT SUPPORTED** — coupled=dirty (0.010477) in this corpus |
| "The detection + migration pipeline protects downstream analytics" | **CONDITIONALLY TRUE** — only if quarantine leads to audit+repair (C5), not deletion (C3) |

**Do not resubmit until manuscript framing is changed**: the honest contribution is the audit-aware pipeline design — shared data lineage, quarantine-then-repair workflow, reproducible provenance. The deletion-based gate claim must be removed or scoped to contexts where FP rates are near zero.

---

## Outputs

| File | Contents |
|---|---|
| `f1b_per_query_all_conditions.csv` | 35 rows × all 8-condition metrics |
| `f1b_error_magnitude_distributions.csv` | Median/p90/max by condition × stratum |
| `f1b_materiality_sensitivity.csv` | % queries exceeding 0.1%/1%/5% at each condition |
| `f1b_coupled_gate_comparison.csv` | Coupled vs dirty/cleansed/repaired summary |
| `f1b_analyst_cost.csv` | Queue size, TP/FP/FN counts, FP fractions |
| `f1b_query_executions.json` | Full execution log for auditor review |
| `F1B_JOINT_GATE_REPORT.md` | Narrative report with opening three-liners |

**Script**: `phase2_rebuild/rebuttal/f1b_joint_gate.py`  
**Round-2 artifact superseded**: `rebuttal_artifacts/round2/f1_joint_gate/` (F1 binary-metric results remain for audit trail)
