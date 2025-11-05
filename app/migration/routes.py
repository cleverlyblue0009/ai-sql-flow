from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime

from ..database import get_db, User, Project, Connection, MigrationLog, Job
from ..database.models import UserRole
from .schemas import (
    MigrationSetupRequest, MigrationResponse, ConnectionTestRequest,
    ConnectionTestResponse, SQLTranslationRequest, SQLTranslationResponse,
    MigrationProgressResponse, PerformanceAnalysisResponse, DatabaseListResponse,
    MigrationConfigRequest, MigrationStatusResponse, BatchSQLConversionRequest,
    BatchSQLConversionResponse, DialectDetectionRequest, DialectDetectionResponse
)
from .services import MigrationService, SQLTranslationService, ConnectionService
from .enterprise_features import batch_migration_manager, export_manager, history_manager
from .batch_sql_converter import batch_converter
from ..tasks.migration_tasks import start_migration_task_wrapper, translate_sql_task_wrapper, analyze_sql_schema_task_wrapper
from ..utils.audit import log_migration_action

router = APIRouter(prefix="/migration", tags=["SQL Migration"])
logger = logging.getLogger(__name__)

# Initialize services
migration_service = MigrationService()
translation_service = SQLTranslationService()
connection_service = ConnectionService()


@router.get("/databases", response_model=DatabaseListResponse)
async def get_supported_databases():
    """Get list of supported database types and their dialects"""
    
    try:
        databases = await migration_service.get_supported_databases()
        return DatabaseListResponse(databases=databases)
        
    except Exception as e:
        logger.error(f"Error getting supported databases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get supported databases"
        )


@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_database_connection(
    request: ConnectionTestRequest,
    db: Session = Depends(get_db)
):
    """Test database connection with provided credentials - No auth required"""
    
    try:
        # Test the connection
        test_result = await connection_service.test_connection(
            connection_type=request.connection_type,
            host=request.host,
            port=request.port,
            database=request.database,
            username=request.username,
            password=request.password,
            connection_params=request.connection_params
        )
        
        return test_result
        
    except Exception as e:
        logger.error(f"Error testing connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test connection"
        )


