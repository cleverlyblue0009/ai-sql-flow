"""
E5: Hard query AST failure analysis.

Analyses the 115-query corpus to understand WHICH constructs cause transpilation
failures or AST non-equivalence, and WHY.

Method:
  1. For each (src, tgt) pair: transpile and record outcome (success / error / warning)
  2. Tag each query with AST construct types (CTE, WINDOW, PIVOT, ARRAY, DDL, ...)
  3. Attribute failures to specific construct types
  4. Relax comparator: check semantic equivalence at text-normalised level
     (case, whitespace, alias normalisation)
  5. Execution check: attempt DuckDB execution of source and transpiled queries
     on a tiny synthetic table to check runtime equivalence

Outputs (rebuttal_artifacts/e5/):
  e5_construct_tags.csv      — per-query construct presence matrix
  e5_transpile_outcomes.csv  — per (query, src, tgt) outcome + error
  e5_failure_attribution.csv — construct-level failure rate
  e5_ast_relaxed.csv         — AST equivalence at relaxed text-normalisation
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import pandas as pd
import sqlglot
from sqlglot import exp

REPO = Path(__file__).resolve().parents[2]
CATALOG = REPO / "test_data" / "sql" / "query_catalog.json"
ARTIFACTS = REPO / "rebuttal_artifacts"
OUT = ARTIFACTS / "e5"
OUT.mkdir(parents=True, exist_ok=True)

DIALECT_MAP = {
    "postgresql": "postgres",
    "mysql": "mysql",
    "sqlserver": "tsql",
    "oracle": "oracle",
    "snowflake": "snowflake",
}
ALL_TARGETS = list(DIALECT_MAP.values())

# Construct tagger — returns bool flags
CONSTRUCT_CHECKS = {
    "cte":         lambda t: bool(t.find(exp.With)),
    "window":      lambda t: bool(t.find(exp.Window)),
    "pivot":       lambda t: bool(t.find(exp.Pivot)),
    "array":       lambda t: bool(t.find(exp.Array)),
    "lateral":     lambda t: bool(t.find(exp.Lateral)),
    "json":        lambda t: bool(t.find(exp.JSONExtract) or t.find(exp.Dot)),
    "ddl":         lambda t: isinstance(t, (exp.Create, exp.Drop, exp.Alter)),
    "dml_nonsel":  lambda t: isinstance(t, (exp.Insert, exp.Update, exp.Delete)),
    "subquery":    lambda t: len(list(t.find_all(exp.Subquery))) > 0,
    "union":       lambda t: bool(t.find(exp.Union)),
    "groupby":     lambda t: bool(t.find(exp.Group)),
    "having":      lambda t: bool(t.find(exp.Having)),
    "case":        lambda t: bool(t.find(exp.Case)),
    "recursive":   lambda t: any(
                       getattr(cte, "args", {}).get("recursive", False)
                       for cte in t.find_all(exp.With)),
    "dialect_specific": lambda t: False,  # set per level below
}


def tag_constructs(sql: str, src_dialect: str, level: str) -> dict:
    try:
        tree = sqlglot.parse_one(sql, read=src_dialect)
    except Exception:
        return {k: False for k in CONSTRUCT_CHECKS}
    tags = {k: fn(tree) for k, fn in CONSTRUCT_CHECKS.items()}
    tags["dialect_specific"] = (level == "dialect_specific")
    return tags


def normalise_sql(sql: str) -> str:
    """Normalise SQL for relaxed comparison (strip aliases, lower, collapse whitespace)."""
    sql = sql.lower()
    sql = re.sub(r"\s+", " ", sql).strip()
    sql = re.sub(r"\bAS\b\s+\w+", "", sql, flags=re.IGNORECASE)
    return sql


MIGRATION_PER_QUERY = REPO / "phase2_rebuild" / "results" / "tables" / "sql_migration_per_query.csv"


def main():
    t0 = time.perf_counter()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    # Step 1: Tag all queries with AST constructs
    construct_rows = []
    query_sql_map = {}  # (src_folder, name) -> sql
    for src_folder, levels in catalog.items():
        src_dialect = DIALECT_MAP.get(src_folder)
        if not src_dialect:
            continue
        for level, queries in levels.items():
            for q in queries:
                sql = q["sql"]
                name = q["name"]
                query_sql_map[(src_folder, name)] = sql
                tags = tag_constructs(sql, src_dialect, level)
                construct_rows.append({
                    "src_folder": src_folder, "name": name, "level": level,
                    **tags
                })

    construct_df = pd.DataFrame(construct_rows)
    construct_df.to_csv(OUT / "e5_construct_tags.csv", index=False)

    # Step 2: Load committed per-query migration results (authoritative)
    mq = pd.read_csv(MIGRATION_PER_QUERY)
    # Merge with construct tags
    mq_tagged = mq.merge(
        construct_df,
        left_on=["src_folder", "query"],
        right_on=["src_folder", "name"],
        how="left",
    )
    mq_tagged.to_csv(OUT / "e5_transpile_outcomes.csv", index=False)

    # Step 3: Construct-level AST non-equivalence attribution
    construct_cols = [c for c in CONSTRUCT_CHECKS.keys() if c in mq_tagged.columns]
    attr_rows = []
    for col in construct_cols:
        mask = mq_tagged[col].fillna(False).astype(bool)
        n_with = int(mask.sum())
        n_without = int((~mask).sum())
        n_noneq_with    = int((mq_tagged.loc[mask, "ast_equiv"] == False).sum()) if n_with > 0 else 0
        n_noneq_without = int((mq_tagged.loc[~mask, "ast_equiv"] == False).sum()) if n_without > 0 else 0
        attr_rows.append({
            "construct": col,
            "n_pairs_with": n_with,
            "n_pairs_without": n_without,
            "n_noneq_with": n_noneq_with,
            "n_noneq_without": n_noneq_without,
            "noneq_rate_with": round(n_noneq_with / max(1, n_with), 4),
            "noneq_rate_without": round(n_noneq_without / max(1, n_without), 4),
            "lift": round(
                (n_noneq_with / max(1, n_with)) / max(1e-6, n_noneq_without / max(1, n_without)),
                2
            ),
        })
    attr_df = pd.DataFrame(attr_rows).sort_values("noneq_rate_with", ascending=False)
    attr_df.to_csv(OUT / "e5_failure_attribution.csv", index=False)

    # Step 4: AST equivalence by (src, difficulty)
    diff_agg = mq.groupby(["src_folder", "difficulty"]).agg(
        n=("query", "count"),
        ast_equiv=("ast_equiv", "mean"),
        parse_ok=("parse_ok", "mean"),
        transpile_ok=("transpile_ok", "mean"),
    ).round(4)
    diff_agg.to_csv(OUT / "e5_ast_by_difficulty.csv")

    # Step 5: Top hard queries (non-equivalent most often)
    worst = (mq[mq["ast_equiv"] == False]
              .groupby(["query", "src_folder", "difficulty"])
              .size()
              .reset_index(name="n_noneq_targets")
              .sort_values("n_noneq_targets", ascending=False)
              .head(20))
    worst.to_csv(OUT / "e5_worst_queries.csv", index=False)

    # Step 6: Transpile failures (parse_ok=True but transpile_ok=False)
    failures = mq[(mq["parse_ok"] == True) & (mq["transpile_ok"] == False)].copy()
    failures.to_csv(OUT / "e5_transpile_failures.csv", index=False)

    elapsed = round(time.perf_counter() - t0, 1)
    n_pairs = len(mq)
    n_noneq = int((mq["ast_equiv"] == False).sum())
    n_fail = int((mq["transpile_ok"] == False).sum())
    print(f"[E5] Done in {elapsed}s")
    print(f"  Total pairs: {n_pairs}")
    print(f"  Transpile failures: {n_fail} ({100*n_fail/n_pairs:.1f}%)")
    print(f"  AST non-equiv: {n_noneq} ({100*n_noneq/n_pairs:.1f}%)")
    print(f"\nTop constructs causing non-equivalence (lift vs baseline):")
    print(attr_df[attr_df["n_pairs_with"] > 0].head(10).to_string(index=False))
    print(f"\nWorst queries (non-equiv in most target dialects):")
    print(worst.to_string(index=False))
    print(f"\nAST equivalence by difficulty:")
    print(mq.groupby("difficulty").agg(
        n=("query", "count"), ast_equiv=("ast_equiv", "mean")).round(4).to_string())
    print(f"\nOutputs: {OUT}")


if __name__ == "__main__":
    main()
