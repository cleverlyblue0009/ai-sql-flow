"""Generate large, clear standalone figures for the paper into paper/images/.

Same content as 20_generate_figures.py but with:
  - significantly larger figure sizes
  - 300 DPI PNGs
  - bigger fonts / line widths / annotations
  - tight layout but generous margins
  - separate PNG + PDF for each figure

Outputs:
  paper/images/fig2_pr_curves.{pdf,png}
  paper/images/fig3_confmat.{pdf,png}
  paper/images/fig4_threshold_sweep.{pdf,png}
  paper/images/fig5_scalability.{pdf,png}
  paper/images/fig6_perfamily.{pdf,png}
  paper/images/fig7_ablation.{pdf,png}
  paper/images/fig8_sql_matrix.{pdf,png}
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import confusion_matrix, precision_recall_curve

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SCORES_DIR = ROOT / "results" / "scores"
TABLES_DIR = ROOT / "results" / "tables"
OUT_DIR = REPO / "paper" / "images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = ["D1", "D2", "D3"]
DATASET_TITLES = {
    "D1": "D1: SEC EDGAR GL",
    "D2": "D2: NYC FY2024 Payroll",
    "D3": "D3: UCI Credit Default",
}
DETECTORS = ["rule", "stat", "iforest", "lof", "hybrid", "hybrid_lr"]
DET_LABEL = {
    "rule":      "Rule",
    "stat":      "Robust Stat",
    "iforest":   "Isolation Forest",
    "lof":       "LOF",
    "hybrid":    "Hybrid (fixed)",
    "hybrid_lr": "Hybrid$_\\mathrm{LR}$ (ours)",
}
DET_COLOR = {
    "rule":      "#1b9e77",
    "stat":      "#d95f02",
    "iforest":   "#7570b3",
    "lof":       "#e7298a",
    "hybrid":    "#66a61e",
    "hybrid_lr": "#e6ab02",
}
DET_LW = {
    "rule": 2.0, "stat": 2.0, "iforest": 2.0, "lof": 2.0,
    "hybrid": 2.2, "hybrid_lr": 3.0,
}

# Larger paper-quality typography
sns.set_context("talk", font_scale=0.85)
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.titlesize": 16,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 11,
    "axes.linewidth": 1.1,
    "lines.linewidth": 2.0,
    "savefig.bbox": "tight",
    "savefig.dpi": 300,
})


def _load_scores(did: str) -> pd.DataFrame:
    return pd.read_parquet(SCORES_DIR / f"{did}_scores.parquet")


def _save(fig, name: str):
    fig.savefig(OUT_DIR / f"{name}.pdf")
    fig.savefig(OUT_DIR / f"{name}.png", dpi=300)
    plt.close(fig)
    print(f"  wrote {name}.{{pdf,png}}  ->  {OUT_DIR / name}")


def fig_pr_curves():
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    for ax, did in zip(axes, DATASETS):
        sc = _load_scores(did)
        y = sc["y"].to_numpy()
        for det in DETECTORS:
            if det not in sc.columns:
                continue
            p, r, _ = precision_recall_curve(y, sc[det].to_numpy())
            ax.plot(r, p, label=DET_LABEL[det], color=DET_COLOR[det],
                    linewidth=DET_LW[det])
        ax.set_title(DATASET_TITLES[did])
        ax.set_xlabel("Recall")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.02)
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("Precision")
    axes[-1].legend(loc="upper right", frameon=True, framealpha=0.95)
    fig.suptitle("Precision–Recall curves per detector across the three real-world datasets",
                 fontsize=18, y=1.03)
    fig.tight_layout()
    _save(fig, "fig2_pr_curves")


def fig_confmat():
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5))
    for ax, did in zip(axes, DATASETS):
        sc = _load_scores(did)
        y = sc["y"].to_numpy()
        s = sc["hybrid_lr"].to_numpy()
        p, r, t = precision_recall_curve(y, s)
        f1 = np.where((p + r) > 0, 2 * p * r / (p + r + 1e-12), 0.0)
        tau = float(t[max(0, np.argmax(f1[:-1]))]) if t.size else 0.5
        yhat = (s >= tau).astype(int)
        cm = confusion_matrix(y, yhat, labels=[0, 1])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                    xticklabels=["Normal", "Anomaly"],
                    yticklabels=["Normal", "Anomaly"], cbar=False,
                    annot_kws={"size": 18, "weight": "bold"},
                    linewidths=0.6, linecolor="white")
        ax.set_title(f"{DATASET_TITLES[did]}  ($\\tau$={tau:.3f})")
        ax.set_xlabel("Predicted")
        if ax is axes[0]:
            ax.set_ylabel("True")
    fig.suptitle("Confusion matrices at the stacked hybrid's best-F1 threshold",
                 fontsize=18, y=1.03)
    fig.tight_layout()
    _save(fig, "fig3_confmat")


def fig_threshold_sweep():
    df = pd.read_csv(TABLES_DIR / "threshold_sweep.csv")
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    for ax, did in zip(axes, DATASETS):
        sub = df[df["dataset"] == did].sort_values("threshold")
        ax.plot(sub["threshold"], sub["f1"],        color="#1f77b4", label="F1",        linewidth=2.8)
        ax.plot(sub["threshold"], sub["precision"], color="#2ca02c", label="Precision", linewidth=2.0, linestyle="--")
        ax.plot(sub["threshold"], sub["recall"],    color="#ff7f0e", label="Recall",    linewidth=2.0, linestyle="--")
        if "fpr" in sub.columns:
            ax.plot(sub["threshold"], sub["fpr"], color="#d62728", label="FPR",
                    linewidth=1.8, linestyle=":")
        # Mark the F1 peak
        idx = sub["f1"].idxmax()
        if pd.notna(idx):
            best = sub.loc[idx]
            ax.axvline(best["threshold"], color="black", alpha=0.35, linewidth=1, linestyle="-.")
            ax.annotate(f"$\\tau^*$={best['threshold']:.2f}\nF1={best['f1']:.3f}",
                        xy=(best["threshold"], best["f1"]),
                        xytext=(8, -10), textcoords="offset points",
                        fontsize=11, ha="left",
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="grey", alpha=0.85))
        ax.set_title(DATASET_TITLES[did])
        ax.set_xlabel(r"Decision threshold $\tau$")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.02)
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("Metric value")
    axes[-1].legend(loc="upper right", frameon=True, framealpha=0.95)
    fig.suptitle("Threshold sweep of the stacked hybrid score",
                 fontsize=18, y=1.03)
    fig.tight_layout()
    _save(fig, "fig4_threshold_sweep")


def fig_scalability():
    df = pd.read_csv(TABLES_DIR / "scalability.csv").sort_values("n_rows")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    ax1 = axes[0]
    ax1.plot(df["n_rows"], df["elapsed_sec"], "o-", color="#1f77b4", markersize=10, linewidth=2.6)
    if len(df) >= 2:
        slope = df["elapsed_sec"].iloc[-1] / df["n_rows"].iloc[-1]
        xs = np.linspace(df["n_rows"].min(), df["n_rows"].max(), 50)
        ax1.plot(xs, slope * xs, "--", color="grey", alpha=0.8, linewidth=1.8,
                 label=f"linear ref ($\\approx${slope*1e6:.1f} $\\mu$s/row)")
        ax1.legend()
    for _, row in df.iterrows():
        ax1.annotate(f"{row['elapsed_sec']:.2f}s",
                     xy=(row["n_rows"], row["elapsed_sec"]),
                     xytext=(8, 4), textcoords="offset points", fontsize=11)
    ax1.set_xlabel("Sample size $n$")
    ax1.set_ylabel("Wall-clock runtime (s)")
    ax1.set_title("Runtime vs. $n$")
    ax1.grid(True, alpha=0.3)

    ax2 = axes[1]
    ax2.plot(df["n_rows"], df["f1"], "s-", color="#d62728", markersize=10, linewidth=2.6)
    for _, row in df.iterrows():
        ax2.annotate(f"{row['f1']:.3f}",
                     xy=(row["n_rows"], row["f1"]),
                     xytext=(8, 6), textcoords="offset points", fontsize=11)
    ax2.set_xlabel("Sample size $n$")
    ax2.set_ylabel("F1 (hybrid$_\\mathrm{LR}$)")
    ax2.set_title("Quality vs. $n$")
    ax2.set_ylim(0, 1)
    ax2.grid(True, alpha=0.3)

    fig.suptitle("Scalability on NYC payroll: linear runtime, stable quality",
                 fontsize=18, y=1.03)
    fig.tight_layout()
    _save(fig, "fig5_scalability")


def fig_perfamily():
    df = pd.read_csv(TABLES_DIR / "per_family.csv")
    pivot = df.pivot_table(index="family", columns="dataset", values="recall", aggfunc="mean")
    pivot = pivot[DATASETS]
    fig, ax = plt.subplots(figsize=(9, 8))
    sns.heatmap(pivot, annot=True, fmt=".3f", cmap="YlGnBu",
                ax=ax, vmin=0, vmax=1,
                annot_kws={"size": 13, "weight": "bold"},
                linewidths=0.6, linecolor="white",
                cbar_kws={"label": "Recall at best-F1 threshold"})
    ax.set_xlabel("Dataset")
    ax.set_ylabel("Anomaly family")
    ax.set_title("Per-family recall (stacked hybrid)")
    fig.tight_layout()
    _save(fig, "fig6_perfamily")


def fig_ablation():
    df = pd.read_csv(TABLES_DIR / "ablation.csv")
    fig, ax = plt.subplots(figsize=(13, 6))
    order = ["none", "rule", "stat", "iforest", "lof"]
    labels = ["Full", "−rule", "−stat", "−iforest", "−lof"]
    width = 0.26
    x = np.arange(len(order))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    for i, did in enumerate(DATASETS):
        sub = df[df["dataset"] == did].set_index("leave_out").reindex(order)
        bars = ax.bar(x + (i - 1) * width, sub["f1"].fillna(0), width,
                      label=DATASET_TITLES[did], color=colors[i], edgecolor="black", linewidth=0.6)
        for b, v in zip(bars, sub["f1"].fillna(0).values):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.012, f"{v:.3f}",
                    ha="center", va="bottom", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Stacker configuration (full vs. leave-one-detector-out)")
    ax.set_ylabel("F1 (hybrid$_\\mathrm{LR}$)")
    ax.set_ylim(0, 1.02)
    ax.grid(True, alpha=0.25, axis="y")
    ax.legend(loc="upper right", frameon=True, framealpha=0.95)
    ax.set_title("Leave-one-detector-out ablation")
    fig.tight_layout()
    _save(fig, "fig7_ablation")


def fig_sql_matrix():
    df = pd.read_csv(TABLES_DIR / "sql_migration_matrix.csv")
    pivot = df.pivot(index="src_dialect", columns="tgt_dialect", values="ast_equiv_rate")
    fig, ax = plt.subplots(figsize=(9, 7.5))
    sns.heatmap(pivot, annot=True, fmt=".3f", cmap="RdYlGn", vmin=0, vmax=1,
                ax=ax, annot_kws={"size": 14, "weight": "bold"},
                linewidths=0.6, linecolor="white",
                cbar_kws={"label": "AST-footprint equivalence rate"})
    ax.set_xlabel("Target dialect")
    ax.set_ylabel("Source dialect")
    ax.set_title("Cross-dialect SQL transpilation\n(strict AST-footprint equivalence over 575 pairs)")
    fig.tight_layout()
    _save(fig, "fig8_sql_matrix")


def main() -> int:
    print(f"Generating LARGE figures into {OUT_DIR} ...")
    fig_pr_curves()
    fig_confmat()
    fig_threshold_sweep()
    fig_scalability()
    fig_perfamily()
    fig_ablation()
    fig_sql_matrix()
    print(f"\nAll figures written to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
