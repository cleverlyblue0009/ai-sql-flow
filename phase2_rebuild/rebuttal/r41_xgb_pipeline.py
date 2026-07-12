"""
R4.1 — XGBoost meta-learner adoption and full pipeline regeneration.

Decision (from F2 evidence):
  XGBoost (hybrid_xgb) replaces LogisticRegression (hybrid_lr) as the primary stacker.
  - Nested-threshold 10-seed mean F1: LR 0.4525/0.3718/0.7782 vs XGB 0.6137/0.5345/0.7995
  - Holm-corrected p ~ 0 on all three datasets
  - XGB oracle-nested gap 0.002-0.005 → advantage is real, not threshold overfitting
  - XGB raw ECE 0.003/0.006/0.001 vs LR raw 0.261/0.325/0.040
  - LR remains as ablation/comparison row; hybrid_fixed (max-fusion) remains too

Strategy: load COMMITTED base scores (rule/stat/iforest/lof) from
phase2_rebuild/results/scores/ — no re-running of IsolationForest/LOF.
Compute hybrid_xgb via 5-fold OOF XGBClassifier on top.
For multi-seed: load rebuttal_artifacts/seeds/seed{N}/scores/ and compute XGB OOF.

Outputs → rebuttal_artifacts/round4/r41_xgb_pipeline/
Also updates phase2_rebuild/results/scores/*_scores.parquet with hybrid_xgb column.
"""
from __future__ import annotations

import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ttest_rel, wilcoxon
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score, balanced_accuracy_score,
    precision_recall_curve, precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedKFold
from xgboost import XGBClassifier


def holm_correct(ps: np.ndarray) -> np.ndarray:
    """Holm-Bonferroni correction. Returns corrected p-values."""
    n = len(ps)
    order = np.argsort(ps)
    corrected = np.zeros(n)
    running_max = 0.0
    for rank, idx in enumerate(order):
        adj = ps[idx] * (n - rank)
        running_max = max(running_max, adj)
        corrected[idx] = min(running_max, 1.0)
    return corrected

warnings.filterwarnings("ignore")

REPO   = Path(__file__).resolve().parents[2]
SCORES = REPO / "phase2_rebuild" / "results" / "scores"
PROC   = REPO / "phase2_rebuild" / "data" / "processed"
LABELS = REPO / "phase2_rebuild" / "data" / "labels"
TABLES = REPO / "phase2_rebuild" / "results" / "tables"
SEEDS_ROOT = REPO / "rebuttal_artifacts" / "seeds"
ROUND4 = REPO / "rebuttal_artifacts" / "round4" / "r41_xgb_pipeline"
ROUND4.mkdir(parents=True, exist_ok=True)

SEED   = 42
SEEDS  = list(range(42, 52))
DATASETS = ["D1", "D2", "D3"]
BASE_COLS = ["rule", "stat", "iforest", "lof"]
N_FOLDS = 5


# ---------------------------------------------------------------------------
# XGB OOF stacker
# ---------------------------------------------------------------------------
def xgb_oof(y: np.ndarray, base: np.ndarray,
             seed: int = SEED, k: int = N_FOLDS) -> np.ndarray:
    n_neg = int((y == 0).sum())
    n_pos = int((y == 1).sum())
    spw = max(1.0, n_neg / max(1, n_pos))
    out = np.zeros(len(y), dtype=float)
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)
    for tr, te in skf.split(base, y):
        clf = XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=1.0,
            scale_pos_weight=spw, random_state=seed,
            eval_metric="logloss", use_label_encoder=False,
            verbosity=0, n_jobs=-1,
        )
        clf.fit(base[tr], y[tr])
        out[te] = clf.predict_proba(base[te])[:, 1]
    return out


