"""
E4: Confidence-aware routing.

Tests a 3-lane selective prediction policy on top of the stacked hybrid_lr scores:
  Lane AUTO-CLEAN : score < low_tau   → auto-quarantine   (high anomaly confidence)
  Lane MANUAL-REVIEW: low_tau ≤ score ≤ high_tau → send to analyst
  Lane AUTO-PASS  : score > high_tau  → auto-pass          (high clean confidence)

Measures:
  1. Coverage (fraction of rows in each lane) at representative threshold pairs
  2. Precision / recall in AUTO-CLEAN (is the auto-quarantine right?)
  3. Analyst workload in MANUAL-REVIEW lane
  4. ECE (Expected Calibration Error) of hybrid_lr scores as probabilities
  5. Platt-scaled calibration: does calibration improve the policy?

Outputs (rebuttal_artifacts/e4/):
  e4_routing_metrics.csv     — coverage/precision/recall/workload by lane and threshold
  e4_calibration.csv         — ECE before/after Platt scaling, per dataset
  e4_routing_grid.csv        — exhaustive (low_tau, high_tau) grid for a figure
"""
from __future__ import annotations

import importlib.util
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (brier_score_loss, f1_score,
                             precision_score, recall_score)
from sklearn.model_selection import StratifiedKFold

warnings.filterwarnings("ignore")

SEED = 42
REPO = Path(__file__).resolve().parents[2]
SCORES_DIR = REPO / "phase2_rebuild" / "results" / "scores"
SCRIPTS = REPO / "phase2_rebuild" / "scripts"
ARTIFACTS = REPO / "rebuttal_artifacts"
OUT = ARTIFACTS / "e4"
OUT.mkdir(parents=True, exist_ok=True)


def load_scores(did: str) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_parquet(SCORES_DIR / f"{did}_scores.parquet")
    scores = df["hybrid_lr"].to_numpy()
    y = df["y"].to_numpy().astype(float)
    return scores, y


def expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray,
                                n_bins: int = 10) -> float:
    """ECE: weighted mean of |accuracy - confidence| per bin."""
    y_bin = (y_true > 0.5).astype(int)
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        in_bin = (y_prob >= bins[i]) & (y_prob < bins[i + 1])
        if in_bin.sum() == 0:
            continue
        acc = y_bin[in_bin].mean()
        conf = y_prob[in_bin].mean()
        ece += in_bin.sum() * abs(acc - conf)
    return ece / max(1, len(y_true))


def platt_scale(scores: np.ndarray, y: np.ndarray, seed: int) -> np.ndarray:
    """Fit a logistic regression on OOF scores for Platt scaling."""
    y_bin = (y > 0.5).astype(int)
    kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    cal_scores = np.zeros(len(scores))
    lr = LogisticRegression(solver="lbfgs", max_iter=500)
    for tr, te in kf.split(scores.reshape(-1, 1), y_bin):
        lr.fit(scores[tr].reshape(-1, 1), y_bin[tr])
        cal_scores[te] = lr.predict_proba(scores[te].reshape(-1, 1))[:, 1]
    return cal_scores


def routing_metrics(scores: np.ndarray, y: np.ndarray,
                     low_tau: float, high_tau: float) -> dict:
    """
    Lane AUTO-CLEAN:    score >= high_tau  (high anomaly confidence)
    Lane MANUAL-REVIEW: low_tau <= score < high_tau
    Lane AUTO-PASS:     score < low_tau    (high clean confidence)
    """
    y_bin = (y > 0.5).astype(int)
    n = len(y)

    auto_clean_mask   = scores >= high_tau
    manual_mask       = (scores >= low_tau) & (scores < high_tau)
    auto_pass_mask    = scores < low_tau

    def lane_metrics(mask: np.ndarray, predicted_label: int) -> dict:
        if mask.sum() == 0:
            return {"coverage": 0.0, "n": 0, "precision": float("nan"),
                    "recall": float("nan"), "accuracy": float("nan")}
        coverage = mask.sum() / n
        y_sub = y_bin[mask]
        n_sub = int(mask.sum())
        if predicted_label == 1:
            acc = y_sub.mean()
            prec = precision_score(y_sub, np.ones(n_sub, int), zero_division=0)
            rec = recall_score(y_sub, np.ones(n_sub, int), zero_division=0)
        else:
            acc = (1 - y_sub).mean()
            prec = precision_score(1 - y_sub, np.ones(n_sub, int), zero_division=0)
            rec = recall_score(1 - y_sub, np.ones(n_sub, int), zero_division=0)
        return {"coverage": round(float(coverage), 4), "n": n_sub,
                "precision": round(float(prec), 4), "recall": round(float(rec), 4),
                "accuracy": round(float(acc), 4)}

    ac = lane_metrics(auto_clean_mask, predicted_label=1)
    mr = lane_metrics(manual_mask, predicted_label=-1)
    ap = lane_metrics(auto_pass_mask, predicted_label=0)

    analyst_burden = float(manual_mask.sum() / n)
    missed_anomalies_in_pass = int(y_bin[auto_pass_mask].sum())

    return {
        "low_tau": round(low_tau, 4),
        "high_tau": round(high_tau, 4),
        "auto_clean_coverage":   ac["coverage"],
        "auto_clean_precision":  ac["precision"],
        "auto_clean_recall":     ac.get("recall", float("nan")),
        "manual_review_coverage": mr["coverage"],
        "analyst_burden":        round(analyst_burden, 4),
        "auto_pass_coverage":    ap["coverage"],
        "auto_pass_accuracy":    ap["accuracy"],
        "missed_anomalies_in_pass": missed_anomalies_in_pass,
    }


