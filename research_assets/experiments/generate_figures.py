#!/usr/bin/env python3
"""
Publication-quality figure generation for IEEE Access paper.
All figures derive exclusively from experiment result JSON files.
Outputs: PNG (300 DPI) + SVG per figure.
"""

import sys, json, logging
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import matplotlib.ticker as mticker

try:
    import seaborn as sns
    HAS_SNS = True
except ImportError:
    HAS_SNS = False

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_assets.experiments.experiment_config import (
    RESULTS_DIR, FIGURES_DIR, FIGURE_DPI, FIGURE_WIDTH, FIGURE_HEIGHT,
    PALETTE, BASELINE_PALETTE
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── IEEE-style global theme ───────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":       "serif",
    "font.serif":        ["DejaVu Serif", "Times New Roman", "Times", "serif"],
    "font.size":         10,
    "axes.titlesize":    11,
    "axes.labelsize":    10,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "legend.fontsize":   9,
    "figure.dpi":        FIGURE_DPI,
    "savefig.dpi":       FIGURE_DPI,
    "savefig.bbox":      "tight",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.3,
    "grid.linestyle":    "--",
})


def save_fig(fig: plt.Figure, name: str, subdir: str = ""):
    base = FIGURES_DIR / subdir if subdir else FIGURES_DIR
    base.mkdir(parents=True, exist_ok=True)
    for fmt in ["png", "svg"]:
        path = base / f"{name}.{fmt}"
        fig.savefig(path, format=fmt, bbox_inches="tight")
    log.info(f"  Saved: {name}.png / .svg")
    plt.close(fig)


def load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    log.warning(f"  Missing result file: {path}")
    return {}


# ── Figure 1: Ablation Study Bar Chart ────────────────────────────────────────

def fig_ablation():
    data = load_json(RESULTS_DIR / "ablation" / "ablation_results.json")
    agg  = data.get("aggregate", {})
    if not agg:
        log.warning("  Ablation data missing, skipping")
        return

    components = list(agg.keys())
    f1s    = [agg[c]["mean_f1"]   for c in components]
    stds   = [agg[c]["std_f1"]    for c in components]
    precs  = [agg[c]["mean_precision"] for c in components]
    recalls= [agg[c]["mean_recall"]    for c in components]

    # Sort by F1 desc
    order  = sorted(range(len(f1s)), key=lambda i: f1s[i], reverse=True)
    components = [components[i] for i in order]
    f1s    = [f1s[i]    for i in order]
    stds   = [stds[i]   for i in order]
    precs  = [precs[i]  for i in order]
    recalls= [recalls[i] for i in order]

    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))
    x   = np.arange(len(components))
    w   = 0.28
    colors = [PALETTE.get(c, "#888888") for c in components]

    bars = ax.bar(x - w, f1s,    w, label="F1-Score",  color=colors, alpha=0.85, edgecolor="white")
    ax.bar(x,     precs,  w, label="Precision", color=colors, alpha=0.55, edgecolor="white", hatch="//")
    ax.bar(x + w, recalls, w, label="Recall",    color=colors, alpha=0.35, edgecolor="white", hatch="..")
    ax.errorbar(x - w, f1s, yerr=stds, fmt="none", capsize=3, color="black", linewidth=1)

    # Highlight full system
    full_idx = next((i for i, c in enumerate(components) if c == "full_system"), None)
    if full_idx is not None:
        ax.get_children()[full_idx].set_edgecolor("black")
        ax.get_children()[full_idx].set_linewidth(2.0)

    ax.set_xticks(x)
    ax.set_xticklabels([c.replace("_", "\n") for c in components], fontsize=8)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Score")
    ax.set_title("Fig. 1: Ablation Study — Component-wise Performance Comparison")
    ax.legend(loc="upper right", ncol=3)
    ax.axhline(y=f1s[0] if full_idx == 0 else max(f1s), color="#1a73e8",
               linewidth=0.8, linestyle=":")
    fig.tight_layout()
    save_fig(fig, "fig1_ablation_study", "ablation")


# ── Figure 2: Baseline Comparison ─────────────────────────────────────────────

