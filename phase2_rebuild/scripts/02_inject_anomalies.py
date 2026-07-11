"""
Phase 2 rebuild — Step 02: inject deterministic anomaly masks into the processed datasets.

Implements the families documented in
phase2_rebuild/anomaly_injection_plan.md verbatim:
    D1 (SEC): A1 sign flip / A2 magnitude / A3 tag mismatch / A4 period / A5 duplicate
    D2 (NYC): B1 OT-Reg / B2 salary-basis / B3 near-dup name / B4 agency-title / B5 magnitude
    D3 (UCI): C1 EDU code / C2 LIMIT_BAL=0 inconsistency / C3 BILL sign / C4 PAY temporal / C5 AGE range

Output convention (parquet):
    data/processed/D{1,2,3}_injected.parquet     real data + injected anomalies
    data/labels/D{1,2,3}_mask.parquet            (row_index, anomaly_type, original_value, perturbed_value, injection_rng_seed)

Determinism: global SEED=42; per-family child seeds derived via numpy SeedSequence.
Idempotent: re-running with no changes produces bit-identical mask checksums.

Run from repo root:
    python phase2_rebuild/scripts/02_inject_anomalies.py
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PROC = REPO_ROOT / "phase2_rebuild" / "data" / "processed"
LABELS = REPO_ROOT / "phase2_rebuild" / "data" / "labels"
LABELS.mkdir(parents=True, exist_ok=True)

SEED = 42
RATE_PER_FAMILY = 0.01  # 1 % per family => ~5 % total per dataset


def child_rng(name: str) -> np.random.Generator:
    """Deterministic per-family RNG, derived from SEED + family name."""
    digest = int.from_bytes(hashlib.sha256(f"{SEED}::{name}".encode()).digest()[:8], "big")
    return np.random.default_rng(digest)


def pick_indices(n_rows: int, rate: float, rng: np.random.Generator,
                 eligible: np.ndarray | None = None) -> np.ndarray:
    """Sample target indices without replacement.

    If `eligible` is supplied, draw only from those row indices; otherwise from
    range(n_rows). Returns at most ceil(n_rows * rate) indices.
    """
    target = int(np.ceil(n_rows * rate))
    if eligible is None:
        pool = np.arange(n_rows)
    else:
        pool = np.asarray(eligible, dtype=np.int64)
    if target >= len(pool):
        return np.sort(pool)
    chosen = rng.choice(pool, size=target, replace=False)
    return np.sort(chosen)


def file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# D1 — SEC EDGAR GL slice
# ---------------------------------------------------------------------------
D1_SIGN_TAGS = {
    "Assets", "Revenues", "CashAndCashEquivalents",
    "CashAndCashEquivalentsAtCarryingValue",
    "AssetsCurrent", "LiabilitiesCurrent", "Liabilities",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "StockholdersEquity", "CommonStockSharesOutstanding",
}
D1_TAG_POOL_FOR_MISMATCH = [
    "Revenues", "CostOfGoodsSold", "GrossProfit", "OperatingExpenses",
    "InterestExpense", "IncomeTaxExpenseBenefit", "EarningsPerShareBasic",
]


def inject_d1(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    n = len(df)
    mask_entries: list[dict] = []

    # A1 sign flip on non-negative GAAP tags with positive value
    rng = child_rng("D1_A1_signflip")
    eligible = df.index[df["tag"].isin(D1_SIGN_TAGS) & (df["value"] > 0)].to_numpy()
    idx = pick_indices(n, RATE_PER_FAMILY, rng, eligible=eligible)
    for i in idx:
        orig = df.at[i, "value"]
        df.at[i, "value"] = -orig
        mask_entries.append({"row_index": int(i), "anomaly_type": "A1_sign_flip",
                             "original_value": float(orig),
                             "perturbed_value": float(df.at[i, "value"])})

    # A2 magnitude outlier: multiply by 10^k, k in {3,4}
    rng = child_rng("D1_A2_magnitude")
    used = set(int(i) for i in idx)
    eligible = np.array([i for i in df.index[df["value"].notna()].to_numpy() if int(i) not in used])
    idx = pick_indices(n, RATE_PER_FAMILY, rng, eligible=eligible)
    ks = rng.choice([3, 4], size=len(idx))
    for i, k in zip(idx, ks):
        orig = df.at[i, "value"]
        df.at[i, "value"] = orig * (10 ** int(k))
        mask_entries.append({"row_index": int(i), "anomaly_type": "A2_magnitude_outlier",
                             "original_value": float(orig),
                             "perturbed_value": float(df.at[i, "value"])})
        used.add(int(i))

    # A3 tag-value mismatch: replace tag with semantically inconsistent one
    rng = child_rng("D1_A3_tag_mismatch")
    eligible = np.array([i for i in df.index.to_numpy() if int(i) not in used])
    idx = pick_indices(n, RATE_PER_FAMILY, rng, eligible=eligible)
    new_tags = rng.choice(D1_TAG_POOL_FOR_MISMATCH, size=len(idx))
    for i, t in zip(idx, new_tags):
        orig = df.at[i, "tag"]
        if orig == t:
            continue
        df.at[i, "tag"] = t
        mask_entries.append({"row_index": int(i), "anomaly_type": "A3_tag_mismatch",
                             "original_value": str(orig),
                             "perturbed_value": str(t)})
        used.add(int(i))

    # A4 period violation: set ddate far outside any sensible window
    rng = child_rng("D1_A4_period")
    eligible = np.array([i for i in df.index.to_numpy() if int(i) not in used])
    idx = pick_indices(n, RATE_PER_FAMILY, rng, eligible=eligible)
    bad_dates = rng.choice([19500101, 21000101, 18000101], size=len(idx))
    for i, d in zip(idx, bad_dates):
        orig = df.at[i, "ddate"]
        df.at[i, "ddate"] = int(d)
        mask_entries.append({"row_index": int(i), "anomaly_type": "A4_period_violation",
                             "original_value": int(orig),
                             "perturbed_value": int(d)})
        used.add(int(i))

    # A5 duplicate posting: append duplicate rows; the duplicates are the anomalies.
    rng = child_rng("D1_A5_duplicate")
    eligible = np.array([i for i in df.index.to_numpy() if int(i) not in used])
    src_idx = pick_indices(n, RATE_PER_FAMILY, rng, eligible=eligible)
    dup_rows = df.loc[src_idx].copy()
    next_index = len(df)
    new_indices = np.arange(next_index, next_index + len(dup_rows))
    dup_rows.index = new_indices
    df = pd.concat([df, dup_rows])
    for src, new in zip(src_idx, new_indices):
        mask_entries.append({"row_index": int(new), "anomaly_type": "A5_duplicate_posting",
                             "original_value": int(src),
                             "perturbed_value": int(new)})

    mask = pd.DataFrame(mask_entries)
    mask["injection_rng_seed"] = SEED
    # Cast to consistent str type for the value columns (they are heterogeneous).
    mask["original_value"] = mask["original_value"].astype(str)
    mask["perturbed_value"] = mask["perturbed_value"].astype(str)
    mask = mask.sort_values(["anomaly_type", "row_index"]).reset_index(drop=True)
    return df.reset_index(drop=True), mask


# ---------------------------------------------------------------------------
# D2 — NYC payroll FY2024 slice
# ---------------------------------------------------------------------------
D2_AGENCY_TITLE_SWAP = [
    ("DEPT OF EDUCATION", "FIREFIGHTER"),
    ("FIRE DEPARTMENT", "TEACHER"),
    ("POLICE DEPARTMENT", "CHIEF LIBRARIAN"),
    ("DEPARTMENT OF SANITATION", "ASSISTANT DISTRICT ATTORNEY"),
    ("DEPT OF PARKS & RECREATION", "AIRCRAFT MECHANIC"),
]


def _one_char_perturb(s, rng: np.random.Generator) -> str:
    if not isinstance(s, str) or len(s) == 0:
        return "ANOMX"
    pos = int(rng.integers(0, len(s)))
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    new_char = alphabet[int(rng.integers(0, 26))]
    while new_char == s[pos].upper():
        new_char = alphabet[int(rng.integers(0, 26))]
    return s[:pos] + new_char + s[pos + 1:]


def inject_d2(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    n = len(df)
    used: set[int] = set()
    entries: list[dict] = []

    # B1 OT-Regular inconsistency: Regular Hours == 0 but Total OT Paid > 0
    rng = child_rng("D2_B1_ot_regular")
    eligible_pool = df.index[(df["Regular Hours"].fillna(0) == 0)
                              & (df["Total OT Paid"].fillna(0) == 0)].to_numpy()
    idx = pick_indices(n, RATE_PER_FAMILY, rng, eligible=eligible_pool)
    fake_ot = rng.uniform(500, 5000, size=len(idx)).round(2)
    for i, v in zip(idx, fake_ot):
        orig = df.at[i, "Total OT Paid"]
        df.at[i, "Total OT Paid"] = float(v)
        entries.append({"row_index": int(i), "anomaly_type": "B1_ot_regular_inconsistency",
                        "original_value": str(orig), "perturbed_value": f"{v:.2f}"})
        used.add(int(i))

    # B2 Salary-pay-basis mismatch: per Annum + tiny Regular Gross Paid
    rng = child_rng("D2_B2_salary_basis")
    pool = df.index[(df["Pay Basis"] == "per Annum")
                     & (df["Base Salary"] > 10000)
                     & (~df.index.isin(used))].to_numpy()
    idx = pick_indices(n, RATE_PER_FAMILY, rng, eligible=pool)
    for i in idx:
        base = df.at[i, "Base Salary"]
        orig = df.at[i, "Regular Gross Paid"]
        new_val = float(base) * 0.02  # 2 % of base salary
        df.at[i, "Regular Gross Paid"] = new_val
        entries.append({"row_index": int(i), "anomaly_type": "B2_salary_basis_mismatch",
                        "original_value": str(orig), "perturbed_value": f"{new_val:.2f}"})
        used.add(int(i))

    # B3 Near-duplicate name within agency: duplicate row with 1-char perturbed Last Name
    rng = child_rng("D2_B3_near_dup_name")
    pool = np.array([i for i in df.index.to_numpy() if int(i) not in used], dtype=np.int64)
    src_idx = pick_indices(n, RATE_PER_FAMILY, rng, eligible=pool)
    dup_rows = df.loc[src_idx].copy()
    new_last = [_one_char_perturb(s, rng) for s in dup_rows["Last Name"].tolist()]
    dup_rows["Last Name"] = new_last
    next_index = len(df)
    new_indices = np.arange(next_index, next_index + len(dup_rows))
    dup_rows.index = new_indices
    df = pd.concat([df, dup_rows])
    for src, new, ln in zip(src_idx, new_indices, new_last):
        entries.append({"row_index": int(new), "anomaly_type": "B3_near_duplicate_name",
                        "original_value": str(df.iloc[src]["Last Name"]),
                        "perturbed_value": str(ln)})
        used.add(int(new))

    # B4 Agency-title violation: assign a wrong-domain title
    rng = child_rng("D2_B4_agency_title")
    pool = np.array([i for i in df.index.to_numpy() if int(i) not in used], dtype=np.int64)
    idx = pick_indices(n, RATE_PER_FAMILY, rng, eligible=pool)
    choices = [t for _, t in D2_AGENCY_TITLE_SWAP]
    new_titles = rng.choice(choices, size=len(idx))
    for i, t in zip(idx, new_titles):
        orig = df.at[i, "Title Description"]
        df.at[i, "Title Description"] = t
        entries.append({"row_index": int(i), "anomaly_type": "B4_agency_title_violation",
                        "original_value": str(orig), "perturbed_value": str(t)})
        used.add(int(i))

    # B5 Magnitude outlier on Regular Gross Paid
    rng = child_rng("D2_B5_magnitude")
    pool = np.array([i for i in df.index.to_numpy()
                     if int(i) not in used and pd.notna(df.at[i, "Regular Gross Paid"])],
                    dtype=np.int64)
    idx = pick_indices(n, RATE_PER_FAMILY, rng, eligible=pool)
    for i in idx:
        orig = df.at[i, "Regular Gross Paid"]
        new_val = float(orig) * 10.0
        df.at[i, "Regular Gross Paid"] = new_val
        entries.append({"row_index": int(i), "anomaly_type": "B5_magnitude_outlier",
                        "original_value": f"{float(orig):.2f}",
                        "perturbed_value": f"{new_val:.2f}"})
        used.add(int(i))

    mask = pd.DataFrame(entries)
    mask["injection_rng_seed"] = SEED
    mask = mask.sort_values(["anomaly_type", "row_index"]).reset_index(drop=True)
    return df.reset_index(drop=True), mask


# ---------------------------------------------------------------------------
# D3 — UCI Credit Default
# ---------------------------------------------------------------------------
TARGET_COL_D3 = "default payment next month"  # actual column name in the parquet


def inject_d3(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    n = len(df)
    used: set[int] = set()
    entries: list[dict] = []

    # C1 EDUCATION out-of-domain (valid codes are 0-6; we set 7)
    rng = child_rng("D3_C1_education_oob")
    idx = pick_indices(n, RATE_PER_FAMILY, rng)
    for i in idx:
        orig = df.at[i, "EDUCATION"]
        df.at[i, "EDUCATION"] = 7
        entries.append({"row_index": int(i), "anomaly_type": "C1_education_out_of_domain",
                        "original_value": str(int(orig)), "perturbed_value": "7"})
        used.add(int(i))

    # C2 LIMIT_BAL=0 while default==0 and BILL_AMT1>0
    rng = child_rng("D3_C2_limitbal_zero")
    pool = df.index[(df[TARGET_COL_D3] == 0) & (df["BILL_AMT1"] > 0)
                    & (~df.index.isin(used))].to_numpy()
    idx = pick_indices(n, RATE_PER_FAMILY, rng, eligible=pool)
    for i in idx:
        orig = df.at[i, "LIMIT_BAL"]
        df.at[i, "LIMIT_BAL"] = 0
        entries.append({"row_index": int(i), "anomaly_type": "C2_limitbal_inconsistency",
                        "original_value": str(int(orig)), "perturbed_value": "0"})
        used.add(int(i))

    # C3 Sign violation on BILL_AMT1 (negate a positive bill)
    rng = child_rng("D3_C3_bill_sign")
    pool = df.index[(df["BILL_AMT1"] > 0) & (~df.index.isin(used))].to_numpy()
    idx = pick_indices(n, RATE_PER_FAMILY, rng, eligible=pool)
    for i in idx:
        orig = df.at[i, "BILL_AMT1"]
        df.at[i, "BILL_AMT1"] = -int(orig)
        entries.append({"row_index": int(i), "anomaly_type": "C3_bill_sign_violation",
                        "original_value": str(int(orig)),
                        "perturbed_value": str(-int(orig))})
        used.add(int(i))

    # C4 PAY_0=-2 (no consumption) but BILL_AMT1>5000
    rng = child_rng("D3_C4_pay_temporal")
    pool = df.index[(df["BILL_AMT1"] > 5000) & (~df.index.isin(used))].to_numpy()
    idx = pick_indices(n, RATE_PER_FAMILY, rng, eligible=pool)
    for i in idx:
        orig = df.at[i, "PAY_0"]
        df.at[i, "PAY_0"] = -2
        entries.append({"row_index": int(i), "anomaly_type": "C4_pay_temporal_violation",
                        "original_value": str(int(orig)), "perturbed_value": "-2"})
        used.add(int(i))

    # C5 AGE range violation (< 18 or > 95)
    rng = child_rng("D3_C5_age_range")
    pool = np.array([i for i in df.index.to_numpy() if int(i) not in used], dtype=np.int64)
    idx = pick_indices(n, RATE_PER_FAMILY, rng, eligible=pool)
    ages = rng.choice([15, 16, 17, 99, 105, 120], size=len(idx))
    for i, a in zip(idx, ages):
        orig = df.at[i, "AGE"]
        df.at[i, "AGE"] = int(a)
        entries.append({"row_index": int(i), "anomaly_type": "C5_age_range_violation",
                        "original_value": str(int(orig)),
                        "perturbed_value": str(int(a))})
        used.add(int(i))

    mask = pd.DataFrame(entries)
    mask["injection_rng_seed"] = SEED
    mask = mask.sort_values(["anomaly_type", "row_index"]).reset_index(drop=True)
    return df.reset_index(drop=True), mask


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def run(dataset_id: str, injector, in_name: str) -> dict:
    src = PROC / f"{in_name}.parquet"
    out_data = PROC / f"{dataset_id}_injected.parquet"
    out_mask = LABELS / f"{dataset_id}_mask.parquet"
    df = pd.read_parquet(src)
    n0 = len(df)
    injected, mask = injector(df)
    injected.to_parquet(out_data, index=False)
    mask.to_parquet(out_mask, index=False)
    counts = mask.groupby("anomaly_type").size().to_dict()
    return {
        "dataset_id": dataset_id,
        "rows_in": n0,
        "rows_out": len(injected),
        "anomalies_total": len(mask),
        "anomalies_rate": round(len(mask) / len(injected), 4),
        "anomalies_by_type": counts,
        "data_path": str(out_data),
        "mask_path": str(out_mask),
        "data_sha256": file_sha256(out_data),
        "mask_sha256": file_sha256(out_mask),
    }


def main() -> int:
    t0 = time.time()
    report = {
        "seed": SEED,
        "rate_per_family": RATE_PER_FAMILY,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "datasets": {},
    }
    for did, fn, in_name in [
        ("D1", inject_d1, "D1_sec_gl"),
        ("D2", inject_d2, "D2_nyc_fy2024"),
        ("D3", inject_d3, "D3_uci_credit"),
    ]:
        print(f"[{did}] Injecting anomalies into {in_name} ...")
        rep = run(did, fn, in_name)
        report["datasets"][did] = rep
        print(f"     rows {rep['rows_in']} -> {rep['rows_out']}, "
              f"anomalies {rep['anomalies_total']} ({rep['anomalies_rate']:.2%})")
        for t, c in rep["anomalies_by_type"].items():
            print(f"       {t}: {c}")

    report["elapsed_sec"] = round(time.time() - t0, 2)
    out = REPO_ROOT / "phase2_rebuild" / "data" / "injection_manifest.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nManifest: {out}")
    print(f"Elapsed: {report['elapsed_sec']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
