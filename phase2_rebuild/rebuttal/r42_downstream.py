"""
R4.2 — Downstream experiments regenerated on hybrid_xgb stacker.

Covers four areas from the task spec:
  A. Calibration + routing: ECE/Brier for hybrid_xgb; 3-lane routing; review budget.
     Key question: does XGB's already-excellent raw calibration (ECE~0.003) make
     Platt scaling unnecessary? Report honestly.
  B. Joint gate rerun: re-run F1b's 35-query experiment using hybrid_xgb tau*.
     XGB has higher precision -> fewer FPs in quarantine -> expect selection-bias
     magnitude to shrink. Report the new numbers vs F1b (hybrid_lr) side-by-side.
  C. Modern baselines: run ECOD, COPOD, HBOS, LODA, AutoEncoder, DeepSVDD, KNN
     (with per-detector timeout) and compare F1 vs hybrid_xgb per dataset. Plain
     verdict: wins / ties / losses.
  D. Extended stacker (XGB): does adding ECOD + DeepSVDD as base signals (4->6)
     improve the XGB stacker? Report with XGB feature importances.

Outputs -> rebuttal_artifacts/round4/r42_downstream/
"""
from __future__ import annotations

import json
import signal
import time
import warnings
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import sqlglot
import sqlglot.expressions as exp
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score, balanced_accuracy_score, brier_score_loss,
    precision_recall_curve, precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedKFold
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

REPO    = Path(__file__).resolve().parents[2]
SCORES  = REPO / "phase2_rebuild" / "results" / "scores"
PROC    = REPO / "phase2_rebuild" / "data" / "processed"
LABELS  = REPO / "phase2_rebuild" / "data" / "labels"
ROUND4  = REPO / "rebuttal_artifacts" / "round4" / "r42_downstream"
ROUND4.mkdir(parents=True, exist_ok=True)
R41     = REPO / "rebuttal_artifacts" / "round4" / "r41_xgb_pipeline"

SEED       = 42
N_FOLDS    = 5
DATASETS   = ["D1", "D2", "D3"]
BASE_COLS  = ["rule", "stat", "iforest", "lof"]
EPS        = 1e-9
TIMEOUT_S  = 120    # pyod detector timeout (seconds)

