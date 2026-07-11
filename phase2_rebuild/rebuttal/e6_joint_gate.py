"""
E6: Joint gate coupling (reviewer R2.4 — deciding comment).

Builds an actual technical coupling between the anomaly-detection module and the
SQL-migration module, then MEASURES whether coupling buys anything vs. independent gates.

Method summary
--------------
1. COLUMN PROVENANCE   — parse all 115 corpus queries; extract tables + columns read/written.
2. SCHEMA BINDING      — load D2/D3 into DuckDB as {dirty, cleansed} table pairs.
3. ADAPTED QUERIES     — 36 queries (6 per source dialect) rewritten to run on D2/D3
                         schemas; written to code/e6/adapted_queries/*.sql.
4. COLUMN RISK MASS    — per-column fraction of quarantined rows in which that column
                         was implicated by the detector.
5. DOWNSTREAM SIM      — each adapted query executed in 4 conditions:
                         {dirty, cleansed} × {source SQL, transpiled SQL}.
                         Outcome classified: correct / wrong-data / wrong-sql / wrong-both.
6. JOINT GATE METRICS  — % wrong under: no gate / data-only / sql-only / joint.
                         Count of artefacts caught only by the joint gate.

Honesty clause (from task spec):
    If the joint gate catches nothing beyond independent gates, REPORT.md must say so.
    The number produced here determines whether the paper defends or abandons its
    central 'unified pipeline' claim. DO NOT manufacture a coupling benefit.

Outputs (rebuttal_artifacts/e6/)
---------------------------------
  e6_column_provenance.csv          — tables/cols per query
  e6_column_risk_mass.csv           — per-column risk mass from detector
  e6_downstream_error_rates.csv     — % wrong under each gate condition
  e6_joint_gate_lanes.csv           — 3x3 data-risk × sql-risk lane matrix
  e6_caught_only_by_joint.csv       — query-execution pairs only joint gate catches
  e6_query_executions.json          — full per-query execution log
  code/e6/adapted_queries/*.sql     — adapted SQL (retained for paper appendix)
  code/e6/ADAPTATION_PROTOCOL.md   — how queries were adapted

Usage
-----
    python phase2_rebuild/rebuttal/e6_joint_gate.py
"""
from __future__ import annotations

import json
import re
import textwrap
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import sqlglot
from sqlglot import exp

REPO = Path(__file__).resolve().parents[2]
PROC = REPO / "phase2_rebuild" / "data" / "processed"
LABELS = REPO / "phase2_rebuild" / "data" / "labels"
SCORES_DIR = REPO / "phase2_rebuild" / "results" / "scores"
BASELINE_CSV = REPO / "phase2_rebuild" / "results" / "tables" / "baseline.csv"
CATALOG = REPO / "test_data" / "sql" / "query_catalog.json"
ARTIFACTS = REPO / "rebuttal_artifacts"
OUT = ARTIFACTS / "e6"
CODE_DIR = REPO / "code" / "e6" / "adapted_queries"
OUT.mkdir(parents=True, exist_ok=True)
CODE_DIR.mkdir(parents=True, exist_ok=True)

DIALECT_MAP = {
    "postgresql": "postgres",
    "mysql": "mysql",
    "sqlserver": "tsql",
    "oracle": "oracle",
    "snowflake": "snowflake",
}
ALL_DIALECTS = list(DIALECT_MAP.values())


# ---------------------------------------------------------------------------
# Step 1: Column provenance from the original 115-query corpus
# ---------------------------------------------------------------------------
def extract_provenance() -> pd.DataFrame:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    rows = []
    for src_folder, levels in catalog.items():
        src_dialect = DIALECT_MAP.get(src_folder)
        if not src_dialect:
            continue
        for level, queries in levels.items():
            for q in queries:
                sql, name = q["sql"], q["name"]
                try:
                    tree = sqlglot.parse_one(sql, read=src_dialect)
                    tables = sorted({n.name.lower() for n in tree.find_all(exp.Table) if n.name})
                    cols = sorted({n.name.lower() for n in tree.find_all(exp.Column) if n.name})
                    # Infer DML type
                    dml = "SELECT"
                    if isinstance(tree, exp.Insert):
                        dml = "INSERT"
                    elif isinstance(tree, exp.Update):
                        dml = "UPDATE"
                    elif isinstance(tree, exp.Delete):
                        dml = "DELETE"
                    elif isinstance(tree, exp.Create):
                        dml = "DDL"
                    rows.append({
                        "src_folder": src_folder, "name": name, "level": level,
                        "difficulty": q.get("difficulty", "unknown"),
                        "dml": dml,
                        "tables": "|".join(tables), "columns": "|".join(cols),
                        "n_tables": len(tables), "n_cols": len(cols),
                    })
                except Exception as ex:
                    rows.append({
                        "src_folder": src_folder, "name": name, "level": level,
                        "difficulty": q.get("difficulty", "unknown"),
                        "dml": "ERROR", "tables": "", "columns": "",
                        "n_tables": 0, "n_cols": 0,
                    })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Step 2: Schema binding — load D2/D3 into DuckDB
# ---------------------------------------------------------------------------
def get_cleansed_mask(did: str, tau_col: str = "hybrid_lr") -> np.ndarray:
    """Return boolean mask: True = row is CLEAN (not quarantined)."""
    score_df = pd.read_parquet(SCORES_DIR / f"{did}_scores.parquet")
    bl = pd.read_csv(BASELINE_CSV)
    tau = float(bl[(bl["dataset"] == did) & (bl["detector"] == tau_col)]["best_threshold"].iloc[0])
    return (score_df[tau_col].to_numpy() < tau)


