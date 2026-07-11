# Citation Order Audit

`natbib[numbers,sort]` is responsible for renumbering citations in order of
first appearance. The audit script verifies that every cited key resolves to
a `refs.bib` entry and reports any missing or unused entries.

## Final state

```
Bib entries:       43
Cited unique keys: 41
Unused in bib:     2   (loshin2010master, wieder2019impact)
Missing from bib:  0
```

- **0 missing**: every `\cite{...}` resolves to a valid bib key. The compiled
  PDF will not show any `?` placeholders.
- **2 unused**: held in `refs.bib` as reviewer-anticipated references
  (master-data management background, payroll-quality background). Acceptable
  for IEEE Access submission; can be removed on revision.
- **`sort` option**: numeric labels are reassigned by order of first
  appearance — no manual renumbering needed when new content is inserted.

## How the audit works

```python
# phase2_rebuild/scripts/40_audit_paper.py
cited = set(re.findall(r"\\cite[a-z]*\{([^}]+)\}", tex_source))
cited = {k.strip() for grp in cited for k in grp.split(",")}
bib_keys = set(re.findall(r"^@\w+\{\s*([^,]+),", bib_source, flags=re.M))
print("missing:", cited - bib_keys)
print("unused :", bib_keys - cited)
```

## Re-run command

```powershell
.\venv\Scripts\python.exe phase2_rebuild\scripts\40_audit_paper.py
```

Outputs land in `phase2_rebuild/results/audits/`:

- `citation_audit.txt` — bib counts and missing/unused lists
- `xref_audit.csv` — every `\label` and nearest `\ref`
- `metric_occurrences.csv` — every `\num{...}` literal
- `summary.md` — one-screen summary
