# Figure Generation Report

All figures are rendered with matplotlib 3.10.9 + seaborn 0.13.2 (no LaTeX
toolchain dependency) at 300 dpi to both `.pdf` and `.png` under `paper/images/`.

## Global rc

```python
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "pdf.fonttype": 42,
    "ps.fonttype":  42,
    "savefig.dpi":  300,
    "savefig.bbox": "tight",
})
sns.set_context("talk", font_scale=0.85)
```

## Figure inventory (paper order = LaTeX order, matches the PDF)

| LaTeX # | File                            | Generator script                          | Notes                                    |
|---------|---------------------------------|-------------------------------------------|------------------------------------------|
| 1       | `fig1_architecture.pdf`         | TikZ (inline) + `22_generate_architecture.py` | Panels A/B; TikZ also kept as fallback |
| 2       | `fig2_pr_curves.pdf`            | `21_generate_large_figures.py`            | PR per dataset, 4 curves each            |
| 3       | `fig6_perfamily.pdf`            | `21_generate_large_figures.py`            | Recall heatmap, families × detectors     |
| 4       | `fig4_threshold_sweep.pdf`      | `21_generate_large_figures.py`            | P/R/F1 vs τ with τ* marker               |
| 5       | `fig3_confmat.pdf`              | `21_generate_large_figures.py`            | Stacker confusion matrix per dataset     |
| 6       | `fig7_ablation.pdf`             | `21_generate_large_figures.py`            | Bar chart of F1 deltas vs full           |
| 7       | `fig5_scalability.pdf`          | `21_generate_large_figures.py`            | Wall-clock vs N (log–log)                |
| 8       | `fig8_sql_matrix.pdf`           | `21_generate_large_figures.py`            | Source × target AST-equiv heatmap        |
| 9       | `fig10_confidence_dist.pdf`     | `23_failure_confidence_case.py`           | Score density by label, log y, τ* line   |
| 10      | `fig9_failure_analysis.pdf`     | `23_failure_confidence_case.py`           | (a) cause taxonomy, (b) top-10 fragile   |
| 11      | `fig11_case_study.pdf`          | `23_failure_confidence_case.py`           | (a) detector bars, (b) envelope, (c) SQL |

(Note: filename indices ≠ in-paper figure numbers. LaTeX numbers figures by
order of `\begin{figure}` blocks in `dataflow_ai_v2.tex`; the file IDs are
historical generator labels and don't need to change.)

## Polish-pass changes

- **fig10** — Originally used `sharey=True`, which let D3's near-zero clean
  spike dominate; switched to `sharey=False` + `set_yscale("log")` with
  `ylim(1e-2, 1e3)` to reveal sub-decade detail in all three panels. τ* is
  drawn as a dashed vertical at each dataset's audit cut.
- **fig9** — Right-panel x-axis was initially "Failing target dialects (out of 4)";
  corrected to "out of 5" because each query has 5 possible targets
  including identity round-trip.
- **fig11** — Detector-bar panel ylim raised 1.15 → 1.30 and the legend
  moved to the upper-right so the `1.000` data label no longer overlaps
  the τ* legend entry.

## Determinism

No figure depends on a fresh RNG draw. All figures consume the same parquet /
CSV artefacts produced by `10_run_anomaly_experiments.py` and
`30_run_sql_migration.py` under `SEED=42`. Regenerating from a clean clone
yields byte-identical PDFs modulo matplotlib's embedded timestamp.
