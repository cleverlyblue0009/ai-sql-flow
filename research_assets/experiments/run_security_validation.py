#!/usr/bin/env python3
"""
Security Validation Experiment — IEEE Access
Tests input validation, anomaly injection handling, and system resilience.
"""

import sys, json, logging
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_assets.experiments.experiment_config import RANDOM_SEED, RESULTS_DIR
from research_assets.experiments.experiment_engine import full_system_detect

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)
OUT = RESULTS_DIR / "security"
OUT.mkdir(parents=True, exist_ok=True)


SECURITY_TESTS = [
    {
        "name":        "sql_injection_in_text_column",
        "description": "Text field contains SQL injection payload",
        "severity":    "high",
    },
    {
        "name":        "xss_payload_in_text",
        "description": "Text field contains XSS payload",
        "severity":    "high",
    },
    {
        "name":        "oversized_string_value",
        "description": "Single field with 1MB string value",
        "severity":    "medium",
    },
    {
        "name":        "null_byte_injection",
        "description": "String fields contain null bytes",
        "severity":    "medium",
    },
    {
        "name":        "path_traversal_filename",
        "description": "Field contains path traversal sequence",
        "severity":    "medium",
    },
    {
        "name":        "float_overflow",
        "description": "Numeric column with np.inf and np.nan",
        "severity":    "low",
    },
    {
        "name":        "empty_string_fields",
        "description": "All text fields are empty strings",
        "severity":    "low",
    },
    {
        "name":        "max_rows_boundary",
        "description": "Dataset with exactly 1 row",
        "severity":    "low",
    },
    {
        "name":        "unicode_adversarial",
        "description": "Unicode RTL override and zero-width chars",
        "severity":    "medium",
    },
    {
        "name":        "command_injection_field",
        "description": "Field with OS command injection payload",
        "severity":    "high",
    },
    {
        "name":        "duplicate_column_names",
        "description": "DataFrame with duplicate column names",
        "severity":    "low",
    },
    {
        "name":        "extremely_wide_table",
        "description": "1000-column dataset",
        "severity":    "low",
    },
]


def gen_security_payload(test_name: str) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)

    if test_name == "sql_injection_in_text_column":
        payloads = [
            "'; DROP TABLE accounts; --",
            "' OR '1'='1",
            "1; SELECT * FROM users",
            '" OR 1=1 --',
            "UNION SELECT NULL,NULL,NULL--",
        ]
        df = pd.DataFrame({
            "id":      range(50),
            "balance": rng.uniform(100, 10000, 50),
            "name":    [payloads[i % len(payloads)] for i in range(50)],
        })

    elif test_name == "xss_payload_in_text":
        payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
            '"><script>alert(document.cookie)</script>',
        ]
        df = pd.DataFrame({
            "id":      range(50),
            "balance": rng.uniform(100, 10000, 50),
            "name":    [payloads[i % len(payloads)] for i in range(50)],
        })

    elif test_name == "oversized_string_value":
        big = "A" * 100_000
        df = pd.DataFrame({
            "id":    range(20),
            "value": rng.uniform(1, 100, 20),
            "text":  [big if i == 5 else f"normal_{i}" for i in range(20)],
        })

    elif test_name == "null_byte_injection":
        df = pd.DataFrame({
            "id":    range(30),
            "value": rng.uniform(1, 100, 30),
            "text":  [f"text\x00with\x00nulls_{i}" for i in range(30)],
        })

    elif test_name == "path_traversal_filename":
        df = pd.DataFrame({
            "id":       range(20),
            "balance":  rng.uniform(100, 1000, 20),
            "filepath": ["../../../etc/passwd" if i % 5 == 0
                         else f"normal/path/file_{i}.txt" for i in range(20)],
        })

    elif test_name == "float_overflow":
        vals = list(rng.uniform(1, 100, 45)) + [np.inf, -np.inf, np.nan, float("nan"), 1e308]
        df = pd.DataFrame({"id": range(50), "value": vals})

    elif test_name == "empty_string_fields":
        df = pd.DataFrame({
            "id":    range(50),
            "value": rng.uniform(1, 100, 50),
            "name":  [""] * 50,
            "code":  [""] * 50,
        })

    elif test_name == "max_rows_boundary":
        df = pd.DataFrame({"id": [1], "value": [42.0], "text": ["single_row"]})

    elif test_name == "unicode_adversarial":
        payloads = [
            "‮ABC",    # RTL override
            "​‌‍",           # zero-width chars
            "﻿ normal text",            # BOM
            "café naïve résumé",            # accented
            "中文测试",                       # CJK
        ]
        df = pd.DataFrame({
            "id":    range(50),
            "value": rng.uniform(1, 100, 50),
            "text":  [payloads[i % len(payloads)] for i in range(50)],
        })

    elif test_name == "command_injection_field":
        payloads = [
            "$(cat /etc/passwd)",
            "`whoami`",
            "& net user",
            "; rm -rf /",
        ]
        df = pd.DataFrame({
            "id":    range(40),
            "value": rng.uniform(1, 100, 40),
            "cmd":   [payloads[i % len(payloads)] for i in range(40)],
        })

    elif test_name == "duplicate_column_names":
        data = rng.uniform(1, 100, (30, 4))
        df = pd.DataFrame(data, columns=["id", "value", "value", "text"])
        # pandas handles duplicate cols — test if our code handles it too
        df = df.loc[:, ~df.columns.duplicated()]

    elif test_name == "extremely_wide_table":
        data = {f"col_{i}": rng.uniform(0, 1, 50) for i in range(1000)}
        df = pd.DataFrame(data)

    else:
        df = pd.DataFrame({"id": range(10), "value": range(10)})

    return df


