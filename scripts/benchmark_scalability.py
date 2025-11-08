#!/usr/bin/env python3
"""
Scalability Benchmarking Script

This script tests DataFlow AI's scalability by:
1. Generating datasets of varying sizes (1K to 10M rows)
2. Uploading and analyzing each dataset
3. Measuring processing time, memory usage, and CPU usage
4. Calculating throughput (rows per second)
5. Analyzing scaling characteristics (linear vs exponential)
"""

import sys
import json
import time
import psutil
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import logging
import asyncio
import aiohttp
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000"
RESULTS_DIR = Path("results/scalability")
TEST_SIZES = [1000, 10000, 100000, 1000000]  # Skip 10M for speed
NUM_COLUMNS = 15


class ScalabilityBenchmark:
    """Benchmark scalability with varying dataset sizes"""
    
    def __init__(self, api_base_url: str = API_BASE_URL):
        self.api_base_url = api_base_url
        self.process = psutil.Process()
        
    def generate_test_dataset(self, num_rows: int, num_cols: int = NUM_COLUMNS) -> pd.DataFrame:
        """Generate a test dataset of specified size"""
        
        logger.info(f"Generating dataset: {num_rows:,} rows × {num_cols} columns")
        
        data = {
            'id': range(1, num_rows + 1),
            'name': [f"Customer_{i}" for i in range(num_rows)],
            'email': [f"customer{i}@example.com" for i in range(num_rows)],
            'age': np.random.randint(18, 80, num_rows),
            'salary': np.random.uniform(30000, 150000, num_rows),
            'purchase_amount': np.random.uniform(10, 5000, num_rows),
            'account_balance': np.random.uniform(-1000, 50000, num_rows),
            'credit_score': np.random.randint(300, 850, num_rows),
            'num_purchases': np.random.randint(0, 100, num_rows),
            'created_date': pd.date_range('2020-01-01', periods=num_rows, freq='1min')[:num_rows],
        }
        
        # Add additional columns to reach num_cols
        for i in range(10, num_cols):
            data[f'metric_{i}'] = np.random.uniform(0, 1000, num_rows)
        
        df = pd.DataFrame(data)
        
        # Introduce some data quality issues
        # Add missing values (5%)
        for col in ['age', 'salary', 'purchase_amount']:
            mask = np.random.random(num_rows) < 0.05
            df.loc[mask, col] = np.nan
        
        # Add duplicates (2%)
        num_duplicates = int(num_rows * 0.02)
        if num_duplicates > 0:
            duplicate_indices = np.random.choice(num_rows, num_duplicates)
            df = pd.concat([df, df.iloc[duplicate_indices]], ignore_index=True)
        
        # Add outliers (1%)
        num_outliers = int(num_rows * 0.01)
        outlier_indices = np.random.choice(len(df), num_outliers)
        df.loc[outlier_indices, 'salary'] = np.random.uniform(500000, 1000000, num_outliers)
        
        logger.info(f"✓ Generated dataset: {len(df):,} rows (including duplicates)")
        
        return df
    
    async def upload_and_analyze(
        self,
        df: pd.DataFrame,
        session: aiohttp.ClientSession
    ) -> Dict[str, Any]:
        """Upload dataset and analyze, measuring performance"""
        
        dataset_size = len(df)
        logger.info(f"\n{'='*60}\nBenchmarking dataset: {dataset_size:,} rows\n{'='*60}")
        
        # Convert to Excel in memory
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        excel_data = excel_buffer.getvalue()
        
        # Start monitoring
        start_time = time.time()
        start_cpu = psutil.cpu_percent(interval=1)
        start_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
        
        try:
            # 1. Upload file
            data = aiohttp.FormData()
            data.add_field(
                'file',
                excel_buffer,
                filename=f'test_dataset_{dataset_size}.xlsx',
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            async with session.post(
                f"{self.api_base_url}/data-quality/upload",
                data=data,
                timeout=aiohttp.ClientTimeout(total=600)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Upload failed: {error_text}")
                
                upload_result = await response.json()
                profile_id = upload_result.get('data_profile_id')
            
            logger.info(f"  ✓ Upload complete (profile_id: {profile_id})")
            
            # Wait for initial analysis
            await asyncio.sleep(3)
            
            # 2. Start comprehensive analysis
            async with session.post(
                f"{self.api_base_url}/data-quality/analyze",
                json={
                    "data_profile_id": profile_id,
                    "analysis_types": ["all"],
                    "ai_enabled": True,
                    "sample_size": None
                },
                timeout=aiohttp.ClientTimeout(total=600)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Analysis start failed: {error_text}")
                
                analysis_result = await response.json()
                job_id = analysis_result.get('job_id')
            
            logger.info(f"  ✓ Analysis started (job_id: {job_id})")
            
            # 3. Poll until complete
            max_wait = 600  # 10 minutes
            poll_start = time.time()
            
            while time.time() - poll_start < max_wait:
                async with session.get(
                    f"{self.api_base_url}/data-quality/status/{job_id}",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        status_result = await response.json()
                        status = status_result.get('status')
                        
                        if status == 'completed':
                            logger.info(f"  ✓ Analysis complete")
                            break
                        elif status == 'failed':
                            error_msg = status_result.get('error_message', 'Unknown error')
                            raise Exception(f"Analysis failed: {error_msg}")
                
                await asyncio.sleep(2)
            else:
                raise Exception(f"Analysis timed out after {max_wait} seconds")
            
            # End monitoring
            end_time = time.time()
            end_cpu = psutil.cpu_percent(interval=1)
            end_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
            
            processing_time = end_time - start_time
            avg_cpu = (start_cpu + end_cpu) / 2
            memory_usage = end_memory - start_memory
            throughput = dataset_size / processing_time
            
            result = {
                "dataset_size_rows": dataset_size,
                "columns": len(df.columns),
                "processing_time_seconds": round(processing_time, 2),
                "memory_usage_mb": round(memory_usage, 2),
                "cpu_usage_percent": round(avg_cpu, 2),
                "throughput_rows_per_second": round(throughput, 0)
            }
            
            logger.info(f"  Processing Time: {processing_time:.2f}s")
            logger.info(f"  Memory Usage: {memory_usage:.2f} MB")
            logger.info(f"  CPU Usage: {avg_cpu:.1f}%")
            logger.info(f"  Throughput: {throughput:,.0f} rows/sec")
            
            return result
            
        except Exception as e:
            logger.error(f"✗ Benchmark failed: {str(e)}")
            return {
                "dataset_size_rows": dataset_size,
                "columns": len(df.columns),
                "error": str(e),
                "processing_time_seconds": time.time() - start_time
            }
    
    def analyze_scaling(self, results: List[Dict[str, Any]]) -> Dict[str, str]:
        """Analyze scaling characteristics"""
        
        # Extract successful results
        valid_results = [r for r in results if 'error' not in r]
        
        if len(valid_results) < 2:
            return {
                "memory_scaling": "insufficient_data",
                "time_scaling": "insufficient_data",
                "throughput_improvement": "insufficient_data"
            }
        
        # Analyze memory scaling
        sizes = [r['dataset_size_rows'] for r in valid_results]
        memories = [r['memory_usage_mb'] for r in valid_results]
        
        # Simple linear regression to check if memory grows linearly
        size_ratio = sizes[-1] / sizes[0] if sizes[0] > 0 else 1
        memory_ratio = memories[-1] / memories[0] if memories[0] > 0 else 1
        
        if memory_ratio < size_ratio * 0.7:
            memory_scaling = "sub_linear"
        elif memory_ratio > size_ratio * 1.3:
            memory_scaling = "super_linear"
        else:
            memory_scaling = "linear"
        
        # Analyze time scaling
        times = [r['processing_time_seconds'] for r in valid_results]
        time_ratio = times[-1] / times[0] if times[0] > 0 else 1
        
        if time_ratio < size_ratio * 0.8:
            time_scaling = "sub_linear"
        elif time_ratio > size_ratio * 1.2:
            time_scaling = "super_linear"
        else:
            time_scaling = "linear"
        
        # Analyze throughput
        throughputs = [r['throughput_rows_per_second'] for r in valid_results]
        if throughputs[-1] > throughputs[0]:
            throughput_improvement = "improving_with_size"
        elif throughputs[-1] < throughputs[0] * 0.8:
            throughput_improvement = "degrading_with_size"
        else:
            throughput_improvement = "stable"
        
        return {
            "memory_scaling": memory_scaling,
            "time_scaling": time_scaling,
            "throughput_improvement": throughput_improvement
        }
    
    async def run_benchmarks(self) -> Dict[str, Any]:
        """Run all scalability benchmarks"""
        
        logger.info(f"\n{'='*80}\nStarting Scalability Benchmarking\n{'='*80}\n")
        
        # Create aiohttp session
        async with aiohttp.ClientSession() as session:
            # Test API connectivity
            try:
                async with session.get(f"{self.api_base_url}/health", timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        logger.warning(f"API returned status {response.status}")
            except Exception as e:
                logger.error(f"✗ Cannot connect to API at {self.api_base_url}")
                logger.error(f"  Error: {str(e)}")
                logger.error("  Please start the backend with: uvicorn app.main:app --reload")
                return {"error": "API not accessible"}
            
            logger.info("✓ API is accessible")
            
            # Run benchmarks for each size
            results = []
            
            for size in TEST_SIZES:
                logger.info(f"\n{'='*80}\nTesting dataset size: {size:,} rows\n{'='*80}")
                
                # Generate dataset
                df = self.generate_test_dataset(size, NUM_COLUMNS)
                
                # Run benchmark
                result = await self.upload_and_analyze(df, session)
                results.append(result)
                
                # Small delay between tests
                await asyncio.sleep(5)
            
            # Analyze scaling characteristics
            scaling_analysis = self.analyze_scaling(results)
            
            # Compile final results
            final_results = {
                "benchmark_timestamp": datetime.now().isoformat(),
                "api_base_url": self.api_base_url,
                "test_sizes": TEST_SIZES,
                "num_columns": NUM_COLUMNS,
                "scalability_tests": results,
                "scaling_analysis": scaling_analysis
            }
            
            # Save results
            RESULTS_DIR.mkdir(parents=True, exist_ok=True)
            results_file = RESULTS_DIR / "benchmark_results.json"
            
            with open(results_file, 'w') as f:
                json.dump(final_results, f, indent=2)
            
            logger.info(f"\n{'='*80}")
            logger.info(f"✓ Scalability Benchmarking Complete!")
            logger.info(f"  Results saved to: {results_file}")
            logger.info(f"  Dataset sizes tested: {', '.join(f'{s:,}' for s in TEST_SIZES)}")
            logger.info(f"  Memory scaling: {scaling_analysis['memory_scaling']}")
            logger.info(f"  Time scaling: {scaling_analysis['time_scaling']}")
            logger.info(f"  Throughput: {scaling_analysis['throughput_improvement']}")
            logger.info(f"{'='*80}\n")
            
            return final_results


async def main():
    """Main entry point"""
    
    benchmark = ScalabilityBenchmark()
    results = await benchmark.run_benchmarks()
    
    if "error" not in results:
        return 0
    else:
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n\nBenchmarking interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nFatal error: {str(e)}", exc_info=True)
        sys.exit(1)
