# E6 Query Adaptation Protocol

## Method
36 adapted queries were written to run against the D2 (payroll) and D3 (credit)
DuckDB tables, preserving the structural complexity of the original 115-query corpus.

Each adapted query:
- Uses a `{table}` placeholder substituted with the dirty or clean table name.
- Reads at least one column that is the target of an anomaly injection family.
- Preserves the dialect-specific syntax of its source dialect (e.g., backtick
  identifiers for MySQL, square-bracket identifiers for T-SQL, QUALIFY clause for
  Snowflake, FETCH FIRST for Oracle).

## Distribution
- PostgreSQL: 6 queries (2 easy, 2 medium, 2 hard)
- MySQL: 7 queries (3 easy, 3 medium, 1 hard)
- SQL Server: 6 queries (2 easy, 2 medium, 2 hard)
- Oracle: 6 queries (2 easy, 2 medium, 2 hard)
- Snowflake: 6 queries (2 easy, 2 medium, 2 hard)

## Original corpus
The 115-query corpus in test_data/sql/query_catalog.json is NOT modified.

## DuckDB compatibility note
DuckDB natively supports PostgreSQL dialect. Queries from other dialects are
transpiled to PostgreSQL via sqlglot before execution. Transpilation failures
and execution errors are logged in e6_query_executions.json.
