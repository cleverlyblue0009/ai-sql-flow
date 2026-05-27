#!/usr/bin/env python3
"""
Confidence Score Distribution Analysis — IEEE Access
Analyzes confidence score distributions, routing quality, and threshold effectiveness.
"""

import sys, json, logging, statistics
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_assets.experiments.experiment_config import RANDOM_SEED, RESULTS_DIR
from research_assets.experiments.experiment_engine import confidence_routing

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from scipy import stats as scipy_stats

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)
np.random.seed(RANDOM_SEED)
OUT = RESULTS_DIR / "confidence"
OUT.mkdir(parents=True, exist_ok=True)


# ── Confidence score generators ───────────────────────────────────────────────

def isolation_forest_scores(df: pd.DataFrame,
                              contamination: float = 0.10) -> np.ndarray:
    """Return anomaly scores normalized to [0, 1]."""
    numeric = df.select_dtypes(include=[np.number]).fillna(0)
    if numeric.empty or len(numeric) < 20:
        return np.full(len(df), 0.5)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(numeric)
    model  = IsolationForest(contamination=contamination,
                              random_state=RANDOM_SEED)
    model.fit(scaled)
    raw_scores = model.decision_function(scaled)  # higher = more normal
    # normalize to [0, 1]; invert so high = anomalous
    norm = (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min() + 1e-8)
    return 1.0 - norm   # confidence of being an anomaly