@router.post("/setup", response_model=MigrationResponse)
async def setup_migration(
    request: MigrationSetupRequest,
    db: Session = Depends(get_db)
):
    """Set up a new migration project - No auth required"""
    
    try:
        # Get or create a default user for demo purposes
        demo_user = db.query(User).filter(User.email == "demo@example.com").first()
        if not demo_user:
            demo_user = User(
                email="demo@example.com",
                username="demo",
                firebase_uid="demo_uid",
                full_name="Demo User",
                role=UserRole.ADMIN
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        
        # Validate project ownership
        project = db.query(Project).filter(
            Project.id == request.project_id
        ).first()
        
        if not project:
            # Create default project if not exists
            project = Project(
                name="Default Project",
                owner_id=demo_user.id,
                description="Auto-created project for migrations"
            )
            db.add(project)
            db.commit()
            db.refresh(project)
        
        # Create or get source connection
        source_connection = await connection_service.create_or_get_connection(
            db=db,
            user_id=demo_user.id,
            name=f"{request.source_config.connection_type}_source",
            connection_type=request.source_config.connection_type,
            host=request.source_config.host,
            port=request.source_config.port,
            database=request.source_config.database,
            username=request.source_config.username,
            password=request.source_config.password,
            connection_params=request.source_config.connection_params
        )
        
        # Create or get target connection
        target_connection = await connection_service.create_or_get_connection(
            db=db,
            user_id=demo_user.id,
            name=f"{request.target_config.connection_type}_target",
            connection_type=request.target_config.connection_type,
            host=request.target_config.host,
            port=request.target_config.port,
            database=request.target_config.database,
            username=request.target_config.username,
            password=request.target_config.password,
            connection_params=request.target_config.connection_params
        )
        
        # Create migration log
        migration_id = str(uuid.uuid4())
        migration_log = MigrationLog(
            migration_id=migration_id,
            project_id=request.project_id,
            source_connection_id=source_connection.id,
            target_connection_id=target_connection.id,
            name=request.name,
            description=request.description,
            source_dialect=request.source_config.connection_type,
            target_dialect=request.target_config.connection_type,
            schema_mapping=request.migration_options.get("schema_mapping", {}),
            table_mappings=request.migration_options.get("table_mappings", {})
        )
        
        db.add(migration_log)
        db.commit()
        db.refresh(migration_log)
        
        return MigrationResponse(
            migration_id=migration_id,
            status="created",
            message="Migration setup completed successfully",
            created_at=migration_log.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up migration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set up migration"
        )


@router.post("/translate-sql", response_model=SQLTranslationResponse)
async def translate_sql(
    request: SQLTranslationRequest,
    db: Session = Depends(get_db)
):
    """Translate SQL from source dialect to target dialect - No auth required"""
    
    try:
        # Get or create a default user for demo purposes
        demo_user = db.query(User).filter(User.email == "demo@example.com").first()
        if not demo_user:
            demo_user = User(
                email="demo@example.com",
                username="demo",
                firebase_uid="demo_uid",
                full_name="Demo User",
                role=UserRole.ADMIN
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        
        # Start translation job
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            job_type="sql_translation",
            name=f"SQL Translation: {request.source_dialect} to {request.target_dialect}",
            user_id=demo_user.id,
            parameters={
                "source_sql": request.source_sql,
                "source_dialect": request.source_dialect,
                "target_dialect": request.target_dialect,
                "optimization_level": request.optimization_level
            }
        )
        
        db.add(job)
        db.commit()
        
        # Start background translation
        translate_sql_task_wrapper(
            job_id=job_id,
            source_sql=request.source_sql,
            source_dialect=request.source_dialect,
            target_dialect=request.target_dialect,
            optimization_level=request.optimization_level
        )
        
        return SQLTranslationResponse(
            job_id=job_id,
            status="processing",
            message="SQL translation started"
        )
        
    except Exception as e:
        logger.error(f"Error starting SQL translation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start SQL translation: {str(e)}"
        )


@router.post("/start", response_model=Dict[str, str])
async def start_migration(
    migration_id: str,
    config: MigrationConfigRequest,
    db: Session = Depends(get_db)
):
    """Start the migration process - No auth required"""
    
    try:
        # Get or create a default user for demo purposes
        demo_user = db.query(User).filter(User.email == "demo@example.com").first()
        if not demo_user:
            demo_user = User(
                email="demo@example.com",
                username="demo",
                firebase_uid="demo_uid",
                full_name="Demo User",
                role=UserRole.ADMIN
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        
        # Get migration log
        migration_log = db.query(MigrationLog).filter(
            MigrationLog.migration_id == migration_id
        ).first()
        
        if not migration_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Migration not found"
            )
        
        if migration_log.status.value not in ["created", "failed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Migration cannot be started from status: {migration_log.status.value}"
            )
        
        # Create migration job
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            job_type="migration",
            name=f"Migration: {migration_log.name}",
            user_id=demo_user.id,
            project_id=migration_log.project_id,
            parameters={
                "migration_id": migration_id,
                "migrate_schema": config.migrate_schema,
                "migrate_data": config.migrate_data,
                "preserve_constraints": config.preserve_constraints,
                "optimize_for_target": config.optimize_for_target,
                "batch_size": config.batch_size,
                "parallel_jobs": config.parallel_jobs
            }
        )
        
        db.add(job)
        db.commit()
        
        # Update migration status
        migration_log.status = "mapping"
        migration_log.started_at = datetime.utcnow()
        db.commit()
        
        # Start background migration
        start_migration_task_wrapper(
            migration_id=migration_id,
            job_id=job_id,
            config=config.dict()
        )
        
        return {
            "message": "Migration started successfully",
            "job_id": job_id,
            "migration_id": migration_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting migration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start migration: {str(e)}"
        )


@router.get("/progress/{migration_id}", response_model=MigrationProgressResponse)
async def get_migration_progress(
    migration_id: str,
    db: Session = Depends(get_db)
):
    """Get migration progress and status - No auth required"""
    
    try:
        # Get migration log
        migration_log = db.query(MigrationLog).filter(
            MigrationLog.migration_id == migration_id
        ).first()
        
        if not migration_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Migration not found"
            )
        
        # Get associated job
        job = db.query(Job).filter(
            Job.parameters.contains({"migration_id": migration_id}),
            Job.job_type == "migration"
        ).order_by(Job.created_at.desc()).first()
        
        # Build progress response
        progress = await migration_service.get_migration_progress(migration_log, job)
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting migration progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get migration progress"
        )


@router.get("/performance/{migration_id}", response_model=PerformanceAnalysisResponse)
async def get_performance_analysis(
    migration_id: str,
    db: Session = Depends(get_db)
):
    """Get migration performance analysis - No auth required"""
    
    try:
        # Get migration log
        migration_log = db.query(MigrationLog).filter(
            MigrationLog.migration_id == migration_id
        ).first()
        
        if not migration_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Migration not found"
            )
        
        if migration_log.status.value != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Performance analysis only available for completed migrations"
            )
        
        # Get performance analysis
        analysis = await migration_service.get_performance_analysis(migration_log)
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance analysis"
        )


