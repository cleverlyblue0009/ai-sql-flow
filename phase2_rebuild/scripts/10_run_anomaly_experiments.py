"""
Phase 3 — Anomaly detection on D1/D2/D3 injected datasets.

Detector families (each emits a per-row anomaly score in [0,1]):
    rule    — domain rules from the injection plan (sign / range / schema).
    stat    — robust z-score / IQR on per-group numeric features.
    iforest — sklearn IsolationForest on a small feature matrix.
    lof     — sklearn LocalOutlierFactor (novelty=False; reuse all data).
    hybrid  — late-fusion: max(rule, stat, iforest, lof) per row.

Metrics emitted per detector per dataset:
    precision, recall, F1, balanced_accuracy, AUC-PR (when score available),
    FPR @ optimal-F1 threshold, support, and per-family recall.

Outputs (all under phase2_rebuild/results/):
    tables/baseline.csv             one row per (dataset, detector)
    tables/per_family.csv           one row per (dataset, detector, family)
    tables/threshold_sweep.csv      threshold sweep for hybrid
    tables/cv.csv                   5-fold CV on hybrid
    tables/ablation.csv             leave-one-detector-out from hybrid
    tables/scalability.csv          hybrid on D2 sub-samples
    scores/D{1,2,3}_scores.parquet  per-row detector scores + label (for figures)
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                              f1_score, precision_recall_curve,
                              precision_recall_fscore_support)
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

REPO = Path(__file__).resolve().parents[2]
PROC = REPO / "phase2_rebuild" / "data" / "processed"
LABELS = REPO / "phase2_rebuild" / "data" / "labels"
RESULTS = REPO / "phase2_rebuild" / "results"
(RESULTS / "tables").mkdir(parents=True, exist_ok=True)
(RESULTS / "scores").mkdir(parents=True, exist_ok=True)

SEED = 42
rng_global = np.random.default_rng(SEED)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_dataset(did: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_parquet(PROC / f"{did}_injected.parquet").reset_index(drop=True)
    mask = pd.read_parquet(LABELS / f"{did}_mask.parquet")
    y = np.zeros(len(df), dtype=np.int8)
    family = np.array([""] * len(df), dtype=object)
    for _, r in mask.iterrows():
        ri = int(r["row_index"])
        if 0 <= ri < len(df):
            y[ri] = 1
            family[ri] = str(r["anomaly_type"])
    label_df = pd.DataFrame({"y": y, "family": family})
    return df, label_df


def metrics_from_scores(y: np.ndarray, scores: np.ndarray) -> dict:
    """Threshold-free + best-F1 threshold metrics."""
    auc_pr = float(average_precision_score(y, scores)) if scores.std() > 0 else float("nan")
    prec, rec, thr = precision_recall_curve(y, scores)
    # Best F1 threshold (drop the implicit final point where recall=0)
    f1s = (2 * prec[:-1] * rec[:-1]) / np.where((prec[:-1] + rec[:-1]) > 0, prec[:-1] + rec[:-1], 1)
    best = int(np.nanargmax(f1s)) if len(f1s) else 0
    best_thr = float(thr[best]) if len(thr) else 0.5
    pred = (scores >= best_thr).astype(np.int8)
    p, r, f, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    fpr = float((pred & (y == 0)).sum() / max(1, (y == 0).sum()))
    bal = float(balanced_accuracy_score(y, pred))
    return {
        "auc_pr": auc_pr,
        "best_threshold": best_thr,
        "precision": float(p),
        "recall": float(r),
        "f1": float(f),
        "balanced_acc": bal,
        "fpr_at_best_f1": fpr,
    }


def safe_log10(x: pd.Series) -> pd.Series:
    return np.log10(np.maximum(np.abs(x.astype(float)), 1e-9))


# ---------------------------------------------------------------------------
# Per-dataset feature extraction + per-family rule scoring
# ---------------------------------------------------------------------------
def features_d1(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Returns (X for ML, rule_score in [0,1])."""
    v = df["value"].astype(float)
    log_abs_v = safe_log10(v)
    qtrs = df["qtrs"].astype(float).fillna(0)
    ddate = df["ddate"].astype(float).fillna(0)
    year = (ddate // 10000).astype(float)

    # Robust z by tag for log|value|
    tag_med = log_abs_v.groupby(df["tag"]).transform("median")
    tag_mad = log_abs_v.groupby(df["tag"]).transform(lambda s: (s - s.median()).abs().median())
    z = (log_abs_v - tag_med).abs() / np.where(tag_mad > 1e-6, 1.4826 * tag_mad, 1.0)

    # Duplicate detection: same (adsh, tag, value)
    dup_key = df.groupby(["adsh", "tag", "value"]).cumcount()
    is_dup = (dup_key > 0).astype(int)

    # Period violation rule: 2024Q4 filings expect ddate years roughly 2020-2025
    period_bad = ((year < 2018) | (year > 2026)).astype(int)

    # Sign rule: a small set of always-positive GAAP tags
    pos_tags = {"Assets", "Revenues", "CashAndCashEquivalents",
                "CashAndCashEquivalentsAtCarryingValue", "AssetsCurrent",
                "LiabilitiesCurrent", "Liabilities", "StockholdersEquity",
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "CommonStockSharesOutstanding"}
    sign_bad = (df["tag"].isin(pos_tags) & (v < 0)).astype(int)

    rule_score = np.clip(0.6 * sign_bad + 0.6 * is_dup + 0.6 * period_bad
                          + 0.4 * (z > 4).astype(int), 0, 1)

    X = np.column_stack([
        log_abs_v.fillna(0).to_numpy(),
        z.fillna(0).to_numpy(),
        is_dup.to_numpy(),
        sign_bad.to_numpy(),
        period_bad.to_numpy(),
        qtrs.to_numpy(),
    ])
    return X, rule_score.to_numpy()


def features_d2(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    base = df["Base Salary"].astype(float).fillna(0)
    rgp = df["Regular Gross Paid"].astype(float).fillna(0)
    rh = df["Regular Hours"].astype(float).fillna(0)
    otp = df["Total OT Paid"].astype(float).fillna(0)

    # Robust z by Agency for log Regular Gross Paid
    log_rgp = safe_log10(rgp + 1)
    g = df.groupby("Agency Name")
    med = log_rgp.groupby(df["Agency Name"]).transform("median")
    mad = log_rgp.groupby(df["Agency Name"]).transform(lambda s: (s - s.median()).abs().median())
    z = (log_rgp - med).abs() / np.where(mad > 1e-6, 1.4826 * mad, 1.0)

    # Salary/basis rule
    per_annum_low = ((df["Pay Basis"] == "per Annum") & (base > 10000) & (rgp < 0.05 * base)).astype(int)
    # OT vs Regular rule
    ot_no_reg = ((rh == 0) & (otp > 0)).astype(int)
    # Near-duplicate name rule via groupby cumulative count (Last Name + Agency)
    df_keys = df["Last Name"].fillna("").str.upper() + "|" + df["Agency Name"].fillna("").str.upper()
    dup = (df_keys.groupby(df_keys).cumcount() > 0).astype(int)

    # Agency-title violation rule (very small heuristic): mention 'TEACHER' in non-DOE agency
    title_u = df["Title Description"].fillna("").str.upper()
    agency_u = df["Agency Name"].fillna("").str.upper()
    title_wrong = (((title_u.str.contains("TEACHER")) & (~agency_u.str.contains("EDUCATION|DEPT OF ED")))
                   | ((title_u.str.contains("FIREFIGHTER")) & (~agency_u.str.contains("FIRE")))
                   | ((title_u.str.contains("LIBRARIAN")) & (~agency_u.str.contains("LIBRARY|POLICE|EDUCATION")))).astype(int)

    rule_score = np.clip(0.6 * per_annum_low + 0.6 * ot_no_reg + 0.5 * dup + 0.5 * title_wrong
                          + 0.4 * (z > 4).astype(int), 0, 1)

    X = np.column_stack([
        base.to_numpy(), rgp.to_numpy(), rh.to_numpy(), otp.to_numpy(),
        log_rgp.fillna(0).to_numpy(),
        z.fillna(0).to_numpy(),
        per_annum_low.to_numpy(),
        ot_no_reg.to_numpy(),
        dup.to_numpy(),
        title_wrong.to_numpy(),
    ])
    return X, rule_score.to_numpy()


def features_d3(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    edu = df["EDUCATION"].astype(int)
    lim = df["LIMIT_BAL"].astype(int)
    bill1 = df["BILL_AMT1"].astype(int)
    pay0 = df["PAY_0"].astype(int)
    age = df["AGE"].astype(int)
    deflt = df["default payment next month"].astype(int)

    # Rules per injection-plan families
    edu_oob = (~edu.isin([0, 1, 2, 3, 4, 5, 6])).astype(int)
    limit_bad = ((lim == 0) & (bill1 > 0) & (deflt == 0)).astype(int)
    bill_neg_strange = (bill1 < 0).astype(int)
    pay_temporal_bad = ((pay0 == -2) & (bill1 > 5000)).astype(int)
    age_bad = ((age < 18) | (age > 95)).astype(int)

    rule_score = np.clip(0.7 * edu_oob + 0.6 * limit_bad + 0.5 * bill_neg_strange
                          + 0.6 * pay_temporal_bad + 0.7 * age_bad, 0, 1)

    feature_cols = ["LIMIT_BAL", "AGE", "BILL_AMT1", "PAY_0", "PAY_AMT1", "EDUCATION", "MARRIAGE", "SEX"]
    X = df[feature_cols].astype(float).to_numpy()
    X = np.column_stack([X, edu_oob.to_numpy(), limit_bad.to_numpy(),
                         bill_neg_strange.to_numpy(), pay_temporal_bad.to_numpy(),
                         age_bad.to_numpy()])
    return X, rule_score.to_numpy()


FEATURE_FNS = {"D1": features_d1, "D2": features_d2, "D3": features_d3}


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------
def stat_score(X: np.ndarray) -> np.ndarray:
    """Average robust z over the numeric columns, mapped to [0,1] via 1-exp(-z/4)."""
    Xs = X.copy().astype(float)
    med = np.median(Xs, axis=0)
    mad = np.median(np.abs(Xs - med), axis=0)
    mad = np.where(mad > 1e-9, mad, 1.0)
    z = np.abs((Xs - med) / (1.4826 * mad))
    avg_z = z.mean(axis=1)
    return 1.0 - np.exp(-avg_z / 4.0)


def iforest_score(X: np.ndarray) -> np.ndarray:
    Xs = StandardScaler().fit_transform(X)
    iso = IsolationForest(n_estimators=200, random_state=SEED, contamination="auto",
                          n_jobs=-1)
    iso.fit(Xs)
    raw = -iso.score_samples(Xs)  # higher = more anomalous
    return (raw - raw.min()) / max(1e-9, raw.max() - raw.min())


def lof_score(X: np.ndarray) -> np.ndarray:
    Xs = StandardScaler().fit_transform(X)
    n_neighbors = min(50, max(5, len(X) // 1000))
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, n_jobs=-1)
    lof.fit_predict(Xs)
    raw = -lof.negative_outlier_factor_
    return (raw - raw.min()) / max(1e-9, raw.max() - raw.min())


def hybrid_score(rule: np.ndarray, stat: np.ndarray, iso: np.ndarray,
                 lof: np.ndarray, weights=(0.35, 0.20, 0.30, 0.15)) -> np.ndarray:
    w = np.array(weights, dtype=float)
    w = w / w.sum()
    return w[0] * rule + w[1] * stat + w[2] * iso + w[3] * lof


def stacked_hybrid_score(y: np.ndarray, base_scores: np.ndarray, k: int = 5) -> np.ndarray:
    """Logistic-regression stacker over base detectors with k-fold OOF predictions."""
    out = np.zeros(len(y), dtype=float)
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=SEED)
    for tr, te in skf.split(base_scores, y):
        clf = LogisticRegression(max_iter=2000, class_weight="balanced",
                                  random_state=SEED, solver="liblinear")
        clf.fit(base_scores[tr], y[tr])
        out[te] = clf.predict_proba(base_scores[te])[:, 1]
    return out


def xgb_stacked_hybrid_score(y: np.ndarray, base_scores: np.ndarray, k: int = 5) -> np.ndarray:
    """XGBoost stacker over base detectors with k-fold OOF predictions.

    Uses scale_pos_weight to handle class imbalance without changing the
    class distribution via resampling or class_weight.
    """
    n_neg = int((y == 0).sum())
    n_pos = int((y == 1).sum())
    spw = max(1.0, n_neg / max(1, n_pos))
    out = np.zeros(len(y), dtype=float)
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=SEED)
    for tr, te in skf.split(base_scores, y):
        clf = XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=1.0,
            scale_pos_weight=spw, random_state=SEED,
            eval_metric="logloss", use_label_encoder=False,
            verbosity=0, n_jobs=-1,
        )
        clf.fit(base_scores[tr], y[tr])
        out[te] = clf.predict_proba(base_scores[te])[:, 1]
    return out


DETECTORS = ["rule", "stat", "iforest", "lof", "hybrid", "hybrid_lr", "hybrid_xgb"]


# ---------------------------------------------------------------------------
# Run a single dataset end-to-end
# ---------------------------------------------------------------------------
@dataclass
class DatasetRun:
    dataset_id: str
    n_rows: int
    n_anomalies: int
    scores: pd.DataFrame
    baseline_rows: list[dict]
    family_rows: list[dict]


def run_dataset(did: str) -> DatasetRun:
    df, lab = load_dataset(did)
    y = lab["y"].to_numpy()
    fam = lab["family"].to_numpy()
    print(f"  rows={len(df)} anomalies={int(y.sum())}")
    feat_fn = FEATURE_FNS[did]
    X, rule = feat_fn(df)
    stat = stat_score(X)
    iso = iforest_score(X)
    lof = lof_score(X)
    hyb = hybrid_score(rule, stat, iso, lof)
    base_scores = np.column_stack([rule, stat, iso, lof])
    hyb_lr = stacked_hybrid_score(y, base_scores)
    hyb_xgb = xgb_stacked_hybrid_score(y, base_scores)

    scores = pd.DataFrame({"y": y, "family": fam,
                           "rule": rule, "stat": stat,
                           "iforest": iso, "lof": lof,
                           "hybrid": hyb, "hybrid_lr": hyb_lr,
                           "hybrid_xgb": hyb_xgb})

    baseline_rows = []
    for name in DETECTORS:
        m = metrics_from_scores(y, scores[name].to_numpy())
        m["dataset"] = did
        m["detector"] = name
        # Stop-condition tripwire from rebuild contract.
        if any(m[k] >= 0.99 for k in ("precision", "recall", "f1", "auc_pr") if not np.isnan(m[k])):
            print(f"  TRIPWIRE: {did}/{name} hit ≥99% — {m}")
        baseline_rows.append(m)

    # Per-family recall at hybrid_xgb best-F1 threshold (the adopted stacker).
    base_hyb = next(r for r in baseline_rows if r["detector"] == "hybrid_xgb")
    thr = base_hyb["best_threshold"]
    pred = (hyb_xgb >= thr).astype(int)
    family_rows = []
    for f in sorted({x for x in fam if x}):
        mask = fam == f
        tp = int((pred[mask] == 1).sum())
        n = int(mask.sum())
        family_rows.append({"dataset": did, "family": f,
                            "n_injected": n, "recovered": tp,
                            "recall": tp / max(1, n)})
    return DatasetRun(did, len(df), int(y.sum()), scores, baseline_rows, family_rows)


# ---------------------------------------------------------------------------
# CV / ablation / scalability
# ---------------------------------------------------------------------------
def cv_eval(did: str, runs: dict, k: int = 5) -> list[dict]:
    """K-fold CV on hybrid_xgb scores: re-threshold within each fold for honest reporting."""
    sc = runs[did].scores.copy()
    y = sc["y"].to_numpy()
    hyb = sc["hybrid_xgb"].to_numpy()
    kf = KFold(n_splits=k, shuffle=True, random_state=SEED)
    rows = []
    for i, (tr, te) in enumerate(kf.split(hyb)):
        prec, rec, thr = precision_recall_curve(y[tr], hyb[tr])
        f1s = (2 * prec[:-1] * rec[:-1]) / np.where((prec[:-1] + rec[:-1]) > 0, prec[:-1] + rec[:-1], 1)
        bt = float(thr[int(np.nanargmax(f1s))]) if len(thr) else 0.5
        pred_te = (hyb[te] >= bt).astype(int)
        p, r, f, _ = precision_recall_fscore_support(y[te], pred_te, average="binary", zero_division=0)
        rows.append({"dataset": did, "fold": i + 1, "n_test": len(te),
                     "threshold_from_train": bt,
                     "precision": float(p), "recall": float(r), "f1": float(f)})
    return rows


def ablation_eval(did: str, runs: dict) -> list[dict]:
    """Leave-one-detector-out from the hybrid_xgb stacker (refit on remaining detectors)."""
    sc = runs[did].scores.copy()
    y = sc["y"].to_numpy()
    cols = ["rule", "stat", "iforest", "lof"]
    rows = []
    full_scores = sc[cols].to_numpy()
    full_hyb = xgb_stacked_hybrid_score(y, full_scores)
    m = metrics_from_scores(y, full_hyb)
    rows.append({"dataset": did, "leave_out": "none",
                 "f1": m["f1"], "precision": m["precision"],
                 "recall": m["recall"], "auc_pr": m["auc_pr"]})
    for drop in cols:
        keep = [c for c in cols if c != drop]
        sub = sc[keep].to_numpy()
        if sub.shape[1] == 0:
            continue
        hyb = xgb_stacked_hybrid_score(y, sub)
        m = metrics_from_scores(y, hyb)
        rows.append({"dataset": did, "leave_out": drop,
                     "f1": m["f1"], "precision": m["precision"],
                     "recall": m["recall"], "auc_pr": m["auc_pr"]})
    return rows


def scalability_eval(did: str = "D2", sizes=(10_000, 50_000, 100_000, 200_000)) -> list[dict]:
    """Time hybrid_xgb end-to-end on increasing sub-samples of D2."""
    df, lab = load_dataset(did)
    rows = []
    for n in sizes:
        if n > len(df):
            continue
        idx = np.random.default_rng(SEED).choice(len(df), size=n, replace=False)
        sub = df.iloc[idx].reset_index(drop=True)
        y = lab["y"].to_numpy()[idx]
        t0 = time.time()
        feat_fn = FEATURE_FNS[did]
        X, rule = feat_fn(sub)
        stat = stat_score(X)
        iso = iforest_score(X)
        lof = lof_score(X)
        base = np.column_stack([rule, stat, iso, lof])
        hyb = xgb_stacked_hybrid_score(y, base)
        elapsed = time.time() - t0
        m = metrics_from_scores(y, hyb)
        rows.append({"dataset": did, "n_rows": n, "elapsed_sec": round(elapsed, 3),
                     "rows_per_sec": int(n / max(1e-9, elapsed)),
                     "f1": m["f1"], "precision": m["precision"], "recall": m["recall"]})
        print(f"    n={n} -> {elapsed:.2f}s  F1={m['f1']:.3f}")
    return rows


def threshold_sweep_eval(did: str, runs: dict, n_thresholds: int = 25) -> list[dict]:
    sc = runs[did].scores.copy()
    y = sc["y"].to_numpy()
    s = sc["hybrid_xgb"].to_numpy()
    qs = np.linspace(0.50, 0.99, n_thresholds)
    thresholds = np.quantile(s, qs)
    rows = []
    for q, t in zip(qs, thresholds):
        pred = (s >= t).astype(int)
        p, r, f, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
        flagged = int(pred.sum())
        rows.append({"dataset": did, "score_quantile": float(q),
                     "threshold": float(t), "flagged": flagged,
                     "review_workload_pct": 100.0 * flagged / len(s),
                     "precision": float(p), "recall": float(r), "f1": float(f),
                     "fpr": float(((pred == 1) & (y == 0)).sum() / max(1, (y == 0).sum()))})
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    t0 = time.time()
    runs: dict[str, DatasetRun] = {}
    print("[1/5] Running baseline detectors on D1, D2, D3 ...")
    for did in ["D1", "D2", "D3"]:
        print(f" -- {did}")
        runs[did] = run_dataset(did)

    baseline = pd.DataFrame(sum((r.baseline_rows for r in runs.values()), []))
    baseline.to_csv(RESULTS / "tables" / "baseline.csv", index=False)
    print(f"     baseline.csv rows={len(baseline)}")

    family = pd.DataFrame(sum((r.family_rows for r in runs.values()), []))
    family.to_csv(RESULTS / "tables" / "per_family.csv", index=False)
    print(f"     per_family.csv rows={len(family)}")

    # Persist scores for figures.
    for did, r in runs.items():
        r.scores.to_parquet(RESULTS / "scores" / f"{did}_scores.parquet", index=False)

    print("[2/5] 5-fold CV on hybrid (D1/D2/D3) ...")
    cv_rows: list[dict] = []
    for did in ["D1", "D2", "D3"]:
        cv_rows.extend(cv_eval(did, runs))
    pd.DataFrame(cv_rows).to_csv(RESULTS / "tables" / "cv.csv", index=False)

    print("[3/5] Ablation on hybrid (D1/D2/D3) ...")
    ab_rows: list[dict] = []
    for did in ["D1", "D2", "D3"]:
        ab_rows.extend(ablation_eval(did, runs))
    pd.DataFrame(ab_rows).to_csv(RESULTS / "tables" / "ablation.csv", index=False)

    print("[4/5] Threshold sweep on hybrid (D1/D2/D3) ...")
    sw_rows: list[dict] = []
    for did in ["D1", "D2", "D3"]:
        sw_rows.extend(threshold_sweep_eval(did, runs))
    pd.DataFrame(sw_rows).to_csv(RESULTS / "tables" / "threshold_sweep.csv", index=False)

    print("[5/5] Scalability on D2 sub-samples ...")
    sc_rows = scalability_eval("D2")
    pd.DataFrame(sc_rows).to_csv(RESULTS / "tables" / "scalability.csv", index=False)

    print(f"\nTotal elapsed: {time.time() - t0:.1f}s")
    # Summary
    print("\nBaseline F1 by detector x dataset:")
    print(baseline.pivot(index="detector", columns="dataset", values="f1").round(3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
