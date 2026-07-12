"""
R4.5: Relaxed AST comparator + execution equivalence (postgres -> duckdb focus).

Extends F5 (Round 2) with three canonicalization steps applied BEFORE comparison:
  1. Type-precision stripping: DECIMAL(10,2) -> DECIMAL, VARCHAR(255) -> VARCHAR
  2. LATERAL keyword removal where semantically trivial in DuckDB context
  3. Quote normalization: double-quote, backtick, square-bracket delimiters removed

Research questions:
  (a) How many footprint-inequivalent pairs flip to equivalent under relaxation?
  (b) Does relaxed agree more with execution equivalence than footprint alone?
  (c) Which dialect pairs and query difficulty levels benefit most?

Input: committed phase2_rebuild/results/tables/sql_migration_per_query.csv
Output: rebuttal_artifacts/round4/r45_ast/
  r45_per_query.csv       — per (query,src,tgt): footprint_equiv, relaxed_equiv, exec_equiv
  r45_summary.csv         — aggregate rates per (src_dialect, tgt_dialect)
  r45_flip_analysis.csv   — rows where footprint != relaxed
  R45_REPORT.md
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Optional

import duckdb
import numpy as np
import pandas as pd
import sqlglot
from sqlglot import exp

REPO      = Path(__file__).resolve().parents[2]
CATALOG   = REPO / "test_data" / "sql" / "query_catalog.json"
COMMITTED = REPO / "phase2_rebuild" / "results" / "tables" / "sql_migration_per_query.csv"
OUTDIR    = REPO / "rebuttal_artifacts" / "round4" / "r45_ast"
OUTDIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Round-2 F5 helpers (reproduced exactly for footprint re-validation)
# ---------------------------------------------------------------------------
def _ast_footprint(tree: exp.Expression) -> tuple:
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


DIALECT_MAP = {
    "postgresql": "postgres",
    "mysql":      "mysql",
    "sqlserver":  "tsql",
    "oracle":     "oracle",
    "snowflake":  "snowflake",
}
SQLGLOT_DIALECTS = {v for v in DIALECT_MAP.values()}


def footprint_equiv_pair(sql: str, src: str, tgt: str) -> Optional[bool]:
    """Returns footprint equivalence for one (sql, src, tgt) pair. None = error."""
    try:
        tree_src = sqlglot.parse_one(sql, read=src)
    except Exception:
        return None
    if src == tgt:
        return True
    try:
        out = tree_src.sql(dialect=tgt)
        tree_tgt = sqlglot.parse_one(out, read=tgt)
        return _ast_footprint(tree_src) == _ast_footprint(tree_tgt)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Relaxed canonicalization
# ---------------------------------------------------------------------------
_TYPE_PREC_RE = re.compile(
    r'\b(VARCHAR|CHAR|NVARCHAR|NCHAR|DECIMAL|NUMERIC|FLOAT|DOUBLE\s+PRECISION|'
    r'NUMBER|BINARY_FLOAT|BINARY_DOUBLE|TEXT|CLOB|NCLOB|BLOB|RAW)\s*\(\s*[\d\s,]+\s*\)',
    re.IGNORECASE,
)
_LATERAL_RE     = re.compile(r'\bLATERAL\b', re.IGNORECASE)
_DOUBLE_QUOTE_RE = re.compile(r'"(\w+)"')
_BACKTICK_RE     = re.compile(r'`(\w+)`')
_SQUARE_RE       = re.compile(r'\[(\w+)\]')
_WS_RE           = re.compile(r'\s+')


def _canonicalize(sql: str) -> str:
    """Apply relaxed canonicalization: type precision, LATERAL, quotes, whitespace."""
    sql = _TYPE_PREC_RE.sub(lambda m: m.group(1).upper(), sql)
    sql = _LATERAL_RE.sub("", sql)
    sql = _DOUBLE_QUOTE_RE.sub(r'\1', sql)
    sql = _BACKTICK_RE.sub(r'\1', sql)
    sql = _SQUARE_RE.sub(r'\1', sql)
    sql = _WS_RE.sub(" ", sql).strip()
    return sql.lower()


def relaxed_equiv_pair(sql: str, src: str, tgt: str) -> Optional[bool]:
    """
    Relaxed equivalence: parse both source and transpiled, canonicalize both,
    compare AST footprints after canonicalization. None = parse/transpile error.
    """
    try:
        canon_src = _canonicalize(sql)
        tree_src  = sqlglot.parse_one(canon_src, read=src, error_level=sqlglot.ErrorLevel.IGNORE)
    except Exception:
        return None
    if src == tgt:
        return True
    try:
        out = sqlglot.transpile(sql, read=src, write=tgt, unsupported_level=sqlglot.ErrorLevel.IGNORE)[0]
    except Exception:
        return None
    try:
        canon_tgt = _canonicalize(out)
        tree_tgt  = sqlglot.parse_one(canon_tgt, read=tgt, error_level=sqlglot.ErrorLevel.IGNORE)
        return _ast_footprint(tree_src) == _ast_footprint(tree_tgt)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Execution equivalence on synthetic DuckDB schema
# ---------------------------------------------------------------------------
_SCHEMA_SQL = """
CREATE OR REPLACE TABLE users (
    id INTEGER, name VARCHAR, age INTEGER, email VARCHAR, city VARCHAR,
    created_at DATE, is_active BOOLEAN, salary DECIMAL, department_id INTEGER
);
CREATE OR REPLACE TABLE orders (
    id INTEGER, user_id INTEGER, amount DECIMAL(12,2), order_date DATE,
    status VARCHAR, product_id INTEGER, quantity INTEGER
);
CREATE OR REPLACE TABLE products (
    id INTEGER, name VARCHAR, price DECIMAL(10,2), category VARCHAR,
    stock_qty INTEGER, supplier_id INTEGER
);
CREATE OR REPLACE TABLE employees (
    id INTEGER, name VARCHAR, department_id INTEGER, salary DECIMAL(10,2),
    hire_date DATE, manager_id INTEGER, title VARCHAR, age INTEGER
);
CREATE OR REPLACE TABLE departments (
    id INTEGER, name VARCHAR, budget DECIMAL(12,0), location VARCHAR
);
CREATE OR REPLACE TABLE customers (
    id INTEGER, name VARCHAR, email VARCHAR, city VARCHAR,
    created_at DATE, total_spend DECIMAL(12,2)
);
CREATE OR REPLACE TABLE transactions (
    id INTEGER, customer_id INTEGER, amount DECIMAL(12,2),
    txn_date DATE, category VARCHAR, status VARCHAR
);
CREATE OR REPLACE TABLE monthly_sales (
    month INTEGER, year INTEGER, region VARCHAR, revenue DECIMAL(12,2)
);

