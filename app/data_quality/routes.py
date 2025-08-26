from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
import io
import uuid
from datetime import datetime
import logging

from ..database import get_db, User, Project, DataProfile, Job
from ..auth import get_current_verified_user
from .schemas import (
    DataUploadRequest, DataAnalysisRequest, DataCleaningRequest,
    DataProfileResponse, DataCleaningResult, JobStatusResponse, DataQualityReport
)
from .analyzer import DataQualityAnalyzer
from .cleaner import DataCleaner
from ..tasks.data_quality_tasks import (
    analyze_data_quality_task, clean_data_task, generate_report_task
)
from ..utils.file_storage import FileStorageManager
from ..utils.audit import log_data_quality_action

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])
logger = logging.getLogger(__name__)

# Initialize components
analyzer = DataQualityAnalyzer()
cleaner = DataCleaner()
storage_manager = FileStorageManager()


@router.post("/upload", response_model=Dict[str, Any])
async def upload_data_file(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    file_format: str = Form("csv"),
    delimiter: str = Form(","),
    encoding: str = Form("utf-8"),
    has_header: bool = Form(True),
    sample_rows: Optional[int] = Form(1000),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Upload and process data file for quality analysis"""
    
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
        
        # Validate file size
        file_size = 0
        file_content = await file.read()
        file_size = len(file_content)
        
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {max_size // (1024*1024)}MB"
            )
        
        # Generate unique file path
        file_id = str(uuid.uuid4())
        file_path = f"data/{current_user.id}/{project_id}/{file_id}_{file.filename}"
        
        # Store file
        await storage_manager.upload_file(file_content, file_path)
        
        # Read and analyze file
        try:
            df = await _read_file(file_content, file_format, delimiter, encoding, has_header)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read file: {str(e)}"
            )
        
        # Create data profile
        data_profile = DataProfile(
            project_id=project_id,
            source_name=file.filename,
            source_type="file",
            file_path=file_path,
            file_size=file_size,
            column_count=len(df.columns),
            row_count=len(df),
            schema_info={
                "columns": [{"name": col, "dtype": str(df[col].dtype)} for col in df.columns]
            }
        )
        
        db.add(data_profile)
        db.commit()
        db.refresh(data_profile)
        
        # Create background job for initial analysis
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            job_type="data_upload",
            name=f"Upload and analyze {file.filename}",
            user_id=current_user.id,
            project_id=project_id,
            parameters={
                "data_profile_id": data_profile.id,
                "file_path": file_path,
                "sample_rows": sample_rows
            }
        )
        
        db.add(job)
        db.commit()
        
        # Start background analysis
        analyze_data_quality_task.delay(
            data_profile_id=data_profile.id,
            job_id=job_id,
            sample_size=sample_rows
        )
        
        # Log action
        log_data_quality_action(
            db=db,
            user_id=current_user.id,
            action="file_upload",
            project_id=project_id,
            file_name=file.filename,
            details={"file_size": file_size, "rows": len(df), "columns": len(df.columns)},
            success=True
        )
        
        return {
            "message": "File uploaded successfully",
            "data_profile_id": data_profile.id,
            "job_id": job_id,
            "file_info": {
                "name": file.filename,
                "size": file_size,
                "rows": len(df),
                "columns": len(df.columns)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


@router.post("/analyze", response_model=Dict[str, str])
async def analyze_data_quality(
    request: DataAnalysisRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Start comprehensive data quality analysis"""
    
    try:
        # Validate data profile ownership
        data_profile = db.query(DataProfile).join(Project).filter(
            DataProfile.id == request.data_profile_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not data_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data profile not found"
            )
        
        # Create analysis job
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            job_type="data_analysis",
            name=f"Analyze {data_profile.source_name}",
            user_id=current_user.id,
            project_id=request.project_id,
            parameters={
                "data_profile_id": request.data_profile_id,
                "analysis_types": request.analysis_types,
                "ai_enabled": request.ai_enabled,
                "sample_size": request.sample_size
            }
        )
        
        db.add(job)
        db.commit()
        
        # Start background analysis
        analyze_data_quality_task.delay(
            data_profile_id=request.data_profile_id,
            job_id=job_id,
            analysis_types=request.analysis_types,
            ai_enabled=request.ai_enabled,
            sample_size=request.sample_size
        )
        
        # Log action
        log_data_quality_action(
            db=db,
            user_id=current_user.id,
            action="data_analysis_start",
            project_id=request.project_id,
            details={"analysis_types": request.analysis_types, "ai_enabled": request.ai_enabled},
            success=True
        )
        
        return {
            "message": "Data quality analysis started",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start analysis"
        )


