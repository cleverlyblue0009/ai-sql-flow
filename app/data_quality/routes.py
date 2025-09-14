from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
import io
import uuid
from datetime import datetime
import logging

from ..database.config import get_db
from ..database.models import User, Project, DataProfile, Job
from .schemas import (
    DataUploadRequest, DataAnalysisRequest, DataCleaningRequest,
    DataProfileResponse, DataCleaningResult, JobStatusResponse, DataQualityReport
)
from .analyzer import DataQualityAnalyzer

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])
logger = logging.getLogger(__name__)

# Initialize analyzer
analyzer = DataQualityAnalyzer()

# Temporary mock user for testing (replace when auth is implemented)
class MockUser:
    def __init__(self):
        self.id = 1
        self.email = "test@example.com"
        self.username = "testuser"

def get_current_user():
    """Temporary mock user function - replace with real authentication"""
    return MockUser()


@router.post("/upload", response_model=Dict[str, Any])
async def upload_data_file(
    file: UploadFile = File(...),
    project_id: Optional[int] = Form(None),
    file_format: str = Form("auto"),
    delimiter: str = Form(","),
    encoding: str = Form("utf-8"),
    has_header: bool = Form(True),
    sample_rows: Optional[int] = Form(1000),
    current_user: MockUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process data file for quality analysis"""
    
    try:
        # Create default project if none specified
        if project_id is None:
            project = Project(
                name=f"Data Quality Project - {file.filename}",
                description=f"Auto-created project for {file.filename}",
                owner_id=current_user.id,
                settings={}
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            project_id = project.id
        else:
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
        
        # Auto-detect file format if needed
        if file_format == "auto":
            file_format = _detect_file_format(file.filename)
        
        # Read and analyze file
        try:
            df = await _read_file(file_content, file_format, delimiter, encoding, has_header)
            logger.info(f"Successfully read file: {len(df)} rows, {len(df.columns)} columns")
        except Exception as e:
            logger.error(f"Failed to read file {file.filename}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read {file_format} file '{file.filename}': {str(e)}. Please ensure the file is not corrupted and in the correct format."
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
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post("/analyze", response_model=Dict[str, str])
async def analyze_data_quality(
    request: DataAnalysisRequest,
    current_user: MockUser = Depends(get_current_user),
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


@router.get("/recent-uploads", response_model=List[Dict[str, Any]])
async def get_recent_uploads(
    limit: int = 10,
    current_user: MockUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent file uploads for the current user"""
    
    try:
        logger.info(f"Getting recent uploads for user {current_user.id}")
        
        # Get recent data profiles for user's projects
        recent_profiles = (
            db.query(DataProfile)
            .join(Project)
            .filter(Project.owner_id == current_user.id)
            .order_by(DataProfile.created_at.desc())
            .limit(limit)
            .all()
        )
        
        logger.info(f"Found {len(recent_profiles)} recent profiles")
        
        uploads = []
        for profile in recent_profiles:
            # Get the latest job for this profile using JSON operations
            latest_job = (
                db.query(Job)
                .filter(Job.parameters.contains({"data_profile_id": profile.id}))
                .order_by(Job.created_at.desc())
                .first()
            )
            
            status_value = "pending"
            if latest_job:
                status_value = latest_job.status.value
            
            uploads.append({
                "id": profile.id,
                "name": profile.source_name,
                "size": f"{profile.file_size / (1024*1024):.1f} MB" if profile.file_size else "Unknown",
                "date": profile.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "status": status_value,
                "rows": profile.row_count or 0,
                "columns": profile.column_count or 0,
                "quality_score": profile.overall_quality_score
            })
        
        logger.info(f"Returning {len(uploads)} uploads")
        return uploads
        
    except Exception as e:
        logger.error(f"Error getting recent uploads: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent uploads: {str(e)}"
        )


@router.get("/quality-summary/{data_profile_id}", response_model=Dict[str, Any])
async def get_quality_summary(
    data_profile_id: int,
    current_user: MockUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quality assessment summary for a data profile"""
    
    try:
        # Validate data profile ownership
        data_profile = db.query(DataProfile).join(Project).filter(
            DataProfile.id == data_profile_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not data_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data profile not found"
            )
        
        # Return mock data for now (replace with real data when analysis is implemented)
        quality_metrics = {
            "completeness": {
                "score": 92.5,
                "issues": 127,
                "status": "good",
                "description": "Missing values detected in 3 columns"
            },
            "accuracy": {
                "score": 89.3,
                "issues": 203,
                "status": "warning", 
                "description": "Format inconsistencies in date fields"
            },
            "consistency": {
                "score": 96.1,
                "issues": 45,
                "status": "excellent",
                "description": "Minor duplicate records found"
            },
            "validity": {
                "score": 87.8,
                "issues": 156,
                "status": "warning",
                "description": "Invalid email formats detected"
            }
        }
        
        # Use real data if available
        if data_profile.completeness_score is not None:
            quality_metrics["completeness"]["score"] = data_profile.completeness_score
        if data_profile.accuracy_score is not None:
            quality_metrics["accuracy"]["score"] = data_profile.accuracy_score
        if data_profile.consistency_score is not None:
            quality_metrics["consistency"]["score"] = data_profile.consistency_score
        if data_profile.validity_score is not None:
            quality_metrics["validity"]["score"] = data_profile.validity_score
        
        issue_breakdown = [
            {"type": "Duplicates", "count": 1247, "severity": "medium"},
            {"type": "Missing Values", "count": 892, "severity": "high"},
            {"type": "Outliers", "count": 234, "severity": "low"},
            {"type": "Format Issues", "count": 567, "severity": "medium"},
            {"type": "Invalid References", "count": 89, "severity": "high"}
        ]
        
        return {
            "data_profile_id": data_profile_id,
            "file_name": data_profile.source_name,
            "overall_quality_score": data_profile.overall_quality_score or 76.3,
            "quality_metrics": quality_metrics,
            "issue_breakdown": issue_breakdown,
            "last_analyzed": data_profile.updated_at.isoformat() if data_profile.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quality summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get quality summary"
        )


@router.post("/clean", response_model=Dict[str, Any])
async def start_data_cleaning(
    request: DataCleaningRequest,
    current_user: MockUser = Depends(get_current_user),
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
            project_id=data_profile.project_id,
            parameters={
                "data_profile_id": request.data_profile_id,
                "cleaning_operations": request.cleaning_operations,
                "preview_only": request.preview_only
            }
        )
        
        db.add(job)
        db.commit()
        
        return {
            "message": "Data cleaning started",
            "job_id": job_id,
            "preview_only": request.preview_only
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting data cleaning: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start data cleaning"
        )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: MockUser = Depends(get_current_user),
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
            estimated_completion=None,
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


# Helper functions
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
        elif file_format.lower() in ["xlsx", "excel", "xls"]:
            try:
                df = pd.read_excel(file_stream, header=0 if has_header else None, engine='openpyxl')
            except Exception as e:
                # Try with different engines if openpyxl fails
                file_stream.seek(0)  # Reset stream position
                try:
                    df = pd.read_excel(file_stream, header=0 if has_header else None)
                except Exception as e2:
                    raise ValueError(f"Failed to read Excel file with both openpyxl and default engines: {str(e)}, {str(e2)}")
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


def _detect_file_format(filename: str) -> str:
    """Detect file format from filename extension"""
    
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    format_mapping = {
        'csv': 'csv',
        'xlsx': 'xlsx',  # Use xlsx specifically for pandas
        'xls': 'xlsx',   # Treat xls as xlsx for pandas
        'json': 'json',
        'parquet': 'parquet',
        'tsv': 'tsv',
        'txt': 'csv'  # Assume txt files are CSV
    }
    
    return format_mapping.get(extension, 'csv')