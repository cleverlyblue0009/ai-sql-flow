"""
Enterprise features for SQL migration system
Includes batch migration, export capabilities, history management, and rollback functionality
"""

import os
import json
import zipfile
import logging
from typing import Dict, List, Any, Optional, BinaryIO
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uuid
import tempfile
import asyncio

from ..database import MigrationLog, Job, User, Project, JobStatus, MigrationStatus
from .services import MigrationService, SQLTranslationService
from .sql_parser import SQLParser
from ..tasks.migration_tasks import start_migration_task, analyze_sql_schema_task, translate_sql_task

logger = logging.getLogger(__name__)


class BatchMigrationManager:
    """Manages batch migration operations for multiple SQL files"""
    
    def __init__(self):
        self.migration_service = MigrationService()
        self.translation_service = SQLTranslationService()
        self.sql_parser = SQLParser()
    
    async def create_batch_migration(
        self,
        db: Session,
        user_id: int,
        project_id: int,
        batch_name: str,
        sql_files: List[Dict[str, Any]],
        source_config: Dict[str, Any],
        target_config: Dict[str, Any],
        migration_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a batch migration from multiple SQL files"""
        
        try:
            batch_id = str(uuid.uuid4())
            migration_ids = []
            
            # Create individual migrations for each file
            for i, sql_file in enumerate(sql_files):
                migration_name = f"{batch_name} - {sql_file['filename']}"
                
                # Create migration log
                migration_id = str(uuid.uuid4())
                migration_log = MigrationLog(
                    migration_id=migration_id,
                    project_id=project_id,
                    name=migration_name,
                    description=f"Part {i+1} of batch migration: {batch_name}",
                    source_dialect=source_config['connection_type'],
                    target_dialect=target_config['connection_type'],
                    original_sql=sql_file['content'],
                    schema_mapping=migration_options.get('schema_mapping', {}),
                    table_mappings=migration_options.get('table_mappings', {})
                )
                
                db.add(migration_log)
                migration_ids.append(migration_id)
            
            db.commit()
            
            # Create batch metadata
            batch_metadata = {
                "batch_id": batch_id,
                "batch_name": batch_name,
                "migration_ids": migration_ids,
                "total_files": len(sql_files),
                "created_at": datetime.utcnow().isoformat(),
                "status": "created",
                "source_config": source_config,
                "target_config": target_config,
                "migration_options": migration_options
            }
            
            return {
                "batch_id": batch_id,
                "migration_ids": migration_ids,
                "status": "created",
                "message": f"Batch migration created with {len(sql_files)} files",
                "metadata": batch_metadata
            }
            
        except Exception as e:
            logger.error(f"Error creating batch migration: {str(e)}")
            raise
    
    async def start_batch_migration(
        self,
        db: Session,
        batch_id: str,
        migration_ids: List[str],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Start a batch migration process"""
        
        try:
            batch_job_id = str(uuid.uuid4())
            
            # Create master job for batch
            batch_job = Job(
                job_id=batch_job_id,
                job_type="batch_migration",
                name=f"Batch Migration: {batch_id}",
                user_id=config.get('user_id'),
                project_id=config.get('project_id'),
                parameters={
                    "batch_id": batch_id,
                    "migration_ids": migration_ids,
                    "config": config
                }
            )
            
            db.add(batch_job)
            db.commit()
            
            # Start individual migrations
            migration_jobs = []
            for migration_id in migration_ids:
                job_id = str(uuid.uuid4())
                
                # Create individual job
                job = Job(
                    job_id=job_id,
                    job_type="migration",
                    name=f"Migration: {migration_id}",
                    user_id=config.get('user_id'),
                    project_id=config.get('project_id'),
                    parameters={
                        "migration_id": migration_id,
                        "batch_id": batch_id,
                        "config": config
                    }
                )
                
                db.add(job)
                migration_jobs.append((migration_id, job_id))
            
            db.commit()
            
            # Start background tasks
            for migration_id, job_id in migration_jobs:
                start_migration_task.delay(migration_id, job_id, config)
            
            return {
                "batch_job_id": batch_job_id,
                "migration_jobs": migration_jobs,
                "status": "started",
                "message": f"Batch migration started with {len(migration_ids)} migrations"
            }
            
        except Exception as e:
            logger.error(f"Error starting batch migration: {str(e)}")
            raise
    
    async def get_batch_progress(
        self,
        db: Session,
        batch_id: str
    ) -> Dict[str, Any]:
        """Get progress of batch migration"""
        
        try:
            # Get all migrations in batch
            migrations = db.query(MigrationLog).filter(
                MigrationLog.migration_id.in_(
                    db.query(Job.parameters['migration_id']).filter(
                        Job.parameters.contains({"batch_id": batch_id})
                    )
                )
            ).all()
            
            if not migrations:
                return {"error": "Batch not found"}
            
            # Calculate overall progress
            total_migrations = len(migrations)
            completed_migrations = len([m for m in migrations if m.status == MigrationStatus.COMPLETED])
            failed_migrations = len([m for m in migrations if m.status == MigrationStatus.FAILED])
            running_migrations = len([m for m in migrations if m.status in [MigrationStatus.MAPPING, MigrationStatus.TRANSLATING, MigrationStatus.EXECUTING]])
            
            overall_progress = sum([m.progress_percentage or 0 for m in migrations]) / total_migrations
            
            # Determine batch status
            if completed_migrations == total_migrations:
                batch_status = "completed"
            elif failed_migrations > 0:
                batch_status = "partially_failed"
            elif running_migrations > 0:
                batch_status = "running"
            else:
                batch_status = "pending"
            
            return {
                "batch_id": batch_id,
                "status": batch_status,
                "overall_progress": overall_progress,
                "total_migrations": total_migrations,
                "completed_migrations": completed_migrations,
                "failed_migrations": failed_migrations,
                "running_migrations": running_migrations,
                "migrations": [
                    {
                        "migration_id": m.migration_id,
                        "name": m.name,
                        "status": m.status.value,
                        "progress": m.progress_percentage or 0,
                        "current_phase": m.current_phase
                    }
                    for m in migrations
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting batch progress: {str(e)}")
            raise


class MigrationExportManager:
    """Manages export of migration results and translated SQL"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    async def export_migration_results(
        self,
        db: Session,
        migration_ids: List[str],
        export_format: str = "zip",
        include_original: bool = True,
        include_translated: bool = True,
        include_reports: bool = True
    ) -> str:
        """Export migration results to various formats"""
        
        try:
            export_id = str(uuid.uuid4())
            export_filename = f"migration_export_{export_id}.{export_format}"
            export_path = os.path.join(self.temp_dir, export_filename)
            
            # Get migration data
            migrations = db.query(MigrationLog).filter(
                MigrationLog.migration_id.in_(migration_ids)
            ).all()
            
            if not migrations:
                raise ValueError("No migrations found")
            
            if export_format == "zip":
                return await self._create_zip_export(
                    migrations, export_path, include_original, include_translated, include_reports
                )
            elif export_format == "json":
                return await self._create_json_export(
                    migrations, export_path, include_original, include_translated, include_reports
                )
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
                
        except Exception as e:
            logger.error(f"Error exporting migration results: {str(e)}")
            raise
    
    async def _create_zip_export(
        self,
        migrations: List[MigrationLog],
        export_path: str,
        include_original: bool,
        include_translated: bool,
        include_reports: bool
    ) -> str:
        """Create ZIP export of migration results"""
        
        with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for migration in migrations:
                migration_folder = f"migration_{migration.migration_id}"
                
                # Add original SQL
                if include_original and migration.original_sql:
                    original_filename = f"{migration_folder}/original_{migration.source_dialect}.sql"
                    zipf.writestr(original_filename, migration.original_sql)
                
                # Add translated SQL
                if include_translated and migration.translated_sql:
                    translated_filename = f"{migration_folder}/translated_{migration.target_dialect}.sql"
                    zipf.writestr(translated_filename, migration.translated_sql)
                
                # Add migration report
                if include_reports:
                    report = self._generate_migration_report(migration)
                    report_filename = f"{migration_folder}/migration_report.json"
                    zipf.writestr(report_filename, json.dumps(report, indent=2, default=str))
                
                # Add performance metrics if available
                if migration.performance_metrics:
                    metrics_filename = f"{migration_folder}/performance_metrics.json"
                    zipf.writestr(metrics_filename, json.dumps(migration.performance_metrics, indent=2))
            
            # Add summary report
            summary_report = self._generate_summary_report(migrations)
            zipf.writestr("summary_report.json", json.dumps(summary_report, indent=2, default=str))
        
        return export_path
    
    async def _create_json_export(
        self,
        migrations: List[MigrationLog],
        export_path: str,
        include_original: bool,
        include_translated: bool,
        include_reports: bool
    ) -> str:
        """Create JSON export of migration results"""
        
        export_data = {
            "export_metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "migration_count": len(migrations),
                "export_options": {
                    "include_original": include_original,
                    "include_translated": include_translated,
                    "include_reports": include_reports
                }
            },
            "migrations": []
        }
        
        for migration in migrations:
            migration_data = {
                "migration_id": migration.migration_id,
                "name": migration.name,
                "description": migration.description,
                "source_dialect": migration.source_dialect,
                "target_dialect": migration.target_dialect,
                "status": migration.status.value,
                "created_at": migration.created_at.isoformat() if migration.created_at else None,
                "completed_at": migration.completed_at.isoformat() if migration.completed_at else None
            }
            
            if include_original and migration.original_sql:
                migration_data["original_sql"] = migration.original_sql
            
            if include_translated and migration.translated_sql:
                migration_data["translated_sql"] = migration.translated_sql
            
            if include_reports:
                migration_data["report"] = self._generate_migration_report(migration)
            
            if migration.performance_metrics:
                migration_data["performance_metrics"] = migration.performance_metrics
            
            export_data["migrations"].append(migration_data)
        
        # Write JSON file
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return export_path
    
    def _generate_migration_report(self, migration: MigrationLog) -> Dict[str, Any]:
        """Generate detailed migration report"""
        
        return {
            "migration_id": migration.migration_id,
            "name": migration.name,
            "description": migration.description,
            "source_dialect": migration.source_dialect,
            "target_dialect": migration.target_dialect,
            "status": migration.status.value,
            "progress_percentage": migration.progress_percentage,
            "current_phase": migration.current_phase,
            "created_at": migration.created_at,
            "started_at": migration.started_at,
            "completed_at": migration.completed_at,
            "translation_confidence": migration.translation_confidence,
            "semantic_similarity": migration.semantic_similarity,
            "schema_mapping": migration.schema_mapping,
            "table_mappings": migration.table_mappings,
            "execution_log": migration.execution_log,
            "error_log": migration.error_log,
            "ai_optimizations": migration.ai_optimizations,
            "performance_predictions": migration.performance_predictions
        }
    
    def _generate_summary_report(self, migrations: List[MigrationLog]) -> Dict[str, Any]:
        """Generate summary report for multiple migrations"""
        
        total_migrations = len(migrations)
        completed_migrations = len([m for m in migrations if m.status == MigrationStatus.COMPLETED])
        failed_migrations = len([m for m in migrations if m.status == MigrationStatus.FAILED])
        
        # Calculate average metrics
        avg_confidence = sum([m.translation_confidence or 0 for m in migrations]) / total_migrations
        avg_similarity = sum([m.semantic_similarity or 0 for m in migrations]) / total_migrations
        
        # Collect dialects
        source_dialects = list(set([m.source_dialect for m in migrations]))
        target_dialects = list(set([m.target_dialect for m in migrations]))
        
        return {
            "summary": {
                "total_migrations": total_migrations,
                "completed_migrations": completed_migrations,
                "failed_migrations": failed_migrations,
                "success_rate": (completed_migrations / total_migrations) * 100 if total_migrations > 0 else 0,
                "average_translation_confidence": avg_confidence,
                "average_semantic_similarity": avg_similarity,
                "source_dialects": source_dialects,
                "target_dialects": target_dialects
            },
            "migration_details": [
                {
                    "migration_id": m.migration_id,
                    "name": m.name,
                    "status": m.status.value,
                    "progress": m.progress_percentage or 0
                }
                for m in migrations
            ]
        }


class MigrationHistoryManager:
    """Manages migration history and rollback functionality"""
    
    def __init__(self):
        self.migration_service = MigrationService()
    
    async def get_migration_history(
        self,
        db: Session,
        project_id: int,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get migration history with filtering options"""
        
        try:
            query = db.query(MigrationLog).filter(
                MigrationLog.project_id == project_id
            )
            
            # Apply filters
            if status_filter:
                query = query.filter(MigrationLog.status == MigrationStatus(status_filter))
            
            if date_from:
                query = query.filter(MigrationLog.created_at >= date_from)
            
            if date_to:
                query = query.filter(MigrationLog.created_at <= date_to)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            migrations = query.order_by(desc(MigrationLog.created_at)).offset(offset).limit(limit).all()
            
            # Format results
            history_items = []
            for migration in migrations:
                history_items.append({
                    "migration_id": migration.migration_id,
                    "name": migration.name,
                    "description": migration.description,
                    "status": migration.status.value,
                    "source_dialect": migration.source_dialect,
                    "target_dialect": migration.target_dialect,
                    "created_at": migration.created_at,
                    "started_at": migration.started_at,
                    "completed_at": migration.completed_at,
                    "progress_percentage": migration.progress_percentage,
                    "current_phase": migration.current_phase,
                    "translation_confidence": migration.translation_confidence,
                    "semantic_similarity": migration.semantic_similarity,
                    "has_backup": self._has_rollback_data(migration)
                })
            
            return {
                "history": history_items,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_next": offset + limit < total_count,
                    "has_prev": offset > 0
                },
                "filters_applied": {
                    "status": status_filter,
                    "date_from": date_from,
                    "date_to": date_to
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting migration history: {str(e)}")
            raise
    
    async def create_rollback_point(
        self,
        db: Session,
        migration_id: str,
        rollback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a rollback point for a migration"""
        
        try:
            migration = db.query(MigrationLog).filter(
                MigrationLog.migration_id == migration_id
            ).first()
            
            if not migration:
                raise ValueError("Migration not found")
            
            # Store rollback data in migration log
            if not migration.execution_log:
                migration.execution_log = []
            
            rollback_entry = {
                "type": "rollback_point",
                "created_at": datetime.utcnow().isoformat(),
                "data": rollback_data
            }
            
            migration.execution_log.append(rollback_entry)
            db.commit()
            
            return {
                "migration_id": migration_id,
                "rollback_point_created": True,
                "timestamp": rollback_entry["created_at"]
            }
            
        except Exception as e:
            logger.error(f"Error creating rollback point: {str(e)}")
            raise
    
    async def perform_rollback(
        self,
        db: Session,
        migration_id: str,
        rollback_reason: str
    ) -> Dict[str, Any]:
        """Perform rollback for a migration"""
        
        try:
            migration = db.query(MigrationLog).filter(
                MigrationLog.migration_id == migration_id
            ).first()
            
            if not migration:
                raise ValueError("Migration not found")
            
            if not self._has_rollback_data(migration):
                raise ValueError("No rollback data available for this migration")
            
            # Create rollback job
            rollback_job_id = str(uuid.uuid4())
            rollback_job = Job(
                job_id=rollback_job_id,
                job_type="migration_rollback",
                name=f"Rollback: {migration.name}",
                user_id=migration.project.owner_id,
                project_id=migration.project_id,
                parameters={
                    "migration_id": migration_id,
                    "rollback_reason": rollback_reason
                }
            )
            
            db.add(rollback_job)
            
            # Update migration status
            migration.status = MigrationStatus.FAILED
            if not migration.error_log:
                migration.error_log = []
            
            migration.error_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "type": "rollback",
                "reason": rollback_reason,
                "job_id": rollback_job_id
            })
            
            db.commit()
            
            return {
                "migration_id": migration_id,
                "rollback_job_id": rollback_job_id,
                "status": "rollback_initiated",
                "message": "Rollback process started"
            }
            
        except Exception as e:
            logger.error(f"Error performing rollback: {str(e)}")
            raise
    
    def _has_rollback_data(self, migration: MigrationLog) -> bool:
        """Check if migration has rollback data available"""
        
        if not migration.execution_log:
            return False
        
        return any(
            entry.get("type") == "rollback_point" 
            for entry in migration.execution_log
        )


# Global instances
batch_migration_manager = BatchMigrationManager()
export_manager = MigrationExportManager()
history_manager = MigrationHistoryManager()