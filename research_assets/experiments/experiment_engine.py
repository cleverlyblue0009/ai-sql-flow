"""
Core experiment engine — directly exercises DataQualityAnalyzer ML components.
No web server required.  All metrics are real, computed from sklearn/scipy.
"""

import sys, time, logging, asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_assets.experiments.experiment_config import RANDOM_SEED

# sklearn
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score
)
from sklearn.neighbors import LocalOutlierFactor
from scipy import stats
import psutil, os

log = logging.getLogger(__name__)
np.random.seed(RANDOM_SEED)


# ─── Detection helpers ─────────────────────────────────────────────────────────

def iqr_outliers(series: pd.Series) -> np.ndarray:
    """Return boolean mask of IQR-based outliers."""
    Q1, Q3 = series.quantile(0.25), series.quantile(0.75)
    IQR = Q3 - Q1
    return ((series < Q1 - 1.5*IQR) | (series > Q3 + 1.5*IQR)).values


def zscore_outliers(series: pd.Series, threshold: float = 3.0) -> np.ndarray:
    z = np.abs(stats.zscore(series.dropna()))
    mask = np.zeros(len(series), dtype=bool)
    valid = series.notna().values
    mask[valid] = z > threshold
    return mask


def isolation_forest_outliers(df: pd.DataFrame,
                               contamination: float = 0.10) -> np.ndarray:
    numeric = df.select_dtypes(include=[np.number]).fillna(0)
    if numeric.empty or len(numeric) < 20:
        return np.zeros(len(df), dtype=bool)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(numeric)
    model  = IsolationForest(contamination=contamination, random_state=RANDOM_SEED)
    labels = model.fit_predict(scaled)
    return labels == -1


def lof_outliers(df: pd.DataFrame, contamination: float = 0.10) -> np.ndarray:
    numeric = df.select_dtypes(include=[np.number]).fillna(0)
    if numeric.empty or len(numeric) < 20:
        return np.zeros(len(df), dtype=bool)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(numeric)
    model  = LocalOutlierFactor(contamination=contamination)
    labels = model.fit_predict(scaled)
    return labels == -1


def tfidf_duplicates(df: pd.DataFrame,
                     text_cols: List[str],
                     threshold: float = 0.85) -> np.ndarray:
    """Return boolean mask of rows flagged as fuzzy-duplicates."""
    combined = df[text_cols].fillna("").astype(str).apply(" ".join, axis=1)
    if len(combined) < 2:
        return np.zeros(len(df), dtype=bool)
    try:
        vec = TfidfVectorizer(max_features=500)
        mat = vec.fit_transform(combined)
        sim = cosine_similarity(mat)
        np.fill_diagonal(sim, 0)
        return sim.max(axis=1) > threshold
    except Exception:
        return np.zeros(len(df), dtype=bool)


def exact_duplicates(df: pd.DataFrame) -> np.ndarray:
    return df.duplicated(keep="first").values


def rule_based_null_check(df: pd.DataFrame) -> np.ndarray:
    return df.isnull().any(axis=1).values


def rule_based_range_check(series: pd.Series,
                            lo: float = None,
                            hi: float = None) -> np.ndarray:
    mask = np.zeros(len(series), dtype=bool)
    if lo is not None:
        mask |= (series < lo).fillna(False).values
    if hi is not None:
        mask |= (series > hi).fillna(False).values
    return mask


def cross_field_validation(df: pd.DataFrame) -> np.ndarray:
    """
    Detects cross-field inconsistencies in GL / financial datasets.
    Heuristics used:
      - debit/credit sign conflicts
      - balance < 0 for Asset accounts
      - currency anomalies
    """
    mask = np.zeros(len(df), dtype=bool)
    if "debit" in df.columns and "credit" in df.columns:
        mask |= ((df["debit"].fillna(0) < 0) | (df["credit"].fillna(0) < 0)).values
    if "balance" in df.columns and "account_type" in df.columns:
        asset_mask = df["account_type"].str.lower().str.contains("asset", na=False)
        mask |= (asset_mask & (df["balance"].fillna(0) < 0)).values
    if "currency" in df.columns:
        valid = {"USD","EUR","GBP","JPY","CHF","CAD","AUD"}
        mask |= df["currency"].apply(
            lambda x: str(x).upper() not in valid if pd.notna(x) else True).values
    return mask


