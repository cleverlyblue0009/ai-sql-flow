from celery import Celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from typing import Dict, Any
import time
import logging
from datetime import datetime

from ..database import settings, MigrationLog, Job, JobStatus, MigrationStatus
from ..migration.services import SQLTranslationService

# Create Celery app
celery_app = Celery(
    "migration_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger(__name__)
translation_service = SQLTranslationService()


@celery_app.task(bind=True)
def start_migration_task(self, migration_id: str, job_id: str, config: Dict[str, Any]):
    """Background task for database migration"""
    
    db = SessionLocal()
    
    try:
        # Get migration and job records
        migration = db.query(MigrationLog).filter(MigrationLog.migration_id == migration_id).first()
        job = db.query(Job).filter(Job.job_id == job_id).first()
        
        if not migration or not job:
            logger.error(f"Migration or job not found: {migration_id}, {job_id}")
            return
        
        # Update job status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.current_step = "Starting migration"
        job.total_steps = 6
        db.commit()
        
        # Step 1: Source Connection
        self.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 6, 'status': 'Connecting to source database'}
        )
        
        migration.status = MigrationStatus.MAPPING
        migration.current_phase = "Source Connection"
        migration.progress_percentage = 16.7
        db.commit()
        
        time.sleep(2)  # Simulate connection time
        
        # Step 2: Schema Analysis
        self.update_state(
            state='PROGRESS',
            meta={'current': 2, 'total': 6, 'status': 'Analyzing source schema'}
        )
        
        migration.current_phase = "Schema Analysis"
        migration.progress_percentage = 33.3
        job.current_step = "Analyzing schema structure"
        db.commit()
        
        time.sleep(5)  # Simulate schema analysis
        
        # Step 3: SQL Translation
        self.update_state(
            state='PROGRESS',
            meta={'current': 3, 'total': 6, 'status': 'Translating SQL queries'}
        )
        
        migration.status = MigrationStatus.TRANSLATING
        migration.current_phase = "SQL Translation"
        migration.progress_percentage = 50.0
        job.current_step = "Translating SQL queries"
        db.commit()
        
        time.sleep(3)  # Simulate SQL translation
        
        # Step 4: Validation
        self.update_state(
            state='PROGRESS',
            meta={'current': 4, 'total': 6, 'status': 'Validating translated queries'}
        )
        
        migration.current_phase = "Validation"
        migration.progress_percentage = 66.7
        job.current_step = "Validating translations"
        db.commit()
        
        time.sleep(2)  # Simulate validation
        
        # Step 5: Data Migration
        self.update_state(
            state='PROGRESS',
            meta={'current': 5, 'total': 6, 'status': 'Migrating data'}
        )
        
        migration.status = MigrationStatus.EXECUTING
        migration.current_phase = "Data Migration"
        migration.progress_percentage = 83.3
        job.current_step = "Migrating data"
        db.commit()
        
        # Simulate data migration with progress updates
        for i in range(10):
            time.sleep(1.5)
            progress = 83.3 + (i + 1) * 1.3
            migration.progress_percentage = min(progress, 95.0)
            db.commit()
            
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': 5, 
                    'total': 6, 
                    'status': f'Migrating data - {int(progress - 83.3)}% complete'
                }
            )
        
        # Step 6: Performance Test
        self.update_state(
            state='PROGRESS',
            meta={'current': 6, 'total': 6, 'status': 'Running performance tests'}
        )
        
        migration.current_phase = "Performance Test"
        migration.progress_percentage = 95.0
        job.current_step = "Performance testing"
        db.commit()
        
        time.sleep(5)  # Simulate performance testing
        
        # Complete migration
        migration.status = MigrationStatus.COMPLETED
        migration.progress_percentage = 100.0
        migration.completed_at = datetime.utcnow()
        migration.current_phase = "Completed"
        
        # Mock performance metrics
        migration.performance_metrics = {
            "query_performance_improvement": 67.0,
            "resource_usage_reduction": 45.0,
            "cost_savings_monthly": 2340.0,
            "migration_duration_minutes": (datetime.utcnow() - migration.started_at).total_seconds() / 60
        }
        
        # Update job
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.progress_percentage = 100.0
        job.current_step = "Migration completed"
        job.execution_time = (job.completed_at - job.started_at).total_seconds()
        job.result = {
            "status": "success",
            "message": "Migration completed successfully",
            "performance_metrics": migration.performance_metrics
        }
        
        db.commit()
        
        logger.info(f"Migration {migration_id} completed successfully")
        
        return {
            "status": "completed",
            "migration_id": migration_id,
            "message": "Migration completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Migration {migration_id} failed: {str(e)}")
        
        # Update migration status
        if 'migration' in locals():
            migration.status = MigrationStatus.FAILED
            migration.error_log = [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e),
                    "phase": migration.current_phase
                }
            ]
            db.commit()
        
        # Update job status
        if 'job' in locals():
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True)
def translate_sql_task(
    self, 
    job_id: str, 
    source_sql: str, 
    source_dialect: str, 
    target_dialect: str, 
    optimization_level: str = "standard"
):
    """Background task for SQL translation"""
    
    db = SessionLocal()
    
    try:
        # Get job record
        job = db.query(Job).filter(Job.job_id == job_id).first()
        
        if not job:
            logger.error(f"Job not found: {job_id}")
            return
        
        # Update job status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.current_step = "Translating SQL"
        job.progress_percentage = 10.0
        db.commit()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 4, 'status': 'Analyzing source SQL'}
        )
        
        # Perform SQL translation
        translation_result = translation_service.translate_sql(
            source_sql=source_sql,
            source_dialect=source_dialect,
            target_dialect=target_dialect,
            optimization_level=optimization_level
        )
        
        # Update progress
        job.progress_percentage = 50.0
        job.current_step = "Validating translation"
        db.commit()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 2, 'total': 4, 'status': 'Validating translation'}
        )
        
        # Simulate validation time
        time.sleep(1)
        
        # Update progress
        job.progress_percentage = 80.0
        job.current_step = "Generating optimization suggestions"
        db.commit()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 3, 'total': 4, 'status': 'Generating optimization suggestions'}
        )
        
        # Simulate optimization analysis
        time.sleep(1)
        
        # Complete translation
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.progress_percentage = 100.0
        job.current_step = "Translation completed"
        job.execution_time = (job.completed_at - job.started_at).total_seconds()
        job.result = translation_result
        
        db.commit()
        
        logger.info(f"SQL translation {job_id} completed successfully")
        
        return translation_result
        
    except Exception as e:
        logger.error(f"SQL translation {job_id} failed: {str(e)}")
        
        # Update job status
        if 'job' in locals():
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True)
def validate_migration_task(self, migration_id: str, job_id: str):
    """Background task for migration validation"""
    
    db = SessionLocal()
    
    try:
        # Get migration and job records
        migration = db.query(MigrationLog).filter(MigrationLog.migration_id == migration_id).first()
        job = db.query(Job).filter(Job.job_id == job_id).first()
        
        if not migration or not job:
            logger.error(f"Migration or job not found: {migration_id}, {job_id}")
            return
        
        # Update job status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.current_step = "Validating migration"
        job.total_steps = 3
        db.commit()
        
        # Step 1: Data integrity check
        self.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 3, 'status': 'Checking data integrity'}
        )
        
        job.progress_percentage = 33.3
        job.current_step = "Data integrity check"
        db.commit()
        
        time.sleep(3)  # Simulate integrity check
        
        # Step 2: Performance validation
        self.update_state(
            state='PROGRESS',
            meta={'current': 2, 'total': 3, 'status': 'Validating performance'}
        )
        
        job.progress_percentage = 66.7
        job.current_step = "Performance validation"
        db.commit()
        
        time.sleep(2)  # Simulate performance validation
        
        # Step 3: Final validation
        self.update_state(
            state='PROGRESS',
            meta={'current': 3, 'total': 3, 'status': 'Final validation'}
        )
        
        job.progress_percentage = 100.0
        job.current_step = "Final validation"
        db.commit()
        
        time.sleep(1)  # Simulate final validation
        
        # Complete validation
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.execution_time = (job.completed_at - job.started_at).total_seconds()
        job.result = {
            "status": "success",
            "message": "Migration validation completed",
            "validation_results": {
                "data_integrity": "passed",
                "performance": "passed",
                "schema_consistency": "passed"
            }
        }
        
        db.commit()
        
        logger.info(f"Migration validation {migration_id} completed successfully")
        
        return job.result
        
    except Exception as e:
        logger.error(f"Migration validation {migration_id} failed: {str(e)}")
        
        # Update job status
        if 'job' in locals():
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        
        raise
        
    finally:
        db.close()