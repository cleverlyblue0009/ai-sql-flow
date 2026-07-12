"""
F1: Joint gate redesign — TRUE pre-injection reference.

CRITICAL FIX over Round-1 E6
------------------------------
E6 defined the reference as (cleansed, source SQL) — the identical pair that the
joint gate produces.  pct_wrong_joint_gate was hardcoded to 0.0 and wrong_joint
was set to False unconditionally.  This is a circular assignment, not a measurement.

This script defines:
  REFERENCE = query(TRUE_TABLE, SOURCE_SQL)
  TRUE_TABLE = pre-injection parquet — D2: 200k rows, D3: 30k rows

Now all four gate conditions are measurable:

  CONDITION               DATA         SQL          TABLE in DuckDB
  -----------------------------------------------------------------------
  (0) REFERENCE           true         source       payroll_true / credit_true
  (1) TRUE+transpiled     true         transpiled   payroll_true / credit_true
  (2) SQL_GATE (no data)  dirty        source       payroll_dirty / credit_dirty
  (3) NO_GATE             dirty        transpiled   payroll_dirty / credit_dirty
  (4) JOINT_GATE          cleansed     source       payroll_clean / credit_clean
  (5) DATA_GATE           cleansed     transpiled   payroll_clean / credit_clean

  "Transpiled" = postgres → tsql (sqlglot) → duckdb (sqlglot).
  Known drift sources: ::numeric casts, EXTRACT, NULLS LAST, ILIKE.

  Reference is INDEPENDENT of the gate being evaluated.
  joint_gate error is now a measurement, not an assignment.

QUERY STRATA
  targeted  (n=20): queries that read anomaly-injected columns
  control   (n=15): queries that read ONLY columns never perturbed by any injection

COMPARISON RULE (stated explicitly, enforced throughout)
  Scalars  : abs(a - b) <= max(1e-4, 1e-6 * |ref|) → "within_float_tolerance" (NOT counted as error)
  Row-sets : sort rows, compare normalised string; row-count differences classified separately
  The tolerance avoids classifying 1-ULP float noise as a downstream data error.

OUTPUTS (rebuttal_artifacts/round2/f1_joint_gate/)
  f1_per_query_six_conditions.csv   — full per-query result for all 6 conditions
  f1_downstream_error_rates.csv     — gate error rates by stratum (targeted / control)
  f1_joint_required_queries.md      — queries where BOTH single gates fail, joint gate succeeds
  f1_control_vs_targeted_strata.csv — summary by stratum
  f1_query_executions.json          — full persisted results for every condition of every query
  F1_JOINT_GATE_REPORT.md           — narrative report
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import sqlglot

REPO   = Path(__file__).resolve().parents[2]
PROC   = REPO / "phase2_rebuild" / "data" / "processed"
LABELS = REPO / "phase2_rebuild" / "data" / "labels"
SCORES = REPO / "phase2_rebuild" / "results" / "scores"
TABLES = REPO / "phase2_rebuild" / "results" / "tables"
ROUND2 = REPO / "rebuttal_artifacts" / "round2" / "f1_joint_gate"
ROUND2.mkdir(parents=True, exist_ok=True)

BASELINE_CSV = TABLES / "baseline.csv"
FLOAT_TOL    = 1e-4   # absolute tolerance; comparison rule stated in docstring above

# ---------------------------------------------------------------------------
# Query corpus — 35 queries across two strata
#
# Columns perturbed by injection (NEVER appear in control queries):
#   D2: Total_OT_Paid (B1), Regular_Gross_Paid (B2/B5), Title_Description (B4)
#         * B3 adds near-duplicate rows — perturbs row-count but no specific column
#   D3: EDUCATION (C1), LIMIT_BAL (C2), BILL_AMT1 (C3), PAY_0 (C4), AGE (C5)
#
# SAFE columns (control queries only touch these):
#   D2: Agency_Name, Work_Location_Borough, Pay_Basis, Regular_Hours,
#       Total_Other_Pay, Fiscal_Year, OT_Hours, Leave_Status_as_of_June_30
#       ** Note: even safe-column aggregates on D2 differ between true and dirty
#          because B3 added 2,000 extra rows.  This is EXPECTED and REPORTED.
#   D3: SEX, MARRIAGE, PAY_2–PAY_6, BILL_AMT2–BILL_AMT6, PAY_AMT1–PAY_AMT6,
#       default_payment_next_month
# ---------------------------------------------------------------------------

# Each entry: id, dataset, stratum, dialect, sql_template, result_type, uses_postgres_specific
# {table} is replaced at runtime with the appropriate DuckDB table name.
# "dialect" is the source dialect for transpilation; "source" execution = direct DuckDB exec
# (DuckDB is mostly postgres-compatible; postgres-specific syntax is noted in uses_pg_syntax).

QUERIES: list[dict] = [

    # =========================================================================
    # TARGETED — D2 (touch Total_OT_Paid, Regular_Gross_Paid, Title_Description)
    # =========================================================================
    {
        "id": "T01", "dataset": "D2", "stratum": "targeted", "dialect": "postgres",
        "description": "Total OT pay across all employees",
        "sql": 'SELECT ROUND(SUM("Total_OT_Paid"::numeric), 2) AS total_ot FROM {table}',
        "result_type": "scalar", "uses_pg_syntax": True,
    },
    {
        "id": "T02", "dataset": "D2", "stratum": "targeted", "dialect": "postgres",
        "description": "Count employees with OT pay and zero regular hours",
        "sql": 'SELECT COUNT(*) AS n FROM {table} WHERE "Total_OT_Paid" > 0 AND "Regular_Hours" = 0',
        "result_type": "scalar", "uses_pg_syntax": False,
    },
    {
        "id": "T03", "dataset": "D2", "stratum": "targeted", "dialect": "postgres",
        "description": "Average regular gross pay (affected by B2/B5 injections)",
        "sql": 'SELECT ROUND(AVG("Regular_Gross_Paid"::numeric), 2) AS avg_gross FROM {table}',
        "result_type": "scalar", "uses_pg_syntax": True,
    },
    {
        "id": "T04", "dataset": "D2", "stratum": "targeted", "dialect": "postgres",
        "description": "Count employees with gross pay above 200k (magnitude outlier threshold)",
        "sql": 'SELECT COUNT(*) AS n FROM {table} WHERE "Regular_Gross_Paid" > 200000',
        "result_type": "scalar", "uses_pg_syntax": False,
    },
    {
        "id": "T05", "dataset": "D2", "stratum": "targeted", "dialect": "postgres",
        "description": "Top-5 agencies by total OT pay",
        "sql": ('SELECT "Agency_Name", ROUND(SUM("Total_OT_Paid"::numeric), 2) AS agency_ot '
                'FROM {table} GROUP BY "Agency_Name" '
                'ORDER BY agency_ot DESC NULLS LAST LIMIT 5'),
        "result_type": "table", "uses_pg_syntax": True,
    },
    {
        "id": "T06", "dataset": "D2", "stratum": "targeted", "dialect": "postgres",
        "description": "OT-to-gross ratio across all employees",
        "sql": ('SELECT ROUND(SUM("Total_OT_Paid"::numeric) / '
                'NULLIF(SUM("Regular_Gross_Paid"::numeric), 0), 4) AS ot_ratio FROM {table}'),
        "result_type": "scalar", "uses_pg_syntax": True,
    },
    {
        "id": "T07", "dataset": "D2", "stratum": "targeted", "dialect": "postgres",
        "description": "Average gross pay per title, top-10 by avg (ILIKE filter)",
        "sql": ('SELECT "Title_Description", ROUND(AVG("Regular_Gross_Paid"::numeric), 2) AS avg_gp '
                'FROM {table} WHERE "Title_Description" ILIKE \'%ANALYST%\' '
                'GROUP BY "Title_Description" ORDER BY avg_gp DESC NULLS LAST LIMIT 10'),
        "result_type": "table", "uses_pg_syntax": True,
    },
    {
        "id": "T08", "dataset": "D2", "stratum": "targeted", "dialect": "postgres",
        "description": "Count distinct title descriptions (B4 creates new titles)",
        "sql": 'SELECT COUNT(DISTINCT "Title_Description") AS n_titles FROM {table}',
        "result_type": "scalar", "uses_pg_syntax": False,
    },
    {
        "id": "T09", "dataset": "D2", "stratum": "targeted", "dialect": "postgres",
        "description": "Percentile-90 of regular gross pay",
        "sql": 'SELECT ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY "Regular_Gross_Paid"), 2) AS p90 FROM {table}',
        "result_type": "scalar", "uses_pg_syntax": True,
    },
    {
        "id": "T10", "dataset": "D2", "stratum": "targeted", "dialect": "postgres",
        "description": "Window-rank of total OT pay per agency",
        "sql": ('SELECT "Agency_Name", SUM("Total_OT_Paid"::numeric) AS agency_ot, '
                'RANK() OVER (ORDER BY SUM("Total_OT_Paid"::numeric) DESC NULLS LAST) AS rnk '
                'FROM {table} GROUP BY "Agency_Name" ORDER BY rnk LIMIT 5'),
        "result_type": "table", "uses_pg_syntax": True,
    },

    # =========================================================================
    # TARGETED — D3 (touch EDUCATION, LIMIT_BAL, BILL_AMT1, PAY_0, AGE)
    # =========================================================================
    {
        "id": "T11", "dataset": "D3", "stratum": "targeted", "dialect": "postgres",
        "description": "Education distribution (C1 creates out-of-domain value 7)",
        "sql": 'SELECT "EDUCATION", COUNT(*) AS n FROM {table} GROUP BY "EDUCATION" ORDER BY "EDUCATION"',
        "result_type": "table", "uses_pg_syntax": False,
    },
    {
        "id": "T12", "dataset": "D3", "stratum": "targeted", "dialect": "postgres",
        "description": "Count of invalid EDUCATION codes (outside 1-6)",
        "sql": 'SELECT COUNT(*) AS n_invalid FROM {table} WHERE "EDUCATION" NOT IN (1, 2, 3, 4, 5, 6)',
        "result_type": "scalar", "uses_pg_syntax": False,
    },
    {
        "id": "T13", "dataset": "D3", "stratum": "targeted", "dialect": "postgres",
        "description": "Average credit limit (C2 modifies LIMIT_BAL)",
        "sql": 'SELECT ROUND(AVG("LIMIT_BAL"::numeric), 2) AS avg_limit FROM {table}',
        "result_type": "scalar", "uses_pg_syntax": True,
    },
    {
        "id": "T14", "dataset": "D3", "stratum": "targeted", "dialect": "postgres",
        "description": "Count of outlier credit limits (> 500k, from C2)",
        "sql": 'SELECT COUNT(*) AS n_outlier FROM {table} WHERE "LIMIT_BAL" > 500000',
        "result_type": "scalar", "uses_pg_syntax": False,
    },
    {
        "id": "T15", "dataset": "D3", "stratum": "targeted", "dialect": "postgres",
        "description": "Count of negative BILL_AMT1 (C3 flips sign)",
        "sql": 'SELECT COUNT(*) AS n_neg FROM {table} WHERE "BILL_AMT1" < 0',
        "result_type": "scalar", "uses_pg_syntax": False,
    },
    {
        "id": "T16", "dataset": "D3", "stratum": "targeted", "dialect": "postgres",
        "description": "Sum of BILL_AMT1 (C3 flips sign, inflating negative sum)",
        "sql": 'SELECT ROUND(SUM("BILL_AMT1"::numeric), 2) AS sum_bill1 FROM {table}',
        "result_type": "scalar", "uses_pg_syntax": True,
    },
    {
        "id": "T17", "dataset": "D3", "stratum": "targeted", "dialect": "postgres",
        "description": "Count of anomalous pay statuses (PAY_0 outside -2 to 8)",
        "sql": 'SELECT COUNT(*) AS n_bad_pay FROM {table} WHERE "PAY_0" > 8',
        "result_type": "scalar", "uses_pg_syntax": False,
    },
    {
        "id": "T18", "dataset": "D3", "stratum": "targeted", "dialect": "postgres",
        "description": "Average age (C5 introduces age-range violations)",
        "sql": 'SELECT ROUND(AVG("AGE"::numeric), 2) AS avg_age FROM {table}',
        "result_type": "scalar", "uses_pg_syntax": True,
    },
    {
        "id": "T19", "dataset": "D3", "stratum": "targeted", "dialect": "postgres",
        "description": "Count of out-of-range ages (C5: < 18 or > 100)",
        "sql": 'SELECT COUNT(*) AS n_bad_age FROM {table} WHERE "AGE" < 18 OR "AGE" > 100',
        "result_type": "scalar", "uses_pg_syntax": False,
    },
    {
        "id": "T20", "dataset": "D3", "stratum": "targeted", "dialect": "postgres",
        "description": "Credit limit avg by education (combined targeted columns)",
        "sql": ('SELECT "EDUCATION", ROUND(AVG("LIMIT_BAL"::numeric), 2) AS avg_lim '
                'FROM {table} GROUP BY "EDUCATION" ORDER BY "EDUCATION"'),
        "result_type": "table", "uses_pg_syntax": True,
    },

    # =========================================================================
    # CONTROL — D2 (ONLY safe columns; never perturbed by any injection)
    # NOTE: COUNT(*) and SUM aggregates on D2 WILL differ between true and dirty
    # because B3 adds 2,000 near-duplicate rows.  This is expected and honest.
    # =========================================================================
    {
        "id": "C01", "dataset": "D2", "stratum": "control", "dialect": "postgres",
        "description": "Count distinct agencies (B3 adds rows with existing agencies)",
        "sql": 'SELECT COUNT(DISTINCT "Agency_Name") AS n_agencies FROM {table}',
        "result_type": "scalar", "uses_pg_syntax": False,
    },
    {
        "id": "C02", "dataset": "D2", "stratum": "control", "dialect": "postgres",
        "description": "Work borough distribution",
        "sql": ('SELECT "Work_Location_Borough", COUNT(*) AS n FROM {table} '
                'GROUP BY "Work_Location_Borough" ORDER BY n DESC'),
        "result_type": "table", "uses_pg_syntax": False,
    },
    {
        "id": "C03", "dataset": "D2", "stratum": "control", "dialect": "postgres",
        "description": "Pay basis distribution",
        "sql": ('SELECT "Pay_Basis", COUNT(*) AS n FROM {table} '
                'GROUP BY "Pay_Basis" ORDER BY "Pay_Basis"'),
        "result_type": "table", "uses_pg_syntax": False,
    },
    {
        "id": "C04", "dataset": "D2", "stratum": "control", "dialect": "postgres",
        "description": "Average regular hours (not a perturbed column)",
        "sql": 'SELECT ROUND(AVG("Regular_Hours"::numeric), 4) AS avg_hours FROM {table}',
        "result_type": "scalar", "uses_pg_syntax": True,
    },
    {
        "id": "C05", "dataset": "D2", "stratum": "control", "dialect": "postgres",
        "description": "Total other pay (not a perturbed column)",
        "sql": 'SELECT ROUND(SUM("Total_Other_Pay"::numeric), 2) AS total_other FROM {table}',
        "result_type": "scalar", "uses_pg_syntax": True,
    },
    {
        "id": "C06", "dataset": "D2", "stratum": "control", "dialect": "postgres",
        "description": "Average OT hours (not a perturbed column)",
        "sql": 'SELECT ROUND(AVG("OT_Hours"::numeric), 4) AS avg_ot_hrs FROM {table}',
        "result_type": "scalar", "uses_pg_syntax": True,
    },
    {
        "id": "C07", "dataset": "D2", "stratum": "control", "dialect": "postgres",
        "description": "Count active employees (Leave Status — safe column)",
        "sql": 'SELECT COUNT(*) AS n_active FROM {table} WHERE "Leave_Status_as_of_June_30" = \'ACTIVE\'',
        "result_type": "scalar", "uses_pg_syntax": False,
    },
    {
        "id": "C08", "dataset": "D2", "stratum": "control", "dialect": "postgres",
        "description": "Agency regular hours ranking (window function, safe columns only)",
        "sql": ('SELECT "Agency_Name", ROUND(AVG("Regular_Hours"::numeric), 4) AS avg_hrs, '
                'RANK() OVER (ORDER BY AVG("Regular_Hours"::numeric) DESC NULLS LAST) AS rnk '
                'FROM {table} GROUP BY "Agency_Name" ORDER BY rnk LIMIT 10'),
        "result_type": "table", "uses_pg_syntax": True,
    },

    # =========================================================================
    # CONTROL — D3 (ONLY safe columns: SEX, MARRIAGE, BILL_AMT2-6, PAY_AMT1-6, default)
    # D3 is all in-place modification (same 30k rows), so safe columns will be
    # IDENTICAL between true and dirty.  Data gate errors for control queries
    # here are PURELY from FP quarantine by the detector.
    # =========================================================================
    {
        "id": "C09", "dataset": "D3", "stratum": "control", "dialect": "postgres",
        "description": "Sex distribution (safe column)",
        "sql": 'SELECT "SEX", COUNT(*) AS n FROM {table} GROUP BY "SEX" ORDER BY "SEX"',
        "result_type": "table", "uses_pg_syntax": False,
    },
    {
        "id": "C10", "dataset": "D3", "stratum": "control", "dialect": "postgres",
        "description": "Marriage status distribution (safe column)",
        "sql": 'SELECT "MARRIAGE", COUNT(*) AS n FROM {table} GROUP BY "MARRIAGE" ORDER BY "MARRIAGE"',
        "result_type": "table", "uses_pg_syntax": False,
    },
    {
        "id": "C11", "dataset": "D3", "stratum": "control", "dialect": "postgres",
        "description": "Average BILL_AMT2 (safe column, not perturbed)",
        "sql": 'SELECT ROUND(AVG("BILL_AMT2"::numeric), 2) AS avg_bill2 FROM {table}',
        "result_type": "scalar", "uses_pg_syntax": True,
    },
    {
        "id": "C12", "dataset": "D3", "stratum": "control", "dialect": "postgres",
        "description": "Sum of PAY_AMT1 (safe column, not perturbed)",
        "sql": 'SELECT ROUND(SUM("PAY_AMT1"::numeric), 2) AS sum_pay1 FROM {table}',
        "result_type": "scalar", "uses_pg_syntax": True,
    },
    {
        "id": "C13", "dataset": "D3", "stratum": "control", "dialect": "postgres",
        "description": "Default payment distribution (safe column)",
        "sql": ('SELECT "default_payment_next_month", COUNT(*) AS n FROM {table} '
                'GROUP BY "default_payment_next_month" ORDER BY "default_payment_next_month"'),
        "result_type": "table", "uses_pg_syntax": False,
    },
    {
        "id": "C14", "dataset": "D3", "stratum": "control", "dialect": "postgres",
        "description": "Average PAY_AMT3 (safe column)",
        "sql": 'SELECT ROUND(AVG("PAY_AMT3"::numeric), 2) AS avg_pay3 FROM {table}',
        "result_type": "scalar", "uses_pg_syntax": True,
    },
    {
        "id": "C15", "dataset": "D3", "stratum": "control", "dialect": "postgres",
        "description": "Count long delinquent PAY_2 statuses (PAY_2 safe: not perturbed)",
        "sql": 'SELECT COUNT(*) AS n_delin FROM {table} WHERE "PAY_2" >= 2',
        "result_type": "scalar", "uses_pg_syntax": False,
    },
]

assert len(QUERIES) == 35, f"Expected 35 queries, got {len(QUERIES)}"
assert sum(1 for q in QUERIES if q["stratum"] == "targeted") == 20
assert sum(1 for q in QUERIES if q["stratum"] == "control")  == 15


# ---------------------------------------------------------------------------
# SQL transpilation: postgres → tsql → duckdb (2-hop)
# ---------------------------------------------------------------------------
def transpile_2hop(sql: str) -> tuple[str | None, str | None]:
    """
    Transpile postgres → tsql, then tsql → duckdb.
    Returns (duckdb_sql, error_msg).
    The 2-hop is intentional: postgres-specific syntax (::numeric, ILIKE,
    NULLS LAST, PERCENTILE_CONT WITHIN GROUP) may survive 1-hop but is
    known to drift in 2-hop transpilation.
    """
    try:
        tsql = sqlglot.transpile(sql, read="postgres", write="tsql")[0]
    except Exception as ex:
        return None, f"pg→tsql failed: {ex}"
    try:
        dkdb = sqlglot.transpile(tsql, read="tsql", write="duckdb")[0]
        return dkdb, None
    except Exception as ex:
        return None, f"tsql→duckdb failed: {ex}"


# ---------------------------------------------------------------------------
# Query execution
# ---------------------------------------------------------------------------
def run_query(con: duckdb.DuckDBPyConnection, sql: str) -> tuple[object | None, str | None]:
    try:
        res = con.execute(sql).fetchall()
        return res, None
    except Exception as ex:
        return None, str(ex)


# ---------------------------------------------------------------------------
# Tolerance-aware result comparison
# ---------------------------------------------------------------------------
def _to_float(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def normalise_value(v) -> str:
    """Normalise a single cell for string comparison."""
    if v is None:
        return "NULL"
    f = _to_float(v)
    if f is not None:
        # Round to 4 sig-figs to avoid float-noise mismatches in string comparison
        return f"{round(f, 4)}"
    return str(v).strip().lower()


def normalise_result(rows) -> str | None:
    """Convert query result rows to a canonical string for comparison."""
    if rows is None:
        return None
    if len(rows) == 0:
        return "EMPTY"
    normed = sorted(["|".join(normalise_value(v) for v in row) for row in rows])
    return "\n".join(normed)


def compare_results(ref_rows, cand_rows, tol: float = FLOAT_TOL) -> dict:
    """
    Compare candidate result against reference.

    Returns a dict with:
      verdict : 'match' | 'within_float_tolerance' | 'value_diff' | 'row_count_diff'
                 | 'cand_error' | 'ref_error' | 'both_error'
      is_error: bool  (True only for value_diff / row_count_diff)
      delta   : float | None
    """
    if ref_rows is None and cand_rows is None:
        return {"verdict": "both_error", "is_error": False, "delta": None}
    if ref_rows is None:
        return {"verdict": "ref_error",  "is_error": False, "delta": None}
    if cand_rows is None:
        return {"verdict": "cand_error", "is_error": True,  "delta": None}

    if len(ref_rows) != len(cand_rows):
        return {"verdict": "row_count_diff", "is_error": True,
                "delta": len(cand_rows) - len(ref_rows)}

    # Scalar case: single cell
    if len(ref_rows) == 1 and len(ref_rows[0]) == 1:
        rv = _to_float(ref_rows[0][0])
        cv = _to_float(cand_rows[0][0])
        if rv is not None and cv is not None:
            delta = abs(rv - cv)
            thresh = max(tol, 1e-6 * abs(rv))
            if delta <= thresh:
                return {"verdict": "within_float_tolerance", "is_error": False, "delta": delta}
            return {"verdict": "value_diff", "is_error": True, "delta": delta}

    # Multi-row / multi-col: normalised string comparison
    ref_norm  = normalise_result(ref_rows)
    cand_norm = normalise_result(cand_rows)
    if ref_norm == cand_norm:
        return {"verdict": "match", "is_error": False, "delta": None}
    return {"verdict": "value_diff", "is_error": True, "delta": None}


# ---------------------------------------------------------------------------
# Database setup: six tables per dataset
# ---------------------------------------------------------------------------
def build_duckdb(con: duckdb.DuckDBPyConnection) -> dict:
    """
    Creates six tables in DuckDB:
      payroll_true    — D2 pre-injection (200k rows)
      payroll_dirty   — D2 injected (202k rows)
      payroll_clean   — D2 injected minus quarantined rows (hybrid_lr >= tau)
      credit_true     — D3 pre-injection (30k rows)
      credit_dirty    — D3 injected (30k rows)
      credit_clean    — D3 injected minus quarantined rows

    Column names: spaces → underscores, slashes → underscores, parens removed.
    Returns schema_info dict: {did: {true_t, dirty_t, clean_t, n_true, n_dirty, n_clean, tau}}
    """
    bl = pd.read_csv(BASELINE_CSV)
    info = {}

    for did, true_f, inj_f, mask_f in [
        ("D2", "D2_nyc_fy2024", "D2_injected", "D2"),
        ("D3", "D3_uci_credit", "D3_injected", "D3"),
    ]:
        # Load data
        df_true  = pd.read_parquet(PROC / f"{true_f}.parquet")
        df_dirty = pd.read_parquet(PROC / f"{inj_f}.parquet")
        sc       = pd.read_parquet(SCORES / f"{did}_scores.parquet")

        # Normalise column names for DuckDB
        def normalise_cols(df):
            df = df.copy()
            df.columns = [
                c.replace(" ", "_").replace("/", "_")
                 .replace("(", "").replace(")", "").replace("-", "_")
                for c in df.columns
            ]
            return df

        df_true  = normalise_cols(df_true)
        df_dirty = normalise_cols(df_dirty)

        # Cleansed = dirty rows NOT quarantined
        tau = float(bl[(bl["dataset"] == did) & (bl["detector"] == "hybrid_lr")]["best_threshold"].iloc[0])
        keep_mask = sc["hybrid_lr"].to_numpy() < tau
        df_clean  = df_dirty[keep_mask].reset_index(drop=True)

        prefix = "payroll" if did == "D2" else "credit"
        true_t  = f"{prefix}_true"
        dirty_t = f"{prefix}_dirty"
        clean_t = f"{prefix}_clean"

        for tname, df in [(true_t, df_true), (dirty_t, df_dirty), (clean_t, df_clean)]:
            con.execute(f"DROP TABLE IF EXISTS {tname}")
            con.register(f"_tmp_{tname}", df)
            con.execute(f"CREATE TABLE {tname} AS SELECT * FROM _tmp_{tname}")

        info[did] = {
            "true_t":  true_t,  "dirty_t": dirty_t, "clean_t": clean_t,
            "n_true":  len(df_true), "n_dirty": len(df_dirty), "n_clean": len(df_clean),
            "tau":     tau,
            "n_fp":    int((~keep_mask).sum()) - int((sc["y"] > 0.5).sum()),
            "n_fn":    int((sc["y"] > 0.5).sum()) - int(keep_mask[sc["y"].to_numpy() > 0.5].sum() == 0),
        }
        print(f"  {did}: true={len(df_true):,}  dirty={len(df_dirty):,}  "
              f"clean={len(df_clean):,}  tau={tau:.5f}  "
              f"quarantined={int((~keep_mask).sum()):,}  n_pos={int((sc['y']>0.5).sum()):,}")

    return info


# ---------------------------------------------------------------------------
# Per-query six-condition simulation
# ---------------------------------------------------------------------------
def simulate(con: duckdb.DuckDBPyConnection, schema: dict) -> tuple[list[dict], list[dict]]:
    """
    For each query, execute in 6 conditions and compare to reference.

    Returns (per_query_rows, execution_log_entries).
    per_query_rows is suitable for CSV; execution_log_entries for JSON.
    """
    per_query = []
    exec_log  = []

    for q in QUERIES:
        did   = q["dataset"]
        si    = schema[did]
        true_t  = si["true_t"]
        dirty_t = si["dirty_t"]
        clean_t = si["clean_t"]

        # Build the six SQL variants
        sql_src_true  = q["sql"].format(table=true_t)
        sql_src_dirty = q["sql"].format(table=dirty_t)
        sql_src_clean = q["sql"].format(table=clean_t)

        trans_true,  trans_err_true  = transpile_2hop(sql_src_true)
        trans_dirty, trans_err_dirty = transpile_2hop(sql_src_dirty)
        trans_clean, trans_err_clean = transpile_2hop(sql_src_clean)

        # Execute all six
        def ex(sql, err_from_transpile=None):
            if err_from_transpile:
                return None, err_from_transpile
            return run_query(con, sql)

        r0, e0 = run_query(con, sql_src_true)              # (0) REFERENCE
        r1, e1 = ex(trans_true,  trans_err_true)           # (1) true + transpiled
        r2, e2 = run_query(con, sql_src_dirty)             # (2) SQL_GATE (dirty + source)
        r3, e3 = ex(trans_dirty, trans_err_dirty)          # (3) NO_GATE (dirty + transpiled)
        r4, e4 = run_query(con, sql_src_clean)             # (4) JOINT_GATE (clean + source)
        r5, e5 = ex(trans_clean, trans_err_clean)          # (5) DATA_GATE (clean + transpiled)

        # Compare all five against reference
        c1 = compare_results(r0, r1)
        c2 = compare_results(r0, r2)
        c3 = compare_results(r0, r3)
        c4 = compare_results(r0, r4)
        c5 = compare_results(r0, r5)

        # "joint required" = BOTH single gates wrong, but JOINT correct
        sql_gate_wrong  = c2["is_error"]
        data_gate_wrong = c5["is_error"]
        joint_wrong     = c4["is_error"]
        joint_required  = sql_gate_wrong and data_gate_wrong and not joint_wrong

        # Persist for JSON log (full result values)
        entry = {
            "query_id":    q["id"],
            "dataset":     did,
            "stratum":     q["stratum"],
            "description": q["description"],
            "uses_pg_syntax": q["uses_pg_syntax"],
            "transpile_err": {
                "true": trans_err_true, "dirty": trans_err_dirty, "clean": trans_err_clean
            },
            "conditions": {
                "C0_ref":        {"sql": sql_src_true,  "result": str(r0)[:500], "error": e0},
                "C1_true_trans": {"sql": str(trans_true)[:400], "result": str(r1)[:500], "error": e1,
                                  "verdict": c1["verdict"], "is_error": c1["is_error"]},
                "C2_sql_gate":   {"sql": sql_src_dirty, "result": str(r2)[:500], "error": e2,
                                  "verdict": c2["verdict"], "is_error": c2["is_error"]},
                "C3_no_gate":    {"sql": str(trans_dirty)[:400], "result": str(r3)[:500], "error": e3,
                                  "verdict": c3["verdict"], "is_error": c3["is_error"]},
                "C4_joint_gate": {"sql": sql_src_clean, "result": str(r4)[:500], "error": e4,
                                  "verdict": c4["verdict"], "is_error": c4["is_error"]},
                "C5_data_gate":  {"sql": str(trans_clean)[:400], "result": str(r5)[:500], "error": e5,
                                  "verdict": c5["verdict"], "is_error": c5["is_error"]},
            },
            "joint_required": joint_required,
        }
        exec_log.append(entry)

        per_query.append({
            "query_id":           q["id"],
            "dataset":            did,
            "stratum":            q["stratum"],
            "uses_pg_syntax":     q["uses_pg_syntax"],
            "description":        q["description"],
            "ref_ok":             e0 is None,
            # True+transpiled baseline
            "C1_true_trans_verdict":  c1["verdict"],
            "C1_is_error":            c1["is_error"],
            # SQL gate (dirty+source)
            "C2_sql_gate_verdict":    c2["verdict"],
            "C2_is_error":            c2["is_error"],
            # No gate (dirty+transpiled)
            "C3_no_gate_verdict":     c3["verdict"],
            "C3_is_error":            c3["is_error"],
            # Joint gate (clean+source)
            "C4_joint_gate_verdict":  c4["verdict"],
            "C4_is_error":            c4["is_error"],
            # Data gate (clean+transpiled)
            "C5_data_gate_verdict":   c5["verdict"],
            "C5_is_error":            c5["is_error"],
            # Summary
            "joint_required":         joint_required,
            "trans_ok":               trans_err_dirty is None,
        })

        # Progress print
        status = []
        if c2["is_error"]: status.append("SQL_GATE_WRONG")
        if c5["is_error"]: status.append("DATA_GATE_WRONG")
        if c4["is_error"]: status.append("JOINT_WRONG")
        if joint_required: status.append("JOINT_REQUIRED!")
        print(f"  {q['id']} [{q['stratum'][:3]}] {', '.join(status) if status else 'all_ok'}")

    return per_query, exec_log


# ---------------------------------------------------------------------------
# Gate error rate summary
# ---------------------------------------------------------------------------
def compute_gate_rates(per_query: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(per_query)
    rows = []
    for stratum in ["targeted", "control", "all"]:
        sub = df if stratum == "all" else df[df["stratum"] == stratum]
        n = len(sub)
        n_ref_ok = int(sub["ref_ok"].sum())
        ok = sub[sub["ref_ok"]]
        n_ok = len(ok)
        if n_ok == 0:
            continue
        rows.append({
            "stratum":                   stratum,
            "n_queries":                 n,
            "n_ref_executable":          n_ref_ok,
            # Condition 1: true+transpiled — measures SQL-only drift (baseline)
            "pct_wrong_true_trans":      round(100 * ok["C1_is_error"].sum() / n_ok, 1),
            # Condition 2: dirty+source (SQL_GATE_ONLY)
            "pct_wrong_sql_gate":        round(100 * ok["C2_is_error"].sum() / n_ok, 1),
            # Condition 3: dirty+transpiled (NO_GATE)
            "pct_wrong_no_gate":         round(100 * ok["C3_is_error"].sum() / n_ok, 1),
            # Condition 4: clean+source (JOINT_GATE)
            "pct_wrong_joint_gate":      round(100 * ok["C4_is_error"].sum() / n_ok, 1),
            # Condition 5: clean+transpiled (DATA_GATE)
            "pct_wrong_data_gate":       round(100 * ok["C5_is_error"].sum() / n_ok, 1),
            "n_joint_required":          int(ok["joint_required"].sum()),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Write joint-required narrative
# ---------------------------------------------------------------------------
def write_joint_required_md(per_query: list[dict], exec_log: list[dict], out_path: Path):
    df = pd.DataFrame(per_query)
    jr = df[df["joint_required"] == True]

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# F1: Queries Requiring Both Gates (Joint-Required Cases)\n\n")
        f.write(f"**Definition**: a query is 'joint-required' if:\n")
        f.write("- SQL gate alone is WRONG (dirty+source ≠ true reference)\n")
        f.write("- Data gate alone is WRONG (clean+transpiled ≠ true reference)\n")
        f.write("- Joint gate is CORRECT (clean+source = true reference)\n\n")

        if len(jr) == 0:
            f.write("## Result: 0 joint-required queries\n\n")
            f.write("No queries were found where BOTH single gates fail but the joint gate succeeds.\n\n")
            f.write("**Interpretation**: within this query corpus, the joint gate does not provide "
                    "additional error reduction beyond the better single gate.\n")
            return

        f.write(f"**Count**: {len(jr)} joint-required queries\n\n")
        for _, row in jr.iterrows():
            qid = row["query_id"]
            log = next((e for e in exec_log if e["query_id"] == qid), {})
            f.write(f"## {qid} — {row['description']}\n\n")
            f.write(f"- Dataset: {row['dataset']}, Stratum: {row['stratum']}\n")
            f.write(f"- Source SQL: `{log.get('conditions', {}).get('C0_ref', {}).get('sql', 'N/A')}`\n")
            ref_res  = log.get("conditions", {}).get("C0_ref", {}).get("result", "N/A")
            sql_res  = log.get("conditions", {}).get("C2_sql_gate", {}).get("result", "N/A")
            data_res = log.get("conditions", {}).get("C5_data_gate", {}).get("result", "N/A")
            join_res = log.get("conditions", {}).get("C4_joint_gate", {}).get("result", "N/A")
            f.write(f"\n| Condition | Result |\n|---|---|\n")
            f.write(f"| TRUE reference | `{ref_res[:120]}` |\n")
            f.write(f"| SQL gate (dirty+source) | `{sql_res[:120]}` |\n")
            f.write(f"| Data gate (clean+transpiled) | `{data_res[:120]}` |\n")
            f.write(f"| Joint gate (clean+source) | `{join_res[:120]}` |\n\n")
            f.write(f"**Error mechanism**: SQL gate fails because dirty data propagates; "
                    f"data gate fails because transpilation drift affects the cleansed result; "
                    f"joint gate succeeds because it combines clean data with source SQL.\n\n")


# ---------------------------------------------------------------------------
# Main report
# ---------------------------------------------------------------------------
def write_report(rates: pd.DataFrame, per_query_df: pd.DataFrame,
                 schema: dict, n_queries: int, elapsed: float, out: Path):
    targeted = rates[rates["stratum"] == "targeted"].iloc[0] if len(rates[rates["stratum"]=="targeted"]) else None
    control  = rates[rates["stratum"] == "control"].iloc[0]  if len(rates[rates["stratum"]=="control"]) else None
    overall  = rates[rates["stratum"] == "all"].iloc[0]      if len(rates[rates["stratum"]=="all"]) else None

    joint_val    = overall["pct_wrong_joint_gate"] if overall is not None else "N/A"
    sql_gate_val = overall["pct_wrong_sql_gate"]   if overall is not None else "N/A"
    data_gate_val= overall["pct_wrong_data_gate"]  if overall is not None else "N/A"
    no_gate_val  = overall["pct_wrong_no_gate"]    if overall is not None else "N/A"
    n_jr         = int(overall["n_joint_required"]) if overall is not None else 0
    better_single= min(float(sql_gate_val), float(data_gate_val)) if overall is not None else None
    joint_adds   = (float(joint_val) < better_single) if better_single is not None else False

    verdict_line = (
        f"YES — joint gate error ({joint_val}%) < better single gate ({better_single:.1f}%)"
        if joint_adds else
        f"NO — joint gate error ({joint_val}%) >= better single gate ({better_single:.1f}%)"
    )

    with open(out / "F1_JOINT_GATE_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# F1: Joint Gate — True Pre-Injection Reference Experiment\n\n")
        f.write("**Manuscript**: DataFlow AI — IEEE Access Access-2026-28181\n\n")
        f.write("---\n\n")
        f.write("## ONE-LINE VERDICT (R2.4 deciding comment)\n\n")
        f.write(f"**Does the joint gate provide measurable value over the better single gate? "
                f"{verdict_line}**\n\n")
        f.write("---\n\n")
        f.write("## Fix applied vs Round-1 E6\n\n")
        f.write("Round-1 (E6) defined the reference as (cleansed, source SQL) — identical to "
                "the joint gate output. `wrong_joint` was hardcoded to `False`; "
                "`pct_wrong_joint_gate = 0.0` was a literal assignment. This experiment "
                "replaces that with:\n\n")
        f.write("  **REFERENCE = query(TRUE_TABLE, SOURCE_SQL)**\n\n")
        f.write("  `TRUE_TABLE` = pre-injection parquet, independent of any gate.\n\n")
        f.write("All four gate error rates are now MEASUREMENTS, not assignments.\n\n")
        f.write("---\n\n")
        f.write("## Dataset context\n\n")
        for did in ["D2", "D3"]:
            si = schema[did]
            f.write(f"**{did}**: true={si['n_true']:,}  dirty={si['n_dirty']:,}  "
                    f"clean={si['n_clean']:,}  tau={si['tau']:.5f}  "
                    f"quarantined={si['n_dirty']-si['n_clean']:,} "
                    f"(~{100*(si['n_dirty']-si['n_clean'])/si['n_dirty']:.1f}% of rows)\n\n")
            f.write(f"  Note: quarantined > n_pos means false positives exist — "
                    f"joint gate will have non-zero error even from FP over-removal.\n\n")
        f.write("## Experimental design\n\n")
        f.write(f"- {n_queries} queries: 20 targeted (touch injected columns) + 15 control (safe columns only)\n")
        f.write("- 6 execution conditions per query:\n\n")
        f.write("  | Condition | Data | SQL | Gate |\n")
        f.write("  |---|---|---|---|\n")
        f.write("  | C0 | true | source | REFERENCE |\n")
        f.write("  | C1 | true | transpiled | SQL-only drift baseline |\n")
        f.write("  | C2 | dirty | source | SQL_GATE_ONLY |\n")
        f.write("  | C3 | dirty | transpiled | NO_GATE |\n")
        f.write("  | C4 | clean | source | JOINT_GATE |\n")
        f.write("  | C5 | clean | transpiled | DATA_GATE_ONLY |\n\n")
        f.write("- Transpilation: postgres → tsql → duckdb (2-hop via sqlglot)\n")
        f.write(f"- Float tolerance: abs(a-b) <= max({FLOAT_TOL}, 1e-6*|ref|) → "
                f"'within_float_tolerance' — NOT counted as error\n\n")
        f.write("## Gate error rates (all queries with executable reference)\n\n")
        f.write(rates.to_markdown(index=False) if hasattr(rates, "to_markdown") else rates.to_string(index=False))
        f.write("\n\n")
        f.write("## Strata comparison\n\n")
        f.write("- **Targeted queries** touch anomaly-injected columns; errors reflect both data corruption and detector imperfection.\n")
        f.write("- **Control queries** touch only safe columns; errors reflect detector FP over-removal and SQL transpilation drift.\n\n")
        if targeted is not None:
            f.write(f"| | Targeted | Control |\n|---|---|---|\n")
            f.write(f"| No gate wrong | {targeted['pct_wrong_no_gate']}% | {control['pct_wrong_no_gate'] if control is not None else 'N/A'}% |\n")
            f.write(f"| SQL gate wrong | {targeted['pct_wrong_sql_gate']}% | {control['pct_wrong_sql_gate'] if control is not None else 'N/A'}% |\n")
            f.write(f"| Data gate wrong | {targeted['pct_wrong_data_gate']}% | {control['pct_wrong_data_gate'] if control is not None else 'N/A'}% |\n")
            f.write(f"| Joint gate wrong | {targeted['pct_wrong_joint_gate']}% | {control['pct_wrong_joint_gate'] if control is not None else 'N/A'}% |\n")
            f.write(f"| Joint-required | {int(targeted['n_joint_required'])} | {int(control['n_joint_required']) if control is not None else 0} |\n\n")
        f.write("## Interpretation\n\n")
        f.write("### On the joint gate's value\n\n")
        if joint_adds:
            f.write(f"The joint gate's measured error rate ({joint_val}%) is lower than the best "
                    f"single gate ({better_single:.1f}%). The {n_jr} joint-required "
                    f"case(s) are those where neither single gate alone is sufficient.\n\n")
        else:
            f.write(f"The joint gate's measured error rate ({joint_val}%) is NOT lower than "
                    f"the best single gate ({better_single:.1f}%). "
                    f"Within this corpus, the joint gate does not provide additional "
                    f"error reduction beyond applying the better single gate alone.\n\n")
            f.write("**For the manuscript**: the paper should not claim the joint gate provides "
                    "error reduction beyond the best single gate. A defensible and honest "
                    "contribution is the UNIFIED PIPELINE DESIGN — shared data provenance, "
                    "reproducible audit trail, and a single deployment surface — rather than "
                    "a claim that coupling the two gates multiplicatively reduces error.\n\n")
        f.write("### On the detector's imperfection\n\n")
        f.write("The joint gate error reflects the detector's FP rate: rows that are CLEAN "
                "but flagged as anomalous are removed from the cleansed table, creating "
                "systematic bias in all aggregates even on safe columns. "
                "This is a measurement of the detector quality ceiling, not a gate design flaw.\n\n")
        f.write(f"---\n\nGenerated in {elapsed:.1f}s.  Outputs: rebuttal_artifacts/round2/f1_joint_gate/\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    t0 = time.perf_counter()
    print("[F1] Building DuckDB tables ...", flush=True)
    con = duckdb.connect(":memory:")
    schema = build_duckdb(con)

    print(f"[F1] Simulating {len(QUERIES)} queries × 6 conditions ...", flush=True)
    per_query, exec_log = simulate(con, schema)

    per_query_df = pd.DataFrame(per_query)
    per_query_df.to_csv(ROUND2 / "f1_per_query_six_conditions.csv", index=False)

    rates = compute_gate_rates(per_query)
    rates.to_csv(ROUND2 / "f1_downstream_error_rates.csv", index=False)

    strata_df = per_query_df.groupby("stratum").agg(
        n_queries=("query_id", "count"),
        pct_wrong_sql_gate  =("C2_is_error",   lambda x: round(100*x.mean(), 1)),
        pct_wrong_no_gate   =("C3_is_error",   lambda x: round(100*x.mean(), 1)),
        pct_wrong_joint_gate=("C4_is_error",   lambda x: round(100*x.mean(), 1)),
        pct_wrong_data_gate =("C5_is_error",   lambda x: round(100*x.mean(), 1)),
        n_joint_required    =("joint_required", "sum"),
    ).reset_index()
    strata_df.to_csv(ROUND2 / "f1_control_vs_targeted_strata.csv", index=False)

    (ROUND2 / "f1_query_executions.json").write_text(
        json.dumps(exec_log, indent=2, default=str), encoding="utf-8"
    )

    write_joint_required_md(per_query, exec_log, ROUND2 / "f1_joint_required_queries.md")

    elapsed = time.perf_counter() - t0
    write_report(rates, per_query_df, schema, len(QUERIES), elapsed, ROUND2)

    print(f"\n[F1] Done in {elapsed:.1f}s")
    print("\n=== GATE ERROR RATES ===")
    print(rates.to_string(index=False))
    print("\n=== STRATA ===")
    print(strata_df.to_string(index=False))
    n_jr = int(per_query_df["joint_required"].sum())
    print(f"\n=== JOINT-REQUIRED queries: {n_jr} ===")
    print(f"Outputs: {ROUND2}")


if __name__ == "__main__":
    main()