INSERT INTO departments VALUES
  (1,'Engineering',500000,'New York'),(2,'Sales',300000,'Chicago'),
  (3,'HR',200000,'Boston'),(4,'Finance',400000,'Austin');

INSERT INTO employees VALUES
  (1,'Alice',1,95000.00,'2020-01-15',NULL,'Senior Engineer',32),
  (2,'Bob',2,70000.00,'2021-03-01',1,'Sales Rep',28),
  (3,'Carol',1,85000.00,'2019-06-01',1,'Engineer',35),
  (4,'Dave',3,65000.00,'2022-01-10',NULL,'HR Manager',41),
  (5,'Eve',4,90000.00,'2018-09-15',NULL,'CFO',50),
  (6,'Frank',2,75000.00,'2021-07-01',2,'Sales Lead',30),
  (7,'Grace',1,105000.00,'2017-04-20',1,'Principal Engineer',40);

INSERT INTO users VALUES
  (1,'Alice',32,'alice@example.com','New York','2020-01-15',TRUE,95000.00,1),
  (2,'Bob',28,'bob@example.com','Chicago','2021-03-01',TRUE,70000.00,2),
  (3,'Carol',35,'carol@example.com','Boston','2019-06-01',FALSE,85000.00,1),
  (4,'Dave',41,'dave@example.com','Austin','2022-01-10',TRUE,65000.00,3),
  (5,'Eve',50,'eve@example.com','New York','2018-09-15',TRUE,90000.00,4);