def fig_baseline():
    data = load_json(RESULTS_DIR / "baseline" / "baseline_results.json")
    agg  = data.get("aggregate", {})
    if not agg:
        log.warning("  Baseline data missing, skipping")
        return

    systems = list(agg.keys())
    metrics = ["mean_f1", "mean_precision", "mean_recall", "mean_accuracy"]
    labels  = ["F1-Score", "Precision", "Recall", "Accuracy"]
    x = np.arange(len(systems))
    w = 0.20

    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))
    for i, (m, lbl) in enumerate(zip(metrics, labels)):
        vals = [agg[s].get(m, 0) for s in systems]
        bars = ax.bar(x + (i - 1.5) * w, vals, w, label=lbl, alpha=0.80)

    # Highlight proposed system
    full_idx = next((i for i, s in enumerate(systems)
                     if "hybrid" in s or "full" in s), None)
    if full_idx is not None:
        ax.axvspan(full_idx - 0.55, full_idx + 0.55,
                   color="#1a73e8", alpha=0.08, zorder=0)
        ax.text(full_idx, 1.03, "★ Proposed", ha="center", fontsize=8,
                color="#1a73e8", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([s.replace("_", "\n") for s in systems], fontsize=8)
    ax.set_ylim(0, 1.10)
    ax.set_ylabel("Score")
    ax.set_title("Fig. 2: Baseline Comparison — Proposed System vs. Six Baselines")
    ax.legend(loc="lower right", ncol=2)
    fig.tight_layout()
    save_fig(fig, "fig2_baseline_comparison", "baseline")


# ── Figure 3: Scalability ──────────────────────────────────────────────────────

def fig_scalability():
    data = load_json(RESULTS_DIR / "scalability" / "scalability_results.json")
    res  = data.get("results", {})
    if not res:
        log.warning("  Scalability data missing, skipping")
        return

    sizes      = sorted([int(k) for k in res])
    latencies  = [res[str(n)]["mean_latency_ms"]  for n in sizes]
    stds       = [res[str(n)]["std_latency_ms"]   for n in sizes]
    throughputs= [res[str(n)]["throughput_rows_per_s"] for n in sizes]
    memories   = [res[str(n)]["mean_mem_delta_mb"] for n in sizes]

    fig, axes = plt.subplots(1, 3, figsize=(FIGURE_WIDTH * 1.5, FIGURE_HEIGHT * 0.8))

    # (a) Latency
    ax = axes[0]
    ax.errorbar(sizes, latencies, yerr=stds, marker="o", color="#1a73e8",
                linewidth=2, capsize=4, markersize=6)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Dataset Size (rows)")
    ax.set_ylabel("Latency (ms)")
    ax.set_title("(a) Latency vs. Size")

    scaling_exp = data.get("scaling_exponent")
    if scaling_exp:
        ax.text(0.05, 0.92, f"slope={scaling_exp:.3f}", transform=ax.transAxes,
                fontsize=8, color="#d93025")

    # (b) Throughput
    ax = axes[1]
    ax.plot(sizes, throughputs, marker="s", color="#0f9d58", linewidth=2, markersize=6)
    ax.set_xscale("log")
    ax.set_xlabel("Dataset Size (rows)")
    ax.set_ylabel("Rows / Second")
    ax.set_title("(b) Throughput vs. Size")

    # (c) Memory
    ax = axes[2]
    ax.bar(range(len(sizes)), memories, color="#e8710a", alpha=0.80, edgecolor="white")
    ax.set_xticks(range(len(sizes)))
    ax.set_xticklabels([f"{s//1000}K" if s >= 1000 else str(s) for s in sizes], fontsize=8)
    ax.set_xlabel("Dataset Size")
    ax.set_ylabel("Memory Δ (MB)")
    ax.set_title("(c) Memory Usage vs. Size")

    fig.suptitle("Fig. 3: Scalability Analysis", fontsize=11, y=1.02)
    fig.tight_layout()
    save_fig(fig, "fig3_scalability", "scalability")


# ── Figure 4: Robustness ──────────────────────────────────────────────────────

def fig_robustness():
    data  = load_json(RESULTS_DIR / "robustness" / "robustness_results.json")
    noise = data.get("noise_level_results", [])
    adv   = data.get("adversarial_results", [])
    if not noise:
        log.warning("  Robustness data missing, skipping")
        return

    fig, axes = plt.subplots(1, 2, figsize=(FIGURE_WIDTH * 1.3, FIGURE_HEIGHT * 0.85))

    # (a) Noise degradation
    ax = axes[0]
    levels = [r["noise_frac"] for r in noise]
    f1s    = [r["f1"]        for r in noise]
    precs  = [r["precision"] for r in noise]
    recs   = [r["recall"]    for r in noise]

    ax.plot(levels, f1s,    "o-", color="#1a73e8", label="F1-Score",  linewidth=2)
    ax.plot(levels, precs,  "s--",color="#e8710a", label="Precision", linewidth=1.5)
    ax.plot(levels, recs,   "^-.",color="#0f9d58", label="Recall",    linewidth=1.5)
    ax.set_xlabel("Noise Level (fraction)")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.set_title("(a) Performance Under Noise")
    ax.legend(fontsize=8)
    ax.fill_between(levels, f1s, alpha=0.08, color="#1a73e8")

    # (b) Adversarial pass bar
    ax = axes[1]
    if adv:
        names   = [r["test"][:20].replace("_","\n") for r in adv]
        colors  = ["#0f9d58" if "PASS" in r["status"] else "#d93025" for r in adv]
        values  = [1 if "PASS" in r["status"] else 0 for r in adv]
        y_pos   = range(len(names))
        ax.barh(y_pos, values, color=colors, alpha=0.85, edgecolor="white")
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names, fontsize=7)
        ax.set_xlim(0, 1.3)
        ax.set_xlabel("Pass (1) / Fail (0)")
        ax.set_title("(b) Adversarial Input Tests")
        pass_rate = data.get("adversarial_pass_rate", 0)
        ax.text(0.7, len(names) - 1.5, f"Pass rate: {pass_rate:.0%}",
                fontsize=9, color="black", fontweight="bold")

    fig.suptitle("Fig. 4: Robustness Analysis", fontsize=11, y=1.01)
    fig.tight_layout()
    save_fig(fig, "fig4_robustness", "robustness")