def tfidf_confidence_scores(df: pd.DataFrame,
                              text_cols: list,
                              threshold: float = 0.85) -> np.ndarray:
    """Return per-row duplicate-confidence scores from TF-IDF cosine similarity."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as cos_sim
    combined = df[text_cols].fillna("").astype(str).apply(" ".join, axis=1)
    if len(combined) < 2:
        return np.zeros(len(df))
    try:
        vec = TfidfVectorizer(max_features=500)
        mat = vec.fit_transform(combined)
        sim = cos_sim(mat)
        np.fill_diagonal(sim, 0)
        return sim.max(axis=1)
    except Exception:
        return np.zeros(len(df))


def composite_confidence_score(df: pd.DataFrame,
                                 text_cols: list) -> np.ndarray:
    """
    Weighted composite of IsolationForest + TF-IDF + null-rate per row.
    """
    w_if   = 0.45
    w_tfidf= 0.35
    w_null = 0.20

    if_scores = isolation_forest_scores(df)

    if text_cols and any(c in df.columns for c in text_cols):
        valid_txt = [c for c in text_cols if c in df.columns]
        tfidf_scores = tfidf_confidence_scores(df, valid_txt)
    else:
        tfidf_scores = np.zeros(len(df))

    null_scores = df.isnull().mean(axis=1).values  # fraction of nulls per row

    composite = (w_if * if_scores +
                 w_tfidf * tfidf_scores +
                 w_null  * null_scores)

    # clamp to [0, 1]
    composite = np.clip(composite, 0.0, 1.0)
    return composite


# ── Routing quality evaluation ─────────────────────────────────────────────────

def evaluate_routing(scores: np.ndarray,
                      y_true: np.ndarray,
                      low_th: float = 0.40,
                      high_th: float = 0.70) -> dict:
    routing = confidence_routing(scores, low_th, high_th)

    # High-confidence rejects (routing=0): are they truly anomalies?
    reject_mask = routing == 0
    accept_mask = routing == 2
    review_mask = routing == 1

    def safe_prec(pred, truth):
        if pred.sum() == 0:
            return float("nan")
        return float((pred & truth.astype(bool)).sum() / pred.sum())

    auto_accept_precision  = safe_prec(accept_mask, 1 - y_true)  # accepted should be clean
    auto_reject_precision  = safe_prec(reject_mask, y_true.astype(bool))   # rejected should be anomalies
    review_rate            = float(review_mask.mean())
    auto_accept_rate       = float(accept_mask.mean())
    auto_reject_rate       = float(reject_mask.mean())

    return {
        "low_threshold":  low_th,
        "high_threshold": high_th,
        "auto_accept_rate":       round(auto_accept_rate,       4),
        "manual_review_rate":     round(review_rate,            4),
        "auto_reject_rate":       round(auto_reject_rate,       4),
        "auto_accept_precision":  round(auto_accept_precision,  4) if not np.isnan(auto_accept_precision) else None,
        "auto_reject_precision":  round(auto_reject_precision,  4) if not np.isnan(auto_reject_precision) else None,
    }


# ── Threshold sweep ────────────────────────────────────────────────────────────

def threshold_sweep(scores: np.ndarray, y_true: np.ndarray) -> list:
    """Sweep binarization threshold and compute P/R/F1."""
    from research_assets.experiments.experiment_engine import compute_metrics
    thresholds = np.arange(0.1, 1.0, 0.05)
    rows = []
    for t in thresholds:
        y_pred = (scores > t).astype(int)
        m = compute_metrics(y_true, y_pred)
        m["threshold"] = round(float(t), 2)
        rows.append(m)
    return rows


# ── Confidence distribution statistics ────────────────────────────────────────

def describe_scores(scores: np.ndarray) -> dict:
    return {
        "mean":   round(float(scores.mean()), 4),
        "std":    round(float(scores.std()),  4),
        "min":    round(float(scores.min()),  4),
        "q25":    round(float(np.percentile(scores, 25)), 4),
        "median": round(float(np.median(scores)),         4),
        "q75":    round(float(np.percentile(scores, 75)), 4),
        "max":    round(float(scores.max()),  4),
        "skewness":   round(float(scipy_stats.skew(scores)),     4),
        "kurtosis":   round(float(scipy_stats.kurtosis(scores)), 4),
        "histogram":  np.histogram(scores, bins=20)[0].tolist(),
        "bin_edges":  [round(float(x), 3) for x in np.histogram(scores, bins=20)[1]],
    }


def main():
    log.info("=" * 70)
    log.info("CONFIDENCE ANALYSIS  —  IEEE Access Experiment")
    log.info("=" * 70)

    datasets = [
        ("gl_accounts",       ["account_name","account_type"]),
        ("trial_balance",     ["account_id","period"]),
        ("journal_entries",   ["description","dr_account"]),
        ("mapping_table",     ["source_account","target_account"]),
    ]

    all_results = {}
    ds_dir = Path(__file__).resolve().parents[1] / "datasets"

    for ds_name, text_cols in datasets:
        log.info(f"\nDataset: {ds_name}")
        try:
            df  = pd.read_csv(ds_dir / f"{ds_name}.csv")
            gt_file = ds_dir / f"{ds_name}_ground_truth.json"
            gt  = json.loads(gt_file.read_text()) if gt_file.exists() else {}

            rng = np.random.default_rng(RANDOM_SEED)
            n_anom = min(gt.get("total_anomalies", int(len(df)*0.10)), len(df))
            y_true = np.zeros(len(df), dtype=int)
            y_true[rng.choice(len(df), n_anom, replace=False)] = 1

            scores = composite_confidence_score(df, text_cols)

            dist_stats = describe_scores(scores)
            routing_std = evaluate_routing(scores, y_true)
            routing_tight = evaluate_routing(scores, y_true, low_th=0.30, high_th=0.80)
            thresh_sweep = threshold_sweep(scores, y_true)

            # Best threshold by F1
            best = max(thresh_sweep, key=lambda x: x["f1"])

            all_results[ds_name] = {
                "n_rows":          len(df),
                "anomaly_rate":    float(y_true.mean()),
                "score_distribution": dist_stats,
                "routing_standard": routing_std,
                "routing_tight":    routing_tight,
                "threshold_sweep":  thresh_sweep,
                "best_threshold":   best["threshold"],
                "best_f1":          best["f1"],
            }

            log.info(f"  scores:  mean={dist_stats['mean']:.4f}  "
                     f"std={dist_stats['std']:.4f}  "
                     f"skew={dist_stats['skewness']:.3f}")
            log.info(f"  routing: accept={routing_std['auto_accept_rate']:.1%}  "
                     f"review={routing_std['manual_review_rate']:.1%}  "
                     f"reject={routing_std['auto_reject_rate']:.1%}")
            log.info(f"  best threshold={best['threshold']:.2f}  F1={best['f1']:.4f}")

        except Exception as e:
            log.error(f"  FAILED: {e}", exc_info=True)

    out_file = OUT / "confidence_results.json"
    with open(out_file, "w") as f:
        json.dump({"experiment":"confidence_analysis",
                    "seed": RANDOM_SEED,
                    "datasets": all_results}, f, indent=2)

    log.info(f"\nSaved → {out_file}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
