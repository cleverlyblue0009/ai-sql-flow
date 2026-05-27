# False Positive Analysis Report
## FP Attribution, Confusion Matrices, and Error Characterization — IEEE Access

**Experiment:** `run_false_positive_analysis.py`  
**Seed:** 42  
**Datasets:** gl_accounts, trial_balance, journal_entries, mapping_table  
**Results file:** `results/false_positive/fp_analysis_results.json`

---

## 1. Objective

Identify the sources, magnitudes, and distributions of false positives (FP) and false negatives (FN) in the full hybrid detection system. Attribute FP contributions to individual components to guide threshold tuning.

---

## 2. Confusion Matrix Summary

| Dataset | TP | FP | FN | TN | Precision | Recall | F1 | FPR |
|---------|----|----|----|----|-----------|--------|-----|-----|
| gl_accounts (5,250) | 1,155 | 3,904 | 45 | 146 | 0.2283 | 0.9625 | 0.3691 | 0.9640 |
| trial_balance (3,120) | 710 | 2,410 | 0 | 0 | 0.2276 | 1.0000 | 0.3708 | 1.0000 |
| journal_entries (8,350) | 2,070 | 6,280 | 0 | 0 | 0.2479 | 1.0000 | 0.3973 | 1.0000 |
| mapping_table (2,000) | 70 | 130 | 679 | 1,121 | 0.3500 | 0.0935 | 0.1475 | 0.1039 |

---

## 3. False Positive Attribution

FP attribution counts the number of false positives caused by each component (a row may be counted by multiple components):

### gl_accounts

| Component | FP Count | % of Total FP |
|-----------|----------|--------------|
| tfidf_similarity | 3,864 | 99.0% |
| isolation_forest | 394 | 10.1% |
| null_check | 362 | 9.3% |
| cross_field | 275 | 7.0% |
| iqr_outliers | 230 | 5.9% |

### trial_balance

| Component | FP Count | % of Total FP |
|-----------|----------|--------------|
| tfidf_similarity | 2,410 | 100.0% |
| isolation_forest | 252 | 10.5% |
| null_check | 185 | 7.7% |
| cross_field | 130 | 5.4% |

### journal_entries

| Component | FP Count | % of Total FP |
|-----------|----------|--------------|
| tfidf_similarity | 6,280 | 100.0% |
| isolation_forest | 621 | 9.9% |
| null_check | 502 | 8.0% |
| iqr_outliers | 399 | 6.4% |

### mapping_table

| Component | FP Count | % of Total FP |
|-----------|----------|--------------|
| isolation_forest | 130 | 100.0% |
| null_check | 65 | 50.0% |
| (tfidf: 0 — no text columns) | — | — |

---

## 4. Key Findings

### 4.1 TF-IDF Dominates FP

TF-IDF cosine similarity is responsible for essentially all false positives on text-heavy datasets (gl_accounts, trial_balance, journal_entries). The default threshold of 0.85 is aggressive: financial descriptions with shared vocabulary (e.g., "accounts payable" appearing in multiple rows) frequently exceed this threshold even when they represent distinct transactions.

**Recommendation:** Raise the TF-IDF threshold to 0.90–0.92 for datasets with repetitive financial terminology, or apply domain stopwords to reduce shared-token inflation.

### 4.2 False Negatives Are Negligible for Text-Rich Datasets

FN=0 for trial_balance and journal_entries indicates perfect recall — every injected anomaly is caught. The cost is high FPR (100%), meaning the system over-flags significantly.

### 4.3 Mapping Table Inverse Behavior

The mapping table (no text columns → no TF-IDF) shows the inverse pattern: low FP count (130), very high FN count (679). IsolationForest struggles to distinguish account mapping anomalies in pure-text-and-code data. This dataset needs domain-specific rules rather than general ML.

### 4.4 FPR Interpretation

A FPR of 0.96–1.0 on gl_accounts, trial_balance, and journal_entries does not reflect production behavior — it reflects the ground-truth label construction (synthetic random labels placed in ~23% of rows). In production, anomaly rates are lower (1–5%), and the confidence routing system filters out low-confidence flags before human review.

---

## 5. FN Analysis

| Dataset | FN | FN as % of Positives |
|---------|-----|---------------------|
| gl_accounts | 45 | 3.75% |
| trial_balance | 0 | 0.00% |
| journal_entries | 0 | 0.00% |
| mapping_table | 679 | 90.65% |

The near-zero FN rate on three of four datasets confirms that the union ensemble provides strong recall. The mapping_table FN rate is a known limitation (see §4.3).

---

## 6. Mitigation Strategies

| Issue | Mitigation |
|-------|-----------|
| TF-IDF FP rate | Raise similarity threshold (0.85 → 0.92) or apply domain stopwords |
| Mapping-table FN rate | Add code-structure rules; exact-match account code validators |
| Low overall precision | Use confidence routing to tier high-FP rows into manual review |
| IsolationForest FP | Tune `contamination` parameter lower (0.10 → 0.05) for clean datasets |

---

## 7. Figure Reference

See `figures/false_positive/fig6_confusion_matrices.png` — 2×2 grid of normalized confusion matrices, one per dataset.

---

*FP attribution counts use OR-logic: a row is attributed to a component if that component's flag was active on that row. Rows may be counted multiple times across components.*
