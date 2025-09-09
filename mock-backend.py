#!/usr/bin/env python3
"""
Simple mock backend for DataFlow AI Platform demo
This provides realistic mock data for the frontend to demonstrate functionality.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import random
import json
from datetime import datetime, timedelta

app = FastAPI(
    title="DataFlow AI Platform Mock API",
    description="Mock backend for demonstration purposes",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mock data
MOCK_METRICS = {
    "data_quality_score": 94.2,
    "active_migrations": 12,
    "success_rate": 99.1,
    "cost_savings": 2400000,  # $2.4M
    "tables_processed_today": 1247,
    "change_data_quality": "+2.4%",
    "change_migrations": "+3",
    "change_success_rate": "+0.5%",
    "change_cost_savings": "+$340K"
}

MOCK_ACTIVITIES = [
    {
        "id": 1,
        "type": "migration",
        "title": "PostgreSQL to Snowflake migration completed",
        "description": "Successfully migrated customer_data table with 2.3M records",
        "timestamp": "2 minutes ago",
        "status": "success",
        "user": "admin@company.com"
    },
    {
        "id": 2,
        "type": "quality",
        "title": "Data quality check started for customer_data table",
        "description": "Analyzing 1.2M records for completeness and accuracy",
        "timestamp": "15 minutes ago",
        "status": "running",
        "user": "data.engineer@company.com"
    },
    {
        "id": 3,
        "type": "alert",
        "title": "Schema validation warning in orders table",
        "description": "Detected potential data type mismatches in 3 columns",
        "timestamp": "1 hour ago",
        "status": "warning",
        "user": "db.admin@company.com"
    },
    {
        "id": 4,
        "type": "success",
        "title": "Performance optimization applied",
        "description": "Query execution time improved by 67%",
        "timestamp": "2 hours ago",
        "status": "success",
        "user": "system"
    }
]

MOCK_SYSTEM_STATUS = {
    "overall_health": 97.8,
    "services": [
        {"name": "Data Processing Engine", "status": "operational", "uptime": "99.9%", "response_time": "245ms"},
        {"name": "SQL Translation API", "status": "operational", "uptime": "99.7%", "response_time": "189ms"},
        {"name": "Quality Assessment", "status": "degraded", "uptime": "97.2%", "response_time": "1.2s"},
        {"name": "Migration Workers", "status": "operational", "uptime": "99.8%", "response_time": "567ms"}
    ],
    "performance": {
        "cpu_usage": 68,
        "memory_usage": 74,
        "storage_usage": 45,
        "active_users": 247
    }
}

MOCK_UPLOADS = [
    {
        "id": "upload_1",
        "name": "customer_data.csv",
        "size": "15.2 MB",
        "upload_date": "2 hours ago",
        "status": "analyzed"
    },
    {
        "id": "upload_2", 
        "name": "transactions.xlsx",
        "size": "8.7 MB",
        "upload_date": "1 day ago",
        "status": "cleaned"
    },
    {
        "id": "upload_3",
        "name": "user_profiles.json", 
        "size": "3.1 MB",
        "upload_date": "3 days ago",
        "status": "pending"
    }
]

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time(),
        "database": "connected",
        "redis": "connected",
        "services": {
            "authentication": "operational",
            "data_quality": "operational",
            "background_tasks": "operational"
        }
    }

# System info endpoint
@app.get("/info")
async def system_info():
    return {
        "name": "DataFlow AI Platform Mock API",
        "version": "1.0.0",
        "description": "Mock backend for demonstration purposes",
        "capabilities": {
            "authentication": {"jwt_auth": True, "oauth2": True},
            "data_quality": {"ai_analysis": True, "duplicate_detection": True},
            "file_processing": {"supported_formats": ["CSV", "Excel", "JSON"]},
        }
    }

# Dashboard endpoints
@app.get("/dashboard/overview")
async def get_dashboard_overview():
    # Add some randomness to make it feel more real
    metrics = MOCK_METRICS.copy()
    metrics["data_quality_score"] += random.uniform(-0.5, 0.5)
    metrics["active_migrations"] += random.randint(-2, 3)
    metrics["success_rate"] += random.uniform(-0.2, 0.2)
    
    return {
        "metrics": metrics,
        "activities": MOCK_ACTIVITIES,
        "quick_stats": {
            "files_uploaded_today": 23,
            "active_processes": 12,
            "avg_processing_time": 847,
            "error_rate": 0.8
        },
        "system_status": MOCK_SYSTEM_STATUS
    }

@app.get("/dashboard/metrics")
async def get_dashboard_metrics():
    metrics = MOCK_METRICS.copy()
    metrics["data_quality_score"] += random.uniform(-0.5, 0.5)
    return metrics

@app.get("/dashboard/activities")
async def get_dashboard_activities(limit: int = 20):
    return {"activities": MOCK_ACTIVITIES[:limit], "total": len(MOCK_ACTIVITIES)}

@app.get("/dashboard/system-status")
async def get_system_status():
    return MOCK_SYSTEM_STATUS

# Data Quality endpoints
@app.get("/data-quality/uploads")
async def get_recent_uploads(limit: int = 10):
    return MOCK_UPLOADS[:limit]

@app.post("/data-quality/upload")
async def upload_file():
    # Simulate file upload
    upload_id = f"upload_{int(time.time())}"
    return {
        "id": upload_id,
        "status": "uploaded",
        "message": "File uploaded successfully and analysis started",
        "analysis_id": f"analysis_{upload_id}"
    }

@app.post("/data-quality/clean/{file_id}")
async def start_cleaning(file_id: str):
    job_id = f"job_{int(time.time())}"
    return {
        "job_id": job_id,
        "status": "started",
        "message": "Cleaning process initiated",
        "estimated_time": "5-10 minutes"
    }

# Migration endpoints
@app.get("/migration/active")
async def get_active_migrations():
    return [
        {
            "id": "mig_001",
            "source": "MySQL",
            "target": "Snowflake", 
            "status": "running",
            "progress": 67,
            "started_at": "2024-01-09T10:30:00Z"
        },
        {
            "id": "mig_002",
            "source": "PostgreSQL",
            "target": "Redshift",
            "status": "pending",
            "progress": 0,
            "started_at": None
        }
    ]

@app.post("/migration/start")
async def start_migration():
    migration_id = f"mig_{int(time.time())}"
    return {
        "migration_id": migration_id,
        "status": "started",
        "message": "Migration process initiated"
    }

@app.post("/migration/translate")
async def translate_sql():
    return {
        "translated_sql": "-- Translated SQL would appear here",
        "status": "success",
        "optimizations_applied": ["Index hints removed", "Date functions converted"]
    }

# Error handler
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Not Found",
        "message": f"Endpoint not found: {request.url.path}",
        "available_endpoints": ["/health", "/dashboard/overview", "/data-quality/uploads"]
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "DataFlow AI Platform Mock API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting DataFlow AI Platform Mock Backend...")
    print("📊 Dashboard data will be served with realistic mock values")
    print("🔗 Frontend should connect to http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)