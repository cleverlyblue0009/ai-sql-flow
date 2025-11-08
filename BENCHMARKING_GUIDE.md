# DataFlow AI Benchmarking Guide

## Overview

This guide explains how to run comprehensive benchmarks on DataFlow AI to collect real metrics and automatically update the research paper with actual performance data.

---

## What Gets Updated

The benchmarking system will replace **ALL [?] placeholders** in `RESEARCH_PAPER.md` with real metrics:

- ✅ **Overall accuracy percentages** (95.2% instead of [?]%)
- ✅ **Confidence scores** (92.7% instead of [?]%)
- ✅ **Processing times** (2.12s instead of [?]s)
- ✅ **Scalability metrics** (39,605 rows/sec instead of [?])
- ✅ **Complete tables** with all SQL translation performance data
- ✅ **Case studies** with actual timing and improvement metrics
- ✅ **Statistical significance** (p-values, confidence intervals)
- ✅ **Comparison metrics** vs baselines (SQLMorph, Great Expectations)

---

## Quick Start

### 1. Prerequisites

```bash
# Install Python dependencies (if not already installed)
pip install -r requirements.txt

# Additional dependencies for benchmark scripts
pip install aiohttp psutil scipy sqlparse openpyxl

# Optional: For PDF/DOCX generation
pip install python-docx reportlab
```

### 2. Start the Backend

```bash
# Terminal 1: Start FastAPI backend
uvicorn app.main:app --reload

# Wait for it to start (you should see "Application startup complete")
```

### 3. Run Complete Benchmarking Pipeline

```bash
# Terminal 2: Run the complete benchmarking suite
python scripts/run_complete_benchmarking.py
```

This single command will:
1. Generate test datasets
2. Generate SQL test cases
3. Run data quality benchmarks (calling real APIs)
4. Run SQL migration benchmarks (calling real APIs)
5. Run scalability benchmarks (testing various dataset sizes)
6. Process all results with statistical analysis
7. **Automatically update the research paper** with real metrics
8. Generate output files (MD, DOCX, PDF)

---

## Output Files

After running the complete pipeline, you'll find:

### Research Paper Outputs
- `results/research_paper_updated.md` - **Updated paper with all [?] filled**
- `results/research_paper_updated.docx` - Word document version
- `results/research_paper_updated.pdf` - PDF version
- `results/replacement_log.json` - Audit trail of all replacements

### Benchmark Results
- `results/data_quality/benchmark_results.json` - Data quality metrics
- `results/sql_migration/benchmark_results.json` - SQL translation metrics
- `results/scalability/benchmark_results.json` - Scalability metrics

### Processed Results
- `results/metrics_summary.json` - Aggregated metrics for paper
- `results/findings.md` - Narrative findings report
- `results/tables.json` - Formatted tables for insertion
- `results/statistical_analysis.json` - Statistical analysis data

### Test Data
- `test_data/excel/` - Generated test datasets
- `test_data/sql/` - Generated SQL test queries

---

## Running Individual Benchmarks

You can also run benchmarks individually:

### Data Quality Benchmark
```bash
python scripts/benchmark_data_quality.py
```

Tests data quality analysis by:
- Uploading test datasets to `/data-quality/upload`
- Running analysis via `/data-quality/analyze`
- Measuring precision, recall, F1 scores
- Recording processing time, memory, CPU usage

**Output:** `results/data_quality/benchmark_results.json`

### SQL Migration Benchmark
```bash
python scripts/benchmark_sql_migration.py
```

Tests SQL translation by:
- Translating queries across dialect pairs (PostgreSQL→Snowflake, MySQL→Snowflake, etc.)
- Validating translated SQL syntax
- Measuring success rate and confidence scores
- Comparing with SQLMorph baseline

**Output:** `results/sql_migration/benchmark_results.json`

### Scalability Benchmark
```bash
python scripts/benchmark_scalability.py
```

Tests scalability by:
- Testing with datasets from 1K to 1M rows
- Measuring processing time, memory, CPU
- Calculating throughput (rows/sec)
- Analyzing scaling characteristics

**Output:** `results/scalability/benchmark_results.json`

### Process Results
```bash
python scripts/process_benchmark_results.py
```

Processes all benchmark results:
- Calculates statistical measures (mean, std dev, CI)
- Performs significance tests (t-tests)
- Generates comparison metrics vs baselines
- Creates metrics summary for paper update

**Output:** `results/metrics_summary.json`, `results/findings.md`, `results/tables.json`

### Update Research Paper
```bash
python scripts/update_research_paper.py
```

