"""
Phase 2 rebuild — Step 01: extract clean working slices from the raw downloads.

Deterministic. Idempotent. Writes parquet files under
phase2_rebuild/data/processed/. Never mutates files under data/raw/.

Outputs:
    D1_sec_gl.parquet         50,000 real GL-style postings from SEC EDGAR num.txt
    D2_nyc_fy2024.parquet     200,000 stratified-sampled FY2024 NYC payroll rows
    D3_uci_credit.parquet     30,000 UCI credit-default rows (full)

Run from repo root:
    python phase2_rebuild/scripts/01_extract_and_sample.py
"""
from __future__ import annotations

import io
import json
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW = REPO_ROOT / "phase2_rebuild" / "data" / "raw"
PROC = REPO_ROOT / "phase2_rebuild" / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

SEED = 42
TARGET_D1_ROWS = 50_000
TARGET_D2_ROWS = 200_000


def extract_d1_sec_gl() -> dict:
    """Stream SEC num.txt from the zip, filter, take the first TARGET_D1_ROWS rows."""
    src = RAW / "sec_edgar" / "2024q4.zip"
    out = PROC / "D1_sec_gl.parquet"
    if out.exists():
        df = pd.read_parquet(out)
        return {"rows": len(df), "path": str(out), "status": "skip-existing"}

    cols = ["adsh", "tag", "version", "ddate", "qtrs", "uom", "value", "coreg", "segments"]
    keep_dtype = {"adsh": "string", "tag": "string", "version": "string",
                  "uom": "string", "coreg": "string", "segments": "string"}
    collected: list[pd.DataFrame] = []
    rows = 0
    with zipfile.ZipFile(src) as z, z.open("num.txt") as f:
        # num.txt is tab-separated, may contain bad lines (footnotes with embedded tabs).
        reader = pd.read_csv(
            f, sep="\t", usecols=cols, dtype=keep_dtype,
            on_bad_lines="skip", chunksize=200_000, na_values=[""],
            engine="python",
        )
        for chunk in reader:
            chunk = chunk.assign(
                value=pd.to_numeric(chunk["value"], errors="coerce"),
                ddate=pd.to_numeric(chunk["ddate"], errors="coerce"),
                qtrs=pd.to_numeric(chunk["qtrs"], errors="coerce"),
            )
            chunk = chunk[(chunk["uom"] == "USD")
                          & chunk["qtrs"].isin([0, 1])
                          & chunk["value"].notna()
                          & chunk["tag"].notna()
                          & chunk["adsh"].notna()]
            if len(chunk) == 0:
                continue
            need = TARGET_D1_ROWS - rows
            if need <= 0:
                break
            take = chunk.head(need).copy()
            collected.append(take)
            rows += len(take)
            if rows >= TARGET_D1_ROWS:
                break

    df = pd.concat(collected, ignore_index=True)
    df = df.reset_index(drop=True)
    df.to_parquet(out, index=False)
    return {"rows": len(df), "path": str(out), "status": "written"}