def lr_oof(y: np.ndarray, base: np.ndarray,
           seed: int = SEED, k: int = N_FOLDS) -> np.ndarray:
    out = np.zeros(len(y), dtype=float)
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)
    for tr, te in skf.split(base, y):
        clf = LogisticRegression(max_iter=2000, class_weight="balanced",
                                  solver="liblinear", random_state=seed)
        clf.fit(base[tr], y[tr])
        out[te] = clf.predict_proba(base[te])[:, 1]
    return out


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def metrics_from_scores(y: np.ndarray, s: np.ndarray) -> dict:
    auc_pr = float(average_precision_score(y, s)) if s.std() > 0 else float("nan")
    prec, rec, thr = precision_recall_curve(y, s)
    f1s = (2 * prec[:-1] * rec[:-1]) / np.where(
        (prec[:-1] + rec[:-1]) > 0, prec[:-1] + rec[:-1], 1.0)
    best = int(np.nanargmax(f1s)) if len(f1s) else 0
    best_thr = float(thr[best]) if len(thr) else 0.5
    pred = (s >= best_thr).astype(np.int8)
    p, r, f, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    fpr = float(((pred == 1) & (y == 0)).sum() / max(1, (y == 0).sum()))
    return {
        "auc_pr": round(auc_pr, 4), "best_threshold": round(best_thr, 4),
        "precision": round(float(p), 4), "recall": round(float(r), 4),
        "f1": round(float(f), 4),
        "balanced_acc": round(float(balanced_accuracy_score(y, pred)), 4),
        "fpr_at_best_f1": round(fpr, 4),
    }


def nested_f1(y: np.ndarray, s: np.ndarray, k: int = N_FOLDS, seed: int = SEED) -> float:
    """F1 under nested threshold (tau selected on train folds, evaluated on test fold)."""
    scores_te = []
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)
    for tr, te in skf.split(s, y):
        prec, rec, thr = precision_recall_curve(y[tr], s[tr])
        f1s = (2 * prec[:-1] * rec[:-1]) / np.where(
            (prec[:-1] + rec[:-1]) > 0, prec[:-1] + rec[:-1], 1.0)
        bt = float(thr[int(np.nanargmax(f1s))]) if len(thr) else 0.5
        pred_te = (s[te] >= bt).astype(np.int8)
        _, _, f, _ = precision_recall_fscore_support(y[te], pred_te, average="binary", zero_division=0)
        scores_te.append(float(f))
    return round(float(np.mean(scores_te)), 4)


# ---------------------------------------------------------------------------
# Stage 1: seed=42 — extend committed scores with hybrid_xgb
# ---------------------------------------------------------------------------
def run_seed42_baseline() -> dict[str, dict]:
    print("[R4.1] Stage 1: computing hybrid_xgb on seed=42 base scores ...", flush=True)
    result = {}
    for did in DATASETS:
        sc = pd.read_parquet(SCORES / f"{did}_scores.parquet")
        y    = sc["y"].to_numpy()
        base = sc[BASE_COLS].to_numpy()

        t0 = time.perf_counter()
        hyb_xgb = xgb_oof(y, base, seed=SEED)
        elapsed = time.perf_counter() - t0

        # Write hybrid_xgb into the committed scores parquet
        sc["hybrid_xgb"] = hyb_xgb
        sc.to_parquet(SCORES / f"{did}_scores.parquet", index=False)

        m = metrics_from_scores(y, hyb_xgb)
        m_nested = nested_f1(y, hyb_xgb)
        result[did] = {**m, "f1_nested": m_nested, "elapsed_xgb_s": round(elapsed, 2)}
        print(f"  {did}: F1={m['f1']:.4f}  AUC-PR={m['auc_pr']:.4f}  "
              f"tau*={m['best_threshold']:.4f}  nested_F1={m_nested:.4f}  "
              f"time={elapsed:.1f}s", flush=True)
    return result