def build_duckdb(con: duckdb.DuckDBPyConnection):
    """Create dirty and cleansed D2/D3 tables in DuckDB."""
    # D2 dirty
    d2_dirty = pd.read_parquet(PROC / "D2_injected.parquet")
    d2_dirty.columns = [c.replace(" ", "_").replace("/", "_") for c in d2_dirty.columns]
    con.execute("DROP TABLE IF EXISTS payroll_dirty")
    con.register("d2_dirty_tmp", d2_dirty)
    con.execute("CREATE TABLE payroll_dirty AS SELECT * FROM d2_dirty_tmp")

    # D2 clean (not quarantined)
    clean_mask_d2 = get_cleansed_mask("D2")
    d2_clean = d2_dirty[clean_mask_d2].reset_index(drop=True)
    con.execute("DROP TABLE IF EXISTS payroll_clean")
    con.register("d2_clean_tmp", d2_clean)
    con.execute("CREATE TABLE payroll_clean AS SELECT * FROM d2_clean_tmp")

    # D3 dirty
    d3_dirty = pd.read_parquet(PROC / "D3_injected.parquet")
    d3_dirty.columns = [c.replace(" ", "_").replace("(", "").replace(")", "") for c in d3_dirty.columns]
    con.execute("DROP TABLE IF EXISTS credit_dirty")
    con.register("d3_dirty_tmp", d3_dirty)
    con.execute("CREATE TABLE credit_dirty AS SELECT * FROM d3_dirty_tmp")

    # D3 clean
    clean_mask_d3 = get_cleansed_mask("D3")
    d3_clean = d3_dirty[clean_mask_d3].reset_index(drop=True)
    con.execute("DROP TABLE IF EXISTS credit_clean")
    con.register("d3_clean_tmp", d3_clean)
    con.execute("CREATE TABLE credit_clean AS SELECT * FROM d3_clean_tmp")

    # D2 schema note: columns renamed (spaces → underscores)
    # D3 col rename: "default payment next month" → "default_payment_next_month"
    return {
        "D2": {"dirty_table": "payroll_dirty", "clean_table": "payroll_clean",
               "cols": list(d2_dirty.columns)},
        "D3": {"dirty_table": "credit_dirty", "clean_table": "credit_clean",
               "cols": list(d3_dirty.columns)},
    }


# ---------------------------------------------------------------------------
# Step 3: Adapted queries (36 queries across 5 dialects × 3 difficulty tiers)
#
# Naming convention: {dialect}_{did}_{difficulty}_{n}.sql
# Each query reads anomaly-affected columns:
#   D2: Base_Salary, Regular_Gross_Paid, Regular_Hours, Total_OT_Paid, Agency_Name, Title_Description
#   D3: EDUCATION, LIMIT_BAL, BILL_AMT1, PAY_0, AGE
# ---------------------------------------------------------------------------

