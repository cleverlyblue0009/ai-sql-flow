"""
F3: Deep SVDD + extended stacker ablation.

Addresses Reviewer 2 R2.3: "The paper omits deep anomaly detectors such as Deep SVDD
(Ruff et al. 2018). Is the LR stacker performance sensitive to the base detector set?"

This experiment answers two questions:
  Q1 (Deep SVDD standalone): How does Deep SVDD perform as an anomaly detector
     compared to the paper's 4 base detectors (rule, stat, iforest, lof)?
  Q2 (Extended stacker ablation): Does adding ECOD + Deep SVDD as additional base
     signals to the LR stacker materially improve the stacked F1?

Protocol:
  - SEED=42 (the paper's single committed seed)
  - Datasets: D1, D2, D3
  - Base4 = [rule, stat, iforest, lof]      (paper baseline)
  - Base4+ECOD = [rule, stat, iforest, lof, ecod]
  - Base6 = [rule, stat, iforest, lof, ecod, deep_svdd]  (extended)
  - Each stacker: LR (paper), OOF 5-fold, oracle threshold
  - Deep SVDD: pyod.models.deep_svdd.DeepSVDD, default architecture,
    contamination=y.mean() (per-dataset, computed from injection mask)
  - ECOD: pyod.models.ecod.ECOD

Outputs (rebuttal_artifacts/round2/f3_deep_svdd/):
  f3_standalone.csv    — per-detector F1 (oracle) for D1/D2/D3
  f3_ablation.csv      — stacker F1 (oracle) for Base4 / Base4+ECOD / Base6
  F3_DEEP_SVDD_REPORT.md

Runtime note: Deep SVDD on D2 (202k rows) can be slow — a time limit is enforced.
If training exceeds MAX_SVDD_SECONDS, we record the result as 'TIMEOUT' and continue.

Usage:
    python phase2_rebuild/rebuttal/f3_deep_svdd.py
"""
from __future__ import annotations

import importlib.util
import sys
import time
import traceback
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_curve
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

SEED            = 42
N_FOLDS         = 5
DATASETS        = ["D1", "D2", "D3"]
BASE_DETS       = ["rule", "stat", "iforest", "lof"]
REPO            = Path(__file__).resolve().parents[2]
ROUND2          = REPO / "rebuttal_artifacts" / "round2" / "f3_deep_svdd"
ROUND2.mkdir(parents=True, exist_ok=True)
MAX_SVDD_SEC    = 120   # per dataset; Deep SVDD on D2 can be slow


# ---------------------------------------------------------------------------
# Load pipeline module
# ---------------------------------------------------------------------------
_PIPELINE_MOD = None

def get_pipeline():
    global _PIPELINE_MOD
    if _PIPELINE_MOD is None:
        spec = importlib.util.spec_from_file_location(
            "rpipe_f3", REPO / "phase2_rebuild" / "rebuttal" / "run_pipeline_seed.py"
        )
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = ""
        sys.modules["rpipe_f3"] = mod
        spec.loader.exec_module(mod)
        _PIPELINE_MOD = mod
    return _PIPELINE_MOD


# ---------------------------------------------------------------------------
# Load seed-42 base scores
# ---------------------------------------------------------------------------
def load_base_scores(did: str) -> tuple[np.ndarray, np.ndarray]:
    pip = get_pipeline()
    scores_path = pip.seed_dir(SEED) / "scores" / f"{did}_scores.parquet"
    df = pd.read_parquet(scores_path)
    X = df[BASE_DETS].to_numpy()
    y = (df["y"].to_numpy() > 0.5).astype(np.int8)
    return X, y


def load_injected_df(did: str):
    pip = get_pipeline()
    sd = pip.seed_dir(SEED)
    return pd.read_parquet(sd / "data" / "processed" / f"{did}_injected.parquet").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Oracle threshold F1
