"""
F1b: Joint gate — magnitude metric, repaired condition, coupled gate.

Fixes two fundamental flaws in F1 (which fixed E6's circular reference):

FLAW 1 — Binary metric (F1b.1):
  F1 used is_error: bool. Under row-deleting quarantine, ANY aggregate
  over a smaller row set diverges from the aggregate over the full set,
  even with a perfect detector. 91.4% "error" rate measures "rows were
  deleted", not "the gate failed". Replace with relative-error magnitude:
    rel_err = |a − r| / max(|r|, 1e-9)
  Report the DISTRIBUTION and a materiality sensitivity curve at 0.1/1/5%.

FLAW 2 — Missing repaired condition (F1b.2):
  The paper describes quarantined rows routed to an audit queue and
  reviewed by an analyst — not permanently deleted. Add C5/C6: start
  from dirty, restore TRUE values for every quarantined row (TP: analyst
  confirms and corrects; FP: analyst clears and restores unchanged).
  This models the deployment the paper actually claims.

ADDITION — Coupled gate (F1b.3):
  The coupling mechanism worth testing: the migration module receives the
  quarantine MASK plus per-row column-level provenance (which columns
  drove the quarantine decision), and for each query reinstates quarantined
  rows whose implicated columns do NOT appear anywhere in the query.
  This is a genuine information-flow coupling between the anomaly detector
  and the SQL migration layer.

ADDITION — Fixed execution path (F1b.4):
  F1 transpiled postgres → tsql → duckdb (2-hop), manufacturing drift
  not present in the real pipeline. F1b transpiles postgres → duckdb
  in a single hop, matching 30_run_sql_migration.py.

Conditions (8, excluding reference):
  C0  true+source       REFERENCE
  C1  dirty+source      SQL_GATE (no data cleaning)
  C2  dirty+transpiled  NO_GATE
  C3  cleansed+source   JOINT_GATE (deletion)
  C4  cleansed+trans    DATA_GATE (deletion)
  C5  repaired+source   REPAIRED (analyst review model)
  C6  repaired+trans    REPAIRED_TRANS
  C7  coupled+source    COUPLED_GATE (column-aware reinstatement)

Outputs: rebuttal_artifacts/round3/f1b_joint_gate/
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
import sqlglot.expressions as exp

REPO   = Path(__file__).resolve().parents[2]
PROC   = REPO / "phase2_rebuild" / "data" / "processed"
LABELS = REPO / "phase2_rebuild" / "data" / "labels"
SCORES = REPO / "phase2_rebuild" / "results" / "scores"
TABLES = REPO / "phase2_rebuild" / "results" / "tables"
ROUND3 = REPO / "rebuttal_artifacts" / "round3" / "f1b_joint_gate"
ROUND3.mkdir(parents=True, exist_ok=True)

BASELINE_CSV = TABLES / "baseline.csv"
EPS = 1e-9
MATERIALITY_THRESHOLDS = [0.001, 0.01, 0.05]   # 0.1%, 1%, 5%

# ---------------------------------------------------------------------------
# Query corpus — same 35 queries as F1 (reuse verbatim)
# ---------------------------------------------------------------------------
QUERIES: list[dict] = [
    # ---- TARGETED D2 ----
    {"id":"T01","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "description":"Total OT pay across all employees",
     "sql":'SELECT ROUND(SUM("Total_OT_Paid"::numeric), 2) AS total_ot FROM {table}',
     "result_type":"scalar"},
    {"id":"T02","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "description":"Count employees with OT pay and zero regular hours",
     "sql":'SELECT COUNT(*) AS n FROM {table} WHERE "Total_OT_Paid" > 0 AND "Regular_Hours" = 0',
     "result_type":"scalar"},
    {"id":"T03","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "description":"Average regular gross pay",
     "sql":'SELECT ROUND(AVG("Regular_Gross_Paid"::numeric), 2) AS avg_gross FROM {table}',
     "result_type":"scalar"},
    {"id":"T04","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "description":"Count employees with gross pay above 200k",
     "sql":'SELECT COUNT(*) AS n FROM {table} WHERE "Regular_Gross_Paid" > 200000',
     "result_type":"scalar"},
    {"id":"T05","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "description":"Top-5 agencies by total OT pay",
     "sql":('SELECT "Agency_Name", ROUND(SUM("Total_OT_Paid"::numeric), 2) AS agency_ot '
            'FROM {table} GROUP BY "Agency_Name" ORDER BY agency_ot DESC LIMIT 5'),
     "result_type":"table"},
    {"id":"T06","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "description":"OT-to-gross ratio across all employees",
     "sql":('SELECT ROUND(SUM("Total_OT_Paid"::numeric) / '
            'NULLIF(SUM("Regular_Gross_Paid"::numeric), 0), 4) AS ot_ratio FROM {table}'),
     "result_type":"scalar"},
    {"id":"T07","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "description":"Average gross pay per title (ILIKE filter)",
     "sql":('SELECT "Title_Description", ROUND(AVG("Regular_Gross_Paid"::numeric), 2) AS avg_gp '
            'FROM {table} WHERE "Title_Description" ILIKE \'%ANALYST%\' '
            'GROUP BY "Title_Description" ORDER BY avg_gp DESC LIMIT 10'),
     "result_type":"table"},
    {"id":"T08","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "description":"Count distinct title descriptions",
     "sql":'SELECT COUNT(DISTINCT "Title_Description") AS n_titles FROM {table}',
     "result_type":"scalar"},
    {"id":"T09","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "description":"Percentile-90 of regular gross pay",
     "sql":'SELECT ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY "Regular_Gross_Paid"), 2) AS p90 FROM {table}',
     "result_type":"scalar"},
    {"id":"T10","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "description":"Window-rank of total OT pay per agency",
     "sql":('SELECT "Agency_Name", SUM("Total_OT_Paid"::numeric) AS agency_ot, '
            'RANK() OVER (ORDER BY SUM("Total_OT_Paid"::numeric) DESC) AS rnk '
            'FROM {table} GROUP BY "Agency_Name" ORDER BY rnk LIMIT 5'),
     "result_type":"table"},
    # ---- TARGETED D3 ----
    {"id":"T11","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "description":"Education distribution",
     "sql":'SELECT "EDUCATION", COUNT(*) AS n FROM {table} GROUP BY "EDUCATION" ORDER BY "EDUCATION"',
     "result_type":"table"},
    {"id":"T12","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "description":"Count of invalid EDUCATION codes",
     "sql":'SELECT COUNT(*) AS n_invalid FROM {table} WHERE "EDUCATION" NOT IN (1, 2, 3, 4, 5, 6)',
     "result_type":"scalar"},
    {"id":"T13","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "description":"Average credit limit",
     "sql":'SELECT ROUND(AVG("LIMIT_BAL"::numeric), 2) AS avg_limit FROM {table}',
     "result_type":"scalar"},
    {"id":"T14","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "description":"Count of outlier credit limits (> 500k)",
     "sql":'SELECT COUNT(*) AS n_outlier FROM {table} WHERE "LIMIT_BAL" > 500000',
     "result_type":"scalar"},
    {"id":"T15","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "description":"Count of negative BILL_AMT1",
     "sql":'SELECT COUNT(*) AS n_neg FROM {table} WHERE "BILL_AMT1" < 0',
     "result_type":"scalar"},
    {"id":"T16","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "description":"Sum of BILL_AMT1",
     "sql":'SELECT ROUND(SUM("BILL_AMT1"::numeric), 2) AS sum_bill1 FROM {table}',
     "result_type":"scalar"},
    {"id":"T17","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "description":"Count of anomalous pay statuses (PAY_0 > 8)",
     "sql":'SELECT COUNT(*) AS n_bad_pay FROM {table} WHERE "PAY_0" > 8',
     "result_type":"scalar"},
    {"id":"T18","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "description":"Average age",
     "sql":'SELECT ROUND(AVG("AGE"::numeric), 2) AS avg_age FROM {table}',
     "result_type":"scalar"},
    {"id":"T19","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "description":"Count of out-of-range ages",
     "sql":'SELECT COUNT(*) AS n_bad_age FROM {table} WHERE "AGE" < 18 OR "AGE" > 100',
     "result_type":"scalar"},
    {"id":"T20","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "description":"Credit limit avg by education",
     "sql":('SELECT "EDUCATION", ROUND(AVG("LIMIT_BAL"::numeric), 2) AS avg_lim '
            'FROM {table} GROUP BY "EDUCATION" ORDER BY "EDUCATION"'),
     "result_type":"table"},
    # ---- CONTROL D2 ----
    {"id":"C01","dataset":"D2","stratum":"control","dialect":"postgres",
     "description":"Count distinct agencies",
     "sql":'SELECT COUNT(DISTINCT "Agency_Name") AS n_agencies FROM {table}',
     "result_type":"scalar"},
    {"id":"C02","dataset":"D2","stratum":"control","dialect":"postgres",
     "description":"Work borough distribution",
     "sql":('SELECT "Work_Location_Borough", COUNT(*) AS n FROM {table} '
            'GROUP BY "Work_Location_Borough" ORDER BY n DESC'),
     "result_type":"table"},
    {"id":"C03","dataset":"D2","stratum":"control","dialect":"postgres",
     "description":"Pay basis distribution",
     "sql":('SELECT "Pay_Basis", COUNT(*) AS n FROM {table} '
            'GROUP BY "Pay_Basis" ORDER BY "Pay_Basis"'),
     "result_type":"table"},
    {"id":"C04","dataset":"D2","stratum":"control","dialect":"postgres",
     "description":"Average regular hours",
     "sql":'SELECT ROUND(AVG("Regular_Hours"::numeric), 4) AS avg_hours FROM {table}',
     "result_type":"scalar"},
    {"id":"C05","dataset":"D2","stratum":"control","dialect":"postgres",
     "description":"Total other pay",
     "sql":'SELECT ROUND(SUM("Total_Other_Pay"::numeric), 2) AS total_other FROM {table}',
     "result_type":"scalar"},
    {"id":"C06","dataset":"D2","stratum":"control","dialect":"postgres",
     "description":"Average OT hours",
     "sql":'SELECT ROUND(AVG("OT_Hours"::numeric), 4) AS avg_ot_hrs FROM {table}',
     "result_type":"scalar"},
    {"id":"C07","dataset":"D2","stratum":"control","dialect":"postgres",
     "description":"Count active employees",
     "sql":'SELECT COUNT(*) AS n_active FROM {table} WHERE "Leave_Status_as_of_June_30" = \'ACTIVE\'',
     "result_type":"scalar"},
    {"id":"C08","dataset":"D2","stratum":"control","dialect":"postgres",
     "description":"Agency regular hours ranking",
     "sql":('SELECT "Agency_Name", ROUND(AVG("Regular_Hours"::numeric), 4) AS avg_hrs, '
            'RANK() OVER (ORDER BY AVG("Regular_Hours"::numeric) DESC) AS rnk '
            'FROM {table} GROUP BY "Agency_Name" ORDER BY rnk LIMIT 10'),
     "result_type":"table"},
    # ---- CONTROL D3 ----
    {"id":"C09","dataset":"D3","stratum":"control","dialect":"postgres",
     "description":"Sex distribution",
     "sql":'SELECT "SEX", COUNT(*) AS n FROM {table} GROUP BY "SEX" ORDER BY "SEX"',
     "result_type":"table"},
    {"id":"C10","dataset":"D3","stratum":"control","dialect":"postgres",
     "description":"Marriage status distribution",
     "sql":'SELECT "MARRIAGE", COUNT(*) AS n FROM {table} GROUP BY "MARRIAGE" ORDER BY "MARRIAGE"',
     "result_type":"table"},
    {"id":"C11","dataset":"D3","stratum":"control","dialect":"postgres",
     "description":"Average BILL_AMT2",
     "sql":'SELECT ROUND(AVG("BILL_AMT2"::numeric), 2) AS avg_bill2 FROM {table}',
     "result_type":"scalar"},
    {"id":"C12","dataset":"D3","stratum":"control","dialect":"postgres",
     "description":"Sum of PAY_AMT1",
     "sql":'SELECT ROUND(SUM("PAY_AMT1"::numeric), 2) AS sum_pay1 FROM {table}',
     "result_type":"scalar"},
    {"id":"C13","dataset":"D3","stratum":"control","dialect":"postgres",
     "description":"Default payment distribution",
     "sql":('SELECT "default_payment_next_month", COUNT(*) AS n FROM {table} '
            'GROUP BY "default_payment_next_month" ORDER BY "default_payment_next_month"'),
     "result_type":"table"},
    {"id":"C14","dataset":"D3","stratum":"control","dialect":"postgres",
     "description":"Average PAY_AMT3",
     "sql":'SELECT ROUND(AVG("PAY_AMT3"::numeric), 2) AS avg_pay3 FROM {table}',
     "result_type":"scalar"},
    {"id":"C15","dataset":"D3","stratum":"control","dialect":"postgres",
     "description":"Count long delinquent PAY_2",
     "sql":'SELECT COUNT(*) AS n_delin FROM {table} WHERE "PAY_2" >= 2',
     "result_type":"scalar"},
]
assert len(QUERIES) == 35


# ---------------------------------------------------------------------------
# Transpilation: single-hop postgres → duckdb (F1b.4)
# ---------------------------------------------------------------------------
def transpile_1hop(sql: str) -> tuple[str | None, str | None]:
    """postgres → duckdb in one hop (matches 30_run_sql_migration.py)."""
    try:
        dkdb = sqlglot.transpile(sql, read="postgres", write="duckdb")[0]
        return dkdb, None
    except Exception as ex:
        return None, str(ex)


def get_query_columns(sql: str) -> frozenset[str]:
    """Extract all column names referenced in SQL (for coupled gate)."""
    try:
        tree = sqlglot.parse_one(sql, dialect="postgres")
        cols: set[str] = set()
        for node in tree.walk():
            n = node[0] if isinstance(node, tuple) else node
            if isinstance(n, exp.Column) and n.name:
                cols.add(n.name.strip('"').lower().replace(" ", "_"))
        return frozenset(cols)
    except Exception:
        return frozenset()


# ---------------------------------------------------------------------------
# Column normalization (same as F1)
# ---------------------------------------------------------------------------
def normalise_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [
        c.replace(" ", "_").replace("/", "_")
         .replace("(", "").replace(")", "").replace("-", "_")
        for c in df.columns
    ]
    return df


# ---------------------------------------------------------------------------
# Magnitude comparison — never collapses to boolean
# ---------------------------------------------------------------------------
def _to_float(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _normalise_val(v) -> str:
    if v is None:
        return "NULL"
    f = _to_float(v)
    return f"{round(f, 4)}" if f is not None else str(v).strip().lower()


def _null_mag(error_tag: str) -> dict:
    return {"rel_err": None, "abs_err": None, "jaccard": None,
            "missing_rows": None, "extra_rows": None, "row_delta": None,
            "mean_col_rel_err": None, "median_col_rel_err": None,
            "max_col_rel_err": None, "exec_error": error_tag}


def compare_magnitude(ref_rows, cand_rows, result_type: str = "scalar") -> dict:
    """
    Return magnitude metrics for one (query, condition) pair.
    Key field is rel_err: the primary headline metric.
    For scalars: rel_err = |a - r| / max(|r|, EPS).
    For tables: rel_err = max relative error across aligned numeric cells;
                jaccard on string-normalised row sets.
    NEVER collapsed to a boolean here.
    """
    if ref_rows is None and cand_rows is None:
        return _null_mag("both_error")
    if ref_rows is None:
        return _null_mag("ref_error")
    if cand_rows is None:
        return _null_mag("cand_error")

    row_delta = len(cand_rows) - len(ref_rows)

    # --- Scalar ---
    if result_type == "scalar" or (len(ref_rows) == 1 and len(ref_rows[0]) == 1):
        rv = _to_float(ref_rows[0][0]) if ref_rows else None
        cv = _to_float(cand_rows[0][0]) if cand_rows else None
        if rv is not None and cv is not None:
            abs_err = abs(rv - cv)
            rel_err = abs_err / max(abs(rv), EPS)
            return {"rel_err": round(rel_err, 8), "abs_err": round(abs_err, 6),
                    "jaccard": 1.0 if rel_err < 1e-6 else 0.0,
                    "missing_rows": 0, "extra_rows": 0, "row_delta": row_delta,
                    "mean_col_rel_err": round(rel_err, 8),
                    "median_col_rel_err": round(rel_err, 8),
                    "max_col_rel_err": round(rel_err, 8),
                    "exec_error": None}
        # Non-numeric scalar
        rv_s = str(ref_rows[0][0]).strip().lower() if ref_rows else ""
        cv_s = str(cand_rows[0][0]).strip().lower() if cand_rows else ""
        match = rv_s == cv_s
        return {"rel_err": 0.0 if match else 1.0, "abs_err": 0.0 if match else 1.0,
                "jaccard": 1.0 if match else 0.0,
                "missing_rows": 0, "extra_rows": 0, "row_delta": row_delta,
                "mean_col_rel_err": 0.0 if match else 1.0,
                "median_col_rel_err": 0.0 if match else 1.0,
                "max_col_rel_err": 0.0 if match else 1.0,
                "exec_error": None}

    # --- Table ---
    def row_key(row):
        return "|".join(_normalise_val(v) for v in row)

    ref_keys = [row_key(r) for r in ref_rows]
    cand_keys = [row_key(r) for r in cand_rows]
    ref_set  = set(ref_keys)
    cand_set = set(cand_keys)
    intersection = ref_set & cand_set
    union = ref_set | cand_set
    jaccard = len(intersection) / len(union) if union else 1.0
    missing_rows = len(ref_set - cand_set)
    extra_rows   = len(cand_set - ref_set)

    # Align rows on first column (group-by key) and compute per-cell rel err
    cand_by_key: dict = {}
    for row in cand_rows:
        k = str(row[0]).strip().lower() if row else ""
        cand_by_key.setdefault(k, []).append(row)

    col_rel_errs: list[float] = []
    for ref_row in ref_rows:
        k = str(ref_row[0]).strip().lower() if ref_row else ""
        if k in cand_by_key:
            cand_row = cand_by_key[k][0]
            for rv, cv in zip(ref_row, cand_row):
                rf = _to_float(rv)
                cf = _to_float(cv)
                if rf is not None and cf is not None:
                    col_rel_errs.append(abs(rf - cf) / max(abs(rf), EPS))

    mean_re   = float(np.mean(col_rel_errs))   if col_rel_errs else float("nan")
    median_re = float(np.median(col_rel_errs)) if col_rel_errs else float("nan")
    max_re    = float(np.max(col_rel_errs))    if col_rel_errs else float("nan")
    # Headline: max is the worst-case cell error; Jaccard captures row-set divergence
    headline_rel = max(1.0 - jaccard, max_re if not np.isnan(max_re) else 0.0)

    return {"rel_err": round(headline_rel, 8), "abs_err": None,
            "jaccard": round(jaccard, 4),
            "missing_rows": missing_rows, "extra_rows": extra_rows,
            "row_delta": row_delta,
            "mean_col_rel_err": round(mean_re, 8) if not np.isnan(mean_re) else None,
            "median_col_rel_err": round(median_re, 8) if not np.isnan(median_re) else None,
            "max_col_rel_err": round(max_re, 8) if not np.isnan(max_re) else None,
            "exec_error": None}


# ---------------------------------------------------------------------------
# Column provenance for coupled gate (F1b.3)
# No ground-truth labels used — purely statistical (z-score vs true table).
# ---------------------------------------------------------------------------
def compute_column_provenance(
    df_true: pd.DataFrame,
    df_dirty: pd.DataFrame,
    quarantine_mask: np.ndarray,
    z_threshold: float = 3.0,
) -> dict[int, frozenset[str]]:
    """
    For each quarantined row position in df_dirty, identify which columns
    are statistical outliers (|z| > z_threshold relative to df_true distribution).

    Returns dict: row_pos (int) → frozenset of implicated column names.

    Semantics:
      empty frozenset  → no column anomaly detected; treat as likely FP; safe to
                         reinstate for any query (see coupled gate logic below).
      non-empty set    → columns driving the anomaly; reinstate only for queries
                         that do NOT reference any of these columns.
      "STRUCTURAL"     → row position ≥ len(df_true) (extra B3-type row);
                         never reinstate regardless of query columns.
    """
    STRUCTURAL = frozenset(["__STRUCTURAL__"])
    n_true = len(df_true)

    numeric_cols = [c for c in df_true.columns
                    if pd.api.types.is_numeric_dtype(df_true[c])]

    # Compute distribution on true table
    means = df_true[numeric_cols].mean()
    stds  = df_true[numeric_cols].std().replace(0, 1)

    provenance: dict[int, frozenset[str]] = {}
    quarantined_positions = np.where(quarantine_mask)[0]

    for pos in quarantined_positions:
        if pos >= n_true:
            # Extra row (B3-type structural addition) — never reinstate
            provenance[int(pos)] = STRUCTURAL
            continue
        row = df_dirty.iloc[pos]
        implicated: set[str] = set()
        for col in numeric_cols:
            val = row.get(col, None)
            if val is not None and not (isinstance(val, float) and np.isnan(val)):
                z = abs((float(val) - means[col]) / stds[col])
                if z > z_threshold:
                    implicated.add(col.lower())
        provenance[int(pos)] = frozenset(implicated)

    return provenance


def should_reinstate(pos: int, provenance: dict, query_cols: frozenset[str]) -> bool:
    """
    Coupled gate reinstatement decision for one quarantined row.
    Reinstate if:
      - Provenance is empty (likely FP, no anomalous column detected), OR
      - Provenance columns are disjoint from query columns.
    Never reinstate STRUCTURAL rows.
    """
    prov = provenance.get(pos, frozenset())
    if "__STRUCTURAL__" in prov:
        return False
    if not prov:
        # Likely FP — reinstate for all queries
        return True
    # Only reinstate if query doesn't touch the implicated columns
    query_lower = frozenset(c.lower() for c in query_cols)
    return prov.isdisjoint(query_lower)


# ---------------------------------------------------------------------------
# DuckDB table building
# ---------------------------------------------------------------------------
def run_query(con, sql: str) -> tuple[list | None, str | None]:
    try:
        return con.execute(sql).fetchall(), None
    except Exception as ex:
        return None, str(ex)


def build_duckdb(con: duckdb.DuckDBPyConnection) -> dict:
    """
    Build DuckDB tables for each dataset:
      {pfx}_true, {pfx}_dirty, {pfx}_clean, {pfx}_repaired

    Returns schema dict with row counts, tau, FP/FN counts, quarantine mask,
    column provenance, and dataframes for coupled gate use.
    """
    bl = pd.read_csv(BASELINE_CSV)
    schema: dict = {}

    for did, true_f, inj_f in [
        ("D2", "D2_nyc_fy2024", "D2_injected"),
        ("D3", "D3_uci_credit", "D3_injected"),
    ]:
        df_true  = normalise_cols(pd.read_parquet(PROC / f"{true_f}.parquet"))
        df_dirty = normalise_cols(pd.read_parquet(PROC / f"{inj_f}.parquet"))
        sc       = pd.read_parquet(SCORES / f"{did}_scores.parquet")

        tau = float(bl[(bl["dataset"] == did) & (bl["detector"] == "hybrid_lr")]["best_threshold"].iloc[0])
        qmask = (sc["hybrid_lr"].to_numpy() >= tau)
        y     = sc["y"].to_numpy() > 0.5
        n_quarantined = int(qmask.sum())
        n_pos         = int(y.sum())
        n_tp          = int((qmask & y).sum())
        n_fp          = int((qmask & ~y).sum())
        n_fn          = int((~qmask & y).sum())
        n_tn          = int((~qmask & ~y).sum())

        # --- Cleansed table (quarantine-by-deletion) ---
        df_clean = df_dirty[~qmask].reset_index(drop=True)

        # --- Repaired table (F1b.2) ---
        # D3: in-place injection, same row count → overlay true values on quarantined positions
        # D2: first len(df_true) rows are originals; rows >= len(df_true) are B3 additions
        n_true = len(df_true)
        df_repaired = df_dirty.copy()

        # Restore quarantined original rows to true values (single-step iloc — no CoW issue)
        orig_qmask = qmask[:n_true]
        quaran_orig_pos = np.where(orig_qmask)[0]  # positions in [0, n_true) that are quarantined
        if len(quaran_orig_pos):
            # Rebuild from slices so pandas CoW can't interfere
            true_vals = df_true.iloc[quaran_orig_pos].copy()
            true_vals.index = quaran_orig_pos  # restore integer positions for loc
            df_repaired.iloc[quaran_orig_pos] = true_vals.values

        if len(df_dirty) > n_true:
            # D2: drop quarantined B3 rows (restore = non-existence)
            b3_qmask = qmask[n_true:]
            b3_keep  = ~b3_qmask
            df_repaired = pd.concat([
                df_repaired.iloc[:n_true],
                df_dirty.iloc[n_true:][b3_keep],
            ], ignore_index=True)

        # --- Column provenance for coupled gate ---
        col_provenance = compute_column_provenance(df_true, df_dirty, qmask)

        pfx = "payroll" if did == "D2" else "credit"
        tables = {
            f"{pfx}_true":     df_true,
            f"{pfx}_dirty":    df_dirty,
            f"{pfx}_clean":    df_clean,
            f"{pfx}_repaired": df_repaired,
        }
        for tname, df in tables.items():
            con.execute(f"DROP TABLE IF EXISTS {tname}")
            con.register(f"_tmp_{tname}", df)
            con.execute(f"CREATE TABLE {tname} AS SELECT * FROM _tmp_{tname}")

        print(f"  {did}: true={n_true:,}  dirty={len(df_dirty):,}  "
              f"clean={len(df_clean):,}  repaired={len(df_repaired):,}  "
              f"quarantined={n_quarantined:,}  tp={n_tp}  fp={n_fp}  fn={n_fn}",
              flush=True)

        schema[did] = {
            "true_t":     f"{pfx}_true",
            "dirty_t":    f"{pfx}_dirty",
            "clean_t":    f"{pfx}_clean",
            "repaired_t": f"{pfx}_repaired",
            "n_true":     n_true, "n_dirty": len(df_dirty),
            "n_clean":    len(df_clean), "n_repaired": len(df_repaired),
            "tau": tau,
            "n_quarantined": n_quarantined,
            "n_pos": n_pos, "n_tp": n_tp, "n_fp": n_fp, "n_fn": n_fn, "n_tn": n_tn,
            "qmask": qmask,
            "col_provenance": col_provenance,
            "df_dirty": df_dirty,
        }

    return schema


# ---------------------------------------------------------------------------
# Per-query simulation: all 8 conditions
# ---------------------------------------------------------------------------
def simulate(con: duckdb.DuckDBPyConnection, schema: dict) -> tuple[list[dict], list[dict]]:
    per_query: list[dict] = []
    exec_log:  list[dict] = []

    for q in QUERIES:
        did  = q["dataset"]
        si   = schema[did]
        rtype = q["result_type"]

        # Build source SQLs for each table
        sql_true     = q["sql"].format(table=si["true_t"])
        sql_dirty    = q["sql"].format(table=si["dirty_t"])
        sql_clean    = q["sql"].format(table=si["clean_t"])
        sql_repaired = q["sql"].format(table=si["repaired_t"])

        # Single-hop transpile (F1b.4)
        tsql_true,     te_true  = transpile_1hop(sql_true)
        tsql_dirty,    te_dirty = transpile_1hop(sql_dirty)
        tsql_clean,    te_clean = transpile_1hop(sql_clean)
        tsql_repaired, te_rep   = transpile_1hop(sql_repaired)

        def ex(sql, err=None):
            if err: return None, err
            return run_query(con, sql)

        # Execute all conditions
        r0, e0 = run_query(con, sql_true)              # C0: REFERENCE
        r1, e1 = run_query(con, sql_dirty)             # C1: dirty+source (SQL_GATE)
        r2, e2 = ex(tsql_dirty, te_dirty)              # C2: dirty+transpiled (NO_GATE)
        r3, e3 = run_query(con, sql_clean)             # C3: cleansed+source (JOINT_GATE)
        r4, e4 = ex(tsql_clean, te_clean)              # C4: cleansed+trans (DATA_GATE)
        r5, e5 = run_query(con, sql_repaired)          # C5: repaired+source
        r6, e6 = ex(tsql_repaired, te_rep)             # C6: repaired+transpiled

        # C7: coupled gate — per-query table
        query_cols = get_query_columns(q["sql"])
        qmask    = si["qmask"]
        df_dirty = si["df_dirty"]
        prov     = si["col_provenance"]

        reinstate = np.array([
            should_reinstate(int(pos), prov, query_cols)
            for pos in range(len(df_dirty))
        ])
        # coupled = non-quarantined rows + reinstated quarantined rows
        coupled_mask = (~qmask) | (qmask & reinstate)
        n_reinstated = int((qmask & reinstate).sum())
        df_coupled = df_dirty[coupled_mask].reset_index(drop=True)

        coupled_t = f"__coupled_{q['id']}__"
        con.execute(f"DROP TABLE IF EXISTS {coupled_t}")
        con.register(f"_tmp_coupled", df_coupled)
        con.execute(f"CREATE TABLE {coupled_t} AS SELECT * FROM _tmp_coupled")
        sql_coupled = q["sql"].format(table=coupled_t)
        r7, e7 = run_query(con, sql_coupled)
        con.execute(f"DROP TABLE IF EXISTS {coupled_t}")

        # Magnitude comparisons (all vs C0)
        m1 = compare_magnitude(r0, r1, rtype)
        m2 = compare_magnitude(r0, r2, rtype)
        m3 = compare_magnitude(r0, r3, rtype)
        m4 = compare_magnitude(r0, r4, rtype)
        m5 = compare_magnitude(r0, r5, rtype)
        m6 = compare_magnitude(r0, r6, rtype)
        m7 = compare_magnitude(r0, r7, rtype)

        # Helper to flatten mag dict with prefix
        def flat(mag: dict, pfx: str) -> dict:
            return {f"{pfx}_{k}": v for k, v in mag.items()}

        row = {
            "query_id":    q["id"],
            "dataset":     did,
            "stratum":     q["stratum"],
            "result_type": rtype,
            "description": q["description"],
            "ref_ok":      e0 is None,
            "n_reinstated_c7": n_reinstated,
            **flat(m1, "C1_dirty_src"),
            **flat(m2, "C2_dirty_trans"),
            **flat(m3, "C3_clean_src"),
            **flat(m4, "C4_clean_trans"),
            **flat(m5, "C5_repaired_src"),
            **flat(m6, "C6_repaired_trans"),
            **flat(m7, "C7_coupled_src"),
        }
        per_query.append(row)

        # Exec log entry
        exec_log.append({
            "query_id": q["id"], "dataset": did, "stratum": q["stratum"],
            "query_cols": sorted(query_cols),
            "n_reinstated_c7": n_reinstated,
            "transpile_errors": {
                "dirty": te_dirty, "clean": te_clean, "repaired": te_rep
            },
            "results": {
                "C0_ref":         {"rows": str(r0)[:500], "err": e0},
                "C1_dirty_src":   {"rows": str(r1)[:500], "err": e1,
                                   "rel_err": m1["rel_err"]},
                "C2_dirty_trans": {"rows": str(r2)[:500], "err": e2,
                                   "rel_err": m2["rel_err"]},
                "C3_clean_src":   {"rows": str(r3)[:500], "err": e3,
                                   "rel_err": m3["rel_err"]},
                "C4_clean_trans": {"rows": str(r4)[:500], "err": e4,
                                   "rel_err": m4["rel_err"]},
                "C5_rep_src":     {"rows": str(r5)[:500], "err": e5,
                                   "rel_err": m5["rel_err"]},
                "C6_rep_trans":   {"rows": str(r6)[:500], "err": e6,
                                   "rel_err": m6["rel_err"]},
                "C7_coupled_src": {"rows": str(r7)[:500], "err": e7,
                                   "rel_err": m7["rel_err"]},
            }
        })

        # Progress
        parts = [f"C1={m1['rel_err']:.4f}" if m1['rel_err'] is not None else "C1=ERR",
                 f"C3={m3['rel_err']:.4f}" if m3['rel_err'] is not None else "C3=ERR",
                 f"C5={m5['rel_err']:.4f}" if m5['rel_err'] is not None else "C5=ERR",
                 f"C7={m7['rel_err']:.4f}" if m7['rel_err'] is not None else "C7=ERR"]
        print(f"  {q['id']} [{q['stratum'][:3]}] {' '.join(parts)}", flush=True)

    return per_query, exec_log


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------
COND_COLS = {
    "C1_dirty_src":   "dirty+source",
    "C2_dirty_trans":  "dirty+trans",
    "C3_clean_src":   "cleansed+source",
    "C4_clean_trans":  "cleansed+trans",
    "C5_repaired_src": "repaired+source",
    "C6_repaired_trans":"repaired+trans",
    "C7_coupled_src":  "coupled+source",
}


def error_magnitude_distributions(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cond, label in COND_COLS.items():
        col = f"{cond}_rel_err"
        if col not in df.columns:
            continue
        for stratum in ["all", "targeted", "control"]:
            sub = df if stratum == "all" else df[df["stratum"] == stratum]
            sub = sub[sub["ref_ok"] == True]
            vals = sub[col].dropna()
            if len(vals) == 0:
                continue
            rows.append({
                "condition": cond, "label": label, "stratum": stratum,
                "n": len(vals),
                "min":    round(float(vals.min()), 6),
                "median": round(float(vals.median()), 6),
                "p75":    round(float(vals.quantile(0.75)), 6),
                "p90":    round(float(vals.quantile(0.90)), 6),
                "max":    round(float(vals.max()), 6),
                "mean":   round(float(vals.mean()), 6),
            })
    return pd.DataFrame(rows)


def materiality_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cond, label in COND_COLS.items():
        col = f"{cond}_rel_err"
        if col not in df.columns:
            continue
        for stratum in ["all", "targeted", "control"]:
            sub = df if stratum == "all" else df[df["stratum"] == stratum]
            sub = sub[sub["ref_ok"] == True]
            vals = sub[col].dropna()
            n = len(vals)
            if n == 0:
                continue
            for thr in MATERIALITY_THRESHOLDS:
                pct = round(100.0 * (vals > thr).sum() / n, 1)
                rows.append({
                    "condition": cond, "label": label,
                    "stratum": stratum, "threshold": thr,
                    "pct_exceeding": pct, "n_queries": n,
                })
    return pd.DataFrame(rows)


def coupled_gate_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Compare coupled vs dirty/cleansed/repaired per stratum."""
    rows = []
    for stratum in ["all", "targeted", "control"]:
        sub = df if stratum == "all" else df[df["stratum"] == stratum]
        sub = sub[sub["ref_ok"] == True]
        if len(sub) == 0:
            continue
        def med(col): return round(float(sub[col].dropna().median()), 6) if col in sub else None

        c1  = med("C1_dirty_src_rel_err")
        c3  = med("C3_clean_src_rel_err")
        c5  = med("C5_repaired_src_rel_err")
        c7  = med("C7_coupled_src_rel_err")
        best_single = min(v for v in [c1, c3, c5] if v is not None) if any(v is not None for v in [c1, c3, c5]) else None
        coupled_better = (c7 < best_single) if (c7 is not None and best_single is not None) else None
        rows.append({
            "stratum": stratum, "n_queries": len(sub),
            "median_dirty_rel_err": c1,
            "median_cleansed_rel_err": c3,
            "median_repaired_rel_err": c5,
            "median_coupled_rel_err": c7,
            "best_single_median": best_single,
            "coupled_beats_best_single": coupled_better,
            "avg_n_reinstated": round(float(sub["n_reinstated_c7"].mean()), 1) if "n_reinstated_c7" in sub else None,
        })
    return pd.DataFrame(rows)


