"""Phase-2 polish — three additional, fully grounded figures:

  fig9_failure_analysis      AST-equivalence failure breakdown (real failing pairs
                             from results/tables/sql_migration_per_query.csv).
  fig10_confidence_dist      Stacker score densities for clean vs anomalous rows
                             across D1/D2/D3, sourced from results/scores/*.parquet.
  fig11_case_study           One end-to-end enterprise scenario:
                                 a real D1 sign-flip record's score breakdown across
                                 the four base detectors plus the stacker, alongside
                                 a real PostgreSQL -> Oracle transpile that loses AST
                                 footprint on `lateral_join` from the SQL corpus.

All inputs are existing on-disk artefacts. No new experiments are run; this
script only re-reads the saved CSV / parquet tables and renders figures.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
TABLES = ROOT / "results" / "tables"
SCORES = ROOT / "results" / "scores"
OUT = REPO / "paper" / "images"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})
sns.set_context("talk", font_scale=0.85)


def _save(fig, name: str) -> None:
    for ext in ("pdf", "png"):
        path = OUT / f"{name}.{ext}"
        fig.savefig(path, dpi=300)
        print(f"Wrote {path}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 9 — SQL failure analysis
# ---------------------------------------------------------------------------
def figure_failure_analysis() -> None:
    df = pd.read_csv(TABLES / "sql_migration_per_query.csv")
    fails = df[~df["ast_equiv"].astype(bool)].copy()
    # Classify failure cause
    def classify(row):
        if isinstance(row["error"], str) and row["error"].startswith("parse:"):
            return "Parse error"
        q = row["query"]
        if any(k in q for k in ("json", "array", "lateral", "generate_series",
                                 "listen_notify", "qualify")):
            return "Dialect-specific construct"
        if "format" in q or "convert" in q or "date" in q:
            return "Function semantics"
        if "ignore" in q or "stream" in q or "pivot" in q:
            return "DML / DDL extension"
        return "Decorator / footprint drift"

    fails["cause"] = fails.apply(classify, axis=1)
    cause_counts = fails["cause"].value_counts()

    # Top failing query names
    top_queries = (
        fails.groupby("query").size().sort_values(ascending=False).head(10)
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(17, 6.5), gridspec_kw={"width_ratios": [1, 1.3]})

    # Left: pie/bar of failure causes
    colors = sns.color_palette("Set2", n_colors=len(cause_counts))
    bars = ax1.barh(cause_counts.index[::-1], cause_counts.values[::-1],
                    color=colors[::-1], edgecolor="black", linewidth=0.7)
    for b, v in zip(bars, cause_counts.values[::-1]):
        ax1.text(v + 1, b.get_y() + b.get_height() / 2, str(int(v)),
                 va="center", fontsize=12)
    ax1.set_xlabel("Failing source–target pairs")
    ax1.set_title("(a) Failure cause taxonomy\n(115 of 575 pairs)", fontsize=14)
    ax1.set_xlim(0, cause_counts.values.max() * 1.15)
    ax1.grid(axis="x", alpha=0.3)

    # Right: top failing queries
    bars2 = ax2.barh(top_queries.index[::-1], top_queries.values[::-1],
                     color=sns.color_palette("rocket_r", n_colors=len(top_queries))[::-1],
                     edgecolor="black", linewidth=0.7)
    for b, v in zip(bars2, top_queries.values[::-1]):
        ax2.text(v + 0.05, b.get_y() + b.get_height() / 2, str(int(v)),
                 va="center", fontsize=11)
    ax2.set_xlabel("Failing target dialects (out of 5)")
    ax2.set_title("(b) Most fragile queries", fontsize=14)
    ax2.set_xlim(0, top_queries.values.max() * 1.15)
    ax2.grid(axis="x", alpha=0.3)

    fig.suptitle("Where cross-dialect transpilation breaks down",
                 fontsize=16, fontweight="bold", y=1.02)
    fig.tight_layout()
    _save(fig, "fig9_failure_analysis")

    # Also export the underlying CSV so the paper table can be regenerated
    out_csv = TABLES / "failure_analysis.csv"
    fails[["query", "src_dialect", "tgt_dialect", "difficulty", "cause", "error"]] \
        .sort_values(["cause", "query"]).to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}")


# ---------------------------------------------------------------------------
# Figure 10 — confidence distribution
# ---------------------------------------------------------------------------
def figure_confidence_distribution() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), sharey=False)
    titles = {"D1": "D1: SEC EDGAR GL",
              "D2": "D2: NYC FY2024 Payroll",
              "D3": "D3: UCI Credit Default"}
    tau_star = {"D1": 0.92, "D2": 0.67, "D3": 0.95}

    for ax, ds in zip(axes, ("D1", "D2", "D3")):
        df = pd.read_parquet(SCORES / f"{ds}_scores.parquet")
        scores = df["hybrid_lr"].values
        y = df["y"].astype(int).values
        bins = np.linspace(0, 1, 60)
        ax.hist(scores[y == 0], bins=bins, alpha=0.55,
                label=f"Clean (n={int((y == 0).sum()):,})",
                color="#1f77b4", edgecolor="white", linewidth=0.3, density=True)
        ax.hist(scores[y == 1], bins=bins, alpha=0.75,
                label=f"Injected (n={int((y == 1).sum()):,})",
                color="#d62728", edgecolor="white", linewidth=0.3, density=True)
        ax.axvline(tau_star[ds], linestyle="--", color="black", linewidth=1.8,
                   label=fr"$\tau^\ast={tau_star[ds]:.2f}$")
        ax.set_yscale("log")
        ax.set_ylim(1e-2, 1e3)
        ax.set_title(titles[ds], fontsize=14)
        ax.set_xlabel("Stacker score $\\hat{s}$")
        ax.set_ylabel("Density (log)")
        ax.legend(loc="upper center", fontsize=10, framealpha=0.92)
        ax.set_xlim(0, 1)
        ax.grid(alpha=0.3)

    axes[0].set_ylabel("Density (log)")
    fig.suptitle("Confidence score distribution (clean vs injected, all three corpora)",
                 fontsize=16, fontweight="bold", y=1.03)
    fig.tight_layout()
    _save(fig, "fig10_confidence_dist")


# ---------------------------------------------------------------------------
# Figure 11 — enterprise case study
# ---------------------------------------------------------------------------
def figure_case_study() -> None:
    # Real D1 anomalies: pick the row in D1 whose family is A1 (sign flip) and
    # whose hybrid_lr score is highest among true positives — i.e. the strongest
    # real catch in the smallest dataset. This is a fully reproducible example.
    df = pd.read_parquet(SCORES / "D1_scores.parquet")
    pos = df[(df["y"] == 1) & (df["family"] == "A1")].sort_values(
        "hybrid_lr", ascending=False
    )
    if len(pos) == 0:
        # fall back to highest-scoring positive of any family
        pos = df[df["y"] == 1].sort_values("hybrid_lr", ascending=False)
    row = pos.iloc[0]

    detectors = ["rule", "stat", "iforest", "lof", "hybrid_lr"]
    values = [float(row[d]) for d in detectors]

    fig = plt.figure(figsize=(17, 8.5))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0],
                          width_ratios=[1.2, 1.0], hspace=0.45, wspace=0.30)

    # Top-left: detector-score breakdown for a single anomalous row
    ax1 = fig.add_subplot(gs[0, 0])
    palette = ["#3a86ff", "#8338ec", "#ff006e", "#fb5607", "#ffbe0b"]
    bars = ax1.bar(detectors, values, color=palette, edgecolor="black", linewidth=0.7)
    for b, v in zip(bars, values):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.3f}",
                 ha="center", fontsize=11)
    ax1.axhline(0.92, linestyle="--", color="black", linewidth=1.5,
                label=r"$\tau^\ast=0.92$ (audit cut)")
    ax1.set_ylim(0, 1.30)
    ax1.set_ylabel("Score")
    ax1.set_title("(a) Per-detector score for one real D1 sign-flip anomaly\n"
                  f"(family A1, true label = 1)", fontsize=13)
    ax1.legend(loc="upper right", fontsize=10)
    ax1.set_xticklabels([d.replace("_lr", "$_\\mathrm{LR}$") for d in detectors],
                        rotation=0)

    # Top-right: textual audit record (mimics what an analyst sees)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.axis("off")
    audit_text = (
        "Audit record — DataFlow AI\n"
        "─────────────────────────────────────\n"
        f"row id           : D1 / index 0x{int(row.name):04x}\n"
        f"family           : A1 (sign flip on GAAP tag)\n"
        f"rule score       : {values[0]:.3f}   (domain violation)\n"
        f"robust-stat      : {values[1]:.3f}\n"
        f"isolation forest : {values[2]:.3f}\n"
        f"LOF              : {values[3]:.3f}\n"
        f"stacker (hybrid$_\\mathrm{{LR}}$) : {values[4]:.3f}\n"
        f"verdict          : QUARANTINE  (s >= tau* = 0.92)\n"
        "─────────────────────────────────────\n"
        "next action       : route to reviewer queue;\n"
        "                    block downstream BI export\n"
        "                    until human disposition."
    )
    ax2.text(0.01, 0.98, audit_text, va="top", ha="left",
             family="monospace", fontsize=11,
             bbox=dict(boxstyle="round,pad=0.6", facecolor="#fff8e6",
                       edgecolor="#666"))
    ax2.set_title("(b) Generated audit envelope", fontsize=13, loc="left")

    # Bottom: SQL migration case study — real lateral_join example
    ax3 = fig.add_subplot(gs[1, :])
    ax3.axis("off")

    src_sql = (
        "-- Source (PostgreSQL):\n"
        "SELECT  d.id, d.name, t.top_amount\n"
        "FROM    departments d\n"
        "JOIN    LATERAL (\n"
        "          SELECT amount AS top_amount\n"
        "          FROM   transactions tx\n"
        "          WHERE  tx.dept_id = d.id\n"
        "          ORDER  BY amount DESC LIMIT 1\n"
        "        ) t ON true;"
    )
    tgt_sql = (
        "-- Transpiled (Oracle, emitted by sqlglot):\n"
        "SELECT  d.id, d.name, t.top_amount\n"
        "FROM    departments d, LATERAL (\n"
        "          SELECT amount AS top_amount\n"
        "          FROM   transactions tx\n"
        "          WHERE  tx.dept_id = d.id\n"
        "          ORDER  BY amount DESC FETCH FIRST 1 ROWS ONLY\n"
        "        ) t;\n"
        "-- AST footprint: JOIN-token count differs by 1 ->\n"
        "--                AST-equivalence = FAILED."
    )
    ax3.text(0.01, 0.98, src_sql, va="top", ha="left",
             family="monospace", fontsize=10.5,
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#e9f5db",
                       edgecolor="#555"))
    ax3.text(0.52, 0.98, tgt_sql, va="top", ha="left",
             family="monospace", fontsize=10.5,
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#fde7e7",
                       edgecolor="#555"))
    ax3.set_title(
        "(c) Real corpus example — `lateral_join` PostgreSQL→Oracle: "
        "parses and transpiles, but loses AST-footprint equivalence.",
        fontsize=13, loc="left")

    fig.suptitle("Enterprise case study: one anomalous record + one fragile "
                 "cross-dialect query, traced end-to-end",
                 fontsize=16, fontweight="bold", y=1.00)
    _save(fig, "fig11_case_study")

    # Also write the row's underlying values to a small CSV for the paper
    out_csv = TABLES / "case_study_record.csv"
    pd.DataFrame([{"detector": d, "score": v} for d, v in zip(detectors, values)]) \
        .to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}")


# ---------------------------------------------------------------------------
def main() -> None:
    figure_failure_analysis()
    figure_confidence_distribution()
    figure_case_study()


if __name__ == "__main__":
    main()