def main():
    t0 = time.perf_counter()
    all_routing = []
    all_calibration = []
    all_grid = []

    for did in ["D1", "D2", "D3"]:
        print(f"[E4] Dataset {did} ...", flush=True)
        scores, y = load_scores(did)
        y_bin = (y > 0.5).astype(int)
        n_pos = int(y_bin.sum())
        print(f"  {len(y):,} rows, {n_pos:,} positives")

        # Calibration (raw scores)
        ece_raw = expected_calibration_error(y, scores)
        brier_raw = brier_score_loss(y_bin, scores)

        # Platt scaling
        cal_scores = platt_scale(scores, y, SEED)
        ece_cal = expected_calibration_error(y, cal_scores)
        brier_cal = brier_score_loss(y_bin, cal_scores)

        all_calibration.append({
            "dataset": did,
            "ece_raw": round(ece_raw, 5),
            "brier_raw": round(brier_raw, 5),
            "ece_platt": round(ece_cal, 5),
            "brier_platt": round(brier_cal, 5),
            "ece_improvement": round(ece_raw - ece_cal, 5),
        })
        print(f"  ECE raw={ece_raw:.5f}  ECE_platt={ece_cal:.5f}  Brier raw={brier_raw:.5f}")

        # Representative 3-lane thresholds
        bl_csv = pd.read_csv(REPO / "phase2_rebuild" / "results" / "tables" / "baseline.csv")
        best_tau = float(bl_csv[(bl_csv["dataset"] == did) & (bl_csv["detector"] == "hybrid_lr")]["best_threshold"].iloc[0])

        # Try a range of (low_tau, high_tau) pairs
        quantiles = [0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.99]
        taus = np.quantile(scores, quantiles)

        # Representative pairs from the routing report
        rep_pairs = [
            (taus[0], taus[4]),  # (q50, q90)
            (taus[1], taus[4]),  # (q60, q90)
            (taus[1], taus[5]),  # (q60, q95)
            (taus[2], taus[5]),  # (q70, q95)
            (taus[2], taus[6]),  # (q70, q99)
        ]
        for low_tau, high_tau in rep_pairs:
            m = routing_metrics(scores, y, low_tau, high_tau)
            m["dataset"] = did
            all_routing.append(m)
            print(f"  tau=({low_tau:.3f},{high_tau:.3f}): clean={m['auto_clean_coverage']:.2%}  review={m['manual_review_coverage']:.2%}  pass={m['auto_pass_coverage']:.2%}  missed={m['missed_anomalies_in_pass']}")

        # Grid for figure (exhaustive)
        tq = np.quantile(scores, np.linspace(0.40, 0.99, 15))
        for i, lt in enumerate(tq):
            for j, ht in enumerate(tq):
                if ht <= lt:
                    continue
                gm = routing_metrics(scores, y, lt, ht)
                gm["dataset"] = did
                all_grid.append(gm)

    pd.DataFrame(all_routing).to_csv(OUT / "e4_routing_metrics.csv", index=False)
    pd.DataFrame(all_calibration).to_csv(OUT / "e4_calibration.csv", index=False)
    pd.DataFrame(all_grid).to_csv(OUT / "e4_routing_grid.csv", index=False)

    elapsed = round(time.perf_counter() - t0, 1)
    print(f"\n[E4] Done in {elapsed}s")
    print("\nCalibration summary:")
    print(pd.DataFrame(all_calibration).to_string(index=False))
    print(f"\nOutputs: {OUT}")


if __name__ == "__main__":
    main()
