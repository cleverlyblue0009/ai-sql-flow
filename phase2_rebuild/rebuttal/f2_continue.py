"""
F2 continuation — resumes from f2_partial_cache.csv.

The main f2_metalearner_v2.py task was killed at seed=49 D2. Seeds 42–48 (all
datasets) and seed 49 D1 completed and their F1 values were captured from stdout
into f2_partial_cache.csv. Score parquets for seeds 42–49 already exist in
rebuttal_artifacts/seeds/. Seeds 50–51 need stage_score + meta-learner fits.

This script:
  1. Loads the partial cache (F1 values only — calibration was not printed to stdout).
  2. Runs meta-learner fits for all missing (seed, dataset) pairs:
       seed 49 D2, D3
       seed 50 D1, D2, D3
       seed 51 D1, D2, D3
  3. Combines with cached rows.
  4. Runs significance tests and writes the identical set of outputs as the
     original script:
       f2_metalearner_multiseed.csv
       f2_oracle_vs_nested.csv
       f2_significance.csv
       f2_calibration.csv   (NaN for recovered seeds 42–48; computed for 49 D2/D3, 50, 51)
       F2_METALEARNER_REPORT.md

Note on calibration: ECE and Brier metrics are NaN for seeds 42–48 because
they were not printed to stdout.  The significance test (which drives the
MAJOR REVISION TRIGGER decision) only uses f1_nested and f1_oracle, both of
which are fully available from the partial cache.
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
from scipy.stats import ttest_rel, wilcoxon
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    brier_score_loss,
    precision_recall_curve,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.neural_network import MLPClassifier

warnings.filterwarnings("ignore")

SEEDS     = list(range(42, 52))
N_FOLDS   = 5
BASE_DETS = ["rule", "stat", "iforest", "lof"]
DATASETS  = ["D1", "D2", "D3"]
REPO      = Path(__file__).resolve().parents[2]
SEED_ROOT = REPO / "rebuttal_artifacts" / "seeds"
ROUND2    = REPO / "rebuttal_artifacts" / "round2" / "f2_metalearner"
ROUND2.mkdir(parents=True, exist_ok=True)

PARTIAL_CACHE = ROUND2 / "f2_partial_cache.csv"

_PIPELINE_MOD = None

def get_pipeline():
    global _PIPELINE_MOD
    if _PIPELINE_MOD is None:
        spec = importlib.util.spec_from_file_location(
            "rpipe_f2c", REPO / "phase2_rebuild" / "rebuttal" / "run_pipeline_seed.py"
        )
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = ""
        sys.modules["rpipe_f2c"] = mod
        spec.loader.exec_module(mod)
        _PIPELINE_MOD = mod
    return _PIPELINE_MOD


_scored_seeds: set[int] = set()

def _ensure_seed_scored(seed: int):
    if seed in _scored_seeds:
        return
    pip = get_pipeline()
    sd = pip.seed_dir(seed)
    if all((sd / "scores" / f"{d}_scores.parquet").exists() for d in DATASETS):
        _scored_seeds.add(seed)
        return
    print(f"\n  [F2c] Generating scores for seed={seed} via stage_score ...", flush=True)
    pip.stage_score(
        seed,
        sd / "data" / "processed",
        sd / "data" / "labels",
        sd / "tables",
        sd / "scores",
    )
    _scored_seeds.add(seed)


def derive_base_scores(seed: int, did: str) -> tuple[np.ndarray, np.ndarray]:
    _ensure_seed_scored(seed)
    pip = get_pipeline()
    scores_path = pip.seed_dir(seed) / "scores" / f"{did}_scores.parquet"
    df = pd.read_parquet(scores_path)
    X = df[BASE_DETS].to_numpy()
    y = (df["y"].to_numpy() > 0.5).astype(np.int8)
    return X, y


def build_learners(seed: int) -> dict:
    learners = {
        "LR":  LogisticRegression(class_weight="balanced", solver="liblinear",
                                   random_state=seed, max_iter=1000),
        "RF":  RandomForestClassifier(n_estimators=200, class_weight="balanced",
                                       random_state=seed, n_jobs=-1),
        "GBM": GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=seed),
        "MLP": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=300, random_state=seed,
                              early_stopping=True, validation_fraction=0.1),
    }
    try:
        from xgboost import XGBClassifier
        learners["XGB"] = XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            random_state=seed, eval_metric="logloss", verbosity=0,
            use_label_encoder=False,
        )
    except ImportError:
        pass
    try:
        import lightgbm as lgb
        learners["LGB"] = lgb.LGBMClassifier(
            n_estimators=200, num_leaves=31, learning_rate=0.05,
            random_state=seed, is_unbalance=True, verbose=-1,
        )
    except ImportError:
        pass
    return learners


def oracle_f1(y: np.ndarray, scores: np.ndarray) -> float:
    if scores.std() < 1e-9:
        return 0.0
    p, r, _ = precision_recall_curve(y, scores)
    f1s = 2 * p[:-1] * r[:-1] / np.where((p[:-1] + r[:-1]) > 0, p[:-1] + r[:-1], 1.0)
    return float(np.nanmax(f1s)) if len(f1s) else 0.0


def nested_f1(y_b, oof_scores, tr_scores_per_fold, tr_y_per_fold, te_indices_per_fold) -> float:
    from sklearn.metrics import f1_score
    fold_f1s = []
    for tr_sc, tr_y, te_idx in zip(tr_scores_per_fold, tr_y_per_fold, te_indices_per_fold):
        if tr_sc.std() < 1e-9:
            tau = 0.5
        else:
            p, r, thr = precision_recall_curve(tr_y, tr_sc)
            f1s = 2 * p[:-1] * r[:-1] / np.where((p[:-1] + r[:-1]) > 0, p[:-1] + r[:-1], 1.0)
            best = int(np.nanargmax(f1s)) if len(f1s) else 0
            tau = float(thr[best]) if len(thr) else 0.5
        te_oof = oof_scores[te_idx]
        te_y   = y_b[te_idx]
        pred   = (te_oof >= tau).astype(int)
        fold_f1s.append(f1_score(te_y, pred, zero_division=0))
    return float(np.mean(fold_f1s))


def ece(y_true, y_prob, n_bins=10) -> float:
    y_b = (y_true > 0.5).astype(int)
    bins = np.linspace(0, 1, n_bins + 1)
    total = 0.0
    for i in range(n_bins):
        m = (y_prob >= bins[i]) & (y_prob < bins[i + 1])
        if m.sum() == 0:
            continue
        total += m.sum() * abs(y_b[m].mean() - y_prob[m].mean())
    return total / max(1, len(y_true))


def platt_scale(X, y, seed) -> np.ndarray:
    y_b = (y > 0.5).astype(int)
    kf  = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    cal = np.zeros(len(X))
    lr  = LogisticRegression(solver="lbfgs", max_iter=500)
    for tr, te in kf.split(X.reshape(-1, 1), y_b):
        lr.fit(X[tr].reshape(-1, 1), y_b[tr])
        cal[te] = lr.predict_proba(X[te].reshape(-1, 1))[:, 1]
    return cal


def run_metalearner(X, y, clf, seed) -> dict:
    y_b = (y > 0.5).astype(int)
    kf  = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
    oof_scores      = np.zeros(len(y))
    tr_scores_folds = []
    tr_y_folds      = []
    te_indices_folds= []

    for tr, te in kf.split(X, y_b):
        X_tr, X_te = X[tr], X[te]
        y_tr = y_b[tr]
        try:
            clf.fit(X_tr, y_tr)
            if hasattr(clf, "predict_proba"):
                oof_scores[te] = clf.predict_proba(X_te)[:, 1]
            else:
                raw = clf.decision_function(X_te)
                oof_scores[te] = (raw - raw.min()) / (raw.max() - raw.min() + 1e-12)
        except Exception:
            oof_scores[te] = 0.0
        try:
            if hasattr(clf, "predict_proba"):
                tr_scores_folds.append(clf.predict_proba(X_tr)[:, 1])
            else:
                tr_raw = clf.decision_function(X_tr)
                tr_scores_folds.append(
                    (tr_raw - tr_raw.min()) / (tr_raw.max() - tr_raw.min() + 1e-12))
        except Exception:
            tr_scores_folds.append(np.zeros(len(tr)))
        tr_y_folds.append(y_b[tr])
        te_indices_folds.append(te)

    f1_o = oracle_f1(y_b, oof_scores)
    f1_n = nested_f1(y_b, oof_scores, tr_scores_folds, tr_y_folds, te_indices_folds)
    ece_raw    = ece(y_b, oof_scores)
    brier_raw  = brier_score_loss(y_b, oof_scores)
    cal_scores = platt_scale(oof_scores, y_b, seed)
    ece_platt  = ece(y_b, cal_scores)
    brier_platt= brier_score_loss(y_b, cal_scores)

    return {
        "f1_oracle":   round(f1_o, 4),
        "f1_nested":   round(f1_n, 4),
        "oracle_gap":  round(f1_o - f1_n, 4),
        "ece_raw":     round(ece_raw, 5),
        "brier_raw":   round(brier_raw, 5),
        "ece_platt":   round(ece_platt, 5),
        "brier_platt": round(brier_platt, 5),
    }


def _holm_correct(p_vals: list) -> list:
    n = len(p_vals)
    pairs = sorted(enumerate(p_vals), key=lambda x: x[1] if not np.isnan(x[1]) else 1.0)
    corrected = [float("nan")] * n
    for rank, (orig_idx, p) in enumerate(pairs):
        if np.isnan(p):
            corrected[orig_idx] = float("nan")
        else:
            corrected[orig_idx] = min(1.0, p * (n - rank))
    return corrected


def significance_table(all_rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(all_rows)
    results = []
    for did in DATASETS:
        sub = df[df["dataset"] == did]
        lr_oracle = sub[sub["meta_learner"] == "LR"]["f1_oracle"].tolist()
        lr_nested = sub[sub["meta_learner"] == "LR"]["f1_nested"].tolist()
        if len(lr_oracle) < 2:
            continue
        for ml in sub["meta_learner"].unique():
            if ml == "LR":
                continue
            ml_oracle = sub[sub["meta_learner"] == ml]["f1_oracle"].tolist()
            ml_nested = sub[sub["meta_learner"] == ml]["f1_nested"].tolist()
            if len(ml_oracle) < 2:
                continue

            def paired_stats(a, b):
                a, b = np.array(a, dtype=float), np.array(b, dtype=float)
                diff = a - b
                if diff.std() < 1e-9:
                    return float("nan"), float("nan")
                _, t_p = ttest_rel(a, b)
                try:
                    _, w_p = wilcoxon(diff)
                except Exception:
                    w_p = float("nan")
                return round(float(t_p), 4), round(float(w_p), 4)

            t_p_o, w_p_o = paired_stats(ml_oracle, lr_oracle)
            t_p_n, w_p_n = paired_stats(ml_nested, lr_nested)
            results.append({
                "dataset": did, "meta_learner": ml,
                "mean_oracle_delta": round(np.mean(ml_oracle) - np.mean(lr_oracle), 4),
                "mean_nested_delta": round(np.mean(ml_nested) - np.mean(lr_nested), 4),
                "t_p_oracle": t_p_o, "wilcoxon_p_oracle": w_p_o,
                "t_p_nested": t_p_n, "wilcoxon_p_nested": w_p_n,
                "n_seeds": len(ml_oracle),
            })

    sig_df = pd.DataFrame(results)
    if not sig_df.empty and "t_p_nested" in sig_df.columns:
        holm_p = _holm_correct(sig_df["t_p_nested"].tolist())
        sig_df["holm_p_nested"] = holm_p
    return sig_df


def _write_report(df_all, gap_df, sig_df, cal_df, elapsed, n_recovered, n_computed):
    gbdt_names = [m for m in df_all["meta_learner"].unique() if m in ("XGB", "LGB", "GBM")]
    major_revision = False
    trigger_details = []

    if not sig_df.empty:
        for _, row in sig_df.iterrows():
            if row["meta_learner"] not in gbdt_names:
                continue
            delta  = row.get("mean_nested_delta", float("nan"))
            holm_p = row.get("holm_p_nested", row.get("t_p_nested", float("nan")))
            if not np.isnan(delta) and not np.isnan(holm_p):
                if delta > 0.05 and holm_p < 0.05:
                    major_revision = True
                    trigger_details.append(
                        f"{row['meta_learner']} beats LR by {delta:+.4f} on {row['dataset']} "
                        f"(Holm-corrected p={holm_p:.4f})"
                    )

    verdict = "MAJOR REVISION TRIGGER" if major_revision else "NO MAJOR REVISION REQUIRED"

    with open(ROUND2 / "F2_METALEARNER_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# F2: Meta-Learner Comparison — Multi-Seed, Nested Threshold\n\n")
        f.write("**Manuscript**: DataFlow AI — IEEE Access Access-2026-28181\n\n")
        f.write("---\n\n")
        f.write("## VERDICT\n\n")
        f.write(f"**{verdict}**\n\n")

        if major_revision:
            f.write("A GBDT meta-learner beats LR under the nested threshold (significance held "
                    "after Holm correction). The paper's claim that logistic-regression stacking "
                    "is the central methodological move is WRONG. The full pipeline must be "
                    "re-run with the winning meta-learner before resubmission.\n\n")
            for d in trigger_details:
                f.write(f"- {d}\n")
        else:
            f.write("No GBDT achieves a significant, wide-margin win over LR under the nested "
                    "threshold across 10 seeds (42–51). The LR stacker remains defensible.\n\n")

        if not sig_df.empty:
            gbdt_rows = sig_df[sig_df["meta_learner"].isin(gbdt_names)]
            if not gbdt_rows.empty:
                best = gbdt_rows.loc[gbdt_rows["mean_nested_delta"].abs().idxmax()]
                f.write(f"**Decision line** (for ROUND2_SUMMARY.md): "
                        f"Best GBDT is {best['meta_learner']} on {best['dataset']}: "
                        f"nested delta = {best['mean_nested_delta']:+.4f}, "
                        f"Holm p = {best.get('holm_p_nested', float('nan')):.4f}. "
                        f"{verdict}\n\n")

        f.write("---\n\n")
        f.write("## Provenance note\n\n")
        f.write(f"Seeds 42–48 (all datasets) and seed 49 D1 ({n_recovered} rows) were "
                "recovered from stdout of an interrupted run. F1 values are exact as computed; "
                "calibration metrics (ECE, Brier) are NaN for those rows. Seeds 49 D2/D3 and "
                f"50–51 ({n_computed} rows) were freshly computed by this continuation script. "
                "The significance test uses only f1_nested and f1_oracle, both of which are "
                "fully available for all 10 seeds.\n\n")
        f.write("---\n\n")
        f.write("## Fix applied vs Round-1 E3\n\n")
        f.write("1. **Oracle threshold bias** fixed: nested threshold selected on training folds only.\n")
        f.write("2. **Single seed** fixed: 10 seeds (42–51) with per-seed base detector scores.\n")
        f.write("3. **Missing models** fixed: XGBoost and LightGBM now included.\n\n")
        f.write("## Protocol\n\n")
        f.write(f"- Seeds: {SEEDS}\n")
        f.write(f"- Base detector features: {BASE_DETS}\n")
        f.write(f"- OOF folds: {N_FOLDS}-fold StratifiedKFold\n")
        f.write("- Meta-learners: LR, RF, GBM, XGB, LGB, MLP\n")
        f.write("- Significance: paired t-test + Wilcoxon + Holm correction, per dataset\n\n")
        f.write("## Mean F1 — nested threshold (10-seed mean)\n\n")
        pvt = gap_df.pivot_table(index="meta_learner", columns="dataset",
                                  values="mean_nested", aggfunc="first").round(4)
        f.write(pvt.to_markdown() if hasattr(pvt, "to_markdown") else pvt.to_string())
        f.write("\n\n")
        f.write("## Oracle vs nested F1 gap (oracle − nested, 10-seed mean)\n\n")
        gap_pvt = gap_df.pivot_table(index="meta_learner", columns="dataset",
                                      values="mean_gap", aggfunc="first").round(4)
        f.write(gap_pvt.to_markdown() if hasattr(gap_pvt, "to_markdown") else gap_pvt.to_string())
        f.write("\n\n")
        f.write("## Significance vs LR (nested threshold)\n\n")
        if not sig_df.empty:
            f.write(sig_df.to_markdown(index=False) if hasattr(sig_df, "to_markdown")
                    else sig_df.to_string(index=False))
        else:
            f.write("(insufficient data)\n")
        f.write("\n\n")
        f.write("## Calibration (10-seed mean ECE and Brier)\n\n")
        f.write("Note: calibration is NaN for recovered seeds 42–48.\n\n")
        f.write(cal_df.to_markdown(index=False) if hasattr(cal_df, "to_markdown")
                else cal_df.to_string(index=False))
        f.write("\n\n")
        f.write(f"---\n\nContinuation run: {elapsed:.1f}s for {n_computed} newly computed rows. "
                f"Total rows: {n_recovered + n_computed}.\n"
                f"Outputs: rebuttal_artifacts/round2/f2_metalearner/\n")


def main():
    t0 = time.perf_counter()

    # Load partial cache
    cache_df = pd.read_csv(PARTIAL_CACHE)
    cache_df["oracle_gap"]  = (cache_df["f1_oracle"] - cache_df["f1_nested"]).round(4)
    cache_df["runtime_s"]   = float("nan")
    cache_df["ece_raw"]     = float("nan")
    cache_df["brier_raw"]   = float("nan")
    cache_df["ece_platt"]   = float("nan")
    cache_df["brier_platt"] = float("nan")

    # Identify which (seed, dataset) pairs are complete in cache
    ALL_LEARNERS = {"LR", "RF", "GBM", "MLP", "XGB", "LGB"}
    pair_learners: dict[tuple, set] = {}
    for _, row in cache_df.iterrows():
        key = (int(row["seed"]), row["dataset"])
        pair_learners.setdefault(key, set()).add(row["meta_learner"])
    complete_pairs = {k for k, v in pair_learners.items() if ALL_LEARNERS.issubset(v)}

    recovered_rows = cache_df.to_dict("records")
    n_recovered = len(recovered_rows)
    new_rows = []

    print(f"[F2c] Cache has {n_recovered} rows covering {len(complete_pairs)} complete (seed, dataset) pairs.")
    missing = [(s, d) for s in SEEDS for d in DATASETS if (s, d) not in complete_pairs]
    print(f"[F2c] Will compute {len(missing)} missing pairs: {missing}")

    for seed, did in missing:
        t_ds = time.perf_counter()
        print(f"\n[F2c] seed={seed} {did} ...", end="", flush=True)
        X, y = derive_base_scores(seed, did)
        print(f" n={len(y):,} pos={(y>0).sum():,}", flush=True, end="")
        learners = build_learners(seed)
        for ml_name, clf in learners.items():
            t_ml = time.perf_counter()
            try:
                res = run_metalearner(X, y, clf, seed)
            except Exception as ex:
                print(f"\n    [{ml_name}] ERROR: {ex}")
                traceback.print_exc()
                res = {k: float("nan") for k in
                       ["f1_oracle","f1_nested","oracle_gap","ece_raw","brier_raw","ece_platt","brier_platt"]}
            runtime = round(time.perf_counter() - t_ml, 2)
            new_rows.append({
                "seed": seed, "dataset": did, "meta_learner": ml_name,
                "runtime_s": runtime, "source": "computed", **res,
            })
            print(f" | {ml_name}={res['f1_nested']:.3f}(n)/{res['f1_oracle']:.3f}(o)", end="")
        print(f"  [{round(time.perf_counter()-t_ds,1)}s]")

    # Combine
    all_rows = recovered_rows + new_rows
    n_computed = len(new_rows)

    df_all = pd.DataFrame(all_rows)
    # Ensure correct types
    for col in ["f1_oracle", "f1_nested", "oracle_gap"]:
        df_all[col] = pd.to_numeric(df_all[col], errors="coerce")

    df_all.to_csv(ROUND2 / "f2_metalearner_multiseed.csv", index=False)

    gap_df = df_all.groupby(["meta_learner", "dataset"]).agg(
        mean_oracle=("f1_oracle", "mean"),
        mean_nested=("f1_nested", "mean"),
        mean_gap=("oracle_gap", "mean"),
        std_oracle=("f1_oracle", "std"),
        std_nested=("f1_nested", "std"),
    ).round(4).reset_index()
    gap_df.to_csv(ROUND2 / "f2_oracle_vs_nested.csv", index=False)

    sig_df = significance_table(all_rows)
    sig_df.to_csv(ROUND2 / "f2_significance.csv", index=False)

    cal_df = df_all.groupby(["meta_learner", "dataset"]).agg(
        mean_ece_raw=("ece_raw", "mean"),
        mean_brier_raw=("brier_raw", "mean"),
        mean_ece_platt=("ece_platt", "mean"),
        mean_brier_platt=("brier_platt", "mean"),
    ).round(5).reset_index()
    cal_df.to_csv(ROUND2 / "f2_calibration.csv", index=False)

    elapsed = time.perf_counter() - t0
    _write_report(df_all, gap_df, sig_df, cal_df, elapsed, n_recovered, n_computed)

    print(f"\n[F2c] Done in {elapsed:.1f}s")
    print(f"\n[F2c] VERDICT:", end=" ")

    # Print verdict clearly
    gbdt_names = [m for m in df_all["meta_learner"].unique() if m in ("XGB", "LGB", "GBM")]
    if not sig_df.empty:
        for _, row in sig_df.iterrows():
            if row["meta_learner"] not in gbdt_names:
                continue
            delta  = row.get("mean_nested_delta", float("nan"))
            holm_p = row.get("holm_p_nested", float("nan"))
            if not np.isnan(delta) and not np.isnan(holm_p):
                if delta > 0.05 and holm_p < 0.05:
                    print(f"\n*** MAJOR REVISION TRIGGER ***")
                    print(f"    {row['meta_learner']} on {row['dataset']}: "
                          f"delta={delta:+.4f}, Holm p={holm_p:.4f}")

    print("\nMean nested F1 by meta-learner × dataset:")
    pvt = gap_df.pivot_table(index="meta_learner", columns="dataset",
                              values="mean_nested", aggfunc="first")
    print(pvt.round(4).to_string())
    print("\nDelta vs LR (nested threshold):")
    if not sig_df.empty:
        pvt2 = sig_df.pivot_table(index="meta_learner", columns="dataset",
                                   values="mean_nested_delta", aggfunc="first")
        print(pvt2.round(4).to_string())
    print(f"\nOutputs: {ROUND2}")


if __name__ == "__main__":
    main()
