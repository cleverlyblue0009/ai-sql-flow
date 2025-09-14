#!/usr/bin/env python3

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import io
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import time

app = FastAPI(title="Data Quality Management API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo
uploaded_files = {}
analysis_jobs = {}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time(),
        "services": {
            "data_quality": "operational"
        }
    }

@app.post("/data-quality/upload")
async def upload_file(
    file: UploadFile = File(...),
    file_format: str = Form("auto"),
    has_header: bool = Form(True),
    sample_rows: Optional[int] = Form(1000)
):
    try:
        # Read file content
        content = await file.read()
        
        # Try to read as DataFrame
        file_stream = io.BytesIO(content)
        
        if file.filename.lower().endswith('.csv'):
            df = pd.read_csv(file_stream, header=0 if has_header else None)
        elif file.filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_stream, header=0 if has_header else None)
        elif file.filename.lower().endswith('.json'):
            df = pd.read_json(file_stream)
        else:
            # Default to CSV
            df = pd.read_csv(file_stream, header=0 if has_header else None)
        
        # Generate IDs
        data_profile_id = len(uploaded_files) + 1
        job_id = str(uuid.uuid4())
        
        # Store file info
        file_info = {
            "id": data_profile_id,
            "name": file.filename,
            "size": len(content),
            "rows": len(df),
            "columns": len(df.columns),
            "uploaded_at": datetime.now().isoformat(),
            "dataframe": df
        }
        
        uploaded_files[data_profile_id] = file_info
        
        # Create mock analysis job
        analysis_jobs[job_id] = {
            "job_id": job_id,
            "status": "running",
            "progress_percentage": 0,
            "data_profile_id": data_profile_id,
            "started_at": datetime.now().isoformat()
        }
        
        return {
            "message": "File uploaded successfully",
            "data_profile_id": data_profile_id,
            "job_id": job_id,
            "file_info": {
                "name": file.filename,
                "size": len(content),
                "rows": len(df),
                "columns": len(df.columns)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")

@app.get("/data-quality/recent-uploads")
async def get_recent_uploads():
    uploads = []
    for file_info in uploaded_files.values():
        uploads.append({
            "id": file_info["id"],
            "name": file_info["name"],
            "size": f"{file_info['size'] / (1024*1024):.1f} MB",
            "date": file_info["uploaded_at"],
            "status": "analyzed",
            "rows": file_info["rows"],
            "columns": file_info["columns"],
            "quality_score": 85.5  # Mock score
        })
    
    return {"status": "success", "data": uploads}

@app.get("/data-quality/quality-summary/{data_profile_id}")
async def get_quality_summary(data_profile_id: int):
    if data_profile_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="Data profile not found")
    
    file_info = uploaded_files[data_profile_id]
    df = file_info["dataframe"]
    
    # Calculate real basic metrics
    total_cells = df.size
    non_null_cells = df.count().sum()
    completeness = (non_null_cells / total_cells) * 100 if total_cells > 0 else 0
    
    duplicate_rows = len(df) - len(df.drop_duplicates())
    uniqueness = ((len(df) - duplicate_rows) / len(df)) * 100 if len(df) > 0 else 100
    
    return {
        "data_profile_id": data_profile_id,
        "file_name": file_info["name"],
        "overall_quality_score": (completeness + uniqueness) / 2,
        "quality_metrics": {
            "completeness": {
                "score": completeness,
                "issues": total_cells - non_null_cells,
                "status": "good" if completeness > 90 else "warning",
                "description": f"Missing values detected in {df.isnull().sum().sum()} cells"
            },
            "accuracy": {
                "score": 89.3,
                "issues": 203,
                "status": "warning",
                "description": "Format inconsistencies detected"
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
                "description": "Invalid formats detected"
            }
        },
        "issue_breakdown": [
            {"type": "Duplicates", "count": duplicate_rows, "severity": "medium"},
            {"type": "Missing Values", "count": int(df.isnull().sum().sum()), "severity": "high"},
            {"type": "Outliers", "count": 234, "severity": "low"},
            {"type": "Format Issues", "count": 567, "severity": "medium"}
        ],
        "last_analyzed": datetime.now().isoformat()
    }

@app.post("/data-quality/analyze")
async def analyze_data(request: Dict[str, Any]):
    data_profile_id = request.get("data_profile_id")
    
    if data_profile_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="Data profile not found")
    
    job_id = str(uuid.uuid4())
    analysis_jobs[job_id] = {
        "job_id": job_id,
        "status": "running",
        "progress_percentage": 0,
        "data_profile_id": data_profile_id,
        "started_at": datetime.now().isoformat()
    }
    
    return {"message": "Analysis started", "job_id": job_id}

@app.post("/data-quality/clean")
async def start_cleaning(request: Dict[str, Any]):
    data_profile_id = request.get("data_profile_id")
    preview_only = request.get("preview_only", False)
    
    if data_profile_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="Data profile not found")
    
    if preview_only:
        return {
            "message": "Preview generated",
            "preview_only": True,
            "preview_data": "Mock preview data would be shown here"
        }
    
    job_id = str(uuid.uuid4())
    analysis_jobs[job_id] = {
        "job_id": job_id,
        "status": "running", 
        "progress_percentage": 0,
        "data_profile_id": data_profile_id,
        "started_at": datetime.now().isoformat()
    }
    
    return {"message": "Cleaning started", "job_id": job_id, "preview_only": False}

@app.get("/data-quality/status/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    
    # Simulate progress
    elapsed = (datetime.now() - datetime.fromisoformat(job["started_at"])).total_seconds()
    progress = min(100, int(elapsed * 10))  # 10% per second, complete in 10 seconds
    
    if progress >= 100:
        job["status"] = "completed"
        job["progress_percentage"] = 100
    else:
        job["progress_percentage"] = progress
    
    return job

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)