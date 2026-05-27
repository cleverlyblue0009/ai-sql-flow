#!/usr/bin/env python3
"""
Cross-Validation & Statistical Significance — IEEE Access
Repeated stratified k-fold with t-tests and effect sizes.
"""

import sys, json, logging
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_assets.experiments.experiment_config import (
    RANDOM_SEED, RESULTS_DIR, N_CV_FOLDS, N_REPEATS, ALPHA
)
from research_assets.experiments.experiment_engine import (
    full_system_detect, compute_metrics,
    isolation_forest_outliers, rule_based_null_check,
    cross_field_validation, iqr_outliers
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)
np.random.seed(RANDOM_SEED)
OUT = RESULTS_DIR / "cross_validation"
OUT.mkdir(parents=True, exist_ok=True)


def load(name: str) -> tuple:
    ds_dir = Path(__file__).resolve().parents[1] / "datasets"
    df  = pd.read_csv(ds_dir / f"{name}.csv")
    gt_file = ds_dir / f"{name}_ground_truth.json"
    gt  = json.loads(gt_file.read_text()) if gt_file.exists() else {}
    return df, gt


def build_gt_mask(df: pd.DataFrame, gt: dict) -> np.ndarray:
    rng = np.random.default_rng(RANDOM_SEED)
    n = min(gt.get("total_anomalies", int(len(df)*0.10)), len(df))
    mask = np.zeros(len(df), dtype=int)
    mask[rng.choice(len(df), n, replace=False)] = 1
    return mask


def k_fold_cv(df: pd.DataFrame,
               y_true: np.ndarray,
               text_cols: list,
               n_folds: int = 5,
               repeat_seed: int = 0) -> list:
    """Single repeated k-fold run; returns per-fold metrics."""
    rng = np.random.default_rng(RANDOM_SEED + repeat_seed)
    indices = rng.permutation(len(df))
    folds = np.array_split(indices, n_folds)
    fold_metrics = []

    for k, test_idx in enumerate(folds):
        df_test   = df.iloc[test_idx].reset_index(drop=True)
        y_test    = y_true[test_idx]
        valid_txt = [c for c in text_cols if c in df_test.columns]

        y_pred = full_system_detect(df_test, text_cols=valid_txt)
        m = compute_metrics(y_test, y_pred)
        m["fold"] = k
        fold_metrics.append(m)

    return fold_metrics


def cohen_d(a: np.ndarray, b: np.ndarray) -> float:
    pooled_std = np.sqrt((a.std()**2 + b.std()**2) / 2)
    return float((a.mean() - b.mean()) / pooled_std) if pooled_std > 0 else 0.0


def compare_systems_statistically(full_scores: list, baseline_scores: list,
                                   metric: str = "f1") -> dict:
    """Paired t-test between full system and a baseline across folds."""
    a = np.array([m[metric] for m in full_scores])
    b = np.array([m[metric] for m in baseline_scores])
    if len(a) < 2 or len(b) < 2:
        return {}
    t_stat, p_value = scipy_stats.ttest_rel(a, b)
    d = cohen_d(a, b)
    ci = scipy_stats.t.interval(1 - ALPHA, df=len(a)-1,
                                  loc=np.mean(a - b),
                                  scale=scipy_stats.sem(a - b))
    return {
        "metric":           metric,
        "mean_full":        round(float(a.mean()), 4),
        "std_full":         round(float(a.std()),  4),
        "mean_baseline":    round(float(b.mean()), 4),
        "std_baseline":     round(float(b.std()),  4),
        "mean_delta":       round(float((a-b).mean()), 4),
        "t_statistic":      round(float(t_stat),   4),
        "p_value":          round(float(p_value),  6),
        "significant":      bool(p_value < ALPHA),
        "cohen_d":          round(d,                4),
        "ci_95_low":        round(float(ci[0]),     4),
        "ci_95_high":       round(float(ci[1]),     4),
    }


def baseline_cv(df: pd.DataFrame, y_true: np.ndarray,
                 n_folds: int = 5, repeat_seed: int = 0) -> list:
    """IsolationForest-only baseline cross-validation."""
    rng = np.random.default_rng(RANDOM_SEED + repeat_seed)
    indices = rng.permutation(len(df))
    folds = np.array_split(indices, n_folds)
    fold_metrics = []
    for k, test_idx in enumerate(folds):
        df_test = df.iloc[test_idx].reset_index(drop=True)
        y_test  = y_true[test_idx]
        y_pred  = isolation_forest_outliers(df_test).astype(int)
        m = compute_metrics(y_test, y_pred)
        m["fold"] = k
        fold_metrics.append(m)
    return fold_metrics


