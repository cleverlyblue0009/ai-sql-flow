#!/usr/bin/env python3
"""
IEEE Access Research Dataset Generator
Generates synthetic enterprise datasets with controlled, measurable anomalies.
All datasets are fully reproducible via RANDOM_SEED = 42.

Output: research_assets/datasets/
"""

import sys, os, json, logging
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_assets.experiments.experiment_config import (
    RANDOM_SEED, DATASET_DIR, SCALABILITY_SIZES
)

np.random.seed(RANDOM_SEED)
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

DATASET_DIR.mkdir(parents=True, exist_ok=True)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _rng():
    return np.random.default_rng(RANDOM_SEED)


def _inject_nulls(df: pd.DataFrame, col: str, frac: float, rng) -> int:
    idx = rng.choice(len(df), int(len(df) * frac), replace=False)
    df.loc[idx, col] = np.nan
    return len(idx)


def _inject_exact_dupes(df: pd.DataFrame, n: int, rng) -> pd.DataFrame:
    idx = rng.choice(len(df), min(n, len(df)), replace=False)
    return pd.concat([df, df.iloc[idx].copy()], ignore_index=True)


def _inject_outliers(df: pd.DataFrame, col: str, factor: float, n: int, rng) -> int:
    idx = rng.choice(len(df), min(n, len(df)), replace=False)
    mu = df[col].mean()
    df.loc[idx, col] = mu * factor
    return len(idx)


# ─── Dataset 1: GL Account Master ─────────────────────────────────────────────

def gen_gl_accounts(n: int = 5_000) -> tuple:
    rng = _rng()
    account_types = ["Asset", "Liability", "Equity", "Revenue", "Expense"]
    data = {
        "account_id":    [f"ACC{i:06d}" for i in range(1, n+1)],
        "account_name":  [f"Account_{i}" for i in range(1, n+1)],
        "account_type":  rng.choice(account_types, n),
        "balance":       rng.uniform(1_000, 500_000, n).round(2),
        "currency":      rng.choice(["USD", "EUR", "GBP"], n, p=[0.70, 0.20, 0.10]),
        "cost_center":   [f"CC{rng.integers(100, 999)}" for _ in range(n)],
        "entity":        rng.choice(["EntityA", "EntityB", "EntityC"], n),
        "is_active":     rng.choice([True, False], n, p=[0.95, 0.05]),
        "last_updated":  pd.date_range("2023-01-01", periods=n, freq="1h")[:n],
    }
    df = pd.DataFrame(data)

    gt = {"n_original": n, "injected": {}}
    # inject anomalies
    gt["injected"]["nulls_balance"]  = _inject_nulls(df, "balance", 0.05, rng)
    gt["injected"]["nulls_currency"] = _inject_nulls(df, "currency", 0.03, rng)
    gt["injected"]["exact_dupes"]    = n - len(df)  # before dupe injection
    df = _inject_exact_dupes(df, 250, rng)
    gt["injected"]["exact_dupes"]    = 250
    gt["injected"]["balance_outliers"]= _inject_outliers(df, "balance", 50, 300, rng)
    # invalid currency
    bad_idx = rng.choice(len(df), 200, replace=False)
    df.loc[bad_idx, "currency"] = rng.choice(["XXX", "INVALID", ""], 200)
    gt["injected"]["invalid_currency"] = 200
    # cross-field: active=False but large positive balance
    cf_idx = rng.choice(df.index[df["is_active"] == False].tolist(),
                        min(50, (df["is_active"]==False).sum()), replace=False)
    df.loc[cf_idx, "balance"] = rng.uniform(100_000, 999_000, len(cf_idx)).round(2)
    gt["injected"]["cross_field_violations"] = len(cf_idx)

    gt["total_rows"] = len(df)
    gt["total_anomalies"] = sum(gt["injected"].values())
    return df, gt


# ─── Dataset 2: Trial Balance ──────────────────────────────────────────────────

