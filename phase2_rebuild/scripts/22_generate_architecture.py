"""Render Figure 1 (the DataFlow AI architecture diagram) as a standalone image.

Output: paper/images/fig1_architecture.{pdf,png}

Mirrors the TikZ figure embedded in dataflow_ai_v2.tex but produced via matplotlib
so it can be viewed/edited without a LaTeX toolchain.
"""
from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.patheffects import withStroke

OUT = Path(__file__).resolve().parents[1].parent / "paper" / "images"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.bbox": "tight",
    "savefig.dpi": 300,
})

# ---------- Layout (data coordinates) ----------------------------------------
fig, ax = plt.subplots(figsize=(18, 10))
ax.set_xlim(0, 100)
ax.set_ylim(0, 60)
ax.set_aspect("equal")
ax.axis("off")

# Color palette (matches TikZ)
C_SRC   = "#dceefc"   # blue!8
C_PROC  = "#fde6cc"   # orange!12
C_DET   = "#daf0d4"   # green!10
C_STACK = "#fff2b8"   # yellow!20
C_SQL   = "#fbd9d9"   # red!10
C_SINK  = "#e8e8e8"   # gray!15
EDGE    = "#454545"
TXT     = "#1a1a1a"

def box(x, y, w, h, color, text, fontsize=12, bold=False, lw=1.2):
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle="round,pad=0.02,rounding_size=0.5",
                          linewidth=lw, edgecolor=EDGE, facecolor=color, zorder=3)
    ax.add_patch(rect)
    ax.text(x, y, text, ha="center", va="center",
            fontsize=fontsize, color=TXT, zorder=4,
            fontweight=("bold" if bold else "normal"))
    return (x, y, w, h)

def arrow(p1, p2, lw=1.4, color=EDGE, style="-|>"):
    a = FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=14,
                        linewidth=lw, color=color, zorder=2,
                        shrinkA=2, shrinkB=2)
    ax.add_patch(a)

def edge_right(b1, b2, **kw):
    """Arrow from right edge of b1 to left edge of b2."""
    x1, y1, w1, h1 = b1
    x2, y2, w2, h2 = b2
    arrow((x1 + w1/2, y1), (x2 - w2/2, y2), **kw)

# ---------- Panel A: anomaly pipeline ----------------------------------------
# Group A background
ax.add_patch(Rectangle((1.5, 14), 86, 42, fill=False, linestyle=(0, (6, 4)),
                       edgecolor="#888", linewidth=1.0, zorder=1))
ax.text(2.5, 55.0, "(A) Anomaly detection & routing",
        fontsize=14, fontweight="bold", color="#333", zorder=5)

# Inputs (left column)
d1 = box( 9, 47, 13, 5, C_SRC, "SEC EDGAR\n(D1: 50.5k rows)", fontsize=11)
d2 = box( 9, 39, 13, 5, C_SRC, "NYC Payroll FY24\n(D2: 202k rows)", fontsize=11)
d3 = box( 9, 31, 13, 5, C_SRC, "UCI Credit Default\n(D3: 30k rows)", fontsize=11)

# Processing
extract = box(28, 39, 15, 5, C_PROC, "Extract & Sample\n(deterministic)",       fontsize=11)
inject  = box(46, 39, 15, 5, C_PROC, "Anomaly Injection\n(15 families, 5%)",    fontsize=11)
feat    = box(64, 39, 15, 5, C_PROC, "Feature Engineering\n(robust-z, dedup, rules)", fontsize=10.5)

# Detectors
rule = box(86, 47, 10.5, 4.2, C_DET, "Rule",             fontsize=11)
stat = box(86, 41, 10.5, 4.2, C_DET, "Robust Stat",      fontsize=11)
iso  = box(86, 35, 10.5, 4.2, C_DET, "Isolation Forest", fontsize=10.5)
lof  = box(86, 29, 10.5, 4.2, C_DET, "LOF",              fontsize=11)

