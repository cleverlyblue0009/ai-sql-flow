# DataFlow AI: Automated Research Data Collection & Benchmarking System

## Overview

This system provides a comprehensive automated benchmarking infrastructure for the DataFlow AI platform. It generates realistic test data, runs extensive benchmarks, collects metrics, performs statistical analysis, and automatically updates the research paper with actual measured values.

## System Architecture

```
scripts/
├── generate_test_datasets.py       # Generates 5 complex Excel datasets with quality issues
├── generate_sql_test_cases.py      # Generates 100+ SQL queries across 5 dialects
├── benchmark_data_quality.py       # Benchmarks data quality analysis (TO BE IMPLEMENTED)
├── benchmark_sql_migration.py      # Benchmarks SQL translation (TO BE IMPLEMENTED)
├── benchmark_scalability.py        # Tests performance at scale (TO BE IMPLEMENTED)
├── process_benchmark_results.py    # Statistical analysis (TO BE IMPLEMENTED)
├── update_research_paper.py        # Auto-updates paper with metrics (TO BE IMPLEMENTED)
└── run_complete_benchmarking.py    # Master orchestration script

test_data/
├── excel/                          # Generated test datasets
│   ├── ecommerce_customers_300k.xlsx
│   ├── healthcare_patients_500k.xlsx
│   ├── financial_transactions_1m.xlsx
│   ├── iot_sensor_data_2m.xlsx
│   ├── mixed_quality_100k.xlsx
│   └── *_metadata.json             # Metadata for each dataset
└── sql/                            # Generated SQL test queries
    ├── postgresql/
    ├── mysql/
    ├── sqlserver/
    ├── oracle/
    └── snowflake/

results/
├── data_quality/                   # Data quality benchmark results
├── sql_migration/                  # SQL translation benchmark results
├── scalability/                    # Scalability test results
├── comparison/                     # Baseline comparisons
├── visualizations/                 # Generated charts and graphs
└── research_paper_updated.md       # Auto-updated research paper
```

## Generated Test Datasets

### 1. E-Commerce Customer Database (300,000 rows)
**Purpose**: Test email-name matching, duplicate detection, format standardization

**Columns**: customer_id, email, first_name, last_name, phone, address, city, state, zip, signup_date, last_purchase_date, purchase_count, loyalty_status, country, income_bracket

**Injected Issues**:
- 12% NULL values across various columns
- 847 exact duplicate records
- 2,341 fuzzy duplicates (variations in formatting)
- 156 email-name mismatches (semantic inconsistencies)
- 3,421 phone format inconsistencies
- 892 invalid email formats
- 2,156 impossible dates
- 1,234 outliers in purchase counts
- 445 invalid zip codes

**Expected Quality Score**: ~85.2% (before cleaning)

### 2. Healthcare Patient Records (500,000 rows)
**Purpose**: Test HIPAA-sensitive data handling, semantic validation

**Columns**: patient_id, ssn, first_name, last_name, dob, gender, email, phone, address, city, state, zip, insurance_provider, policy_number, blood_type, height_cm, weight_kg, last_visit_date, diagnosis_codes, allergies, medications

**Injected Issues**:
- 8% NULL values
- 1,247 exact duplicates (SSN/email matches)
- 3,892 fuzzy duplicates
- 892 semantic mismatches (gender vs name inconsistencies)
- 2,156 impossible height/weight values
- 5,234 age outliers (impossible birth years)
- 1,894 invalid phone/email formats
- 623 inconsistent gender representations

**Expected Quality Score**: ~83.6% (before cleaning)

### 3. Financial Transaction Records (1,000,000 rows)
**Purpose**: Test high-volume processing, outlier detection

**Columns**: transaction_id, account_id, amount, currency, transaction_date, merchant_name, category, payment_method, status, fraud_flag, settlement_date, description

**Injected Issues**:
- 2% NULL values
- 234 exact duplicates
- 4,567 fuzzy duplicates (same transaction, different IDs)
- 12,345 amount outliers
- 2,234 impossible dates (settlement before transaction)
- 5,678 invalid currency codes
- 3,456 inconsistent merchant names (Starbucks/STARBUCKS/starbucks)
- 892 inconsistent status values

**Expected Quality Score**: ~88.6% (before cleaning)

### 4. Sensor IoT Data (2,000,000 rows)
**Purpose**: Test time-series data, massive dataset handling

**Columns**: sensor_id, timestamp, temperature_celsius, humidity_percent, pressure_mb, air_quality_index, location, device_status, battery_level, signal_strength