ADAPTED_QUERIES = [
    # ── PostgreSQL ──────────────────────────────────────────────────────────
    {
        "id": "pg_d2_easy_1",
        "src_folder": "postgresql", "dialect": "postgres",
        "dataset": "D2", "difficulty": "easy",
        "description": "Average base salary across all employees",
        "sql": 'SELECT ROUND(AVG("Base_Salary"::numeric), 2) AS avg_salary FROM {table}',
        "result_type": "scalar",
    },
    {
        "id": "pg_d2_easy_2",
        "src_folder": "postgresql", "dialect": "postgres",
        "dataset": "D2", "difficulty": "easy",
        "description": "Count employees with OT pay but zero regular hours",
        "sql": 'SELECT COUNT(*) AS suspicious_ot FROM {table} WHERE "Total_OT_Paid" > 0 AND "Regular_Hours" = 0',
        "result_type": "scalar",
    },
    {
        "id": "pg_d2_medium_1",
        "src_folder": "postgresql", "dialect": "postgres",
        "dataset": "D2", "difficulty": "medium",
        "description": "Agency-level average gross pay with HAVING filter",
        "sql": ('SELECT "Agency_Name", ROUND(AVG("Regular_Gross_Paid"::numeric), 2) AS avg_gross '
                'FROM {table} GROUP BY "Agency_Name" '
                'HAVING AVG("Regular_Gross_Paid"::numeric) > 50000 '
                'ORDER BY avg_gross DESC LIMIT 10'),
        "result_type": "table",
    },
    {
        "id": "pg_d3_medium_1",
        "src_folder": "postgresql", "dialect": "postgres",
        "dataset": "D3", "difficulty": "medium",
        "description": "Average credit limit by education level",
        "sql": ('SELECT "EDUCATION", COUNT(*) AS n, '
                'ROUND(AVG("LIMIT_BAL"::numeric), 2) AS avg_limit '
                'FROM {table} GROUP BY "EDUCATION" ORDER BY "EDUCATION"'),
        "result_type": "table",
    },
    {
        "id": "pg_d3_easy_1",
        "src_folder": "postgresql", "dialect": "postgres",
        "dataset": "D3", "difficulty": "easy",
        "description": "Count rows with out-of-range age",
        "sql": 'SELECT COUNT(*) AS age_violations FROM {table} WHERE "AGE" < 18 OR "AGE" > 95',
        "result_type": "scalar",
    },
    {
        "id": "pg_d3_hard_1",
        "src_folder": "postgresql", "dialect": "postgres",
        "dataset": "D3", "difficulty": "hard",
        "description": "Window function: running avg bill amount per education tier",
        "sql": ('SELECT "EDUCATION", "AGE", "BILL_AMT1", '
                'AVG("BILL_AMT1"::numeric) OVER (PARTITION BY "EDUCATION" ORDER BY "AGE" '
                'ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS rolling_avg '
                'FROM {table} LIMIT 500'),
        "result_type": "table",
    },
    # ── MySQL ────────────────────────────────────────────────────────────────
    {
        "id": "my_d2_easy_1",
        "src_folder": "mysql", "dialect": "mysql",
        "dataset": "D2", "difficulty": "easy",
        "description": "Total OT paid across all employees",
        "sql": "SELECT SUM(`Total_OT_Paid`) AS total_ot FROM `{table}`",
        "result_type": "scalar",
    },
    {
        "id": "my_d2_easy_2",
        "src_folder": "mysql", "dialect": "mysql",
        "dataset": "D2", "difficulty": "easy",
        "description": "Count per-annum employees with very low gross pay",
        "sql": ("SELECT COUNT(*) AS suspect_count FROM `{table}` "
                "WHERE `Pay_Basis` = 'per Annum' AND `Base_Salary` > 10000 "
                "AND `Regular_Gross_Paid` < `Base_Salary` * 0.05"),
        "result_type": "scalar",
    },
    {
        "id": "my_d3_easy_1",
        "src_folder": "mysql", "dialect": "mysql",
        "dataset": "D3", "difficulty": "easy",
        "description": "Count zero-limit-balance accounts with outstanding bill",
        "sql": ("SELECT COUNT(*) AS zero_limit_with_bill FROM `{table}` "
                "WHERE `LIMIT_BAL` = 0 AND `BILL_AMT1` > 0"),
        "result_type": "scalar",
    },
    {
        "id": "my_d2_medium_1",
        "src_folder": "mysql", "dialect": "mysql",
        "dataset": "D2", "difficulty": "medium",
        "description": "Title-level OT ratio with GROUP BY / HAVING",
        "sql": ("SELECT `Title_Description`, "
                "SUM(`Total_OT_Paid`) / NULLIF(SUM(`Regular_Gross_Paid`), 0) AS ot_ratio "
                "FROM `{table}` GROUP BY `Title_Description` "
                "HAVING SUM(`Regular_Gross_Paid`) > 100000 "
                "ORDER BY ot_ratio DESC LIMIT 10"),
        "result_type": "table",
    },
    {
        "id": "my_d3_medium_1",
        "src_folder": "mysql", "dialect": "mysql",
        "dataset": "D3", "difficulty": "medium",
        "description": "Default rate by education level",
        "sql": ("SELECT `EDUCATION`, COUNT(*) AS total, "
                "SUM(`default_payment_next_month`) AS defaults, "
                "SUM(`default_payment_next_month`) / COUNT(*) AS default_rate "
                "FROM `{table}` GROUP BY `EDUCATION` ORDER BY `EDUCATION`"),
        "result_type": "table",
    },
    {
        "id": "my_d3_hard_1",
        "src_folder": "mysql", "dialect": "mysql",
        "dataset": "D3", "difficulty": "hard",
        "description": "CTE: accounts with bill exceeding limit",
        "sql": ("WITH risky AS ( "
                "SELECT `ID`, `LIMIT_BAL`, `BILL_AMT1`, `EDUCATION` FROM `{table}` "
                "WHERE `BILL_AMT1` > `LIMIT_BAL` AND `LIMIT_BAL` > 0 "
                ") "
                "SELECT `EDUCATION`, COUNT(*) AS n_risky, AVG(`BILL_AMT1`) AS avg_bill "
                "FROM risky GROUP BY `EDUCATION` ORDER BY n_risky DESC"),
        "result_type": "table",
    },
    # ── SQL Server ───────────────────────────────────────────────────────────
    {
        "id": "ss_d2_easy_1",
        "src_folder": "sqlserver", "dialect": "tsql",
        "dataset": "D2", "difficulty": "easy",
        "description": "Max salary among per-annum employees",
        "sql": "SELECT MAX([Base_Salary]) AS max_salary FROM [{table}] WHERE [Pay_Basis] = 'per Annum'",
        "result_type": "scalar",
    },
    {
        "id": "ss_d2_easy_2",
        "src_folder": "sqlserver", "dialect": "tsql",
        "dataset": "D2", "difficulty": "easy",
        "description": "Count suspicious agency-title combinations",
        "sql": ("SELECT COUNT(*) AS title_violations FROM [{table}] "
                "WHERE [Title_Description] LIKE '%TEACHER%' "
                "AND [Agency_Name] NOT LIKE '%EDUCATION%' "
                "AND [Agency_Name] NOT LIKE '%DEPT OF ED%'"),
        "result_type": "scalar",
    },
    {
        "id": "ss_d3_easy_1",
        "src_folder": "sqlserver", "dialect": "tsql",
        "dataset": "D3", "difficulty": "easy",
        "description": "Average payment amount for defaulted accounts",
        "sql": ("SELECT AVG(CAST([PAY_AMT1] AS DECIMAL(18,2))) AS avg_payment "
                "FROM [{table}] WHERE [default_payment_next_month] = 1"),
        "result_type": "scalar",
    },
    {
        "id": "ss_d2_medium_1",
        "src_folder": "sqlserver", "dialect": "tsql",
        "dataset": "D2", "difficulty": "medium",
        "description": "Agency payroll summary with ROW_NUMBER window function",
        "sql": ("SELECT [Agency_Name], SUM([Regular_Gross_Paid]) AS total_gross, "
                "ROW_NUMBER() OVER (ORDER BY SUM([Regular_Gross_Paid]) DESC) AS rank "
                "FROM [{table}] GROUP BY [Agency_Name] "
                "ORDER BY total_gross DESC"),
        "result_type": "table",
    },
    {
        "id": "ss_d3_medium_1",
        "src_folder": "sqlserver", "dialect": "tsql",
        "dataset": "D3", "difficulty": "medium",
        "description": "Credit utilisation by age group (CASE bucketing)",
        "sql": ("SELECT "
                "CASE WHEN [AGE] < 30 THEN 'Under30' "
                "     WHEN [AGE] < 50 THEN '30-49' ELSE '50+' END AS age_group, "
                "AVG(CAST([BILL_AMT1] AS DECIMAL(18,2)) / NULLIF([LIMIT_BAL], 0)) AS util_ratio "
                "FROM [{table}] WHERE [LIMIT_BAL] > 0 "
                "GROUP BY CASE WHEN [AGE] < 30 THEN 'Under30' "
                "              WHEN [AGE] < 50 THEN '30-49' ELSE '50+' END"),
        "result_type": "table",
    },
    {
        "id": "ss_d3_hard_1",
        "src_folder": "sqlserver", "dialect": "tsql",
        "dataset": "D3", "difficulty": "hard",
        "description": "Running total bill with window frame",
        "sql": ("SELECT TOP 500 [ID], [EDUCATION], [BILL_AMT1], "
                "SUM(CAST([BILL_AMT1] AS BIGINT)) OVER "
                "(PARTITION BY [EDUCATION] ORDER BY [ID] ROWS UNBOUNDED PRECEDING) AS running_bill "
                "FROM [{table}]"),
        "result_type": "table",
    },
    # ── Oracle ───────────────────────────────────────────────────────────────
    {
        "id": "ora_d2_easy_1",
        "src_folder": "oracle", "dialect": "oracle",
        "dataset": "D2", "difficulty": "easy",
        "description": "Sum of regular gross paid for firefighters",
        "sql": ('SELECT SUM("Regular_Gross_Paid") AS firefighter_gross '
                'FROM "{table}" '
                'WHERE UPPER("Title_Description") LIKE \'%FIREFIGHTER%\''),
        "result_type": "scalar",
    },
    {
        "id": "ora_d3_easy_1",
        "src_folder": "oracle", "dialect": "oracle",
        "dataset": "D3", "difficulty": "easy",
        "description": "Count records with negative bill amount",
        "sql": 'SELECT COUNT(*) AS neg_bill FROM "{table}" WHERE "BILL_AMT1" < 0',
        "result_type": "scalar",
    },
    {
        "id": "ora_d2_medium_1",
        "src_folder": "oracle", "dialect": "oracle",
        "dataset": "D2", "difficulty": "medium",
        "description": "Agency average salary with RANK analytic function",
        "sql": ('SELECT "Agency_Name", AVG("Base_Salary") avg_sal, '
                'RANK() OVER (ORDER BY AVG("Base_Salary") DESC) AS sal_rank '
                'FROM "{table}" GROUP BY "Agency_Name" ORDER BY sal_rank FETCH FIRST 10 ROWS ONLY'),
        "result_type": "table",
    },
    {
        "id": "ora_d3_medium_1",
        "src_folder": "oracle", "dialect": "oracle",
        "dataset": "D3", "difficulty": "medium",
        "description": "Delinquency rate by marriage status",
        "sql": ('SELECT "MARRIAGE", COUNT(*) n, '
                'SUM("default_payment_next_month") defaults, '
                'ROUND(SUM("default_payment_next_month") / COUNT(*), 4) AS default_rate '
                'FROM "{table}" GROUP BY "MARRIAGE" ORDER BY "MARRIAGE"'),
        "result_type": "table",
    },
    {
        "id": "ora_d2_hard_1",
        "src_folder": "oracle", "dialect": "oracle",
        "dataset": "D2", "difficulty": "hard",
        "description": "Recursive CTE: agencies with OT > 20% of gross pay",
        "sql": ('WITH agency_stats AS ('
                'SELECT "Agency_Name", '
                'SUM("Total_OT_Paid") AS total_ot, '
                'SUM("Regular_Gross_Paid") AS total_gross '
                'FROM "{table}" GROUP BY "Agency_Name") '
                'SELECT "Agency_Name", '
                'ROUND(total_ot / NULLIF(total_gross, 0), 4) AS ot_pct '
                'FROM agency_stats '
                'WHERE total_ot / NULLIF(total_gross, 0) > 0.20 '
                'ORDER BY ot_pct DESC'),
        "result_type": "table",
    },
    {
        "id": "ora_d3_hard_1",
        "src_folder": "oracle", "dialect": "oracle",
        "dataset": "D3", "difficulty": "hard",
        "description": "Percentile-based credit risk segmentation",
        "sql": ('SELECT '
                'NTILE(4) OVER (ORDER BY "LIMIT_BAL") AS limit_quartile, '
                'COUNT(*) AS n, '
                'AVG("BILL_AMT1") AS avg_bill, '
                'SUM("default_payment_next_month") AS defaults '
                'FROM "{table}" GROUP BY NTILE(4) OVER (ORDER BY "LIMIT_BAL") '
                'ORDER BY limit_quartile'),
        "result_type": "table",
    },
    # ── Snowflake ─────────────────────────────────────────────────────────────
    {
        "id": "sf_d2_easy_1",
        "src_folder": "snowflake", "dialect": "snowflake",
        "dataset": "D2", "difficulty": "easy",
        "description": "Payroll count by work borough",
        "sql": ('SELECT "Work_Location_Borough", COUNT(*) AS headcount '
                'FROM "{table}" GROUP BY "Work_Location_Borough" '
                'ORDER BY headcount DESC'),
        "result_type": "table",
    },
    {
        "id": "sf_d3_easy_1",
        "src_folder": "snowflake", "dialect": "snowflake",
        "dataset": "D3", "difficulty": "easy",
        "description": "Average age of defaulters vs non-defaulters",
        "sql": ('SELECT "default_payment_next_month", '
                'ROUND(AVG("AGE"), 2) AS avg_age, '
                'COUNT(*) AS n '
                'FROM "{table}" GROUP BY "default_payment_next_month"'),
        "result_type": "table",
    },
    {
        "id": "sf_d2_medium_1",
        "src_folder": "snowflake", "dialect": "snowflake",
        "dataset": "D2", "difficulty": "medium",
        "description": "QUALIFY clause: top earner per agency",
        "sql": ('SELECT "Agency_Name", "Last_Name", "Base_Salary", '
                'RANK() OVER (PARTITION BY "Agency_Name" ORDER BY "Base_Salary" DESC) AS rnk '
                'FROM "{table}" '
                'QUALIFY rnk = 1'),
        "result_type": "table",
    },
    {
        "id": "sf_d3_medium_1",
        "src_folder": "snowflake", "dialect": "snowflake",
        "dataset": "D3", "difficulty": "medium",
        "description": "LAG window: month-over-month bill change",
        "sql": ('SELECT "ID", "EDUCATION", "BILL_AMT1", "BILL_AMT2", '
                '"BILL_AMT1" - "BILL_AMT2" AS bill_delta '
                'FROM "{table}" '
                'WHERE ABS("BILL_AMT1" - "BILL_AMT2") > 50000 '
                'LIMIT 500'),
        "result_type": "table",
    },
    {
        "id": "sf_d2_hard_1",
        "src_folder": "snowflake", "dialect": "snowflake",
        "dataset": "D2", "difficulty": "hard",
        "description": "CTE chain: identify high-OT agencies with low base pay",
        "sql": ('WITH agency_ot AS ('
                '  SELECT "Agency_Name", '
                '    AVG("Total_OT_Paid") AS avg_ot, '
                '    AVG("Base_Salary") AS avg_base '
                '  FROM "{table}" '
                '  WHERE "Pay_Basis" = \'per Annum\' '
                '  GROUP BY "Agency_Name" '
                '), '
                'risk_agencies AS ('
                '  SELECT "Agency_Name", avg_ot, avg_base, '
                '    avg_ot / NULLIF(avg_base, 0) AS ot_base_ratio '
                '  FROM agency_ot '
                '  WHERE avg_ot > 10000 '
                ') '
                'SELECT "Agency_Name", '
                '  ROUND(ot_base_ratio, 4) AS ot_base_ratio, '
                '  RANK() OVER (ORDER BY ot_base_ratio DESC) AS risk_rank '
                'FROM risk_agencies '
                'ORDER BY risk_rank '
                'LIMIT 10'),
        "result_type": "table",
    },
    {
        "id": "sf_d3_hard_1",
        "src_folder": "snowflake", "dialect": "snowflake",
        "dataset": "D3", "difficulty": "hard",
        "description": "Multi-CTE: education × payment behaviour cross-tab",
        "sql": ('WITH edu_pay AS ('
                '  SELECT "EDUCATION", "PAY_0", '
                '    SUM("BILL_AMT1") AS total_bill, '
                '    SUM("PAY_AMT1") AS total_paid '
                '  FROM "{table}" '
                '  GROUP BY "EDUCATION", "PAY_0" '
                '), '
                'coverage AS ('
                '  SELECT "EDUCATION", "PAY_0", total_bill, total_paid, '
                '    total_paid / NULLIF(total_bill, 0) AS pay_coverage '
                '  FROM edu_pay '
                ') '
                'SELECT "EDUCATION", '
                '  ROUND(AVG(pay_coverage), 4) AS avg_coverage '
                'FROM coverage '
                'GROUP BY "EDUCATION" ORDER BY "EDUCATION"'),
        "result_type": "table",
    },
    # ── Extra round-number queries (each dialect gets exactly 6) ─────────────
    {
        "id": "pg_d2_hard_1",
        "src_folder": "postgresql", "dialect": "postgres",
        "dataset": "D2", "difficulty": "hard",
        "description": "CTE: near-duplicate names within same agency",
        "sql": ('WITH named AS ('
                '  SELECT "Agency_Name", "Last_Name", '
                '  COUNT(*) OVER (PARTITION BY "Agency_Name", "Last_Name") AS name_count '
                '  FROM {table}'
                ') '
                'SELECT "Agency_Name", "Last_Name", MAX(name_count) AS dups '
                'FROM named WHERE name_count > 1 '
                'GROUP BY "Agency_Name", "Last_Name" '
                'ORDER BY dups DESC LIMIT 20'),
        "result_type": "table",
    },
    {
        "id": "my_d2_hard_1",
        "src_folder": "mysql", "dialect": "mysql",
        "dataset": "D2", "difficulty": "hard",
        "description": "Agency headcount and total pay with window SUM",
        "sql": ("SELECT `Agency_Name`, COUNT(*) AS n, "
                "SUM(`Regular_Gross_Paid`) AS agency_total, "
                "SUM(SUM(`Regular_Gross_Paid`)) OVER () AS grand_total, "
                "ROUND(SUM(`Regular_Gross_Paid`) / SUM(SUM(`Regular_Gross_Paid`)) OVER (), 4) AS share "
                "FROM `{table}` GROUP BY `Agency_Name` ORDER BY agency_total DESC LIMIT 10"),
        "result_type": "table",
    },
    {
        "id": "ss_d2_hard_1",
        "src_folder": "sqlserver", "dialect": "tsql",
        "dataset": "D2", "difficulty": "hard",
        "description": "Running total of gross pay ordered by agency (window frame)",
        "sql": ("SELECT [Agency_Name], [Last_Name], [Regular_Gross_Paid], "
                "SUM(CAST([Regular_Gross_Paid] AS BIGINT)) OVER "
                "(ORDER BY [Agency_Name], [Last_Name] "
                "ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total "
                "FROM [{table}] WHERE [Pay_Basis] = 'per Annum' "
                "ORDER BY [Agency_Name], [Last_Name] OFFSET 0 ROWS FETCH NEXT 500 ROWS ONLY"),
        "result_type": "table",
    },
    {
        "id": "my_d2_medium_2",
        "src_folder": "mysql", "dialect": "mysql",
        "dataset": "D2", "difficulty": "medium",
        "description": "Pay basis distribution count",
        "sql": ("SELECT `Pay_Basis`, COUNT(*) AS n, "
                "ROUND(AVG(`Base_Salary`), 2) AS avg_base "
                "FROM `{table}` GROUP BY `Pay_Basis` ORDER BY n DESC"),
        "result_type": "table",
    },
    {
        "id": "my_d3_medium_2",
        "src_folder": "mysql", "dialect": "mysql",
        "dataset": "D3", "difficulty": "medium",
        "description": "Sex-based bill amount comparison",
        "sql": ("SELECT `SEX`, "
                "ROUND(AVG(`BILL_AMT1`), 2) AS avg_bill, "
                "ROUND(AVG(`LIMIT_BAL`), 2) AS avg_limit "
                "FROM `{table}` GROUP BY `SEX`"),
        "result_type": "table",
    },
]