def gen_trial_balance(n: int = 3_000) -> tuple:
    rng = _rng()
    data = {
        "tb_id":         range(1, n+1),
        "account_id":    [f"ACC{rng.integers(1, 5001):06d}" for _ in range(n)],
        "period":        rng.choice(["2023-Q1","2023-Q2","2023-Q3","2023-Q4"], n),
        "debit":         rng.uniform(0, 200_000, n).round(2),
        "credit":        rng.uniform(0, 200_000, n).round(2),
        "net_balance":   None,
        "account_type":  rng.choice(["Asset","Liability","Equity","Revenue","Expense"], n),
        "entity":        rng.choice(["EntityA","EntityB","EntityC"], n),
    }
    df = pd.DataFrame(data)
    df["net_balance"] = (df["debit"] - df["credit"]).round(2)

    gt = {"n_original": n, "injected": {}}
    gt["injected"]["nulls_debit"]  = _inject_nulls(df, "debit",  0.04, rng)
    gt["injected"]["nulls_credit"] = _inject_nulls(df, "credit", 0.04, rng)
    # debit/credit sign anomalies: negative debit
    neg_idx = rng.choice(len(df), 150, replace=False)
    df.loc[neg_idx, "debit"] = -rng.uniform(1, 50_000, 150).round(2)
    gt["injected"]["negative_debit"] = 150
    # balance mismatch: net_balance inconsistent with debit-credit
    mismatch_idx = rng.choice(len(df), 200, replace=False)
    df.loc[mismatch_idx, "net_balance"] = df.loc[mismatch_idx, "debit"] + rng.uniform(1000, 10000, 200)
    gt["injected"]["balance_mismatches"] = 200
    df = _inject_exact_dupes(df, 120, rng)
    gt["injected"]["exact_dupes"] = 120

    gt["total_rows"] = len(df)
    gt["total_anomalies"] = sum(gt["injected"].values())
    return df, gt


# ─── Dataset 3: Journal Entries ────────────────────────────────────────────────

def gen_journal_entries(n: int = 8_000) -> tuple:
    rng = _rng()
    data = {
        "je_id":          [f"JE{i:08d}" for i in range(1, n+1)],
        "posting_date":   pd.date_range("2022-01-01", periods=n, freq="1h")[:n],
        "value_date":     pd.date_range("2022-01-01", periods=n, freq="1h")[:n],
        "amount":         rng.uniform(100, 50_000, n).round(2),
        "currency":       rng.choice(["USD", "EUR", "GBP"], n, p=[0.70, 0.20, 0.10]),
        "dr_account":     [f"ACC{rng.integers(1, 5001):06d}" for _ in range(n)],
        "cr_account":     [f"ACC{rng.integers(1, 5001):06d}" for _ in range(n)],
        "description":    [f"Journal entry {i}" for i in range(1, n+1)],
        "status":         rng.choice(["posted", "pending", "reversed"], n, p=[0.85, 0.10, 0.05]),
        "approver":       [f"User{rng.integers(1, 50)}" for _ in range(n)],
    }
    df = pd.DataFrame(data)

    gt = {"n_original": n, "injected": {}}
    # Posting after value date (temporal anomaly)
    td_idx = rng.choice(len(df), 400, replace=False)
    df.loc[td_idx, "posting_date"] = df.loc[td_idx, "value_date"] + pd.to_timedelta(
        rng.integers(1, 90, 400), unit="D")
    gt["injected"]["temporal_anomalies"] = 400
    gt["injected"]["nulls_approver"] = _inject_nulls(df, "approver", 0.08, rng)
    gt["injected"]["amount_outliers"] = _inject_outliers(df, "amount", 200, 500, rng)
    # same dr/cr account (self-transfer)
    self_idx = rng.choice(len(df), 180, replace=False)
    df.loc[self_idx, "cr_account"] = df.loc[self_idx, "dr_account"]
    gt["injected"]["self_transfers"] = 180
    df = _inject_exact_dupes(df, 350, rng)
    gt["injected"]["exact_dupes"] = 350

    gt["total_rows"] = len(df)
    gt["total_anomalies"] = sum(gt["injected"].values())
    return df, gt


# ─── Dataset 4: Mapping Table ──────────────────────────────────────────────────

def gen_mapping_table(n: int = 2_000) -> tuple:
    rng = _rng()
    source_names = [f"SRC_Account_{i}" for i in range(1, n+1)]
    target_names = [f"TGT_Account_{i}" for i in range(1, n+1)]
    data = {
        "mapping_id":     range(1, n+1),
        "source_account": source_names,
        "target_account": target_names,
        "source_type":    rng.choice(["Asset","Liability","Equity","Revenue","Expense"], n),
        "target_type":    rng.choice(["Asset","Liability","Equity","Revenue","Expense"], n),
        "confidence":     rng.uniform(0.60, 1.00, n).round(3),
        "mapping_method": rng.choice(["exact","semantic","rule_based","manual"], n,
                                     p=[0.40, 0.30, 0.20, 0.10]),
        "is_validated":   rng.choice([True, False], n, p=[0.70, 0.30]),
    }
    df = pd.DataFrame(data)

    gt = {"n_original": n, "injected": {}}
    # type mismatch (source type != target type — semantic anomaly)
    mismatch_idx = rng.choice(len(df), 300, replace=False)
    other_types = [t for t in ["Asset","Liability","Equity","Revenue","Expense"]]
    for i in mismatch_idx:
        df.loc[i, "target_type"] = rng.choice(
            [t for t in other_types if t != df.loc[i, "source_type"]])
    gt["injected"]["type_mismatches"] = 300
    # low-confidence mappings flagged as validated
    low_conf_idx = df.index[(df["confidence"] < 0.70) & (df["is_validated"] == True)]
    gt["injected"]["low_conf_validated"] = len(low_conf_idx)
    gt["injected"]["nulls_confidence"] = _inject_nulls(df, "confidence", 0.05, rng)

    gt["total_rows"] = len(df)
    gt["total_anomalies"] = sum(gt["injected"].values())
    return df, gt


