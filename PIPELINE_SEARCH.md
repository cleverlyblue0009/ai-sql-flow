# DataFlow AI Pipeline Search Report
Generated: 2026-07-11

---

## 1. VERDICT: **FOUND**

The complete DataFlow AI pipeline is intact, committed to git, and already pushed to GitHub. Nothing needs to be regenerated or recovered from deleted-file paths.

---

## 2. Ranked Candidates

### Candidate 1 — Pipeline (PRIMARY)
**Path:** `C:\Users\UPASANA\ai-sql-flow\phase2_rebuild\`
**What it is:** The complete experiment pipeline — all ten numbered Python scripts, three raw corpora, injection manifest with SHA-256 hashes, anomaly masks, processed/injected datasets, scorer outputs, result tables, and figures fig1–fig8.
**Git status:** Committed in `research-experiments-ieee-access` branch, commit `0baecc3 "Commit current workspace changes"`. Remote `origin/research-experiments-ieee-access` is at the same commit (already pushed).
**Last modified:** 2026-05-27

**Fingerprints matched:**
- `SEED = 42` ✓ (`02_inject_anomalies.py:36`, `10_run_anomaly_experiments.py:50`)
- `42::` seeding — `f"{SEED}::{name}"` ✓ (`02_inject_anomalies.py:42`)
- `1.4826` MAD constant ✓ (`10_run_anomaly_experiments.py:112,154,224`)
- `IsolationForest(n_estimators=200, contamination="auto")` ✓ (line 231)
- `LocalOutlierFactor` ✓ (line 241)
- `LogisticRegression(class_weight="balanced")` ✓ (line 263)
- `hybrid_lr` detector ✓ (multiple scripts)
- A1–A5 families (SEC EDGAR): `A1_sign_flip`, `A2_magnitude_outlier`, `A3_tag_mismatch`, `A4_period_violation`, `A5_duplicate_posting` ✓
- B1–B5 families (NYC Payroll): `B1_ot_regular_inconsistency`, `B2_salary_basis_mismatch`, `B3_near_duplicate_name`, `B4_agency_title_violation`, `B5_magnitude_outlier` ✓
- C1–C5 families (UCI Credit): `C1_education_out_of_domain`, `C2_limitbal_inconsistency`, `C3_bill_sign_violation`, `C4_pay_temporal_violation`, `C5_age_range_violation` ✓
- `sqlglot` ✓ (`30_run_sql_migration.py:27-28`)
- `_ast_footprint`, `ast_equiv`, `transpile` ✓ (`30_run_sql_migration.py:86-195`)
- SHA-256 hashes in injection manifest ✓ (`data/injection_manifest.json`)
- **Total anomalies: 13,998 / 282,500 rows ✓** (D1: 2,498/50,500; D2: 10,000/202,000; D3: 1,500/30,000 — matches paper exactly)

---

### Candidate 2 — LaTeX Manuscript (PRIMARY)
**Path:** `C:\Users\UPASANA\Downloads\DATAFLOW\`
**What it is:** Complete LaTeX manuscript package — `DataFlow.tex` (63KB), `DATAFLOW.pdf` (4.0MB), `ieeeaccess.cls`, `IEEEtran.cls`, `FINAL_BIBLIOGRAPHY.bib`, and all **eleven** figures (`fig1_architecture.png` through `fig11_case_study.png`).
**Last modified:** 2026-07-11 (today — most recently touched artifact)

**Fingerprints matched:**
- `ieeeaccess.cls` ✓
- `sqlglot` ✓ (lines 276, 346, 423, 555, 897)
- `1.4826` ✓ (line 482)
- `footprint` / `ast_footprint` / `AST-footprint equivalence` ✓ (lines 73, 181, 593, 696, 938)
- `42::` seed derivation ✓ (line 603)
- `adsh` (SEC EDGAR duplicate-posting field) ✓ (line 478)
- `num.txt` ✓ (line 624)
- D1 = SEC EDGAR, D2 = NYC Payroll FY2024, D3 = UCI Credit Default ✓
- All 11 figures present ✓

**Note on "Merge 3" / FINAL.tex:** The paper uses neither name. The TeX file is `DataFlow.tex`; the PDF is `DATAFLOW.pdf`. No `FINAL.tex` on disk. The "Merge 3" working title was apparently not preserved in any filename.

---

### Candidate 3 — Older research_assets (NOT the DataFlow pipeline — discard)
**Path:** `C:\Users\UPASANA\Downloads\research_assets\`
**Last modified:** 2026-05-27

This is from the older `research-experiments-ieee-access` system (Gemini-based SQL translation, mock financial CSVs, F1=0.3212, RANDOM_SEED=42 but no 42:: seeding, no EDGAR/Payroll/UCI). Does **not** match the DataFlow fingerprints. Discarded as old-version noise per search instructions.

---

## 3. Coverage Map

| Artefact | Present? | Path |
|---|---|---|
| **extract stage** (`00_download_datasets.py`, `01_extract_and_sample.py`) | ✓ YES | `phase2_rebuild/scripts/00_*.py`, `01_*.py` |
| **inject stage** (`02_inject_anomalies.py`) | ✓ YES | `phase2_rebuild/scripts/02_inject_anomalies.py` |
| **score stage** (`10_run_anomaly_experiments.py`) | ✓ YES | `phase2_rebuild/scripts/10_run_anomaly_experiments.py` |
| **ablate stage** (inside `10_run_anomaly_experiments.py`) | ✓ YES | same script; `results/tables/ablation.csv` produced |
| **sweep stage** (inside `10_run_anomaly_experiments.py`) | ✓ YES | same script; `results/tables/threshold_sweep.csv` produced |
| **transpile stage** (`30_run_sql_migration.py`) | ✓ YES | `phase2_rebuild/scripts/30_run_sql_migration.py` |
| **render stage** (`20_`, `21_`, `22_`, `23_` scripts) | ✓ YES | `phase2_rebuild/scripts/20_*.py` through `23_*.py` |
| **Raw corpus D1 — SEC EDGAR `2024q4.zip`** | ✓ YES | `phase2_rebuild/data/raw/sec_edgar/2024q4.zip` (123MB) |
| **Raw corpus D2 — NYC Payroll CSV** | ✓ YES | `phase2_rebuild/data/raw/nyc_payroll/citywide_payroll.csv` (958MB) |
| **Raw corpus D3 — UCI Credit ZIP** | ✓ YES | `phase2_rebuild/data/raw/uci_credit_default/default_of_credit_card_clients.zip` (5.5MB) |
| **Injected datasets** | ✓ YES | `data/processed/D1_injected.parquet`, `D2_injected.parquet`, `D3_injected.parquet` |
| **Anomaly masks** (parquet, not .npy) | ✓ YES | `data/labels/D1_mask.parquet`, `D2_mask.parquet`, `D3_mask.parquet` |
| **Injection manifest + SHA-256 hashes** | ✓ YES | `data/injection_manifest.json` |
| **Score outputs** | ✓ YES | `results/scores/D1_scores.parquet` (2.1MB), `D2_scores.parquet` (7.2MB), `D3_scores.parquet` (1.5MB) |
| **Result tables (Tables 5–11)** | ✓ YES | `results/tables/`: `baseline.csv`, `cv.csv`, `per_family.csv`, `ablation.csv`, `threshold_sweep.csv`, `scalability.csv`, `sql_migration_matrix.csv`, `sql_migration_by_complexity.csv`, `sql_migration_by_difficulty.csv`, `failure_analysis.csv` |
| **Figures fig1–fig8** | ✓ YES | `phase2_rebuild/results/figures/` (PNG+PDF, 300 DPI) |
| **Figures fig9–fig11** | ✓ YES (manuscript only) | `Downloads/DATAFLOW/figures/fig9_failure_analysis.png`, `fig10_confidence_dist.png`, `fig11_case_study.png` — generated by `23_failure_confidence_case.py` but **not** saved back to `results/figures/` |
| **LaTeX source (`DataFlow.tex`)** | ✓ YES | `Downloads/DATAFLOW/DataFlow.tex` |
| **Compiled PDF** | ✓ YES | `Downloads/DATAFLOW/DATAFLOW.pdf` (4.0MB) |
| **`ieeeaccess.cls`** | ✓ YES | `Downloads/DATAFLOW/ieeeaccess.cls` |
| **`FINAL.tex` / "Merge 3"** | ✗ NOT FOUND | No file by this name exists on disk. The TeX file is named `DataFlow.tex`. |

---

## 4. Recoverable-but-Deleted

**Nothing needs to be recovered from git dangling objects, VS Code history, Recycle Bin, or transcripts.** Everything is live on disk and in git.

- Git dangling objects: `git fsck --lost-found` in the repo would reveal any, but unnecessary — HEAD at `0baecc3` is clean and complete.
- VS Code local history (884 files at `%APPDATA%\Code\User\History`): not searched in detail because the pipeline was found complete in git. Available as fallback if any specific file is needed.
- Claude Code transcripts: the single JSONL for this project is 60KB (the current conversation). No large prior session transcript for the DataFlow build was found.
- The large C--Users-UPASANA transcripts (12.4MB, 3.3MB) were not searched for fingerprints — available as fallback.

---

## 5. Dead Ends

| Location | What was checked | Result |
|---|---|---|
| `~/.claude/projects/**/*.jsonl` (large files) | Listed all; the ai-sql-flow project JSONL is 60KB | No prior session transcript for DataFlow build |
| `~/research`, `~/ieee`, `~/dataflow`, etc. | Directory name scan across all of `C:\Users\UPASANA` | No separate working dirs found (pipeline lives inside `ai-sql-flow/phase2_rebuild`) |
| Anomaly masks as `.npy` | Glob `*mask*.npy` | None; masks are in `.parquet` format |
| `FINAL.tex` / "Merge 3" filename | Full file system name search | Not found; manuscript is `DataFlow.tex` |
| Downloads `research_assets/` | Listed all files | Old version (RANDOM_SEED=42, mock data, no EDGAR/Payroll/UCI) — discard |
| Browser download history | SQLite at `%LOCALAPPDATA%\Google\Chrome\User Data\Default\History` or Edge equivalent — **not read** because the data files are already on disk | If you need to confirm download provenance, run: `Copy-Item "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\History" "$env:TEMP\edge_history.db" -Force` then open with any SQLite viewer |
| Recycle Bin (`C:\$Recycle.Bin`) | Not scanned — unnecessary since pipeline is complete in git | Skip |
| Jupyter notebooks | Not found in home dir scan | None present |
| Berka dataset (`phase2_rebuild/data/raw/berka/`) | Present on disk but not referenced by paper fingerprints | Appears to be a development artifact; not part of the paper's three corpora |

---

## 6. Files Copied to `~/dataflow_recovered/`

```
dataflow_recovered/
├── pipeline/
│   ├── scripts/
│   │   ├── 00_download_datasets.py
│   │   ├── 01_extract_and_sample.py
│   │   ├── 02_inject_anomalies.py      ← SEED=42, 42:: seeding, A1-C5 families
│   │   ├── 10_run_anomaly_experiments.py ← 1.4826, IsolationForest 200, LOF, LR
│   │   ├── 20_generate_figures.py
│   │   ├── 21_generate_large_figures.py
│   │   ├── 22_generate_architecture.py
│   │   ├── 23_failure_confidence_case.py ← generates fig9, fig10, fig11
│   │   ├── 30_run_sql_migration.py     ← sqlglot, ast_footprint, ast_equiv
│   │   └── 40_audit_paper.py
│   ├── data/
│   │   ├── injection_manifest.json     ← SHA-256 hashes for all masks+data
│   │   ├── extract_manifest.json
│   │   ├── download_manifest.json
│   │   ├── labels/
│   │   │   ├── D1_mask.parquet         ← 2,498 anomaly rows
│   │   │   ├── D2_mask.parquet         ← 10,000 anomaly rows
│   │   │   └── D3_mask.parquet         ← 1,500 anomaly rows
│   │   └── processed/
│   │       ├── D1_sec_gl.parquet       ← pre-injection SEC EDGAR sample
│   │       ├── D1_injected.parquet
│   │       ├── D2_nyc_fy2024.parquet
│   │       ├── D2_injected.parquet
│   │       ├── D3_uci_credit.parquet
│   │       └── D3_injected.parquet
│   ├── results/
│   │   ├── figures/                    ← fig1–fig8 (PNG + PDF)
│   │   ├── tables/                     ← baseline, cv, per_family, ablation,
│   │   │                                   threshold_sweep, scalability,
│   │   │                                   sql_migration_*, failure_analysis
│   │   ├── scores/                     ← D1/D2/D3_scores.parquet
│   │   └── audits/
│   ├── anomaly_injection_plan.md
│   ├── results_manifest.md
│   ├── experiment_log.md
│   ├── reproducibility_report.md
│   └── (report .md files from phase2_rebuild/reports/)
└── manuscript/
    ├── DataFlow.tex                    ← complete LaTeX source (63KB)
    ├── DATAFLOW.pdf                    ← compiled PDF (4.0MB)
    ├── FINAL_BIBLIOGRAPHY.bib
    ├── ieeeaccess.cls
    ├── IEEEtran.cls
    ├── bullet.png, logo.png, notaglinelogo.png
    └── figures/
        ├── fig1_architecture.png       ← all 11 figures, 300 DPI
        ├── fig2_pr_curves.png
        ├── ...
        ├── fig10_confidence_dist.png
        ├── fig11_case_study.png
        └── author_upasana.png, author_berlin.png