# Inputs -> Extract
arrow((d1[0]+d1[2]/2,  d1[1]),  (extract[0]-extract[2]/2, extract[1]+1.5))
arrow((d2[0]+d2[2]/2,  d2[1]),  (extract[0]-extract[2]/2, extract[1]))
arrow((d3[0]+d3[2]/2,  d3[1]),  (extract[0]-extract[2]/2, extract[1]-1.5))

# Pipeline arrows
edge_right(extract, inject)
edge_right(inject, feat)

# feat -> detectors (fan out)
for det in (rule, stat, iso, lof):
    arrow((feat[0]+feat[2]/2, feat[1]), (det[0]-det[2]/2, det[1]))

# ---- Stacker + routing (below detectors, in lower-right of Panel A) ----
stacker = box(46, 22, 22, 6, C_STACK,
              "Logistic-regression stacker\n(5-fold OOF)",
              fontsize=12, bold=True, lw=2.0)
audit  = box(83, 25, 15, 4.5, C_SINK, "Audit / Quarantine", fontsize=11)
clean  = box(83, 19, 15, 4.5, C_SINK, "Cleansed dataset",   fontsize=11)

# Detectors -> stacker
for det in (rule, stat, iso, lof):
    arrow((det[0]-det[2]/2, det[1]), (stacker[0]+stacker[2]/2, stacker[1]+(det[1]-38)/8))

# stacker -> audit / clean (thick) with labels
arr_top = FancyArrowPatch((stacker[0]+stacker[2]/2, stacker[1]+1.4),
                          (audit[0]-audit[2]/2, audit[1]),
                          arrowstyle="-|>", mutation_scale=18, linewidth=2.2,
                          color="#111", zorder=2)
arr_bot = FancyArrowPatch((stacker[0]+stacker[2]/2, stacker[1]-1.4),
                          (clean[0]-clean[2]/2, clean[1]),
                          arrowstyle="-|>", mutation_scale=18, linewidth=2.2,
                          color="#111", zorder=2)
ax.add_patch(arr_top); ax.add_patch(arr_bot)
ax.text(65, 25.0, r"$s \geq \tau$", fontsize=13, color="#111", ha="center",
        path_effects=[withStroke(linewidth=3, foreground="white")])
ax.text(65, 19.0, r"$s < \tau$",    fontsize=13, color="#111", ha="center",
        path_effects=[withStroke(linewidth=3, foreground="white")])

# ---------- Panel B: SQL pipeline --------------------------------------------
ax.add_patch(Rectangle((1.5, 2), 96, 9.5, fill=False, linestyle=(0, (6, 4)),
                       edgecolor="#888", linewidth=1.0, zorder=1))
ax.text(2.5, 10.5, "(B) Cross-dialect SQL migration",
        fontsize=14, fontweight="bold", color="#333", zorder=5)

sql_in = box(12, 6.0, 18, 5, C_SRC, "SQL Corpus\n(109 queries, 5 dialects)", fontsize=11)
parse  = box(34, 6.0, 16, 5, C_SQL, "Parse (sqlglot,\nsource dialect)",      fontsize=11)
trans  = box(54, 6.0, 16, 5, C_SQL, "Cross-dialect\ntranspile",              fontsize=11)
astchk = box(74, 6.0, 16, 5, C_SQL, "AST footprint\nequivalence",            fontsize=11)
sqlout = box(93, 6.0, 11, 5, C_SINK, "Validated\ntarget SQL",                fontsize=10.5)

edge_right(sql_in, parse)
edge_right(parse, trans)
edge_right(trans, astchk)
edge_right(astchk, sqlout)

# ---------- Title ------------------------------------------------------------
ax.text(50, 58.5, "DataFlow AI — End-to-End Architecture",
        ha="center", va="center", fontsize=18, fontweight="bold")

# Save
fig.savefig(OUT / "fig1_architecture.pdf")
fig.savefig(OUT / "fig1_architecture.png", dpi=300)
plt.close(fig)
print(f"Wrote {OUT / 'fig1_architecture.pdf'}")
print(f"Wrote {OUT / 'fig1_architecture.png'}")
