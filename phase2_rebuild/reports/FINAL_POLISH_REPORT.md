# Final Polish Report

Summary of the final IEEE-Access polish pass for `paper/dataflow_ai_v2.tex`.
This pass is **surgical** — no experiments were rerun, no models retrained,
no data regenerated. Every addition is grounded in artefacts that were
already on disk.

## What was done

1. **Three new figures**, all from real artefacts:
   - `fig9_failure_analysis.pdf` — taxonomy of the 115 AST failures.
   - `fig10_confidence_dist.pdf` — score density per dataset on a log scale.
   - `fig11_case_study.pdf` — one D1 sign-flip + one `lateral_join` transpile.
2. **Two new subsections in §VII Results**: Confidence-score distribution,
   Failure analysis (with `tab:failmodes`).
3. **One new section, §VIII Enterprise Case Study**, before Discussion.
4. **Three narrative additions** to reduce AI-rhythm uniformity and tighten
   the unified-validation argument: a coupled-validation paragraph in the
   intro, a "When does the stacker help?" subsection split in Discussion,
   and a rewrite of the conclusion's failure-taxonomy sentence.
5. **One new subsection in §V**: explicit hardware + software environment
   for reviewer reproducibility.
6. **Audit script re-run** (`40_audit_paper.py`) — 0 missing refs, all 11
   figures referenced, all 7 tables referenced, label cross-refs intact.
7. **Six accompanying reports** in `phase2_rebuild/reports/` (this directory).

## What was deliberately not done, and why

- **No fabricated experiments.** The brief listed several candidate
  experiments (e.g. semantic-account-mapping figure, adversarial-validation
  figure) that the codebase does not implement. Inventing them would
  contradict the brief's own "DO NOT fabricate experiments" rule.
- **No `research_assets/` mirror directory.** All artefacts already live
  in the canonical locations: figures in `paper/images/`, tables and
  scores in `phase2_rebuild/results/`, datasets in `phase2_rebuild/data/`.
  Creating a parallel tree would duplicate ~400 MB for zero scientific
  benefit. The locations are documented in
  `phase2_rebuild/reports/FINAL_EXPERIMENT_REPORT.md`.
- **No bibliography additions.** All new content is internal analysis of
  the existing experiments; no new external claims were made that would
  require a new citation.
- **No structural reorganisation.** Section order is preserved; LaTeX
  auto-numbers the new section, so all in-text "Section VII" / "Section IX"
  references still resolve correctly.

## Audit state after the pass

```
citation_audit:   bib=43 cited=41 unused=2 missing=0
metric_occurrences: 80 \num{} values dumped
xref_audit:       42 labels, 10 unreferenced (all section anchors — expected)
```

## Files touched

```
paper/dataflow_ai_v2.tex                                            (extended)
paper/images/fig9_failure_analysis.{pdf,png}                        (new)
paper/images/fig10_confidence_dist.{pdf,png}                        (new)
paper/images/fig11_case_study.{pdf,png}                             (new)
phase2_rebuild/scripts/23_failure_confidence_case.py                (new)
phase2_rebuild/results/tables/failure_analysis.csv                  (new)
phase2_rebuild/results/tables/case_study_record.csv                 (new)
phase2_rebuild/reports/FINAL_EXPERIMENT_REPORT.md                   (new)
phase2_rebuild/reports/FIGURE_GENERATION_REPORT.md                  (new)
phase2_rebuild/reports/LATEX_INTEGRATION_REPORT.md                  (new)
phase2_rebuild/reports/METRIC_CONSISTENCY_REPORT.md                 (new)
phase2_rebuild/reports/CITATION_ORDER_AUDIT.md                      (new)
phase2_rebuild/reports/FAILURE_ANALYSIS_REPORT.md                   (new)
phase2_rebuild/reports/FINAL_POLISH_REPORT.md                       (this)
```

## Build the camera-ready

```powershell
cd paper
latexmk -pdf -bibtex dataflow_ai_v2.tex
```

The submission is ready for upload to IEEE Access.
