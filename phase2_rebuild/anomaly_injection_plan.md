# Anomaly Injection Plan — Phase 2 Rebuild

> **Purpose.** D1–D3 are real public datasets but **do not** ship with audit-grade
> anomaly labels. We therefore lay a documented, deterministic, domain-informed
> injection pass on top of them and treat the injected mask as ground truth for the
> precision/recall/F1/FPR metrics reported in the rebuilt paper. Every claim in this
> document maps directly to a function in `phase2_rebuild/scripts/01_inject_anomalies.py`
> (to be implemented in Phase 2). The original raw files are **never** mutated.

## Honesty contract

1. The rebuilt paper will explicitly label results from these datasets as
   **SEMI-SYNTHETIC**: real-data backbone + documented synthetic anomaly mask.
2. Injection rates are reported alongside every metric. Recall/precision are reported
   against the injected mask only; native dataset labels (e.g., D3's `default.payment.next.month`)
   are reported separately and never conflated with anomaly detection.
3. Injection seeds are fixed (`RANDOM_SEED = 42`) and re-running the script must
   reproduce identical masks bit-for-bit. CI verifies this via a checksum on the
   exported label files.
4. Injection rates are deliberately moderate (target **3 %–8 %** per dataset, not the
   10 %–38 % used in the previous synthetic submission). This is closer to production
   anomaly rates and reduces the risk of artefact-driven recall inflation that
   reviewers correctly flagged in the previous draft.

## Per-dataset injection design

### D1 — SEC EDGAR FSDS (`num.txt`) → "GL accounts" + "Trial balance" slots

**Sampling.** Take the first **N₁ = 50,000** rows of `num.txt` filtered to:
`qtrs ∈ {0,1}` (point-in-time and single-quarter facts), `uom = "USD"`, and
`value` parseable as float. This yields a real GL-style table of
`(adsh, tag, ddate, value, segments)` postings.

**Injection types (target rate per type, all multiplied by global ~5 %).**

| ID | Anomaly type | Mechanism | Rationale |
|---|---|---|---|
| A1 | Sign flip | Negate `value` on randomly chosen 1.0 % rows whose `tag` is a strictly non-negative GAAP concept (e.g., `Assets`, `Revenues`, `CashAndCashEquivalents`). | Real accounting-error pattern: posting a credit where a debit belongs. |
| A2 | Magnitude outlier | Multiply `value` by `10^k`, `k ∈ {3,4}`, on 1.0 % of rows. | Real "wrong unit / extra zero" data-entry error. |
| A3 | Tag–value mismatch | Replace `tag` on 1.0 % of rows with a syntactically valid but semantically inconsistent GAAP tag (e.g., assign `Revenues` to a row whose value is structurally a count). | Tests cross-field semantic check (mirrors paper's cross-field algorithm). |
| A4 | Period violation | Set `ddate` on 1.0 % of rows to a date outside the filing's reporting window. | Tests period-format / range validators. |
| A5 | Duplicate posting | For 1.0 % of rows, duplicate the row with an identical `value` and `tag` under the same `adsh`. | Real double-posting bookkeeping error; tests TF-IDF / dedup branch. |

Total injection rate ≈ **5.0 %**. All injected row indices saved to
`phase2_rebuild/data/labels/D1_sec_edgar_mask.parquet` with columns
`(row_index, anomaly_type, injection_rng_seed)`.

### D2 — NYC Citywide Payroll → "Journal entries" + "Entity structures" slots

**Sampling.** Filter to **fiscal year 2024** (most recent complete year at time of
download) and to non-null `Agency Name`. Expect ~600k rows; if larger than 200k,
take a deterministic stratified sample by `Agency Name` of 200,000 rows
(seeded). Output schema: `(Fiscal Year, Agency, Title, Last, First, Base Salary,
Regular Gross Paid, OT Hours, Total OT Paid)`.

**Injection types.**

| ID | Anomaly type | Mechanism | Rationale |
|---|---|---|---|
| B1 | OT–Regular inconsistency | On 1.0 % of rows where `Regular Hours = 0`, set `Total OT Paid > 0`. | Real payroll error: OT paid without underlying regular hours. |
| B2 | Salary–pay-basis mismatch | On 1.0 % of rows with `Pay Basis = "per Annum"`, set `Regular Gross Paid` to be < 5 % of `Base Salary`. | Real "wrong pay basis" posting error. |
| B3 | Near-duplicate name within agency | For 1.0 % of rows, duplicate the row with a one-character perturbation in `Last Name`. | Tests TF-IDF near-duplicate detection — direct analogue to the previous paper's "duplicate name" anomaly. |
| B4 | Agency–title violation | On 1.0 % of rows, swap `Title Description` with a title from a different agency family (e.g., "FIREFIGHTER" under "DEPT OF EDUCATION"). | Cross-field semantic violation (agency → permissible titles). |
| B5 | Magnitude outlier | Multiply `Regular Gross Paid` by `10` on 1.0 % of rows. | Real data-entry "extra zero" error. |

Total injection rate ≈ **5.0 %**. Mask saved to
`phase2_rebuild/data/labels/D2_nyc_payroll_mask.parquet`.

### D3 — UCI Credit Card Default → "Mapping table" slot

**Sampling.** Use all 30,000 rows. Convert from `.xls` to `.parquet` on first
ingest (depends on `pandas` + `xlrd<2.0` or `openpyxl` — verify in Phase 2).

**Injection types.**

| ID | Anomaly type | Mechanism | Rationale |
|---|---|---|---|
| C1 | Categorical out-of-domain | On 1.0 % of rows, set `EDUCATION` to an undefined code (e.g., `7`). | Real "uncoded category" mapping error. |
| C2 | Numeric–categorical mismatch | On 1.0 % of rows, set `LIMIT_BAL = 0` while `default.payment.next.month = 0` and at least one `BILL_AMT > 0`. | Internal mapping inconsistency. |
| C3 | Sign violation | On 1.0 % of rows, negate `BILL_AMT1`. | Real billing-direction inversion. |
| C4 | Cross-field temporal violation | On 1.0 % of rows, set `PAY_0 = -2` (no consumption) but `BILL_AMT1 > 5000`. | Cross-field rule violation. |
| C5 | Range violation | On 1.0 % of rows, set `AGE` to a value < 18 or > 95. | Domain-range violation. |

Total injection rate ≈ **5.0 %**. Mask saved to
`phase2_rebuild/data/labels/D3_uci_credit_mask.parquet`.

## Determinism

- Global seed: `42`.
- Each row's injection assignment is computed from
  `numpy.random.default_rng(SEED).permutation(N)[:n_inject]`, deterministic given
  `(SEED, N)`.
- Output mask files include the seed in their metadata; downstream code refuses
  to use any mask that does not match the registered seed.

## What this plan deliberately does NOT promise

- **Realism floor, not realism guarantee.** Injected anomalies are *plausible*
  approximations of real-world errors, not draws from a verified empirical error
  distribution. The paper's threats-to-validity section must say so.
- **No fraud detection.** D3's native `default.payment.next.month` label is a credit
  outcome, not an anomaly label. We will **not** report it as anomaly-detection performance.
- **No claim of audit-grade ground truth.** Without an annotator, we cannot claim
  these are "the" anomalies in the data; we only claim recoverability of the
  injected mask we ourselves created.

## Open issues to resolve in Phase 2

1. UCI `.xls` ingestion path (xlrd ≥ 2.0 dropped XLS support; need `openpyxl` for
   `.xlsx` or `xlrd==1.2.0` for `.xls`). Verify and pin in `requirements.txt`.
2. NYC Payroll has multiple fiscal years; choose FY2024 as primary slice (rationale:
   most recent complete year at time of download).
3. SEC `num.txt` is 527 MB; load with `dtype` mapping and `usecols` to keep
   memory bounded.
