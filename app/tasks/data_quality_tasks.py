from celery import Celery
import pandas as pd
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import logging
import traceback

from ..database.config import settings, SessionLocal
from ..database.models import DataProfile, Job, JobStatus
from ..data_quality.analyzer import DataQualityAnalyzer
from ..data_quality.cleaner import DataCleaner
from ..utils.file_storage import FileStorageManager

# Initialize Celery
celery_app = Celery(
    "ai_data_platform",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

logger = logging.getLogger(__name__)

# Initialize components
analyzer = DataQualityAnalyzer()
cleaner = DataCleaner()
storage_manager = FileStorageManager()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, will be closed in task


def update_job_progress(job_id: str, progress: float, current_step: str, total_steps: int = None):
    """Update job progress in database"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if job:
            job.progress_percentage = progress
            job.current_step = current_step
            if total_steps:
                job.total_steps = total_steps
            if job.status == JobStatus.PENDING:
                job.status = JobStatus.RUNNING
                job.started_at = datetime.utcnow()
            db.commit()
    except Exception as e:
        logger.error(f"Failed to update job progress: {str(e)}")
    finally:
        db.close()


def mark_job_completed(job_id: str, result: Dict[str, Any]):
    """Mark job as completed with result"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if job:
            job.status = JobStatus.COMPLETED
            job.progress_percentage = 100.0
            job.completed_at = datetime.utcnow()
            job.result = result
            db.commit()
    except Exception as e:
        logger.error(f"Failed to mark job completed: {str(e)}")
    finally:
        db.close()


def mark_job_failed(job_id: str, error_message: str):
    """Mark job as failed with error message"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = error_message
            db.commit()
    except Exception as e:
        logger.error(f"Failed to mark job failed: {str(e)}")
    finally:
        db.close()


@celery_app.task(bind=True)
def analyze_data_quality_task(
    self,
    data_profile_id: int,
    job_id: str,
    analysis_types: List[str] = None,
    ai_enabled: bool = True,
    sample_size: Optional[int] = None
):
    """Background task for data quality analysis"""
    
    try:
        logger.info(f"Starting data quality analysis for profile {data_profile_id}")
        
        # Update job status
        update_job_progress(job_id, 5.0, "Initializing analysis", 6)
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Get data profile
            data_profile = db.query(DataProfile).filter(DataProfile.id == data_profile_id).first()
            if not data_profile:
                raise Exception(f"Data profile {data_profile_id} not found")
            
            update_job_progress(job_id, 15.0, "Loading data file")
            
            # Download and load data file
            file_content = asyncio.run(storage_manager.download_file(data_profile.file_path))
            if not file_content:
                raise Exception(f"Failed to download file: {data_profile.file_path}")
            
            # Read data into DataFrame
            df = pd.read_csv(io.BytesIO(file_content))
            
            update_job_progress(job_id, 30.0, "Analyzing data quality")
            
            # Perform analysis
            analysis_result = analyzer.analyze_data_quality(
                df=df,
                ai_enabled=ai_enabled,
                sample_size=sample_size
            )
            
            update_job_progress(job_id, 70.0, "Storing analysis results")
            
            # Update data profile with results
            data_profile.column_profiles = analysis_result.get("column_profiles", [])
            data_profile.duplicate_analysis = analysis_result.get("duplicate_analysis")
            data_profile.outlier_analysis = analysis_result.get("outlier_analysis")
            data_profile.missing_value_analysis = analysis_result.get("missing_value_analysis")
            data_profile.pattern_analysis = analysis_result.get("pattern_analysis")
            data_profile.ai_recommendations = analysis_result.get("ai_recommendations")
            
            # Update quality scores
            quality_metrics = analysis_result.get("quality_metrics")
            if quality_metrics:
                data_profile.completeness_score = quality_metrics.completeness_score
                data_profile.accuracy_score = quality_metrics.accuracy_score
                data_profile.consistency_score = quality_metrics.consistency_score
                data_profile.validity_score = quality_metrics.validity_score
                data_profile.uniqueness_score = quality_metrics.uniqueness_score
                data_profile.overall_quality_score = quality_metrics.overall_quality_score
            
            db.commit()
            
            update_job_progress(job_id, 90.0, "Generating report")
            
            # Prepare result
            result = {
                "analysis_completed": True,
                "data_profile_id": data_profile_id,
                "quality_score": data_profile.overall_quality_score,
                "issues": _extract_issues(analysis_result),
                "recommendations": analysis_result.get("ai_recommendations", {}),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            # Mark job as completed
            mark_job_completed(job_id, result)
            
            logger.info(f"Data quality analysis completed for profile {data_profile_id}")
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Data quality analysis failed: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        mark_job_failed(job_id, error_msg)
        raise


@celery_app.task(bind=True)
def clean_data_task(
    self,
    data_profile_id: int,
    job_id: str,
    cleaning_operations: List[Dict[str, Any]],
    preview_only: bool = False
):
    """Background task for data cleaning"""
    
    try:
        logger.info(f"Starting data cleaning for profile {data_profile_id}")
        
        # Update job status
        update_job_progress(job_id, 5.0, "Initializing cleaning", len(cleaning_operations) + 3)
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Get data profile
            data_profile = db.query(DataProfile).filter(DataProfile.id == data_profile_id).first()
            if not data_profile:
                raise Exception(f"Data profile {data_profile_id} not found")
            
            update_job_progress(job_id, 15.0, "Loading data file")
            
            # Download and load data file
            file_content = asyncio.run(storage_manager.download_file(data_profile.file_path))
            if not file_content:
                raise Exception(f"Failed to download file: {data_profile.file_path}")
            
            # Read data into DataFrame
            df = pd.read_csv(io.BytesIO(file_content))
            
            update_job_progress(job_id, 25.0, "Executing cleaning operations")
            
            # Perform cleaning
            cleaning_result = cleaner.clean_data(
                df=df,
                cleaning_operations=cleaning_operations,
                preview_only=preview_only
            )
            
            update_job_progress(job_id, 70.0, "Saving cleaned data")
            
            # Save cleaned data if not preview only
            cleaned_file_path = None
            if not preview_only and cleaning_result.cleaned_rows > 0:
                # Create cleaned data file
                cleaned_df_csv = cleaning_result.preview_data  # This would be the full cleaned DataFrame
                if cleaned_df_csv:
                    # Convert back to DataFrame and save
                    cleaned_df = pd.DataFrame(cleaned_df_csv)
                    csv_buffer = io.StringIO()
                    cleaned_df.to_csv(csv_buffer, index=False)
                    csv_content = csv_buffer.getvalue().encode('utf-8')
                    
                    # Generate cleaned file path
                    original_path = data_profile.file_path
                    path_parts = original_path.split('/')
                    filename = path_parts[-1]
                    name, ext = filename.rsplit('.', 1)
                    cleaned_filename = f"{name}_cleaned.{ext}"
                    cleaned_file_path = '/'.join(path_parts[:-1] + [cleaned_filename])
                    
                    # Upload cleaned file
                    asyncio.run(storage_manager.upload_file(csv_content, cleaned_file_path))
            
            update_job_progress(job_id, 90.0, "Finalizing results")
            
            # Prepare result
            result = {
                "cleaning_completed": True,
                "data_profile_id": data_profile_id,
                "original_rows": cleaning_result.original_rows,
                "cleaned_rows": cleaning_result.cleaned_rows,
                "removed_rows": cleaning_result.removed_rows,
                "modifications": cleaning_result.modifications,
                "cleaning_summary": cleaning_result.cleaning_summary,
                "quality_improvement": cleaning_result.quality_improvement,
                "preview_data": cleaning_result.preview_data if preview_only else None,
                "cleaned_file_path": cleaned_file_path,
                "cleaning_timestamp": datetime.utcnow().isoformat()
            }
            
            # Mark job as completed
            mark_job_completed(job_id, result)
            
            logger.info(f"Data cleaning completed for profile {data_profile_id}")
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Data cleaning failed: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        mark_job_failed(job_id, error_msg)
        raise


@celery_app.task(bind=True)
def generate_report_task(
    self,
    data_profile_id: int,
    job_id: str,
    report_type: str = "comprehensive"
):
    """Background task for generating data quality reports"""
    
    try:
        logger.info(f"Generating report for profile {data_profile_id}")
        
        # Update job status
        update_job_progress(job_id, 10.0, "Gathering data", 4)
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Get data profile
            data_profile = db.query(DataProfile).filter(DataProfile.id == data_profile_id).first()
            if not data_profile:
                raise Exception(f"Data profile {data_profile_id} not found")
            
            update_job_progress(job_id, 30.0, "Analyzing current state")
            
            # Generate visualizations and charts (placeholder)
            charts = _generate_charts(data_profile)
            
            update_job_progress(job_id, 70.0, "Compiling report")
            
            # Prepare comprehensive report
            result = {
                "report_generated": True,
                "data_profile_id": data_profile_id,
                "report_type": report_type,
                "summary": {
                    "file_name": data_profile.source_name,
                    "rows": data_profile.row_count,
                    "columns": data_profile.column_count,
                    "overall_quality": data_profile.overall_quality_score
                },
                "quality_metrics": {
                    "completeness": data_profile.completeness_score,
                    "accuracy": data_profile.accuracy_score,
                    "consistency": data_profile.consistency_score,
                    "validity": data_profile.validity_score,
                    "uniqueness": data_profile.uniqueness_score
                },
                "analysis_results": {
                    "duplicates": data_profile.duplicate_analysis,
                    "outliers": data_profile.outlier_analysis,
                    "missing_values": data_profile.missing_value_analysis,
                    "patterns": data_profile.pattern_analysis
                },
                "recommendations": data_profile.ai_recommendations,
                "charts": charts,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Mark job as completed
            mark_job_completed(job_id, result)
            
            logger.info(f"Report generation completed for profile {data_profile_id}")
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Report generation failed: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        mark_job_failed(job_id, error_msg)
        raise


def _extract_issues(analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract issues from analysis result"""
    issues = []
    
    # Extract duplicate issues
    duplicate_analysis = analysis_result.get("duplicate_analysis")
    if duplicate_analysis and duplicate_analysis.get("total_duplicates", 0) > 0:
        issues.append({
            "type": "duplicates",
            "severity": "medium" if duplicate_analysis["duplicate_percentage"] < 10 else "high",
            "count": duplicate_analysis["total_duplicates"],
            "percentage": duplicate_analysis["duplicate_percentage"],
            "description": f"Found {duplicate_analysis['total_duplicates']} duplicate records"
        })
    
    # Extract outlier issues
    outlier_analysis = analysis_result.get("outlier_analysis")
    if outlier_analysis and outlier_analysis.get("total_outliers", 0) > 0:
        issues.append({
            "type": "outliers",
            "severity": "low" if outlier_analysis["outlier_percentage"] < 5 else "medium",
            "count": outlier_analysis["total_outliers"],
            "percentage": outlier_analysis["outlier_percentage"],
            "description": f"Found {outlier_analysis['total_outliers']} outlier values"
        })
    
    # Extract missing value issues
    missing_analysis = analysis_result.get("missing_value_analysis")
    if missing_analysis and missing_analysis.get("total_missing", 0) > 0:
        issues.append({
            "type": "missing_values",
            "severity": "medium" if missing_analysis["missing_percentage"] < 20 else "high",
            "count": missing_analysis["total_missing"],
            "percentage": missing_analysis["missing_percentage"],
            "description": f"Found {missing_analysis['total_missing']} missing values"
        })
    
    return issues


def _generate_charts(data_profile: DataProfile) -> Dict[str, str]:
    """Generate charts for data quality report (placeholder)"""
    # This would generate actual charts using matplotlib/plotly
    # For now, return placeholder chart data
    
    charts = {}
    
    if data_profile.overall_quality_score:
        charts["quality_score"] = f"data:image/png;base64,placeholder_quality_chart"
    
    if data_profile.column_profiles:
        charts["column_distribution"] = f"data:image/png;base64,placeholder_column_chart"
    
    if data_profile.duplicate_analysis:
        charts["duplicates"] = f"data:image/png;base64,placeholder_duplicate_chart"
    
    return charts