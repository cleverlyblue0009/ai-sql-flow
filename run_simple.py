#!/usr/bin/env python3
"""
Simple FastAPI server runner with minimal dependencies for testing the fixes.
This script attempts to start the server with fallbacks for missing dependencies.
"""

import sys
import os
import time
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add workspace to path
sys.path.insert(0, '/workspace')

# Try to import FastAPI and related modules
try:
    from fastapi import FastAPI, HTTPException, status, File, UploadFile, Form
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError as e:
    print(f"FastAPI not available: {e}")
    FASTAPI_AVAILABLE = False

# Try to import pandas for file processing
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    print("Pandas not available - file processing will use mock data")
    PANDAS_AVAILABLE = False

def create_minimal_app():
    """Create a minimal FastAPI app with the fixed endpoints"""
    
    if not FASTAPI_AVAILABLE:
        print("Cannot create app - FastAPI not available")
        return None
    
    app = FastAPI(
        title="Data Quality API - Test Mode",
        description="Minimal version for testing the fixes",
        version="1.0.0-test"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "success",
            "data": {
                "status": "healthy",
                "version": "1.0.0-test",
                "timestamp": time.time(),
                "services": {
                    "data_quality": "operational",
                    "file_processing": "operational" if PANDAS_AVAILABLE else "mock_mode"
                }
            }
        }
    
    # Recent uploads endpoint
    @app.get("/data-quality/recent-uploads")
    async def get_recent_uploads(limit: int = 10):
        """Get recent file uploads"""
        mock_uploads = [
            {
                "id": 1,
                "name": "sales_data_2024.csv",
                "size": "2.3 MB",
                "date": "2024-01-15 14:30:00",
                "status": "completed",
                "rows": 15420,
                "columns": 8,
                "quality_score": 92.5
            },
            {
                "id": 2,
                "name": "customer_records.xlsx",
                "size": "5.7 MB",
                "date": "2024-01-14 09:15:00",
                "status": "completed",
                "rows": 28750,
                "columns": 12,
                "quality_score": 87.3
            },
            {
                "id": 3,
                "name": "inventory_data.json",
                "size": "1.2 MB",
                "date": "2024-01-13 16:45:00",
                "status": "analyzing",
                "rows": 8930,
                "columns": 6,
                "quality_score": None
            }
        ]
        
        return {
            "status": "success",
            "data": mock_uploads[:limit]
        }
    
    # File upload endpoint
    @app.post("/data-quality/upload")
    async def upload_file(
        file: UploadFile = File(...),
        file_format: str = Form("auto"),
        delimiter: str = Form(","),
        encoding: str = Form("utf-8"),
        has_header: bool = Form(True)
    ):
        """Upload and analyze file"""
        
        try:
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            
            # Validate file size
            max_size = 100 * 1024 * 1024  # 100MB
            if file_size > max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Maximum size is {max_size // (1024*1024)}MB"
                )
            
            # Auto-detect file format
            if file_format == "auto":
                extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
                format_mapping = {
                    'csv': 'csv',
                    'xlsx': 'excel',
                    'xls': 'excel',
                    'json': 'json',
                    'parquet': 'parquet',
                    'tsv': 'tsv'
                }
                file_format = format_mapping.get(extension, 'csv')
            
            if PANDAS_AVAILABLE:
                # Process file with pandas
                try:
                    import io
                    file_stream = io.BytesIO(file_content)
                    
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
                    else:
                        # Default to CSV
                        df = pd.read_csv(
                            file_stream,
                            delimiter=delimiter,
                            encoding=encoding,
                            header=0 if has_header else None
                        )
                    
                    # Calculate quality metrics
                    total_cells = len(df) * len(df.columns)
                    missing_cells = df.isnull().sum().sum()
                    completeness = ((total_cells - missing_cells) / total_cells * 100) if total_cells > 0 else 0
                    
                    # Column analysis
                    column_analysis = []
                    for col in df.columns:
                        col_data = df[col]
                        column_analysis.append({
                            "name": col,
                            "data_type": str(col_data.dtype),
                            "null_count": int(col_data.isnull().sum()),
                            "unique_count": int(col_data.nunique()),
                            "completeness": ((len(col_data) - col_data.isnull().sum()) / len(col_data) * 100) if len(col_data) > 0 else 0
                        })
                    
                    rows = len(df)
                    columns = len(df.columns)
                    
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to process file: {str(e)}"
                    )
            else:
                # Mock processing without pandas
                rows = 1000
                columns = 5
                completeness = 95.0
                missing_cells = 25
                column_analysis = [
                    {"name": "column_1", "data_type": "object", "null_count": 5, "unique_count": 950, "completeness": 99.5},
                    {"name": "column_2", "data_type": "int64", "null_count": 0, "unique_count": 1000, "completeness": 100.0},
                    {"name": "column_3", "data_type": "float64", "null_count": 10, "unique_count": 990, "completeness": 99.0},
                    {"name": "column_4", "data_type": "object", "null_count": 8, "unique_count": 15, "completeness": 99.2},
                    {"name": "column_5", "data_type": "datetime64[ns]", "null_count": 2, "unique_count": 998, "completeness": 99.8}
                ]
            
            return {
                "status": "success",
                "message": "File uploaded and analyzed successfully",
                "data": {
                    "upload_id": f"upload_{int(time.time())}",
                    "file_info": {
                        "name": file.filename,
                        "size": file_size,
                        "format": file_format,
                        "rows": rows,
                        "columns": columns
                    },
                    "quality_summary": {
                        "overall_completeness": round(completeness, 2),
                        "total_missing_values": int(missing_cells),
                        "processing_mode": "pandas" if PANDAS_AVAILABLE else "mock"
                    },
                    "column_analysis": column_analysis[:10]
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    # Analysis endpoint
    @app.post("/data-quality/analyze")
    async def analyze_data():
        """Start data quality analysis"""
        return {
            "status": "success",
            "message": "Data quality analysis started",
            "data": {
                "job_id": f"job_{int(time.time())}",
                "analysis_types": ["completeness", "accuracy", "consistency"],
                "estimated_completion": "2-5 minutes",
                "status": "running"
            }
        }
    
    return app

def main():
    """Main function to start the server"""
    print("Starting minimal FastAPI server for testing...")
    
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI is not available. Please install FastAPI to run the server.")
        print("   Try: pip install fastapi uvicorn")
        return 1
    
    app = create_minimal_app()
    if app is None:
        return 1
    
    print("✅ Server created successfully")
    print("🌐 Available endpoints:")
    print("   - GET  /health")
    print("   - GET  /data-quality/recent-uploads")
    print("   - POST /data-quality/upload")
    print("   - POST /data-quality/analyze")
    print("   - GET  /docs (API documentation)")
    print()
    print("🚀 Starting server on http://localhost:8000")
    print("   Press Ctrl+C to stop")
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        return 0
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())