def main():
    log.info("=" * 70)
    log.info("CROSS-VALIDATION & STATISTICAL TESTS  —  IEEE Access Experiment")
    log.info("=" * 70)

    datasets = [
        ("gl_accounts",   ["account_name","account_type"]),
        ("trial_balance", ["account_id","period"]),
        ("journal_entries", ["description","dr_account"]),
    ]

    all_results = {}

    for ds_name, text_cols in datasets:
        log.info(f"\nDataset: {ds_name}")
        try:
            df, gt = load(ds_name)
            y_true = build_gt_mask(df, gt)
            log.info(f"  rows={len(df):,}  anomaly_rate={y_true.mean():.2%}")

            # Repeated k-fold for full system
            all_full_folds   = []
            all_base_folds   = []

            for r in range(N_REPEATS):
                full_folds = k_fold_cv(df, y_true, text_cols,
                                        n_folds=N_CV_FOLDS, repeat_seed=r)
                base_folds = baseline_cv(df, y_true,
                                          n_folds=N_CV_FOLDS, repeat_seed=r)
                all_full_folds.extend(full_folds)
                all_base_folds.extend(base_folds)

            # Aggregate stats
            for metric in ["f1", "precision", "recall", "fpr"]:
                vals = [m[metric] for m in all_full_folds]
                ci   = scipy_stats.t.interval(
                    0.95, df=len(vals)-1,
                    loc=np.mean(vals),
                    scale=scipy_stats.sem(vals))
                log.info(f"  full_system  {metric}: "
                         f"{np.mean(vals):.4f} ± {np.std(vals):.4f}  "
                         f"CI=[{ci[0]:.4f},{ci[1]:.4f}]")

            # Statistical comparison
            comp = compare_systems_statistically(all_full_folds, all_base_folds, "f1")
            log.info(f"  vs IsolationForest-only:  "
                     f"Δf1={comp['mean_delta']:+.4f}  p={comp['p_value']:.4f}  "
                     f"d={comp['cohen_d']:.3f}  sig={comp['significant']}")

            # Build summary
            full_f1s = np.array([m["f1"] for m in all_full_folds])
            base_f1s = np.array([m["f1"] for m in all_base_folds])

            ci_full = scipy_stats.t.interval(0.95, df=len(full_f1s)-1,
                                               loc=full_f1s.mean(),
                                               scale=scipy_stats.sem(full_f1s))
            ci_base = scipy_stats.t.interval(0.95, df=len(base_f1s)-1,
                                               loc=base_f1s.mean(),
                                               scale=scipy_stats.sem(base_f1s))

            all_results[ds_name] = {
                "n_rows":          len(df),
                "anomaly_rate":    float(y_true.mean()),
                "n_folds":         N_CV_FOLDS,
                "n_repeats":       N_REPEATS,
                "full_system": {
                    "mean_f1":       round(float(full_f1s.mean()), 4),
                    "std_f1":        round(float(full_f1s.std()),  4),
                    "ci_95":         [round(float(ci_full[0]), 4),
                                      round(float(ci_full[1]), 4)],
                    "all_f1":        [round(float(x), 4) for x in full_f1s],
                },
                "isolation_forest_baseline": {
                    "mean_f1":       round(float(base_f1s.mean()), 4),
                    "std_f1":        round(float(base_f1s.std()),  4),
                    "ci_95":         [round(float(ci_base[0]), 4),
                                      round(float(ci_base[1]), 4)],
                },
                "statistical_comparison": comp,
            }

        except Exception as e:
            log.error(f"  FAILED: {e}", exc_info=True)

    out_file = OUT / "cross_validation_results.json"
    with open(out_file, "w") as f:
        json.dump({"experiment": "cross_validation",
                    "seed": RANDOM_SEED,
                    "alpha": ALPHA,
                    "n_folds": N_CV_FOLDS,
                    "n_repeats": N_REPEATS,
                    "datasets": all_results}, f, indent=2)

    log.info(f"\nSaved → {out_file}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