Updates the research paper:
- Loads `RESEARCH_PAPER.md` template
- Loads `results/metrics_summary.json`
- Replaces all [?] placeholders with actual values
- Generates MD, DOCX, and PDF versions

**Output:** `results/research_paper_updated.md` (and DOCX, PDF)

---

## Benchmark Script Details

### 1. benchmark_data_quality.py

**What it tests:**
- Data quality analysis accuracy
- Issue detection (duplicates, outliers, missing values)
- Precision, recall, and F1 scores
- Processing performance

**API endpoints called:**
- `POST /data-quality/upload` - Upload dataset
- `POST /data-quality/analyze` - Start analysis
- `GET /data-quality/status/{job_id}` - Poll status
- `GET /data-quality/quality-summary/{profile_id}` - Get results

**Metrics collected:**
- Overall quality scores (before/after cleaning)
- Detection accuracy (precision, recall, F1)
- False positive/negative rates
- Processing time per 1000 rows
- Memory and CPU usage

**Iterations:** Runs 3 times per dataset and averages results

### 2. benchmark_sql_migration.py

**What it tests:**
- SQL translation across 5 dialect pairs
- Translation success rates
- Confidence scoring accuracy
- Syntax validation

**API endpoints called:**
- `POST /migration/translate-sql` - Start translation
- `GET /migration/jobs/{job_id}/status` - Poll status

**Metrics collected:**
- Success rate per dialect pair
- Average confidence scores
- Processing time per query
- Semantic similarity scores
- Validation warnings

**Dialect pairs tested:**
- PostgreSQL → Snowflake
- MySQL → Snowflake
- Oracle → Snowflake
- SQL Server → Snowflake
- BigQuery → Snowflake

**Complexity levels:**
- Basic queries
- Intermediate queries
- Advanced queries
- Dialect-specific queries

### 3. benchmark_scalability.py

**What it tests:**
- Performance with increasing dataset sizes
- Memory scaling characteristics
- CPU utilization patterns
- Throughput measurements

**Dataset sizes tested:**
- 1,000 rows
- 10,000 rows
- 100,000 rows
- 1,000,000 rows

**Metrics collected:**
- Processing time (seconds)
- Memory usage (MB)
- CPU usage (%)
- Throughput (rows/second)
- Scaling characteristics (linear/sub-linear/super-linear)

### 4. process_benchmark_results.py

**What it does:**
- Loads all benchmark results
- Calculates statistical measures
- Performs significance tests
- Generates comparison metrics

**Statistical analysis:**
- Mean, standard deviation
- 95% confidence intervals
- T-tests for significance (p-values)
- Comparison with baselines

**Outputs:**
- `metrics_summary.json` - For paper update
- `findings.md` - Narrative report
- `tables.json` - Formatted tables
- `statistical_analysis.json` - Detailed stats

### 5. update_research_paper.py

**What it does:**
- Parses research paper template
- Identifies all [?] placeholders
- Replaces with actual metrics
- Generates multiple output formats

**Replacement strategy:**
- Abstract metrics
- Contribution metrics
- Table data (all 3 tables)
- Case study results
- Discussion metrics
- Performance analysis
- Metadata (dates, word count)

**Outputs:**
- Markdown (.md)
- Word document (.docx)
- PDF (.pdf)
- Replacement log (.json)

---

## Troubleshooting

### Backend Not Running
```
Error: Cannot connect to API at http://localhost:8000
```

**Solution:** Start the backend in a separate terminal:
```bash
uvicorn app.main:app --reload
```

### No Test Data Found
```
Warning: No test files found in test_data/excel/
```

**Solution:** Generate test data first:
```bash
python scripts/generate_test_datasets.py
python scripts/generate_sql_test_cases.py
```

### Missing Python Packages
```
ModuleNotFoundError: No module named 'aiohttp'
```

**Solution:** Install required packages:
```bash
pip install aiohttp psutil scipy sqlparse openpyxl
```

### Benchmark Timeout
```
Error: Job timed out after 300 seconds
```

**Solution:** 
- Large datasets may take longer
- Increase timeout in script configuration
- Or test with smaller datasets first

### Memory Issues
```
MemoryError during large dataset processing
```

**Solution:**
- Reduce `TEST_SIZES` in `benchmark_scalability.py`
- Close other memory-intensive applications
- Test with smaller datasets

---

## Configuration

### Adjusting Test Parameters

Edit the constants at the top of each script:

**benchmark_data_quality.py:**
```python
NUM_ITERATIONS = 3  # Number of times to run each test
API_BASE_URL = "http://localhost:8000"  # Backend URL
```

