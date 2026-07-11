# Phase 2 Rebuild — Workspace Overview

This directory contains the rebuild pipeline that replaces the previous
synthetic-only evaluation in the DataFlow AI IEEE Access submission with
results computed on real public data.

**This directory is the single source of truth for the rebuild.**
The legacy paper lives at `paper/dataflow_ai_legacy.tex` and is read-only.
The rebuilt paper will be written to `paper/dataflow_ai_v2.tex` in Phase 4.

## Phase status

| Phase | Scope | Status |
|---|---|---|
| 1 | Dataset acquisition + provenance + injection plan | **complete** |
| 2 | Extraction + sampling + anomaly injection + label files | not started |
| 3 | Re-run all metrics, ablation, CV, scalability, threshold sweeps, PR curves | not started |
| 4 | Regenerate all figures + rewrite IEEE Access .tex against new results | not started |
| 5 | Citation audit + metric-consistency audit + reproducibility report | not started |

## Where to look

- **What datasets and why** → [`dataset_registry.md`](dataset_registry.md)
- **What anomalies, where, and how** → [`anomaly_injection_plan.md`](anomaly_injection_plan.md)
- **Full audit trail of every action** → [`experiment_log.md`](experiment_log.md)
- **Every promised artefact + its current status** → [`results_manifest.md`](results_manifest.md)
- **Download script (real public sources only)** → [`scripts/00_download_datasets.py`](scripts/00_download_datasets.py)
- **Download manifest with SHA256 + sizes** → `data/download_manifest.json`

## Non-negotiable rules carried into every phase

1. No fabricated metrics. Every number in the rebuilt paper traces to a script
   in this directory and a real file on disk.
2. No invented citations. Gaps remain marked `[CITATION NEEDED]`.
3. Raw datasets are never mutated. Anomaly injection writes new processed
   files + parquet label masks under `data/processed/` and `data/labels/`.
4. Random seed is fixed at `42` everywhere (NumPy, generators, scikit-learn).
5. Suspiciously perfect metrics (≥ 99 %) are a stop condition. If a run
   produces them, the run is investigated, not published.

## Reproducing Phase 1 from scratch

```powershell
# from repo root, in the project venv:
python phase2_rebuild\scripts\00_download_datasets.py
```

Expected exit code: `0`. Expected manifest: see SHA256 values in
[`experiment_log.md`](experiment_log.md) under the 2026-05-27 entry.
