"""SQL migration experiments using sqlglot.

For every query in test_data/sql/query_catalog.json:
  - parse in its source dialect
  - transpile to every other supported target dialect
  - measure: parse_success, transpile_success, ast_roundtrip_equivalence, latency
  - aggregate by source x target, by complexity, by difficulty.

Outputs (under phase2_rebuild/results/):
  tables/sql_migration_matrix.csv     (per source x target aggregates)
  tables/sql_migration_per_query.csv  (raw per-query results)
  tables/sql_migration_by_difficulty.csv
  tables/sql_migration_by_complexity.csv
  tables/sql_migration_summary.csv    (overall headline numbers)

Determinism: pure functional; no RNG.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd
import sqlglot
from sqlglot import exp

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
CATALOG = WORKSPACE / "test_data" / "sql" / "query_catalog.json"
OUT_TABLES = ROOT / "results" / "tables"
OUT_TABLES.mkdir(parents=True, exist_ok=True)

DIALECTS = ["postgres", "mysql", "tsql", "oracle", "snowflake"]
# Mapping from catalog folder names to sqlglot dialect identifiers
SRC_MAP = {
    "postgresql": "postgres",
    "mysql": "mysql",
    "sqlserver": "tsql",
    "oracle": "oracle",
    "snowflake": "snowflake",
}


def _normalize_ast(sql: str, dialect: str) -> str:
    """Parse and re-emit with normalization, for AST equivalence checks."""
    tree = sqlglot.parse_one(sql, read=dialect)
    return tree.sql(dialect=dialect, normalize=True, comments=False)


def _try_transpile(sql: str, src: str, tgt: str) -> tuple[bool, bool, bool, float, str]:
    """Return (parse_ok, transpile_ok, roundtrip_equiv, latency_ms, err)."""
    t0 = time.perf_counter()
    # Parse stage
    try:
        tree = sqlglot.parse_one(sql, read=src)
        parse_ok = True
    except Exception as e:
        return (False, False, False, (time.perf_counter() - t0) * 1000, f"parse:{type(e).__name__}")
    if src == tgt:
        # Identity transpile: success if AST re-emits cleanly
        try:
            out = tree.sql(dialect=tgt)
            equiv = _normalize_ast(out, tgt) == _normalize_ast(sql, src)
            return (True, True, equiv, (time.perf_counter() - t0) * 1000, "")
        except Exception as e:
            return (True, False, False, (time.perf_counter() - t0) * 1000, f"emit:{type(e).__name__}")
    # Cross-dialect transpile
    try:
        out = tree.sql(dialect=tgt)
        transpile_ok = True
    except Exception as e:
        return (True, False, False, (time.perf_counter() - t0) * 1000, f"transpile:{type(e).__name__}")
    # AST equivalence: re-parse the translated query in the target dialect and
    # compare its AST footprint (table/column/expression nodes) to source.
    try:
        tree2 = sqlglot.parse_one(out, read=tgt)
        equiv = _ast_footprint(tree) == _ast_footprint(tree2)
    except Exception:
        equiv = False
    return (True, transpile_ok, equiv, (time.perf_counter() - t0) * 1000, "")


def _ast_footprint(tree: exp.Expression) -> tuple:
    """Compute a dialect-agnostic structural footprint for AST equivalence.

    Counts node types and references to tables/columns; ignores literal
    formatting differences across dialects.
    """
    counts: dict[str, int] = {}
    tables: set[str] = set()
    columns: set[str] = set()
    for node in tree.walk():
        n = node[0] if isinstance(node, tuple) else node
        if not isinstance(n, exp.Expression):
            continue
        k = type(n).__name__
        counts[k] = counts.get(k, 0) + 1
        if isinstance(n, exp.Table):
            tables.add(n.name.lower() if n.name else "")
        elif isinstance(n, exp.Column):
            columns.add(n.name.lower() if n.name else "")
    return (tuple(sorted(counts.items())), tuple(sorted(tables)), tuple(sorted(columns)))


def main() -> int:
    print(f"Loading catalog: {CATALOG}")
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    rows = []
    for src_folder, levels in catalog.items():
        src_dialect = SRC_MAP.get(src_folder)
        if not src_dialect:
            continue
        for level, queries in levels.items():
            for q in queries:
                sql = q["sql"]
                name = q["name"]
                complexity = q.get("complexity", 0)
                difficulty = q.get("difficulty", "unknown")
                for tgt in DIALECTS:
                    parse_ok, trans_ok, equiv, lat_ms, err = _try_transpile(sql, src_dialect, tgt)
                    rows.append({
                        "query": name,
                        "src_folder": src_folder,
                        "src_dialect": src_dialect,
                        "tgt_dialect": tgt,
                        "level": level,
                        "complexity": complexity,
                        "difficulty": difficulty,
                        "parse_ok": parse_ok,
                        "transpile_ok": trans_ok,
                        "ast_equiv": equiv,
                        "latency_ms": round(lat_ms, 3),
                        "error": err,
                    })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_TABLES / "sql_migration_per_query.csv", index=False)

    # Source x target matrix (transpile success rate, AST equivalence rate)
    pivot_trans = (df.groupby(["src_dialect", "tgt_dialect"])["transpile_ok"]
                     .mean().reset_index(name="transpile_rate"))
    pivot_equiv = (df.groupby(["src_dialect", "tgt_dialect"])["ast_equiv"]
                     .mean().reset_index(name="ast_equiv_rate"))
    pivot_lat = (df.groupby(["src_dialect", "tgt_dialect"])["latency_ms"]
                   .mean().reset_index(name="latency_ms_mean"))
    matrix = pivot_trans.merge(pivot_equiv, on=["src_dialect", "tgt_dialect"]).merge(
        pivot_lat, on=["src_dialect", "tgt_dialect"]
    )
    matrix.to_csv(OUT_TABLES / "sql_migration_matrix.csv", index=False)

    by_diff = (df.groupby(["difficulty"])
                 .agg(n=("query", "size"),
                      parse_rate=("parse_ok", "mean"),
                      transpile_rate=("transpile_ok", "mean"),
                      ast_equiv_rate=("ast_equiv", "mean"),
                      latency_ms_mean=("latency_ms", "mean"))
                 .reset_index())
    by_diff.to_csv(OUT_TABLES / "sql_migration_by_difficulty.csv", index=False)

    # Complexity buckets
    bins = [0, 20, 40, 60, 80, 100, 1000]
    labels = ["[0-20]", "[20-40]", "[40-60]", "[60-80]", "[80-100]", "[100+]"]
    df["complexity_bucket"] = pd.cut(df["complexity"], bins=bins, labels=labels, include_lowest=True)
    by_cx = (df.groupby(["complexity_bucket"], observed=True)
               .agg(n=("query", "size"),
                    parse_rate=("parse_ok", "mean"),
                    transpile_rate=("transpile_ok", "mean"),
                    ast_equiv_rate=("ast_equiv", "mean"),
                    latency_ms_mean=("latency_ms", "mean"))
               .reset_index())
    by_cx.to_csv(OUT_TABLES / "sql_migration_by_complexity.csv", index=False)

    overall = pd.DataFrame([{
        "n_queries": df["query"].nunique(),
        "n_pairs": len(df),
        "parse_rate": df["parse_ok"].mean(),
        "transpile_rate": df["transpile_ok"].mean(),
        "ast_equiv_rate": df["ast_equiv"].mean(),
        "latency_ms_mean": df["latency_ms"].mean(),
        "latency_ms_p95": df["latency_ms"].quantile(0.95),
    }])
    overall.to_csv(OUT_TABLES / "sql_migration_summary.csv", index=False)

    print(f"\nQueries:        {df['query'].nunique()}")
    print(f"Source-target pairs: {len(df)}")
    print(f"Parse success:  {df['parse_ok'].mean():.3f}")
    print(f"Transpile rate: {df['transpile_ok'].mean():.3f}")
    print(f"AST equivalence:{df['ast_equiv'].mean():.3f}")
    print(f"Mean latency:   {df['latency_ms'].mean():.2f} ms")
    print(f"P95 latency:    {df['latency_ms'].quantile(0.95):.2f} ms")

    # Tripwire
    for col in ("parse_ok", "transpile_ok", "ast_equiv"):
        if df[col].mean() >= 0.99:
            print(f"\n[TRIPWIRE] {col} mean = {df[col].mean():.4f} >= 0.99")

    print("\nSrc x Tgt transpile rate:")
    print(matrix.pivot(index="src_dialect", columns="tgt_dialect",
                      values="transpile_rate").round(3))
    print("\nSrc x Tgt AST-equiv rate:")
    print(matrix.pivot(index="src_dialect", columns="tgt_dialect",
                      values="ast_equiv_rate").round(3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
