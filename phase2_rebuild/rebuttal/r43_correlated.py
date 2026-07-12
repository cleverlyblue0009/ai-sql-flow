"""
R4.3: Correlated failure injection — CLUSTERED and CO-OCCURRING modes.

Research question: Does hybrid_xgb performance degrade when anomalies are
(a) CLUSTERED: all injections of one family concentrated in a single cohort, or
(b) CO-OCCURRING: multiple families injected into the same rows?

Both modes preserve total injection count (~5% prevalence) but change the
spatial/correlation structure. Comparison baseline is the INDEPENDENT injection
(standard random placement, same as committed datasets).

Datasets tested:
  D3 (UCI credit, 30k rows) — all three modes
  D2 (NYC payroll, subsampled to 50k rows) — all three modes

Outputs: rebuttal_artifacts/round4/r43_correlated/
  r43_correlated_results.csv  — (dataset, mode, metric, value) long format
  r43_by_family.csv           — per-family recall in each mode
  R43_REPORT.md
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (average_precision_score, f1_score,
                              precision_recall_curve,
                              precision_recall_fscore_support)
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

REPO    = Path(__file__).resolve().parents[2]
PROC    = REPO / "phase2_rebuild" / "data" / "processed"
OUTDIR  = REPO / "rebuttal_artifacts" / "round4" / "r43_correlated"
OUTDIR.mkdir(parents=True, exist_ok=True)

SEED = 42
RATE = 0.01   # 1% per family
D2_SUBSAMPLE = 50_000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def child_rng(name: str, seed: int = SEED) -> np.random.Generator:
    digest = int.from_bytes(
        hashlib.sha256(f"{seed}::{name}".encode()).digest()[:8], "big"
    )
    return np.random.default_rng(digest)


def pick(pool: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    n = min(n, len(pool))
    return np.sort(rng.choice(pool, size=n, replace=False))


def metrics_from_scores(y: np.ndarray, scores: np.ndarray) -> dict:
    if scores.std() < 1e-9 or y.sum() == 0:
        return {"f1": 0.0, "auc_pr": 0.0, "precision": 0.0, "recall": 0.0, "threshold": 0.5}
    auc_pr = float(average_precision_score(y, scores))
    prec, rec, thr = precision_recall_curve(y, scores)
    f1s = 2 * prec[:-1] * rec[:-1] / np.where(prec[:-1] + rec[:-1] > 0, prec[:-1] + rec[:-1], 1)
    best = int(np.nanargmax(f1s)) if len(f1s) else 0
    bt = float(thr[best]) if len(thr) else 0.5
    pred = (scores >= bt).astype(np.int8)
    p, r, f, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    return {"f1": float(f), "auc_pr": auc_pr,
            "precision": float(p), "recall": float(r), "threshold": bt}


def xgb_oof(y: np.ndarray, base_scores: np.ndarray, k: int = 5) -> np.ndarray:
    n_neg = int((y == 0).sum())
    n_pos = int((y == 1).sum())
    if n_pos < k:
        return np.zeros(len(y))
    spw = max(1.0, n_neg / max(1, n_pos))
    out = np.zeros(len(y), dtype=float)
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=SEED)
    for tr, te in skf.split(base_scores, y):
        clf = XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=1.0,
            scale_pos_weight=spw, random_state=SEED,
            eval_metric="logloss", use_label_encoder=False,
            verbosity=0, n_jobs=-1,
        )
        clf.fit(base_scores[tr], y[tr])
        out[te] = clf.predict_proba(base_scores[te])[:, 1]
    return out


# ---------------------------------------------------------------------------
# Feature extraction (mirrors 10_run_anomaly_experiments.py)
# ---------------------------------------------------------------------------
def safe_log10(x: np.ndarray) -> np.ndarray:
    return np.log10(np.maximum(np.abs(x), 1e-9))


def features_d3(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    edu   = df["EDUCATION"].astype(int)
    lim   = df["LIMIT_BAL"].astype(int)
    bill1 = df["BILL_AMT1"].astype(int)
    pay0  = df["PAY_0"].astype(int)
    age   = df["AGE"].astype(int)
    deflt = df["default payment next month"].astype(int)

    edu_oob  = (~edu.isin([0, 1, 2, 3, 4, 5, 6])).astype(int)
    lim_bad  = ((lim == 0) & (bill1 > 0) & (deflt == 0)).astype(int)
    bill_neg = (bill1 < 0).astype(int)
    pay_bad  = ((pay0 == -2) & (bill1 > 5000)).astype(int)
    age_bad  = ((age < 18) | (age > 95)).astype(int)

    rule = np.clip(
        0.7 * edu_oob + 0.6 * lim_bad + 0.5 * bill_neg + 0.6 * pay_bad + 0.7 * age_bad,
        0, 1
    )
    fc = ["LIMIT_BAL", "AGE", "BILL_AMT1", "PAY_0", "PAY_AMT1", "EDUCATION", "MARRIAGE", "SEX"]
    X = np.column_stack([
        df[fc].astype(float).to_numpy(),
        edu_oob.to_numpy(), lim_bad.to_numpy(),
        bill_neg.to_numpy(), pay_bad.to_numpy(), age_bad.to_numpy(),
    ])
    return X, rule.to_numpy()


def features_d2(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    base = df["Base Salary"].astype(float).fillna(0)
    rgp  = df["Regular Gross Paid"].astype(float).fillna(0)
    rh   = df["Regular Hours"].astype(float).fillna(0)
    otp  = df["Total OT Paid"].astype(float).fillna(0)

    log_rgp = np.log10(np.maximum(rgp + 1, 1e-9))
    log_rgp_s = pd.Series(log_rgp, index=df.index)
    med = log_rgp_s.groupby(df["Agency Name"]).transform("median")
    mad = log_rgp_s.groupby(df["Agency Name"]).transform(
        lambda s: (s - s.median()).abs().median()
    )
    z = (log_rgp_s - med).abs() / np.where(mad > 1e-6, 1.4826 * mad, 1.0)

    per_annum_low = (
        (df["Pay Basis"] == "per Annum") & (base > 10000) & (rgp < 0.05 * base)
    ).astype(int)
    ot_no_reg  = ((rh == 0) & (otp > 0)).astype(int)
    df_keys    = df["Last Name"].fillna("").str.upper() + "|" + df["Agency Name"].fillna("").str.upper()
    dup        = (df_keys.groupby(df_keys).cumcount() > 0).astype(int)
    title_u    = df["Title Description"].fillna("").str.upper()
    agency_u   = df["Agency Name"].fillna("").str.upper()
    title_wrong = (
        ((title_u.str.contains("TEACHER"))     & (~agency_u.str.contains("EDUCATION|DEPT OF ED")))
        | ((title_u.str.contains("FIREFIGHTER")) & (~agency_u.str.contains("FIRE")))
        | ((title_u.str.contains("LIBRARIAN"))   & (~agency_u.str.contains("LIBRARY|POLICE|EDUCATION")))
    ).astype(int)

    rule = np.clip(
        0.6 * per_annum_low + 0.6 * ot_no_reg + 0.5 * dup + 0.5 * title_wrong
        + 0.4 * (z > 4).astype(int),
        0, 1,
    )
    X = np.column_stack([
        base.to_numpy(), rgp.to_numpy(), rh.to_numpy(), otp.to_numpy(),
        log_rgp, z.to_numpy(),
        per_annum_low.to_numpy(), ot_no_reg.to_numpy(),
        dup.to_numpy(), title_wrong.to_numpy(),
    ])
    return X, rule.to_numpy()


def stat_score(X: np.ndarray) -> np.ndarray:
    Xs  = X.copy().astype(float)
    med = np.median(Xs, axis=0)
    mad = np.median(np.abs(Xs - med), axis=0)
    mad = np.where(mad > 1e-9, mad, 1.0)
    avg_z = np.abs((Xs - med) / (1.4826 * mad)).mean(axis=1)
    return 1.0 - np.exp(-avg_z / 4.0)


def iforest_score(X: np.ndarray) -> np.ndarray:
    Xs  = StandardScaler().fit_transform(X)
    iso = IsolationForest(n_estimators=200, random_state=SEED, contamination="auto", n_jobs=-1)
    iso.fit(Xs)
    raw = -iso.score_samples(Xs)
    return (raw - raw.min()) / max(1e-9, raw.max() - raw.min())


def lof_score(X: np.ndarray) -> np.ndarray:
    Xs = StandardScaler().fit_transform(X)
    n_nb = min(50, max(5, len(X) // 1000))
    lof = LocalOutlierFactor(n_neighbors=n_nb, n_jobs=-1)
    lof.fit_predict(Xs)
    raw = -lof.negative_outlier_factor_
    return (raw - raw.min()) / max(1e-9, raw.max() - raw.min())


def run_pipeline(df: pd.DataFrame, y: np.ndarray, family: np.ndarray, did: str,
                 mode: str) -> dict:
    t0 = time.time()
    feat_fn = features_d3 if did == "D3" else features_d2
    X, rule = feat_fn(df)
    stat  = stat_score(X)
    ifo   = iforest_score(X)
    lof   = lof_score(X)
    base  = np.column_stack([rule, stat, ifo, lof])
    xgb   = xgb_oof(y, base)

    row = {"dataset": did, "mode": mode, "n_rows": len(df),
           "n_anomalies": int(y.sum()), "elapsed_s": round(time.time() - t0, 1)}
    for name, sc in [("rule", rule), ("stat", stat), ("iforest", ifo),
                     ("lof", lof), ("hybrid_xgb", xgb)]:
        m = metrics_from_scores(y, sc)
        for k, v in m.items():
            row[f"{name}_{k}"] = round(v, 4) if isinstance(v, float) else v

    # Per-family recall at hybrid_xgb best threshold
    thr  = row["hybrid_xgb_threshold"]
    pred = (xgb >= thr).astype(np.int8)
    fam_rows = []
    for f in sorted({x for x in family if x}):
        mask = family == f
        tp = int((pred[mask] == 1).sum())
        n  = int(mask.sum())
        fam_rows.append({"dataset": did, "mode": mode, "family": f,
                         "n_injected": n, "recovered": tp,
                         "recall": round(tp / max(1, n), 4)})

    elapsed = round(time.time() - t0, 1)
    print(f"  {did}/{mode}: F1={row['hybrid_xgb_f1']:.4f}  "
          f"AUC-PR={row['hybrid_xgb_auc_pr']:.4f}  "
          f"anomalies={int(y.sum())}  t={elapsed}s")
    return row, fam_rows


# ---------------------------------------------------------------------------
# D3 injection variants
# ---------------------------------------------------------------------------
def inject_d3_independent(df_true: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Original random injection — 5 families × 1% = 5%."""
    df = df_true.copy().reset_index(drop=True)
    n  = len(df)
    y  = np.zeros(n, dtype=np.int8)
    fam = np.array([""] * n, dtype=object)
    used: set[int] = set()

    # C1 education OOB
    rng = child_rng("D3_C1")
    pool = df.index[df["EDUCATION"].isin([0,1,2,3,4,5,6])].to_numpy()
    pool = np.array([i for i in pool if i not in used])
    idx  = pick(pool, int(np.ceil(n * RATE)), rng)
    oob_vals = rng.choice([7, 8], size=len(idx))
    for i, v in zip(idx, oob_vals):
        df.at[i, "EDUCATION"] = int(v); y[i] = 1; fam[i] = "C1_education_out_of_domain"; used.add(int(i))

    # C2 LIMIT_BAL inconsistency (set to 0)
    rng = child_rng("D3_C2")
    pool = np.array([i for i in df.index.to_numpy() if i not in used])
    idx  = pick(pool, int(np.ceil(n * RATE)), rng)
    for i in idx:
        df.at[i, "LIMIT_BAL"] = 0; y[i] = 1; fam[i] = "C2_limitbal_inconsistency"; used.add(int(i))

    # C3 BILL_AMT1 sign violation (negate)
    rng = child_rng("D3_C3")
    pool = np.array([i for i in df.index.to_numpy() if i not in used and df.at[i, "BILL_AMT1"] > 0])
    idx  = pick(pool, int(np.ceil(n * RATE)), rng)
    for i in idx:
        df.at[i, "BILL_AMT1"] = -abs(df.at[i, "BILL_AMT1"]); y[i] = 1; fam[i] = "C3_bill_sign_violation"; used.add(int(i))

    # C4 PAY temporal violation (set PAY_0=-2, inflate BILL_AMT1)
    rng = child_rng("D3_C4")
    pool = np.array([i for i in df.index.to_numpy() if i not in used])
    idx  = pick(pool, int(np.ceil(n * RATE)), rng)
    for i in idx:
        df.at[i, "PAY_0"] = -2; df.at[i, "BILL_AMT1"] = abs(df.at[i, "BILL_AMT1"]) + 6000
        y[i] = 1; fam[i] = "C4_pay_temporal_violation"; used.add(int(i))

    # C5 AGE range violation
    rng = child_rng("D3_C5")
    pool = np.array([i for i in df.index.to_numpy() if i not in used])
    idx  = pick(pool, int(np.ceil(n * RATE)), rng)
    age_vals = rng.choice([10, 15, 105, 120], size=len(idx))
    for i, v in zip(idx, age_vals):
        df.at[i, "AGE"] = int(v); y[i] = 1; fam[i] = "C5_age_range_violation"; used.add(int(i))

    return df, y, fam


