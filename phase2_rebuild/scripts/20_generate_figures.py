"""Generate all paper figures from existing results tables.

Outputs to phase2_rebuild/results/figures/ as PDF (vector) and PNG (preview).

Figures:
  fig2_pr_curves.pdf        -- PR curves per dataset, all detectors
  fig3_confmat.pdf          -- 3-panel confusion matrices at best-F1 threshold (hybrid_lr)
  fig4_threshold_sweep.pdf  -- F1/precision/recall/FPR vs threshold (hybrid_lr)
  fig5_scalability.pdf      -- D2 scalability, runtime vs n + F1 vs n
  fig6_perfamily.pdf        -- per-anomaly-family recall heatmap
  fig7_ablation.pdf         -- leave-one-out F1 bars per dataset
  fig8_sql_matrix.pdf       -- SQL transpile dialect-pair AST-equivalence heatmap

(Fig 1, the architecture diagram, is TikZ inside the .tex source.)
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (confusion_matrix, precision_recall_curve)

ROOT = Path(__file__).resolve().parents[1]
SCORES_DIR = ROOT / "results" / "scores"
TABLES_DIR = ROOT / "results" / "tables"
FIGS_DIR = ROOT / "results" / "figures"
FIGS_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = ["D1", "D2", "D3"]
DATASET_TITLES = {
    "D1": "D1: SEC EDGAR GL",
    "D2": "D2: NYC FY2024 Payroll",
    "D3": "D3: UCI Credit Default",
}
DETECTORS = ["rule", "stat", "iforest", "lof", "hybrid", "hybrid_lr"]
DET_COLOR = {
    "rule":      "#1b9e77",
    "stat":      "#d95f02",
    "iforest":   "#7570b3",
    "lof":       "#e7298a",
    "hybrid":    "#66a61e",
    "hybrid_lr": "#e6ab02",
}

sns.set_context("paper", font_scale=0.95)
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.bbox": "tight",
    "savefig.dpi": 200,
})


def _load_scores(did: str) -> pd.DataFrame:
    return pd.read_parquet(SCORES_DIR / f"{did}_scores.parquet")


def _save(fig, name: str):
    fig.savefig(FIGS_DIR / f"{name}.pdf")
    fig.savefig(FIGS_DIR / f"{name}.png", dpi=200)
    plt.close(fig)
    print(f"  wrote {name}.{{pdf,png}}")


def fig_pr_curves():
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.4), sharey=True)
    for ax, did in zip(axes, DATASETS):
        sc = _load_scores(did)
        y = sc["y"].to_numpy()
        for det in DETECTORS:
            if det not in sc.columns:
                continue
            p, r, _ = precision_recall_curve(y, sc[det].to_numpy())
            ax.plot(r, p, label=det, color=DET_COLOR[det], linewidth=1.4)
        ax.set_title(DATASET_TITLES[did], fontsize=10)
        ax.set_xlabel("Recall")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.02)
        ax.grid(True, alpha=0.25)
    axes[0].set_ylabel("Precision")
    axes[-1].legend(loc="upper right", fontsize=7, frameon=True)
    fig.tight_layout()
    _save(fig, "fig2_pr_curves")


def fig_confmat():
    fig, axes = plt.subplots(1, 3, figsize=(9.5, 3.2))
    for ax, did in zip(axes, DATASETS):
        sc = _load_scores(did)
        y = sc["y"].to_numpy()
        s = sc["hybrid_lr"].to_numpy()
        # Best-F1 threshold
        p, r, t = precision_recall_curve(y, s)
        f1 = np.where((p + r) > 0, 2 * p * r / (p + r + 1e-12), 0.0)
        if t.size == 0:
            tau = 0.5
        else:
            tau = float(t[max(0, np.argmax(f1[:-1]))])
        yhat = (s >= tau).astype(int)
        cm = confusion_matrix(y, yhat, labels=[0, 1])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                    xticklabels=["Normal", "Anomaly"],
                    yticklabels=["Normal", "Anomaly"], cbar=False,
                    annot_kws={"size": 9})
        ax.set_title(f"{DATASET_TITLES[did]}\n$\\tau$={tau:.3f}", fontsize=9)
        ax.set_xlabel("Predicted")
        if ax is axes[0]:
            ax.set_ylabel("True")
    fig.tight_layout()
    _save(fig, "fig3_confmat")


def fig_threshold_sweep():
    df = pd.read_csv(TABLES_DIR / "threshold_sweep.csv")
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.2), sharey=True)
    for ax, did in zip(axes, DATASETS):
        sub = df[df["dataset"] == did].sort_values("threshold")
        ax.plot(sub["threshold"], sub["f1"], color="#1f77b4", label="F1", linewidth=1.5)
        ax.plot(sub["threshold"], sub["precision"], color="#2ca02c", label="Precision",
                linewidth=1.2, linestyle="--")
        ax.plot(sub["threshold"], sub["recall"], color="#ff7f0e", label="Recall",
                linewidth=1.2, linestyle="--")
        if "fpr" in sub.columns:
            ax.plot(sub["threshold"], sub["fpr"], color="#d62728", label="FPR",
                    linewidth=1.0, linestyle=":")
        ax.set_title(DATASET_TITLES[did], fontsize=10)
        ax.set_xlabel(r"Decision threshold $\tau$")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.02)
        ax.grid(True, alpha=0.25)
    axes[0].set_ylabel("Metric")
    axes[-1].legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    _save(fig, "fig4_threshold_sweep")


def fig_scalability():
    df = pd.read_csv(TABLES_DIR / "scalability.csv").sort_values("n_rows")
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.0))
    ax1 = axes[0]
    ax1.plot(df["n_rows"], df["elapsed_sec"], "o-", color="#1f77b4")
    ax1.set_xlabel("Sample size $n$")
    ax1.set_ylabel("Runtime (s)")
    ax1.set_title("Wall-clock vs $n$", fontsize=10)
    ax1.grid(True, alpha=0.3)
    # Fit linear reference
    if len(df) >= 2:
        slope = df["elapsed_sec"].iloc[-1] / df["n_rows"].iloc[-1]
        xs = np.linspace(df["n_rows"].min(), df["n_rows"].max(), 50)
        ax1.plot(xs, slope * xs, "--", color="grey", alpha=0.7,
                 label=f"linear ref ({slope*1e6:.2f} $\\mu$s/row)")
        ax1.legend(fontsize=8)
    ax2 = axes[1]
    ax2.plot(df["n_rows"], df["f1"], "s-", color="#d62728")
    ax2.set_xlabel("Sample size $n$")
    ax2.set_ylabel("F1 (hybrid$_{LR}$)")
    ax2.set_title("Quality vs $n$", fontsize=10)
    ax2.set_ylim(0, 1)
    ax2.grid(True, alpha=0.3)
    fig.tight_layout()
    _save(fig, "fig5_scalability")


def fig_perfamily():
    df = pd.read_csv(TABLES_DIR / "per_family.csv")
    # Pivot: rows=family, cols=dataset, values=recall
    pivot = df.pivot_table(index="family", columns="dataset", values="recall", aggfunc="mean")
    pivot = pivot[DATASETS]
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="YlGnBu", ax=ax,
                cbar_kws={"label": "Recall (hybrid$_{LR}$)"})
    ax.set_xlabel("Dataset")
    ax.set_ylabel("Anomaly family")
    ax.set_title("Per-family recall at best-F1 threshold", fontsize=10)
    fig.tight_layout()
    _save(fig, "fig6_perfamily")


def fig_ablation():
    df = pd.read_csv(TABLES_DIR / "ablation.csv")
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    order = ["none", "rule", "stat", "iforest", "lof"]
    width = 0.25
    x = np.arange(len(order))
    for i, did in enumerate(DATASETS):
        sub = df[df["dataset"] == did].set_index("leave_out").reindex(order)
        ax.bar(x + (i - 1) * width, sub["f1"].fillna(0), width,
               label=DATASET_TITLES[did])
    ax.set_xticks(x)
    ax.set_xticklabels(["full"] + order[1:])
    ax.set_xlabel("Detector removed from stacker")
    ax.set_ylabel("F1 (hybrid$_{LR}$)")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.25, axis="y")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    _save(fig, "fig7_ablation")


def fig_sql_matrix():
    df = pd.read_csv(TABLES_DIR / "sql_migration_matrix.csv")
    pivot = df.pivot(index="src_dialect", columns="tgt_dialect", values="ast_equiv_rate")
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="RdYlGn", vmin=0, vmax=1,
                ax=ax, cbar_kws={"label": "AST-equivalence rate"})
    ax.set_xlabel("Target dialect")
    ax.set_ylabel("Source dialect")
    ax.set_title("Cross-dialect SQL transpilation\n(AST footprint equivalence)", fontsize=10)
    fig.tight_layout()
    _save(fig, "fig8_sql_matrix")


def main() -> int:
    print("Generating figures ...")
    fig_pr_curves()
    fig_confmat()
    fig_threshold_sweep()
    fig_scalability()
    fig_perfamily()
    fig_ablation()
    fig_sql_matrix()
    print("\nAll figures written to", FIGS_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
