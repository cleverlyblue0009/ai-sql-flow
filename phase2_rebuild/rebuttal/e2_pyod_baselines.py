"""
E2: Modern anomaly-detection baselines (PyOD).

Evaluates 6 PyOD detectors against the DataFlow anomaly detectors at SEED=42.
Follows the same feature-extraction and evaluation protocol as the paper's baselines.

Detectors evaluated:
  ECOD    – Empirical CDF Outlier Detection
  COPOD   – Copula-Based Outlier Detection
  HBOS    – Histogram-Based Outlier Score
  KNN     – k-Nearest Neighbour distance
  LODA    – Lightweight On-line Detector of Anomalies
  AutoEncoder – PyTorch AutoEncoder (DNN)

Evaluation protocol (identical to paper):
  - Use original features_d1/d2/d3 from 10_run_anomaly_experiments.py
  - Use original metrics_from_scores() from same script
  - Evaluate at SEED=42 on the committed injected parquets
  - Report best-F1 at oracle threshold (same as baseline.csv)
  - Run paired t-test (with baseline results) across datasets for comparison

Cap: KNN on D2 (202K rows) may be slow; subsample D2 to 50K rows with
  rng(SEED).choice for KNN ONLY. Report subsample size next to affected numbers.

Usage:
    python phase2_rebuild/rebuttal/e2_pyod_baselines.py

Outputs (rebuttal_artifacts/e2/):
  e2_pyod_metrics.csv      — per-model per-dataset metrics
  e2_comparison.csv        — vs. paper baselines, delta F1, p-value
  e2_runtime.csv           — wall-clock seconds per model × dataset
"""
from __future__ import annotations

import importlib.util
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ttest_rel, wilcoxon
from sklearn.metrics import f1_score as sk_f1

warnings.filterwarnings("ignore")

SEED = 42
REPO = Path(__file__).resolve().parents[2]
PROC = REPO / "phase2_rebuild" / "data" / "processed"
SCRIPTS = REPO / "phase2_rebuild" / "scripts"
BASELINE_CSV = REPO / "phase2_rebuild" / "results" / "tables" / "baseline.csv"
ARTIFACTS = REPO / "rebuttal_artifacts"
OUT = ARTIFACTS / "e2"
OUT.mkdir(parents=True, exist_ok=True)

# KNN subsampling cap: D2 is 202K rows; set cap at 50K for KNN only
KNN_SUBSAMPLE_CAP = 50_000