@router.get("/report/{job_id}", response_model=DataQualityReport)
async def get_quality_report(
    job_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive data quality report"""
    
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
        
        if job.status.value != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job not completed. Current status: {job.status.value}"
            )
        
        # Get data profile
        data_profile_id = job.parameters.get("data_profile_id")
        data_profile = db.query(DataProfile).filter(DataProfile.id == data_profile_id).first()
        
        if not data_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data profile not found"
            )
        
        # Build report from stored results
        report = DataQualityReport(
            job_id=job_id,
            project_id=job.project_id,
            data_profile_id=data_profile.id,
            generated_at=datetime.utcnow(),
            summary={
                "file_name": data_profile.source_name,
                "rows": data_profile.row_count,
                "columns": data_profile.column_count,
                "file_size": data_profile.file_size,
                "overall_quality": data_profile.overall_quality_score
            },
            quality_metrics=data_profile.column_profiles or {},
            column_analysis=data_profile.column_profiles or [],
            issues_found=job.result.get("issues", []) if job.result else [],
            ai_insights=data_profile.ai_recommendations,
            recommendations=data_profile.cleaning_suggestions,
            charts=job.result.get("charts") if job.result else None
        )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get report"
        )


@router.post("/clean", response_model=Dict[str, str])
async def clean_data(
    request: DataCleaningRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Start data cleaning process"""
    
    try:
        # Validate data profile ownership
        data_profile = db.query(DataProfile).join(Project).filter(
            DataProfile.id == request.data_profile_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not data_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data profile not found"
            )
        
        # Create cleaning job
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            job_type="data_cleaning",
            name=f"Clean {data_profile.source_name}",
            user_id=current_user.id,
            project_id=request.project_id,
            parameters={
                "data_profile_id": request.data_profile_id,
                "cleaning_operations": request.cleaning_operations,
                "preview_only": request.preview_only
            }
        )
        
        db.add(job)
        db.commit()
        
        # Start background cleaning
        clean_data_task.delay(
            data_profile_id=request.data_profile_id,
            job_id=job_id,
            cleaning_operations=request.cleaning_operations,
            preview_only=request.preview_only
        )
        
        # Log action
        log_data_quality_action(
            db=db,
            user_id=current_user.id,
            action="data_cleaning_start",
            project_id=request.project_id,
            details={
                "operations": [op["operation"] for op in request.cleaning_operations],
                "preview_only": request.preview_only
            },
            success=True
        )
        
        return {
            "message": "Data cleaning started",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting cleaning: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start cleaning"
        )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get job status and progress"""
    
    try:
        job = db.query(Job).filter(
            Job.job_id == job_id,
            Job.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status.value,
            progress_percentage=job.progress_percentage,
            current_step=job.current_step,
            total_steps=job.total_steps,
            started_at=job.started_at,
            estimated_completion=None,  # Could be calculated based on progress
            result=job.result,
            error_message=job.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job status"
        )


@router.get("/profiles/{project_id}", response_model=List[DataProfileResponse])
async def list_data_profiles(
    project_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """List all data profiles for a project"""
    
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
        
        # Get data profiles
        profiles = db.query(DataProfile).filter(
            DataProfile.project_id == project_id
        ).order_by(DataProfile.created_at.desc()).all()
        
        return profiles
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing profiles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list profiles"
        )


@router.get("/download/{job_id}")
async def download_cleaned_data(
    job_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Download cleaned data file"""
    
    try:
        # Get job
        job = db.query(Job).filter(
            Job.job_id == job_id,
            Job.user_id == current_user.id,
            Job.job_type == "data_cleaning"
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cleaning job not found"
            )
        
        if job.status.value != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cleaning job not completed"
            )
        
        # Get cleaned file path from job result
        if not job.result or "cleaned_file_path" not in job.result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cleaned file not found"
            )
        
        cleaned_file_path = job.result["cleaned_file_path"]
        
        # Download file from storage
        file_content = await storage_manager.download_file(cleaned_file_path)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename=cleaned_{job.name}.csv"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )


async def _read_file(
    file_content: bytes, 
    file_format: str, 
    delimiter: str, 
    encoding: str, 
    has_header: bool
) -> pd.DataFrame:
    """Read file content into DataFrame"""
    
    file_stream = io.BytesIO(file_content)
    
    try:
        if file_format.lower() == "csv":
            df = pd.read_csv(
                file_stream,
                delimiter=delimiter,
                encoding=encoding,
                header=0 if has_header else None
            )
        elif file_format.lower() in ["xlsx", "excel"]:
            df = pd.read_excel(file_stream, header=0 if has_header else None)
        elif file_format.lower() == "json":
            df = pd.read_json(file_stream, encoding=encoding)
        elif file_format.lower() == "parquet":
            df = pd.read_parquet(file_stream)
        elif file_format.lower() == "tsv":
            df = pd.read_csv(
                file_stream,
                delimiter='\t',
                encoding=encoding,
                header=0 if has_header else None
            )
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        return df
        
    except Exception as e:
        raise ValueError(f"Failed to read {file_format} file: {str(e)}")