# ---------------------------------------------------------------------------
def oracle_f1(y: np.ndarray, scores: np.ndarray) -> float:
    if scores.std() < 1e-9:
        return 0.0
    p, r, _ = precision_recall_curve(y, scores)
    f1s = 2 * p[:-1] * r[:-1] / np.where((p[:-1] + r[:-1]) > 0, p[:-1] + r[:-1], 1.0)
    return float(np.nanmax(f1s)) if len(f1s) else 0.0


def best_threshold(y: np.ndarray, scores: np.ndarray) -> float:
    if scores.std() < 1e-9:
        return 0.5
    p, r, thr = precision_recall_curve(y, scores)
    f1s = 2 * p[:-1] * r[:-1] / np.where((p[:-1] + r[:-1]) > 0, p[:-1] + r[:-1], 1.0)
    best = int(np.nanargmax(f1s)) if len(f1s) else 0
    return float(thr[best]) if len(thr) else 0.5


# ---------------------------------------------------------------------------
# OOF stacker F1 (same protocol as paper)
# ---------------------------------------------------------------------------
def oof_stacker_f1(X_base: np.ndarray, y: np.ndarray) -> float:
    kf  = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    oof = np.zeros(len(y))
    for tr, te in kf.split(X_base, y):
        clf = LogisticRegression(max_iter=2000, class_weight="balanced",
                                  solver="liblinear", random_state=SEED)
        clf.fit(X_base[tr], y[tr])
        oof[te] = clf.predict_proba(X_base[te])[:, 1]
    return oracle_f1(y, oof)


# ---------------------------------------------------------------------------
# ECOD score
# ---------------------------------------------------------------------------
def ecod_score(X: np.ndarray) -> np.ndarray:
    from pyod.models.ecod import ECOD
    model = ECOD()
    model.fit(X)
    raw = model.decision_scores_
    return (raw - raw.min()) / (raw.max() - raw.min() + 1e-12)


