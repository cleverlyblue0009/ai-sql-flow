from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime

from ..database import get_db, User, Project, Connection, MigrationLog, Job
from ..auth import get_current_verified_user
from .schemas import (
    MigrationSetupRequest, MigrationResponse, ConnectionTestRequest,
    ConnectionTestResponse, SQLTranslationRequest, SQLTranslationResponse,
    MigrationProgressResponse, PerformanceAnalysisResponse, DatabaseListResponse,
    MigrationConfigRequest, MigrationStatusResponse
)
from .services import MigrationService, SQLTranslationService, ConnectionService
from .enterprise_features import batch_migration_manager, export_manager, history_manager
from .ai_translator import AITranslationEngine
from ..tasks.migration_tasks import start_migration_task_wrapper, translate_sql_task_wrapper, analyze_sql_schema_task_wrapper
from ..utils.audit import log_migration_action

router = APIRouter(prefix="/migration", tags=["SQL Migration"])
logger = logging.getLogger(__name__)

# Initialize services
migration_service = MigrationService()
translation_service = SQLTranslationService()
connection_service = ConnectionService()
ai_engine = AITranslationEngine()


@router.get("/databases", response_model=DatabaseListResponse)
async def get_supported_databases(
    current_user: User = Depends(get_current_verified_user)
):
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Test database connection with provided credentials"""
    
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
        
        # Log the test attempt
        await log_migration_action(
            db=db,
            user_id=current_user.id,
            action="connection_test",
            details={
                "connection_type": request.connection_type,
                "host": request.host,
                "port": request.port,
                "database": request.database,
                "success": test_result.success
            },
            success=test_result.success
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Set up a new migration project"""
    
    try:
        # Validate project ownership
        project = db.query(Project).filter(
            Project.id == request.project_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Create or get source connection
        source_connection = await connection_service.create_or_get_connection(
            db=db,
            user_id=current_user.id,
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
            user_id=current_user.id,
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
        
        # Log action
        await log_migration_action(
            db=db,
            user_id=current_user.id,
            action="migration_setup",
            project_id=request.project_id,
            details={
                "migration_id": migration_id,
                "source_type": request.source_config.connection_type,
                "target_type": request.target_config.connection_type
            },
            success=True
        )
        
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Translate SQL from source dialect to target dialect"""
    
    try:
        # Start translation job
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            job_type="sql_translation",
            name=f"SQL Translation: {request.source_dialect} to {request.target_dialect}",
            user_id=current_user.id,
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Start the migration process"""
    
    try:
        # Get migration log
        migration_log = db.query(MigrationLog).filter(
            MigrationLog.migration_id == migration_id
        ).join(Project).filter(
            Project.owner_id == current_user.id
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
            user_id=current_user.id,
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
        
        # Log action
        await log_migration_action(
            db=db,
            user_id=current_user.id,
            action="migration_start",
            project_id=migration_log.project_id,
            details={
                "migration_id": migration_id,
                "job_id": job_id,
                "config": config.dict()
            },
            success=True
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get migration progress and status"""
    
    try:
        # Get migration log
        migration_log = db.query(MigrationLog).filter(
            MigrationLog.migration_id == migration_id
        ).join(Project).filter(
            Project.owner_id == current_user.id
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get migration performance analysis"""
    
    try:
        # Get migration log
        migration_log = db.query(MigrationLog).filter(
            MigrationLog.migration_id == migration_id
        ).join(Project).filter(
            Project.owner_id == current_user.id
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get detailed migration status"""
    
    try:
        # Get migration log
        migration_log = db.query(MigrationLog).filter(
            MigrationLog.migration_id == migration_id
        ).join(Project).filter(
            Project.owner_id == current_user.id
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """List all migrations for a project"""
    
    try:
        # Validate project ownership
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
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

@router.post("/detect-dialect")
async def detect_sql_dialect(
    sql_content: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Detect SQL dialect using Gemini AI"""
    
    try:
        if not sql_content or not sql_content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SQL content cannot be empty"
            )
        
        # Use AI engine to detect dialect
        result = await ai_engine.detect_sql_dialect(sql_content)
        
        logger.info(f"Detected SQL dialect: {result['dialect']} with {result['confidence']}% confidence (method: {result['method']})")
        
        return {
            "success": True,
            "dialect": result["dialect"],
            "confidence": result["confidence"],
            "features": result["features"],
            "explanation": result["explanation"],
            "alternative_dialects": result.get("alternative_dialects", []),
            "detection_method": result["method"]
        }
        
    except Exception as e:
        logger.error(f"Error detecting SQL dialect: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect SQL dialect: {str(e)}"
        )


@router.post("/analyze-sql")
async def analyze_sql_schema(
    sql_content: str,
    source_dialect: str = "mysql",
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Analyze SQL schema and structure"""
    
    try:
        # Create analysis job
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            job_type="sql_analysis",
            name="SQL Schema Analysis",
            user_id=current_user.id,
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Create a batch migration from multiple SQL files"""
    
    try:
        result = await batch_migration_manager.create_batch_migration(
            db=db,
            user_id=current_user.id,
            project_id=project_id,
            batch_name=batch_name,
            sql_files=sql_files,
            source_config=source_config,
            target_config=target_config,
            migration_options=migration_options
        )
        
        # Log action
        await log_migration_action(
            db=db,
            user_id=current_user.id,
            action="batch_migration_created",
            project_id=project_id,
            details={
                "batch_id": result["batch_id"],
                "file_count": len(sql_files)
            },
            success=True
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Start a batch migration process"""
    
    try:
        config["user_id"] = current_user.id
        
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get progress of batch migration"""
    
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Export migration results to various formats"""
    
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get migration history with filtering options"""
    
    try:
        # Verify project access
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        history = await history_manager.get_migration_history(
            db=db,
            project_id=project_id,
            user_id=current_user.id,
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
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Perform rollback for a migration"""
    
    try:
        result = await history_manager.perform_rollback(
            db=db,
            migration_id=migration_id,
            rollback_reason=rollback_reason
        )
        
        # Log action
        await log_migration_action(
            db=db,
            user_id=current_user.id,
            action="migration_rollback",
            details={
                "migration_id": migration_id,
                "reason": rollback_reason
            },
            success=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error performing rollback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform rollback"
        )


# Jobs API endpoints for polling status
@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get job status and results"""
    
    try:
        # Get job
        job = db.query(Job).filter(
            Job.job_id == job_id,
            Job.user_id == current_user.id
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