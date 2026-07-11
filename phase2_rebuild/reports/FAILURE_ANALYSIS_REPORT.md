# Failure Analysis Report

Source data: `phase2_rebuild/results/tables/sql_migration_per_query.csv`
(575 source–target pairs). 115 rows fail the strict AST-footprint check.
Classification done by `phase2_rebuild/scripts/23_failure_confidence_case.py
::classify(row)`.

## Cause distribution

| Cause                          | Pairs | Share | Operationally |
|--------------------------------|------:|------:|---------------|
| Decorator / footprint drift    |   62  |  54%  | Auto-promote with normaliser |
| Dialect-specific construct     |   24  |  21%  | Manual review |
| Function semantics             |   15  |  13%  | Manual review |
| DML / DDL extension            |    9  |   8%  | Manual review |
| Parse error                    |    5  |   4%  | Hard reject at ingestion |
| **Total**                      |  115  | 100%  |               |

## Heuristics

The `classify(row)` heuristic inspects each pair's `error` field plus the
source SQL and assigns to exactly one bucket:

- **Parse error** — `error` contains `ParseError` (5 pairs, all PostgreSQL
  `LISTEN/NOTIFY` and similar non-standard extensions).
- **DML / DDL extension** — source contains `INSERT IGNORE`, `CREATE STREAM`,
  `PIVOT`, or `MERGE` and the target dialect lacks an equivalent.
- **Function semantics** — source contains `DATE_FORMAT`, `TRY_CONVERT`,
  `FORMAT`, or `DATEDIFF` and the AST diff is concentrated in argument order.
- **Dialect-specific construct** — source contains `LATERAL`, `QUALIFY`,
  `OVER PARTITION`, `generate_series`, or `jsonb_*`.
- **Decorator / footprint drift** — default bucket; the post-transpile AST
  has the same node types as the source but fewer tokens (precision
  annotations, identifier quoting, comments, etc. silently dropped).

## Top-10 fragile queries

Pulled from `failure_analysis.csv` by counting how many of the 5 target
dialects each source query fails on. Top of the list (full ranking in
Fig. 10b in the paper):

| Source query              | Source dialect | Failing targets (out of 5) |
|---------------------------|---------------|---------------------------:|
| `lateral_join`            | postgres      | 4 |
| `qualify_window`          | snowflake     | 4 |
| `pivot_quarter`           | tsql          | 3 |
| `try_convert_decimal`     | tsql          | 3 |
| `insert_on_conflict`      | postgres      | 3 |
| `merge_using`             | oracle        | 3 |
| `jsonb_path_exists`       | postgres      | 3 |
| `listen_notify`           | postgres      | 3 |
| `date_format_iso`         | mysql         | 2 |
| `copy_grants_create`      | snowflake     | 2 |

## Practitioner takeaway (paraphrased from §VII-J of the paper)

The 80% headline AST-equivalence rate partitions into three actionable buckets:

1. **Auto-promotable** (~54%): cosmetic decorator drift. A small library of
   ~12 normalisation rules over the AST would reclaim these.
2. **Reviewable** (~42%): genuinely lossy translations; need a human or a
   schema-aware row-equivalence runner against representative seed data.
3. **Hard-reject** (~4%): parser doesn't accept the input. Should fail at
   ingestion with a clear error rather than be quietly routed through.

## Artefacts

- `phase2_rebuild/results/tables/failure_analysis.csv` — 115 rows: `query`,
  `src_dialect`, `tgt_dialect`, `difficulty`, `cause`, `error`.
- `paper/images/fig9_failure_analysis.pdf` — two-panel figure: cause taxonomy
  + top-10 fragile sources.
- Paper §VII-J `subsec:failure`, Table `tab:failmodes`.
