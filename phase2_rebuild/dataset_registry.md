# Dataset Registry — Phase 2 Rebuild

> **Status:** Phase 1 (acquisition + provenance). Last updated by the rebuild agent
> on the date of this commit. Checksums are filled in by `scripts/00_download_datasets.py`
> after a successful download; if a row's `SHA256` column is `PENDING`, the file has not
> yet been verified on this machine.

This registry is the single source of truth for which real public datasets back the
Phase 2 rebuild experiments. Every numeric result in the rebuilt paper must trace back
to one of these files, plus an injection script under `phase2_rebuild/scripts/`.

## Honesty markers used in this document

- **REAL** — file is downloaded unchanged from the upstream public source.
- **SEMI-SYNTHETIC** — REAL data with domain-informed anomaly injection layered on top.
  The injection script and its seed are recorded; ground-truth masks are saved
  separately so the original real data is never overwritten.
- **SYNTHETIC** — generated end-to-end by code. Not used in Phase 2 except as
  micro-benchmarks for adversarial/security tests (Section RQ3b of the paper).

## Datasets

### D1 — SEC EDGAR Financial Statement Data Sets (FSDS)

| Field | Value |
|---|---|
| Slot in paper | GL accounts + Trial balance |
| Provenance | U.S. Securities and Exchange Commission, Division of Economic and Risk Analysis (DERA) |
| Landing page | https://www.sec.gov/dera/data/financial-statement-data-sets |
| Concrete file | `https://www.sec.gov/files/dera/data/financial-statement-data-sets/2024q4.zip` (one quarter; later phases may add more) |
| Format | Pipe-delimited TSV inside ZIP: `sub.txt`, `num.txt`, `tag.txt`, `pre.txt` |
| Approx size | ~80–120 MB compressed per quarter |
| License | Public domain (U.S. federal government work, 17 U.S.C. §105) |
| Realism note | These are the actual numeric line items reported by every SEC filer (10-K, 10-Q, etc.). `num.txt` rows are real general-ledger-style account postings with `adsh, tag, ddate, qtrs, uom, value`. |
| SHA256 | PENDING |
| Local path | `phase2_rebuild/data/raw/sec_edgar/2024q4.zip` |

### D2 — NYC Citywide Payroll Data (Office of Payroll Administration)

| Field | Value |
|---|---|
| Slot in paper | Journal entries + Entity structures |
| Provenance | New York City Office of Payroll Administration, published on NYC Open Data. |
| Landing page | https://data.cityofnewyork.us/City-Government/Citywide-Payroll-Data-Fiscal-Year-/k397-673e |
| Concrete file | `https://data.cityofnewyork.us/api/views/k397-673e/rows.csv?accessType=DOWNLOAD` |
| Format | CSV (~5M rows × 17 cols across all fiscal years; row count grows each year) |
| Approx size | ~1.0–1.5 GB CSV uncompressed. Phase 2 will sample a single fiscal year to keep compute bounded. |
| License | NYC Open Data Terms of Use — public domain for research and analysis with attribution to NYC OPA. |
| Realism note | Real per-employee fiscal-year payroll postings with `Agency Name`, `Last Name`, `First Name`, `Agency Start Date`, `Work Location Borough`, `Title Description`, `Leave Status as of June 30`, `Base Salary`, `Pay Basis`, `Regular Hours`, `Regular Gross Paid`, `OT Hours`, `Total OT Paid`, `Total Other Pay`. Hierarchy: Agency → Title → Employee. Used as a journal-entry surrogate (each row is a labour-cost posting against an agency cost-centre) and as the entity-structure surrogate (agency/title/employee tree). |
| Selection rationale | Chosen *after* the Berka 1999 mirror at relational.fit.cvut.cz was confirmed broken and the community GitHub mirror returned HTTP 404 (logged in `experiment_log.md`, Phase 1 entry). NYC Payroll is a more defensible substitute because (a) the upstream is institutionally maintained, (b) the data is genuinely real (not anonymised reconstructions), and (c) the schema admits the same anomaly types we planned for Berka (duplicate names, period mismatches, debit/credit-pair surrogates via OT vs Regular pay). |
| SHA256 | PENDING |
| Local path | `phase2_rebuild/data/raw/nyc_payroll/citywide_payroll.csv` |

### D3 — UCI Default of Credit Card Clients (Yeh & Lien 2009)

| Field | Value |
|---|---|
| Slot in paper | Mapping table |
| Provenance | Yeh, I.-C., & Lien, C.-H. (2009). "The comparisons of data mining techniques for the predictive accuracy of probability of default of credit card clients." *Expert Systems with Applications*, 36(2), 2473–2480. Dataset deposited at UCI Machine Learning Repository, ID 350. |
| Landing page | https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients |
| Concrete file | `https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip` |
| Format | XLS inside ZIP (~30,000 rows × 24 columns); convert to CSV on first ingest |
| Approx size | ~1 MB |
| License | CC BY 4.0 (UCI ML Repository terms) |
| Realism note | Real Taiwanese credit-card account data (Oct 2005 cohort) with demographic, billing-history, and payment-history columns plus a binary default-payment label. Used here as a "mapping table" surrogate because of its categorical-to-class structure (education → risk, marriage → risk, etc.). |
| SHA256 | PENDING |
| Local path | `phase2_rebuild/data/raw/uci_credit_default/default of credit card clients.zip` |

## Anomaly labelling policy

None of D1–D3 ship with audit-grade anomaly labels (SEC filings are not annotated for
errors; Berka transactions are not annotated for fraud beyond loan-default outcome;
UCI credit-default is annotated for *default*, not for *data-quality* anomalies). The
rebuilt paper will therefore:

1. Treat every row of D1–D3 as **REAL** baseline data.
2. Apply **domain-informed anomaly injection** (see `anomaly_injection_plan.md`) at
   declared, parameterised rates and record the injected row indices as ground truth.
3. Report results on **SEMI-SYNTHETIC** datasets and disclose the injection design in
   the methodology section.

Where a dataset *does* ship with a native label (D3's `default.payment.next.month`),
that label will be reported alongside but kept distinct from the injected anomaly mask,
so that "detecting injected anomalies" and "predicting default" are never conflated.

## Forbidden uses

- D1, D2, D3 must **never** be redistributed as part of this repository. Only download
  scripts and checksums are committed; the binary files live under `data/raw/` which
  must be `.gitignore`-d.
- No claim of proprietary enterprise origin may be made for any of these files.
- No statement of the form "we obtained this data from [Company X]" may be made.