```

**NOT copied (large raw data — already safe in git):**
- `phase2_rebuild/data/raw/sec_edgar/2024q4.zip` — 123MB, at `C:\Users\UPASANA\ai-sql-flow\phase2_rebuild\data\raw\sec_edgar\2024q4.zip`
- `phase2_rebuild/data/raw/nyc_payroll/citywide_payroll.csv` — 958MB, at `C:\Users\UPASANA\ai-sql-flow\phase2_rebuild\data\raw\nyc_payroll\citywide_payroll.csv`
- `phase2_rebuild/data/raw/uci_credit_default/default_of_credit_card_clients.zip` — 5.5MB, at `C:\Users\UPASANA\ai-sql-flow\phase2_rebuild\data\raw\uci_credit_default\default_of_credit_card_clients.zip`

---

## 7. Git Recovery (if needed in future)

The pipeline is fully committed and pushed. To restore from scratch:

```bash
git clone https://github.com/cleverlyblue0009/ai-sql-flow.git
cd ai-sql-flow
git checkout research-experiments-ieee-access
# pipeline is at phase2_rebuild/
```

To verify the injection manifest checksums:
```python
import hashlib, json, pathlib
manifest = json.load(open("phase2_rebuild/data/injection_manifest.json"))
for ds, info in manifest["datasets"].items():
    h = hashlib.sha256(pathlib.Path(info["data_path"]).read_bytes()).hexdigest()
    print(ds, "DATA", "OK" if h == info["data_sha256"] else "MISMATCH", h)
```