# ---------------------------------------------------------------------------
# Stage 2: baseline table (all detectors, seed=42)
# ---------------------------------------------------------------------------
def build_baseline_table() -> pd.DataFrame:
    print("[R4.1] Stage 2: baseline table ...", flush=True)
    rows = []
    for did in DATASETS:
        sc = pd.read_parquet(SCORES / f"{did}_scores.parquet")
        y = sc["y"].to_numpy()
        for det in ["rule", "stat", "iforest", "lof", "hybrid", "hybrid_lr", "hybrid_xgb"]:
            if det not in sc.columns:
                continue
            m = metrics_from_scores(y, sc[det].to_numpy())
            m["f1_nested"] = nested_f1(y, sc[det].to_numpy()) if det in ("hybrid_lr", "hybrid_xgb") else float("nan")
            m["dataset"] = did
            m["detector"] = det
            rows.append(m)
    df = pd.DataFrame(rows)
    df.to_csv(ROUND4 / "baseline_xgb.csv", index=False)
    print(f"  baseline_xgb.csv: {len(df)} rows", flush=True)
    return df


# ---------------------------------------------------------------------------
# Stage 3: per-family recall under hybrid_xgb
# ---------------------------------------------------------------------------
def build_per_family_table() -> pd.DataFrame:
    print("[R4.1] Stage 3: per-family recall ...", flush=True)
    rows = []
    for did in DATASETS:
        sc = pd.read_parquet(SCORES / f"{did}_scores.parquet")
        y    = sc["y"].to_numpy()
        fam  = sc["family"].to_numpy()
        hyb_xgb = sc["hybrid_xgb"].to_numpy()
        m = metrics_from_scores(y, hyb_xgb)
        thr = m["best_threshold"]
        pred = (hyb_xgb >= thr).astype(np.int8)
        for f in sorted({x for x in fam if x}):
            mask = fam == f
            tp = int((pred[mask] == 1).sum())
            n  = int(mask.sum())
            rows.append({"dataset": did, "family": f, "detector": "hybrid_xgb",
                         "n_injected": n, "recovered": tp,
                         "recall": round(tp / max(1, n), 4)})
    df = pd.DataFrame(rows)
    df.to_csv(ROUND4 / "per_family_xgb.csv", index=False)
    print(f"  per_family_xgb.csv: {len(df)} rows", flush=True)
    return df


# ---------------------------------------------------------------------------
# Stage 4: CV (nested threshold within each fold)
# ---------------------------------------------------------------------------
def build_cv_table() -> pd.DataFrame:
    print("[R4.1] Stage 4: 5-fold CV ...", flush=True)
    rows = []
    for did in DATASETS:
        sc = pd.read_parquet(SCORES / f"{did}_scores.parquet")
        y = sc["y"].to_numpy()
        hyb_xgb = sc["hybrid_xgb"].to_numpy()
        skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
        for i, (tr, te) in enumerate(skf.split(hyb_xgb, y)):
            prec, rec, thr = precision_recall_curve(y[tr], hyb_xgb[tr])
            f1s = (2 * prec[:-1] * rec[:-1]) / np.where(
                (prec[:-1] + rec[:-1]) > 0, prec[:-1] + rec[:-1], 1.0)
            bt = float(thr[int(np.nanargmax(f1s))]) if len(thr) else 0.5
            pred_te = (hyb_xgb[te] >= bt).astype(np.int8)
            p, r, f, _ = precision_recall_fscore_support(
                y[te], pred_te, average="binary", zero_division=0)
            rows.append({"dataset": did, "fold": i + 1, "n_test": len(te),
                         "threshold_from_train": round(bt, 4),
                         "precision": round(float(p), 4), "recall": round(float(r), 4),
                         "f1": round(float(f), 4), "detector": "hybrid_xgb"})
    df = pd.DataFrame(rows)
    df.to_csv(ROUND4 / "cv_xgb.csv", index=False)
    print(f"  cv_xgb.csv: {len(df)} rows", flush=True)
    return df