# ─── Dataset 5: Entity Structures (for cross-field validation) ────────────────

def gen_entity_structures(n: int = 1_000) -> tuple:
    rng = _rng()
    data = {
        "entity_id":     [f"ENT{i:04d}" for i in range(1, n+1)],
        "entity_name":   [f"Entity_{i}" for i in range(1, n+1)],
        "country":       rng.choice(["US","GB","DE","FR","JP"], n),
        "currency":      rng.choice(["USD","GBP","EUR","EUR","JPY"], n),
        "fiscal_year_end": rng.choice(["Dec","Mar","Jun","Sep"], n),
        "consolidation_level": rng.integers(1, 5, n),
        "parent_entity": [f"ENT{rng.integers(1, n+1):04d}" if rng.random() > 0.3 else None
                          for _ in range(n)],
        "is_active":     rng.choice([True, False], n, p=[0.92, 0.08]),
    }
    df = pd.DataFrame(data)

    gt = {"n_original": n, "injected": {}}
    # country/currency mismatch (e.g. country=US but currency=EUR)
    cc_idx = rng.choice(len(df), 120, replace=False)
    for i in cc_idx:
        country = df.loc[i, "country"]
        wrong_ccy = {"US": "EUR", "GB": "USD", "DE": "JPY",
                     "FR": "GBP", "JP": "USD"}[country]
        df.loc[i, "currency"] = wrong_ccy
    gt["injected"]["country_currency_mismatches"] = 120
    # self-reference (entity is its own parent)
    self_idx = rng.choice(len(df), 50, replace=False)
    df.loc[self_idx, "parent_entity"] = df.loc[self_idx, "entity_id"]
    gt["injected"]["self_referencing_parents"] = 50

    gt["total_rows"] = len(df)
    gt["total_anomalies"] = sum(gt["injected"].values())
    return df, gt


# ─── Dataset 6: Scalability datasets ──────────────────────────────────────────

