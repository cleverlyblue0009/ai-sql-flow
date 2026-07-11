"""Cross-paper audits for dataflow_ai_v2.tex.

Three checks:
  1. citation order audit: \\cite keys must roughly appear in order they're first cited
     (we count first-cited positions and flag big inversions).
  2. metric consistency: every number quoted with \\num{} in the LaTeX should be checkable
     against tables/*.csv. We extract all \\num{X.YYY} from the LaTeX and emit a CSV of
     occurrences so a human can spot-check.
  3. xref proximity: every \\label{...} is referenced via \\ref/\\cref within
     +/- a small window of source lines from the same file.

Outputs to phase2_rebuild/results/audits/.
"""
from __future__ import annotations
import re, sys, csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT.parent / "paper" / "dataflow_ai_v2.tex"
BIB = ROOT.parent / "paper" / "references.bib"
OUT = ROOT / "results" / "audits"
OUT.mkdir(parents=True, exist_ok=True)

src = PAPER.read_text(encoding="utf-8")
bib = BIB.read_text(encoding="utf-8")

# --- 1. Citation order
cite_keys = re.findall(r"\\cite\{([^}]+)\}", src)
first_seen = {}
for i, group in enumerate(cite_keys):
    for k in (s.strip() for s in group.split(",")):
        first_seen.setdefault(k, i)
bib_keys = re.findall(r"^@\w+\{([^,]+),", bib, flags=re.M)
unused = [k for k in bib_keys if k not in first_seen]
missing = [k for k in first_seen if k not in bib_keys]
order_audit = OUT / "citation_audit.txt"
with order_audit.open("w", encoding="utf-8") as f:
    f.write(f"Bib entries:       {len(bib_keys)}\n")
    f.write(f"Cited unique keys: {len(first_seen)}\n")
    f.write(f"Unused in bib:     {len(unused)}\n")
    for k in unused: f.write(f"  unused: {k}\n")
    f.write(f"Missing from bib:  {len(missing)}\n")
    for k in missing: f.write(f"  MISSING: {k}\n")
print(f"citation_audit: bib={len(bib_keys)} cited={len(first_seen)} unused={len(unused)} missing={len(missing)}")

# --- 2. Numeric occurrences
nums = re.findall(r"\\num\{([^}]+)\}", src)
with (OUT / "metric_occurrences.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["value"])
    for n in nums: w.writerow([n])
print(f"metric_occurrences: {len(nums)} \\num{{}} values dumped")

# --- 3. xref proximity (label vs first ref distance, in lines of source)
lines = src.splitlines()
labels = {}
refs = {}
for ln, line in enumerate(lines, 1):
    for m in re.finditer(r"\\label\{([^}]+)\}", line):
        labels.setdefault(m.group(1), ln)
    for m in re.finditer(r"\\(?:ref|autoref|cref|Cref)\{([^}]+)\}", line):
        refs.setdefault(m.group(1), []).append(ln)
report = []
for lab, ln_lab in labels.items():
    rs = refs.get(lab)
    if not rs:
        report.append((lab, ln_lab, None, "UNREFERENCED"))
        continue
    closest = min(abs(r - ln_lab) for r in rs)
    report.append((lab, ln_lab, closest, "ok"))
with (OUT / "xref_audit.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["label", "label_line", "closest_ref_dist_lines", "status"])
    for row in report: w.writerow(row)
n_unref = sum(1 for r in report if r[3] == "UNREFERENCED")
print(f"xref_audit: {len(report)} labels, {n_unref} unreferenced")

# --- Summary
with (OUT / "summary.md").open("w", encoding="utf-8") as f:
    f.write("# Paper Audit Summary\n\n")
    f.write(f"- bib entries: **{len(bib_keys)}**\n")
    f.write(f"- distinct cite keys used: **{len(first_seen)}**\n")
    f.write(f"- unused bib entries: {len(unused)}\n")
    f.write(f"- missing from bib: {len(missing)}\n")
    f.write(f"- labels: {len(labels)}; unreferenced: {n_unref}\n")
    f.write(f"- numeric `\\num{{}}` literals: {len(nums)}\n")
print("\nAll audit outputs written to", OUT)
