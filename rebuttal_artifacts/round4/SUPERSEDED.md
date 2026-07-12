# SUPERSEDED artefacts — Round 4

This file records which prior artefacts are superseded by Round 4 outputs.
Prior artefacts are NOT deleted; they remain at their original paths for audit.

| superseded artefact | superseded by | reason |
|:--------------------|:--------------|:-------|
| `round1/` — all baseline tables with hybrid_lr | `round4/r41_xgb_pipeline/baseline_xgb.csv` | XGB adopted as primary stacker |
| `round2/f2_metalearner/` | `round4/r41_xgb_pipeline/` | XGB OOF now canonical stacker |
| `round2/f3_deep_svdd/` | `round4/r42_downstream/modern_baselines_vs_xgb.csv` | Superseded by full pyod baseline comparison |
| `round2/f4_prevalence_drift/` | `round4/r43_correlated/` | Correlated injection is a more complete robustness test |
| `round2/f5_ast_execution/` | `round4/r45_ast/` | Round 4 adds relaxed comparator and richer synthetic schema |
| `round3/f1b_joint_gate/` (analyst_cost) | `round4/r42_downstream/analyst_cost_xgb.csv` | XGB tau* used in place of LR tau* for fair comparison |
| Any table citing hybrid_lr as primary detector | Corresponding `*_xgb.csv` in round4 | XGB is now the reported system |

## What is NOT superseded

- `round3/f1b_joint_gate/` per-query magnitude CSVs — still the canonical magnitude analysis (used as reference in R4.2-B)
- `round3/ROUND3_SUMMARY.md` — joint gate design decisions remain valid
- `round1/` raw results — retained as historical record
- `round2/` F1/F5 methodology — F1b (round3) and R4.5 (round4) extend but don't invalidate