# 35 queries reused verbatim from F1b
QUERIES: list[dict] = [
    {"id":"T01","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "sql":'SELECT ROUND(SUM("Total_OT_Paid"::numeric), 2) AS total_ot FROM {table}',
     "result_type":"scalar"},
    {"id":"T02","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "sql":'SELECT COUNT(*) AS n FROM {table} WHERE "Total_OT_Paid" > 0 AND "Regular_Hours" = 0',
     "result_type":"scalar"},
    {"id":"T03","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "sql":'SELECT ROUND(AVG("Regular_Gross_Paid"::numeric), 2) AS avg_gross FROM {table}',
     "result_type":"scalar"},
    {"id":"T04","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "sql":'SELECT COUNT(*) AS n FROM {table} WHERE "Regular_Gross_Paid" > 200000',
     "result_type":"scalar"},
    {"id":"T05","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "sql":('SELECT "Agency_Name", ROUND(SUM("Total_OT_Paid"::numeric), 2) AS agency_ot '
            'FROM {table} GROUP BY "Agency_Name" ORDER BY agency_ot DESC LIMIT 5'),
     "result_type":"table"},
    {"id":"T06","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "sql":('SELECT ROUND(SUM("Total_OT_Paid"::numeric) / '
            'NULLIF(SUM("Regular_Gross_Paid"::numeric), 0), 4) AS ot_ratio FROM {table}'),
     "result_type":"scalar"},
    {"id":"T07","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "sql":('SELECT "Title_Description", ROUND(AVG("Regular_Gross_Paid"::numeric), 2) AS avg_gp '
            'FROM {table} WHERE "Title_Description" ILIKE \'%ANALYST%\' '
            'GROUP BY "Title_Description" ORDER BY avg_gp DESC LIMIT 10'),
     "result_type":"table"},
    {"id":"T08","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "sql":'SELECT COUNT(DISTINCT "Title_Description") AS n_titles FROM {table}',
     "result_type":"scalar"},
    {"id":"T09","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "sql":'SELECT ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY "Regular_Gross_Paid"), 2) AS p90 FROM {table}',
     "result_type":"scalar"},
    {"id":"T10","dataset":"D2","stratum":"targeted","dialect":"postgres",
     "sql":('SELECT "Agency_Name", SUM("Total_OT_Paid"::numeric) AS agency_ot, '
            'RANK() OVER (ORDER BY SUM("Total_OT_Paid"::numeric) DESC) AS rnk '
            'FROM {table} GROUP BY "Agency_Name" ORDER BY rnk LIMIT 5'),
     "result_type":"table"},
    {"id":"T11","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "sql":'SELECT "EDUCATION", COUNT(*) AS n FROM {table} GROUP BY "EDUCATION" ORDER BY "EDUCATION"',
     "result_type":"table"},
    {"id":"T12","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "sql":'SELECT COUNT(*) AS n_invalid FROM {table} WHERE "EDUCATION" NOT IN (1, 2, 3, 4, 5, 6)',
     "result_type":"scalar"},
    {"id":"T13","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "sql":'SELECT ROUND(AVG("LIMIT_BAL"::numeric), 2) AS avg_limit FROM {table}',
     "result_type":"scalar"},
    {"id":"T14","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "sql":'SELECT COUNT(*) AS n_outlier FROM {table} WHERE "LIMIT_BAL" > 500000',
     "result_type":"scalar"},
    {"id":"T15","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "sql":'SELECT COUNT(*) AS n_neg FROM {table} WHERE "BILL_AMT1" < 0',
     "result_type":"scalar"},
    {"id":"T16","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "sql":'SELECT ROUND(SUM("BILL_AMT1"::numeric), 2) AS sum_bill1 FROM {table}',
     "result_type":"scalar"},
    {"id":"T17","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "sql":'SELECT COUNT(*) AS n_bad_pay FROM {table} WHERE "PAY_0" > 8',
     "result_type":"scalar"},
    {"id":"T18","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "sql":'SELECT ROUND(AVG("AGE"::numeric), 2) AS avg_age FROM {table}',
     "result_type":"scalar"},
    {"id":"T19","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "sql":'SELECT COUNT(*) AS n_bad_age FROM {table} WHERE "AGE" < 18 OR "AGE" > 100',
     "result_type":"scalar"},
    {"id":"T20","dataset":"D3","stratum":"targeted","dialect":"postgres",
     "sql":('SELECT "EDUCATION", ROUND(AVG("LIMIT_BAL"::numeric), 2) AS avg_lim '
            'FROM {table} GROUP BY "EDUCATION" ORDER BY "EDUCATION"'),
     "result_type":"table"},
    {"id":"C01","dataset":"D2","stratum":"control","dialect":"postgres",
     "sql":'SELECT COUNT(DISTINCT "Agency_Name") AS n_agencies FROM {table}',
     "result_type":"scalar"},
    {"id":"C02","dataset":"D2","stratum":"control","dialect":"postgres",
     "sql":('SELECT "Work_Location_Borough", COUNT(*) AS n FROM {table} '
            'GROUP BY "Work_Location_Borough" ORDER BY n DESC'),
     "result_type":"table"},
    {"id":"C03","dataset":"D2","stratum":"control","dialect":"postgres",
     "sql":('SELECT "Pay_Basis", COUNT(*) AS n FROM {table} '
            'GROUP BY "Pay_Basis" ORDER BY "Pay_Basis"'),
     "result_type":"table"},
    {"id":"C04","dataset":"D2","stratum":"control","dialect":"postgres",
     "sql":'SELECT ROUND(AVG("Regular_Hours"::numeric), 4) AS avg_hours FROM {table}',
     "result_type":"scalar"},
    {"id":"C05","dataset":"D2","stratum":"control","dialect":"postgres",
     "sql":'SELECT ROUND(SUM("Total_Other_Pay"::numeric), 2) AS total_other FROM {table}',
     "result_type":"scalar"},
    {"id":"C06","dataset":"D2","stratum":"control","dialect":"postgres",
     "sql":'SELECT ROUND(AVG("OT_Hours"::numeric), 4) AS avg_ot_hrs FROM {table}',
     "result_type":"scalar"},
    {"id":"C07","dataset":"D2","stratum":"control","dialect":"postgres",
     "sql":'SELECT COUNT(*) AS n_active FROM {table} WHERE "Leave_Status_as_of_June_30" = \'ACTIVE\'',
     "result_type":"scalar"},
    {"id":"C08","dataset":"D2","stratum":"control","dialect":"postgres",
     "sql":('SELECT "Agency_Name", ROUND(AVG("Regular_Hours"::numeric), 4) AS avg_hrs, '
            'RANK() OVER (ORDER BY AVG("Regular_Hours"::numeric) DESC) AS rnk '
            'FROM {table} GROUP BY "Agency_Name" ORDER BY rnk LIMIT 10'),
     "result_type":"table"},
    {"id":"C09","dataset":"D3","stratum":"control","dialect":"postgres",
     "sql":'SELECT "SEX", COUNT(*) AS n FROM {table} GROUP BY "SEX" ORDER BY "SEX"',
     "result_type":"table"},
    {"id":"C10","dataset":"D3","stratum":"control","dialect":"postgres",
     "sql":'SELECT "MARRIAGE", COUNT(*) AS n FROM {table} GROUP BY "MARRIAGE" ORDER BY "MARRIAGE"',
     "result_type":"table"},
    {"id":"C11","dataset":"D3","stratum":"control","dialect":"postgres",
     "sql":'SELECT ROUND(AVG("BILL_AMT2"::numeric), 2) AS avg_bill2 FROM {table}',
     "result_type":"scalar"},
    {"id":"C12","dataset":"D3","stratum":"control","dialect":"postgres",
     "sql":'SELECT ROUND(SUM("PAY_AMT1"::numeric), 2) AS sum_pay1 FROM {table}',
     "result_type":"scalar"},
    {"id":"C13","dataset":"D3","stratum":"control","dialect":"postgres",
     "sql":('SELECT "default_payment_next_month", COUNT(*) AS n FROM {table} '
            'GROUP BY "default_payment_next_month" ORDER BY "default_payment_next_month"'),
     "result_type":"table"},
    {"id":"C14","dataset":"D3","stratum":"control","dialect":"postgres",
     "sql":'SELECT ROUND(AVG("PAY_AMT3"::numeric), 2) AS avg_pay3 FROM {table}',
     "result_type":"scalar"},
    {"id":"C15","dataset":"D3","stratum":"control","dialect":"postgres",
     "sql":'SELECT COUNT(*) AS n_delin FROM {table} WHERE "PAY_2" >= 2',
     "result_type":"scalar"},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def metrics_from_scores(y: np.ndarray, s: np.ndarray) -> dict:
    auc_pr = float(average_precision_score(y, s)) if s.std() > 0 else float("nan")
    prec, rec, thr = precision_recall_curve(y, s)
    f1s = (2 * prec[:-1] * rec[:-1]) / np.where(
        (prec[:-1] + rec[:-1]) > 0, prec[:-1] + rec[:-1], 1.0)
    best = int(np.nanargmax(f1s)) if len(f1s) else 0
    best_thr = float(thr[best]) if len(thr) else 0.5
    pred = (s >= best_thr).astype(np.int8)
    p, r, f, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    fpr = float(((pred == 1) & (y == 0)).sum() / max(1, (y == 0).sum()))
    return {
        "auc_pr": round(auc_pr, 4), "best_threshold": round(best_thr, 4),
        "precision": round(float(p), 4), "recall": round(float(r), 4),
        "f1": round(float(f), 4), "fpr_at_best_f1": round(fpr, 4),
    }