@router.get("/status/{migration_id}", response_model=MigrationStatusResponse)
async def get_migration_status(
    migration_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed migration status - No auth required"""
    
    try:
        # Get migration log
        migration_log = db.query(MigrationLog).filter(
            MigrationLog.migration_id == migration_id
        ).first()
        
        if not migration_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Migration not found"
            )
        
        # Build status response
        status_response = await migration_service.get_migration_status(migration_log)
        return status_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting migration status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get migration status"
        )


@router.get("/list/{project_id}")
async def list_migrations(
    project_id: int,
    db: Session = Depends(get_db)
):
    """List all migrations for a project - No auth required"""
    
    try:
        # Validate project exists
        project = db.query(Project).filter(
            Project.id == project_id
        ).first()
        
        if not project:
            # Return empty list for non-existent projects
            return {"migrations": []}
        
        # Get migrations
        migrations = db.query(MigrationLog).filter(
            MigrationLog.project_id == project_id
        ).order_by(MigrationLog.created_at.desc()).all()
        
        return {
            "migrations": [
                {
                    "migration_id": m.migration_id,
                    "name": m.name,
                    "status": m.status.value,
                    "source_dialect": m.source_dialect,
                    "target_dialect": m.target_dialect,
                    "created_at": m.created_at,
                    "started_at": m.started_at,
                    "completed_at": m.completed_at,
                    "progress_percentage": m.progress_percentage
                }
                for m in migrations
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing migrations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list migrations"
        )


# Enterprise Features Endpoints

@router.post("/analyze-sql")
async def analyze_sql_schema(
    sql_content: str,
    source_dialect: str = "mysql",
    db: Session = Depends(get_db)
):
    """Analyze SQL schema and structure - No auth required"""
    
    try:
        # Get or create a default user for demo purposes
        demo_user = db.query(User).filter(User.email == "demo@example.com").first()
        if not demo_user:
            demo_user = User(
                email="demo@example.com",
                username="demo",
                firebase_uid="demo_uid",
                full_name="Demo User",
                role=UserRole.ADMIN
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        
        # Create analysis job
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            job_type="sql_analysis",
            name="SQL Schema Analysis",
            user_id=demo_user.id,
            parameters={
                "sql_content": sql_content[:1000] + "..." if len(sql_content) > 1000 else sql_content,
                "source_dialect": source_dialect
            }
        )
        
        db.add(job)
        db.commit()
        
        # Start background analysis
        analyze_sql_schema_task_wrapper(job_id, sql_content, source_dialect)
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "SQL analysis started"
        }
        
    except Exception as e:
        logger.error(f"Error starting SQL analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start SQL analysis"
        )


@router.post("/batch/create")
async def create_batch_migration(
    batch_name: str,
    sql_files: List[Dict[str, Any]],
    source_config: Dict[str, Any],
    target_config: Dict[str, Any],
    migration_options: Dict[str, Any] = {},
    project_id: int = 1,  # Default project for demo
    db: Session = Depends(get_db)
):
    """Create a batch migration from multiple SQL files - No auth required"""
    
    try:
        # Get or create a default user for demo purposes
        demo_user = db.query(User).filter(User.email == "demo@example.com").first()
        if not demo_user:
            demo_user = User(
                email="demo@example.com",
                username="demo",
                firebase_uid="demo_uid",
                full_name="Demo User",
                role=UserRole.ADMIN
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        
        result = await batch_migration_manager.create_batch_migration(
            db=db,
            user_id=demo_user.id,
            project_id=project_id,
            batch_name=batch_name,
            sql_files=sql_files,
            source_config=source_config,
            target_config=target_config,
            migration_options=migration_options
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating batch migration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create batch migration"
        )


@router.post("/batch/{batch_id}/start")
async def start_batch_migration(
    batch_id: str,
    migration_ids: List[str],
    config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Start a batch migration process - No auth required"""
    
    try:
        # Get or create a default user for demo purposes
        demo_user = db.query(User).filter(User.email == "demo@example.com").first()
        if not demo_user:
            demo_user = User(
                email="demo@example.com",
                username="demo",
                firebase_uid="demo_uid",
                full_name="Demo User",
                role=UserRole.ADMIN
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        
        config["user_id"] = demo_user.id
        
        result = await batch_migration_manager.start_batch_migration(
            db=db,
            batch_id=batch_id,
            migration_ids=migration_ids,
            config=config
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error starting batch migration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start batch migration"
        )


@router.get("/batch/{batch_id}/progress")
async def get_batch_progress(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """Get progress of batch migration - No auth required"""
    
    try:
        progress = await batch_migration_manager.get_batch_progress(db, batch_id)
        return progress
        
    except Exception as e:
        logger.error(f"Error getting batch progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get batch progress"
        )


@router.post("/export")
async def export_migration_results(
    migration_ids: List[str],
    export_format: str = "zip",
    include_original: bool = True,
    include_translated: bool = True,
    include_reports: bool = True,
    db: Session = Depends(get_db)
):
    """Export migration results to various formats - No auth required"""
    
    try:
        export_path = await export_manager.export_migration_results(
            db=db,
            migration_ids=migration_ids,
            export_format=export_format,
            include_original=include_original,
            include_translated=include_translated,
            include_reports=include_reports
        )
        
        return {
            "export_path": export_path,
            "export_format": export_format,
            "migration_count": len(migration_ids),
            "message": "Export created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error exporting migration results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export migration results"
        )


@router.get("/history/{project_id}")
async def get_migration_history(
    project_id: int,
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get migration history with filtering options - No auth required"""
    
    try:
        # Get or create a default user for demo purposes
        demo_user = db.query(User).filter(User.email == "demo@example.com").first()
        if not demo_user:
            demo_user = User(
                email="demo@example.com",
                username="demo",
                firebase_uid="demo_uid",
                full_name="Demo User",
                role=UserRole.ADMIN
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        
        history = await history_manager.get_migration_history(
            db=db,
            project_id=project_id,
            user_id=demo_user.id,
            limit=limit,
            offset=offset,
            status_filter=status_filter,
            date_from=date_from,
            date_to=date_to
        )
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting migration history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get migration history"
        )


@router.post("/rollback/{migration_id}")
async def rollback_migration(
    migration_id: str,
    rollback_reason: str,
    db: Session = Depends(get_db)
):
    """Perform rollback for a migration - No auth required"""
    
    try:
        result = await history_manager.perform_rollback(
            db=db,
            migration_id=migration_id,
            rollback_reason=rollback_reason
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error performing rollback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform rollback"
        )


# Batch SQL Converter endpoint (NEW - Wizard-style conversion)
@router.post("/convert-sql-batch", response_model=BatchSQLConversionResponse)
async def convert_sql_batch(
    request: BatchSQLConversionRequest,
    db: Session = Depends(get_db)
):
    """
    Batch SQL conversion with automatic dialect detection
    
    Request body:
    {
        "files": [
            {
                "filename": "script.sql",
                "content": "CREATE TABLE...",
                "source_dialect": "mysql" (optional - will auto-detect if not provided)
            }
        ],
        "target_dialect": "snowflake",
        "conversion_options": {
            "optimization_level": "standard",
            "convert_schema": true,
            "convert_data": true,
            "keep_constraints": true,
            "optimize_code": true
        }
    }
    """
    
    try:
        logger.info(f"Starting batch SQL conversion: {len(request.files)} files to {request.target_dialect}")
        
        # Convert files to dict format expected by batch_converter
        files_data = [
            {
                "filename": file.filename,
                "content": file.content,
                "source_dialect": file.source_dialect
            }
            for file in request.files
        ]
        
        # Convert conversion_options to dict
        conversion_options = {}
        if request.conversion_options:
            conversion_options = request.conversion_options.dict()
        
        # Perform batch conversion
        result = await batch_converter.convert_batch(
            files=files_data,
            target_dialect=request.target_dialect,
            conversion_options=conversion_options
        )
        
        logger.info(f"Batch conversion completed: {result['success_count']} succeeded, {result['failure_count']} failed")
        
        return BatchSQLConversionResponse(
            success=True,
            message=f"Converted {result['success_count']} files successfully",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Batch SQL conversion failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch conversion failed: {str(e)}"
        )


@router.post("/detect-dialect", response_model=DialectDetectionResponse)
async def detect_sql_dialect(
    request: DialectDetectionRequest
):
    """
    Detect SQL dialect from content
    
    Returns:
    {
        "dialect": "mysql",
        "confidence": 85,
        "features": ["AUTO_INCREMENT", "ENGINE=InnoDB"],
        "reasoning": "Detected MySQL-specific syntax"
    }
    """
    
    try:
        result = await batch_converter.detect_sql_dialect(
            request.sql_content, 
            request.filename or "unknown.sql"
        )
        return DialectDetectionResponse(
            success=True,
            data=result
        )
        
    except Exception as e:
        logger.error(f"Dialect detection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dialect detection failed: {str(e)}"
        )


# Jobs API endpoints for polling status
@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get job status and results - No auth required"""
    
    try:
        # Get job
        job = db.query(Job).filter(
            Job.job_id == job_id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        response = {
            "job_id": job.job_id,
            "status": job.status.value if job.status else "unknown",
            "progress": job.progress,
            "current_step": job.current_step,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "completed_at": job.completed_at
        }
        
        # Add result if job is completed
        if job.status and job.status.value == "completed" and job.result:
            response["result"] = job.result
        
        # Add error if job failed
        if job.status and job.status.value == "failed" and job.error_message:
            response["error"] = job.error_message
            response["error_message"] = job.error_message
            
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job status"
        )