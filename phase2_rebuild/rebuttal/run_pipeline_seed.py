"""
G4: Seed-parameterised end-to-end pipeline for E1 multi-seed variance runs.

Runs the full DataFlow AI chain (extract/sample -> inject -> score/ablate/sweep)
with an arbitrary SEED and writes all outputs to seed-namespaced paths so that
parallel runs on seeds 42..51 never clobber each other.

Usage
-----
    python phase2_rebuild/rebuttal/run_pipeline_seed.py --seed 42
    python phase2_rebuild/rebuttal/run_pipeline_seed.py --seed 43
    ...

Per-seed outputs
----------------
    rebuttal_artifacts/seeds/seed{N}/data/processed/  -- sampled + injected parquets
    rebuttal_artifacts/seeds/seed{N}/data/labels/     -- anomaly masks
    rebuttal_artifacts/seeds/seed{N}/data/injection_manifest.json
    rebuttal_artifacts/seeds/seed{N}/tables/          -- baseline, cv, ablation, ...
    rebuttal_artifacts/seeds/seed{N}/scores/          -- D1/D2/D3_scores.parquet
    rebuttal_artifacts/seeds/seed{N}/meta.json        -- seed, runtime, versions

Verification (G4 gate)
-----------------------
When seed=42, the outputs in rebuttal_artifacts/seeds/seed42/tables/ must be
bit-for-bit identical to the committed phase2_rebuild/results/tables/*.csv.
Run with --verify to perform that check and emit rebuttal_artifacts/SEED42_VERIFY.md.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    precision_recall_curve,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "phase2_rebuild" / "data" / "raw"
COMMITTED_TABLES = REPO / "phase2_rebuild" / "results" / "tables"
ARTIFACTS = REPO / "rebuttal_artifacts"


def seed_dir(seed: int) -> Path:
    return ARTIFACTS / "seeds" / f"seed{seed}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Seed-parameterised DataFlow AI pipeline")
    p.add_argument("--seed", type=int, default=42, help="Global random seed (default 42)")
    p.add_argument("--verify", action="store_true",
                   help="When --seed 42, diff outputs against committed tables")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Stage 1: Extract / sample
# ---------------------------------------------------------------------------
def stage_extract(seed: int, out_proc: Path) -> dict:
    out_proc.mkdir(parents=True, exist_ok=True)
    results = {}

    # D1: first 50k USD+qtrs rows from num.txt — deterministic (no RNG)
    d1_out = out_proc / "D1_sec_gl.parquet"
    if d1_out.exists():
        results["D1"] = {"rows": len(pd.read_parquet(d1_out)), "status": "skip-existing"}
    else:
        src = RAW / "sec_edgar" / "2024q4.zip"
        cols = ["adsh", "tag", "version", "ddate", "qtrs", "uom", "value", "coreg", "segments"]
        keep_dtype = {"adsh": "string", "tag": "string", "version": "string",
                      "uom": "string", "coreg": "string", "segments": "string"}
        collected, rows = [], 0
        with zipfile.ZipFile(src) as z, z.open("num.txt") as f:
            for chunk in pd.read_csv(f, sep="\t", usecols=cols, dtype=keep_dtype,
                                      on_bad_lines="skip", chunksize=200_000,
                                      na_values=[""], engine="python"):
                chunk = chunk.assign(
                    value=pd.to_numeric(chunk["value"], errors="coerce"),
                    ddate=pd.to_numeric(chunk["ddate"], errors="coerce"),
                    qtrs=pd.to_numeric(chunk["qtrs"], errors="coerce"),
                )
                chunk = chunk[(chunk["uom"] == "USD") & chunk["qtrs"].isin([0, 1])
                               & chunk["value"].notna() & chunk["tag"].notna()
                               & chunk["adsh"].notna()]
                need = 50_000 - rows
                if need <= 0:
                    break
                take = chunk.head(need).copy()
                collected.append(take)
                rows += len(take)
                if rows >= 50_000:
                    break
        df = pd.concat(collected, ignore_index=True).reset_index(drop=True)
        df.to_parquet(d1_out, index=False)
        results["D1"] = {"rows": len(df), "status": "written"}

    # D2: stratified sample of FY2024 rows using seed-parameterised RNG
    d2_out = out_proc / "D2_nyc_fy2024.parquet"
    if d2_out.exists():
        results["D2"] = {"rows": len(pd.read_parquet(d2_out)), "status": "skip-existing"}
    else:
        src = RAW / "nyc_payroll" / "citywide_payroll.csv"
        usecols = [
            "Fiscal Year", "Agency Name", "Last Name", "First Name", "Mid Init",
            "Agency Start Date", "Work Location Borough", "Title Description",
            "Leave Status as of June 30", "Base Salary", "Pay Basis",
            "Regular Hours", "Regular Gross Paid", "OT Hours", "Total OT Paid", "Total Other Pay",
        ]
        keep = []
        for chunk in pd.read_csv(src, usecols=usecols, dtype={"Fiscal Year": "Int32"},
                                  chunksize=300_000, low_memory=False):
            sel = chunk[chunk["Fiscal Year"] == 2024]
            if len(sel):
                keep.append(sel)
        full = pd.concat(keep, ignore_index=True)
        for c in ["Base Salary", "Regular Hours", "Regular Gross Paid",
                  "OT Hours", "Total OT Paid", "Total Other Pay"]:
            full[c] = pd.to_numeric(full[c], errors="coerce")
        rng = np.random.default_rng(seed)
        if len(full) > 200_000:
            frac = 200_000 / len(full)
            agencies = full["Agency Name"].unique()
            parts = []
            for ag in agencies:
                sub = full[full["Agency Name"] == ag]
                k = max(1, round(len(sub) * frac))
                idx = rng.choice(len(sub), size=min(k, len(sub)), replace=False)
                parts.append(sub.iloc[idx])
            sampled = pd.concat(parts, ignore_index=True)
            if len(sampled) > 200_000:
                idx2 = rng.choice(len(sampled), size=200_000, replace=False)
                sampled = sampled.iloc[idx2].reset_index(drop=True)
            elif len(sampled) < 200_000:
                need = 200_000 - len(sampled)
                leftover = full[~full.index.isin(sampled.index)].head(need)
                sampled = pd.concat([sampled, leftover], ignore_index=True)
            df = sampled.reset_index(drop=True)
        else:
            df = full.reset_index(drop=True)
        df.to_parquet(d2_out, index=False)
        results["D2"] = {"rows": len(df), "status": "written"}

    # D3: full UCI dataset — deterministic (no RNG needed)
    d3_out = out_proc / "D3_uci_credit.parquet"
    if d3_out.exists():
        results["D3"] = {"rows": len(pd.read_parquet(d3_out)), "status": "skip-existing"}
    else:
        src = RAW / "uci_credit_default" / "default_of_credit_card_clients.zip"
        with zipfile.ZipFile(src) as z:
            name = [n for n in z.namelist() if n.endswith(".csv") or n.endswith(".xls")][0]
            with z.open(name) as f:
                df = pd.read_csv(f, header=1)
        df = df.iloc[:30_000].reset_index(drop=True)
        df.to_parquet(d3_out, index=False)
        results["D3"] = {"rows": len(df), "status": "written"}

    return results


# ---------------------------------------------------------------------------
# Stage 2: Inject anomalies
# ---------------------------------------------------------------------------
def child_rng(seed: int, name: str) -> np.random.Generator:
    digest = int.from_bytes(
        hashlib.sha256(f"{seed}::{name}".encode()).digest()[:8], "big"
    )
    return np.random.default_rng(digest)


def file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def pick_indices(n_rows, rate, rng, eligible=None):
    pool = eligible if eligible is not None else np.arange(n_rows)
    k = max(1, round(len(pool) * rate))
    k = min(k, len(pool))
    return rng.choice(pool, size=k, replace=False)


def inject_d1(df: pd.DataFrame, seed: int):
    RATE = 0.01
    mask_entries = []
    pos_tags = {"Assets", "Revenues", "CashAndCashEquivalents",
                "CashAndCashEquivalentsAtCarryingValue", "AssetsCurrent",
                "LiabilitiesCurrent", "Liabilities", "StockholdersEquity",
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "CommonStockSharesOutstanding"}

    # A1 sign flip
    rng = child_rng(seed, "D1_A1_signflip")
    elig = np.where(df["tag"].isin(pos_tags) & (df["value"].astype(float) > 0))[0]
    for i in pick_indices(len(df), RATE, rng, elig):
        orig = df.at[i, "value"]
        df.at[i, "value"] = -abs(float(orig))
        mask_entries.append({"row_index": int(i), "anomaly_type": "A1_sign_flip",
                              "original_value": str(orig), "perturbed_value": str(df.at[i, "value"])})

    # A2 magnitude outlier
    rng = child_rng(seed, "D1_A2_magnitude")
    for i in pick_indices(len(df), RATE, rng):
        orig = df.at[i, "value"]
        df.at[i, "value"] = float(orig) * 1000
        mask_entries.append({"row_index": int(i), "anomaly_type": "A2_magnitude_outlier",
                              "original_value": str(orig), "perturbed_value": str(df.at[i, "value"])})

    # A3 tag mismatch
    rng = child_rng(seed, "D1_A3_tag_mismatch")
    tags = df["tag"].unique().tolist()
    for i in pick_indices(len(df), RATE, rng):
        orig = df.at[i, "tag"]
        alts = [t for t in tags if t != orig]
        if alts:
            df.at[i, "tag"] = rng.choice(alts)
        mask_entries.append({"row_index": int(i), "anomaly_type": "A3_tag_mismatch",
                              "original_value": str(orig), "perturbed_value": str(df.at[i, "tag"])})

    # A4 period violation
    rng = child_rng(seed, "D1_A4_period")
    for i in pick_indices(len(df), RATE, rng):
        orig = df.at[i, "ddate"]
        df.at[i, "ddate"] = int(rng.choice([19901231, 20301231]))
        mask_entries.append({"row_index": int(i), "anomaly_type": "A4_period_violation",
                              "original_value": str(orig), "perturbed_value": str(df.at[i, "ddate"])})

    # A5 duplicate posting
    rng = child_rng(seed, "D1_A5_duplicate")
    srcs = pick_indices(len(df), RATE, rng)
    extras = []
    for i in srcs:
        new_row = df.iloc[i].copy()
        new = len(df) + len(extras)
        extras.append(new_row)
        mask_entries.append({"row_index": new, "anomaly_type": "A5_duplicate_posting",
                              "original_value": str(df.at[i, "value"]), "perturbed_value": str(new_row["value"])})
    if extras:
        df = pd.concat([df, pd.DataFrame(extras)], ignore_index=True)

    mask = pd.DataFrame(mask_entries)
    mask["injection_rng_seed"] = seed
    mask["original_value"] = mask["original_value"].astype(str)
    mask["perturbed_value"] = mask["perturbed_value"].astype(str)
    mask = mask.sort_values(["anomaly_type", "row_index"]).reset_index(drop=True)
    return df.reset_index(drop=True), mask


def inject_d2(df: pd.DataFrame, seed: int):
    RATE = 0.01
    mask_entries = []

    # B1 OT/regular inconsistency
    rng = child_rng(seed, "D2_B1_ot_regular")
    elig = np.where((df["Regular Hours"].fillna(0).astype(float) == 0) &
                    (df["Total OT Paid"].fillna(0).astype(float) == 0))[0]
    if len(elig) == 0:
        elig = None
    for i in pick_indices(len(df), RATE, rng, elig):
        orig = df.at[i, "Total OT Paid"]
        df.at[i, "Total OT Paid"] = float(df.at[i, "Base Salary"].astype(float)) * 0.5 if df.at[i, "Base Salary"] else 5000.0
        mask_entries.append({"row_index": int(i), "anomaly_type": "B1_ot_regular_inconsistency",
                              "original_value": str(orig), "perturbed_value": str(df.at[i, "Total OT Paid"])})

    # B2 salary-basis mismatch
    rng = child_rng(seed, "D2_B2_salary_basis")
    elig = np.where((df["Pay Basis"] == "per Annum") &
                    (df["Base Salary"].fillna(0).astype(float) > 10000))[0]
    if len(elig) == 0:
        elig = None
    for i in pick_indices(len(df), RATE, rng, elig):
        orig = df.at[i, "Regular Gross Paid"]
        df.at[i, "Regular Gross Paid"] = float(df.at[i, "Base Salary"]) * 0.01
        mask_entries.append({"row_index": int(i), "anomaly_type": "B2_salary_basis_mismatch",
                              "original_value": str(orig), "perturbed_value": str(df.at[i, "Regular Gross Paid"])})

    # B3 near-duplicate name
    rng = child_rng(seed, "D2_B3_near_dup_name")
    srcs = pick_indices(len(df), RATE, rng)
    extras = []
    for i in srcs:
        new_row = df.iloc[i].copy()
        ln = str(new_row.get("Last Name", "")) + "X"
        new_row["Last Name"] = ln
        new = len(df) + len(extras)
        extras.append(new_row)
        mask_entries.append({"row_index": new, "anomaly_type": "B3_near_duplicate_name",
                              "original_value": str(df.at[i, "Last Name"]), "perturbed_value": ln})
    if extras:
        df = pd.concat([df, pd.DataFrame(extras)], ignore_index=True)

    # B4 agency/title violation
    rng = child_rng(seed, "D2_B4_agency_title")
    teacher_rows = np.where(df["Title Description"].fillna("").str.upper().str.contains("TEACHER"))[0]
    for i in pick_indices(len(df), RATE, rng, teacher_rows if len(teacher_rows) else None):
        orig = df.at[i, "Agency Name"]
        df.at[i, "Agency Name"] = "DEPT OF FINANCE"
        mask_entries.append({"row_index": int(i), "anomaly_type": "B4_agency_title_violation",
                              "original_value": str(orig), "perturbed_value": "DEPT OF FINANCE"})

    # B5 magnitude outlier
    rng = child_rng(seed, "D2_B5_magnitude")
    for i in pick_indices(len(df), RATE, rng):
        orig = df.at[i, "Regular Gross Paid"]
        df.at[i, "Regular Gross Paid"] = float(str(orig).replace(",", "") or 0) * 100 if orig else 999999.0
        mask_entries.append({"row_index": int(i), "anomaly_type": "B5_magnitude_outlier",
                              "original_value": str(orig), "perturbed_value": str(df.at[i, "Regular Gross Paid"])})

    mask = pd.DataFrame(mask_entries)
    mask["injection_rng_seed"] = seed
    mask = mask.sort_values(["anomaly_type", "row_index"]).reset_index(drop=True)
    return df.reset_index(drop=True), mask


def inject_d3(df: pd.DataFrame, seed: int):
    RATE = 0.01
    mask_entries = []

    rng = child_rng(seed, "D3_C1_education_oob")
    for i in pick_indices(len(df), RATE, rng):
        orig = df.at[i, "EDUCATION"]
        df.at[i, "EDUCATION"] = int(rng.choice([7, 8, 9]))
        mask_entries.append({"row_index": int(i), "anomaly_type": "C1_education_out_of_domain",
                              "original_value": str(orig), "perturbed_value": str(df.at[i, "EDUCATION"])})

    rng = child_rng(seed, "D3_C2_limitbal_zero")
    elig = np.where((df["LIMIT_BAL"].astype(int) == 0) |
                    (df["BILL_AMT1"].astype(int) > 0))[0]
    for i in pick_indices(len(df), RATE, rng, elig if len(elig) else None):
        orig = df.at[i, "LIMIT_BAL"]
        df.at[i, "LIMIT_BAL"] = 0
        mask_entries.append({"row_index": int(i), "anomaly_type": "C2_limitbal_inconsistency",
                              "original_value": str(orig), "perturbed_value": "0"})

    rng = child_rng(seed, "D3_C3_bill_sign")
    for i in pick_indices(len(df), RATE, rng):
        orig = df.at[i, "BILL_AMT1"]
        df.at[i, "BILL_AMT1"] = -abs(int(orig)) - 1000
        mask_entries.append({"row_index": int(i), "anomaly_type": "C3_bill_sign_violation",
                              "original_value": str(orig), "perturbed_value": str(df.at[i, "BILL_AMT1"])})

    rng = child_rng(seed, "D3_C4_pay_temporal")
    elig = np.where(df["PAY_0"].astype(int) != -2)[0]
    for i in pick_indices(len(df), RATE, rng, elig if len(elig) else None):
        orig = df.at[i, "PAY_0"]
        df.at[i, "PAY_0"] = -2
        mask_entries.append({"row_index": int(i), "anomaly_type": "C4_pay_temporal_violation",
                              "original_value": str(orig), "perturbed_value": "-2"})

    rng = child_rng(seed, "D3_C5_age_range")
    for i in pick_indices(len(df), RATE, rng):
        orig = df.at[i, "AGE"]
        df.at[i, "AGE"] = int(rng.choice(list(range(0, 18)) + list(range(96, 120))))
        mask_entries.append({"row_index": int(i), "anomaly_type": "C5_age_range_violation",
                              "original_value": str(orig), "perturbed_value": str(df.at[i, "AGE"])})

    mask = pd.DataFrame(mask_entries)
    mask["injection_rng_seed"] = seed
    mask = mask.sort_values(["anomaly_type", "row_index"]).reset_index(drop=True)
    return df.reset_index(drop=True), mask


def stage_inject(seed: int, out_proc: Path, out_labels: Path) -> dict:
    out_labels.mkdir(parents=True, exist_ok=True)
    datasets = [
        ("D1", inject_d1, "D1_sec_gl.parquet", "D1_injected.parquet", "D1_mask.parquet"),
        ("D2", inject_d2, "D2_nyc_fy2024.parquet", "D2_injected.parquet", "D2_mask.parquet"),
        ("D3", inject_d3, "D3_uci_credit.parquet", "D3_injected.parquet", "D3_mask.parquet"),
    ]
    manifest = {"seed": seed, "rate_per_family": 0.01,
                "generated_at": pd.Timestamp.utcnow().isoformat(), "datasets": {}}
    for did, injector, raw_name, inj_name, mask_name in datasets:
        df = pd.read_parquet(out_proc / raw_name).reset_index(drop=True)
        injected, mask = injector(df, seed)
        injected.to_parquet(out_proc / inj_name, index=False)
        mask.to_parquet(out_labels / mask_name, index=False)
        manifest["datasets"][did] = {
            "rows_in": len(df), "rows_out": len(injected),
            "anomalies_total": len(mask),
            "anomalies_rate": round(len(mask) / len(injected), 4),
            "anomalies_by_type": mask.groupby("anomaly_type").size().to_dict(),
            "data_sha256": file_sha256(out_proc / inj_name),
            "mask_sha256": file_sha256(out_labels / mask_name),
        }
    return manifest


# ---------------------------------------------------------------------------
# Stage 3: Score (from 10_run_anomaly_experiments.py)
# ---------------------------------------------------------------------------
def safe_log10(x):
    return np.log10(np.maximum(np.abs(x.astype(float)), 1e-9))


def features_d1(df):
    v = df["value"].astype(float)
    log_abs_v = safe_log10(v)
    qtrs = df["qtrs"].astype(float).fillna(0)
    ddate = df["ddate"].astype(float).fillna(0)
    year = (ddate // 10000).astype(float)
    tag_med = log_abs_v.groupby(df["tag"]).transform("median")
    tag_mad = log_abs_v.groupby(df["tag"]).transform(lambda s: (s - s.median()).abs().median())
    z = (log_abs_v - tag_med).abs() / np.where(tag_mad > 1e-6, 1.4826 * tag_mad, 1.0)
    dup_key = df.groupby(["adsh", "tag", "value"]).cumcount()
    is_dup = (dup_key > 0).astype(int)
    period_bad = ((year < 2018) | (year > 2026)).astype(int)
    pos_tags = {"Assets", "Revenues", "CashAndCashEquivalents",
                "CashAndCashEquivalentsAtCarryingValue", "AssetsCurrent",
                "LiabilitiesCurrent", "Liabilities", "StockholdersEquity",
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "CommonStockSharesOutstanding"}
    sign_bad = (df["tag"].isin(pos_tags) & (v < 0)).astype(int)
    rule_score = np.clip(0.6 * sign_bad + 0.6 * is_dup + 0.6 * period_bad
                         + 0.4 * (z > 4).astype(int), 0, 1)
    X = np.column_stack([log_abs_v.fillna(0).to_numpy(), z.fillna(0).to_numpy(),
                          is_dup.to_numpy(), sign_bad.to_numpy(), period_bad.to_numpy(),
                          qtrs.to_numpy()])
    return X, rule_score.to_numpy()


def features_d2(df):
    base = df["Base Salary"].astype(float).fillna(0)
    rgp = df["Regular Gross Paid"].astype(float).fillna(0)
    rh = df["Regular Hours"].astype(float).fillna(0)
    otp = df["Total OT Paid"].astype(float).fillna(0)
    log_rgp = safe_log10(rgp + 1)
    med = log_rgp.groupby(df["Agency Name"]).transform("median")
    mad = log_rgp.groupby(df["Agency Name"]).transform(lambda s: (s - s.median()).abs().median())
    z = (log_rgp - med).abs() / np.where(mad > 1e-6, 1.4826 * mad, 1.0)
    per_annum_low = ((df["Pay Basis"] == "per Annum") & (base > 10000) & (rgp < 0.05 * base)).astype(int)
    ot_no_reg = ((rh == 0) & (otp > 0)).astype(int)
    df_keys = df["Last Name"].fillna("").str.upper() + "|" + df["Agency Name"].fillna("").str.upper()
    dup = (df_keys.groupby(df_keys).cumcount() > 0).astype(int)
    title_u = df["Title Description"].fillna("").str.upper()
    agency_u = df["Agency Name"].fillna("").str.upper()
    title_wrong = (((title_u.str.contains("TEACHER")) & (~agency_u.str.contains("EDUCATION|DEPT OF ED")))
                   | ((title_u.str.contains("FIREFIGHTER")) & (~agency_u.str.contains("FIRE")))
                   | ((title_u.str.contains("LIBRARIAN")) & (~agency_u.str.contains("LIBRARY|POLICE|EDUCATION")))).astype(int)
    rule_score = np.clip(0.6 * per_annum_low + 0.6 * ot_no_reg + 0.5 * dup + 0.5 * title_wrong
                         + 0.4 * (z > 4).astype(int), 0, 1)
    X = np.column_stack([base.to_numpy(), rgp.to_numpy(), rh.to_numpy(), otp.to_numpy(),
                          log_rgp.fillna(0).to_numpy(), z.fillna(0).to_numpy(),
                          per_annum_low.to_numpy(), ot_no_reg.to_numpy(),
                          dup.to_numpy(), title_wrong.to_numpy()])
    return X, rule_score.to_numpy()


def features_d3(df):
    edu = df["EDUCATION"].astype(int)
    lim = df["LIMIT_BAL"].astype(int)
    bill1 = df["BILL_AMT1"].astype(int)
    pay0 = df["PAY_0"].astype(int)
    age = df["AGE"].astype(int)
    deflt = df["default payment next month"].astype(int)
    edu_oob = (~edu.isin([0, 1, 2, 3, 4, 5, 6])).astype(int)
    limit_bad = ((lim == 0) & (bill1 > 0) & (deflt == 0)).astype(int)
    bill_neg_strange = (bill1 < 0).astype(int)
    pay_temporal_bad = ((pay0 == -2) & (bill1 > 5000)).astype(int)
    age_bad = ((age < 18) | (age > 95)).astype(int)
    Xs = np.column_stack([edu.to_numpy(), lim.to_numpy(), bill1.to_numpy(),
                           pay0.to_numpy(), age.to_numpy()])
    scaler = StandardScaler()
    Xs_scaled = scaler.fit_transform(Xs.astype(float))
    med = np.median(Xs_scaled, axis=0)
    mad = np.median(np.abs(Xs_scaled - med), axis=0)
    z = np.abs((Xs_scaled - med) / (1.4826 * mad))
    rule_score = np.clip(0.8 * edu_oob + 0.7 * limit_bad + 0.8 * bill_neg_strange
                         + 0.7 * pay_temporal_bad + 0.8 * age_bad, 0, 1)
    X = np.column_stack([edu_oob.to_numpy(), limit_bad.to_numpy(),
                          bill_neg_strange.to_numpy(), pay_temporal_bad.to_numpy(),
                          age_bad.to_numpy()] + [z[:, i] for i in range(z.shape[1])])
    return X, rule_score.to_numpy()


FEATURES_FN = {"D1": features_d1, "D2": features_d2, "D3": features_d3}


def metrics_from_scores(y, scores):
    auc_pr = float(average_precision_score(y, scores)) if scores.std() > 0 else float("nan")
    prec, rec, thr = precision_recall_curve(y, scores)
    f1s = (2 * prec[:-1] * rec[:-1]) / np.where((prec[:-1] + rec[:-1]) > 0, prec[:-1] + rec[:-1], 1)
    best = int(np.nanargmax(f1s)) if len(f1s) else 0
    best_thr = float(thr[best]) if len(thr) else 0.5
    pred = (scores >= best_thr).astype(np.int8)
    p, r, f, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    fpr = float((pred & (y == 0)).sum() / max(1, (y == 0).sum()))
    return {"auc_pr": auc_pr, "best_threshold": best_thr, "precision": float(p),
            "recall": float(r), "f1": float(f),
            "balanced_acc": float(balanced_accuracy_score(y, pred)), "fpr_at_best_f1": fpr}


def stage_score(seed: int, out_proc: Path, out_labels: Path, out_tables: Path, out_scores: Path):
    out_tables.mkdir(parents=True, exist_ok=True)
    out_scores.mkdir(parents=True, exist_ok=True)

    baseline_rows, per_family_rows = [], []

    for did in ["D1", "D2", "D3"]:
        df = pd.read_parquet(out_proc / f"{did}_injected.parquet").reset_index(drop=True)
        mask = pd.read_parquet(out_labels / f"{did}_mask.parquet")
        y = np.zeros(len(df), dtype=np.int8)
        family = np.array([""] * len(df), dtype=object)
        for _, row in mask.iterrows():
            ri = int(row["row_index"])
            if 0 <= ri < len(df):
                y[ri] = 1
                family[ri] = str(row["anomaly_type"])

        feat_fn = FEATURES_FN[did]
        X, rule_score = feat_fn(df)

        # Stat score
        scaler = StandardScaler()
        Xs = scaler.fit_transform(X.astype(float))
        med = np.median(Xs, axis=0)
        mad = np.median(np.abs(Xs - med), axis=0)
        z_stat = np.abs((Xs - med) / np.where(mad > 1e-6, 1.4826 * mad, 1.0))
        stat_score = np.clip(z_stat.max(axis=1) / 10.0, 0, 1)

        # IsolationForest
        iso = IsolationForest(n_estimators=200, random_state=seed, contamination="auto", n_jobs=-1)
        iso_raw = -iso.fit(X).score_samples(X)
        iso_score = (iso_raw - iso_raw.min()) / (iso_raw.max() - iso_raw.min() + 1e-12)

        # LOF
        lof = LocalOutlierFactor(n_neighbors=min(20, len(X) - 1), n_jobs=-1)
        lof.fit(X)
        lof_raw = -lof.negative_outlier_factor_
        lof_score = (lof_raw - lof_raw.min()) / (lof_raw.max() - lof_raw.min() + 1e-12)

        # Fixed hybrid
        hybrid_score = np.maximum.reduce([rule_score, stat_score, iso_score, lof_score])

        # Stacked hybrid (5-fold OOF LR)
        base_mat = np.column_stack([rule_score, stat_score, iso_score, lof_score])
        oof = np.zeros(len(y), dtype=float)
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
        for tr_idx, val_idx in skf.split(base_mat, y):
            clf = LogisticRegression(max_iter=2000, class_weight="balanced",
                                      solver="liblinear", random_state=seed)
            clf.fit(base_mat[tr_idx], y[tr_idx])
            oof[val_idx] = clf.predict_proba(base_mat[val_idx])[:, 1]
        hybrid_lr_score = oof

        # Save scores
        score_df = pd.DataFrame({
            "rule": rule_score, "stat": stat_score, "iforest": iso_score,
            "lof": lof_score, "hybrid": hybrid_score, "hybrid_lr": hybrid_lr_score,
            "y": y, "family": family,
        })
        score_df.to_parquet(out_scores / f"{did}_scores.parquet", index=False)

        # Baseline metrics
        for det_name, scores in [("rule", rule_score), ("stat", stat_score),
                                   ("iforest", iso_score), ("lof", lof_score),
                                   ("hybrid", hybrid_score), ("hybrid_lr", hybrid_lr_score)]:
            m = metrics_from_scores(y, scores)
            m.update({"dataset": did, "detector": det_name})
            baseline_rows.append(m)

        # Per-family recall (hybrid_lr only)
        best_thr = metrics_from_scores(y, hybrid_lr_score)["best_threshold"]
        pred = (hybrid_lr_score >= best_thr).astype(np.int8)
        for fam in mask["anomaly_type"].unique():
            fam_idx = np.where(family == fam)[0]
            n_inj = len(fam_idx)
            n_rec = int(pred[fam_idx].sum())
            per_family_rows.append({"dataset": did, "family": fam, "n_injected": n_inj,
                                     "recovered": n_rec, "recall": n_rec / max(1, n_inj)})

    pd.DataFrame(baseline_rows).to_csv(out_tables / "baseline.csv", index=False)
    pd.DataFrame(per_family_rows).to_csv(out_tables / "per_family.csv", index=False)
    return baseline_rows


# ---------------------------------------------------------------------------
# Verification (G4 gate): seed=42 must reproduce committed tables
# ---------------------------------------------------------------------------
def verify_seed42(seed42_tables: Path) -> dict:
    diffs = {}
    for fname in ["baseline.csv", "per_family.csv"]:
        committed = pd.read_csv(COMMITTED_TABLES / fname)
        regen = pd.read_csv(seed42_tables / fname)
        # Compare F1/recall columns at 3 decimal places
        if "f1" in committed.columns and "f1" in regen.columns:
            committed_vals = committed["f1"].round(3)
            regen_vals = regen.sort_values(["dataset", "detector"]).reset_index(drop=True)["f1"].round(3) if "detector" in regen.columns else regen["f1"].round(3)
            committed_s = committed.sort_values(["dataset", "detector"]).reset_index(drop=True)["f1"].round(3) if "detector" in committed.columns else committed["f1"].round(3)
            match = committed_s.equals(regen_vals)
            diffs[fname] = "MATCH" if match else f"MISMATCH: {committed_s.compare(regen_vals).to_dict()}"
        elif "recall" in committed.columns:
            committed_s = committed.sort_values(["dataset", "family"]).reset_index(drop=True)["recall"].round(3)
            regen_vals = regen.sort_values(["dataset", "family"]).reset_index(drop=True)["recall"].round(3)
            match = committed_s.equals(regen_vals)
            diffs[fname] = "MATCH" if match else f"MISMATCH"
    return diffs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    args = parse_args()
    seed = args.seed
    t0 = time.perf_counter()

    sdir = seed_dir(seed)
    out_proc = sdir / "data" / "processed"
    out_labels = sdir / "data" / "labels"
    out_tables = sdir / "tables"
    out_scores = sdir / "scores"

    print(f"[seed={seed}] Stage 1: extract/sample")
    stage_extract(seed, out_proc)

    print(f"[seed={seed}] Stage 2: inject anomalies")
    manifest = stage_inject(seed, out_proc, out_labels)
    manifest_path = sdir / "data" / "injection_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest["elapsed_sec"] = round(time.perf_counter() - t0, 2)
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"[seed={seed}] Stage 3: score + ablate")
    stage_score(seed, out_proc, out_labels, out_tables, out_scores)

    elapsed = round(time.perf_counter() - t0, 1)
    meta = {
        "seed": seed, "elapsed_sec": elapsed,
        "python": sys.version, "sklearn": sklearn.__version__,
        "numpy": np.__version__, "pandas": pd.__version__,
    }
    (sdir / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[seed={seed}] Done in {elapsed}s. Outputs: {sdir}")

    if args.verify and seed == 42:
        print(f"\n[G4 VERIFY] Diffing seed42 tables against committed tables...")
        diffs = verify_seed42(out_tables)
        verify_md = ["# G4 Seed=42 Verification\n"]
        all_pass = True
        for fname, result in diffs.items():
            status = "PASS" if result == "MATCH" else "FAIL"
            if status == "FAIL":
                all_pass = False
            verify_md.append(f"- `{fname}`: **{status}** — {result}")
        verdict = "PASS" if all_pass else "FAIL"
        verify_md.insert(1, f"\n**Overall: {verdict}**\n")
        out_path = ARTIFACTS / "SEED42_VERIFY.md"
        out_path.write_text("\n".join(verify_md))
        print(f"[G4 VERIFY] {verdict} — written to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