**Injected Issues**:
- 5% NULL values (sensor failures)
- 892 exact duplicates
- 3,456 temperature outliers (-273°C, 150°C)
- 2,341 humidity outliers (>100%, negative)
- 4,567 pressure outliers
- 1,234 inconsistent sensor IDs
- 678 battery levels >100%

**Expected Quality Score**: ~86.8% (before cleaning)

### 5. Mixed Quality Dataset (100,000 rows)
**Purpose**: Quick testing with all issue types

**Columns**: id, name, email, phone, age, salary, hire_date, status

**Expected Quality Score**: ~76.4% (worst case for testing)

## Generated SQL Test Cases

### Query Organization

**By Complexity Level**:
- **Level 1: Basic** (20 queries per dialect) - Simple SELECT, INSERT, UPDATE, basic JOINs
- **Level 2: Intermediate** (30 queries per dialect) - Subqueries, CTEs, window functions, aggregations
- **Level 3: Advanced** (25 queries per dialect) - Recursive CTEs, complex window functions, nested queries
- **Level 4: Dialect-Specific** (15 queries per dialect) - Vendor-specific features

**By Dialect**:
- PostgreSQL (90+ queries)
- MySQL (50+ queries)
- SQL Server (30+ queries)
- Oracle (30+ queries)
- Snowflake (30+ queries)

**Total**: 100+ realistic SQL queries with known transformation requirements

### Example Query Categories

1. **Data Type Conversions**: SERIAL → INT AUTOINCREMENT, JSONB → VARIANT
2. **Function Mappings**: NOW() → CURRENT_TIMESTAMP(), IFNULL() → COALESCE()
3. **Syntax Differences**: LIMIT/OFFSET → TOP, backticks → double quotes
4. **Dialect-Specific Features**: Array operations, JSON handling, full-text search

## Running the System

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure backend is running
uvicorn app.main:app --reload
```

### Option 1: Run Complete Pipeline

```bash
python scripts/run_complete_benchmarking.py
```

This executes all 8 steps in sequence:
1. Generate test datasets
2. Generate SQL test cases
3. Run data quality benchmarks
4. Run SQL migration benchmarks
5. Run scalability tests
6. Process benchmark results
7. Update research paper
8. Generate reports

### Option 2: Run Individual Scripts

```bash
# Step 1: Generate test data
python scripts/generate_test_datasets.py

# Step 2: Generate SQL queries
python scripts/generate_sql_test_cases.py

# Step 3-7: Run benchmarks (requires backend running)
python scripts/benchmark_data_quality.py
python scripts/benchmark_sql_migration.py
python scripts/benchmark_scalability.py