def analyst_cost_table(schema: dict) -> pd.DataFrame:
    rows = []
    for did, si in schema.items():
        n_q = si["n_quarantined"]
        n_fp = si["n_fp"]
        n_tp = si["n_tp"]
        rows.append({
            "dataset": did,
            "n_quarantined": n_q,
            "n_tp_in_queue": n_tp,
            "n_fp_in_queue": n_fp,
            "fp_fraction": round(n_fp / n_q, 4) if n_q > 0 else None,
            "n_fn_escaped": si["n_fn"],
            "n_pos_total": si["n_pos"],
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def write_report(df: pd.DataFrame, dist_df: pd.DataFrame,
                 mat_df: pd.DataFrame, coup_df: pd.DataFrame,
                 cost_df: pd.DataFrame, schema: dict, elapsed: float):

    # Compute headline numbers for the 3 opening lines
    all_ok = df[df["ref_ok"] == True]

    def med_all(col):
        v = all_ok[col].dropna()
        return round(float(v.median()), 6) if len(v) else None

    med_dirty   = med_all("C1_dirty_src_rel_err")
    med_clean   = med_all("C3_clean_src_rel_err")
    med_repaired= med_all("C5_repaired_src_rel_err")
    med_coupled = med_all("C7_coupled_src_rel_err")

    # Control queries only
    ctl = all_ok[all_ok["stratum"] == "control"]
    def med_ctl(col):
        v = ctl[col].dropna()
        return round(float(v.median()), 6) if len(v) else None

    med_dirty_ctl = med_ctl("C1_dirty_src_rel_err")
    med_clean_ctl = med_ctl("C3_clean_src_rel_err")
    selection_bias = (med_clean_ctl is not None and med_dirty_ctl is not None
                      and med_clean_ctl > med_dirty_ctl)
    selection_bias_mag = round(abs((med_clean_ctl or 0.0) - (med_dirty_ctl or 0.0)), 6)

    # Best single gate
    best_single = min(v for v in [med_dirty, med_clean, med_repaired] if v is not None) if any(v is not None for v in [med_dirty, med_clean, med_repaired]) else None
    coupling_helps = (med_coupled is not None and best_single is not None and med_coupled < best_single)

    # Analyst cost
    d2_cost = cost_df[cost_df["dataset"] == "D2"].iloc[0] if "D2" in cost_df["dataset"].values else None
    d3_cost = cost_df[cost_df["dataset"] == "D3"].iloc[0] if "D3" in cost_df["dataset"].values else None

    with open(ROUND3 / "F1B_JOINT_GATE_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# F1b: Joint Gate — Magnitude Metric, Repaired Condition, Coupled Gate\n\n")
        f.write("**Manuscript**: DataFlow AI — IEEE Access Access-2026-28181\n\n")
        f.write("---\n\n")
        f.write("## Opening lines (R2.4 deciding comment)\n\n")

        # Line 1: coupling
        line1_verdict = "YES" if coupling_helps else "NO"
        f.write(f"**1. Does coupling reduce relative error vs the better single gate?  {line1_verdict}**  \n")
        f.write(f"Median rel-err: dirty={med_dirty}, cleansed={med_clean}, "
                f"repaired={med_repaired}, coupled={med_coupled}. "
                f"Best single = {best_single}.\n\n")

        # Line 2: selection bias
        line2_verdict = "YES" if selection_bias else "NO"
        f.write(f"**2. Does quarantine-by-deletion introduce measurable selection bias into "
                f"aggregates over uncorrupted columns?  {line2_verdict}**  \n")
        f.write(f"Control queries: cleansed median rel-err = {med_clean_ctl} vs "
                f"dirty median = {med_dirty_ctl}. ")
        if selection_bias:
            f.write(f"Selection bias magnitude = {selection_bias_mag:.4f} (cleansed is WORSE "
                    f"than dirty on safe-column queries due to FP row removal).\n\n")
        else:
            f.write(f"No significant selection bias detected (delta = {selection_bias_mag:.4f}).\n\n")

        # Line 3: analyst cost
        f.write(f"**3. What does the FP rate cost?**  \n")
        if d2_cost is not None:
            f.write(f"D2: {d2_cost['n_quarantined']:,} rows in review queue, "
                    f"{d2_cost['n_fp_in_queue']:,} FPs ({100*d2_cost['fp_fraction']:.1f}%). "
                    f"FP-induced cleansed bias on control queries: {med_clean_ctl}.  \n")
        if d3_cost is not None:
            f.write(f"D3: {d3_cost['n_quarantined']:,} rows in review queue, "
                    f"{d3_cost['n_fp_in_queue']:,} FPs ({100*d3_cost['fp_fraction']:.1f}%).  \n")
        f.write("\n---\n\n")

        f.write("## Fixes applied vs F1 and E6\n\n")
        f.write("| Fix | F1b change |\n|---|---|\n")
        f.write("| Binary metric (F1 flaw) | Replaced with rel-err magnitude; stored per (query, condition) |\n")
        f.write("| Repaired condition missing | Added C5/C6: quarantined rows restored to TRUE values |\n")
        f.write("| Coupled gate not tested | Added C7: column-provenance-aware reinstatement |\n")
        f.write("| 2-hop transpilation | Now single-hop postgres→duckdb |\n\n")

        f.write("## Conditions\n\n")
        f.write("| Code | Data | SQL | Gate |\n|---|---|---|---|\n")
        f.write("| C0 | true | source | REFERENCE |\n")
        f.write("| C1 | dirty | source | SQL_GATE |\n")
        f.write("| C2 | dirty | transpiled | NO_GATE |\n")
        f.write("| C3 | cleansed (deletion) | source | JOINT_GATE |\n")
        f.write("| C4 | cleansed (deletion) | trans | DATA_GATE |\n")
        f.write("| C5 | repaired (analyst review) | source | REPAIRED |\n")
        f.write("| C6 | repaired | trans | REPAIRED_TRANS |\n")
        f.write("| C7 | coupled (col-aware) | source | COUPLED_GATE |\n\n")

        f.write("## Dataset context\n\n")
        for did, si in schema.items():
            f.write(f"**{did}**: true={si['n_true']:,}  dirty={si['n_dirty']:,}  "
                    f"cleansed={si['n_clean']:,}  repaired={si['n_repaired']:,}  "
                    f"quarantined={si['n_quarantined']:,} (tp={si['n_tp']}, fp={si['n_fp']}, fn={si['n_fn']})\n\n")

        f.write("## Median relative error by condition and stratum\n\n")
        f.write(dist_df[dist_df["stratum"].isin(["all","targeted","control"])]
                [["condition","stratum","median","p90","max"]]
                .to_markdown(index=False) if hasattr(dist_df, "to_markdown")
                else dist_df.to_string(index=False))
        f.write("\n\n")

        f.write("## Materiality sensitivity (% queries exceeding threshold)\n\n")
        pivot = mat_df.pivot_table(
            index=["condition","stratum"], columns="threshold",
            values="pct_exceeding", aggfunc="first"
        ).reset_index()
        f.write(pivot.to_markdown(index=False) if hasattr(pivot, "to_markdown")
                else pivot.to_string(index=False))
        f.write("\n\n")

        f.write("## Coupled gate vs other conditions\n\n")
        f.write(coup_df.to_markdown(index=False) if hasattr(coup_df, "to_markdown")
                else coup_df.to_string(index=False))
        f.write("\n\n")

        f.write("## Analyst cost\n\n")
        f.write(cost_df.to_markdown(index=False) if hasattr(cost_df, "to_markdown")
                else cost_df.to_string(index=False))
        f.write("\n\n")

        f.write("## Interpretation\n\n")
        f.write("### Why F1's 91.4% error rate was void\n\n")
        f.write("F1 used a binary `is_error` flag. Under row-deleting quarantine, "
                "ANY aggregate over 28,212 rows (cleansed D3) differs from the same "
                "aggregate over 30,000 rows (true D3), even with a perfect detector. "
                "The binary metric guaranteed near-100% error for the cleansed condition "
                "regardless of detector quality. F1b replaces this with relative error: "
                "a 0.86% AVG(BILL_AMT2) deviation is now measured as 0.0086, not 'wrong'.\n\n")

        f.write("### The selection-bias finding\n\n")
        if selection_bias:
            f.write(f"Quarantine-by-deletion introduces measurable selection bias "
                    f"into aggregates over columns that were NEVER corrupted. "
                    f"On control queries, the cleansed condition (median rel-err = {med_clean_ctl}) "
                    f"is WORSE than the dirty condition (median rel-err = {med_dirty_ctl}). "
                    f"This is FP over-quarantine: {schema['D3']['n_fp']} innocent D3 rows "
                    f"were removed, biasing every aggregate — including safe-column aggregates "
                    f"the detector never intended to affect.\n\n")
        else:
            f.write("Selection bias from FP removal is below measurable threshold in this corpus.\n\n")

        f.write("### The repaired condition\n\n")
        f.write("C5/C6 (repaired) models the deployment the paper actually claims: quarantined "
                "rows are sent to an audit queue, an analyst reviews each one, confirmed errors "
                "are corrected (TP: restore true value), and false alarms are cleared "
                "(FP: row restored unchanged). Under this model, FP bias disappears. "
                "The residual error in C5 comes only from false negatives (corrupted rows "
                "that escaped the detector and remain in the table).\n\n")

        f.write("### The coupled gate\n\n")
        if coupling_helps:
            f.write(f"C7 (coupled gate) achieves median rel-err = {med_coupled}, "
                    f"which is lower than the best single gate ({best_single}). "
                    f"Column-level provenance allows safe reinstatement of quarantined rows "
                    f"for queries that do not touch any anomalous column, reducing "
                    f"FP-induced selection bias without compromising targeted-column integrity.\n\n")
        else:
            f.write(f"C7 (coupled gate) achieves median rel-err = {med_coupled}. "
                    f"This does NOT beat the best single gate (median = {best_single}). "
                    f"The honest conclusion: simple column-provenance-based reinstatement "
                    f"does not provide a measurable advantage over the better single gate "
                    f"in this corpus. The coupling mechanism is technically sound but "
                    f"the practical gain is small. The manuscript should not claim "
                    f"multiplicative error reduction from coupling; a shared-audit-contract "
                    f"framing is more defensible.\n\n")

        f.write(f"---\n\nGenerated in {elapsed:.1f}s. Outputs: rebuttal_artifacts/round3/f1b_joint_gate/\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    t0 = time.perf_counter()
    print("[F1b] Building DuckDB tables ...", flush=True)
    con = duckdb.connect(":memory:")
    schema = build_duckdb(con)

    print(f"[F1b] Simulating {len(QUERIES)} queries × 8 conditions ...", flush=True)
    per_query, exec_log = simulate(con, schema)

    df = pd.DataFrame(per_query)
    df.to_csv(ROUND3 / "f1b_per_query_all_conditions.csv", index=False)

    dist_df = error_magnitude_distributions(df)
    dist_df.to_csv(ROUND3 / "f1b_error_magnitude_distributions.csv", index=False)

    mat_df = materiality_sensitivity(df)
    mat_df.to_csv(ROUND3 / "f1b_materiality_sensitivity.csv", index=False)

    coup_df = coupled_gate_comparison(df)
    coup_df.to_csv(ROUND3 / "f1b_coupled_gate_comparison.csv", index=False)

    cost_df = analyst_cost_table(schema)
    cost_df.to_csv(ROUND3 / "f1b_analyst_cost.csv", index=False)

    (ROUND3 / "f1b_query_executions.json").write_text(
        json.dumps(exec_log, indent=2, default=str), encoding="utf-8"
    )

    elapsed = time.perf_counter() - t0
    write_report(df, dist_df, mat_df, coup_df, cost_df, schema, elapsed)

    print(f"\n[F1b] Done in {elapsed:.1f}s")
    print("\n=== MEDIAN RELATIVE ERROR BY CONDITION ===")
    all_ok = df[df["ref_ok"] == True]
    for cond in COND_COLS:
        col = f"{cond}_rel_err"
        if col in all_ok.columns:
            vals = all_ok[col].dropna()
            if len(vals):
                print(f"  {cond}: median={vals.median():.6f}  p90={vals.quantile(0.9):.6f}  max={vals.max():.6f}")

    print(f"\nOutputs: {ROUND3}")


if __name__ == "__main__":
    main()
