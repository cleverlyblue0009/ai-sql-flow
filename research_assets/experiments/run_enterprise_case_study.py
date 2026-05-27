#!/usr/bin/env python3
"""
Enterprise Migration Case Study — IEEE Access
End-to-end simulation of a realistic enterprise GL migration workflow.
"""

import sys, json, logging, time
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_assets.experiments.experiment_config import RANDOM_SEED, RESULTS_DIR
from research_assets.experiments.experiment_engine import (
    full_system_detect, compute_metrics, ResourceMonitor,
    cross_field_validation, isolation_forest_outliers, tfidf_duplicates
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)
np.random.seed(RANDOM_SEED)
OUT = RESULTS_DIR / "enterprise"
OUT.mkdir(parents=True, exist_ok=True)
DS_DIR = Path(__file__).resolve().parents[1] / "datasets"

# ── Simulate SQL translation (rule-based, no API required) ────────────────────

MYSQL_TO_SNOWFLAKE_RULES = {
    "AUTO_INCREMENT": "AUTOINCREMENT",
    "TINYINT":        "SMALLINT",
    "MEDIUMINT":      "INT",
    "LONGTEXT":       "TEXT",
    "`":              '"',
    "ENGINE=InnoDB":  "",
    "CHARSET=utf8mb4":"",
    "IFNULL(":        "NVL(",
    "NOW()":          "CURRENT_TIMESTAMP()",
}

PG_TO_SNOWFLAKE_RULES = {
    "SERIAL":                   "AUTOINCREMENT",
    "BIGSERIAL":                "AUTOINCREMENT",
    "BOOLEAN":                  "BOOL",
    "TIMESTAMP WITH TIME ZONE": "TIMESTAMP_TZ",
    "RETURNING *":              "",
    "::text":                   "",
    "::integer":                "",
}


def rule_based_translate(sql: str, source: str, target: str) -> dict:
    import re, time as _time
    t0 = _time.perf_counter()
    out = sql
    rules = {}
    if source == "mysql" and target == "snowflake":
        rules = MYSQL_TO_SNOWFLAKE_RULES
    elif source == "postgresql" and target == "snowflake":
        rules = PG_TO_SNOWFLAKE_RULES

    n_transforms = 0
    for src_pat, tgt_rep in rules.items():
        if src_pat in out:
            out = out.replace(src_pat, tgt_rep)
            n_transforms += 1

    # Confidence heuristic: penalise for remaining dialect keywords
    penalty_terms = ["AUTO_INCREMENT", "SERIAL", "TINYINT", "`", "ENGINE=", "RETURNING"]
    remaining = sum(1 for t in penalty_terms if t in out)
    confidence = max(0.55, 0.92 - remaining * 0.06 - (0.02 if len(sql) > 2000 else 0))

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return {
        "translated_sql":  out.strip(),
        "n_transforms":    n_transforms,
        "confidence":      round(confidence, 4),
        "latency_ms":      round(elapsed_ms, 3),
        "translation_method": "rule_based",
    }


def semantic_similarity(s1: str, s2: str) -> float:
    """Token-overlap Jaccard similarity between two SQL strings."""
    import re
    t1 = set(re.findall(r"\b\w+\b", s1.upper()))
    t2 = set(re.findall(r"\b\w+\b", s2.upper()))
    if not t1 | t2:
        return 0.0
    return len(t1 & t2) / len(t1 | t2)


# ── Workflow stages ────────────────────────────────────────────────────────────

def stage_ingestion(df: pd.DataFrame) -> dict:
    t0 = time.perf_counter()
    n_rows  = len(df)
    n_cols  = len(df.columns)
    null_ct = int(df.isnull().sum().sum())
    dup_ct  = int(df.duplicated().sum())
    latency = (time.perf_counter() - t0) * 1000
    return dict(stage="ingestion", n_rows=n_rows, n_cols=n_cols,
                null_count=null_ct, duplicate_count=dup_ct,
                latency_ms=round(latency, 2))


