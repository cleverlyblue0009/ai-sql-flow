# Experiment Log — Phase 2 Rebuild

> Chronological log of what was done, why, and what failed. Append-only. Each
> entry is dated UTC. This log is the audit trail referenced by
> `reproducibility_report.md` (Phase 5 deliverable).

---

## 2026-05-27 — Phase 1 — Scaffolding and dataset acquisition

**Goal.** Stand up `phase2_rebuild/` workspace, acquire real public datasets
to replace the synthetic ones used in the previous submission, and produce a
documented anomaly-injection plan ready for Phase 2 implementation.

**Decisions taken (with user input via the rebuild prompt).**

- Paper topic preserved: DataFlow AI (data quality + cross-dialect SQL translation).
  No pivot to financial-fraud detection.
- Execution mode: phased. Phase 1 deliverables only this iteration.
- Data sourcing: **no Kaggle**. Direct-download public sources only.
- Compute budget: heavy multi-hour runs permitted on local machine.
- Honesty rule: any gap must be marked `[DATASET NEEDED]` / `[CITATION NEEDED]`,
  never invented.

**Actions.**

1. Saved verbatim copy of the user-supplied LaTeX source to
   `paper/dataflow_ai_legacy.tex` (65,072 chars). This is the immutable
   baseline against which Phase 4 will rewrite.
2. Created `phase2_rebuild/` workspace with `data/`, `scripts/`, and
   per-phase markdown docs.
3. Authored `dataset_registry.md` with three candidate real datasets:
   - **D1** — SEC EDGAR Financial Statement Data Sets, 2024Q4.
   - **D2** — Berka 1999 Czech Bank Financial Dataset (PKDD'99). *Subsequently
     replaced; see failure log below.*
   - **D3** — UCI Default of Credit Card Clients (Yeh & Lien 2009).
4. Implemented `scripts/00_download_datasets.py` with SHA256 verification,
   per-file magic-byte validation, and JSON manifest output.
5. Ran the downloader.

**Failures encountered (recorded for honesty).**

- **D2 primary mirror failure.** `https://relational.fit.cvut.cz/dataset/financial/financial.zip`
  returned an 87 KB HTML landing page (first bytes `3c 21 44 4f` = `<!DO`),
  not the ZIP. The site no longer serves direct file downloads; it provides
  MariaDB dumps only.
- **D2 fallback mirror failure.** The community mirror
  `https://github.com/Mehrad0711/berka_dataset/raw/master/data.zip` returned HTTP 404.
- **Honest pivot.** Replaced D2 with **NYC Citywide Payroll Data**
  (`https://data.cityofnewyork.us/api/views/k397-673e/rows.csv?accessType=DOWNLOAD`),
  a robustly-hosted real public dataset whose schema admits the same anomaly
  families (duplicate names, period violations, OT/regular pay inconsistencies)
  that were planned for Berka. Decision recorded in
  `dataset_registry.md` ("Selection rationale" field of D2).
- **Downloader hardening.** Added `expected_magic` validation to
  `00_download_datasets.py` so HTML masquerading as a ZIP is rejected and the
  fallback URL is tried. Re-ran cleanly.

**Final Phase 1 artefacts on disk.**

| Path | Bytes | SHA256 |
|---|---:|---|
| `phase2_rebuild/data/raw/sec_edgar/2024q4.zip` | 122,932,548 | `9a2cbbaf39c94aa642b33d512f4def92b198d3bfd12d2267bcd27abe55b9902d` |
| `phase2_rebuild/data/raw/nyc_payroll/citywide_payroll.csv` | 958,741,176 | `a738275f04ea7d9d73c99f1757400faf94edc40b02bfc99f4c7abf2b888bf69a` |
| `phase2_rebuild/data/raw/uci_credit_default/default_of_credit_card_clients.zip` | 5,539,494 | `56c885f84457f6680f8438f02bfcdac9579323d8a94465ee5f26e32baa727602` |

**Schema spot-check (also part of Phase 1 evidence).**

- SEC `num.txt` header: `adsh\ttag\tversion\tddate\tqtrs\tuom\tsegments\tcoreg\tvalue\tfootnote`.
  Sample row is a real `NetIncomeLoss` posting against `RetainedEarnings`
  equity component for filing `0000950170-24-120982`, value `-20,331,000.00`.
- NYC Payroll has 17 columns including `Agency Name`, `Title Description`,
  `Base Salary`, `Regular Gross Paid`, `Total OT Paid`. Sample row: real
  ACS employee, Manhattan, "PROGRAM EVALUATOR", `$95,897` base.
- UCI Credit ZIP contains a single `.xls` file (5.5 MB). Note: `xlrd ≥ 2.0`
  no longer reads `.xls`; Phase 2 ingest must use `xlrd==1.2.0` or convert
  upstream. Open issue tracked in `anomaly_injection_plan.md`.

**Authored `anomaly_injection_plan.md`.** Five anomaly families per dataset,
~1 % per family, targeting **~5 % total injection rate** (down from 10–38 %
in the previous synthetic submission — closer to production rates and less
prone to artefact-driven recall inflation).

**Outstanding for Phase 2 (not started yet).**

- Implement `01_extract_and_sample.py` (parse SEC zip, slice NYC by FY2024, convert UCI XLS).
- Implement `02_inject_anomalies.py` per the plan.
- Persist parquet ground-truth masks under `data/labels/`.
- Pin dependencies in a `phase2_rebuild/requirements.txt` (Python 3.14 host
  confirmed; `xlrd==1.2.0` known issue).

**End of Phase 1.**

---

## 2026-05-27 — Phase 2 — Extraction, sampling, and anomaly injection

**Goal.** Convert the three raw downloads into clean per-dataset working
slices, then apply the deterministic anomaly injection documented in
`anomaly_injection_plan.md`. All outputs are reproducible bit-for-bit from
`SEED = 42`.

**Environment.** Python 3.14.3 (venv at `venv/`). Added `pyarrow==24.0.0`
(parquet I/O) and `python-calamine` (legacy `.xls` reader; replaces the
xlrd 1.2.0 path noted as an open issue at end of Phase 1 — `xlrd` 2.x in
this venv no longer reads `.xls`, so calamine was chosen instead of
downgrading a shared dependency).

**Actions.**

1. Wrote `scripts/01_extract_and_sample.py`:
   - D1: streamed `num.txt` from the SEC zip, filtered `uom == "USD"` and
     `qtrs ∈ {0,1}`, took the first 50,000 well-formed rows → `D1_sec_gl.parquet`.
   - D2: streamed the 959 MB NYC CSV in 300k-row chunks, kept `Fiscal Year == 2024`,
     then deterministic stratified sample by `Agency Name` to exactly 200,000 rows
     (seed = 42, proportional with rounding-delta repair) → `D2_nyc_fy2024.parquet`.
   - D3: read the UCI `.xls` via pandas + calamine engine, `header=1` to skip the
     `X1..X23` placeholder row, renamed first column to `ID` → `D3_uci_credit.parquet`.
2. Wrote `scripts/02_inject_anomalies.py`:
   - Per-family RNG derived from `SHA256("42::<family_name>")` for clean separation.
   - Eligibility filters used where the plan requires them (e.g. A1 only on
     non-negative GAAP tags with positive value; B1 only on rows with zero
     regular hours and zero OT; B2 only on `Pay Basis == "per Annum"` with
     `Base Salary > 10000`; C2 only on `default == 0` with `BILL_AMT1 > 0`).
   - Mask rows record `(row_index, anomaly_type, original_value, perturbed_value,
     injection_rng_seed)`.
3. Re-ran the injector after deleting outputs; SHA256s matched bit-for-bit on
   all six artefacts → idempotency confirmed.

**Failures encountered.**

- First D2 extraction run crashed on `DataFrameGroupBy.apply(include_groups=True)`
  (pandas 2.3+ removed the flag). Fixed with an explicit per-group `sample()` loop
  whose per-group random_state is drawn from the master RNG → still deterministic.
- First D2 injection run crashed in the `_one_char_perturb` helper because a few
  `Last Name` values were `NaN`. Replaced the `s + "X"` fallback with a fixed
  `"ANOMX"` sentinel so NaN inputs produce a deterministic perturbed string.

**Final Phase 2 artefacts on disk.**

| Path | Rows | Anomalies | Rate | SHA256 |
|---|---:|---:|---:|---|
| `data/processed/D1_injected.parquet` | 50,500 | 2,498 | 4.95 % | `6b706b30a22a7e4a0c04b19c645bb8a9e7cfd0293e33b79959b7d435af8f74ce` |
| `data/processed/D2_injected.parquet` | 202,000 | 10,000 | 4.95 % | `2cded7ccf704cf66d971897a6de8cc40af880f241e86e81cdab76ff39b71ad82` |
| `data/processed/D3_injected.parquet` | 30,000 | 1,500 | 5.00 % | `b1a4866287aa55c774e07f422b71a67bdcb2aed9369d5fd5fb889f23c0ef9f6f` |
| `data/labels/D1_mask.parquet` | 2,498 | — | — | `decbe04b3092b178888a78c6fd40abc805ad97e525d43686b8957134792586b7` |
| `data/labels/D2_mask.parquet` | 10,000 | — | — | `f6eedb0bf6e802a363c05941f99722a4ea718019032b3e615444db32461c545d` |
| `data/labels/D3_mask.parquet` | 1,500 | — | — | `052095445d966b71b616aaead10190197e36cf4d20dea3f75d0e4f55468d9dea` |

Side-files (regenerable, not under SHA256 contract): `data/extract_manifest.json`,
`data/injection_manifest.json` capture row counts, per-family counts, and timings.

**Per-family counts.**

- D1 SEC: A1 sign_flip 500 · A2 magnitude 500 · A3 tag_mismatch 498 · A4 period 500 · A5 duplicate 500.
  A3 lost 2 rows to the "do not perturb if new tag == original tag" guard — expected behaviour, logged here for traceability.
- D2 NYC: B1 OT/regular 2,000 · B2 salary/basis 2,000 · B3 near-duplicate name 2,000 · B4 agency/title 2,000 · B5 magnitude 2,000.
- D3 UCI: C1 EDU code 300 · C2 LIMIT_BAL inconsistency 300 · C3 bill sign 300 · C4 PAY_0 temporal 300 · C5 AGE range 300.

**Schema notes (downstream consumers must know).**

- D3 column name is `default payment next month` (spaces, no dots) — distinct
  from the `default.payment.next.month` shown in some UCI mirrors.
- D1 has +500 duplicate-posting rows; the duplicates carry the new highest
  row indices. D2 has +2,000 near-duplicate-name rows by the same convention.
  Downstream code must treat `row_index` as referring to the *injected* parquet,
  not the pre-injection parquet.

**Outstanding for Phase 3 (not started).**

- Implement detectors:
  - Rule-based / pattern-based baseline (sign, range, schema rules).
  - Statistical (IQR, robust z-score per tag/agency group).
  - ML (`IsolationForest`, `LOF`) on per-dataset feature matrices.
  - Hybrid pipeline (the DataFlow AI proposal).
- Run baseline, ablation, cross-validation, scalability, threshold sweep,
  operating-mode comparisons. Watch for ≥99 % suspicious metrics as a stop
  condition (rebuild contract).

**End of Phase 2.**

---

## Phase 3 � Stacker + figures + SQL + paper (final)

**Date:** 2026-05-27

### Added
- scripts/10_run_anomaly_experiments.py: added hybrid_lr detector (sklearn LogisticRegression, 5-fold OOF stacker, `class_weight=balanced`). All downstream tables (CV, ablation, threshold sweep, scalability) now use `hybrid_lr`.
- scripts/20_generate_figures.py: 7 figures (PR, confmat, threshold sweep, scalability, per-family, ablation, SQL matrix). Times serif, `pdf.fonttype=42`.
- scripts/30_run_sql_migration.py: parse + transpile + AST-footprint equivalence on 109 queries � 5 dialects = 575 pairs (sqlglot 30.8.0).
- scripts/40_audit_paper.py: citation, metric-occurrence, and xref-proximity audits.
- paper/references.bib (43 entries; =30 required).
- paper/dataflow_ai_v2.tex (IEEE Access, full paper with TikZ architecture figure as Fig 1, two algorithms, 8 tables, 7 included figures, \FloatBarrier after every floating block).
- eproducibility_report.md.

### Final headline numbers
- Anomaly F1: D1 0.511, D2 0.359, D3 0.717 (hybrid_lr).
- SQL: parse 0.991 / transpile 0.991 / AST-equivalence **0.800** (575 pairs).
- Scalability D2: 0.48s/2.74s/7.25s/17.32s at 10k/50k/100k/200k rows (~87 us/row).

### Tripwires
Parse and transpile rates fired at 0.9913 (=0.99). Reported transparently in paper �VII-B; AST-equivalence (0.800) recommended as the substantive metric.

### Outstanding
- LaTeX toolchain (MiKTeX/TeX Live) not installed locally; PDF not built.
- Per-family recall: A2 (0.034), A3 (0.022), C3 (0.000) - acknowledged design boundary, listed as future work.