def xgb_oof(y: np.ndarray, base: np.ndarray, seed: int = SEED) -> np.ndarray:
    n_neg, n_pos = int((y == 0).sum()), int((y == 1).sum())
    spw = max(1.0, n_neg / max(1, n_pos))
    out = np.zeros(len(y), dtype=float)
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
    for tr, te in skf.split(base, y):
        clf = XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05,
                            subsample=0.8, colsample_bytree=1.0,
                            scale_pos_weight=spw, random_state=seed,
                            eval_metric="logloss", use_label_encoder=False,
                            verbosity=0, n_jobs=-1)
        clf.fit(base[tr], y[tr])
        out[te] = clf.predict_proba(base[te])[:, 1]
    return out


def normalise_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.replace(" ", "_").replace("/", "_")
                   .replace("(", "").replace(")", "").replace("-", "_")
                  for c in df.columns]
    return df


# ---------------------------------------------------------------------------
# A. Calibration + routing
# ---------------------------------------------------------------------------
def run_calibration() -> pd.DataFrame:
    print("[R4.2-A] Calibration + routing ...", flush=True)
    rows = []
    for did in DATASETS:
        sc = pd.read_parquet(SCORES / f"{did}_scores.parquet")
        y = sc["y"].to_numpy()
        s_xgb = sc["hybrid_xgb"].to_numpy()
        s_lr  = sc["hybrid_lr"].to_numpy()

        for det, s in [("hybrid_xgb", s_xgb), ("hybrid_lr", s_lr)]:
            brier_raw = float(brier_score_loss(y, s))
            # ECE: 10 equal-width bins
            frac_pos, mean_pred = calibration_curve(y, s, n_bins=10, strategy="uniform")
            ece = float(np.mean(np.abs(frac_pos - mean_pred)))

            # Platt scaling (hold-out 20%)
            n = len(y)
            idx = np.random.default_rng(SEED).permutation(n)
            tr_idx, te_idx = idx[:int(0.8*n)], idx[int(0.8*n):]
            platt = LogisticRegression(max_iter=500, solver="liblinear")
            platt.fit(s[tr_idx].reshape(-1, 1), y[tr_idx])
            s_cal = platt.predict_proba(s[te_idx].reshape(-1, 1))[:, 1]
            brier_platt = float(brier_score_loss(y[te_idx], s_cal))
            frac_p2, mean_p2 = calibration_curve(y[te_idx], s_cal, n_bins=10, strategy="uniform")
            ece_platt = float(np.mean(np.abs(frac_p2 - mean_p2)))

            rows.append({
                "dataset": did, "detector": det,
                "ece_raw": round(ece, 5), "brier_raw": round(brier_raw, 5),
                "ece_platt": round(ece_platt, 5), "brier_platt": round(brier_platt, 5),
                "platt_improvement": round(ece - ece_platt, 5),
                "platt_necessary": ece > 0.02,
            })
            print(f"  {did} {det}: ECE_raw={ece:.5f}  ECE_platt={ece_platt:.5f}  "
                  f"Brier_raw={brier_raw:.5f}", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(ROUND4 / "calibration_routing_xgb.csv", index=False)

    # 3-lane routing table
    budget_rows = []
    for did in DATASETS:
        sc = pd.read_parquet(SCORES / f"{did}_scores.parquet")
        y = sc["y"].to_numpy()
        s = sc["hybrid_xgb"].to_numpy()
        m = metrics_from_scores(y, s)
        tau_star = m["best_threshold"]
        tau_lo = float(np.quantile(s, 0.50))   # low-confidence cut
        for t_lo in [tau_lo]:
            n_auto_clean = int((s < t_lo).sum())
            n_review     = int(((s >= t_lo) & (s < tau_star)).sum())
            n_quarantine = int((s >= tau_star).sum())
            tp_q = int(((s >= tau_star) & (y == 1)).sum())
            fp_q = int(((s >= tau_star) & (y == 0)).sum())
            fn_miss = int(((s < tau_star) & (y == 1)).sum())
            budget_rows.append({
                "dataset": did, "tau_lo": round(t_lo, 4), "tau_star": round(tau_star, 4),
                "n_auto_clean": n_auto_clean, "n_review": n_review,
                "n_quarantine": n_quarantine,
                "fp_fraction_quarantine": round(fp_q / max(1, n_quarantine), 4),
                "fn_escaped": fn_miss,
            })
    rb_df = pd.DataFrame(budget_rows)
    rb_df.to_csv(ROUND4 / "review_budget_xgb.csv", index=False)
    print(f"  calibration_routing_xgb.csv: {len(df)} rows  review_budget_xgb.csv: {len(rb_df)} rows",
          flush=True)
    return df


# ---------------------------------------------------------------------------
# B. Joint gate rerun with hybrid_xgb tau*
# ---------------------------------------------------------------------------
def _to_float(v):
    try: return float(v)
    except: return None

def _norm_val(v) -> str:
    if v is None: return "NULL"
    f = _to_float(v)
    return f"{round(f,4)}" if f is not None else str(v).strip().lower()

def _null_mag(tag):
    return {"rel_err": None, "jaccard": None, "exec_error": tag}

def compare_magnitude(ref, cand, rtype="scalar") -> dict:
    if ref is None: return _null_mag("ref_error")
    if cand is None: return _null_mag("cand_error")
    if rtype == "scalar" or (len(ref) == 1 and len(ref[0]) == 1):
        rv = _to_float(ref[0][0]) if ref else None
        cv = _to_float(cand[0][0]) if cand else None
        if rv is not None and cv is not None:
            rel = abs(rv - cv) / max(abs(rv), EPS)
            return {"rel_err": round(rel, 8), "jaccard": 1.0 if rel < 1e-6 else 0.0,
                    "exec_error": None}
        match = str(ref[0][0]).strip().lower() == str(cand[0][0]).strip().lower()
        return {"rel_err": 0.0 if match else 1.0, "jaccard": 1.0 if match else 0.0,
                "exec_error": None}
    # Table
    def rk(row): return "|".join(_norm_val(v) for v in row)
    rs, cs = set(rk(r) for r in ref), set(rk(r) for r in cand)
    j = len(rs & cs) / max(1, len(rs | cs))
    # Numeric alignment
    cand_map = {}
    for row in cand:
        k = str(row[0]).strip().lower() if row else ""
        cand_map.setdefault(k, []).append(row)
    errs = []
    for row in ref:
        k = str(row[0]).strip().lower() if row else ""
        if k in cand_map:
            for rv, cv in zip(row, cand_map[k][0]):
                rf, cf = _to_float(rv), _to_float(cv)
                if rf is not None and cf is not None:
                    errs.append(abs(rf - cf) / max(abs(rf), EPS))
    max_re = float(np.max(errs)) if errs else float("nan")
    headline = max(1.0 - j, max_re if not np.isnan(max_re) else 0.0)
    return {"rel_err": round(headline, 8), "jaccard": round(j, 4), "exec_error": None}


def transpile_1hop(sql: str):
    try:
        return sqlglot.transpile(sql, read="postgres", write="duckdb")[0], None
    except Exception as ex:
        return None, str(ex)


def run_jointgate_xgb() -> pd.DataFrame:
    print("[R4.2-B] Joint gate rerun with hybrid_xgb tau* ...", flush=True)
    bl_xgb = pd.read_csv(R41 / "baseline_xgb.csv")
    con = duckdb.connect(":memory:")
    schema = {}

    for did, true_f, inj_f in [
        ("D2", "D2_nyc_fy2024", "D2_injected"),
        ("D3", "D3_uci_credit", "D3_injected"),
    ]:
        df_true  = normalise_cols(pd.read_parquet(PROC / f"{true_f}.parquet"))
        df_dirty = normalise_cols(pd.read_parquet(PROC / f"{inj_f}.parquet"))
        sc = pd.read_parquet(SCORES / f"{did}_scores.parquet")
        y  = sc["y"].to_numpy()

        tau_xgb = float(bl_xgb[(bl_xgb["dataset"]==did)&(bl_xgb["detector"]=="hybrid_xgb")]["best_threshold"].iloc[0])
        tau_lr  = float(bl_xgb[(bl_xgb["dataset"]==did)&(bl_xgb["detector"]=="hybrid_lr")]["best_threshold"].iloc[0])

        qmask_xgb = sc["hybrid_xgb"].to_numpy() >= tau_xgb
        qmask_lr  = sc["hybrid_lr"].to_numpy()  >= tau_lr
        n_true = len(df_true)

        n_q_xgb = int(qmask_xgb.sum())
        n_tp_xgb = int((qmask_xgb & (y>0.5)).sum())
        n_fp_xgb = int((qmask_xgb & (y<0.5)).sum())
        n_fn_xgb = int((~qmask_xgb & (y>0.5)).sum())

        n_q_lr  = int(qmask_lr.sum())
        n_fp_lr = int((qmask_lr & (y<0.5)).sum())

        # Cleansed (XGB) and Repaired (XGB)
        df_clean = df_dirty[~qmask_xgb].reset_index(drop=True)
        df_repaired = df_dirty.copy()
        quaran_orig = np.where(qmask_xgb[:n_true])[0]
        if len(quaran_orig):
            df_repaired.iloc[quaran_orig] = df_true.iloc[quaran_orig].values
        if len(df_dirty) > n_true:
            b3_keep = ~qmask_xgb[n_true:]
            df_repaired = pd.concat([
                df_repaired.iloc[:n_true],
                df_dirty.iloc[n_true:][b3_keep],
            ], ignore_index=True)

        pfx = "payroll" if did == "D2" else "credit"
        for tname, df in [(f"{pfx}_true", df_true),(f"{pfx}_dirty", df_dirty),
                          (f"{pfx}_clean_xgb", df_clean),(f"{pfx}_repaired_xgb", df_repaired)]:
            con.execute(f"DROP TABLE IF EXISTS {tname}")
            con.register(f"_tmp_{tname}", df)
            con.execute(f"CREATE TABLE {tname} AS SELECT * FROM _tmp_{tname}")

        schema[did] = {
            "true_t": f"{pfx}_true", "dirty_t": f"{pfx}_dirty",
            "clean_t": f"{pfx}_clean_xgb", "repaired_t": f"{pfx}_repaired_xgb",
            "tau_xgb": tau_xgb, "tau_lr": tau_lr,
            "n_q_xgb": n_q_xgb, "n_tp_xgb": n_tp_xgb,
            "n_fp_xgb": n_fp_xgb, "n_fn_xgb": n_fn_xgb,
            "n_q_lr": n_q_lr, "n_fp_lr": n_fp_lr,
        }
        print(f"  {did}: tau_xgb={tau_xgb:.4f}  quarantined={n_q_xgb:,}  "
              f"TP={n_tp_xgb}  FP={n_fp_xgb}  FN={n_fn_xgb}  "
              f"(vs LR: q={n_q_lr:,} fp={n_fp_lr:,})", flush=True)

    rows = []
    for q in QUERIES:
        did = q["dataset"]
        si  = schema[did]
        rt  = q["result_type"]
        for cond, tbl in [("true_src", si["true_t"]), ("dirty_src", si["dirty_t"]),
                          ("clean_xgb_src", si["clean_t"]),
                          ("repaired_xgb_src", si["repaired_t"])]:
            sql = q["sql"].format(table=tbl)
            try:
                res = con.execute(sql).fetchall()
                err = None
            except Exception as ex:
                res, err = None, str(ex)
            rows.append({
                "query_id": q["id"], "dataset": did, "stratum": q["stratum"],
                "condition": cond, "result_type": rt,
                "result": str(res)[:300] if res else None, "exec_error": err,
            })

    # Compute magnitudes: all non-ref conditions vs true_src
    ref_map: dict[tuple, list | None] = {}
    cand_map: dict[tuple, tuple] = {}
    for r in rows:
        k = (r["query_id"], r["dataset"])
        if r["condition"] == "true_src":
            try:
                ref_map[k] = con.execute(QUERIES[next(i for i,q in enumerate(QUERIES) if q["id"]==r["query_id"])]["sql"].format(table=schema[r["dataset"]]["true_t"])).fetchall()
            except:
                ref_map[k] = None

    mag_rows = []
    for q in QUERIES:
        did = q["dataset"]; si = schema[did]; rt = q["result_type"]
        k = (q["id"], did)
        try: ref = con.execute(q["sql"].format(table=si["true_t"])).fetchall()
        except: ref = None
        for cond, tbl in [("dirty_src", si["dirty_t"]),
                          ("clean_xgb_src", si["clean_t"]),
                          ("repaired_xgb_src", si["repaired_t"])]:
            try: cand = con.execute(q["sql"].format(table=tbl)).fetchall()
            except: cand = None
            m = compare_magnitude(ref, cand, rt)
            mag_rows.append({
                "query_id": q["id"], "dataset": did, "stratum": q["stratum"],
                "condition": cond, **m,
            })
        print(f"  {q['id']}: dirty={next((r['rel_err'] for r in mag_rows if r['query_id']==q['id'] and r['condition']=='dirty_src'), None):.4f}  "
              f"clean_xgb={next((r['rel_err'] for r in mag_rows if r['query_id']==q['id'] and r['condition']=='clean_xgb_src'), None):.4f}  "
              f"repaired_xgb={next((r['rel_err'] for r in mag_rows if r['query_id']==q['id'] and r['condition']=='repaired_xgb_src'), None):.4f}",
              flush=True)

    df_mag = pd.DataFrame(mag_rows)
    df_mag.to_csv(ROUND4 / "jointgate_xgb.csv", index=False)

    # Magnitude distribution summary
    dist_rows = []
    for cond in ["dirty_src", "clean_xgb_src", "repaired_xgb_src"]:
        for stratum in ["all", "targeted", "control"]:
            sub = df_mag if stratum == "all" else df_mag[df_mag["stratum"]==stratum]
            vals = sub[sub["condition"]==cond]["rel_err"].dropna()
            if len(vals):
                dist_rows.append({
                    "condition": cond, "stratum": stratum, "n": len(vals),
                    "median": round(float(vals.median()), 6),
                    "p90": round(float(vals.quantile(0.9)), 6),
                    "max": round(float(vals.max()), 6),
                })
    pd.DataFrame(dist_rows).to_csv(ROUND4 / "jointgate_magnitudes_xgb.csv", index=False)

    # Analyst cost with XGB
    cost_rows = []
    for did, si in schema.items():
        cost_rows.append({
            "dataset": did,
            "detector": "hybrid_xgb", "tau": si["tau_xgb"],
            "n_quarantined": si["n_q_xgb"], "n_tp": si["n_tp_xgb"],
            "n_fp": si["n_fp_xgb"], "n_fn": si["n_fn_xgb"],
            "fp_fraction": round(si["n_fp_xgb"] / max(1, si["n_q_xgb"]), 4),
        })
        cost_rows.append({
            "dataset": did,
            "detector": "hybrid_lr (F1b reference)", "tau": si["tau_lr"],
            "n_quarantined": si["n_q_lr"], "n_tp": None,
            "n_fp": si["n_fp_lr"], "n_fn": None,
            "fp_fraction": round(si["n_fp_lr"] / max(1, si["n_q_lr"]), 4),
        })
    pd.DataFrame(cost_rows).to_csv(ROUND4 / "analyst_cost_xgb.csv", index=False)
    print(f"  jointgate_xgb.csv: {len(df_mag)} rows", flush=True)
    return df_mag


# ---------------------------------------------------------------------------
# C. Modern baselines (pyod)
# ---------------------------------------------------------------------------
def _run_pyod_detector(name: str, did: str, X: np.ndarray, y: np.ndarray,
                        contamination: float) -> dict:
    from sklearn.preprocessing import StandardScaler as SS
    Xs = SS().fit_transform(X.astype(float))
    t0 = time.perf_counter()
    try:
        if name == "ECOD":
            from pyod.models.ecod import ECOD
            clf = ECOD(contamination=contamination)
        elif name == "COPOD":
            from pyod.models.copod import COPOD
            clf = COPOD(contamination=contamination)
        elif name == "HBOS":
            from pyod.models.hbos import HBOS
            clf = HBOS(contamination=contamination)
        elif name == "LODA":
            from pyod.models.loda import LODA
            clf = LODA(contamination=contamination)
        elif name == "AutoEncoder":
            from pyod.models.auto_encoder import AutoEncoder
            clf = AutoEncoder(contamination=contamination, epochs=10,
                              hidden_neurons=[16, 4, 4, 16],
                              verbose=0, random_state=SEED)
        elif name == "DeepSVDD":
            from pyod.models.deep_svdd import DeepSVDD
            clf = DeepSVDD(contamination=contamination, epochs=20,
                           hidden_neurons=[8, 4], random_state=SEED,
                           verbose=0)
        elif name == "KNN":
            from pyod.models.knn import KNN
            n_nbrs = min(20, max(5, len(X) // 5000))
            clf = KNN(contamination=contamination, n_neighbors=n_nbrs)
        else:
            return {"detector": name, "dataset": did, "f1": float("nan"),
                    "auc_pr": float("nan"), "elapsed_s": 0.0, "note": "unknown"}

        clf.fit(Xs)
        scores = clf.decision_scores_
        scores = (scores - scores.min()) / max(1e-9, scores.max() - scores.min())
        elapsed = round(time.perf_counter() - t0, 2)
        m = metrics_from_scores(y, scores)
        return {**m, "detector": name, "dataset": did,
                "elapsed_s": elapsed, "note": "ok"}
    except Exception as ex:
        elapsed = round(time.perf_counter() - t0, 2)
        return {"detector": name, "dataset": did, "f1": float("nan"),
                "auc_pr": float("nan"), "elapsed_s": elapsed,
                "note": f"ERROR: {str(ex)[:100]}"}


def run_modern_baselines() -> pd.DataFrame:
    print("[R4.2-C] Modern baselines (pyod) ...", flush=True)
    # Load features from committed pipeline scripts
    import importlib.util, sys as _sys
    spec = importlib.util.spec_from_file_location(
        "pipe10", REPO / "phase2_rebuild" / "scripts" / "10_run_anomaly_experiments.py")
    mod = importlib.util.module_from_spec(spec)
    _sys.modules["pipe10"] = mod
    spec.loader.exec_module(mod)

    DETECTORS_PYOD = ["ECOD", "COPOD", "HBOS", "LODA", "AutoEncoder", "DeepSVDD", "KNN"]
    rows = []
    # First add hybrid_xgb as the DataFlow entry (already computed)
    bl_xgb = pd.read_csv(R41 / "baseline_xgb.csv")
    for did in DATASETS:
        row = bl_xgb[(bl_xgb["dataset"]==did) & (bl_xgb["detector"]=="hybrid_xgb")].iloc[0]
        rows.append({
            "detector": "DataFlow_hybrid_xgb", "dataset": did,
            "f1": row["f1"], "auc_pr": row["auc_pr"],
            "precision": row["precision"], "recall": row["recall"],
            "elapsed_s": float("nan"), "note": "DataFlow (adopted stacker)",
        })

    for did in DATASETS:
        sc = pd.read_parquet(SCORES / f"{did}_scores.parquet")
        y = sc["y"].to_numpy()
        contamination = float(y.mean())
        feat_fn = mod.FEATURE_FNS[did]
        # Need the original (non-injected) df for feature extraction
        df_inj = pd.read_parquet(PROC / f"{did}_injected.parquet").reset_index(drop=True)
        X, _ = feat_fn(df_inj)
        print(f"  {did}: X.shape={X.shape}  contamination={contamination:.4f}", flush=True)

        for det_name in DETECTORS_PYOD:
            print(f"    {did}/{det_name} ...", end=" ", flush=True)
            result = _run_pyod_detector(det_name, did, X, y, contamination)
            rows.append(result)
            print(f"F1={result.get('f1','?'):.4f}  ({result['elapsed_s']:.1f}s)  {result['note'][:40]}",
                  flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(ROUND4 / "modern_baselines_vs_xgb.csv", index=False)
    print(f"  modern_baselines_vs_xgb.csv: {len(df)} rows", flush=True)
    return df


# ---------------------------------------------------------------------------
# D. Extended stacker (XGB with ECOD + DeepSVDD)
# ---------------------------------------------------------------------------
def run_extended_stacker() -> pd.DataFrame:
    print("[R4.2-D] Extended stacker (Base4 vs Base6 with XGB) ...", flush=True)
    import importlib.util, sys as _sys
    spec = importlib.util.spec_from_file_location(
        "pipe10b", REPO / "phase2_rebuild" / "scripts" / "10_run_anomaly_experiments.py")
    mod = importlib.util.module_from_spec(spec)
    _sys.modules["pipe10b"] = mod
    spec.loader.exec_module(mod)

    rows = []
    importances_rows = []

    for did in DATASETS:
        sc = pd.read_parquet(SCORES / f"{did}_scores.parquet")
        y = sc["y"].to_numpy()
        contamination = float(y.mean())
        base4 = sc[BASE_COLS].to_numpy()

        # Base4 XGB (already done in R4.1 — just retrieve)
        xgb_base4 = sc["hybrid_xgb"].to_numpy()
        m4 = metrics_from_scores(y, xgb_base4)
        rows.append({**m4, "dataset": did, "base_set": "Base4",
                     "detectors": "rule,stat,iforest,lof"})

        # Add ECOD score
        df_inj = pd.read_parquet(PROC / f"{did}_injected.parquet").reset_index(drop=True)
        feat_fn = mod.FEATURE_FNS[did]
        X, _ = feat_fn(df_inj)
        from sklearn.preprocessing import StandardScaler as SS
        Xs = SS().fit_transform(X.astype(float))

        print(f"  {did} ECOD ...", flush=True)
        try:
            from pyod.models.ecod import ECOD
            ecod_clf = ECOD(contamination=contamination)
            ecod_clf.fit(Xs)
            ecod_s = ecod_clf.decision_scores_
            ecod_s = (ecod_s - ecod_s.min()) / max(1e-9, ecod_s.max() - ecod_s.min())
            base5 = np.column_stack([base4, ecod_s])
            xgb_base5 = xgb_oof(y, base5)
            m5 = metrics_from_scores(y, xgb_base5)
            rows.append({**m5, "dataset": did, "base_set": "Base4+ECOD",
                         "detectors": "rule,stat,iforest,lof,ecod"})
        except Exception as ex:
            rows.append({"dataset": did, "base_set": "Base4+ECOD", "f1": float("nan"),
                         "note": str(ex)[:80], "detectors": "rule,stat,iforest,lof,ecod"})
            base5, xgb_base5 = base4, xgb_base4
            ecod_s = np.zeros(len(y))

        print(f"  {did} DeepSVDD ...", flush=True)
        try:
            from pyod.models.deep_svdd import DeepSVDD
            svdd = DeepSVDD(contamination=contamination, epochs=20,
                            hidden_neurons=[8,4], random_state=SEED, verbose=0)
            svdd.fit(Xs)
            svdd_s = svdd.decision_scores_
            svdd_s = (svdd_s - svdd_s.min()) / max(1e-9, svdd_s.max() - svdd_s.min())
            base6 = np.column_stack([base4, ecod_s, svdd_s])
            xgb_base6 = xgb_oof(y, base6)
            m6 = metrics_from_scores(y, xgb_base6)
            rows.append({**m6, "dataset": did, "base_set": "Base6",
                         "detectors": "rule,stat,iforest,lof,ecod,deep_svdd"})
        except Exception as ex:
            rows.append({"dataset": did, "base_set": "Base6", "f1": float("nan"),
                         "note": str(ex)[:80], "detectors": "rule,stat,iforest,lof,ecod,deep_svdd"})

        # Feature importances: fit non-OOF XGB on full data
        n_neg, n_pos = int((y==0).sum()), int((y==1).sum())
        spw = max(1.0, n_neg / max(1, n_pos))
        clf_full = XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05,
                                  subsample=0.8, colsample_bytree=1.0,
                                  scale_pos_weight=spw, random_state=SEED,
                                  eval_metric="logloss", use_label_encoder=False,
                                  verbosity=0, n_jobs=-1)
        clf_full.fit(base4, y)
        for feat, imp in zip(BASE_COLS, clf_full.feature_importances_):
            importances_rows.append({
                "dataset": did, "feature": feat,
                "importance": round(float(imp), 5),
            })
        print(f"  {did} importances: {dict(zip(BASE_COLS, clf_full.feature_importances_.round(3)))}",
              flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(ROUND4 / "extended_stacker_xgb.csv", index=False)
    pd.DataFrame(importances_rows).to_csv(ROUND4 / "xgb_feature_importance.csv", index=False)
    print(f"  extended_stacker_xgb.csv: {len(df)} rows", flush=True)
    return df


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def write_report(cal: pd.DataFrame, jg: pd.DataFrame,
                 baselines: pd.DataFrame, ext: pd.DataFrame, elapsed: float):
    cost = pd.read_csv(ROUND4 / "analyst_cost_xgb.csv")
    magnitudes = pd.read_csv(ROUND4 / "jointgate_magnitudes_xgb.csv")
    importances = pd.read_csv(ROUND4 / "xgb_feature_importance.csv")

    with open(ROUND4 / "R42_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# R4.2: Downstream Experiments — hybrid_xgb\n\n")

        # --- A. Calibration ---
        f.write("## A. Calibration\n\n")
        f.write("Key question: is Platt scaling still needed for hybrid_xgb?\n\n")
        try:
            f.write(cal[["dataset","detector","ece_raw","brier_raw","ece_platt",
                         "brier_platt","platt_necessary"]].to_markdown(index=False) + "\n\n")
        except:
            f.write(cal.to_string(index=False) + "\n\n")
        xgb_ece = cal[cal["detector"]=="hybrid_xgb"]["ece_raw"].mean()
        lr_ece  = cal[cal["detector"]=="hybrid_lr"]["ece_raw"].mean()
        f.write(f"Mean raw ECE: hybrid_xgb={xgb_ece:.5f}  hybrid_lr={lr_ece:.5f}. "
                f"{'Platt scaling NOT required for XGB (ECE < 0.02).' if xgb_ece < 0.02 else 'Platt scaling still beneficial.'}\n\n")

        # --- B. Joint gate ---
        f.write("## B. Joint gate with hybrid_xgb\n\n")
        f.write("### Analyst cost comparison: hybrid_xgb vs hybrid_lr\n\n")
        try:
            f.write(cost.to_markdown(index=False) + "\n\n")
        except:
            f.write(cost.to_string(index=False) + "\n\n")

        f.write("### Relative-error magnitude (median) by condition\n\n")
        try:
            f.write(magnitudes[magnitudes["stratum"]=="all"].to_markdown(index=False) + "\n\n")
        except:
            f.write(magnitudes.to_string(index=False) + "\n\n")

        # --- C. Modern baselines ---
        f.write("## C. Modern baselines vs hybrid_xgb\n\n")
        try:
            bl_piv = baselines[["detector","dataset","f1","auc_pr","note"]].pivot_table(
                index="detector", columns="dataset", values="f1").round(4)
            f.write(bl_piv.to_markdown() + "\n\n")
        except:
            f.write(baselines[["detector","dataset","f1"]].to_string(index=False) + "\n\n")

        f.write("### Verdicts per dataset\n\n")
        for did in DATASETS:
            sub = baselines[baselines["dataset"]==did].copy()
            sub = sub.sort_values("f1", ascending=False)
            xgb_f1 = float(sub[sub["detector"]=="DataFlow_hybrid_xgb"]["f1"].values[0])
            better = sub[sub["f1"] > xgb_f1 + 0.01]["detector"].tolist()
            worse  = sub[sub["f1"] < xgb_f1 - 0.01]["detector"].tolist()
            f.write(f"- **{did}**: DataFlow_hybrid_xgb F1={xgb_f1:.4f}. "
                    f"Better: {better or 'none'}. Worse: {worse}.\n")
        f.write("\n")

        # --- D. Extended stacker ---
        f.write("## D. Extended stacker (XGB)\n\n")
        try:
            f.write(ext[["dataset","base_set","f1","auc_pr","detectors"]].to_markdown(index=False) + "\n\n")
        except:
            f.write(ext.to_string(index=False) + "\n\n")

        f.write("### XGB feature importances\n\n")
        try:
            imp_piv = importances.pivot(index="feature", columns="dataset", values="importance").round(4)
            f.write(imp_piv.to_markdown() + "\n\n")
        except:
            f.write(importances.to_string(index=False) + "\n\n")

        f.write(f"\n---\nGenerated in {elapsed:.1f}s\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    t0 = time.perf_counter()

    cal_df = run_calibration()
    jg_df  = run_jointgate_xgb()
    bl_df  = run_modern_baselines()
    ext_df = run_extended_stacker()

    elapsed = time.perf_counter() - t0
    write_report(cal_df, jg_df, bl_df, ext_df, elapsed)

    print(f"\n[R4.2] Done in {elapsed:.1f}s")
    print(f"Outputs: {ROUND4}")

    # Quick summary
    print("\n=== CALIBRATION (mean ECE) ===")
    print(cal_df.groupby("detector")[["ece_raw","ece_platt"]].mean().round(5))
    print("\n=== JOINT GATE MEDIAN REL-ERR (hybrid_xgb) ===")
    magnitudes = pd.read_csv(ROUND4 / "jointgate_magnitudes_xgb.csv")
    print(magnitudes[magnitudes["stratum"]=="all"][["condition","median"]].to_string(index=False))
    print("\n=== MODERN BASELINES (F1) ===")
    try:
        bl = pd.read_csv(ROUND4 / "modern_baselines_vs_xgb.csv")
        print(bl[["detector","dataset","f1"]].pivot_table(
            index="detector", columns="dataset", values="f1").round(4))
    except: pass


if __name__ == "__main__":
    main()