def gen_scalability_dataset(n: int) -> pd.DataFrame:
    """Numeric dataset with 10% anomaly injection for scalability benchmarks."""
    rng = _rng()
    df = pd.DataFrame({
        "id":          range(n),
        "value_a":     rng.normal(100, 15, n),
        "value_b":     rng.normal(500, 80, n),
        "value_c":     rng.exponential(200, n),
        "category":    rng.choice(["A","B","C","D"], n),
        "flag":        rng.choice([0, 1], n, p=[0.97, 0.03]),
        "text_field":  [f"Record_{i} description" for i in range(n)],
    })
    # inject 10% anomalies
    anom_n = max(1, int(n * 0.10))
    idx = rng.choice(n, anom_n, replace=False)
    df.loc[idx[:anom_n//2], "value_a"] = rng.uniform(1000, 5000, anom_n//2)
    df.loc[idx[anom_n//2:], "value_b"] = -rng.uniform(1000, 5000, anom_n - anom_n//2)
    return df


# ─── Dataset 7: Robustness / Noise Injection variants ─────────────────────────

def gen_robustness_variants(base_n: int = 2_000) -> dict:
    """Returns dict of DataFrames with progressively more noise."""
    rng = _rng()
    base_df, _ = gen_gl_accounts(base_n)

    variants = {}
    noise_levels = {
        "clean":            0.00,
        "low_noise":        0.05,
        "medium_noise":     0.15,
        "high_noise":       0.30,
        "extreme_noise":    0.50,
    }
    for level_name, frac in noise_levels.items():
        df = base_df.copy()
        if frac > 0:
            # inject nulls
            for col in ["balance", "currency", "account_type"]:
                _inject_nulls(df, col, frac / 3, rng)
            # inject outliers
            _inject_outliers(df, "balance", 100, int(len(df) * frac / 2), rng)
            # corrupt text
            n_corrupt = int(len(df) * frac / 4)
            idx = rng.choice(len(df), n_corrupt, replace=False)
            df.loc[idx, "account_name"] = [
                f"CORRUPT_{rng.integers(0, 999999)}" for _ in range(n_corrupt)
            ]
        variants[level_name] = df

    return variants


# ─── Dataset 8: SQL Migration Test Cases ──────────────────────────────────────

SQL_TEST_CASES = [
    # (id, source_dialect, complexity_label, sql)
    (1, "mysql",      "simple",
     "SELECT id, name FROM users WHERE status = 'active' LIMIT 100;"),
    (2, "mysql",      "medium",
     "SELECT u.id, u.name, COUNT(o.id) AS orders FROM users u "
     "LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name;"),
    (3, "mysql",      "complex",
     "SELECT a.*, b.total FROM accounts a "
     "INNER JOIN (SELECT account_id, SUM(amount) AS total FROM transactions "
     "WHERE status='completed' GROUP BY account_id) b ON a.id = b.account_id "
     "WHERE a.balance > IFNULL(b.total, 0) ORDER BY b.total DESC LIMIT 50;"),
    (4, "postgresql", "simple",
     "SELECT id, email FROM customers WHERE created_at > NOW() - INTERVAL '30 days';"),
    (5, "postgresql", "medium",
     "WITH ranked AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC) rn "
     "FROM employees) SELECT * FROM ranked WHERE rn = 1;"),
    (6, "postgresql", "complex",
     "SELECT p.id, p.name, COALESCE(s.total, 0) AS sales "
     "FROM products p LEFT JOIN (SELECT product_id, SUM(qty * price) AS total "
     "FROM sales GROUP BY product_id) s ON p.id = s.product_id "
     "WHERE p.is_active = TRUE ORDER BY sales DESC NULLS LAST;"),
    (7, "sqlserver",  "simple",
     "SELECT TOP 100 id, [name], email FROM [dbo].[users] WHERE is_active = 1;"),
    (8, "sqlserver",  "medium",
     "SELECT ISNULL(dept, 'N/A') dept, AVG(salary) avg_sal "
     "FROM [HR].[Employees] GROUP BY dept HAVING AVG(salary) > 50000;"),
    (9, "sqlserver",  "complex",
     "SELECT e.EmployeeID, e.Name, d.DeptName, RANK() OVER "
     "(PARTITION BY d.DeptID ORDER BY e.Salary DESC) AS SalaryRank "
     "FROM Employees e INNER JOIN Departments d ON e.DeptID = d.DeptID;"),
    (10,"mysql",      "ddl",
     "CREATE TABLE `orders` (`id` INT AUTO_INCREMENT PRIMARY KEY, "
     "`customer_id` INT NOT NULL, `amount` DECIMAL(10,2), "
     "`created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
     "ENGINE=InnoDB CHARSET=utf8mb4;"),
]


def gen_sql_test_cases_df() -> pd.DataFrame:
    return pd.DataFrame(SQL_TEST_CASES,
                        columns=["id","source_dialect","complexity","sql"])


# ─── Main ──────────────────────────────────────────────────────────────────────

def save(df: pd.DataFrame, name: str, gt: dict = None):
    path = DATASET_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    if gt:
        meta_path = DATASET_DIR / f"{name}_ground_truth.json"
        with open(meta_path, "w") as f:
            json.dump(gt, f, indent=2, default=str)
    log.info(f"  Saved {name}: {len(df):,} rows × {len(df.columns)} cols → {path.name}")
    return path


def main():
    log.info("=" * 70)
    log.info("IEEE Access Research Dataset Generation")
    log.info(f"Seed: {RANDOM_SEED}  |  Output: {DATASET_DIR}")
    log.info("=" * 70)

    # 1–5: core enterprise datasets
    log.info("\n[1/8] GL Account Master …")
    df, gt = gen_gl_accounts(5_000);  save(df, "gl_accounts", gt)

    log.info("[2/8] Trial Balance …")
    df, gt = gen_trial_balance(3_000); save(df, "trial_balance", gt)

    log.info("[3/8] Journal Entries …")
    df, gt = gen_journal_entries(8_000); save(df, "journal_entries", gt)

    log.info("[4/8] Mapping Table …")
    df, gt = gen_mapping_table(2_000);  save(df, "mapping_table", gt)

    log.info("[5/8] Entity Structures …")
    df, gt = gen_entity_structures(1_000); save(df, "entity_structures", gt)

    # 6: scalability
    log.info("[6/8] Scalability datasets …")
    for n in SCALABILITY_SIZES:
        df = gen_scalability_dataset(n)
        save(df, f"scalability_{n}")

    # 7: robustness variants
    log.info("[7/8] Robustness noise variants …")
    variants = gen_robustness_variants(2_000)
    for name, df in variants.items():
        save(df, f"robustness_{name}")

    # 8: SQL test cases
    log.info("[8/8] SQL migration test cases …")
    df = gen_sql_test_cases_df()
    save(df, "sql_test_cases")

    # manifest
    manifest = {
        "generated_at": str(pd.Timestamp.now()),
        "seed": RANDOM_SEED,
        "datasets": [str(p.name) for p in sorted(DATASET_DIR.glob("*.csv"))],
    }
    with open(DATASET_DIR / "MANIFEST.json", "w") as f:
        json.dump(manifest, f, indent=2)

    log.info("\n" + "=" * 70)
    log.info(f"Done. {len(manifest['datasets'])} files written to {DATASET_DIR}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
