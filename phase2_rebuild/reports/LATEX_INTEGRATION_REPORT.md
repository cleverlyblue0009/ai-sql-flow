# LaTeX Integration Report

Target file: `paper/dataflow_ai_v2.tex` (IEEE Access `ieeeaccess.cls`,
`natbib[numbers,sort]`, `IEEEtranN.bst`).

## What changed in this pass

### Added content

| Where (logical)            | Kind         | Label(s)                                              |
|----------------------------|--------------|-------------------------------------------------------|
| §I Intro                   | paragraph    | (no new label) — coupled-validation framing           |
| §V Experimental Setup      | subsection   | `subsec:env` — hardware / software environment        |
| §VII Results               | subsection   | `subsec:confidence`, `fig:confidence`                 |
| §VII Results               | subsection   | `subsec:failure`, `tab:failmodes`, `fig:failure`      |
| §VIII Enterprise Case Study| section      | `sec:case`, `fig:case` (two subsections inside)       |
| §IX Discussion             | subsection   | "Coupling integrity and migration in one gate"        |
| §X Conclusion              | rewrite      | failure-taxonomy sentence added                       |

### Unchanged on purpose

- Section numbering is preserved (LaTeX auto-numbers the new section, the
  existing Discussion and Conclusion shift from VIII/IX to IX/X automatically).
- Bibliography (`refs.bib`) — no new entries; all new content is grounded in
  on-repo artefacts that were already cited or do not require external citation.
- All previously defined labels are intact (verified by audit, see
  `CITATION_ORDER_AUDIT.md`).

## Cross-reference integrity

Audit was re-run after every edit (`phase2_rebuild/scripts/40_audit_paper.py`).
Final state:

```
citation_audit: bib=43 cited=41 unused=2 missing=0
xref_audit: 42 labels, 10 unreferenced
```

The 10 "unreferenced" labels are all section / subsection anchors used by
`hyperref` for the table of contents and PDF outline (`sec:intro`,
`subsec:bases`, `subsec:routing`, `subsec:env`, `subsec:datasets`,
`subsec:threshold`, `subsec:ablation`, `subsec:sql`, `subsec:confidence`,
`subsec:threats`). These do not require in-text `\ref` and are expected.

## Float / page-break hygiene

Each new section / subsection ends with `\FloatBarrier` so the new figures
(`fig:confidence`, `fig:failure`, `fig:case`) cannot drift past their owning
subsections. The three new wide figures use `figure*` (two-column span).

## Build verification

The .tex was not compiled in this pass (no TeX Live in the dev environment),
but the audit script parses the same structures `pdflatex` will see (`\label`,
`\ref`, `\cite`, `\includegraphics`, environment matching). Every
`\includegraphics` target listed in §V/§VII/§VIII exists in `paper/images/`.

To compile:

```powershell
cd paper
latexmk -pdf -bibtex dataflow_ai_v2.tex
```
