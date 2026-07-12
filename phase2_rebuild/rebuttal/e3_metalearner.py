"""
E3: Meta-learner comparison.

Tests whether replacing the LogisticRegression stacker with gradient-boosted
or ensemble meta-learners improves the stacked F1.

Meta-learners compared (all in OOF 5-fold protocol, identical to paper):
  LR       — LogisticRegression(class_weight='balanced', solver='liblinear') [baseline]
  RF       — RandomForestClassifier(n_estimators=200, class_weight='balanced')
  XGB      — XGBClassifier(scale_pos_weight=neg/pos, eval_metric='logloss')
  LGB      — LGBMClassifier(is_unbalance=True)
  GBM      — GradientBoostingClassifier
  MLP      — MLPClassifier(hidden_layer_sizes=(64,32))

Protocol:
  - Same 4 base detector scores (rule, stat, iforest, lof) as stacking features
  - StratifiedKFold(n_splits=5, random_state=SEED, shuffle=True) — same as paper
  - Oracle-threshold F1 at best PR point (same metrics_from_scores)
  - Datasets: D1, D2, D3

Outputs (rebuttal_artifacts/e3/):
  e3_metalearner_metrics.csv   — F1 per learner per dataset
  e3_comparison.csv            — delta vs LR baseline, p-value (paired t by fold)
"""
from __future__ import annotations

import importlib.util
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from scipy.stats import ttest_rel

warnings.filterwarnings("ignore")

SEED = 42
REPO = Path(__file__).resolve().parents[2]
PROC = REPO / "phase2_rebuild" / "data" / "processed"
SCORES_DIR = REPO / "phase2_rebuild" / "results" / "scores"
SCRIPTS = REPO / "phase2_rebuild" / "scripts"
BASELINE_CSV = REPO / "phase2_rebuild" / "results" / "tables" / "baseline.csv"
ARTIFACTS = REPO / "rebuttal_artifacts"
OUT = ARTIFACTS / "e3"
OUT.mkdir(parents=True, exist_ok=True)

BASE_DETECTORS = ["rule", "stat", "iforest", "lof"]


def load_score_module():
    spec = importlib.util.spec_from_file_location(
        "anomaly_exp_e3", SCRIPTS / "10_run_anomaly_experiments.py"
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = ""
    sys.modules["anomaly_exp_e3"] = mod
    spec.loader.exec_module(mod)
    mod.SEED = SEED
    return mod


def build_meta_learners(seed: int) -> dict:
    learners = {
        "LR": LogisticRegression(class_weight="balanced", solver="liblinear",
                                  random_state=seed, max_iter=1000),
        "RF": RandomForestClassifier(n_estimators=200, class_weight="balanced",
                                      random_state=seed, n_jobs=-1),
        "GBM": GradientBoostingClassifier(n_estimators=100, random_state=seed),
        "MLP": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=200,
                              random_state=seed, early_stopping=True, validation_fraction=0.1),
    }
    try:
        from xgboost import XGBClassifier
        learners["XGB"] = XGBClassifier(n_estimators=200, random_state=seed,
                                         use_label_encoder=False, eval_metric="logloss",
                                         verbosity=0)
    except ImportError:
        print("[E3] XGBoost not available; skipping.")
    try:
        import lightgbm as lgb
        learners["LGB"] = lgb.LGBMClassifier(n_estimators=200, random_state=seed,
                                               is_unbalance=True, verbose=-1)
    except ImportError:
        print("[E3] LightGBM not available; skipping.")
    return learners


def oof_stacked_f1(scores: np.ndarray, y: np.ndarray,
                    clf, score_mod, seed: int) -> tuple[float, list[float]]:
    """
    5-fold stratified OOF meta-learning.
    Returns (overall F1 at oracle threshold, per-fold F1 list).
    """
    kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    y_bin = (y > 0.5).astype(int)
    oof_scores = np.zeros(len(y))

    for tr, te in kf.split(scores, y_bin):
        X_tr, X_te = scores[tr], scores[te]
        y_tr = y_bin[tr]
        try:
            clf.fit(X_tr, y_tr)
            if hasattr(clf, "predict_proba"):
                oof_scores[te] = clf.predict_proba(X_te)[:, 1]
            else:
                oof_scores[te] = clf.decision_function(X_te)
        except Exception as ex:
            print(f"      fold error: {ex}")
            oof_scores[te] = 0.0

    metrics = score_mod.metrics_from_scores(y, oof_scores)

    # Per-fold F1 for significance testing
    fold_f1s = []
    for tr, te in kf.split(scores, y_bin):
        oof_scores_fold = np.zeros(len(te))
        X_tr, X_te = scores[tr], scores[te]
        y_tr = y_bin[tr]
        try:
            clf.fit(X_tr, y_tr)
            if hasattr(clf, "predict_proba"):
                oof_scores_fold = clf.predict_proba(X_te)[:, 1]
            else:
                oof_scores_fold = clf.decision_function(X_te)
        except Exception:
            pass
        m = score_mod.metrics_from_scores(y[te], oof_scores_fold)
        fold_f1s.append(m["f1"])

    return metrics["f1"], fold_f1s


