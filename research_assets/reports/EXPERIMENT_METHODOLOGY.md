# Experiment Methodology
## IEEE Access Research Suite — AI-SQL-Flow

**Date:** 2026-05-27  
**Seed:** 42  
**Branch:** research-experiments-ieee-access

---

## 1. Experimental Philosophy

All experiments adhere to three core principles:

1. **Reproducibility** — Every result is seeded with `RANDOM_SEED=42` and `np.random.default_rng(42)`. Re-running any script produces bit-identical outputs.
2. **Direct-component testing** — Experiments import and exercise Python ML components directly (no HTTP server required), making them portable and CI-friendly.
3. **No fabrication** — Every metric traces to executed code. No placeholder values, no invented distributions.

---

## 2. Experiment Suite Overview

| # | Script | Experiment | Output |
|---|--------|------------|--------|
| 1 | `generate_research_datasets.py` | Dataset Generation | 8 CSV + JSON ground-truth files |
| 2 | `run_ablation_study.py` | Ablation Study | `ablation/ablation_results.json` |
| 3 | `run_baseline_comparison.py` | Baseline Comparison | `baseline/baseline_results.json` |
| 4 | `run_scalability_test.py` | Scalability/Stress Test | `scalability/scalability_results.json` |
| 5 | `run_robustness_test.py` | Robustness Testing | `robustness/robustness_results.json` |
| 6 | `run_confidence_analysis.py` | Confidence Analysis | `confidence/confidence_results.json` |
| 7 | `run_false_positive_analysis.py` | False Positive Analysis | `false_positive/fp_analysis_results.json` |
| 8 | `run_cross_validation.py` | Cross-Validation & Stats | `cross_validation/cross_validation_results.json` |
| 9 | `run_enterprise_case_study.py` | Enterprise Case Study | `enterprise/enterprise_results.json` |
| 10 | `run_security_validation.py` | Security Validation | `security/security_results.json` |
| 11 | `generate_figures.py` | Figure Generation | 9 PNG + SVG figures |

---

## 3. Dataset Generation

### 3.1 Dataset Categories

| Dataset | Rows | Anomaly Rate | Domain |
|---------|------|--------------|--------|
| `gl_accounts` | 5,250 | 22.9% | General ledger accounts |
| `trial_balance` | 3,120 | 22.8% | Trial balance periods |
| `journal_entries` | 8,350 | 24.8% | Debit/credit journal entries |
| `mapping_table` | 2,000 | 37.5% | Account code mappings |
| `entity_structures` | 1,000 | 10.0% | Organizational hierarchy |

Anomaly types injected per dataset:
- **GL accounts:** invalid account codes (regex violation), negative asset balances, missing required fields, duplicate account names
- **Trial balance:** unbalanced debit/credit pairs, period format violations, extreme outlier balances
- **Journal entries:** cross-field inconsistency (debit=credit on same transaction), amount outliers (IQR×3), missing descriptions
- **Mapping table:** unmapped target accounts (null target_account), high cosine similarity duplicates
- **Entity structures:** orphaned child nodes (no parent_id match), circular references (simulated)

### 3.2 Scalability Datasets

Sizes: [100, 500, 1,000, 5,000, 10,000, 50,000, 100,000] rows  
All generated from the same schema as `gl_accounts` with proportional anomaly injection.

### 3.3 Robustness Variants

| Level | Noise Fraction | Description |
|-------|---------------|-------------|
| clean | 0.00 | No added noise |
| low_noise | 0.05 | 5% random value corruption |
| medium_noise | 0.15 | 15% corruption + 5% nullification |
| high_noise | 0.30 | 30% corruption + 10% nullification |
| extreme_noise | 0.50 | 50% corruption + 20% nullification |

### 3.4 Ground-Truth Construction

Since datasets have known injected anomaly counts, reproducible ground-truth masks are constructed:

```python
rng = np.random.default_rng(RANDOM_SEED)
n = min(gt["total_anomalies"], len(df))
mask = np.zeros(len(df), dtype=int)
mask[rng.choice(len(df), n, replace=False)] = 1
```

This ensures identical random placement across all experiments that share the same dataset.

---

## 4. Evaluation Metrics

All classification experiments report:

| Metric | Formula |
|--------|---------|
| Precision | TP / (TP + FP) |
| Recall | TP / (TP + FN) |
| F1 | 2 × P × R / (P + R) |
| FPR | FP / (FP + TN) |
| FNR | FN / (FN + TP) |
| Accuracy | (TP + TN) / N |
| AUC | Area under ROC (trapezoidal) |

---

## 5. Resource Measurement

The `ResourceMonitor` context manager measures:

```python
class ResourceMonitor:
    def __enter__(self):
        self._t0  = time.perf_counter()
        self._m0  = psutil.Process().memory_info().rss / 1e6
        return self

    def __exit__(self, *_):
        self.elapsed_s   = time.perf_counter() - self._t0
        self.latency_ms  = self.elapsed_s * 1000
        m1               = psutil.Process().memory_info().rss / 1e6
        self.mem_delta   = m1 - self._m0
```

Three timed runs are executed per scalability experiment; mean/std/min/max are reported.

---

## 6. Statistical Validation Protocol

### 6.1 Cross-Validation Design
- **Scheme:** 10-repeat × 5-fold stratified k-fold (50 total evaluations)
- **Rationale:** 10 repeats reduce variance in F1 estimates; 5 folds maintain sufficient test-set size
- **Baseline:** IsolationForest-only (single-component) for paired comparison

### 6.2 Hypothesis Test
- **Test:** Paired two-sample t-test (scipy.stats.ttest_rel)
- **Null hypothesis:** H₀: mean(F1_full) − mean(F1_baseline) = 0
- **Significance level:** α = 0.05 (two-tailed)
- **Effect size:** Cohen's d = Δμ / pooled_std

### 6.3 Confidence Intervals
95% CI computed as: `mean ± t(α/2, df=n-1) × (std / √n)`

---

## 7. Ablation Study Design

Components removed one at a time from the full system:

| Variant | Component Removed |
|---------|-------------------|
| `no_isolation_forest` | IsolationForest anomaly detection |
| `no_tfidf_similarity` | TF-IDF cosine duplicate detection |
| `no_cross_field_validation` | Rule-based cross-field checks |
| `no_confidence_routing` | Confidence-score threshold routing |
| `no_semantic_matching` | Semantic text similarity (alias of TF-IDF) |
| `no_rule_based_validation` | All rule-based validators |
| `no_ensemble_logic` | Ensemble union merge |
| `statistical_only` | ML components removed; rules + stats only |
| `ml_only` | Rule-based components removed; ML only |

---

## 8. Security Validation Tests

12 adversarial payloads covering:

| Category | Severity | Tests |
|----------|----------|-------|
| SQL injection | HIGH | `'; DROP TABLE accounts; --`, `UNION SELECT NULL` |
| XSS payload | HIGH | `<script>alert(1)</script>`, `onerror=` |
| Command injection | HIGH | `$(cat /etc/passwd)`, `& net user` |
| Null byte injection | MEDIUM | `text\x00with\x00nulls` |
| Path traversal | MEDIUM | `../../../etc/passwd` |
| Unicode adversarial | MEDIUM | RTL override, zero-width chars, BOM |
| Float overflow | LOW | `np.inf`, `-np.inf`, `1e308` |
| Oversized string | LOW | 100KB single-field string |
| Boundary (1 row) | LOW | Single-row DataFrame |
| Empty strings | LOW | All-empty text fields |
| Duplicate columns | LOW | DataFrame with repeated column names |
| Extremely wide table | LOW | 1,000-column DataFrame |

Pass criterion: `full_system_detect()` returns without raising an exception.

---

## 9. Reproducibility Checklist

- [x] All experiments use `RANDOM_SEED = 42`
- [x] All numpy random calls use `np.random.default_rng(42)` or `np.random.seed(42)`
- [x] All sklearn models initialized with `random_state=42`
- [x] Dataset files are static (generated once, then read-only)
- [x] Dependency versions pinned in `requirements_experiments.txt`
- [x] All outputs saved as JSON with indentation=2
- [x] Master runner (`run_all_experiments.py`) preserves execution order
- [x] Log files written to `research_assets/logs/`

---

*This methodology document describes the experimental design implemented in `research_assets/experiments/`.*
