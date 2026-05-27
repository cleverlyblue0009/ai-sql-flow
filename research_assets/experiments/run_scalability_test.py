#!/usr/bin/env python3
"""
Scalability / Stress Test Experiment — IEEE Access
Measures runtime, memory, and throughput as dataset size scales.
"""

import sys, json, logging, statistics
from pathlib import Path
import numpy as np
import pandas as pd
import psutil, os

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_assets.experiments.experiment_config import (
    RANDOM_SEED, RESULTS_DIR, SCALABILITY_SIZES
)
from research_assets.experiments.experiment_engine import (
    full_system_detect, ResourceMonitor
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)
np.random.seed(RANDOM_SEED)
OUT = RESULTS_DIR / "scalability"
OUT.mkdir(parents=True, exist_ok=True)

N_REPEATS = 3          # averaged runs per size


def load_scalability_df(n: int) -> pd.DataFrame:
    path = Path(__file__).resolve().parents[1] / "datasets" / f"scalability_{n}.csv"
    return pd.read_csv(path)


def measure_one(df: pd.DataFrame) -> dict:
    """Single timing run; returns latency and memory."""
    with ResourceMonitor() as rm:
        y_pred = full_system_detect(df, text_cols=["text_field"])
    anomaly_rate = y_pred.mean()
    return {
        "latency_s":      round(rm.elapsed_s, 4),
        "latency_ms":     rm.latency_ms,
        "mem_delta_mb":   round(rm.mem_delta, 2),
        "anomaly_rate":   round(float(anomaly_rate), 4),
        "n_anomalies":    int(y_pred.sum()),
    }


def main():
    log.info("=" * 70)
    log.info("SCALABILITY / STRESS TEST  —  IEEE Access Experiment")
    log.info("=" * 70)

    results = {}
    proc = psutil.Process(os.getpid())

    for n in SCALABILITY_SIZES:
        try:
            df = load_scalability_df(n)
            log.info(f"\nSize: {n:>7,} rows")

            # warm-up run
            _ = full_system_detect(df.head(100), text_cols=["text_field"])

            # timed runs
            runs = []
            for i in range(N_REPEATS):
                m = measure_one(df)
                runs.append(m)
                log.info(f"  run {i+1}: {m['latency_ms']:.1f}ms  "
                         f"mem_Δ={m['mem_delta_mb']:.1f}MB  "
                         f"anomaly_rate={m['anomaly_rate']:.2%}")

            latencies  = [r["latency_ms"]   for r in runs]
            mem_deltas = [r["mem_delta_mb"] for r in runs]

            summary = {
                "n_rows":             n,
                "n_cols":             len(df.columns),
                "n_repeats":          N_REPEATS,
                "mean_latency_ms":    round(statistics.mean(latencies),  2),
                "std_latency_ms":     round(statistics.stdev(latencies) if len(latencies)>1 else 0, 2),
                "min_latency_ms":     round(min(latencies),              2),
                "max_latency_ms":     round(max(latencies),              2),
                "mean_mem_delta_mb":  round(statistics.mean(mem_deltas), 2),
                "throughput_rows_per_s": round(n / (statistics.mean(latencies)/1000), 1),
                "latency_ms_per_1k":  round(statistics.mean(latencies) / (n/1000), 3),
                "base_memory_mb":     round(proc.memory_info().rss / 1024**2, 1),
                "anomaly_rate":       runs[0]["anomaly_rate"],
            }
            results[str(n)] = summary

            log.info(f"  → avg {summary['mean_latency_ms']:.1f}ms  "
                     f"throughput={summary['throughput_rows_per_s']:,.0f} rows/s  "
                     f"per-1k={summary['latency_ms_per_1k']:.2f}ms")

        except Exception as e:
            log.error(f"  FAILED n={n}: {e}", exc_info=True)

    # Compute scalability regression (log-linear fit)
    sizes_arr = np.array([int(k) for k in results])
    lat_arr   = np.array([results[k]["mean_latency_ms"] for k in results])
    if len(sizes_arr) >= 3:
        coeffs = np.polyfit(np.log(sizes_arr), np.log(lat_arr), 1)
        scaling_exponent = round(float(coeffs[0]), 3)
        log.info(f"\nScaling exponent (log-log slope): {scaling_exponent:.3f}")
        log.info("  (<1.0 = sublinear,  1.0 = linear,  >1.0 = superlinear)")
    else:
        scaling_exponent = None

    output = {
        "experiment":       "scalability_stress_test",
        "seed":             RANDOM_SEED,
        "n_repeats":        N_REPEATS,
        "sizes_tested":     SCALABILITY_SIZES,
        "scaling_exponent": scaling_exponent,
        "results":          results,
    }
    out_file = OUT / "scalability_results.json"
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)

    log.info(f"\nSaved → {out_file}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