# Step 8: Process results
python scripts/process_benchmark_results.py
python scripts/update_research_paper.py
```

## Implementation Status

### ✅ Completed
- ✅ Directory structure created
- ✅ `generate_test_datasets.py` - Fully implemented
- ✅ `generate_sql_test_cases.py` - Core implementation complete
- ✅ `run_complete_benchmarking.py` - Orchestration framework complete
- ✅ Updated `requirements.txt` with all dependencies

### 🚧 To Be Implemented

The following scripts need to be implemented to call actual DataFlow AI APIs and collect real metrics:

#### `benchmark_data_quality.py`
**Purpose**: Test data quality analysis on all generated datasets

**Implementation Requirements**:
1. Load each Excel dataset from `test_data/excel/`
2. Call `/data-quality/upload` API endpoint for each
3. Call `/data-quality/analyze` API endpoint
4. Poll `/data-quality/status/{job_id}` until complete
5. Retrieve quality metrics via `/data-quality/quality-summary/{profile_id}`
6. Compare metrics against expected values in metadata
7. Calculate accuracy, precision, recall, F1-score
8. Measure processing time, memory usage, CPU usage
9. Save results to `results/data_quality/benchmark_results.json`

**Expected Output**:
```json
{
  "dataset_name": "ecommerce_customers_300k",
  "before_cleaning": {
    "completeness_percent": 88.3,
    "validity_percent": 82.1,
    "overall_quality_score": 85.52
  },
  "after_cleaning": {
    "overall_quality_score": 99.18
  },
  "improvements": {
    "overall_quality_improvement_percent": 13.66
  },
  "performance": {
    "processing_time_seconds": 12.34,
    "memory_usage_mb": 542.1
  },
  "detection_accuracy": {
    "precision": 0.94,
    "recall": 0.96,
    "f1_score": 0.95
  }
}
```

#### `benchmark_sql_migration.py`
**Purpose**: Test SQL translation across all dialect pairs

**Implementation Requirements**:
1. Load SQL queries from `test_data/sql/`
2. For each source dialect → target dialect pair:
   - Call `/migration/translate-sql` API endpoint
   - Record confidence score
   - Measure processing time
   - Validate translated SQL syntax using sqlparse
   - Calculate semantic similarity score
3. Compare against rule-based baseline (SQLMorph)
4. Calculate success rate by complexity level
5. Save results to `results/sql_migration/benchmark_results.json`

**Expected Output**:
```json
{
  "total_translations_tested": 562,
  "overall_success_rate": 0.943,
  "overall_average_confidence": 0.927,
  "by_dialect_pair": {
    "PostgreSQL_to_Snowflake": {
      "success_rate": 0.967,
      "avg_confidence": 0.945
    }
  },
  "by_complexity_level": {
    "basic": {"success_rate": 0.99},
    "advanced": {"success_rate": 0.92}
  }
}
```

#### `benchmark_scalability.py`
**Purpose**: Test performance with varying dataset sizes

**Implementation Requirements**:
1. Generate datasets of varying sizes: 1K, 10K, 100K, 1M, 10M rows
2. For each size:
   - Upload to `/data-quality/upload`
   - Start analysis via `/data-quality/analyze`
   - Measure: processing time, memory usage, CPU %, throughput
3. Generate scalability table showing linear/sub-linear scaling
4. Save results to `results/scalability/benchmark_results.json`

**Expected Output**:
```json
{
  "scalability_tests": [
    {
      "dataset_size_rows": 1000,
      "processing_time_seconds": 0.12,
      "memory_usage_mb": 45,
      "throughput_rows_per_second": 8333
    },
    {
      "dataset_size_rows": 1000000,
      "processing_time_seconds": 18.45,
      "memory_usage_mb": 1245,
      "throughput_rows_per_second": 54222
    }
  ]
}
```

#### `process_benchmark_results.py`
**Purpose**: Aggregate results and perform statistical analysis

**Implementation Requirements**:
1. Load all benchmark JSON files from `results/`
2. Calculate summary statistics:
   - Mean, standard deviation, min, max for all metrics
   - 95% confidence intervals
   - P-values for significance testing (t-tests, ANOVA)
3. Generate comparison tables (DataFlow AI vs baselines)
4. Create visualization data (charts_data.json)
5. Write findings narrative (findings.md)
6. Output `results/metrics_summary.json`

**Expected Output**:
```json
{
  "data_quality": {
    "overall_accuracy": 95.2,
    "precision": 0.94,
    "recall": 0.96,
    "f1_score": 0.95,
    "confidence_interval_95": [94.8, 95.6],
    "p_value": 0.0001
  },
  "sql_migration": {
    "overall_success_rate": 94.3,
    "avg_confidence": 92.7,
    "improvement_over_baseline": 16.1
  }
}
```

#### `update_research_paper.py`
**Purpose**: Replace [?] placeholders in research paper with actual metrics

**Implementation Requirements**:
1. Load `RESEARCH_PAPER.md`
2. Load `results/metrics_summary.json`
3. Find all [?] placeholders in the paper
4. Replace with corresponding metrics:
   - Abstract: overall accuracy, confidence, processing time
   - Table 1: SQL translation success rates by dialect pair
   - Table 2: Data quality detection precision/recall
   - Table 3: Scalability measurements
   - Case studies: actual confidence scores and processing times
5. Save updated paper to `results/research_paper_updated.md`
6. Generate .docx and .pdf versions using python-docx and reportlab
7. Create replacement log showing all changes made

**Expected Output**:
- `results/research_paper_updated.md`
- `results/research_paper_updated.docx`
- `results/research_paper_updated.pdf`
- `results/replacement_log.json`

## Metrics to Collect

### Data Quality Metrics
- **Completeness**: % of non-null values
- **Validity**: % of values matching expected types/formats
- **Uniqueness**: % of unique records (1 - duplicate %)
- **Consistency**: % of values following consistent formats
- **Accuracy**: % of values without outliers/anomalies
- **Overall Quality Score**: Weighted average of above

### SQL Translation Metrics
- **Success Rate**: % of queries translated without errors
- **Confidence Score**: AI-reported confidence (0-1)
- **Processing Time**: Seconds to translate
- **Semantic Similarity**: Token overlap between source and target
- **Validation Status**: Syntax valid vs invalid

### Performance Metrics
- **Processing Time**: Wall-clock time (seconds)
- **Memory Usage**: Peak memory consumption (MB)
- **CPU Usage**: Average CPU utilization (%)
- **Throughput**: Rows processed per second
- **Latency**: Response time for API calls (ms)

### Comparison Metrics
- **vs Great Expectations** (data quality): False positive reduction, accuracy improvement
- **vs SQLMorph** (SQL translation): Success rate improvement, confidence advantage
- **Statistical Significance**: P-values, confidence intervals

## Expected Research Paper Updates

### Abstract
**Before**: "...demonstrates [?]% accuracy, translates SQL with [?]% confidence..."
**After**: "...demonstrates 95.2% accuracy, translates SQL with 92.7% confidence..."

### Table 1: SQL Translation Performance
All [?] filled with actual success rates, confidence scores, processing times

### Table 2: Data Quality Detection
All [?] filled with precision, recall, F1-score for each issue type

### Table 3: Scalability
All [?] filled with processing times and throughput for each dataset size

### Case Studies
All [?] filled with actual confidence scores, processing times, validation results

## Baseline Comparisons

The system compares DataFlow AI against:

1. **Great Expectations** (data quality)
   - Industry-standard rule-based quality tool
   - Compare: false positive rates, detection accuracy, processing time

2. **SQLMorph** (SQL translation)
   - Academic rule-based translation system
   - Compare: success rates, handling of complex queries

## Validation & Quality Assurance

### Test Data Validation
- All Excel files load correctly (tested with pandas)
- All SQL queries parse correctly (tested with sqlparse)
- Injected issues are measurable and reproducible
- Ground truth metrics calculated correctly

### Benchmark Accuracy
- Results reproducible with RANDOM_SEED=42
- No API errors or timeouts during collection
- All metrics calculated correctly
- Statistical tests properly executed

### Output Validation
- All JSON is valid and parseable
- All markdown renders correctly
- No [?] placeholders remain (except where data unavailable)
- Tables formatted correctly

## Usage Examples

### Generate Only Test Data
```bash
python scripts/generate_test_datasets.py
```

Output:
```
Generating E-Commerce dataset with 300000 rows...
Generating Healthcare dataset with 500000 rows...
Generating Financial dataset with 1000000 rows...
Generating IoT dataset with 2000000 rows...
Generating Mixed Quality dataset with 100000 rows...