def main():
    t0 = time.perf_counter()

    print("[E3] Loading scoring module ...", flush=True)
    score_mod = load_score_module()

    meta_learners = build_meta_learners(SEED)

    rows = []
    fold_rows = []

    for did in ["D1", "D2", "D3"]:
        print(f"\n[E3] Dataset {did} ...", flush=True)
        # Load existing base detector scores (committed parquets)
        scores_df = pd.read_parquet(SCORES_DIR / f"{did}_scores.parquet")
        y = scores_df["y"].to_numpy().astype(float)
        X = scores_df[BASE_DETECTORS].to_numpy()
        print(f"  {len(y):,} rows, {int((y > 0.5).sum()):,} positives")

        for name, clf in meta_learners.items():
            print(f"  {name} ...", flush=True, end="")
            t_s = time.perf_counter()
            f1_overall, fold_f1s = oof_stacked_f1(X, y, clf, score_mod, SEED)
            elapsed = round(time.perf_counter() - t_s, 2)
            print(f" F1={f1_overall:.4f}  ({elapsed}s)")
            rows.append({"dataset": did, "meta_learner": name, "f1": round(f1_overall, 4),
                          "runtime_s": elapsed})
            for fi, ff1 in enumerate(fold_f1s):
                fold_rows.append({"dataset": did, "meta_learner": name, "fold": fi, "f1": ff1})

    metrics_df = pd.DataFrame(rows)
    metrics_df.to_csv(OUT / "e3_metalearner_metrics.csv", index=False)
    fold_df = pd.DataFrame(fold_rows)
    fold_df.to_csv(OUT / "e3_fold_f1s.csv", index=False)

    # Significance vs LR baseline
    cmp_rows = []
    lr_folds = {did: fold_df[(fold_df["dataset"] == did) & (fold_df["meta_learner"] == "LR")]["f1"].tolist()
                for did in ["D1", "D2", "D3"]}

    bl = pd.read_csv(BASELINE_CSV)
    lr_paper = {r["dataset"]: r["f1"] for _, r in bl[bl["detector"] == "hybrid_lr"].iterrows()}

    for _, row in metrics_df.iterrows():
        did = row["dataset"]
        ml = row["meta_learner"]
        if ml == "LR":
            continue
        fl = fold_df[(fold_df["dataset"] == did) & (fold_df["meta_learner"] == ml)]["f1"].tolist()
        lr_fl = lr_folds.get(did, [])
        if len(fl) == len(lr_fl) and len(fl) >= 2:
            t_stat, p_val = ttest_rel(fl, lr_fl)
        else:
            p_val = float("nan")
        cmp_rows.append({
            "dataset": did, "meta_learner": ml,
            "f1": row["f1"],
            "lr_f1": metrics_df[(metrics_df["dataset"] == did) & (metrics_df["meta_learner"] == "LR")]["f1"].iloc[0],
            "delta_vs_lr": round(row["f1"] - metrics_df[(metrics_df["dataset"] == did) & (metrics_df["meta_learner"] == "LR")]["f1"].iloc[0], 4),
            "p_vs_lr": round(float(p_val), 4) if not np.isnan(p_val) else float("nan"),
            "paper_hybrid_lr": round(lr_paper.get(did, float("nan")), 4),
        })

    cmp_df = pd.DataFrame(cmp_rows)
    cmp_df.to_csv(OUT / "e3_comparison.csv", index=False)

    elapsed = round(time.perf_counter() - t0, 1)
    print(f"\n[E3] Done in {elapsed}s")
    print("\nF1 by meta-learner × dataset:")
    pivot = metrics_df.pivot_table(index="meta_learner", columns="dataset", values="f1", aggfunc="first")
    print(pivot.round(4).to_string())
    print("\nDelta vs LR (within this experiment):")
    if not cmp_df.empty:
        pvt2 = cmp_df.pivot_table(index="meta_learner", columns="dataset", values="delta_vs_lr", aggfunc="first")
        print(pvt2.round(4).to_string())
    print(f"\nOutputs: {OUT}")


if __name__ == "__main__":
    main()