def stage_anomaly_detection(df: pd.DataFrame, text_cols: list) -> dict:
    with ResourceMonitor() as rm:
        y_pred = full_system_detect(df, text_cols=text_cols)
    n_flagged = int(y_pred.sum())
    flag_rate = round(float(y_pred.mean()), 4)
    return dict(stage="anomaly_detection", n_flagged=n_flagged,
                flag_rate=flag_rate, latency_ms=rm.latency_ms,
                mem_delta_mb=round(rm.mem_delta, 2))


def stage_account_mapping(df: pd.DataFrame,
                           mapping_df: pd.DataFrame) -> dict:
    t0 = time.perf_counter()
    # Merge source accounts with mapping table
    if "account_id" in df.columns and "source_account" in mapping_df.columns:
        merged = df.merge(
            mapping_df[["source_account","target_account","confidence","is_validated"]],
            left_on="account_id", right_on="source_account", how="left")
        mapped_ct    = int(merged["target_account"].notna().sum())
        unmapped_ct  = int(merged["target_account"].isna().sum())
        avg_conf     = float(merged["confidence"].dropna().mean()) if merged["confidence"].notna().any() else 0.0
        validated_ct = int(merged["is_validated"].fillna(False).sum())
    else:
        mapped_ct = unmapped_ct = validated_ct = 0
        avg_conf  = 0.0

    latency = (time.perf_counter() - t0) * 1000
    return dict(stage="account_mapping",
                total_accounts=len(df),
                mapped_count=mapped_ct,
                unmapped_count=unmapped_ct,
                mapping_rate=round(mapped_ct/max(len(df),1), 4),
                avg_confidence=round(avg_conf, 4),
                validated_count=validated_ct,
                latency_ms=round(latency, 2))


def stage_sql_translation(test_cases_df: pd.DataFrame) -> dict:
    t0 = time.perf_counter()
    translations = []
    for _, row in test_cases_df.iterrows():
        result = rule_based_translate(row["sql"], row["source_dialect"], "snowflake")
        result["id"]         = int(row["id"])
        result["complexity"] = row["complexity"]
        result["source"]     = row["source_dialect"]
        result["sim_score"]  = round(semantic_similarity(row["sql"], result["translated_sql"]), 4)
        translations.append(result)

    confidences = [t["confidence"] for t in translations]
    latency_total = (time.perf_counter() - t0) * 1000

    return dict(stage="sql_translation",
                n_statements=len(translations),
                avg_confidence=round(float(np.mean(confidences)), 4),
                std_confidence=round(float(np.std(confidences)),  4),
                min_confidence=round(float(np.min(confidences)),  4),
                max_confidence=round(float(np.max(confidences)),  4),
                avg_semantic_similarity=round(
                    float(np.mean([t["sim_score"] for t in translations])), 4),
                total_latency_ms=round(latency_total, 2),
                per_statement_latency_ms=round(latency_total/max(len(translations),1), 3),
                translations=translations)


def stage_validation(df: pd.DataFrame,
                      anomaly_result: dict,
                      mapping_result: dict) -> dict:
    t0 = time.perf_counter()
    issues = []
    if anomaly_result["flag_rate"] > 0.15:
        issues.append("High anomaly rate exceeds 15% threshold")
    if mapping_result["mapping_rate"] < 0.90:
        issues.append(f"Low mapping coverage: {mapping_result['mapping_rate']:.1%}")
    if mapping_result["avg_confidence"] < 0.75:
        issues.append(f"Low average mapping confidence: {mapping_result['avg_confidence']:.2f}")
    validation_passed = len(issues) == 0
    latency = (time.perf_counter() - t0) * 1000
    return dict(stage="validation",
                passed=validation_passed,
                issues=issues,
                n_issues=len(issues),
                latency_ms=round(latency, 2))