INSERT INTO products VALUES
  (1,'Laptop',1200.00,'Electronics',50,1),
  (2,'Mouse',25.00,'Electronics',200,1),
  (3,'Desk',350.00,'Furniture',30,2),
  (4,'Chair',250.00,'Furniture',45,2),
  (5,'Monitor',450.00,'Electronics',60,1),
  (6,'Keyboard',80.00,'Electronics',150,1);

INSERT INTO orders VALUES
  (1,1,1200.00,'2024-01-05','completed',1,1),
  (2,2,75.00,'2024-01-10','completed',2,3),
  (3,1,350.00,'2024-01-15','pending',3,1),
  (4,3,700.00,'2024-01-20','completed',5,1),
  (5,4,500.00,'2024-02-01','cancelled',4,2),
  (6,2,480.00,'2024-02-05','completed',6,6),
  (7,5,1650.00,'2024-02-10','completed',1,1),
  (8,1,25.00,'2024-02-15','completed',2,1),
  (9,3,250.00,'2024-03-01','pending',4,1),
  (10,5,450.00,'2024-03-10','completed',5,2);

INSERT INTO customers SELECT id, name, email, city, created_at, salary FROM users;

INSERT INTO transactions VALUES
  (1,1,1200.00,'2024-01-05','Electronics','completed'),
  (2,2,75.00,'2024-01-10','Electronics','completed'),
  (3,1,350.00,'2024-01-15','Furniture','pending'),
  (4,3,700.00,'2024-01-20','Electronics','completed'),
  (5,4,500.00,'2024-02-01','Furniture','cancelled');

INSERT INTO monthly_sales VALUES
  (1,2024,'North',120000.00),(2,2024,'North',135000.00),
  (3,2024,'South',98000.00),(1,2024,'South',88000.00),
  (2,2024,'East',110000.00),(3,2024,'East',125000.00);
