"""
E7: Limits of injected anomalies — prevalence sweep.

Tests how the DataFlow hybrid_lr model (trained at ~5% prevalence) generalises
to different effective prevalence regimes by subsampling the committed D3 scored data.

Method:
  For each target prevalence P ∈ {1%, 2%, 3%, 5%, 7%, 10%, 15%, 20%, 25%, 30%}:
    - Keep all N_anomaly rows (n=1,500 for D3)
    - Subsample N_clean rows to achieve N_anomaly/N_clean = P/(1-P)
    - Evaluate hybrid_lr scores at:
        (a) fixed tau from baseline.csv (paper threshold — may be miscalibrated)
        (b) oracle tau (best F1 on this subsample — upper bound)
    - Report F1, precision, recall, AUC-PR

  Subsampling protocol: seeded rng(SEED), reproducible.
  Subsample size is printed next to every metric.

Also runs D1 and D2 (same method).

Outputs (rebuttal_artifacts/e7/):
  e7_prevalence_sweep.csv   — full metrics by dataset and prevalence
  e7_fixed_vs_oracle.csv    — fixed-tau vs oracle-tau F1 gap
"""
from __future__ import annotations

import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

SEED = 42
REPO = Path(__file__).resolve().parents[2]
SCORES_DIR = REPO / "phase2_rebuild" / "results" / "scores"
BASELINE_CSV = REPO / "phase2_rebuild" / "results" / "tables" / "baseline.csv"
ARTIFACTS = REPO / "rebuttal_artifacts"
OUT = ARTIFACTS / "e7"
OUT.mkdir(parents=True, exist_ok=True)

PREVALENCES = [0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20, 0.25, 0.30]


def load_scores(did: str) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_parquet(SCORES_DIR / f"{did}_scores.parquet")
    scores = df["hybrid_lr"].to_numpy()
    y = (df["y"].to_numpy() > 0.5).astype(int)
    return scores, y


def metrics_at_threshold(y: np.ndarray, scores: np.ndarray, tau: float) -> dict:
    from sklearn.metrics import (f1_score, precision_score, recall_score,
                                  average_precision_score)
    pred = (scores >= tau).astype(int)
    return {
        "f1":        round(float(f1_score(y, pred, zero_division=0)), 4),
        "precision": round(float(precision_score(y, pred, zero_division=0)), 4),
        "recall":    round(float(recall_score(y, pred, zero_division=0)), 4),
        "auc_pr":    round(float(average_precision_score(y, scores)) if scores.std() > 0 else float("nan"), 4),
    }


def oracle_f1(y: np.ndarray, scores: np.ndarray) -> tuple[float, float]:
    """Oracle: best F1 at any threshold."""
    from sklearn.metrics import precision_recall_curve
    p, r, thr = precision_recall_curve(y, scores)
    f1s = 2 * p[:-1] * r[:-1] / np.where((p[:-1] + r[:-1]) > 0, p[:-1] + r[:-1], 1)
    best = int(np.nanargmax(f1s))
    return float(f1s[best]), float(thr[best])


def sweep_prevalence(did: str, scores: np.ndarray, y: np.ndarray, tau: float) -> list[dict]:
    rng = np.random.default_rng(SEED)
    pos_idx = np.where(y == 1)[0]
    neg_idx = np.where(y == 0)[0]
    n_pos = len(pos_idx)
    n_total_full = len(y)
    rows = []

    for prev in PREVALENCES:
        # How many clean rows to include to achieve this prevalence?
        n_neg_target = int(n_pos * (1 - prev) / max(prev, 1e-6))
        n_neg_target = min(n_neg_target, len(neg_idx))
        if n_neg_target < 10:
            continue

        # Subsample clean rows (seeded)
        chosen_neg = rng.choice(neg_idx, size=n_neg_target, replace=False)
        idx = np.concatenate([pos_idx, chosen_neg])
        y_sub = y[idx]
        s_sub = scores[idx]
        actual_prev = float(y_sub.sum() / len(y_sub))

        # Fixed threshold metrics
        fixed_m = metrics_at_threshold(y_sub, s_sub, tau)
        # Oracle threshold
        ormax_f1, oracle_tau = oracle_f1(y_sub, s_sub)

        rows.append({
            "dataset": did,
            "target_prevalence": round(prev, 3),
            "actual_prevalence": round(actual_prev, 4),
            "n_pos": int(y_sub.sum()),
            "n_neg": n_neg_target,
            "n_total": len(y_sub),
            "f1_fixed_tau":   fixed_m["f1"],
            "prec_fixed_tau": fixed_m["precision"],
            "rec_fixed_tau":  fixed_m["recall"],
            "auc_pr":         fixed_m["auc_pr"],
            "f1_oracle_tau":  round(ormax_f1, 4),
            "fixed_oracle_gap": round(ormax_f1 - fixed_m["f1"], 4),
        })
        print(f"  {did} prev={prev:.0%}: F1_fixed={fixed_m['f1']:.4f}  F1_oracle={ormax_f1:.4f}  n={len(y_sub):,}")

    return rows


def main():
    t0 = time.perf_counter()
    bl = pd.read_csv(BASELINE_CSV)

    all_rows = []
    for did in ["D1", "D2", "D3"]:
        print(f"\n[E7] Dataset {did} ...", flush=True)
        scores, y = load_scores(did)
        tau = float(bl[(bl["dataset"] == did) & (bl["detector"] == "hybrid_lr")]["best_threshold"].iloc[0])
        print(f"  n_pos={y.sum():,}  n_neg={(1-y).sum():,}  tau={tau:.5f}")
        rows = sweep_prevalence(did, scores, y, tau)
        all_rows.extend(rows)

    sweep_df = pd.DataFrame(all_rows)
    sweep_df.to_csv(OUT / "e7_prevalence_sweep.csv", index=False)

    # Fixed vs oracle gap summary
    gap_df = sweep_df[["dataset", "target_prevalence", "f1_fixed_tau", "f1_oracle_tau",
                         "fixed_oracle_gap"]].copy()
    gap_df.to_csv(OUT / "e7_fixed_vs_oracle.csv", index=False)

    elapsed = round(time.perf_counter() - t0, 1)
    print(f"\n[E7] Done in {elapsed}s")
    print("\nPrevalence sweep summary (fixed-tau F1):")
    pivot = sweep_df.pivot_table(index="target_prevalence", columns="dataset",
                                  values="f1_fixed_tau", aggfunc="first")
    print(pivot.round(4).to_string())
    print("\nFixed vs oracle F1 gap at 5% prevalence (paper setting):")
    at5 = sweep_df[sweep_df["target_prevalence"] == 0.05][["dataset", "f1_fixed_tau", "f1_oracle_tau", "fixed_oracle_gap"]]
    print(at5.to_string(index=False))
    print(f"\nOutputs: {OUT}")


if __name__ == "__main__":
    main()
