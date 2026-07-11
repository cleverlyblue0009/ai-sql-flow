"""
E1: Multi-seed variance and significance testing (reviewer refs R1.3, R2.2).

Seeds 42..51 (10 seeds). Each seed re-injects and re-scores D1/D2/D3 using the
original injection and scoring modules with SEED patched to S.  The committed
clean parquets (D{1,2,3}_sec_gl / nyc_fy2024 / uci_credit) are reused as the
base — only injection positions and model random states change across seeds.

Outputs (all in rebuttal_artifacts/e1/)
----------------------------------------
  e1_per_seed.json                    raw per-seed × detector × dataset
  e1_multiseed_metrics.csv            mean/std/95CI per detector × dataset
  e1_significance.csv                 paired t / Wilcoxon / Cohen-d / Holm-BH
  e1_perfamily_recall_multiseed.csv   per-family recall mean ± std across seeds
  e1_threshold_nested_vs_oracle.csv   oracle-tau vs nested-tau F1 (hybrid_lr)
  e1_f1_boxplots_by_dataset.png       box plots, D1/D2/D3 side by side

Usage
-----
    python phase2_rebuild/rebuttal/e1_multiseed.py
    python phase2_rebuild/rebuttal/e1_multiseed.py --seeds 42 43 44   # subset
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.stats as st
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    precision_recall_curve,
    precision_recall_fscore_support,
)
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.linear_model import LogisticRegression

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "phase2_rebuild" / "scripts"
COMMITTED_PROC = REPO / "phase2_rebuild" / "data" / "processed"
COMMITTED_LABELS = REPO / "phase2_rebuild" / "data" / "labels"
ARTIFACTS = REPO / "rebuttal_artifacts"
OUT = ARTIFACTS / "e1"
OUT.mkdir(parents=True, exist_ok=True)

DEFAULT_SEEDS = list(range(42, 52))  # 42..51
DATASETS = ["D1", "D2", "D3"]
DETECTORS = ["rule", "stat", "iforest", "lof", "hybrid", "hybrid_lr"]
CLEAN_FILES = {
    "D1": "D1_sec_gl.parquet",
    "D2": "D2_nyc_fy2024.parquet",
    "D3": "D3_uci_credit.parquet",
}


# ---------------------------------------------------------------------------
# Module loader (registers in sys.modules so @dataclass works)
# ---------------------------------------------------------------------------
def _load_module(name: str, path: Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = ""
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Metrics helper
# ---------------------------------------------------------------------------
def metrics_from_scores(y: np.ndarray, scores: np.ndarray) -> dict:
    auc_pr = float(average_precision_score(y, scores)) if scores.std() > 0 else float("nan")
    prec, rec, thr = precision_recall_curve(y, scores)
    f1s = (2 * prec[:-1] * rec[:-1]) / np.where(
        (prec[:-1] + rec[:-1]) > 0, prec[:-1] + rec[:-1], 1
    )
    best = int(np.nanargmax(f1s)) if len(f1s) else 0
    best_thr = float(thr[best]) if len(thr) else 0.5
    pred = (scores >= best_thr).astype(np.int8)
    p, r, f, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    fpr = float((pred & (y == 0)).sum() / max(1, (y == 0).sum()))
    return {
        "auc_pr": auc_pr, "threshold": best_thr,
        "precision": float(p), "recall": float(r), "f1": float(f),
        "balanced_acc": float(balanced_accuracy_score(y, pred)),
        "fpr": fpr,
    }


# ---------------------------------------------------------------------------
# Nested-threshold F1 (threshold honesty check)
# ---------------------------------------------------------------------------
def nested_f1(y: np.ndarray, scores: np.ndarray, n_splits: int = 5) -> float:
    """Select threshold on train folds, evaluate on test fold — avoids oracle bias."""
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=0)
    fold_f1s = []
    for tr, te in kf.split(scores):
        prec, rec, thr = precision_recall_curve(y[tr], scores[tr])
        f1s = (2 * prec[:-1] * rec[:-1]) / np.where(
            (prec[:-1] + rec[:-1]) > 0, prec[:-1] + rec[:-1], 1
        )
        bt = float(thr[int(np.nanargmax(f1s))]) if len(thr) else 0.5
        pred = (scores[te] >= bt).astype(int)
        _, _, f, _ = precision_recall_fscore_support(y[te], pred, average="binary", zero_division=0)
        fold_f1s.append(float(f))
    return float(np.mean(fold_f1s))


# ---------------------------------------------------------------------------
# Run one seed: inject → score
# ---------------------------------------------------------------------------
def run_one_seed(seed: int, inj_mod, score_mod) -> dict:
    """Returns per-dataset dicts with scores, labels, family tags."""
    # --- Patch seed in both modules ---
    inj_mod.SEED = seed
    score_mod.SEED = seed

    seed_dir = ARTIFACTS / "seeds" / f"seed{seed}"
    proc_dir = seed_dir / "data" / "processed"
    labels_dir = seed_dir / "data" / "labels"
    tables_dir = seed_dir / "tables"
    proc_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    # Copy committed clean parquets (deterministic; same rows across seeds)
    for did, fname in CLEAN_FILES.items():
        dst = proc_dir / fname
        if not dst.exists():
            shutil.copy2(COMMITTED_PROC / fname, dst)

    # --- Injection (using original inject module) ---
    inj_results = {}
    for did, fname in CLEAN_FILES.items():
        inj_dst = proc_dir / f"{did}_injected.parquet"
        mask_dst = labels_dir / f"{did}_mask.parquet"
        if inj_dst.exists() and mask_dst.exists():
            inj_results[did] = {"status": "skip-existing"}
            continue
        df = pd.read_parquet(proc_dir / fname).reset_index(drop=True)
        inject_fn = getattr(inj_mod, f"inject_{did.lower()}")
        df_inj, mask_df = inject_fn(df)
        df_inj.to_parquet(inj_dst, index=False)
        mask_df.to_parquet(mask_dst, index=False)
        inj_results[did] = {"rows": len(df_inj), "anomalies": len(mask_df)}

    # --- Scoring (using original scoring module, patched SEED) ---
    # Temporarily override the module's path constants to use seed-namespaced dirs
    orig_proc = score_mod.PROC
    orig_labels = score_mod.LABELS
    orig_results = score_mod.RESULTS
    score_mod.PROC = proc_dir
    score_mod.LABELS = labels_dir
    score_mod.RESULTS = tables_dir.parent

    results = {}
    for did in DATASETS:
        df, lab = score_mod.load_dataset(did)
        y = lab["y"].to_numpy()
        fam = lab["family"].to_numpy()
        X, rule = score_mod.FEATURE_FNS[did](df)
        stat = score_mod.stat_score(X)
        iso = score_mod.iforest_score(X)
        lof = score_mod.lof_score(X)
        hyb = score_mod.hybrid_score(rule, stat, iso, lof)
        base_mat = np.column_stack([rule, stat, iso, lof])
        hyb_lr = score_mod.stacked_hybrid_score(y, base_mat)

        det_scores = {
            "rule": rule, "stat": stat, "iforest": iso,
            "lof": lof, "hybrid": hyb, "hybrid_lr": hyb_lr,
        }
        baseline = {}
        for det, sc in det_scores.items():
            baseline[det] = metrics_from_scores(y, sc)

        # Per-family recall at hybrid_lr threshold
        best_thr = baseline["hybrid_lr"]["threshold"]
        pred = (hyb_lr >= best_thr).astype(int)
        family_recall = {}
        for f in sorted({x for x in fam if x}):
            mask = fam == f
            n = int(mask.sum())
            tp = int((pred[mask] == 1).sum())
            family_recall[f] = tp / max(1, n)

        # Threshold honesty check
        oracle_f1 = baseline["hybrid_lr"]["f1"]
        nested_f1_val = nested_f1(y, hyb_lr)

        results[did] = {
            "y": y, "family": fam,
            "scores": det_scores,
            "baseline": baseline,
            "family_recall": family_recall,
            "oracle_f1": oracle_f1,
            "nested_f1": nested_f1_val,
        }

    # Restore module state
    score_mod.PROC = orig_proc
    score_mod.LABELS = orig_labels
    score_mod.RESULTS = orig_results

    return results


# ---------------------------------------------------------------------------
# Significance testing
# ---------------------------------------------------------------------------
def cohens_d_paired(a: np.ndarray, b: np.ndarray) -> float:
    diff = a - b
    return float(diff.mean() / (diff.std(ddof=1) + 1e-12))


def holm_bonferroni(p_vals: list[float]) -> list[float]:
    n = len(p_vals)
    indexed = sorted(enumerate(p_vals), key=lambda x: x[1])
    adjusted = [None] * n
    running_max = 0.0
    for rank, (orig_idx, p) in enumerate(indexed):
        corrected = p * (n - rank)
        running_max = max(running_max, corrected)
        adjusted[orig_idx] = min(running_max, 1.0)
    return adjusted


def run_significance(all_seed_data: dict) -> list[dict]:
    """
    all_seed_data: {seed: {did: {baseline: {det: {f1: ...}}}}}
    Tests per dataset:
      - hybrid_lr vs hybrid (fixed)
      - hybrid_lr vs best single detector (rule/stat/iforest/lof)
    """
    comparisons_raw = []
    for did in DATASETS:
        # Collect F1 vectors across seeds for each detector
        f1_by_det = {det: [] for det in DETECTORS}
        for seed_data in all_seed_data.values():
            for det in DETECTORS:
                f1_by_det[det].append(seed_data[did]["baseline"][det]["f1"])
        f1_by_det = {k: np.array(v) for k, v in f1_by_det.items()}

        # Find best single detector
        single_dets = ["rule", "stat", "iforest", "lof"]
        best_single = max(single_dets, key=lambda d: f1_by_det[d].mean())

        test_pairs = [
            ("hybrid_lr", "hybrid", "lr_vs_fixed"),
            ("hybrid_lr", best_single, f"lr_vs_{best_single}"),
        ]
        for det_a, det_b, label in test_pairs:
            a, b = f1_by_det[det_a], f1_by_det[det_b]
            diff = a - b
            t_stat, p_t = st.ttest_rel(a, b)
            try:
                w_stat, p_w = st.wilcoxon(diff)
            except ValueError:
                w_stat, p_w = 0.0, 1.0
            d = cohens_d_paired(a, b)
            comparisons_raw.append({
                "dataset": did,
                "comparison": label,
                "det_a": det_a,
                "det_b": det_b,
                "mean_a": float(a.mean()),
                "mean_b": float(b.mean()),
                "mean_diff": float(diff.mean()),
                "std_diff": float(diff.std(ddof=1)),
                "t_stat": float(t_stat),
                "p_ttest": float(p_t),
                "w_stat": float(w_stat),
                "p_wilcoxon": float(p_w),
                "cohens_d": d,
                "n_seeds": len(a),
            })

    # Holm-Bonferroni over all t-test p-values
    p_vals = [r["p_ttest"] for r in comparisons_raw]
    adj = holm_bonferroni(p_vals)
    for r, a in zip(comparisons_raw, adj):
        r["p_ttest_holm"] = a
        r["significant_holm05"] = a < 0.05

    return comparisons_raw


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, nargs="+", default=DEFAULT_SEEDS)
    return p.parse_args()


def main():
    args = parse_args()
    seeds = args.seeds
    t0 = time.perf_counter()

    print(f"[E1] Loading original modules ...", flush=True)
    inj_mod = _load_module("inject_orig", SCRIPTS / "02_inject_anomalies.py")
    score_mod = _load_module("score_orig", SCRIPTS / "10_run_anomaly_experiments.py")

    # Check inject module has per-dataset inject functions
    for did in ["d1", "d2", "d3"]:
        fn_name = f"inject_{did}"
        if not hasattr(inj_mod, fn_name):
            print(f"  WARNING: inject module missing {fn_name} — injection will be done inline")
            break

    all_seed_data = {}
    for seed in seeds:
        t_seed = time.perf_counter()
        print(f"[E1] seed={seed} ...", flush=True)
        # For seed 42: if already computed, load from existing seed42 tables
        tables_dir = ARTIFACTS / "seeds" / f"seed{seed}" / "tables"
        if seed == 42 and (tables_dir / "baseline.csv").exists():
            print(f"  seed=42 already computed, loading committed tables", flush=True)
            bl = pd.read_csv(ARTIFACTS / "seeds" / "seed42" / "tables" / "baseline.csv")
            pf = pd.read_csv(ARTIFACTS / "seeds" / "seed42" / "tables" / "per_family.csv")
            seed_data = {}
            for did in DATASETS:
                bl_did = bl[bl["dataset"] == did].set_index("detector")
                seed_data[did] = {
                    "baseline": {
                        det: {"f1": bl_did.loc[det, "f1"],
                              "precision": bl_did.loc[det, "precision"],
                              "recall": bl_did.loc[det, "recall"],
                              "auc_pr": bl_did.loc[det, "auc_pr"],
                              "fpr": bl_did.loc[det, "fpr_at_best_f1"],
                              "threshold": bl_did.loc[det, "best_threshold"]}
                        for det in DETECTORS
                    },
                    "family_recall": dict(zip(
                        pf[pf["dataset"] == did]["family"],
                        pf[pf["dataset"] == did]["recall"]
                    )),
                    "oracle_f1": bl_did.loc["hybrid_lr", "f1"],
                    "nested_f1": None,  # will compute below
                }
            # Compute nested F1 from seed42 scores if available
            score_dir = ARTIFACTS / "seeds" / "seed42" / "scores"
            if score_dir.exists():
                for did in DATASETS:
                    score_df = pd.read_parquet(score_dir / f"{did}_scores.parquet")
                    y = score_df["y"].to_numpy()
                    hl_scores = score_df["hybrid_lr"].to_numpy()
                    seed_data[did]["nested_f1"] = nested_f1(y, hl_scores)
            all_seed_data[seed] = seed_data
        else:
            try:
                result = run_one_seed(seed, inj_mod, score_mod)
                # Extract serialisable data
                seed_data = {}
                for did in DATASETS:
                    seed_data[did] = {
                        "baseline": result[did]["baseline"],
                        "family_recall": result[did]["family_recall"],
                        "oracle_f1": result[did]["oracle_f1"],
                        "nested_f1": result[did]["nested_f1"],
                    }
                all_seed_data[seed] = seed_data
            except Exception as ex:
                print(f"  ERROR seed={seed}: {ex}", flush=True)
                continue
        elapsed_seed = round(time.perf_counter() - t_seed, 1)
        print(f"  seed={seed} done in {elapsed_seed}s", flush=True)

    # Save raw per-seed JSON
    raw_path = OUT / "e1_per_seed.json"
    raw_path.write_text(json.dumps(
        {str(s): {did: {k: v for k, v in sd.items()
                        if not isinstance(v, (np.ndarray,))}
                  for did, sd in seed_data.items()}
         for s, seed_data in all_seed_data.items()},
        indent=2, default=float
    ), encoding="utf-8")

    # --- Build e1_multiseed_metrics.csv ---
    metric_rows = []
    for det in DETECTORS:
        for did in DATASETS:
            f1_arr = np.array([all_seed_data[s][did]["baseline"][det]["f1"]
                               for s in seeds if s in all_seed_data])
            pr_arr = np.array([all_seed_data[s][did]["baseline"][det]["precision"]
                               for s in seeds if s in all_seed_data])
            rc_arr = np.array([all_seed_data[s][did]["baseline"][det]["recall"]
                               for s in seeds if s in all_seed_data])
            au_arr = np.array([all_seed_data[s][did]["baseline"][det]["auc_pr"]
                               for s in seeds if s in all_seed_data])
            n = len(f1_arr)
            t_crit = st.t.ppf(0.975, df=max(n-1, 1))
            ci_half = t_crit * f1_arr.std(ddof=1) / np.sqrt(n)
            metric_rows.append({
                "dataset": did, "detector": det, "n_seeds": n,
                "f1_mean": float(f1_arr.mean()), "f1_std": float(f1_arr.std(ddof=1)),
                "f1_ci95_lo": float(f1_arr.mean() - ci_half),
                "f1_ci95_hi": float(f1_arr.mean() + ci_half),
                "f1_min": float(f1_arr.min()), "f1_max": float(f1_arr.max()),
                "precision_mean": float(pr_arr.mean()), "precision_std": float(pr_arr.std(ddof=1)),
                "recall_mean": float(rc_arr.mean()), "recall_std": float(rc_arr.std(ddof=1)),
                "auc_pr_mean": float(au_arr.mean()), "auc_pr_std": float(au_arr.std(ddof=1)),
            })
    pd.DataFrame(metric_rows).to_csv(OUT / "e1_multiseed_metrics.csv", index=False)

    # --- Significance tests ---
    sig_rows = run_significance(all_seed_data)
    pd.DataFrame(sig_rows).to_csv(OUT / "e1_significance.csv", index=False)

    # --- Per-family recall multi-seed ---
    all_families = sorted({
        f for s in all_seed_data.values()
        for did_data in s.values()
        for f in did_data["family_recall"].keys()
    })
    fam_rows = []
    for did in DATASETS:
        for fam in sorted({
            f for s in all_seed_data.values()
            for f in all_seed_data[list(all_seed_data.keys())[0]][did]["family_recall"].keys()
        }):
            recalls = np.array([all_seed_data[s][did]["family_recall"].get(fam, np.nan)
                                for s in seeds if s in all_seed_data])
            recalls = recalls[~np.isnan(recalls)]
            n = len(recalls)
            if n == 0:
                continue
            t_crit = st.t.ppf(0.975, df=max(n-1, 1))
            ci_half = t_crit * recalls.std(ddof=1) / np.sqrt(n) if n > 1 else 0.0
            fam_rows.append({
                "dataset": did, "family": fam, "n_seeds": n,
                "recall_mean": float(recalls.mean()),
                "recall_std": float(recalls.std(ddof=1)) if n > 1 else 0.0,
                "recall_ci95_lo": float(recalls.mean() - ci_half),
                "recall_ci95_hi": float(recalls.mean() + ci_half),
                "recall_min": float(recalls.min()),
                "recall_max": float(recalls.max()),
            })
    pd.DataFrame(fam_rows).to_csv(OUT / "e1_perfamily_recall_multiseed.csv", index=False)

    # --- Threshold honesty check ---
    thr_rows = []
    for did in DATASETS:
        for seed in seeds:
            if seed not in all_seed_data:
                continue
            oracle = all_seed_data[seed][did]["oracle_f1"]
            nested = all_seed_data[seed][did].get("nested_f1")
            thr_rows.append({
                "dataset": did, "seed": seed,
                "oracle_f1": float(oracle),
                "nested_f1": float(nested) if nested is not None else float("nan"),
                "bias": float(oracle - nested) if nested is not None else float("nan"),
            })
    thr_df = pd.DataFrame(thr_rows)
    thr_df.to_csv(OUT / "e1_threshold_nested_vs_oracle.csv", index=False)

    # --- Boxplot figure ---
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 3, figsize=(12, 5))
        for ax, did in zip(axes, DATASETS):
            data = []
            labels = []
            for det in DETECTORS:
                vals = [all_seed_data[s][did]["baseline"][det]["f1"]
                        for s in seeds if s in all_seed_data]
                data.append(vals)
                labels.append(det)
            ax.boxplot(data, labels=labels, medianprops={"color": "red"})
            ax.set_title(f"{did}")
            ax.set_ylabel("F1" if did == "D1" else "")
            ax.set_ylim(0, 1)
            ax.tick_params(axis="x", rotation=45)
        fig.suptitle(f"E1 Multi-seed F1 distribution ({len(seeds)} seeds: {seeds[0]}-{seeds[-1]})")
        plt.tight_layout()
        plt.savefig(OUT / "e1_f1_boxplots_by_dataset.png", dpi=150)
        plt.close()
        print(f"[E1] Boxplot saved.", flush=True)
    except Exception as ex:
        print(f"[E1] Boxplot skipped ({ex})", flush=True)

    # --- Console summary ---
    elapsed = round(time.perf_counter() - t0, 1)
    print(f"\n[E1] Done in {elapsed}s. Outputs: {OUT}")

    metrics_df = pd.read_csv(OUT / "e1_multiseed_metrics.csv")
    print("\nF1 mean +/- std (hybrid_lr):")
    hl = metrics_df[metrics_df["detector"] == "hybrid_lr"][["dataset", "f1_mean", "f1_std"]]
    print(hl.to_string(index=False))

    print("\nKey significance results (hybrid_lr vs hybrid_fixed):")
    sig_df = pd.read_csv(OUT / "e1_significance.csv")
    lr_vs_fixed = sig_df[sig_df["comparison"] == "lr_vs_fixed"][
        ["dataset", "mean_diff", "p_ttest", "p_ttest_holm", "significant_holm05", "cohens_d"]
    ]
    print(lr_vs_fixed.to_string(index=False))

    print("\nThreshold bias (oracle - nested) for hybrid_lr:")
    thr_summary = thr_df.groupby("dataset")[["oracle_f1", "nested_f1", "bias"]].mean()
    print(thr_summary.round(4))


if __name__ == "__main__":
    main()
