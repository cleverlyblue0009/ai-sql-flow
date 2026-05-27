# System Analysis Report
## AI-SQL-Flow: Hybrid Data Quality and SQL Migration Platform

**Version:** 1.0  
**Analysis Date:** 2026-05-27  
**Branch:** research-experiments-ieee-access

---

## 1. Overview

AI-SQL-Flow is a production-grade data quality and SQL migration platform integrating machine learning anomaly detection with AI-assisted SQL dialect translation. The system is designed for enterprise financial data workflows — specifically general ledger accounts, trial balances, journal entries, and account mapping tables — where data integrity is critical for regulatory compliance and audit accuracy.

The platform exposes a FastAPI REST API with WebSocket support for real-time progress reporting, backed by SQLite for job state, and integrates with Google Gemini for AI-assisted SQL translation.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client Layer                                 │
│          React/Vite SPA  ←→  WebSocket  ←→  REST API               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                      FastAPI Application                            │
│  /data-quality/*   │   /migration/*   │   /websocket/*             │
└────────┬───────────┴────────┬──────────┴──────────────────────────┘
         │                   │
┌────────▼────────┐  ┌───────▼──────────┐
│  DataQuality    │  │   Migration      │
│  Module         │  │   Module         │
│  ─────────────  │  │  ─────────────── │
│  Analyzer       │  │  AITranslator    │
│  Cleaner        │  │  BatchManager    │
│  Routes         │  │  ExportManager   │
│  Schemas        │  │  HistoryManager  │
└────────┬────────┘  └───────┬──────────┘
         │                   │
┌────────▼───────────────────▼──────────┐
│           Database Layer               │
│   SQLite (app_data.db) via SQLAlchemy  │
└───────────────────────────────────────┘
```

---

## 3. Data Quality Module (`app/data_quality/`)

### 3.1 DataQualityAnalyzer (`analyzer.py`)

The core ML pipeline implements a multi-dimensional quality assessment framework.

**Component Architecture:**
```
DataQualityAnalyzer
├── IsolationForest (contamination=0.10, random_state=42)
├── TfidfVectorizer (max_features=500) + cosine_similarity
├── IQR-based outlier detection (Q1 - 1.5×IQR, Q3 + 1.5×IQR)
├── Z-score outlier detection (threshold=3.0)
├── Pattern validation (email, phone, date, numeric)
├── Missing value analysis (per-column null rates)
└── Cross-field consistency validation
```

**Quality Score Formula:**
```
Q = 0.25 × completeness
  + 0.25 × validity
  + 0.20 × uniqueness
  + 0.15 × consistency
  + 0.15 × accuracy
```

All weights sum to 1.0. Individual dimensions are normalized to [0, 1] before composition.

**Anomaly Detection Flow:**
1. Numeric features extracted and standardized (StandardScaler)
2. IsolationForest fit on full dataset; anomaly score normalized to [0, 1]
3. TF-IDF vectorization of concatenated text columns
4. Cosine similarity matrix computed; per-row max similarity as duplicate score
5. IQR fences computed per numeric column; flags exceed boundaries
6. Cross-field rules applied (negative debits, asset/balance sign, currency format)
7. Results merged via union logic: any flag → flagged row

**Confidence Routing Logic:**
- Score < 0.40 → route = 2 (auto-accept: likely clean)
- 0.40 ≤ Score ≤ 0.70 → route = 1 (manual review)
- Score > 0.70 → route = 0 (auto-reject: likely anomalous)

### 3.2 DataCleaner (`cleaner.py`)

Implements 11 cleaning operations:

| Operation | Algorithm | Use Case |
|-----------|-----------|----------|
| Remove duplicates | Exact match + TF-IDF | Identical/near-identical rows |
| Fill missing (numeric) | KNNImputer (k=5) | Continuous features |
| Fill missing (categorical) | Mode imputation | Categorical features |
| Fill missing (iterative) | IterativeImputer (BayesianRidge) | Complex missingness patterns |
| Remove outliers | IsolationForest | Anomalous numeric patterns |
| Remove outliers | DBSCAN (eps=0.5) | Density-based spatial outliers |
| Standardize formats | Regex + datetime parsing | Date/time, currency, phone |
| Validate ranges | Domain-defined bounds | Financial thresholds |
| Resolve inconsistencies | Rule-based lookup | Type/category normalization |
| Smart deduplication | TF-IDF cosine (threshold=0.85) | Fuzzy/near-duplicate removal |
| Type coercion | pandas astype + fallback | Mixed-type columns |

---

## 4. Migration Module (`app/migration/`)

### 4.1 AITranslationEngine (`ai_translator.py`)

**Primary path:** Google Gemini API (gemini-2.0-flash) with structured prompt engineering.

**Fallback path:** Deterministic rule-based dialect conversion.

**Supported dialect pairs:**

| Source | Target |
|--------|--------|
| MySQL | Snowflake |
| MySQL | PostgreSQL |
| PostgreSQL | Snowflake |
| SQL Server | Snowflake |
| SQL Server | PostgreSQL |

**Rule-based transformation patterns (partial):**

```python
# MySQL → Snowflake
"LIMIT n"                  → "LIMIT n"              # same
"ISNULL(x)"                → "ISNULL(x, 0)"         # Snowflake requires default
"AUTO_INCREMENT"           → "AUTOINCREMENT"
"ENGINE=InnoDB"            → removed
"` backtick identifiers`"  → "\" double-quotes\""
"IFNULL(a, b)"             → "NVL(a, b)"

# SQL Server → Snowflake
"TOP n"                    → "LIMIT n"
"ISNULL(x, y)"             → "NVL(x, y)"
"[bracket identifiers]"    → preserved
"WITH (NOLOCK)"            → removed
```

**Confidence Scoring:**
```
confidence = base_score
           × complexity_penalty
           × semantic_similarity_bonus
```

- Base score: 0.95 for AI path, 0.92 for rule-based
- Complexity penalty: simple=1.0, medium=0.97, complex=0.93, DDL=0.88
- Semantic similarity: Jaccard token overlap between source and translated ASTs

### 4.2 Enterprise Features (`enterprise_features.py`)

**BatchMigrationManager:**
- Manages concurrent migration jobs with queue-based scheduling
- Supports priority levels: HIGH, NORMAL, LOW
- Provides partial rollback to last known-good state

**MigrationExportManager:**
- Exports migration results to: JSON, CSV, SQL script, Excel (xlsx)
- Supports selective export by status (completed, failed, pending)

**MigrationHistoryManager:**
- Maintains full audit trail: source SQL, translated SQL, confidence, timestamp, user
- Supports diff views between migration versions
- Provides rollback by history ID

---

## 5. Confidence Routing Pipeline

The composite confidence scoring used in the research experiments mirrors the production routing logic:

```
composite_score = 0.45 × IsolationForest_anomaly_score
                + 0.35 × TF-IDF_max_cosine_similarity
                + 0.20 × null_rate_per_row
```

**Routing decision tree:**
```
composite_score < low_threshold (0.40)  → route = 2 (auto-accept)
composite_score ≤ high_threshold (0.70) → route = 1 (manual review)
composite_score > high_threshold (0.70) → route = 0 (auto-reject)
```

Tightened routing (low=0.30, high=0.80) increases manual review volume but reduces false positives in auto-accept/reject buckets.

---

## 6. Data Flow

```
CSV / Database Upload
        │
        ▼
┌───────────────────┐
│  File Validation  │  Format check, size limit (100MB default)
│  & Parsing        │  pandas read_csv / read_excel / SQLAlchemy
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Feature          │  Numeric extraction, text concatenation,
│  Engineering      │  null-rate computation, dtype inference
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  ML Anomaly       │  IsolationForest + IQR + TF-IDF + Rules
│  Detection        │  Parallel component execution
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Confidence       │  Weighted composite score computation
│  Scoring          │  Routing decision
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Cleaning         │  KNN/Iterative imputation, deduplication,
│  Operations       │  outlier removal, format standardization
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Report           │  Quality score, dimensions, anomaly list,
│  Generation       │  recommendations, audit trail
└───────────────────┘
```

---

## 7. WebSocket Real-Time Layer

The WebSocket module (`app/websocket/`) provides real-time progress broadcasting for long-running operations:

- `migration_ws.py`: Streams per-SQL-statement translation progress
- `manager.py`: Connection manager with per-job room multiplexing
- Events: `progress`, `status_update`, `error`, `complete`

---

## 8. Database Schema (SQLite via SQLAlchemy)

Key models (`app/database/models.py`):

```
MigrationJob        – id, name, status, source_dialect, target_dialect,
                      created_at, updated_at, user_id
MigrationStatement  – job_id, sequence, source_sql, translated_sql,
                      confidence, method, error, latency_ms
DataQualityJob      – id, filename, status, quality_score, n_rows,
                      n_anomalies, created_at
DataQualityIssue    – job_id, row_index, column, issue_type, severity,
                      description, value
AuditLog            – timestamp, action, entity_type, entity_id,
                      user_id, details_json
```

---

## 9. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| IsolationForest contamination=0.10 | Conservative default; financial datasets typically have <15% anomalies |
| TF-IDF max_features=500 | Balances vocabulary coverage with computational cost at 10K-row scale |
| cosine_similarity threshold=0.85 | Validated on financial terminology: avoids false positives from shared tokens |
| KNNImputer k=5 | Robust for tabular financial data; more stable than mean/mode for correlated features |
| Rule-based SQL fallback | Provides deterministic, auditable translations when LLM is unavailable or quota-exceeded |
| Union logic for anomaly merge | Maximizes recall; precision tuned post-hoc via confidence threshold |
| SQLite for state | Sufficient for single-instance deployment; migration path to PostgreSQL via SQLAlchemy |

---

## 10. Component Dependency Map

```
app/
├── main.py
│   └── imports: data_quality.routes, migration.routes, websocket.routes
├── data_quality/
│   ├── analyzer.py   ← sklearn (IsolationForest, TfidfVectorizer, StandardScaler)
│   │                    scipy (stats), numpy, pandas
│   ├── cleaner.py    ← sklearn (IsolationForest, DBSCAN, KNNImputer, IterativeImputer)
│   └── routes.py     ← analyzer, cleaner, database.models
├── migration/
│   ├── ai_translator.py  ← google.generativeai, difflib, re
│   ├── services.py       ← ai_translator, database.models
│   ├── enterprise_features.py  ← services, database.models
│   └── routes.py         ← services, enterprise_features
└── database/
    ├── config.py    ← sqlalchemy (create_engine, sessionmaker)
    └── models.py    ← sqlalchemy (Column, Integer, String, DateTime, ForeignKey)
```

---

## 11. External Dependencies

| Package | Version (from requirements.txt) | Role |
|---------|----------------------------------|------|
| fastapi | ≥0.104 | REST API framework |
| uvicorn | ≥0.24 | ASGI server |
| sqlalchemy | ≥2.0 | ORM / database abstraction |
| scikit-learn | ≥1.3 | ML models (IsolationForest, TF-IDF, etc.) |
| numpy | ≥1.24 | Numerical computation |
| pandas | ≥2.0 | DataFrame operations |
| scipy | ≥1.11 | Statistical tests, distributions |
| google-generativeai | ≥0.3 | Gemini API integration |
| psutil | ≥5.9 | Memory/CPU monitoring |
| faker | ≥20.0 | Synthetic dataset generation |
| matplotlib | ≥3.7 | Figure generation |
| seaborn | ≥0.13 | Statistical visualization |

---

*Report generated from static code analysis of the `research-experiments-ieee-access` branch.*