def stage_report_generation(stages: list) -> dict:
    t0 = time.perf_counter()
    report = {
        "generated_at": str(pd.Timestamp.now()),
        "pipeline_stages": [s["stage"] for s in stages],
        "total_latency_ms": round(sum(s.get("latency_ms", 0) for s in stages), 2),
        "summary": {
            s["stage"]: {k: v for k, v in s.items() if k != "stage"}
            for s in stages
        }
    }
    latency = (time.perf_counter() - t0) * 1000
    report["report_latency_ms"] = round(latency, 2)
    return report


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 70)
    log.info("ENTERPRISE CASE STUDY  —  IEEE Access Experiment")
    log.info("=" * 70)

    # Load datasets
    gl_df       = pd.read_csv(DS_DIR / "gl_accounts.csv")
    mapping_df  = pd.read_csv(DS_DIR / "mapping_table.csv")
    sql_df      = pd.read_csv(DS_DIR / "sql_test_cases.csv")
    je_df       = pd.read_csv(DS_DIR / "journal_entries.csv")

    log.info(f"\nLoaded datasets:")
    log.info(f"  GL Accounts:       {len(gl_df):,} rows")
    log.info(f"  Mapping Table:     {len(mapping_df):,} rows")
    log.info(f"  Journal Entries:   {len(je_df):,} rows")
    log.info(f"  SQL Test Cases:    {len(sql_df):,} statements")

    # ── Pipeline execution ────────────────────────────────────────────────────
    t_pipeline_start = time.perf_counter()
    stages = []

    log.info("\n[Stage 1] Ingestion …")
    s1 = stage_ingestion(gl_df)
    stages.append(s1)
    log.info(f"  rows={s1['n_rows']:,}  nulls={s1['null_count']:,}  "
             f"dupes={s1['duplicate_count']:,}  {s1['latency_ms']:.1f}ms")

    log.info("[Stage 2] Anomaly Detection …")
    s2 = stage_anomaly_detection(gl_df, ["account_name","account_type"])
    stages.append(s2)
    log.info(f"  flagged={s2['n_flagged']:,}  rate={s2['flag_rate']:.2%}  "
             f"{s2['latency_ms']:.1f}ms")

    log.info("[Stage 3] Account Mapping …")
    s3 = stage_account_mapping(gl_df, mapping_df)
    stages.append(s3)
    log.info(f"  mapped={s3['mapped_count']:,}/{s3['total_accounts']:,}  "
             f"({s3['mapping_rate']:.1%})  conf={s3['avg_confidence']:.3f}  "
             f"{s3['latency_ms']:.1f}ms")

    log.info("[Stage 4] SQL Translation …")
    s4 = stage_sql_translation(sql_df)
    stages.append(s4)
    log.info(f"  statements={s4['n_statements']}  avg_conf={s4['avg_confidence']:.3f}  "
             f"avg_sim={s4['avg_semantic_similarity']:.3f}  "
             f"{s4['total_latency_ms']:.1f}ms total")

    log.info("[Stage 5] Validation …")
    s5 = stage_validation(gl_df, s2, s3)
    stages.append(s5)
    log.info(f"  passed={s5['passed']}  issues={s5['issues']}")

    log.info("[Stage 6] Report Generation …")
    report = stage_report_generation(stages)
    stages.append({"stage": "report_generation",
                   "latency_ms": report.get("report_latency_ms", 0)})

    pipeline_total_ms = (time.perf_counter() - t_pipeline_start) * 1000

    # ── Journal entry anomaly sub-analysis ───────────────────────────────────
    log.info("\n── Journal Entry Cross-Validation ──────────────────────────")
    je_pred = full_system_detect(je_df, text_cols=["description","dr_account"])
    log.info(f"  Journal entries flagged: {je_pred.sum():,}/{len(je_df):,}  "
             f"({je_pred.mean():.2%})")

    output = {
        "experiment": "enterprise_case_study",
        "seed": RANDOM_SEED,
        "pipeline": {
            "total_latency_ms": round(pipeline_total_ms, 2),
            "stages": stages,
            "report": report,
        },
        "journal_entry_analysis": {
            "n_entries": len(je_df),
            "n_flagged": int(je_pred.sum()),
            "flag_rate": round(float(je_pred.mean()), 4),
        },
        "sql_translations": s4["translations"],
    }

    out_file = OUT / "enterprise_results.json"
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2, default=str)

    log.info(f"\nTotal pipeline time: {pipeline_total_ms:.1f}ms")
    log.info(f"Saved → {out_file}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
