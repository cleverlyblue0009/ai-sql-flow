# DataFlow AI v2 — Reproducibility Report

**Generated:** Phase 3 final pass.
**Repository state:** `phase2_rebuild/` is self-contained from raw download through paper output.

---

## 1. Headline numbers (all computed from real public datasets, single seed)

### Anomaly detection (D1 / D2 / D3, F1 at best threshold)

| Detector       | D1 (SEC EDGAR) | D2 (NYC Payroll) | D3 (UCI Credit) |
|----------------|---------------:|-----------------:|----------------:|
| rule           | 0.470          | 0.341            | 0.700           |
| stat           | 0.158          | 0.134            | 0.185           |
| iforest        | 0.427          | 0.361            | 0.614           |
| lof            | 0.146          | 0.104            | 0.100           |
| hybrid (fixed) | 0.368          | 0.366            | 0.698           |
| **hybrid_LR**  | **0.511**      | 0.359            | **0.717**       |

### SQL transpilation (109 queries × 5 dialects = 575 pairs)

| Metric                | Value |
|-----------------------|------:|
| Parse rate            | 0.991 |
| Transpile rate        | 0.991 |
| **AST-equivalence**   | **0.800** |
| Mean latency (ms)     | 1.09  |
| P95 latency (ms)      | 2.51  |

**Tripwire (≥0.99) fired on parse/transpile.** Reported honestly in §VII-B of the paper.
The substantive metric (AST equivalence) is 0.800 — well below the threshold and degrades to 0.742 on
hard queries, exposing where mature transpilers actually break.

---

## 2. Determinism contract

- **Seed.** `SEED = 42` everywhere; child RNGs derived as
  `int.from_bytes(sha256(f"{SEED}::{name}").digest()[:8], "big")`.
- **Raw data.** SHA-256-verified at download (`phase2_rebuild/data/raw/checksums.json`).
- **Injected datasets.** SHA-256 verified to bit-identical reproduction across re-runs:
  - `D1_injected.parquet`: `6b706b30a22a7e4a...`
  - `D2_injected.parquet`: `2cded7ccf704cf66...`
  - `D3_injected.parquet`: `b1a4866287aa55c7...`
  - All three label masks verified identically.
- **Stacker.** Sklearn `LogisticRegression(class_weight='balanced', solver='liblinear', random_state=42)`
  inside a `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`.

---

## 3. Environment

- **Python:** 3.14.3, venv at `venv/`
- **Key versions:** sklearn 1.8.0, pandas 2.3 (current at run-time),
  numpy (current), pyarrow 24.0.0, matplotlib 3.10.9, seaborn 0.13.2, scipy 1.17.1,
  sqlglot 30.8.0, python-calamine (for `.xls` parsing).
- **Hardware:** single CPU core, Windows 11.

---

## 4. End-to-end run

```powershell
# 1. Download + verify raw datasets (SEC EDGAR, NYC payroll, UCI credit)
python phase2_rebuild/scripts/00_download_datasets.py

# 2. Extract + deterministic sampling -> parquet
python phase2_rebuild/scripts/01_extract_and_sample.py

# 3. Inject 15 anomaly families (bit-identical)
python phase2_rebuild/scripts/02_inject_anomalies.py

# 4. Run anomaly experiments (5 detectors + hybrid + hybrid_LR; CV, ablation, sweep, scalability)
python phase2_rebuild/scripts/10_run_anomaly_experiments.py

# 5. Generate all figures (PR, threshold, confmat, scalability, per-family, ablation, SQL matrix)
python phase2_rebuild/scripts/20_generate_figures.py

# 6. SQL migration experiments (575 source-target pairs)
python phase2_rebuild/scripts/30_run_sql_migration.py

# 7. Audit paper
python phase2_rebuild/scripts/40_audit_paper.py

# 8. Compile paper (LaTeX + bibtex)
cd paper
pdflatex dataflow_ai_v2 ; bibtex dataflow_ai_v2 ; pdflatex dataflow_ai_v2 ; pdflatex dataflow_ai_v2
```

---

## 5. Output artefacts

```
phase2_rebuild/results/
  tables/
    baseline.csv                  # 18 rows: 6 detectors × 3 datasets
    per_family.csv                # 15 rows: family-level recall
    cv.csv                        # 15 rows: 5 folds × 3 datasets
    ablation.csv                  # 15 rows: leave-one-out × 3 datasets
    threshold_sweep.csv           # ~72 rows: 24 quantiles × 3 datasets
    scalability.csv               # 4 rows: D2 at 10k/50k/100k/200k
    sql_migration_per_query.csv   # 575 rows
    sql_migration_matrix.csv      # 25 source-target cells
    sql_migration_by_difficulty.csv
    sql_migration_by_complexity.csv
    sql_migration_summary.csv
  figures/
    fig2_pr_curves.{pdf,png}
    fig3_confmat.{pdf,png}
    fig4_threshold_sweep.{pdf,png}
    fig5_scalability.{pdf,png}
    fig6_perfamily.{pdf,png}
    fig7_ablation.{pdf,png}
    fig8_sql_matrix.{pdf,png}
  audits/
    citation_audit.txt
    metric_occurrences.csv
    xref_audit.csv
    summary.md
paper/
  dataflow_ai_v2.tex   # main paper, references all figures and tables
  references.bib       # 43 entries
```

---

## 6. Known limitations (matches §VII of the paper)

1. **Anomaly families are injected, not field-discovered.** Per-family recall is reported so
   practitioners can re-weight to their domain.
2. **Only three datasets.** Chosen for domain diversity and licence clarity, not exhaustive coverage.
3. **SQL corpus is curated.** Dialect-specific failure modes are over-represented in
   Fig. 8 — read as worst-case rather than expected production rate.
4. **Hardware sensitivity not characterised.** All timings on a single CPU core.

---

## 7. Audit summary

- Bib entries: 43 (target ≥30 ✓)
- Cited unique keys: 41 of 43
- Missing from bib: 0
- Cross-references: 34 labels; 9 section labels not back-referenced (normal for IEEE format)
- Numeric literals in paper: 75 `\num{}` values
- Tripwire fires: parse/transpile = 0.9913 (acknowledged in §VII-B)

No metric in the body exceeds the 0.99 tripwire for anomaly detection. AST equivalence (0.800) is
the recommended metric for SQL transpilation evaluation.