**benchmark_sql_migration.py:**
```python
NUM_ITERATIONS = 3
DIALECT_PAIRS = [...]  # Which dialect pairs to test
COMPLEXITY_LEVELS = [...]  # Which complexity levels
```

**benchmark_scalability.py:**
```python
TEST_SIZES = [1000, 10000, 100000, 1000000]  # Dataset sizes
NUM_COLUMNS = 15  # Number of columns per dataset
```

### Custom Metrics

To add custom metrics to the paper:

1. Collect metrics in your benchmark script
2. Add to results JSON
3. Update `update_research_paper.py` to replace corresponding [?]
4. Re-run the update script

---

## Understanding the Output

### Metrics Summary Structure

```json
{
  "data_quality": {
    "overall_accuracy": 95.2,
    "precision": {"mean": 0.945, "std": 0.021, "ci_95": [0.910, 0.980]},
    "recall": {"mean": 0.955, "std": 0.018, "ci_95": [0.922, 0.988]},
    "f1_score": {"mean": 0.950, "std": 0.019, "ci_95": [0.916, 0.984]},
    "p_value": 0.0001,
    "significance": "highly_significant"
  },
  "sql_migration": {
    "overall_success_rate": 94.3,
    "avg_confidence": 92.7,
    "improvement_over_baseline_percent": 20.6
  },
  "scalability": {
    "avg_throughput_rows_per_second": 39605,
    "max_dataset_size_rows": 1000000,
    "scaling_characteristic": "linear"
  }
}
```

### Replacement Log

The replacement log shows every [?] that was replaced:

```json
{
  "total_placeholders_found": 127,
  "total_placeholders_replaced": 127,
  "placeholders_remaining": 0,
  "replacements": [
    {
      "placeholder": "[?]% accuracy",
      "replaced_with": "95.2%",
      "section": "Abstract",
      "original_value": 95.2
    }
  ],
  "status": "COMPLETE - All placeholders filled"
}
```

---

## Expected Runtime

| Step | Duration | Notes |
|------|----------|-------|
| Generate Test Data | 1-2 min | Creates datasets |
| Generate SQL Cases | 30 sec | Creates SQL files |
| Data Quality Benchmark | 5-10 min | Depends on dataset sizes |
| SQL Migration Benchmark | 3-5 min | Depends on query count |
| Scalability Benchmark | 10-20 min | Tests multiple sizes |
| Process Results | 10 sec | Statistical analysis |
| Update Paper | 5 sec | Replace placeholders |
| **Total** | **20-40 min** | Full pipeline |

---

## Next Steps After Benchmarking

1. **Review the updated paper:** `results/research_paper_updated.md`
2. **Check metrics summary:** `results/metrics_summary.json`
3. **Read findings report:** `results/findings.md`
4. **Verify all tables are filled:** Search for any remaining [?] in the paper
5. **Compare with baseline tools:** Review comparison metrics
6. **Share results:** The paper is now publication-ready!

---

## Advanced Usage

### Custom Baseline Comparisons

Edit `process_benchmark_results.py` to compare with different baselines:

```python
# Change baseline values
baseline_f1 = 0.85  # Great Expectations baseline
baseline_success_rate = 0.782  # SQLMorph baseline
```

### Testing Specific Dialects Only

Edit `benchmark_sql_migration.py`:

```python
DIALECT_PAIRS = [
    ("MySQL", "Snowflake"),  # Only test this pair
]
```

### Generating Only Specific Formats

Edit `update_research_paper.py` to skip DOCX/PDF:

```python
# Comment out DOCX/PDF generation sections
# if you only need Markdown
```

---

## Contributing

To add new benchmarks:

1. Create a new benchmark script in `scripts/`
2. Follow the existing pattern (load data, call APIs, measure metrics)
3. Save results to `results/your_benchmark/`
4. Update `process_benchmark_results.py` to include your metrics
5. Update `update_research_paper.py` to replace relevant [?] placeholders
6. Update `run_complete_benchmarking.py` to include your script

---

## Support

For issues or questions:
1. Check the logs in `results/benchmarking_log.txt`
2. Review error messages in the console output
3. Ensure backend is running and accessible
4. Verify all dependencies are installed
5. Check that test data was generated successfully

---

## Summary

The benchmarking system provides:
- ✅ Automated end-to-end testing of DataFlow AI
- ✅ Real metrics collection from actual API calls
- ✅ Statistical analysis with confidence intervals
- ✅ Automatic research paper update
- ✅ Multiple output formats (MD, DOCX, PDF)
- ✅ Comprehensive audit trail

**Result:** A publication-ready research paper with all [?] placeholders filled with actual, measured performance data!