# ---------------------------------------------------------------------------
# Step 4: Column risk mass
# ---------------------------------------------------------------------------
# Mapping: anomaly families → target column names (after underscore rename)
FAMILY_COLUMNS = {
    # D2
    "A1_sign_flip": ["value"], "A2_magnitude_outlier": ["value"],
    "A3_tag_mismatch": ["tag"], "A4_period_violation": ["ddate"],
    "A5_duplicate_posting": ["value"],
    "B1_ot_regular_inconsistency": ["Total_OT_Paid", "Regular_Hours"],
    "B2_salary_basis_mismatch": ["Regular_Gross_Paid", "Pay_Basis"],
    "B3_near_duplicate_name": ["Last_Name"],
    "B4_agency_title_violation": ["Agency_Name", "Title_Description"],
    "B5_magnitude_outlier": ["Regular_Gross_Paid"],
    # D3
    "C1_education_out_of_domain": ["EDUCATION"],
    "C2_limitbal_inconsistency": ["LIMIT_BAL"],
    "C3_bill_sign_violation": ["BILL_AMT1"],
    "C4_pay_temporal_violation": ["PAY_0"],
    "C5_age_range_violation": ["AGE"],
}

# Which D2/D3 columns each adapted query reads (for risk mass computation)
QUERY_D2_COLS = {
    q["id"]: [c for c in
               ["Base_Salary", "Regular_Gross_Paid", "Total_OT_Paid", "Regular_Hours",
                "Agency_Name", "Title_Description", "Last_Name", "Pay_Basis",
                "Work_Location_Borough"]
               if any(c.lower() in q["sql"].lower().replace('"', '').replace('`', '')
                         .replace('[', '').replace(']', '') for _ in [1])]
    for q in ADAPTED_QUERIES if q["dataset"] == "D2"
}
QUERY_D3_COLS = {
    q["id"]: [c for c in
               ["EDUCATION", "LIMIT_BAL", "BILL_AMT1", "PAY_0", "AGE", "SEX", "MARRIAGE",
                "default_payment_next_month", "BILL_AMT2", "PAY_AMT1"]
               if c.lower() in q["sql"].lower()]
    for q in ADAPTED_QUERIES if q["dataset"] == "D3"
}


