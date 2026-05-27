#!/usr/bin/env python3
"""
False Positive / Confusion Matrix Analysis — IEEE Access
Deep investigation into where the system fails: FP patterns, FN patterns, edge cases.
"""

import sys, json, logging
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_assets.experiments.experiment_config import RANDOM_SEED, RESULTS_DIR
from research_assets.experiments.experiment_engine import (
    full_system_detect, compute_metrics,
    isolation_forest_outliers, tfidf_duplicates,
    rule_based_null_check, cross_field_validation, iqr_outliers
)
from sklearn.metrics import confusion_matrix

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)
np.random.seed(RANDOM_SEED)
OUT = RESULTS_DIR / "false_positive"
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


def per_component_masks(df: pd.DataFrame, text_cols: list) -> dict:
    """Return per-component detection masks for FP attribution."""
    masks = {}
    masks["null_check"]        = rule_based_null_check(df).astype(int)
    masks["cross_field"]       = cross_field_validation(df).astype(int)
    masks["isolation_forest"]  = isolation_forest_outliers(df).astype(int)

    iqr_mask = np.zeros(len(df), dtype=bool)
    for col in df.select_dtypes(include=[np.number]).columns:
        s = df[col].dropna()
        if len(s) >= 10:
            iqr_mask |= iqr_outliers(df[col].fillna(df[col].median()))
    masks["iqr_outliers"] = iqr_mask.astype(int)

    if text_cols and any(c in df.columns for c in text_cols):
        valid = [c for c in text_cols if c in df.columns]
        masks["tfidf_similarity"] = tfidf_duplicates(df, valid).astype(int)
    else:
        masks["tfidf_similarity"] = np.zeros(len(df), dtype=int)

    return masks


def analyze_fp_patterns(df: pd.DataFrame,
                          y_true: np.ndarray,
                          y_pred: np.ndarray,
                          component_masks: dict) -> dict:
    fp_idx  = np.where((y_pred == 1) & (y_true == 0))[0]
    fn_idx  = np.where((y_pred == 0) & (y_true == 1))[0]
    tp_idx  = np.where((y_pred == 1) & (y_true == 1))[0]

    # ── FP attribution: which component triggered the FP? ──────────────────
    fp_attribution = {}
    for comp, mask in component_masks.items():
        fp_by_comp = np.sum((mask == 1) & (y_true == 0))
        fp_attribution[comp] = int(fp_by_comp)

    # ── Column-wise FP analysis (numeric outlier FPs) ──────────────────────
    col_fp = {}
    for col in df.select_dtypes(include=[np.number]).columns[:10]:
        s = df[col].fillna(df[col].median())
        from sklearn.preprocessing import StandardScaler
        z = np.abs((s.values - s.mean()) / (s.std() + 1e-8))
        # FP rows with high z-score
        n_high_z_fp = int(np.sum((z > 2) & (y_pred == 1) & (y_true == 0)))
        if n_high_z_fp > 0:
            col_fp[col] = n_high_z_fp

    # ── FN analysis: characterize what was missed ──────────────────────────
    fn_analysis = {
        "total_fn": int(len(fn_idx)),
        "fn_pct_of_positives": round(len(fn_idx) / max(y_true.sum(), 1), 4),
    }
    if len(fn_idx) > 0 and len(df) > 0:
        fn_df = df.iloc[fn_idx]
        fn_analysis["fn_null_rate"] = round(float(fn_df.isnull().mean().mean()), 4)

    return {
        "total_fp": int(len(fp_idx)),
        "total_fn": int(len(fn_idx)),
        "total_tp": int(len(tp_idx)),
        "fpr": round(len(fp_idx) / max((y_true==0).sum(), 1), 4),
        "fnr": round(len(fn_idx) / max((y_true==1).sum(), 1), 4),
        "fp_attribution": fp_attribution,
        "fp_by_column": col_fp,
        "fn_analysis": fn_analysis,
    }


def main():
    log.info("=" * 70)
    log.info("FALSE POSITIVE ANALYSIS  —  IEEE Access Experiment")
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
            df, gt = load(ds_name)
            y_true = build_gt_mask(df, gt)
            y_pred = full_system_detect(df, text_cols=text_cols)
            metrics = compute_metrics(y_true, y_pred)

            # confusion matrix
            cm = confusion_matrix(y_true, y_pred)
            cm_dict = {
                "tn": int(cm[0,0]), "fp": int(cm[0,1]),
                "fn": int(cm[1,0]), "tp": int(cm[1,1]),
            }

            comp_masks = per_component_masks(df, text_cols)
            fp_analysis = analyze_fp_patterns(df, y_true, y_pred, comp_masks)

            all_results[ds_name] = {
                "n_rows": len(df),
                "anomaly_rate": float(y_true.mean()),
                "metrics": metrics,
                "confusion_matrix": cm_dict,
                "fp_analysis": fp_analysis,
            }

            log.info(f"  F1={metrics['f1']:.4f}  FPR={metrics['fpr']:.4f}  FNR={metrics['fnr']:.4f}")
            log.info(f"  CM: TP={cm_dict['tp']}  FP={cm_dict['fp']}  "
                     f"FN={cm_dict['fn']}  TN={cm_dict['tn']}")
            log.info(f"  FP attribution: {fp_analysis['fp_attribution']}")

        except Exception as e:
            log.error(f"  FAILED: {e}", exc_info=True)

    out_file = OUT / "fp_analysis_results.json"
    with open(out_file, "w") as f:
        json.dump({"experiment": "false_positive_analysis",
                    "seed": RANDOM_SEED,
                    "datasets": all_results}, f, indent=2)

    log.info(f"\nSaved → {out_file}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
