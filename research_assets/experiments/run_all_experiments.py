#!/usr/bin/env python3
"""
Master Experiment Runner — IEEE Access
Executes all experiments in correct dependency order.
Usage: python run_all_experiments.py [--skip-slow]
"""

import sys, subprocess, time, json, logging, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ROOT.parent / "logs" / "master_run.log"),
    ]
)
log = logging.getLogger(__name__)


def run_script(script: str, label: str) -> bool:
    path = ROOT / script
    t0   = time.perf_counter()
    log.info(f"\n{'─'*60}")
    log.info(f"▶  {label}")
    log.info(f"   {path}")
    log.info(f"{'─'*60}")
    try:
        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=False,    # let stdout/stderr flow through
            timeout=3600,            # 1-hour timeout
        )
        elapsed = time.perf_counter() - t0
        if result.returncode == 0:
            log.info(f"✓  {label}  ({elapsed:.1f}s)")
            return True
        else:
            log.error(f"✗  {label}  returned exit code {result.returncode}  ({elapsed:.1f}s)")
            return False
    except subprocess.TimeoutExpired:
        log.error(f"✗  {label}  TIMED OUT after 3600s")
        return False
    except Exception as e:
        log.error(f"✗  {label}  EXCEPTION: {e}")
        return False


PIPELINE = [
    # (script_name, label, slow?)
    ("generate_research_datasets.py", "Dataset Generation",          False),
    ("run_ablation_study.py",          "Ablation Study",              False),
    ("run_baseline_comparison.py",     "Baseline Comparison",         False),
    ("run_scalability_test.py",        "Scalability / Stress Test",   True),   # slow for 100k
    ("run_robustness_test.py",         "Robustness Testing",          False),
    ("run_confidence_analysis.py",     "Confidence Analysis",         False),
    ("run_false_positive_analysis.py", "False Positive Analysis",     False),
    ("run_cross_validation.py",        "Cross-Validation & Stats",    True),   # slow: 10×5 folds
    ("run_enterprise_case_study.py",   "Enterprise Case Study",       False),
    ("run_security_validation.py",     "Security Validation",         False),
    ("generate_figures.py",            "Figure Generation",           False),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-slow", action="store_true",
                        help="Skip experiments marked as slow")
    args = parser.parse_args()

    (ROOT.parent / "logs").mkdir(parents=True, exist_ok=True)

    log.info("=" * 70)
    log.info("IEEE ACCESS RESEARCH EXPERIMENT SUITE")
    log.info(f"Root: {ROOT.parent}")
    log.info(f"Skip-slow: {args.skip_slow}")
    log.info("=" * 70)

    t_start = time.perf_counter()
    summary = []

    for script, label, slow in PIPELINE:
        if slow and args.skip_slow:
            log.info(f"◌  SKIPPED (slow): {label}")
            summary.append({"script": script, "label": label, "status": "skipped"})
            continue

        ok = run_script(script, label)
        summary.append({"script": script, "label": label,
                         "status": "ok" if ok else "failed"})

    total_elapsed = time.perf_counter() - t_start

    # ── Write execution summary ────────────────────────────────────────────
    summary_path = ROOT.parent / "results" / "execution_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump({
            "total_elapsed_s": round(total_elapsed, 1),
            "steps":           summary,
            "n_ok":    sum(1 for s in summary if s["status"] == "ok"),
            "n_failed":sum(1 for s in summary if s["status"] == "failed"),
            "n_skipped":sum(1 for s in summary if s["status"] == "skipped"),
        }, f, indent=2)

    log.info(f"\n{'='*70}")
    log.info(f"COMPLETE — total time: {total_elapsed:.0f}s")
    ok_ct    = sum(1 for s in summary if s["status"] == "ok")
    fail_ct  = sum(1 for s in summary if s["status"] == "failed")
    skip_ct  = sum(1 for s in summary if s["status"] == "skipped")
    log.info(f"  ✓  passed:  {ok_ct}")
    log.info(f"  ✗  failed:  {fail_ct}")
    log.info(f"  ◌  skipped: {skip_ct}")
    log.info(f"  Summary → {summary_path}")
    log.info("=" * 70)

    return 0 if fail_ct == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