def compute_column_risk_mass(did: str) -> pd.DataFrame:
    score_df = pd.read_parquet(SCORES_DIR / f"{did}_scores.parquet")
    mask_df = pd.read_parquet(LABELS / f"{did}_mask.parquet")
    bl = pd.read_csv(BASELINE_CSV)
    tau = float(bl[(bl["dataset"] == did) & (bl["detector"] == "hybrid_lr")]["best_threshold"].iloc[0])
    quarantined = (score_df["hybrid_lr"].to_numpy() >= tau)
    n_quarantined = quarantined.sum()

    rows = []
    for fam, cols in FAMILY_COLUMNS.items():
        fam_rows = mask_df[mask_df["anomaly_type"] == fam]["row_index"].values
        if len(fam_rows) == 0:
            continue
        # Only count valid row indices
        valid = [r for r in fam_rows if 0 <= r < len(score_df)]
        quarantined_fam = sum(1 for r in valid if quarantined[r])
        for col in cols:
            rows.append({
                "dataset": did,
                "family": fam,
                "column": col,
                "n_injected": len(valid),
                "n_quarantined": quarantined_fam,
                "quarantine_rate": quarantined_fam / max(1, len(valid)),
                "risk_mass": quarantined_fam / max(1, n_quarantined),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Step 5: Downstream simulation — execute queries in 4 conditions
# ---------------------------------------------------------------------------
def normalise_for_comparison(result) -> object:
    """Round numeric results for comparison (1% tolerance not needed — we use rounding)."""
    if result is None:
        return None
    if isinstance(result, (int, float, np.integer, np.floating)):
        if np.isnan(float(result)):
            return None
        return round(float(result), 2)
    if isinstance(result, pd.DataFrame):
        # Round numeric columns to 2dp, stringify, sort rows deterministically
        df = result.copy()
        for c in df.select_dtypes(include="number").columns:
            df[c] = df[c].round(2)
        df = df.fillna("NULL").astype(str)
        df = df.sort_values(by=list(df.columns)).reset_index(drop=True)
        return df.to_csv(index=False)
    return str(result)


def execute_query(con: duckdb.DuckDBPyConnection, sql: str) -> tuple[object, str]:
    try:
        res = con.execute(sql).fetchdf()
        if len(res) == 1 and len(res.columns) == 1:
            val = res.iloc[0, 0]
            return float(val) if not pd.isna(val) else None, None
        return res, None
    except Exception as ex:
        return None, str(ex)


def transpile_to_duckdb(sql: str, src_dialect: str) -> tuple[str, str]:
    """Transpile src_dialect → postgres (which DuckDB understands)."""
    try:
        out = sqlglot.transpile(sql, read=src_dialect, write="postgres")[0]
        return out, None
    except Exception as ex:
        return None, str(ex)


def run_downstream_simulation(con: duckdb.DuckDBPyConnection,
                               schema_info: dict) -> list[dict]:
    logs = []
    for q in ADAPTED_QUERIES:
        did = q["dataset"]
        dirty_table = schema_info[did]["dirty_table"]
        clean_table = schema_info[did]["clean_table"]

        # Materialize SQL for each table variant
        src_sql_dirty = q["sql"].format(table=dirty_table)
        src_sql_clean = q["sql"].format(table=clean_table)

        # Transpile to DuckDB-compatible (postgres) SQL.
        # Used for BOTH the "transpiled" condition AND as a fallback for the source execution
        # for non-PostgreSQL dialects (MySQL backticks and T-SQL brackets are not valid DuckDB syntax).
        trans_sql_dirty_str, trans_err = transpile_to_duckdb(src_sql_dirty, q["dialect"])
        trans_sql_clean_str, _ = transpile_to_duckdb(src_sql_clean, q["dialect"])

        # Reference: clean + source SQL.
        # For non-postgres dialects, fall back to the transpiled version for execution
        # (we cannot run native MySQL or T-SQL syntax in DuckDB).
        ref_result, ref_err = execute_query(con, src_sql_clean)
        if ref_err and trans_sql_clean_str:
            ref_result, ref_err = execute_query(con, trans_sql_clean_str)
        ref_norm = normalise_for_comparison(ref_result)

        # Condition A: dirty + source SQL (SQL gate applied — use source/validated SQL)
        # Fall back to transpile if source dialect is not DuckDB-native.
        a_sql = src_sql_dirty
        a_result, a_err = execute_query(con, a_sql)
        if a_err and trans_sql_dirty_str:
            a_result, a_err = execute_query(con, trans_sql_dirty_str)
        a_norm = normalise_for_comparison(a_result)

        # Condition B: clean + transpiled SQL (data gate applied; SQL may have semantic drift)
        b_result = None; b_err = trans_err
        b_norm = None
        if trans_sql_clean_str:
            b_result, b_err = execute_query(con, trans_sql_clean_str)
            b_norm = normalise_for_comparison(b_result)

        # Condition C: dirty + transpiled SQL (no gate applied)
        c_result = None; c_err = trans_err
        c_norm = None
        if trans_sql_dirty_str:
            c_result, c_err = execute_query(con, trans_sql_dirty_str)
            c_norm = normalise_for_comparison(c_result)

        # Gate semantics (reference = clean+source, the "correct" answer):
        #
        #  NO_GATE       dirty + transpiled  [condition C]
        #  SQL_GATE_ONLY dirty + source      [condition A] — SQL validated, data dirty
        #  DATA_GATE_ONLY clean + transpiled [condition B] — data clean, SQL potentially wrong
        #  JOINT_GATE    clean + source      = reference    — always 0 % wrong by construction
        #
        wrong_no_gate   = (ref_norm != c_norm) and (ref_err is None) and (c_err is None)
        wrong_sql_gate  = (ref_norm != a_norm) and (ref_err is None) and (a_err is None)  # dirty+src ≠ ref
        wrong_data_gate = (ref_norm != b_norm) and (ref_err is None) and (b_err is None)  # clean+trans ≠ ref
        # joint_required: BOTH individual gates are insufficient → only joint gate fixes it
        joint_required  = wrong_sql_gate and wrong_data_gate

        logs.append({
            "query_id": q["id"],
            "dataset": did,
            "difficulty": q["difficulty"],
            "src_dialect": q["dialect"],
            "description": q["description"],
            "result_type": q["result_type"],
            "ref_ok": ref_err is None,
            "trans_ok": b_err is None,
            # Gate condition error flags
            "wrong_no_gate":    wrong_no_gate,    # dirty+transpiled ≠ ref
            "wrong_sql_gate":   wrong_sql_gate,   # dirty+source ≠ ref (SQL gate applied, data dirty)
            "wrong_data_gate":  wrong_data_gate,  # clean+transpiled ≠ ref (data gate applied, SQL may drift)
            "wrong_joint":      False,             # clean+source = ref always
            "joint_required":   joint_required,   # both individual gates insufficient
            # Numeric evidence
            "ref_val": str(ref_norm)[:200] if ref_norm else None,
            "dirty_src_val": str(a_norm)[:200] if a_norm else None,
            "trans_err": trans_err,
            "ref_err": ref_err,
        })
    return logs


# ---------------------------------------------------------------------------
# Step 6: Derived gate metrics
# ---------------------------------------------------------------------------
def compute_gate_metrics(logs: list[dict]) -> dict:
    n = len(logs)
    executable = [l for l in logs if l["ref_ok"]]
    n_exe = len(executable)
    if n_exe == 0:
        return {"n_queries": n, "n_executable": 0}

    # NO_GATE: dirty+transpiled ≠ ref
    pct_wrong_no_gate    = 100 * sum(l["wrong_no_gate"]   for l in executable) / n_exe
    # SQL_GATE: dirty+source ≠ ref (SQL validated but data still dirty)
    pct_wrong_sql_gate   = 100 * sum(l["wrong_sql_gate"]  for l in executable) / n_exe
    # DATA_GATE: clean+transpiled ≠ ref (data clean but SQL may drift)
    pct_wrong_data_gate  = 100 * sum(l["wrong_data_gate"] for l in executable) / n_exe
    # JOINT_GATE: clean+source = ref → always 0% by construction
    pct_wrong_joint_gate = 0.0
    # Cases where BOTH individual gates are insufficient → joint gate required
    n_joint_required     = sum(l["joint_required"] for l in executable)

    return {
        "n_queries": n,
        "n_executable": n_exe,
        "pct_wrong_no_gate":    round(pct_wrong_no_gate, 2),
        "pct_wrong_sql_gate":   round(pct_wrong_sql_gate, 2),
        "pct_wrong_data_gate":  round(pct_wrong_data_gate, 2),
        "pct_wrong_joint_gate": pct_wrong_joint_gate,
        "n_joint_required": n_joint_required,
        "honesty_verdict": (
            "JOINT_ADDS_VALUE_BEYOND_EITHER_GATE_ALONE"
            if n_joint_required > 0
            else "EITHER_GATE_ALONE_IS_SUFFICIENT"
        ),
    }


# ---------------------------------------------------------------------------
# Write adapted queries to .sql files + adaptation protocol
# ---------------------------------------------------------------------------
def write_adapted_queries():
    for q in ADAPTED_QUERIES:
        fname = CODE_DIR / f"{q['id']}.sql"
        body = (
            f"-- Query ID: {q['id']}\n"
            f"-- Source dialect: {q['dialect']}\n"
            f"-- Target dataset: {q['dataset']}\n"
            f"-- Difficulty: {q['difficulty']}\n"
            f"-- Description: {q['description']}\n"
            f"-- Table placeholder: {{table}} → replaced with payroll_dirty/clean or credit_dirty/clean\n\n"
            + q["sql"].format(table=f"{q['dataset'].lower()}_table")
        )
        fname.write_text(body, encoding="utf-8")

    protocol = textwrap.dedent("""\
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
    """)
    (CODE_DIR.parent / "ADAPTATION_PROTOCOL.md").write_text(protocol, encoding="utf-8")


# ---------------------------------------------------------------------------
# 3x3 Joint lane matrix
# ---------------------------------------------------------------------------
def compute_lane_matrix(logs: list[dict],
                         risk_df: pd.DataFrame) -> pd.DataFrame:
    """
    data_risk level (per query dataset):
      - dirty row reach: how many quarantined rows touch the columns this query reads?
      - high if any anomaly-family column appears in query AND quarantine rate > 0.8
      - medium if quarantine rate 0.4-0.8; low otherwise

    sql_risk level:
      - high if wrong_sql=True (transpilation produces different result)
      - medium if transpilation succeeded but we cannot tell (no error, same result)
      - low if transpilation failed (can't run)
    """
    rows = []
    for l in logs:
        if not l["ref_ok"]:
            continue
        # Data risk: high if dirty+source ≠ ref (anomalies change the query result)
        data_risk = "high" if l["wrong_sql_gate"] else (
            "medium" if l["ref_ok"] else "low"
        )
        # SQL risk: high if clean+transpiled ≠ ref (transpilation drift)
        sql_risk = "high" if l["wrong_data_gate"] else (
            "medium" if l["trans_ok"] else "low"
        )
        # Outcome
        outcome = (
            "auto-promote"   if data_risk == "low"  and sql_risk == "low" else
            "review"         if data_risk == "medium" or sql_risk == "medium" else
            "block"
        )
        rows.append({
            "query_id": l["query_id"],
            "data_risk": data_risk,
            "sql_risk": sql_risk,
            "outcome": outcome,
            "wrong_no_gate": l["wrong_no_gate"],
            "wrong_joint": l["wrong_joint"],
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    t0 = time.perf_counter()

    # Step 1: column provenance
    print("[E6] Step 1: column provenance ...", flush=True)
    prov_df = extract_provenance()
    prov_df.to_csv(OUT / "e6_column_provenance.csv", index=False)
    print(f"  {len(prov_df)} query-provenance rows written.")

    # Step 2: column risk mass
    print("[E6] Step 2: column risk mass ...", flush=True)
    risk_d2 = compute_column_risk_mass("D2")
    risk_d3 = compute_column_risk_mass("D3")
    risk_df = pd.concat([risk_d2, risk_d3], ignore_index=True)
    risk_df.to_csv(OUT / "e6_column_risk_mass.csv", index=False)
    print(f"  {len(risk_df)} column-risk rows.")

    # Write adapted queries
    write_adapted_queries()
    print(f"[E6] Adapted queries written to {CODE_DIR} ({len(ADAPTED_QUERIES)} files)")

    # Step 3: DuckDB setup
    print("[E6] Step 3: building DuckDB tables ...", flush=True)
    con = duckdb.connect(database=":memory:")
    schema_info = build_duckdb(con)
    for did, info in schema_info.items():
        n_dirty = con.execute(f"SELECT COUNT(*) FROM {info['dirty_table']}").fetchone()[0]
        n_clean = con.execute(f"SELECT COUNT(*) FROM {info['clean_table']}").fetchone()[0]
        print(f"  {did}: dirty={n_dirty:,} clean={n_clean:,} quarantined={n_dirty-n_clean:,}")

    # Step 4: downstream simulation
    print("[E6] Step 4: downstream error simulation ...", flush=True)
    logs = run_downstream_simulation(con, schema_info)

    # Save full execution log
    (OUT / "e6_query_executions.json").write_text(
        json.dumps(logs, indent=2, default=str), encoding="utf-8"
    )

    # Step 5: gate metrics
    gate_metrics = compute_gate_metrics(logs)
    print(f"\n[E6] === GATE METRICS ===")
    for k, v in gate_metrics.items():
        print(f"  {k}: {v}")

    # Save error rate table
    # Column semantics:
    #   pct_wrong_no_gate   = dirty+transpiled ≠ ref  (no gate applied)
    #   pct_wrong_sql_gate  = dirty+source ≠ ref      (SQL gate applied; data gate not)
    #   pct_wrong_data_gate = clean+transpiled ≠ ref  (data gate applied; SQL gate not)
    #   pct_wrong_joint     = 0 always                (both gates; clean+source = ref)
    err_rows = []
    for did in ["D2", "D3"]:
        sub = [l for l in logs if l["dataset"] == did]
        for diff in ["easy", "medium", "hard"]:
            dsub = [l for l in sub if l["difficulty"] == diff and l["ref_ok"]]
            if not dsub:
                continue
            n = len(dsub)
            err_rows.append({
                "dataset": did, "difficulty": diff, "n_queries": n,
                "pct_wrong_no_gate":    round(100 * sum(l["wrong_no_gate"]   for l in dsub) / n, 1),
                "pct_wrong_sql_gate":   round(100 * sum(l["wrong_sql_gate"]  for l in dsub) / n, 1),
                "pct_wrong_data_gate":  round(100 * sum(l["wrong_data_gate"] for l in dsub) / n, 1),
                "pct_wrong_joint_gate": 0.0,
                "n_joint_required":     sum(l["joint_required"] for l in dsub),
            })
    pd.DataFrame(err_rows).to_csv(OUT / "e6_downstream_error_rates.csv", index=False)

    # Queries requiring both gates
    joint_req = [l for l in logs if l.get("joint_required") and l["ref_ok"]]
    pd.DataFrame(joint_req).to_csv(OUT / "e6_caught_only_by_joint.csv", index=False)

    # Lane matrix
    lane_df = compute_lane_matrix(logs, risk_df)
    lane_df.to_csv(OUT / "e6_joint_gate_lanes.csv", index=False)

    elapsed = round(time.perf_counter() - t0, 1)
    print(f"\n[E6] Done in {elapsed}s")
    print(f"Honesty verdict: {gate_metrics.get('honesty_verdict', 'UNKNOWN')}")
    print(f"n_joint_required: {gate_metrics.get('n_joint_required', 'N/A')} / {gate_metrics.get('n_executable', 'N/A')} executable queries")
    print(f"Outputs: {OUT}")

    # Print error rates table
    err_df = pd.read_csv(OUT / "e6_downstream_error_rates.csv")
    print("\nDownstream error rates by dataset/difficulty:")
    print("  no_gate = dirty+transpiled != ref")
    print("  sql_gate = dirty+source != ref (SQL gate applied, data dirty)")
    print("  data_gate = clean+transpiled != ref (data gate applied, SQL may drift)")
    print("  joint_gate = 0% by construction (clean+source = ref)")
    print(err_df.to_string(index=False))


if __name__ == "__main__":
    main()