Total Datasets: 5
Total Rows: 4,000,000
Total Size: 3,250.45 MB
Output Directory: /workspace/test_data/excel
```

### Generate Only SQL Queries
```bash
python scripts/generate_sql_test_cases.py
```

Output:
```
Generating postgresql queries...
  - basic: 20 queries
  - intermediate: 30 queries
  - advanced: 25 queries
  - dialect_specific: 15 queries

Total Queries: 230+
Output Directory: /workspace/test_data/sql
```

### Run Complete Pipeline
```bash
python scripts/run_complete_benchmarking.py
```

This will execute all steps and generate a comprehensive report.

## Troubleshooting

### Backend Not Running
**Error**: Connection refused when calling APIs
**Solution**: Start backend with `uvicorn app.main:app --reload`

### Out of Memory
**Error**: MemoryError when processing large datasets
**Solution**: Reduce dataset sizes or increase system RAM

### API Timeout
**Error**: Request timeout for long-running operations
**Solution**: Increase timeout values in benchmark scripts

### Missing Dependencies
**Error**: ModuleNotFoundError
**Solution**: `pip install -r requirements.txt`

## Future Enhancements

1. **Distributed Processing**: Integrate Apache Spark for 100M+ row datasets
2. **Real-Time Dashboard**: Live visualization of benchmark progress
3. **Automated Scheduling**: Cron jobs for nightly benchmark runs
4. **Historical Tracking**: Track metrics over time to measure improvements
5. **Baseline Updates**: Regularly update baseline comparisons
6. **GPU Acceleration**: Leverage CUDA for ML model inference
7. **Cloud Integration**: Run benchmarks on AWS/Azure/GCP for scalability testing

## Contributing

To add new benchmarks:

1. Add test data generator in `generate_test_datasets.py`
2. Add SQL queries in `generate_sql_test_cases.py`
3. Implement benchmark script following existing patterns
4. Update `run_complete_benchmarking.py` to include new step
5. Update this README with new metrics

## License

This benchmarking system is part of the DataFlow AI project.

## Contact

For questions or issues, please open a GitHub issue or contact the development team.

---

**Last Updated**: 2025-01-08
**Version**: 1.0.0
**Status**: Core infrastructure complete, API integration pending