# ---------------------------------------------------------------------------
# Stage 5: leave-one-detector-out ablation (XGB stacker)
# ---------------------------------------------------------------------------
def build_ablation_table() -> pd.DataFrame:
    print("[R4.1] Stage 5: ablation (leave-one-out, XGB stacker) ...", flush=True)
    rows = []
    for did in DATASETS:
        sc = pd.read_parquet(SCORES / f"{did}_scores.parquet")
        y = sc["y"].to_numpy()
        full_base = sc[BASE_COLS].to_numpy()

        # Baseline: all 4 detectors
        full_xgb = xgb_oof(y, full_base)
        m = metrics_from_scores(y, full_xgb)
        rows.append({"dataset": did, "leave_out": "none", "detector": "hybrid_xgb",
                     **m})
        for drop in BASE_COLS:
            keep = [c for c in BASE_COLS if c != drop]
            sub = sc[keep].to_numpy()
            hyb = xgb_oof(y, sub)
            m = metrics_from_scores(y, hyb)
            rows.append({"dataset": did, "leave_out": drop, "detector": "hybrid_xgb",
                         **m})
    df = pd.DataFrame(rows)
    df.to_csv(ROUND4 / "ablation_xgb.csv", index=False)
    print(f"  ablation_xgb.csv: {len(df)} rows", flush=True)
    return df


# ---------------------------------------------------------------------------
# Stage 6: threshold sweep
# ---------------------------------------------------------------------------
def build_threshold_sweep() -> pd.DataFrame:
    print("[R4.1] Stage 6: threshold sweep ...", flush=True)
    rows = []
    for did in DATASETS:
        sc = pd.read_parquet(SCORES / f"{did}_scores.parquet")
        y = sc["y"].to_numpy()
        s = sc["hybrid_xgb"].to_numpy()
        qs = np.linspace(0.50, 0.99, 25)
        thresholds = np.quantile(s, qs)
        for q, t in zip(qs, thresholds):
            pred = (s >= t).astype(np.int8)
            p, r, f, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
            flagged = int(pred.sum())
            rows.append({
                "dataset": did, "detector": "hybrid_xgb",
                "score_quantile": round(float(q), 3),
                "threshold": round(float(t), 4), "flagged": flagged,
                "review_workload_pct": round(100.0 * flagged / len(s), 2),
                "precision": round(float(p), 4), "recall": round(float(r), 4),
                "f1": round(float(f), 4),
                "fpr": round(float(((pred == 1) & (y == 0)).sum() / max(1, (y == 0).sum())), 4),
            })
    df = pd.DataFrame(rows)
    df.to_csv(ROUND4 / "threshold_sweep_xgb.csv", index=False)
    print(f"  threshold_sweep_xgb.csv: {len(df)} rows", flush=True)
    return df