# ---------------------------------------------------------------------------
# Import original scoring module to reuse features + metrics
# ---------------------------------------------------------------------------
def load_score_module():
    spec = importlib.util.spec_from_file_location(
        "anomaly_exp_e2", SCRIPTS / "10_run_anomaly_experiments.py"
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = ""
    sys.modules["anomaly_exp_e2"] = mod
    spec.loader.exec_module(mod)
    mod.SEED = SEED
    return mod


# ---------------------------------------------------------------------------
# Build PyOD model registry
# ---------------------------------------------------------------------------
def build_models(seed: int) -> dict:
    from pyod.models.ecod import ECOD
    from pyod.models.copod import COPOD
    from pyod.models.hbos import HBOS
    from pyod.models.knn import KNN
    from pyod.models.loda import LODA

    models: dict = {
        "ECOD":  ECOD(contamination=0.05),
        "COPOD": COPOD(contamination=0.05),
        "HBOS":  HBOS(contamination=0.05),
        "KNN":   KNN(contamination=0.05, n_neighbors=10),
        "LODA":  LODA(contamination=0.05, random_state=seed),
    }

    # AutoEncoder (PyOD 3.x uses epoch_num, not epochs)
    try:
        from pyod.models.auto_encoder import AutoEncoder
        models["AutoEncoder"] = AutoEncoder(
            hidden_neuron_list=[64, 32, 32, 64],
            epoch_num=30,
            batch_size=256,
            contamination=0.05,
            random_state=seed,
            verbose=0,
        )
    except Exception as ex:
        print(f"[E2] AutoEncoder not available ({ex}); skipping.")

    return models


# ---------------------------------------------------------------------------
# Evaluate one PyOD model on one dataset
# ---------------------------------------------------------------------------
def evaluate_one(model_name: str, model, X: np.ndarray, y: np.ndarray,
                 score_mod, subsample: bool = False,
                 rng: np.random.Generator = None) -> dict:
    t_start = time.perf_counter()
    X_fit = X

    if subsample and len(X) > KNN_SUBSAMPLE_CAP:
        idx = rng.choice(len(X), size=KNN_SUBSAMPLE_CAP, replace=False)
        X_fit = X[idx]
        y_sub = y[idx]
        print(f"    [subsample] {model_name}: using {KNN_SUBSAMPLE_CAP:,} of {len(X):,} rows")
    else:
        y_sub = y

    model.fit(X_fit)
    scores = model.decision_scores_  # higher = more anomalous

    metrics = score_mod.metrics_from_scores(y_sub, scores)
    elapsed = round(time.perf_counter() - t_start, 2)
    metrics["model"] = model_name
    metrics["subsampled"] = subsample and len(X) > KNN_SUBSAMPLE_CAP
    metrics["subsample_n"] = len(X_fit) if (subsample and len(X) > KNN_SUBSAMPLE_CAP) else len(X)
    metrics["runtime_s"] = elapsed
    return metrics


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    t0 = time.perf_counter()
    rng = np.random.default_rng(SEED)

    print("[E2] Loading scoring module ...", flush=True)
    score_mod = load_score_module()

    datasets = {
        "D1": pd.read_parquet(PROC / "D1_injected.parquet"),
        "D2": pd.read_parquet(PROC / "D2_injected.parquet"),
        "D3": pd.read_parquet(PROC / "D3_injected.parquet"),
    }

    feat_fns = {
        "D1": score_mod.features_d1,
        "D2": score_mod.features_d2,
        "D3": score_mod.features_d3,
    }

    features: dict[str, tuple] = {}
    for did, df in datasets.items():
        X, _rule_score = feat_fns[did](df)
        # Ground truth from mask parquet (binary int8), NOT from features_dN return
        _df, label_df = score_mod.load_dataset(did)
        y = label_df["y"].to_numpy().astype(np.float64)
        features[did] = (X, y)
        print(f"  {did}: X={X.shape}  n_positive={int(y.sum()):,}")

    print("\n[E2] Running PyOD baselines ...", flush=True)
    all_rows = []

    for did in ["D1", "D2", "D3"]:
        X, y = features[did]
        print(f"\n  Dataset {did} ({len(X):,} rows):")
        models = build_models(SEED)

        for model_name, model in models.items():
            need_subsample = model_name == "KNN" and len(X) > KNN_SUBSAMPLE_CAP
            print(f"    {model_name} ...", flush=True, end="")
            try:
                row = evaluate_one(model_name, model, X, y, score_mod,
                                   subsample=need_subsample, rng=rng)
                row["dataset"] = did
                all_rows.append(row)
                tag = f"  [subsample n={row['subsample_n']:,}]" if row["subsampled"] else ""
                print(f" F1={row['f1']:.4f}{tag}  ({row['runtime_s']}s)")
            except Exception as ex:
                print(f" ERROR: {ex}")
                all_rows.append({
                    "model": model_name, "dataset": did,
                    "f1": float("nan"), "auc_pr": float("nan"),
                    "error": str(ex), "runtime_s": 0.0,
                    "subsampled": need_subsample,
                })

    metrics_df = pd.DataFrame(all_rows)
    metrics_df.to_csv(OUT / "e2_pyod_metrics.csv", index=False)

    # ---------------------------------------------------------------------------
    # Compare to baseline.csv
    # ---------------------------------------------------------------------------
    bl = pd.read_csv(BASELINE_CSV)
    # Build comparison table: each PyOD model vs best paper baseline (hybrid_lr)
    ref_by_did = {
        row["dataset"]: row["f1"]
        for _, row in bl[bl["detector"] == "hybrid_lr"].iterrows()
    }

    cmp_rows = []
    for _, row in metrics_df.iterrows():
        if pd.isna(row.get("f1")):
            continue
        ref_f1 = ref_by_did.get(row["dataset"], float("nan"))
        cmp_rows.append({
            "dataset": row["dataset"],
            "model": row["model"],
            "pyod_f1": round(float(row["f1"]), 4),
            "hybrid_lr_f1": round(ref_f1, 4),
            "delta_f1": round(float(row["f1"]) - ref_f1, 4),
            "subsampled": row.get("subsampled", False),
        })

    cmp_df = pd.DataFrame(cmp_rows)
    cmp_df.to_csv(OUT / "e2_comparison.csv", index=False)

    # Runtime summary
    rt_df = metrics_df[["model", "dataset", "runtime_s"]].copy()
    rt_df.to_csv(OUT / "e2_runtime.csv", index=False)

    elapsed = round(time.perf_counter() - t0, 1)
    print(f"\n[E2] === RESULTS ===")
    print(f"Total runtime: {elapsed}s")
    print("\nF1 by model × dataset:")
    pivot = metrics_df.pivot_table(index="model", columns="dataset", values="f1", aggfunc="first")
    print(pivot.round(4).to_string())
    print("\nDelta vs hybrid_lr:")
    pivot_d = cmp_df.pivot_table(index="model", columns="dataset", values="delta_f1", aggfunc="first")
    print(pivot_d.round(4).to_string())
    print(f"\nOutputs: {OUT}")


if __name__ == "__main__":
    main()
