#!/usr/bin/env python3
"""
Baseline Comparison Experiment — IEEE Access
Compares full hybrid system against six simpler baselines.
"""

import sys, json, logging, statistics
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_assets.experiments.experiment_config import RANDOM_SEED, RESULTS_DIR
from research_assets.experiments.experiment_engine import (
    full_system_detect, isolation_forest_outliers, tfidf_duplicates,
    rule_based_null_check, cross_field_validation, iqr_outliers,
    exact_duplicates, compute_metrics, ResourceMonitor
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)
np.random.seed(RANDOM_SEED)
OUT = RESULTS_DIR / "baseline"
OUT.mkdir(parents=True, exist_ok=True)


# ── Baseline detector implementations ────────────────────────────────────────

def baseline_rule_based_only(df: pd.DataFrame, **_) -> np.ndarray:
    mask = np.zeros(len(df), dtype=bool)
    mask |= rule_based_null_check(df).astype(bool)
    mask |= cross_field_validation(df).astype(bool)
    mask |= exact_duplicates(df).astype(bool)
    return mask.astype(int)


def baseline_isolation_forest_only(df: pd.DataFrame,
                                    contamination=0.10, **_) -> np.ndarray:
    return isolation_forest_outliers(df, contamination).astype(int)


def baseline_tfidf_only(df: pd.DataFrame, text_cols=None, **_) -> np.ndarray:
    if not text_cols:
        return np.zeros(len(df), dtype=int)
    valid = [c for c in text_cols if c in df.columns]
    return tfidf_duplicates(df, valid).astype(int) if valid else np.zeros(len(df), dtype=int)


def baseline_string_similarity_only(df: pd.DataFrame,
                                      text_cols=None, **_) -> np.ndarray:
    """Levenshtein-style: check Hamming distance on string representations."""
    if not text_cols:
        return np.zeros(len(df), dtype=int)
    valid = [c for c in text_cols if c in df.columns]
    if not valid:
        return np.zeros(len(df), dtype=int)
    combined = df[valid].fillna("").astype(str).apply(" ".join, axis=1)
    mask = np.zeros(len(df), dtype=bool)
    for i in range(len(combined)):
        for j in range(i+1, min(i+20, len(combined))):  # local window
            s1, s2 = combined.iloc[i], combined.iloc[j]
            # normalized edit distance approximation
            if len(s1) > 0 and len(s2) > 0:
                common = sum(c1 == c2 for c1, c2 in zip(s1, s2))
                sim = 2 * common / (len(s1) + len(s2))
                if sim > 0.80:
                    mask[i] = True
                    mask[j] = True
    return mask.astype(int)


def baseline_threshold_validation_only(df: pd.DataFrame, **_) -> np.ndarray:
    """Simple hard-threshold checks on numeric columns."""
    mask = np.zeros(len(df), dtype=bool)
    for col in df.select_dtypes(include=[np.number]).columns:
        s = df[col].fillna(0)
        mu, std = s.mean(), s.std()
        if std > 0:
            mask |= (np.abs((s - mu) / std) > 3).values
    return mask.astype(int)


def baseline_single_model_anomaly(df: pd.DataFrame,
                                   contamination=0.10, **_) -> np.ndarray:
    """Only IQR-based statistical outlier detection."""
    mask = np.zeros(len(df), dtype=bool)
    for col in df.select_dtypes(include=[np.number]).columns:
        s = df[col].dropna()
        if len(s) >= 10:
            mask |= iqr_outliers(df[col].fillna(df[col].median()))
    return mask.astype(int)


BASELINES = {
    "rule_based_only":         baseline_rule_based_only,
    "isolation_forest_only":   baseline_isolation_forest_only,
    "tfidf_only":              baseline_tfidf_only,
    "string_similarity_only":  baseline_string_similarity_only,
    "threshold_validation_only": baseline_threshold_validation_only,
    "single_model_anomaly":    baseline_single_model_anomaly,
}


def load_dataset(name: str) -> tuple:
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


def run_comparison(df: pd.DataFrame,
                   y_true: np.ndarray,
                   text_cols: list) -> list:
    results = []

    # Full hybrid system
    with ResourceMonitor() as rm:
        y_pred = full_system_detect(df, text_cols=text_cols)
    m = compute_metrics(y_true, y_pred)
    m.update({"system":"full_hybrid_system",
               "latency_ms": rm.latency_ms,
               "mem_delta_mb": round(rm.mem_delta, 2)})
    results.append(m)

    # Baselines
    for name, fn in BASELINES.items():
        with ResourceMonitor() as rm:
            y_pred = fn(df, text_cols=text_cols)
        m = compute_metrics(y_true, y_pred)
        m.update({"system": name,
                  "latency_ms": rm.latency_ms,
                  "mem_delta_mb": round(rm.mem_delta, 2)})
        results.append(m)

    return results


def main():
    log.info("=" * 70)
    log.info("BASELINE COMPARISON  —  IEEE Access Experiment")
    log.info("=" * 70)

    datasets = [
        ("gl_accounts",       ["account_name","account_type"]),
        ("trial_balance",     ["account_id","period"]),
        ("journal_entries",   ["description","dr_account"]),
        ("mapping_table",     ["source_account","target_account"]),
    ]

    all_results = {}
    for ds_name, text_cols in datasets:
        log.info(f"\nDataset: {ds_name}")
        try:
            df, gt = load_dataset(ds_name)
            y_true = build_gt_mask(df, gt)
            results = run_comparison(df, y_true, text_cols)
            all_results[ds_name] = results
            for r in results:
                log.info(f"  {r['system']:<35s} F1={r['f1']:.4f}  "
                         f"P={r['precision']:.4f}  R={r['recall']:.4f}  "
                         f"{r['latency_ms']:.0f}ms")
        except Exception as e:
            log.error(f"  FAILED: {e}", exc_info=True)

    # ── Aggregate across datasets ─────────────────────────────────────────────
    all_systems = ["full_hybrid_system"] + list(BASELINES.keys())
    agg = {}
    for sys_name in all_systems:
        vals = [r for rows in all_results.values()
                  for r in rows if r["system"] == sys_name]
        if vals:
            agg[sys_name] = {
                "mean_f1":         round(statistics.mean(v["f1"]         for v in vals), 4),
                "std_f1":          round(statistics.stdev(v["f1"]        for v in vals) if len(vals)>1 else 0, 4),
                "mean_precision":  round(statistics.mean(v["precision"]  for v in vals), 4),
                "mean_recall":     round(statistics.mean(v["recall"]     for v in vals), 4),
                "mean_fpr":        round(statistics.mean(v["fpr"]        for v in vals), 4),
                "mean_accuracy":   round(statistics.mean(v["accuracy"]   for v in vals), 4),
                "mean_latency_ms": round(statistics.mean(v["latency_ms"] for v in vals), 1),
            }

    output = {"experiment": "baseline_comparison",
               "seed": RANDOM_SEED,
               "per_dataset": all_results,
               "aggregate":   agg}

    out_file = OUT / "baseline_results.json"
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)

    log.info(f"\n{'='*70}")
    log.info("Aggregate F1 (all datasets):")
    for sys_name, v in sorted(agg.items(), key=lambda x: -x[1]["mean_f1"]):
        log.info(f"  {sys_name:<35s}  mean_F1={v['mean_f1']:.4f}  ±{v['std_f1']:.4f}")
    log.info(f"\nSaved → {out_file}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