def inject_d3_clustered(df_true: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """CLUSTERED: each family injected ONLY within one cohort (EDUCATION value).
    C1→edu=2 only, C2→edu=3 only, C3→MARRIAGE=1 only, C4→SEX=2 only, C5→edu=2 only.
    Same total injection count, concentrated spatially.
    """
    df = df_true.copy().reset_index(drop=True)
    n  = len(df)
    y  = np.zeros(n, dtype=np.int8)
    fam = np.array([""] * n, dtype=object)
    used: set[int] = set()
    n_per_family = int(np.ceil(n * RATE))

    # C1 — only in EDUCATION == 2 rows
    rng  = child_rng("R43_C1_clustered")
    pool = df.index[df["EDUCATION"] == 2].to_numpy()
    idx  = pick(pool, n_per_family, rng)
    oob_vals = rng.choice([7, 8], size=len(idx))
    for i, v in zip(idx, oob_vals):
        df.at[i, "EDUCATION"] = int(v); y[i] = 1; fam[i] = "C1_education_out_of_domain"; used.add(int(i))

    # C2 — only in EDUCATION == 3 rows
    rng  = child_rng("R43_C2_clustered")
    pool = np.array([i for i in df.index[df["EDUCATION"] == 3].to_numpy() if i not in used])
    idx  = pick(pool, n_per_family, rng)
    for i in idx:
        df.at[i, "LIMIT_BAL"] = 0; y[i] = 1; fam[i] = "C2_limitbal_inconsistency"; used.add(int(i))

    # C3 — only in MARRIAGE == 1 rows
    rng  = child_rng("R43_C3_clustered")
    pool = np.array([i for i in df.index[(df["MARRIAGE"] == 1) & (df["BILL_AMT1"] > 0)].to_numpy() if i not in used])
    idx  = pick(pool, n_per_family, rng)
    for i in idx:
        df.at[i, "BILL_AMT1"] = -abs(df.at[i, "BILL_AMT1"]); y[i] = 1; fam[i] = "C3_bill_sign_violation"; used.add(int(i))

    # C4 — only in SEX == 2 rows
    rng  = child_rng("R43_C4_clustered")
    pool = np.array([i for i in df.index[df["SEX"] == 2].to_numpy() if i not in used])
    idx  = pick(pool, n_per_family, rng)
    for i in idx:
        df.at[i, "PAY_0"] = -2; df.at[i, "BILL_AMT1"] = abs(df.at[i, "BILL_AMT1"]) + 6000
        y[i] = 1; fam[i] = "C4_pay_temporal_violation"; used.add(int(i))

    # C5 — only in EDUCATION == 1 rows (high school; age violations concentrated there)
    rng  = child_rng("R43_C5_clustered")
    pool = np.array([i for i in df.index[df["EDUCATION"] == 1].to_numpy() if i not in used])
    idx  = pick(pool, n_per_family, rng)
    age_vals = rng.choice([10, 15, 105, 120], size=len(idx))
    for i, v in zip(idx, age_vals):
        df.at[i, "AGE"] = int(v); y[i] = 1; fam[i] = "C5_age_range_violation"; used.add(int(i))

    return df, y, fam


def inject_d3_cooccurring(df_true: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """CO-OCCURRING: inject multiple families into the same rows.
    300 rows get C1+C2+C3 together; 300 different rows get C4+C5 together.
    Total anomalous rows: ~600 (vs 1500 in independent), total injection events: ~900.
    Tests: does co-occurring make detection easier (more signals) or harder (fewer unique rows)?
    """
    df  = df_true.copy().reset_index(drop=True)
    n   = len(df)
    y   = np.zeros(n, dtype=np.int8)
    fam = np.array([""] * n, dtype=object)

    n_batch1 = int(np.ceil(n * RATE))   # 300 rows → get C1+C2+C3

    # Batch 1: 300 rows get C1 + C2 + C3
    rng  = child_rng("R43_batch1")
    pool = df.index[df["EDUCATION"].isin([0,1,2,3,4,5,6]) & (df["BILL_AMT1"] > 0)].to_numpy()
    batch1 = pick(pool, n_batch1, rng)
    oob_vals = rng.choice([7, 8], size=len(batch1))
    for i, v in zip(batch1, oob_vals):
        df.at[i, "EDUCATION"]  = int(v)
        df.at[i, "LIMIT_BAL"]  = 0
        df.at[i, "BILL_AMT1"]  = -abs(df.at[i, "BILL_AMT1"])
        y[i] = 1
        fam[i] = "C1+C2+C3_cooccurring"

    # Batch 2: 300 rows get C4 + C5
    used1 = set(int(i) for i in batch1)
    rng   = child_rng("R43_batch2")
    pool  = np.array([i for i in df.index.to_numpy() if i not in used1])
    batch2 = pick(pool, n_batch1, rng)
    age_vals = rng.choice([10, 15, 105, 120], size=len(batch2))
    for i, v in zip(batch2, age_vals):
        df.at[i, "PAY_0"]     = -2
        df.at[i, "BILL_AMT1"] = abs(df.at[i, "BILL_AMT1"]) + 6000
        df.at[i, "AGE"]       = int(v)
        y[i] = 1
        fam[i] = "C4+C5_cooccurring"

    return df, y, fam


# ---------------------------------------------------------------------------
# D2 injection variants (subsampled to D2_SUBSAMPLE rows)
# ---------------------------------------------------------------------------
def _subsample_d2(df_true: pd.DataFrame) -> pd.DataFrame:
    rng = child_rng("D2_subsample")
    idx = rng.choice(len(df_true), size=min(D2_SUBSAMPLE, len(df_true)), replace=False)
    return df_true.iloc[np.sort(idx)].reset_index(drop=True)


def inject_d2_independent(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Independent injection on D2 subsample."""
    df = df.copy().reset_index(drop=True)
    n  = len(df)
    y  = np.zeros(n, dtype=np.int8)
    fam = np.array([""] * n, dtype=object)
    used: set[int] = set()

    # B1 OT-Regular: Regular Hours==0 but set OT Paid > 0
    rng  = child_rng("D2_B1_ot_regular_R43")
    pool = df.index[(df["Regular Hours"].fillna(0) == 0) & (df["Total OT Paid"].fillna(0) == 0)].to_numpy()
    if len(pool) < 10:
        pool = df.index.to_numpy()
    idx = pick(pool, int(np.ceil(n * RATE)), rng)
    amounts = np.abs(rng.normal(1000, 500, size=len(idx))).clip(100, 10000)
    for i, amt in zip(idx, amounts):
        df.at[i, "Total OT Paid"] = float(amt); y[i] = 1; fam[i] = "B1_ot_regular_inconsistency"; used.add(int(i))

    # B2 salary-basis: per Annum + gross << 5% base
    rng  = child_rng("D2_B2_salary_R43")
    pool = np.array([i for i in df.index[(df["Pay Basis"] == "per Annum") & (df["Base Salary"] > 10000)].to_numpy() if i not in used])
    if len(pool) < 10:
        pool = np.array([i for i in df.index.to_numpy() if i not in used])
    idx = pick(pool, int(np.ceil(n * RATE)), rng)
    for i in idx:
        df.at[i, "Regular Gross Paid"] = float(df.at[i, "Base Salary"]) * 0.01
        y[i] = 1; fam[i] = "B2_salary_basis_mismatch"; used.add(int(i))

    # B3 near-duplicate name (perturb Last Name by 1 char)
    rng  = child_rng("D2_B3_name_R43")
    pool = np.array([i for i in df.index.to_numpy() if i not in used])
    idx  = pick(pool, int(np.ceil(n * RATE)), rng)
    for i in idx:
        s = str(df.at[i, "Last Name"]) if pd.notna(df.at[i, "Last Name"]) else "X"
        pos = int(rng.integers(0, max(1, len(s))))
        c   = chr(ord("A") + int(rng.integers(0, 26)))
        df.at[i, "Last Name"] = s[:pos] + c + s[pos+1:]
        y[i] = 1; fam[i] = "B3_near_duplicate_name"; used.add(int(i))

    # B4 agency-title violation
    rng  = child_rng("D2_B4_agency_R43")
    swaps = [("DEPT OF EDUCATION", "FIREFIGHTER"), ("FIRE DEPARTMENT", "TEACHER")]
    pool = np.array([i for i in df.index.to_numpy() if i not in used])
    idx  = pick(pool, int(np.ceil(n * RATE)), rng)
    swap_choice = rng.integers(0, len(swaps), size=len(idx))
    for i, sc in zip(idx, swap_choice):
        df.at[i, "Agency Name"]       = swaps[int(sc)][0]
        df.at[i, "Title Description"] = swaps[int(sc)][1]
        y[i] = 1; fam[i] = "B4_agency_title_violation"; used.add(int(i))

    # B5 magnitude outlier
    rng  = child_rng("D2_B5_magnitude_R43")
    pool = np.array([i for i in df.index.to_numpy() if i not in used])
    idx  = pick(pool, int(np.ceil(n * RATE)), rng)
    for i in idx:
        df.at[i, "Regular Gross Paid"] = float(df.at[i, "Regular Gross Paid"]) * 1000
        y[i] = 1; fam[i] = "B5_magnitude_outlier"; used.add(int(i))

    return df, y, fam


def inject_d2_clustered(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """CLUSTERED: B1 injected ONLY in DEPT OF EDUCATION rows,
    B5 injected ONLY in FIRE DEPARTMENT rows.
    Other families same as independent.
    """
    df  = df.copy().reset_index(drop=True)
    n   = len(df)
    y   = np.zeros(n, dtype=np.int8)
    fam = np.array([""] * n, dtype=object)
    used: set[int] = set()
    n_per = int(np.ceil(n * RATE))

    # B1 — ONLY in DEPT OF EDUCATION
    rng  = child_rng("D2_B1_clustered_R43")
    pool = df.index[df["Agency Name"].str.contains("EDUCATION", na=False)].to_numpy()
    if len(pool) < 10:
        pool = df.index.to_numpy()
    idx = pick(pool, n_per, rng)
    amounts = np.abs(rng.normal(1000, 500, size=len(idx))).clip(100, 10000)
    for i, amt in zip(idx, amounts):
        df.at[i, "Total OT Paid"] = float(amt); y[i] = 1; fam[i] = "B1_ot_regular_inconsistency"; used.add(int(i))

    # B2 same as independent
    rng  = child_rng("D2_B2_salary_R43c")
    pool = np.array([i for i in df.index[(df["Pay Basis"] == "per Annum") & (df["Base Salary"] > 10000)].to_numpy() if i not in used])
    if len(pool) < 10:
        pool = np.array([i for i in df.index.to_numpy() if i not in used])
    idx  = pick(pool, n_per, rng)
    for i in idx:
        df.at[i, "Regular Gross Paid"] = float(df.at[i, "Base Salary"]) * 0.01
        y[i] = 1; fam[i] = "B2_salary_basis_mismatch"; used.add(int(i))

    # B3 same as independent
    rng  = child_rng("D2_B3_name_R43c")
    pool = np.array([i for i in df.index.to_numpy() if i not in used])
    idx  = pick(pool, n_per, rng)
    for i in idx:
        s   = str(df.at[i, "Last Name"]) if pd.notna(df.at[i, "Last Name"]) else "X"
        pos = int(rng.integers(0, max(1, len(s))))
        c   = chr(ord("A") + int(rng.integers(0, 26)))
        df.at[i, "Last Name"] = s[:pos] + c + s[pos+1:]
        y[i] = 1; fam[i] = "B3_near_duplicate_name"; used.add(int(i))

    # B4 same as independent
    rng    = child_rng("D2_B4_agency_R43c")
    swaps  = [("DEPT OF EDUCATION", "FIREFIGHTER"), ("FIRE DEPARTMENT", "TEACHER")]
    pool   = np.array([i for i in df.index.to_numpy() if i not in used])
    idx    = pick(pool, n_per, rng)
    sc_arr = rng.integers(0, len(swaps), size=len(idx))
    for i, sc in zip(idx, sc_arr):
        df.at[i, "Agency Name"]       = swaps[int(sc)][0]
        df.at[i, "Title Description"] = swaps[int(sc)][1]
        y[i] = 1; fam[i] = "B4_agency_title_violation"; used.add(int(i))

    # B5 — ONLY in FIRE DEPARTMENT rows
    rng  = child_rng("D2_B5_clustered_R43")
    pool = np.array([i for i in df.index[df["Agency Name"].str.contains("FIRE", na=False)].to_numpy() if i not in used])
    if len(pool) < 10:
        pool = np.array([i for i in df.index.to_numpy() if i not in used])
    idx  = pick(pool, n_per, rng)
    for i in idx:
        df.at[i, "Regular Gross Paid"] = float(df.at[i, "Regular Gross Paid"]) * 1000
        y[i] = 1; fam[i] = "B5_magnitude_outlier"; used.add(int(i))

    return df, y, fam


def inject_d2_cooccurring(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """CO-OCCURRING: 2500 rows get B1+B5 simultaneously; 2500 get B2+B4.
    B3 is independent. Total anomalous rows ~5500 vs 10000 in independent.
    Total injection events ~10000 (same as independent).
    """
    df  = df.copy().reset_index(drop=True)
    n   = len(df)
    y   = np.zeros(n, dtype=np.int8)
    fam = np.array([""] * n, dtype=object)
    used: set[int] = set()
    n_batch = int(np.ceil(n * RATE))  # ~500

    # Batch 1: n_batch rows get B1+B5
    rng   = child_rng("D2_R43_co_batch1")
    pool  = df.index.to_numpy()
    batch1 = pick(pool, n_batch, rng)
    amounts = np.abs(rng.normal(1000, 500, size=len(batch1))).clip(100, 10000)
    for i, amt in zip(batch1, amounts):
        df.at[i, "Total OT Paid"]      = float(amt)
        df.at[i, "Regular Gross Paid"] = float(df.at[i, "Regular Gross Paid"]) * 1000
        y[i] = 1; fam[i] = "B1+B5_cooccurring"; used.add(int(i))

    # Batch 2: n_batch rows get B2+B4
    rng    = child_rng("D2_R43_co_batch2")
    pool   = np.array([i for i in df.index[(df["Pay Basis"] == "per Annum") & (df["Base Salary"] > 10000)].to_numpy() if i not in used])
    if len(pool) < 10:
        pool = np.array([i for i in df.index.to_numpy() if i not in used])
    batch2 = pick(pool, n_batch, rng)
    swaps  = [("DEPT OF EDUCATION", "FIREFIGHTER"), ("FIRE DEPARTMENT", "TEACHER")]
    sc_arr = rng.integers(0, len(swaps), size=len(batch2))
    for i, sc in zip(batch2, sc_arr):
        df.at[i, "Regular Gross Paid"] = float(df.at[i, "Base Salary"]) * 0.01
        df.at[i, "Agency Name"]        = swaps[int(sc)][0]
        df.at[i, "Title Description"]  = swaps[int(sc)][1]
        y[i] = 1; fam[i] = "B2+B4_cooccurring"; used.add(int(i))

    # B3 independent
    rng  = child_rng("D2_B3_name_R43co")
    pool = np.array([i for i in df.index.to_numpy() if i not in used])
    idx  = pick(pool, n_batch * 2, rng)  # double B3 to keep total prevalence ~5%
    for i in idx:
        s   = str(df.at[i, "Last Name"]) if pd.notna(df.at[i, "Last Name"]) else "X"
        pos = int(rng.integers(0, max(1, len(s))))
        c   = chr(ord("A") + int(rng.integers(0, 26)))
        df.at[i, "Last Name"] = s[:pos] + c + s[pos+1:]
        y[i] = 1; fam[i] = "B3_near_duplicate_name"; used.add(int(i))

    return df, y, fam


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    t_total = time.time()
    print("[R4.3] Correlated failure injection experiment")

    all_rows: list[dict] = []
    all_fam:  list[dict] = []

    # --- D3 ---
    print("[D3] Loading true dataset ...")
    d3_true = pd.read_parquet(PROC / "D3_uci_credit.parquet").reset_index(drop=True)

    for mode, inject_fn in [
        ("independent", inject_d3_independent),
        ("clustered",   inject_d3_clustered),
        ("cooccurring", inject_d3_cooccurring),
    ]:
        print(f"  [D3/{mode}] injecting ...")
        df, y, fam = inject_fn(d3_true)
        print(f"    anomalies={int(y.sum())}  unique_families={len(set(fam[y==1]))}")
        r, fr = run_pipeline(df, y, fam, "D3", mode)
        all_rows.append(r); all_fam.extend(fr)

    # --- D2 (subsampled) ---
    print(f"[D2] Loading and subsampling to {D2_SUBSAMPLE} rows ...")
    d2_full = pd.read_parquet(PROC / "D2_nyc_fy2024.parquet").reset_index(drop=True)
    d2_true = _subsample_d2(d2_full)
    print(f"  D2 subsample: {len(d2_true)} rows")

    for mode, inject_fn in [
        ("independent", inject_d2_independent),
        ("clustered",   inject_d2_clustered),
        ("cooccurring", inject_d2_cooccurring),
    ]:
        print(f"  [D2/{mode}] injecting ...")
        df, y, fam = inject_fn(d2_true)
        print(f"    anomalies={int(y.sum())}  unique_families={len(set(fam[y==1]))}")
        r, fr = run_pipeline(df, y, fam, "D2_50k", mode)
        all_rows.append(r); all_fam.extend(fr)

    # --- Save outputs ---
    results_df = pd.DataFrame(all_rows)
    fam_df     = pd.DataFrame(all_fam)

    results_df.to_csv(OUTDIR / "r43_correlated_results.csv", index=False)
    fam_df.to_csv(OUTDIR / "r43_by_family.csv", index=False)

    # --- Report ---
    lines = ["# R4.3: Correlated Failure Injection\n"]
    lines.append("## Research question\n")
    lines.append("Does hybrid_xgb performance degrade under CLUSTERED or CO-OCCURRING injection?\n")
    lines.append("INDEPENDENT = uniform random (baseline). CLUSTERED = one family per cohort. "
                 "CO-OCCURRING = multiple families per row.\n\n")

    lines.append("## Summary (hybrid_xgb F1 by dataset × mode)\n\n")
    pivot = results_df.pivot_table(
        index="mode", columns="dataset", values="hybrid_xgb_f1"
    )
    lines.append(pivot.to_markdown() + "\n\n")

    lines.append("## Anomaly counts by mode\n\n")
    cnt = results_df[["dataset", "mode", "n_rows", "n_anomalies"]].copy()
    lines.append(cnt.to_markdown(index=False) + "\n\n")

    lines.append("## AUC-PR by dataset × mode\n\n")
    pivot_auc = results_df.pivot_table(
        index="mode", columns="dataset", values="hybrid_xgb_auc_pr"
    )
    lines.append(pivot_auc.to_markdown() + "\n\n")

    lines.append("## Per-family recall (hybrid_xgb)\n\n")
    lines.append(fam_df.to_markdown(index=False) + "\n\n")

    lines.append(f"---\nGenerated in {round(time.time()-t_total,1)}s\n")

    with open(OUTDIR / "R43_REPORT.md", "w", encoding="utf-8") as f:
        f.write("".join(lines))

    print(f"\n[R4.3] Done in {round(time.time()-t_total,1)}s")
    print(f"Outputs: {OUTDIR}")

    print("\n=== hybrid_xgb F1 by dataset x mode ===")
    print(pivot.to_string())


if __name__ == "__main__":
    main()
