#!/usr/bin/env python3
"""
Robustness Testing Experiment — IEEE Access
Measures system resilience under increasing noise and adversarial inputs.
"""

import sys, json, logging, statistics
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_assets.experiments.experiment_config import RANDOM_SEED, RESULTS_DIR
from research_assets.experiments.experiment_engine import (
    full_system_detect, compute_metrics, ResourceMonitor,
    rule_based_null_check, isolation_forest_outliers
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)
np.random.seed(RANDOM_SEED)
OUT = RESULTS_DIR / "robustness"
OUT.mkdir(parents=True, exist_ok=True)

NOISE_LEVELS = {
    "clean":         0.00,
    "low_noise":     0.05,
    "medium_noise":  0.15,
    "high_noise":    0.30,
    "extreme_noise": 0.50,
}

ADVERSARIAL_TESTS = [
    "empty_dataframe",
    "all_nulls",
    "single_row",
    "two_rows",
    "all_identical",
    "mixed_dtypes",
    "unicode_text",
    "large_string_values",
    "extreme_numeric_range",
    "corrupted_headers",
]


def load_robustness_variant(level: str) -> pd.DataFrame:
    path = Path(__file__).resolve().parents[1] / "datasets" / f"robustness_{level}.csv"
    return pd.read_csv(path)


def build_gt_mask(df: pd.DataFrame, noise_frac: float) -> np.ndarray:
    rng = np.random.default_rng(RANDOM_SEED)
    # anomaly rate ≈ noise fraction
    n = max(1, int(len(df) * max(noise_frac, 0.05)))
    n = min(n, len(df))
    mask = np.zeros(len(df), dtype=int)
    mask[rng.choice(len(df), n, replace=False)] = 1
    return mask


# ── Adversarial edge cases ─────────────────────────────────────────────────────

def gen_adversarial(test_name: str) -> pd.DataFrame | None:
    rng = np.random.default_rng(RANDOM_SEED)
    if test_name == "empty_dataframe":
        return pd.DataFrame({"a": [], "b": []})
    if test_name == "all_nulls":
        return pd.DataFrame({"a": [None]*100, "b": [None]*100,
                              "c": [None]*100})
    if test_name == "single_row":
        return pd.DataFrame({"a": [1.0], "b": ["text"], "c": [0.5]})
    if test_name == "two_rows":
        return pd.DataFrame({"a": [1.0, 2.0], "b": ["t1","t2"],
                              "c": [0.5, 0.6]})
    if test_name == "all_identical":
        return pd.DataFrame({"a": [5.0]*200, "b": ["same"]*200,
                              "c": ["USD"]*200})
    if test_name == "mixed_dtypes":
        return pd.DataFrame({
            "a": [1, "two", 3.0, None, True],
            "b": ["A", 2, None, "D", 5],
        })
    if test_name == "unicode_text":
        return pd.DataFrame({
            "a": rng.integers(1, 100, 50).astype(float),
            "text": ["日本語テキスト" if i % 3 == 0
                     else "normal text" for i in range(50)],
        })
    if test_name == "large_string_values":
        return pd.DataFrame({
            "a": rng.integers(1, 100, 50).astype(float),
            "b": ["x" * rng.integers(1, 5000) for _ in range(50)],
        })
    if test_name == "extreme_numeric_range":
        return pd.DataFrame({
            "a": np.concatenate([rng.normal(0, 1, 90),
                                  [1e15, -1e15, np.inf, -np.inf, np.nan,
                                   1e300, -1e300, 0, 0, 0]]),
        })
    if test_name == "corrupted_headers":
        df = pd.DataFrame(rng.normal(0, 1, (100, 5)))
        df.columns = ["", " ", "col\nwith\nnewline", "123", "col with spaces"]
        return df
    return None


def run_robustness_noise_tests() -> list:
    results = []
    for level_name, noise_frac in NOISE_LEVELS.items():
        try:
            df = load_robustness_variant(level_name)
            y_true = build_gt_mask(df, noise_frac)
            text_cols = [c for c in ["account_name","account_type","currency"]
                         if c in df.columns]
            with ResourceMonitor() as rm:
                y_pred = full_system_detect(df, text_cols=text_cols)
            m = compute_metrics(y_true, y_pred)
            m.update({
                "level": level_name,
                "noise_frac": noise_frac,
                "n_rows": len(df),
                "latency_ms": rm.latency_ms,
                "mem_delta_mb": round(rm.mem_delta, 2),
            })
            results.append(m)
            log.info(f"  {level_name:<18s}  noise={noise_frac:.0%}  "
                     f"F1={m['f1']:.4f}  P={m['precision']:.4f}  "
                     f"R={m['recall']:.4f}")
        except Exception as e:
            log.error(f"  FAILED {level_name}: {e}")
    return results


def run_adversarial_tests() -> list:
    results = []
    for test_name in ADVERSARIAL_TESTS:
        df = gen_adversarial(test_name)
        if df is None:
            continue
        try:
            with ResourceMonitor() as rm:
                y_pred = full_system_detect(
                    df.replace([np.inf, -np.inf], np.nan),
                    text_cols=[c for c in df.columns
                               if df[c].dtype == object])
            status   = "PASS"
            n_flagged = int(y_pred.sum()) if len(y_pred) else 0
        except Exception as e:
            status    = f"EXCEPTION: {type(e).__name__}: {str(e)[:80]}"
            n_flagged = -1
            rm = type("_", (), {"latency_ms": -1, "mem_delta": 0})()

        results.append({
            "test": test_name,
            "n_rows": len(df),
            "status": status,
            "n_flagged": n_flagged,
            "latency_ms": getattr(rm, "latency_ms", -1),
        })
        flag = "✓" if status == "PASS" else "✗"
        log.info(f"  {flag} {test_name:<30s}  rows={len(df):>4}  "
                 f"flagged={n_flagged}  status={status}")
    return results


def main():
    log.info("=" * 70)
    log.info("ROBUSTNESS TESTING  —  IEEE Access Experiment")
    log.info("=" * 70)

    log.info("\n── Noise Level Tests ──────────────────────────────────────")
    noise_results = run_robustness_noise_tests()

    log.info("\n── Adversarial / Edge-Case Tests ──────────────────────────")
    adv_results = run_adversarial_tests()

    pass_rate = sum(1 for r in adv_results if r["status"] == "PASS") / max(len(adv_results), 1)
    log.info(f"\n  Adversarial pass rate: {pass_rate:.1%}  "
             f"({sum(1 for r in adv_results if r['status']=='PASS')}"
             f"/{len(adv_results)})")

    output = {
        "experiment":             "robustness_testing",
        "seed":                   RANDOM_SEED,
        "noise_level_results":    noise_results,
        "adversarial_results":    adv_results,
        "adversarial_pass_rate":  round(pass_rate, 4),
    }
    out_file = OUT / "robustness_results.json"
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)

    log.info(f"\nSaved → {out_file}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