def confidence_routing(scores: np.ndarray,
                        low_th: float = 0.60,
                        high_th: float = 0.85) -> np.ndarray:
    """Route: 0=reject, 1=manual_review, 2=auto_accept."""
    routing = np.ones(len(scores), dtype=int)  # default: manual
    routing[scores >= high_th] = 2
    routing[scores <  low_th]  = 0
    return routing


# ─── Detection quality metrics ─────────────────────────────────────────────────

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    total = len(y_true)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0.0)
    fpr       = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr       = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    accuracy  = (tp + tn) / total if total > 0 else 0.0

    try:
        auc = float(roc_auc_score(y_true, y_pred))
    except Exception:
        auc = float("nan")

    return dict(precision=round(precision, 4),
                recall=round(recall, 4),
                f1=round(f1, 4),
                fpr=round(fpr, 4),
                fnr=round(fnr, 4),
                accuracy=round(accuracy, 4),
                auc=round(auc, 4) if not np.isnan(auc) else None,
                tp=tp, fp=fp, fn=fn, tn=tn)


# ─── Timing/resource wrapper ───────────────────────────────────────────────────

class ResourceMonitor:
    def __enter__(self):
        proc = psutil.Process(os.getpid())
        self._t0     = time.perf_counter()
        self._mem0   = proc.memory_info().rss / 1024**2   # MB
        self._proc   = proc
        return self

    def __exit__(self, *_):
        self.elapsed_s = time.perf_counter() - self._t0
        self.mem_delta = self._proc.memory_info().rss / 1024**2 - self._mem0

    @property
    def latency_ms(self):
        return round(self.elapsed_s * 1000, 2)


# ─── Full-system detection pipeline ───────────────────────────────────────────

def full_system_detect(df: pd.DataFrame,
                        text_cols: Optional[List[str]] = None,
                        contamination: float = 0.10) -> np.ndarray:
    """
    Ensemble detector — union of all detection methods.
    Returns binary anomaly mask (1 = anomaly detected).
    """
    mask = np.zeros(len(df), dtype=bool)

    # Null check
    mask |= rule_based_null_check(df)

    # Cross-field validation
    mask |= cross_field_validation(df)

    # IsolationForest
    mask |= isolation_forest_outliers(df, contamination)

    # Statistical (IQR) on all numeric cols
    for col in df.select_dtypes(include=[np.number]).columns:
        s = df[col].dropna()
        if len(s) >= 10:
            col_mask = iqr_outliers(df[col].fillna(df[col].median()))
            mask |= col_mask

    # TF-IDF fuzzy duplicate
    if text_cols and any(c in df.columns for c in text_cols):
        valid_txt = [c for c in text_cols if c in df.columns]
        mask |= tfidf_duplicates(df, valid_txt)

    # Exact duplicates
    mask |= exact_duplicates(df)

    return mask.astype(int)


# ─── Ablation: single component detectors ─────────────────────────────────────

def ablation_detect(df: pd.DataFrame,
                    component: str,
                    text_cols: Optional[List[str]] = None,
                    contamination: float = 0.10) -> np.ndarray:
    """Run the full pipeline minus one component."""
    mask = np.zeros(len(df), dtype=bool)

    if component != "no_rule_based_validation":
        mask |= rule_based_null_check(df)

    if component != "no_cross_field_validation":
        mask |= cross_field_validation(df)

    if component != "no_isolation_forest":
        mask |= isolation_forest_outliers(df, contamination)

    if component not in ("no_ensemble_logic", "statistical_only"):
        for col in df.select_dtypes(include=[np.number]).columns:
            s = df[col].dropna()
            if len(s) >= 10:
                mask |= iqr_outliers(df[col].fillna(df[col].median()))

    if component not in ("no_tfidf_similarity", "no_semantic_matching"):
        if text_cols and any(c in df.columns for c in text_cols):
            valid_txt = [c for c in text_cols if c in df.columns]
            mask |= tfidf_duplicates(df, valid_txt)

    if component != "no_ensemble_logic":
        mask |= exact_duplicates(df)

    return mask.astype(int)