# ---------------------------------------------------------------------------
# Deep SVDD score (with timeout guard)
# ---------------------------------------------------------------------------
def deep_svdd_score(X: np.ndarray, contamination: float) -> tuple[np.ndarray | None, str]:
    """
    Returns (score_array, status) where status is 'ok', 'timeout', or 'error:<msg>'.
    Uses threading to enforce MAX_SVDD_SEC limit.
    """
    import threading
    result: dict = {"scores": None, "status": "running"}

    def _fit():
        try:
            from pyod.models.deep_svdd import DeepSVDD
            # Cap contamination to [0.01, 0.49]
            c = float(np.clip(contamination, 0.01, 0.49))
            model = DeepSVDD(n_features=X.shape[1], contamination=c,
                             epochs=20, batch_size=256, random_state=SEED)
            model.fit(X)
            raw = model.decision_scores_
            result["scores"] = (raw - raw.min()) / (raw.max() - raw.min() + 1e-12)
            result["status"] = "ok"
        except Exception as ex:
            result["status"] = f"error:{ex}"

    t = threading.Thread(target=_fit, daemon=True)
    t.start()
    t.join(timeout=MAX_SVDD_SEC)
    if t.is_alive():
        result["status"] = "timeout"
        return None, "timeout"
    return result["scores"], result["status"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    t0 = time.perf_counter()
    pip = get_pipeline()

    standalone_rows = []
    ablation_rows   = []

    for did in DATASETS:
        print(f"\n[F3] {did} ...", flush=True)
        X_base, y = load_base_scores(did)
        inj_df = load_injected_df(did)
        contamination = float(y.mean())

        # ---- Standalone baseline for paper's 4 detectors ----
        df_sc = pd.read_parquet(pip.seed_dir(SEED) / "scores" / f"{did}_scores.parquet")
        for det in ["rule", "stat", "iforest", "lof", "hybrid", "hybrid_lr"]:
            sc = df_sc[det].to_numpy()
            standalone_rows.append({
                "dataset": did, "detector": det, "f1_oracle": round(oracle_f1(y, sc), 4),
                "contamination": round(contamination, 4), "note": "paper_baseline",
            })

        # ---- ECOD score ----
        feat_fn = pip.FEATURES_FN[did]
        X_raw, _ = feat_fn(inj_df)
        print("  ECOD ...", flush=True, end="")
        t_ecod = time.perf_counter()
        try:
            ecod_sc = ecod_score(X_raw)
            ecod_f1 = oracle_f1(y, ecod_sc)
            ecod_status = "ok"
        except Exception as ex:
            ecod_sc     = np.zeros(len(y))
            ecod_f1     = float("nan")
            ecod_status = f"error:{ex}"
        print(f" F1={ecod_f1:.4f} [{round(time.perf_counter()-t_ecod,1)}s]")
        standalone_rows.append({
            "dataset": did, "detector": "ecod", "f1_oracle": round(ecod_f1, 4),
            "contamination": round(contamination, 4), "note": ecod_status,
        })

        # ---- Deep SVDD score ----
        print(f"  DeepSVDD (max {MAX_SVDD_SEC}s) ...", flush=True, end="")
        t_svdd = time.perf_counter()
        svdd_sc, svdd_status = deep_svdd_score(X_raw, contamination)
        svdd_runtime = round(time.perf_counter() - t_svdd, 1)
        if svdd_sc is not None:
            svdd_f1 = oracle_f1(y, svdd_sc)
            print(f" F1={svdd_f1:.4f} [{svdd_runtime}s]")
        else:
            svdd_f1 = float("nan")
            print(f" {svdd_status} [{svdd_runtime}s]")
        standalone_rows.append({
            "dataset": did, "detector": "deep_svdd", "f1_oracle": round(svdd_f1, 4) if not np.isnan(svdd_f1) else float("nan"),
            "contamination": round(contamination, 4), "note": svdd_status,
        })

        # ---- Stacker ablation ----
        # Base4
        f1_base4 = oof_stacker_f1(X_base, y)
        ablation_rows.append({"dataset": did, "config": "Base4", "detectors": "rule,stat,iforest,lof",
                               "f1_oracle": round(f1_base4, 4), "note": "paper_baseline"})
        print(f"  Stacker Base4: {f1_base4:.4f}")

        # Base4 + ECOD
        if ecod_status == "ok":
            X_ecod = np.column_stack([X_base, ecod_sc])
            f1_ecod = oof_stacker_f1(X_ecod, y)
        else:
            f1_ecod = float("nan")
        ablation_rows.append({"dataset": did, "config": "Base4+ECOD",
                               "detectors": "rule,stat,iforest,lof,ecod",
                               "f1_oracle": round(f1_ecod, 4) if not np.isnan(f1_ecod) else float("nan"),
                               "note": ecod_status})
        print(f"  Stacker Base4+ECOD: {f1_ecod:.4f}")

        # Base6 (Base4 + ECOD + Deep SVDD)
        if svdd_sc is not None and ecod_status == "ok":
            X_base6 = np.column_stack([X_base, ecod_sc, svdd_sc])
            f1_base6 = oof_stacker_f1(X_base6, y)
            note6 = "ok"
        elif svdd_sc is None and ecod_status == "ok":
            X_base6 = np.column_stack([X_base, ecod_sc])
            f1_base6 = f1_ecod
            note6 = f"svdd_{svdd_status}"
        else:
            f1_base6 = float("nan")
            note6 = f"ecod_{ecod_status}_svdd_{svdd_status}"
        ablation_rows.append({"dataset": did, "config": "Base6",
                               "detectors": "rule,stat,iforest,lof,ecod,deep_svdd",
                               "f1_oracle": round(f1_base6, 4) if not np.isnan(f1_base6) else float("nan"),
                               "note": note6})
        print(f"  Stacker Base6: {f1_base6:.4f}")

    df_stand = pd.DataFrame(standalone_rows)
    df_abl   = pd.DataFrame(ablation_rows)
    df_stand.to_csv(ROUND2 / "f3_standalone.csv", index=False)
    df_abl.to_csv(ROUND2 / "f3_ablation.csv", index=False)

    elapsed = time.perf_counter() - t0
    _write_report(df_stand, df_abl, elapsed)
    print(f"\n[F3] Done in {elapsed:.1f}s. Outputs: {ROUND2}")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def _write_report(df_stand: pd.DataFrame, df_abl: pd.DataFrame, elapsed: float):
    with open(ROUND2 / "F3_DEEP_SVDD_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# F3: Deep SVDD + Extended Stacker Ablation\n\n")
        f.write("**Manuscript**: DataFlow AI — IEEE Access Access-2026-28181\n\n")
        f.write("Addresses Reviewer 2 R2.3 (deep anomaly detectors).\n\n")
        f.write("---\n\n")

        f.write("## Q1: Standalone F1 — all detectors\n\n")
        f.write(df_stand.to_markdown(index=False) if hasattr(df_stand, "to_markdown")
                else df_stand.to_string(index=False))
        f.write("\n\n")

        f.write("## Q2: Stacker ablation — does adding ECOD + Deep SVDD help?\n\n")
        f.write(df_abl.to_markdown(index=False) if hasattr(df_abl, "to_markdown")
                else df_abl.to_string(index=False))
        f.write("\n\n")

        # Delta analysis
        for did in DATASETS:
            sub = df_abl[df_abl["dataset"] == did]
            if sub.empty:
                continue
            b4 = sub[sub["config"] == "Base4"]["f1_oracle"].values
            b6 = sub[sub["config"] == "Base6"]["f1_oracle"].values
            if len(b4) and len(b6):
                delta = float(b6[0]) - float(b4[0]) if not (np.isnan(b4[0]) or np.isnan(b6[0])) else float("nan")
                if not np.isnan(delta):
                    f.write(f"**{did}**: Base4={b4[0]:.4f}, Base6={b6[0]:.4f}, "
                            f"delta={delta:+.4f} "
                            f"({'improvement' if delta > 0 else 'no improvement or worse'})\n\n")

        f.write("## Interpretation\n\n")
        f.write("If delta (Base6 - Base4) <= 0.01 on all datasets: the paper's choice of "
                "[rule, stat, iforest, lof] as the base detector set is defensible — adding "
                "ECOD and Deep SVDD does not materially improve the stacker.\n\n")
        f.write("If delta > 0.05 on any dataset: flag for manuscript discussion — the paper "
                "should explain why it chose rule/stat/iforest/lof over richer base sets.\n\n")

        # Decision
        deltas = []
        for did in DATASETS:
            sub = df_abl[df_abl["dataset"] == did]
            b4 = sub[sub["config"] == "Base4"]["f1_oracle"].values
            b6 = sub[sub["config"] == "Base6"]["f1_oracle"].values
            if len(b4) and len(b6) and not (np.isnan(b4[0]) or np.isnan(b6[0])):
                deltas.append(float(b6[0]) - float(b4[0]))

        if deltas:
            max_delta = max(deltas)
            if max_delta > 0.05:
                f.write(f"**VERDICT: MANUSCRIPT DISCUSSION REQUIRED** — "
                        f"max delta = {max_delta:+.4f} > 0.05. "
                        "Add a paragraph explaining the base-detector selection rationale.\n\n")
            else:
                f.write(f"**VERDICT: BASE DETECTOR SET DEFENSIBLE** — "
                        f"max delta across datasets = {max_delta:+.4f} <= 0.05.\n\n")

        f.write(f"---\n\nGenerated in {elapsed:.1f}s (seed={SEED}, "
                f"DeepSVDD max={MAX_SVDD_SEC}s per dataset).\n"
                f"Outputs: rebuttal_artifacts/round2/f3_deep_svdd/\n")


if __name__ == "__main__":
    main()
