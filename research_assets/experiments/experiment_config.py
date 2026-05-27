"""
IEEE Access Experiment Configuration
DataFlow AI: Hybrid ML Data Quality & SQL Migration Research System
"""

import os
from pathlib import Path

# ── Reproducibility ───────────────────────────────────────────────────────────
RANDOM_SEED = 42

# ── Directory Roots ───────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent          # research_assets/
DATASET_DIR   = BASE_DIR / "datasets"
RESULTS_DIR   = BASE_DIR / "results"
FIGURES_DIR   = BASE_DIR / "figures"
REPORTS_DIR   = BASE_DIR / "reports"
LOGS_DIR      = BASE_DIR / "logs"

# ── Dataset sizes for scalability tests ──────────────────────────────────────
SCALABILITY_SIZES = [100, 500, 1_000, 5_000, 10_000, 50_000, 100_000]

# ── Ablation components ───────────────────────────────────────────────────────
ABLATION_COMPONENTS = [
    "full_system",
    "no_isolation_forest",
    "no_tfidf_similarity",
    "no_cross_field_validation",
    "no_confidence_routing",
    "no_semantic_matching",
    "no_rule_based_validation",
    "no_ensemble_logic",
    "statistical_only",
    "ml_only",
]

# ── Baseline systems ──────────────────────────────────────────────────────────
BASELINES = [
    "rule_based_only",
    "isolation_forest_only",
    "tfidf_only",
    "string_similarity_only",
    "threshold_validation_only",
    "single_model_anomaly",
    "full_hybrid_system",          # ← proposed system
]

# ── Contamination rates for anomaly injection ─────────────────────────────────
ANOMALY_RATES = [0.02, 0.05, 0.10, 0.15, 0.20, 0.30]

# ── Statistical test settings ─────────────────────────────────────────────────
N_CV_FOLDS    = 5
N_REPEATS     = 10        # repeated k-fold for statistical significance
ALPHA         = 0.05      # significance level

# ── Figure aesthetics (IEEE Access style) ────────────────────────────────────
FIGURE_DPI    = 300
FIGURE_FORMAT = ["png", "svg"]
FIGURE_WIDTH  = 7.0       # inches – single column = 3.5", double = 7.0"
FIGURE_HEIGHT = 5.0

PALETTE = {
    "full_system":              "#1a73e8",
    "no_isolation_forest":      "#e8710a",
    "no_tfidf_similarity":      "#0f9d58",
    "no_cross_field_validation":"#d93025",
    "no_confidence_routing":    "#7b1fa2",
    "no_semantic_matching":     "#ff6d00",
    "no_rule_based_validation": "#00bcd4",
    "no_ensemble_logic":        "#795548",
    "statistical_only":         "#9e9e9e",
    "ml_only":                  "#607d8b",
}

BASELINE_PALETTE = {
    "rule_based_only":         "#9e9e9e",
    "isolation_forest_only":   "#e8710a",
    "tfidf_only":              "#0f9d58",
    "string_similarity_only":  "#ff6d00",
    "threshold_validation_only":"#7b1fa2",
    "single_model_anomaly":    "#00bcd4",
    "full_hybrid_system":      "#1a73e8",
}