# ── Figure 5: Confidence Score Distributions ──────────────────────────────────

def fig_confidence():
    data = load_json(RESULTS_DIR / "confidence" / "confidence_results.json")
    ds_data = data.get("datasets", {})
    if not ds_data:
        log.warning("  Confidence data missing, skipping")
        return

    n_ds = len(ds_data)
    fig, axes = plt.subplots(2, max(2, (n_ds+1)//2),
                               figsize=(FIGURE_WIDTH * 1.4, FIGURE_HEIGHT))
    axes = axes.flatten()

    for idx, (ds_name, info) in enumerate(ds_data.items()):
        ax = axes[idx]
        hist    = info["score_distribution"]["histogram"]
        edges   = info["score_distribution"]["bin_edges"]
        centers = [(edges[i]+edges[i+1])/2 for i in range(len(hist))]
        ax.bar(centers, hist, width=edges[1]-edges[0],
               color="#1a73e8", alpha=0.70, edgecolor="white")

        best_t = info.get("best_threshold", 0.5)
        ax.axvline(x=best_t, color="#d93025", linewidth=1.5,
                   linestyle="--", label=f"Best θ={best_t:.2f}")

        mu  = info["score_distribution"]["mean"]
        std = info["score_distribution"]["std"]
        ax.text(0.62, 0.90, f"μ={mu:.3f}\nσ={std:.3f}",
                transform=ax.transAxes, fontsize=7.5, va="top",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

        ax.set_title(ds_name.replace("_", " ").title(), fontsize=9)
        ax.set_xlabel("Confidence Score")
        ax.set_ylabel("Count")
        ax.legend(fontsize=7)

    # hide unused axes
    for ax in axes[n_ds:]:
        ax.set_visible(False)

    fig.suptitle("Fig. 5: Confidence Score Distributions by Dataset", fontsize=11)
    fig.tight_layout()
    save_fig(fig, "fig5_confidence_distributions", "confidence")


# ── Figure 6: Confusion Matrices ──────────────────────────────────────────────

def fig_confusion_matrices():
    data = load_json(RESULTS_DIR / "false_positive" / "fp_analysis_results.json")
    ds_data = data.get("datasets", {})
    if not ds_data:
        log.warning("  FP data missing, skipping")
        return

    n_ds = min(len(ds_data), 4)
    fig, axes = plt.subplots(1, n_ds, figsize=(n_ds * 3.2, 3.2))
    if n_ds == 1:
        axes = [axes]

    for ax, (ds_name, info) in zip(axes, list(ds_data.items())[:n_ds]):
        cm_dict = info.get("confusion_matrix", {})
        if not cm_dict:
            continue
        cm = np.array([[cm_dict["tn"], cm_dict["fp"]],
                        [cm_dict["fn"], cm_dict["tp"]]])
        # Normalize
        cm_norm = cm.astype(float) / cm.sum()

        im = ax.imshow(cm_norm, interpolation="nearest",
                       cmap=plt.cm.Blues, vmin=0, vmax=1)
        thresh = 0.5
        for i in range(2):
            for j in range(2):
                ax.text(j, i,
                        f"{cm[i,j]}\n({cm_norm[i,j]:.2%})",
                        ha="center", va="center", fontsize=8,
                        color="white" if cm_norm[i,j] > thresh else "black")
        ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
        ax.set_xticklabels(["Pred\nNormal","Pred\nAnomaly"], fontsize=8)
        ax.set_yticklabels(["True\nNormal","True\nAnomaly"], fontsize=8)
        ax.set_title(ds_name.replace("_", " ").title(), fontsize=9)
        m = info.get("metrics", {})
        ax.set_xlabel(f"F1={m.get('f1',0):.3f}  FPR={m.get('fpr',0):.3f}", fontsize=8)

    fig.suptitle("Fig. 6: Confusion Matrices — Full Hybrid System", fontsize=11)
    fig.tight_layout()
    save_fig(fig, "fig6_confusion_matrices", "false_positive")


# ── Figure 7: Cross-validation CI Plot ────────────────────────────────────────

def fig_cross_validation():
    data = load_json(RESULTS_DIR / "cross_validation" / "cross_validation_results.json")
    ds_data = data.get("datasets", {})
    if not ds_data:
        log.warning("  CV data missing, skipping")
        return

    ds_names  = list(ds_data.keys())
    full_means = [ds_data[d]["full_system"]["mean_f1"]   for d in ds_names]
    full_ci_lo = [ds_data[d]["full_system"]["ci_95"][0]  for d in ds_names]
    full_ci_hi = [ds_data[d]["full_system"]["ci_95"][1]  for d in ds_names]
    base_means = [ds_data[d]["isolation_forest_baseline"]["mean_f1"] for d in ds_names]
    base_ci_lo = [ds_data[d]["isolation_forest_baseline"]["ci_95"][0] for d in ds_names]
    base_ci_hi = [ds_data[d]["isolation_forest_baseline"]["ci_95"][1] for d in ds_names]

    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT * 0.85))
    x = np.arange(len(ds_names))

    ax.errorbar(x - 0.15, full_means,
                yerr=[np.array(full_means) - np.array(full_ci_lo),
                      np.array(full_ci_hi) - np.array(full_means)],
                fmt="o", color="#1a73e8", capsize=5, linewidth=2,
                markersize=8, label="Full Hybrid System")
    ax.errorbar(x + 0.15, base_means,
                yerr=[np.array(base_means) - np.array(base_ci_lo),
                      np.array(base_ci_hi) - np.array(base_means)],
                fmt="s", color="#e8710a", capsize=5, linewidth=2,
                markersize=8, label="IsoForest Baseline", linestyle="--")

    # annotate p-values
    for i, ds in enumerate(ds_names):
        comp = ds_data[ds].get("statistical_comparison", {})
        p = comp.get("p_value")
        if p is not None:
            sig_str = "**" if p < 0.01 else ("*" if p < 0.05 else "ns")
            ax.text(i, max(full_means[i], base_means[i]) + 0.04,
                    sig_str, ha="center", fontsize=10, color="#d93025")

    ax.set_xticks(x)
    ax.set_xticklabels([d.replace("_", "\n") for d in ds_names], fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("F1-Score (95% CI)")
    ax.set_title(f"Fig. 7: Cross-Validation ({data.get('n_folds',5)}-fold × "
                 f"{data.get('n_repeats',10)} repeats)  **p<0.01  *p<0.05  ns=not significant")
    ax.legend(loc="lower right")
    fig.tight_layout()
    save_fig(fig, "fig7_cross_validation_ci", "confidence")


# ── Figure 8: Enterprise pipeline latency waterfall ───────────────────────────

def fig_enterprise():
    data = load_json(RESULTS_DIR / "enterprise" / "enterprise_results.json")
    pipeline = data.get("pipeline", {})
    stages   = pipeline.get("stages", [])
    if not stages:
        log.warning("  Enterprise data missing, skipping")
        return

    stage_names = [s.get("stage","?").replace("_"," ").title() for s in stages]
    latencies   = [s.get("latency_ms", 0) for s in stages]
    total_lat   = pipeline.get("total_latency_ms", sum(latencies))

    fig, axes = plt.subplots(1, 2, figsize=(FIGURE_WIDTH * 1.3, FIGURE_HEIGHT * 0.85))

    # (a) waterfall
    ax = axes[0]
    colors = plt.cm.Blues(np.linspace(0.35, 0.85, len(latencies)))
    bars = ax.barh(range(len(stage_names)), latencies, color=colors, edgecolor="white")
    ax.set_yticks(range(len(stage_names)))
    ax.set_yticklabels(stage_names, fontsize=9)
    ax.set_xlabel("Latency (ms)")
    ax.set_title(f"(a) Pipeline Stage Latency\n(total: {total_lat:.0f}ms)")
    for bar, v in zip(bars, latencies):
        ax.text(v + 0.5, bar.get_y() + bar.get_height()/2,
                f"{v:.1f}ms", va="center", fontsize=8)

    # (b) SQL translation confidence by complexity
    sql_data = data.get("sql_translations", [])
    if sql_data:
        complexities = sorted(set(t["complexity"] for t in sql_data))
        conf_by_comp = {c: [t["confidence"] for t in sql_data if t["complexity"] == c]
                        for c in complexities}
        ax2 = axes[1]
        bp = ax2.boxplot([conf_by_comp[c] for c in complexities],
                          patch_artist=True, notch=False,
                          medianprops=dict(color="white", linewidth=2))
        cmap = plt.cm.Blues(np.linspace(0.35, 0.85, len(complexities)))
        for patch, color in zip(bp["boxes"], cmap):
            patch.set_facecolor(color)
        ax2.set_xticklabels([c.title() for c in complexities], fontsize=9)
        ax2.set_ylim(0, 1.05)
        ax2.set_ylabel("Translation Confidence Score")
        ax2.set_xlabel("Query Complexity")
        ax2.set_title("(b) SQL Translation Confidence\nby Query Complexity")

    fig.suptitle("Fig. 8: Enterprise Case Study — Pipeline Performance", fontsize=11)
    fig.tight_layout()
    save_fig(fig, "fig8_enterprise_pipeline", "enterprise")


# ── Figure 9: Security test summary ───────────────────────────────────────────

def fig_security():
    data = load_json(RESULTS_DIR / "security" / "security_results.json")
    results = data.get("results", [])
    if not results:
        log.warning("  Security data missing, skipping")
        return

    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH * 0.9, FIGURE_HEIGHT * 0.85))
    names  = [r["test"][:28].replace("_", " ") for r in results]
    passes = [1 if "PASS" in r["status"] else 0 for r in results]
    sevs   = [r["severity"] for r in results]
    sev_colors = {"high": "#d93025", "medium": "#e8710a", "low": "#0f9d58"}
    colors = [sev_colors[s] for s in sevs]

    y = range(len(names))
    ax.barh(y, passes, color=colors, alpha=0.85, edgecolor="white")
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlim(0, 1.4)
    ax.set_xlabel("Pass (1) / Fail (0)")
    ax.set_title(f"Fig. 9: Security Validation\n"
                 f"Pass rate: {data.get('pass_rate', 0):.0%}  "
                 f"({data.get('pass_count',0)}/{len(results)} tests)")

    legend_patches = [mpatches.Patch(color=sev_colors[s], label=s.title())
                      for s in ["high", "medium", "low"]]
    ax.legend(handles=legend_patches, title="Severity", loc="lower right", fontsize=8)

    fig.tight_layout()
    save_fig(fig, "fig9_security_validation", "enterprise")


# ── Master runner ──────────────────────────────────────────────────────────────

def main():
    log.info("=" * 70)
    log.info("FIGURE GENERATION  —  IEEE Access Publication Package")
    log.info("=" * 70)

    generators = [
        ("Fig 1: Ablation Study",              fig_ablation),
        ("Fig 2: Baseline Comparison",         fig_baseline),
        ("Fig 3: Scalability",                 fig_scalability),
        ("Fig 4: Robustness",                  fig_robustness),
        ("Fig 5: Confidence Distributions",    fig_confidence),
        ("Fig 6: Confusion Matrices",          fig_confusion_matrices),
        ("Fig 7: Cross-Validation CI",         fig_cross_validation),
        ("Fig 8: Enterprise Pipeline",         fig_enterprise),
        ("Fig 9: Security Validation",         fig_security),
    ]

    success = 0
    for name, fn in generators:
        log.info(f"\n{name}")
        try:
            fn()
            success += 1
        except Exception as e:
            log.error(f"  FAILED: {e}", exc_info=True)

    log.info(f"\n{'='*70}")
    log.info(f"Generated {success}/{len(generators)} figures → {FIGURES_DIR}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
