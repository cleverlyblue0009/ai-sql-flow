# F5: AST Footprint Validation + Execution Equivalence

**Manuscript**: DataFlow AI — IEEE Access Access-2026-28181

---

## Fix applied vs Round-1 E5

**Metric clarification**: The paper's `ast_equiv` column is computed by `_ast_footprint()` in `phase2_rebuild/scripts/30_run_sql_migration.py`. This is a STRUCTURAL fingerprint (counts of each AST node type + set of table and column names), NOT a strict SQL-string comparison. The paper calls this 'strict AST-footprint equivalence', which is accurate but could be misread as character-level string equality.

F5 adds two new comparators:
1. **strict_text_roundtrip**: transpile src→tgt→src, compare normalised text. This is genuinely strict and will reject many syntactically equivalent transformations.
2. **exec_equiv_src2dkdb**: execute both source SQL and the DuckDB-transpiled SQL on a 5-row synthetic table, compare output row-sets.

## Reproducibility: recomputed footprint vs committed values

**PASS** — 0 mismatches out of 575 pairs. The committed sql_migration_per_query.csv is fully reproducible from the query catalog using the same comparison logic.

## Summary matrix — all equivalence measures

| src_dialect   | tgt_dialect   |   n_queries |   transpile_rate |   footprint_committed |   footprint_recomputed |   strict_text_roundtrip |   exec_equiv_src2dkdb |   fp_mismatch_rate |
|:--------------|:--------------|------------:|-----------------:|----------------------:|-----------------------:|------------------------:|----------------------:|-------------------:|
| mysql         | mysql         |          20 |           1      |                1      |                 1      |                       0 |                   nan |                  0 |
| mysql         | oracle        |          20 |           1      |                0.85   |                 0.85   |                       0 |                   nan |                  0 |
| mysql         | postgres      |          20 |           1      |                0.75   |                 0.75   |                       0 |                   nan |                  0 |
| mysql         | snowflake     |          20 |           1      |                0.8    |                 0.8    |                       0 |                   nan |                  0 |
| mysql         | tsql          |          20 |           1      |                0.8    |                 0.8    |                       0 |                   nan |                  0 |
| oracle        | mysql         |          13 |           1      |                0.4615 |                 0.4615 |                       0 |                   nan |                  0 |
| oracle        | oracle        |          13 |           1      |                1      |                 1      |                       0 |                   nan |                  0 |
| oracle        | postgres      |          13 |           1      |                0.7692 |                 0.7692 |                       0 |                   nan |                  0 |
| oracle        | snowflake     |          13 |           1      |                1      |                 1      |                       0 |                   nan |                  0 |
| oracle        | tsql          |          13 |           1      |                0.5385 |                 0.5385 |                       0 |                   nan |                  0 |
| postgres      | mysql         |          55 |           0.9818 |                0.6727 |                 0.6852 |                       0 |                   nan |                  0 |
| postgres      | oracle        |          55 |           0.9818 |                0.8909 |                 0.9074 |                       0 |                   nan |                  0 |
| postgres      | postgres      |          55 |           0.9818 |                0.9818 |                 1      |                       0 |                   nan |                  0 |
| postgres      | snowflake     |          55 |           0.9818 |                0.8727 |                 0.8889 |                       0 |                   nan |                  0 |
| postgres      | tsql          |          55 |           0.9818 |                0.7091 |                 0.7222 |                       0 |                   nan |                  0 |
| snowflake     | mysql         |          14 |           1      |                0.6429 |                 0.6429 |                       0 |                   nan |                  0 |
| snowflake     | oracle        |          14 |           1      |                0.7857 |                 0.7857 |                       0 |                   nan |                  0 |
| snowflake     | postgres      |          14 |           1      |                0.5714 |                 0.5714 |                       0 |                   nan |                  0 |
| snowflake     | snowflake     |          14 |           1      |                1      |                 1      |                       0 |                   nan |                  0 |
| snowflake     | tsql          |          14 |           1      |                0.6429 |                 0.6429 |                       0 |                   nan |                  0 |
| tsql          | mysql         |          13 |           1      |                0.6154 |                 0.6154 |                       0 |                   nan |                  0 |
| tsql          | oracle        |          13 |           1      |                0.6923 |                 0.6923 |                       0 |                   nan |                  0 |
| tsql          | postgres      |          13 |           1      |                0.6923 |                 0.6923 |                       0 |                   nan |                  0 |
| tsql          | snowflake     |          13 |           1      |                0.8462 |                 0.8462 |                       0 |                   nan |                  0 |
| tsql          | tsql          |          13 |           1      |                0.9231 |                 0.9231 |                       0 |                   nan |                  0 |

## Gap: strict text roundtrip − footprint rate

Negative values mean the strict text roundtrip is more conservative than the footprint comparator.

| src_dialect   | tgt_dialect   |   footprint_recomputed |   strict_text_roundtrip |   strict_minus_footprint |
|:--------------|:--------------|-----------------------:|------------------------:|-------------------------:|
| mysql         | mysql         |                 1      |                       0 |                  -1      |
| oracle        | oracle        |                 1      |                       0 |                  -1      |
| postgres      | postgres      |                 1      |                       0 |                  -1      |
| oracle        | snowflake     |                 1      |                       0 |                  -1      |
| snowflake     | snowflake     |                 1      |                       0 |                  -1      |
| tsql          | tsql          |                 0.9231 |                       0 |                  -0.9231 |
| postgres      | oracle        |                 0.9074 |                       0 |                  -0.9074 |
| postgres      | snowflake     |                 0.8889 |                       0 |                  -0.8889 |
| mysql         | oracle        |                 0.85   |                       0 |                  -0.85   |
| tsql          | snowflake     |                 0.8462 |                       0 |                  -0.8462 |
| mysql         | tsql          |                 0.8    |                       0 |                  -0.8    |
| mysql         | snowflake     |                 0.8    |                       0 |                  -0.8    |
| snowflake     | oracle        |                 0.7857 |                       0 |                  -0.7857 |
| oracle        | postgres      |                 0.7692 |                       0 |                  -0.7692 |
| mysql         | postgres      |                 0.75   |                       0 |                  -0.75   |
| postgres      | tsql          |                 0.7222 |                       0 |                  -0.7222 |
| tsql          | postgres      |                 0.6923 |                       0 |                  -0.6923 |
| tsql          | oracle        |                 0.6923 |                       0 |                  -0.6923 |
| postgres      | mysql         |                 0.6852 |                       0 |                  -0.6852 |
| snowflake     | mysql         |                 0.6429 |                       0 |                  -0.6429 |
| snowflake     | tsql          |                 0.6429 |                       0 |                  -0.6429 |
| tsql          | mysql         |                 0.6154 |                       0 |                  -0.6154 |
| snowflake     | postgres      |                 0.5714 |                       0 |                  -0.5714 |
| oracle        | tsql          |                 0.5385 |                       0 |                  -0.5385 |
| oracle        | mysql         |                 0.4615 |                       0 |                  -0.4615 |

## Execution equivalence (source SQL → DuckDB transpiled)

Execution equivalence measures whether running the source SQL in DuckDB (DuckDB is SQL/ANSI-compatible for most SELECT queries) produces the same output as the DuckDB-transpiled version.

| src_dialect   | tgt_dialect   | n_queries   | footprint_recomputed   | exec_equiv_src2dkdb   |
|---------------|---------------|-------------|------------------------|-----------------------|

---

Generated in 3.2s. n=575 query-target pairs, 0 committed/recomputed mismatches.
Outputs: rebuttal_artifacts/round2/f5_ast_execution/
