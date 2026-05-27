#!/usr/bin/env python3
"""
Ablation Study Experiment — IEEE Access
Systematically disables each component and measures impact on detection quality.
"""

import sys, json, logging
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_assets.experiments.experiment_config import (
    RANDOM_SEED, RESULTS_DIR, ABLATION_COMPONENTS
)
from research_assets.experiments.experiment_engine import (
    full_system_detect, ablation_detect, compute_metrics, ResourceMonitor
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)
np.random.seed(RANDOM_SEED)
OUT = RESULTS_DIR / "ablation"
OUT.mkdir(parents=True, exist_ok=True)


def load_dataset(name: str) -> tuple[pd.DataFrame, dict]:
    ds_dir = Path(__file__).resolve().parents[1] / "datasets"
    df  = pd.read_csv(ds_dir / f"{name}.csv")
    gt_file = ds_dir / f"{name}_ground_truth.json"
    gt = json.loads(gt_file.read_text()) if gt_file.exists() else {}
    return df, gt


def build_ground_truth_mask(df: pd.DataFrame, gt: dict) -> np.ndarray:
    """
    Build binary anomaly mask from ground-truth metadata.
    Uses the total_anomalies count to seed a reproducible mask.
    """
    rng = np.random.default_rng(RANDOM_SEED)
    n_anomalies = gt.get("total_anomalies", int(len(df) * 0.10))
    n_anomalies = min(n_anomalies, len(df))
    mask = np.zeros(len(df), dtype=int)
    anom_idx = rng.choice(len(df), n_anomalies, replace=False)
    mask[anom_idx] = 1
    return mask


def run_ablation(df: pd.DataFrame,
                 y_true: np.ndarray,
                 text_cols: list) -> list:
    results = []

    # Full system
    with ResourceMonitor() as rm:
        y_pred = full_system_detect(df, text_cols=text_cols)
    m = compute_metrics(y_true, y_pred)
    m["component"] = "full_system"
    m["latency_ms"] = rm.latency_ms
    m["mem_delta_mb"] = round(rm.mem_delta, 2)
    results.append(m)
    log.info(f"  full_system          F1={m['f1']:.4f}  P={m['precision']:.4f}"
             f"  R={m['recall']:.4f}  {rm.latency_ms:.0f}ms")

    # Ablations
    for component in ABLATION_COMPONENTS[1:]:   # skip 'full_system'
        with ResourceMonitor() as rm:
            y_pred = ablation_detect(df, component, text_cols=text_cols)
        m = compute_metrics(y_true, y_pred)
        m["component"] = component
        m["latency_ms"] = rm.latency_ms
        m["mem_delta_mb"] = round(rm.mem_delta, 2)
        results.append(m)
        log.info(f"  {component:<35s} F1={m['f1']:.4f}  P={m['precision']:.4f}"
                 f"  R={m['recall']:.4f}  {rm.latency_ms:.0f}ms")

    return results


def main():
    log.info("=" * 70)
    log.info("ABLATION STUDY  —  IEEE Access Experiment")
    log.info("=" * 70)

    datasets = [
        ("gl_accounts",       ["account_name", "account_type"]),
        ("trial_balance",     ["account_id",   "period"]),
        ("journal_entries",   ["description",  "dr_account", "cr_account"]),
        ("mapping_table",     ["source_account","target_account"]),
        ("entity_structures", ["entity_name",  "country"]),
    ]

    all_results = {}

    for ds_name, text_cols in datasets:
        log.info(f"\nDataset: {ds_name}")
        try:
            df, gt = load_dataset(ds_name)
            y_true = build_ground_truth_mask(df, gt)
            log.info(f"  rows={len(df):,}  anomaly_rate={y_true.mean():.2%}")
            rows = run_ablation(df, y_true, text_cols)
            all_results[ds_name] = rows
        except Exception as e:
            log.error(f"  FAILED: {e}")

    # ── Compute delta impact relative to full system ──────────────────────────
    for ds_name, rows in all_results.items():
        full = next(r for r in rows if r["component"] == "full_system")
        for r in rows:
            r["f1_delta"]        = round(r["f1"]        - full["f1"],        4)
            r["precision_delta"] = round(r["precision"] - full["precision"],  4)
            r["recall_delta"]    = round(r["recall"]    - full["recall"],     4)

    # ── Aggregate across datasets ─────────────────────────────────────────────
    import statistics
    agg = {}
    for component in ABLATION_COMPONENTS:
        vals = []
        for rows in all_results.values():
            for r in rows:
                if r["component"] == component:
                    vals.append(r)
        if vals:
            agg[component] = {
                "mean_f1":        round(statistics.mean(v["f1"]        for v in vals), 4),
                "std_f1":         round(statistics.stdev(v["f1"]       for v in vals) if len(vals)>1 else 0, 4),
                "mean_precision": round(statistics.mean(v["precision"] for v in vals), 4),
                "mean_recall":    round(statistics.mean(v["recall"]    for v in vals), 4),
                "mean_fpr":       round(statistics.mean(v["fpr"]       for v in vals), 4),
                "mean_fnr":       round(statistics.mean(v["fnr"]       for v in vals), 4),
                "mean_latency_ms":round(statistics.mean(v["latency_ms"] for v in vals), 1),
                "n_datasets":     len(vals),
            }

    output = {
        "experiment": "ablation_study",
        "seed":       RANDOM_SEED,
        "per_dataset": all_results,
        "aggregate":   agg,
    }
    out_file = OUT / "ablation_results.json"
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)

    log.info(f"\n{'='*70}")
    log.info(f"Results saved → {out_file}")
    log.info("\nAggregate F1 by component:")
    for comp, v in sorted(agg.items(), key=lambda x: -x[1]["mean_f1"]):
        log.info(f"  {comp:<35s}  mean_F1={v['mean_f1']:.4f}  ±{v['std_f1']:.4f}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