def extract_d2_nyc_fy2024() -> dict:
    """Filter NYC payroll to Fiscal Year 2024, then stratified-sample to TARGET_D2_ROWS by Agency."""
    src = RAW / "nyc_payroll" / "citywide_payroll.csv"
    out = PROC / "D2_nyc_fy2024.parquet"
    if out.exists():
        df = pd.read_parquet(out)
        return {"rows": len(df), "path": str(out), "status": "skip-existing"}

    usecols = [
        "Fiscal Year", "Agency Name", "Last Name", "First Name", "Mid Init",
        "Agency Start Date", "Work Location Borough", "Title Description",
        "Leave Status as of June 30", "Base Salary", "Pay Basis",
        "Regular Hours", "Regular Gross Paid", "OT Hours", "Total OT Paid", "Total Other Pay",
    ]
    keep: list[pd.DataFrame] = []
    rows_seen = 0
    rows_kept = 0
    reader = pd.read_csv(src, usecols=usecols, dtype={"Fiscal Year": "Int32"},
                        chunksize=300_000, low_memory=False)
    for chunk in reader:
        rows_seen += len(chunk)
        sel = chunk[chunk["Fiscal Year"] == 2024]
        if len(sel):
            keep.append(sel)
            rows_kept += len(sel)
    full = pd.concat(keep, ignore_index=True)
    # Coerce numeric columns
    for c in ["Base Salary", "Regular Hours", "Regular Gross Paid",
              "OT Hours", "Total OT Paid", "Total Other Pay"]:
        full[c] = pd.to_numeric(full[c], errors="coerce")

    # Stratified sample by Agency Name to TARGET_D2_ROWS.
    rng = np.random.default_rng(SEED)
    if len(full) > TARGET_D2_ROWS:
        frac = TARGET_D2_ROWS / len(full)
        parts: list[pd.DataFrame] = []
        for _agency, g in full.groupby("Agency Name", dropna=False, sort=False):
            n = max(1, int(round(len(g) * frac)))
            n = min(n, len(g))
            parts.append(g.sample(n=n, random_state=int(rng.integers(0, 2**31 - 1))))
        sampled = pd.concat(parts)
        # Fix size to exactly TARGET_D2_ROWS.
        if len(sampled) > TARGET_D2_ROWS:
            sampled = sampled.sample(n=TARGET_D2_ROWS,
                                    random_state=int(rng.integers(0, 2**31 - 1)))
        elif len(sampled) < TARGET_D2_ROWS:
            extra = full.drop(sampled.index).sample(
                n=TARGET_D2_ROWS - len(sampled),
                random_state=int(rng.integers(0, 2**31 - 1)),
            )
            sampled = pd.concat([sampled, extra])
        sampled = sampled.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    else:
        sampled = full.reset_index(drop=True)

    sampled.to_parquet(out, index=False)
    return {"rows": len(sampled), "fy2024_total": rows_kept, "rows_seen": rows_seen,
            "path": str(out), "status": "written"}


def extract_d3_uci_credit() -> dict:
    """Convert the UCI XLS to parquet with proper column names."""
    src = RAW / "uci_credit_default" / "default_of_credit_card_clients.zip"
    out = PROC / "D3_uci_credit.parquet"
    if out.exists():
        df = pd.read_parquet(out)
        return {"rows": len(df), "path": str(out), "status": "skip-existing"}

    with zipfile.ZipFile(src) as z:
        name = [n for n in z.namelist() if n.endswith(".xls")][0]
        buf = io.BytesIO(z.read(name))
    # Row 0 is the artificial 'X1'..'X23' header; row 1 has the real names (LIMIT_BAL, ...).
    df = pd.read_excel(buf, engine="calamine", header=1)
    # Tidy first column: it's named 'ID'.
    if df.columns[0] != "ID":
        df = df.rename(columns={df.columns[0]: "ID"})
    df.to_parquet(out, index=False)
    return {"rows": len(df), "cols": len(df.columns), "path": str(out), "status": "written"}


def main() -> int:
    t0 = time.time()
    report = {
        "seed": SEED,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "datasets": {},
    }
    print("[D1] Extracting SEC EDGAR GL slice ...")
    report["datasets"]["D1"] = extract_d1_sec_gl()
    print(f"     {report['datasets']['D1']}")

    print("[D2] Extracting NYC FY2024 payroll slice ...")
    report["datasets"]["D2"] = extract_d2_nyc_fy2024()
    print(f"     {report['datasets']['D2']}")

    print("[D3] Extracting UCI credit-default ...")
    report["datasets"]["D3"] = extract_d3_uci_credit()
    print(f"     {report['datasets']['D3']}")

    report["elapsed_sec"] = round(time.time() - t0, 2)
    out = REPO_ROOT / "phase2_rebuild" / "data" / "extract_manifest.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nManifest: {out}")
    print(f"Elapsed: {report['elapsed_sec']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