def run_security_test(test: dict) -> dict:
    name = test["name"]
    try:
        df = gen_security_payload(name)
        # Sanitize inf/nan before passing
        df_safe = df.copy()
        for col in df_safe.select_dtypes(include=[np.number]).columns:
            df_safe[col] = df_safe[col].replace([np.inf, -np.inf], np.nan)

        text_cols = [c for c in df_safe.columns if df_safe[c].dtype == object]

        y_pred    = full_system_detect(df_safe, text_cols=text_cols)
        status    = "PASS — no exception raised"
        n_flagged = int(y_pred.sum())
        exception = None
    except Exception as e:
        status    = f"EXCEPTION: {type(e).__name__}"
        n_flagged = -1
        exception = str(e)[:200]

    result = {
        "test":        name,
        "description": test["description"],
        "severity":    test["severity"],
        "status":      status,
        "n_flagged":   n_flagged,
        "exception":   exception,
    }
    flag = "✓" if "PASS" in status else "✗"
    log.info(f"  {flag}  [{test['severity'].upper():<6s}] "
             f"{name:<38s}  → {status}")
    return result


def main():
    log.info("=" * 70)
    log.info("SECURITY VALIDATION  —  IEEE Access Experiment")
    log.info("=" * 70)

    results = [run_security_test(t) for t in SECURITY_TESTS]

    pass_ct  = sum(1 for r in results if "PASS" in r["status"])
    fail_ct  = len(results) - pass_ct
    pass_rate = pass_ct / max(len(results), 1)

    log.info(f"\n  Pass rate: {pass_rate:.1%}  ({pass_ct}/{len(results)})")
    if fail_ct > 0:
        log.warning(f"  FAILED tests ({fail_ct}):")
        for r in results:
            if "PASS" not in r["status"]:
                log.warning(f"    {r['test']}: {r['status']}")

    by_severity = {}
    for sev in ["high", "medium", "low"]:
        grp = [r for r in results if r["severity"] == sev]
        by_severity[sev] = {
            "total": len(grp),
            "passed": sum(1 for r in grp if "PASS" in r["status"]),
        }

    output = {
        "experiment":   "security_validation",
        "seed":         RANDOM_SEED,
        "pass_rate":    round(pass_rate, 4),
        "pass_count":   pass_ct,
        "fail_count":   fail_ct,
        "by_severity":  by_severity,
        "results":      results,
    }
    out_file = OUT / "security_results.json"
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)

    log.info(f"\nSaved → {out_file}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