# ---------------------------------------------------------------------------
# Stage 7: scalability (D2, XGB stacker end-to-end)
# ---------------------------------------------------------------------------
def build_scalability_table() -> pd.DataFrame:
    print("[R4.1] Stage 7: scalability on D2 sub-samples ...", flush=True)
    # Load the committed D2 base scores and sub-sample
    sc = pd.read_parquet(SCORES / "D2_scores.parquet")
    y_all = sc["y"].to_numpy()
    base_all = sc[BASE_COLS].to_numpy()
    sizes = [10_000, 50_000, 100_000, 200_000]
    rows = []
    for n in sizes:
        if n > len(sc):
            continue
        idx = np.random.default_rng(SEED).choice(len(sc), size=n, replace=False)
        y_sub   = y_all[idx]
        base_sub = base_all[idx]
        t0 = time.perf_counter()
        hyb_xgb = xgb_oof(y_sub, base_sub)
        elapsed = time.perf_counter() - t0
        m = metrics_from_scores(y_sub, hyb_xgb)
        rows.append({
            "dataset": "D2", "detector": "hybrid_xgb",
            "n_rows": n, "elapsed_sec": round(elapsed, 3),
            "rows_per_sec": int(n / max(1e-9, elapsed)),
            "f1": m["f1"], "precision": m["precision"], "recall": m["recall"],
        })
        print(f"  n={n:,} -> {elapsed:.2f}s  F1={m['f1']:.4f}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(ROUND4 / "scalability_xgb.csv", index=False)
    print(f"  scalability_xgb.csv: {len(df)} rows", flush=True)
    return df


# ---------------------------------------------------------------------------
# Stage 8: multi-seed comparison (seeds 42-51, XGB vs LR vs hybrid_fixed)
# ---------------------------------------------------------------------------
def build_multiseed_table() -> tuple[pd.DataFrame, pd.DataFrame]:
    print("[R4.1] Stage 8: multi-seed significance (seeds 42-51) ...", flush=True)
    rows = []
    for seed in SEEDS:
        if seed == SEED:
            # Use committed scores
            score_dir = SCORES
        else:
            score_dir = SEEDS_ROOT / f"seed{seed}" / "scores"
        for did in DATASETS:
            path = score_dir / f"{did}_scores.parquet"
            if not path.exists():
                print(f"  MISSING: {path}", flush=True)
                continue
            sc = pd.read_parquet(path)
            y = sc["y"].to_numpy()
            base = sc[BASE_COLS].to_numpy()

            hyb_xgb = xgb_oof(y, base, seed=seed)
            hyb_lr  = lr_oof(y, base, seed=seed)
            hyb_fix = np.maximum.reduce([base[:, i] for i in range(base.shape[1])])

            m_xgb = metrics_from_scores(y, hyb_xgb)
            m_lr  = metrics_from_scores(y, hyb_lr)
            m_fix = metrics_from_scores(y, hyb_fix)

            f1_nested_xgb = nested_f1(y, hyb_xgb, seed=seed)
            f1_nested_lr  = nested_f1(y, hyb_lr, seed=seed)
            f1_nested_fix = nested_f1(y, hyb_fix, seed=seed)

            for det, ms, f1n in [
                ("hybrid_xgb", m_xgb, f1_nested_xgb),
                ("hybrid_lr",  m_lr,  f1_nested_lr),
                ("hybrid_fixed", m_fix, f1_nested_fix),
            ]:
                rows.append({
                    "seed": seed, "dataset": did, "detector": det,
                    "f1_oracle": ms["f1"], "f1_nested": f1n,
                    "auc_pr": ms["auc_pr"], "precision": ms["precision"],
                    "recall": ms["recall"], "best_threshold": ms["best_threshold"],
                })
            print(f"  seed={seed} {did}: XGB={m_xgb['f1']:.4f}(nested={f1_nested_xgb:.4f}) "
                  f"LR={m_lr['f1']:.4f}(nested={f1_nested_lr:.4f})", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(ROUND4 / "multiseed_xgb.csv", index=False)
    print(f"  multiseed_xgb.csv: {len(df)} rows", flush=True)

    # Significance: XGB vs LR and XGB vs hybrid_fixed, per dataset
    sig_rows = []
    for did in DATASETS:
        sub = df[df["dataset"] == did]
        xgb_vals = sub[sub["detector"] == "hybrid_xgb"]["f1_nested"].values
        lr_vals  = sub[sub["detector"] == "hybrid_lr"]["f1_nested"].values
        fix_vals = sub[sub["detector"] == "hybrid_fixed"]["f1_nested"].values
        n = min(len(xgb_vals), len(lr_vals), len(fix_vals))
        if n < 3:
            continue
        xgb_vals, lr_vals, fix_vals = xgb_vals[:n], lr_vals[:n], fix_vals[:n]
        for baseline_name, baseline_vals in [("hybrid_lr", lr_vals), ("hybrid_fixed", fix_vals)]:
            try:
                _, t_p = ttest_rel(xgb_vals, baseline_vals)
            except Exception:
                t_p = float("nan")
            try:
                _, w_p = wilcoxon(xgb_vals - baseline_vals)
            except Exception:
                w_p = float("nan")
            sig_rows.append({
                "dataset": did, "comparison": f"hybrid_xgb vs {baseline_name}",
                "mean_xgb": round(float(np.mean(xgb_vals)), 4),
                "mean_baseline": round(float(np.mean(baseline_vals)), 4),
                "mean_delta": round(float(np.mean(xgb_vals - baseline_vals)), 4),
                "t_p": round(float(t_p), 4) if not np.isnan(t_p) else float("nan"),
                "wilcoxon_p": round(float(w_p), 4) if not np.isnan(w_p) else float("nan"),
                "n_seeds": n,
            })

    sig_df = pd.DataFrame(sig_rows)
    if len(sig_df):
        raw_ps = sig_df["t_p"].fillna(1.0).values
        holm_ps = holm_correct(raw_ps)
        sig_df["holm_p"] = [round(p, 4) for p in holm_ps]
    sig_df.to_csv(ROUND4 / "significance_xgb.csv", index=False)
    print(f"  significance_xgb.csv: {len(sig_df)} rows", flush=True)
    return df, sig_df


# ---------------------------------------------------------------------------
# Stage 9: case study (D1 sign-flip record with hybrid_xgb)
# ---------------------------------------------------------------------------
def build_case_study() -> pd.DataFrame:
    print("[R4.1] Stage 9: case study record ...", flush=True)
    sc = pd.read_parquet(SCORES / "D1_scores.parquet")
    pos = sc[(sc["y"] == 1) & (sc["family"] == "A1_sign_flip")].sort_values(
        "hybrid_xgb", ascending=False)
    if len(pos) == 0:
        pos = sc[sc["y"] == 1].sort_values("hybrid_xgb", ascending=False)
    row = pos.iloc[0]
    detectors = ["rule", "stat", "iforest", "lof", "hybrid_lr", "hybrid_xgb"]
    records = [{"detector": d, "score": round(float(row[d]), 4)} for d in detectors]
    tau_lr  = float(pd.read_csv(TABLES / "baseline.csv").query(
        "dataset=='D1' and detector=='hybrid_lr'")["best_threshold"].iloc[0])
    # Get hybrid_xgb tau from our new baseline
    bl_xgb = pd.read_csv(ROUND4 / "baseline_xgb.csv")
    tau_xgb = float(bl_xgb.query("dataset=='D1' and detector=='hybrid_xgb'")["best_threshold"].iloc[0])
    for r in records:
        r["verdict_lr"]  = "QUARANTINE" if r["score"] >= tau_lr  else "pass"
        r["verdict_xgb"] = "QUARANTINE" if r["score"] >= tau_xgb else "pass"
    df = pd.DataFrame(records)
    df.to_csv(ROUND4 / "case_study_xgb.csv", index=False)
    print(f"  case_study_xgb.csv saved. tau_lr={tau_lr:.4f} tau_xgb={tau_xgb:.4f}", flush=True)
    return df


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def write_report(baseline: pd.DataFrame, sig: pd.DataFrame, cv: pd.DataFrame,
                 ablation: pd.DataFrame, thresh: pd.DataFrame, scalability: pd.DataFrame,
                 multiseed: pd.DataFrame, elapsed: float):
    def pivot_f1(df, col="f1"):
        return df.pivot(index="detector", columns="dataset", values=col).round(4)

    bl_xgb = baseline[baseline["detector"].isin(
        ["rule", "stat", "iforest", "lof", "hybrid", "hybrid_lr", "hybrid_xgb"])]

    with open(ROUND4 / "R41_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# R4.1: XGBoost Adoption — Full Pipeline Regeneration\n\n")
        f.write("**Decision**: XGBoost (hybrid_xgb) adopted as primary stacker, replacing hybrid_lr.\n\n")
        f.write("> XGB beats LR by +0.16 (D1), +0.16 (D2), +0.02 (D3) under nested threshold "
                "with Holm-corrected p ~ 0 on all three (F2 evidence, 10 seeds). "
                "XGB raw ECE 0.003/0.006/0.001 vs LR 0.261/0.325/0.040. Adopted.\n\n")
        f.write("---\n\n")

        f.write("## Baseline F1 (oracle threshold, seed=42)\n\n")
        try:
            f.write(pivot_f1(bl_xgb).to_markdown() + "\n\n")
        except Exception:
            f.write(bl_xgb[["dataset","detector","f1"]].to_string(index=False) + "\n\n")

        f.write("## Baseline AUC-PR (seed=42)\n\n")
        try:
            f.write(pivot_f1(bl_xgb, "auc_pr").to_markdown() + "\n\n")
        except Exception:
            f.write(bl_xgb[["dataset","detector","auc_pr"]].to_string(index=False) + "\n\n")

        f.write("## tau* (best-F1 threshold) per dataset\n\n")
        try:
            f.write(pivot_f1(bl_xgb, "best_threshold").to_markdown() + "\n\n")
        except Exception:
            pass

        f.write("## CV (5-fold, nested threshold, seed=42)\n\n")
        cv_sum = cv.groupby(["dataset", "detector"]).agg(
            f1_mean=("f1", "mean"), f1_std=("f1", "std")).round(4).reset_index()
        try:
            f.write(cv_sum.to_markdown(index=False) + "\n\n")
        except Exception:
            f.write(cv_sum.to_string(index=False) + "\n\n")

        f.write("## Leave-one-detector-out ablation (hybrid_xgb)\n\n")
        try:
            f.write(ablation[["dataset","leave_out","f1","auc_pr"]].to_markdown(index=False) + "\n\n")
        except Exception:
            f.write(ablation.to_string(index=False) + "\n\n")

        f.write("## Threshold sweep — tau* per dataset (hybrid_xgb)\n\n")
        best_tau = (thresh.loc[thresh.groupby("dataset")["f1"].idxmax()]
                    [["dataset","threshold","f1","precision","recall","review_workload_pct"]])
        try:
            f.write(best_tau.to_markdown(index=False) + "\n\n")
        except Exception:
            f.write(best_tau.to_string(index=False) + "\n\n")

        f.write("## Scalability (D2, hybrid_xgb)\n\n")
        try:
            f.write(scalability.to_markdown(index=False) + "\n\n")
        except Exception:
            f.write(scalability.to_string(index=False) + "\n\n")

        f.write("## Multi-seed mean F1 (nested threshold, seeds 42-51)\n\n")
        ms_mean = (multiseed.groupby(["dataset","detector"])["f1_nested"]
                   .mean().round(4).unstack("detector").reset_index())
        try:
            f.write(ms_mean.to_markdown(index=False) + "\n\n")
        except Exception:
            f.write(ms_mean.to_string(index=False) + "\n\n")

        f.write("## Significance (XGB vs LR and XGB vs hybrid_fixed)\n\n")
        try:
            f.write(sig.to_markdown(index=False) + "\n\n")
        except Exception:
            f.write(sig.to_string(index=False) + "\n\n")

        f.write(f"\n---\nGenerated in {elapsed:.1f}s\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    t0 = time.perf_counter()

    run_seed42_baseline()
    baseline = build_baseline_table()
    build_per_family_table()
    cv_df    = build_cv_table()
    ablation = build_ablation_table()
    thresh   = build_threshold_sweep()
    scale    = build_scalability_table()
    ms, sig  = build_multiseed_table()
    build_case_study()

    elapsed = time.perf_counter() - t0
    write_report(baseline, sig, cv_df, ablation, thresh, scale, ms, elapsed)

    print(f"\n[R4.1] Done in {elapsed:.1f}s")
    print(f"Outputs: {ROUND4}")

    # Print summary
    print("\n=== BASELINE F1 (oracle) ===")
    bl_xgb = pd.read_csv(ROUND4 / "baseline_xgb.csv")
    print(bl_xgb.pivot(index="detector", columns="dataset", values="f1").round(4))
    print("\n=== SIGNIFICANCE XGB vs LR ===")
    sig_df = pd.read_csv(ROUND4 / "significance_xgb.csv")
    print(sig_df[sig_df["comparison"].str.contains("lr")][
        ["dataset","comparison","mean_delta","t_p","holm_p"]].to_string(index=False))


if __name__ == "__main__":
    main()
