#!/usr/bin/env python3
"""
Simple startup script for DataFlow AI platform (development mode)
"""

import uvicorn
import os
from pathlib import Path

# Set environment variables
os.environ["PYTHONPATH"] = str(Path(__file__).parent)

# Simple FastAPI app without complex dependencies
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

app = FastAPI(
    title="DataFlow AI - Development Mode",
    description="Simplified version for development",
    version="1.0.0-dev"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "DataFlow AI Development Server", "status": "running"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "mode": "development"
    }

# Mock endpoints for frontend
@app.get("/data-quality/recent-uploads")
async def get_recent_uploads():
    return {
        "status": "success",
        "data": [
            {
                "id": 1,
                "name": "customer_data.csv",
                "size": "15.2 MB",
                "date": "2 hours ago",
                "status": "analyzed",
                "rows": 10000,
                "columns": 15,
                "quality_score": 94.2
            }
        ]
    }

@app.get("/dashboard/comprehensive-overview")
async def get_dashboard_overview():
    return {
        "status": "success",
        "data": {
            "timestamp": time.time(),
            "summary": {
                "total_projects": 3,
                "total_data_profiles": 12,
                "recent_activity_count": 23,
                "success_rate": 99.1,
                "avg_quality_score": 94.2,
                "cost_savings": 2340.0
            }
        }
    }

@app.get("/monitoring/system")
async def get_system_metrics():
    return {
        "status": "success",
        "data": {
            "timestamp": time.time(),
            "cpu": {"usage_percent": 45.2, "status": "healthy"},
            "memory": {"usage_percent": 62.1, "status": "healthy"},
            "disk": {"usage_percent": 23.4, "status": "healthy"}
        }
    }

if __name__ == "__main__":
    print("🚀 Starting DataFlow AI Development Server...")
    print("📍 Backend will be available at: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop")
    
    uvicorn.run(
        "run_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )