# Computational Environment

**Manuscript:** DataFlow AI — Access-2026-28181
**Date recorded:** 2026-07-11

---

## Hardware

| Component | Detail |
|-----------|--------|
| OS | Windows 11 Home Single Language 10.0.26200 |
| Architecture | x86-64 (AMD64) |

---

## Python runtime

| Package | Version |
|---------|---------|
| Python | 3.14.3 (tags/v3.14.3:323c59a, Feb 3 2026) |
| numpy | 2.4.4 |
| pandas | 3.0.2 |
| scikit-learn | 1.8.0 |
| sqlglot | 30.8.0 |
| pyarrow | 24.0.0 |
| scipy | 1.17.1 |
| joblib | 1.5.3 |

Full `pip freeze` snapshot: `rebuttal_artifacts/pip_freeze.txt`

**Note:** pyod is NOT installed. Experiment E2 (modern ML baselines: ECOD, COPOD, HBOS, etc.)
requires `pip install pyod` before running.

---

## Datasets

| ID | Name | Source | Access date | SHA-256 of injected parquet |
|----|------|--------|------------|----------------------------|
| D1 | SEC EDGAR 2024-Q4 num.txt | https://www.sec.gov/dera/data/financial-statements | 2024-Q4 zip | `6b706b30a22a7e4a0c04b19c645bb8a9e7cfd0293e33b79959b7d435af8f74ce` |
| D2 | NYC Citywide Payroll FY2024 | https://data.cityofnewyork.us/City-Government/Citywide-Payroll-Data-Fiscal-Year-/k397-673e | FY2024 | `2cded7ccf704cf66d971897a6de8cc40af880f241e86e81cdab76ff39b71ad82` |
| D3 | UCI Credit Card Default | https://archive.ics.uci.edu/ml/datasets/default+of+credit+card+clients | 2024-Q4 | `b1a4866287aa55c774e07f422b71a67bdcb2aed9369d5fd5fb889f23c0ef9f6f` |

All datasets are publicly available under open/academic licenses.
D1 and D3 are deterministic (first 50k / all 30k rows). D2 uses stratified sampling with `np.random.default_rng(42)`.

---

## Wall-clock runtimes at SEED=42 (on this machine)

| Stage | Script | Elapsed |
|-------|--------|---------|
| Extract + sample | 01_extract_and_sample.py | 8.9s (skip-existing) |
| Inject anomalies | 02_inject_anomalies.py | 3.3s |
| Anomaly experiments | 10_run_anomaly_experiments.py | 66.3s |
| SQL migration | 30_run_sql_migration.py | ~2s |
| G4 seed verification | g4_gate.py | 30.3s |

Total pipeline time (01→30): ~80s

Scalability measurements reported in Table 6 vary by machine; the F1 values are
deterministic and reproduce exactly. Timing-only differences are expected across hardware.