"""

_dcon: Optional[duckdb.DuckDBPyConnection] = None


def get_dcon() -> duckdb.DuckDBPyConnection:
    global _dcon
    if _dcon is None:
        _dcon = duckdb.connect(":memory:")
        _dcon.execute(_SCHEMA_SQL)
    return _dcon


def _exec_dkdb(sql: str) -> Optional[list]:
    try:
        rows = get_dcon().execute(sql).fetchall()
        return sorted(rows, key=str)
    except Exception:
        return None


def exec_equiv_pair(sql: str, src: str) -> Optional[bool]:
    """
    Transpile source SQL to DuckDB, execute both on synthetic schema, compare results.
    Source SQL is executed directly in DuckDB (DuckDB is postgres-compatible for most SELECTs).
    Returns None if either cannot execute (e.g., dialect-specific function not in DuckDB).
    """
    try:
        dkdb_sql = sqlglot.transpile(
            sql, read=src, write="duckdb",
            unsupported_level=sqlglot.ErrorLevel.IGNORE
        )[0]
    except Exception:
        return None
    src_rows  = _exec_dkdb(sql)
    dkdb_rows = _exec_dkdb(dkdb_sql)
    if src_rows is None or dkdb_rows is None:
        return None
    return src_rows == dkdb_rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    t0 = time.perf_counter()
    print("[R4.5] Relaxed AST comparator + execution equivalence")

    if not CATALOG.exists():
        print(f"  ERROR: {CATALOG} not found")
        return
    if not COMMITTED.exists():
        print(f"  ERROR: {COMMITTED} not found")
        return

    committed = pd.read_csv(COMMITTED)
    catalog_raw = json.loads(CATALOG.read_text(encoding="utf-8"))

    # Build SQL lookup: (src_folder, query_name) -> sql
    sql_lookup: dict[tuple[str, str], str] = {}
    for dialect, levels in catalog_raw.items():
        for level, queries in levels.items():
            for q in queries:
                sql_lookup[(dialect, q["name"])] = q["sql"]

    print(f"  Committed rows: {len(committed)}  SQL lookup size: {len(sql_lookup)}")

    rows_out: list[dict] = []
    n_total = len(committed)

    for i, row in committed.iterrows():
        q_name    = str(row["query"])
        src_dir   = str(row["src_folder"])
        src_dial  = str(row["src_dialect"])
        tgt_dial  = str(row["tgt_dialect"])
        committed_fp = bool(row["ast_equiv"]) if pd.notna(row["ast_equiv"]) else None
        committed_tp = bool(row["transpile_ok"])

        sql = sql_lookup.get((src_dir, q_name))
        if sql is None:
            # Try all dialect keys
            for dk in catalog_raw:
                for lk, qs in catalog_raw[dk].items():
                    for qq in qs:
                        if qq["name"] == q_name:
                            sql = qq["sql"]
                            break
                    if sql:
                        break
                if sql:
                    break

        if sql is None or not committed_tp:
            rows_out.append({
                "query": q_name, "src_folder": src_dir,
                "src_dialect": src_dial, "tgt_dialect": tgt_dial,
                "level": row.get("level", ""), "difficulty": row.get("difficulty", ""),
                "committed_transpile_ok": committed_tp,
                "committed_footprint_equiv": committed_fp,
                "recomputed_footprint_equiv": None,
                "relaxed_equiv": None,
                "exec_equiv": None,
                "note": "no_sql" if sql is None else "transpile_failed",
            })
            continue

        re_fp = footprint_equiv_pair(sql, src_dial, tgt_dial)
        rx_eq = relaxed_equiv_pair(sql, src_dial, tgt_dial)
        # Only test exec equivalence for postgres->duckdb (most relevant to pipeline)
        ex_eq = exec_equiv_pair(sql, src_dial) if tgt_dial == "duckdb" or (src_dial == "postgres" and tgt_dial == "postgres") else None
        if src_dial == "postgres":
            ex_eq = exec_equiv_pair(sql, src_dial)

        rows_out.append({
            "query": q_name, "src_folder": src_dir,
            "src_dialect": src_dial, "tgt_dialect": tgt_dial,
            "level": row.get("level", ""), "difficulty": row.get("difficulty", ""),
            "committed_transpile_ok": committed_tp,
            "committed_footprint_equiv": committed_fp,
            "recomputed_footprint_equiv": re_fp,
            "relaxed_equiv": rx_eq,
            "exec_equiv": ex_eq,
            "note": "",
        })

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{n_total} processed ...")

    df = pd.DataFrame(rows_out)
    df.to_csv(OUTDIR / "r45_per_query.csv", index=False)
    print(f"  r45_per_query.csv: {len(df)} rows")

    # --- Summary by (src_dialect, tgt_dialect) ---
    valid = df[df["committed_transpile_ok"]].copy()
    summary_rows = []
    for (src, tgt), g in valid.groupby(["src_dialect", "tgt_dialect"]):
        n    = len(g)
        cf   = g["committed_footprint_equiv"].sum()
        rf   = g["recomputed_footprint_equiv"].dropna().astype(bool).sum()
        rx   = g["relaxed_equiv"].dropna().astype(bool).sum()
        ex_g = g["exec_equiv"].dropna().astype(bool)
        ex   = ex_g.sum()
        n_ex = len(ex_g)

        # Flip analysis: committed_fp=False -> relaxed=True (gain)
        n_fp_false   = (g["committed_footprint_equiv"] == False).sum()
        flip_to_eq   = ((g["committed_footprint_equiv"] == False) & (g["relaxed_equiv"] == True)).sum()
        flip_from_eq = ((g["committed_footprint_equiv"] == True)  & (g["relaxed_equiv"] == False)).sum()

        summary_rows.append({
            "src_dialect": src, "tgt_dialect": tgt, "n_pairs": n,
            "committed_fp_rate":    round(cf / max(1, n), 4),
            "recomputed_fp_rate":   round(rf / max(1, n), 4),
            "relaxed_equiv_rate":   round(rx / max(1, n), 4),
            "exec_equiv_rate":      round(ex / max(1, n_ex), 4) if n_ex else None,
            "n_flip_to_equiv":      int(flip_to_eq),
            "n_flip_from_equiv":    int(flip_from_eq),
            "n_fp_false_total":     int(n_fp_false),
        })
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUTDIR / "r45_summary.csv", index=False)
    print(f"  r45_summary.csv: {len(summary)} rows")

    # --- Flip analysis: footprint False -> relaxed True ---
    flips = df[
        (df["committed_transpile_ok"] == True)
        & (df["committed_footprint_equiv"] == False)
        & (df["relaxed_equiv"] == True)
    ].copy()
    flips.to_csv(OUTDIR / "r45_flip_analysis.csv", index=False)
    print(f"  r45_flip_analysis.csv: {len(flips)} rows")

    # --- Overall rates ---
    n_v = len(valid)
    n_cf_true = valid["committed_footprint_equiv"].sum()
    n_rx_true = valid["relaxed_equiv"].dropna().astype(bool).sum()
    n_ex_valid = valid["exec_equiv"].dropna()
    n_ex_true  = n_ex_valid.astype(bool).sum()

    # Agreement: relaxed vs exec (for rows where both are available)
    both = valid.dropna(subset=["relaxed_equiv", "exec_equiv"])
    n_agree = (both["relaxed_equiv"].astype(bool) == both["exec_equiv"].astype(bool)).sum()
    n_both = len(both)
    fp_agree = valid.dropna(subset=["committed_footprint_equiv", "exec_equiv"])
    n_fp_agree = (fp_agree["committed_footprint_equiv"].astype(bool) == fp_agree["exec_equiv"].astype(bool)).sum()

    # Report
    elapsed = round(time.perf_counter() - t0, 1)
    lines = [
        "# R4.5: Relaxed AST Comparator + Execution Equivalence\n\n",
        "## Canonicalization steps applied\n\n",
        "1. **Type-precision stripping**: `VARCHAR(255)` -> `VARCHAR`, `DECIMAL(10,2)` -> `DECIMAL`\n",
        "2. **LATERAL removal**: removes the `LATERAL` keyword (DuckDB supports lateral joins natively)\n",
        "3. **Quote normalization**: strips double-quotes, backticks, square brackets from identifiers\n\n",
        "## Overall rates (transpile_ok rows only)\n\n",
        f"| metric | count | rate |\n|:---|---:|---:|\n",
        f"| n_transpile_ok | {n_v} | 1.000 |\n",
        f"| committed_footprint_equiv | {int(n_cf_true)} | {n_cf_true/max(1,n_v):.4f} |\n",
        f"| relaxed_equiv | {int(n_rx_true)} | {n_rx_true/max(1,n_v):.4f} |\n",
        f"| exec_equiv (n={len(n_ex_valid)}) | {int(n_ex_true)} | {n_ex_true/max(1,len(n_ex_valid)):.4f} |\n\n",
        f"**Flip gain**: {len(flips)} pairs flip from footprint=False to relaxed=True\n",
        f"**Relaxed vs exec agreement**: {n_agree}/{n_both} = {n_agree/max(1,n_both):.4f}\n",
        f"**Footprint vs exec agreement**: {n_fp_agree}/{len(fp_agree)} = {n_fp_agree/max(1,len(fp_agree)):.4f}\n\n",
    ]

    lines.append("## Summary by (src_dialect, tgt_dialect)\n\n")
    lines.append(summary.to_markdown(index=False) + "\n\n")

    lines.append("## Flip analysis sample (footprint=False -> relaxed=True)\n\n")
    if len(flips):
        sample = flips[["query", "src_dialect", "tgt_dialect", "level", "exec_equiv"]].head(15)
        lines.append(sample.to_markdown(index=False) + "\n\n")
    else:
        lines.append("No flips found.\n\n")

    lines.append(f"---\nGenerated in {elapsed}s\n")

    with open(OUTDIR / "R45_REPORT.md", "w", encoding="utf-8") as f:
        f.write("".join(lines))

    print(f"\n[R4.5] Done in {elapsed}s")
    print(f"Outputs: {OUTDIR}")
    print(f"\n=== OVERALL RATES ===")
    print(f"  Committed footprint:  {n_cf_true}/{n_v} = {n_cf_true/max(1,n_v):.4f}")
    print(f"  Relaxed equiv:        {n_rx_true}/{n_v} = {n_rx_true/max(1,n_v):.4f}")
    print(f"  Exec equiv:           {n_ex_true}/{len(n_ex_valid)} = {n_ex_true/max(1,len(n_ex_valid)):.4f}")
    print(f"  Flip gain (fp->rx):   {len(flips)}")
    print(f"  Relaxed vs exec agr:  {n_agree}/{n_both} = {n_agree/max(1,n_both):.4f}")


if __name__ == "__main__":
    main()
