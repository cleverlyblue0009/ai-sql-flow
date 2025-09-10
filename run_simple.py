#!/usr/bin/env python3
"""
Simple startup script for DataFlow AI platform (development mode)
"""

import uvicorn
import os
from pathlib import Path
import time

# Set environment variables
os.environ["PYTHONPATH"] = str(Path(__file__).parent)

# Simple FastAPI app without complex dependencies
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="DataFlow AI - Development Mode",
    description="Simplified version for development",
    version="1.0.0-dev"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8000", "http://localhost:8081"],
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

# API endpoints that match your frontend expectations
@app.get("/api/dashboard")
async def get_dashboard():
    return {
        "tablesProcessedToday": 1247,
        "dataQualityScore": 94.2,
        "dataQualityChange": 2.4,
        "activeMigrations": 12,
        "activeMigrationsChange": 3,
        "successRate": 99.1,
        "successRateChange": 0.5,
        "costSavings": "2.4M",
        "costSavingsChange": "340K",
        "recentActivity": [
            {
                "id": 1,
                "type": "migration",
                "title": "PostgreSQL to Snowflake migration completed",
                "status": "success",
                "timestamp": "2 minutes ago"
            },
            {
                "id": 2,
                "type": "quality_check",
                "title": "Data quality check started for customer_data table",
                "status": "running",
                "timestamp": "15 minutes ago"
            },
            {
                "id": 3,
                "type": "validation",
                "title": "Schema validation warning in orders table",
                "status": "warning",
                "timestamp": "1 hour ago"
            }
        ]
    }

@app.get("/api/data-quality")
async def get_data_quality():
    return {
        "overallScore": 94.2,
        "recentUploads": [
            {
                "filename": "customer_data.csv",
                "size": "15.2 MB",
                "uploadTime": "2 hours ago",
                "status": "analyzed"
            }
        ],
        "qualityMetrics": {
            "completeness": 96.5,
            "accuracy": 92.1,
            "consistency": 94.8,
            "validity": 93.2
        }
    }

@app.get("/api/migrations")
async def get_migrations():
    return {
        "activeMigrations": 12,
        "completedMigrations": 45,
        "failedMigrations": 2,
        "migrations": [
            {
                "id": 1,
                "name": "PostgreSQL to Snowflake",
                "source": "PostgreSQL 12.0",
                "target": "Snowflake Latest",
                "status": "completed",
                "progress": 100,
                "startTime": "2024-01-15T10:00:00Z"
            },
            {
                "id": 2,
                "name": "MySQL to BigQuery",
                "source": "MySQL 8.0",
                "target": "BigQuery",
                "status": "in_progress",
                "progress": 65,
                "startTime": "2024-01-15T14:30:00Z"
            }
        ]
    }

@app.get("/api/monitoring")
async def get_monitoring():
    return {
        "activeProcesses": 23,
        "successRate": 99.2,
        "avgResponseTime": 847,
        "errorRate": 0.8,
        "systemStatus": [
            {
                "service": "Data Processing Engine",
                "status": "operational",
                "uptime": 99.9,
                "responseTime": 245
            },
            {
                "service": "SQL Translation API",
                "status": "operational",
                "uptime": 99.7,
                "responseTime": 189
            },
            {
                "service": "Quality Assessment",
                "status": "degraded",
                "uptime": 97.2,
                "responseTime": 1200
            },
            {
                "service": "Migration Workers",
                "status": "operational",
                "uptime": 99.8,
                "responseTime": 567
            }
        ],
        "alerts": [
            {
                "id": 1,
                "priority": "high",
                "title": "Quality Assessment Performance Degraded",
                "description": "Response times increased by 300% in the last hour",
                "timestamp": "5 minutes ago",
                "affectedComponent": "Quality Assessment Module"
            },
            {
                "id": 2,
                "priority": "medium",
                "title": "High Memory Usage Detected",
                "description": "Migration worker #3 consuming 85% memory",
                "timestamp": "12 minutes ago",
                "affectedComponent": "Migration Workers"
            }
        ]
    }

# Frontend-expected endpoints (matching the API calls from console errors)
@app.get("/data-quality/recent-uploads")
async def get_recent_uploads():
    return [
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

@app.get("/dashboard/comprehensive-overview")
async def get_dashboard_overview():
    return {
        "timestamp": time.time(),
        "summary": {
            "total_projects": 3,
            "total_data_profiles": 12,
            "recent_activity_count": 23,
            "success_rate": 99.1,
            "avg_quality_score": 94.2,
            "cost_savings": 2340.0
        },
        "tablesProcessedToday": 1247,
        "dataQualityScore": 94.2,
        "dataQualityChange": 2.4,
        "activeMigrations": 12,
        "activeMigrationsChange": 3,
        "successRate": 99.1,
        "successRateChange": 0.5,
        "costSavings": "2.4M",
        "costSavingsChange": "340K"
    }

@app.get("/monitoring/system")
async def get_system_metrics():
    return {
        "timestamp": time.time(),
        "cpu": {"usage_percent": 45.2, "status": "healthy"},
        "memory": {"usage_percent": 62.1, "status": "healthy"},
        "disk": {"usage_percent": 23.4, "status": "healthy"},
        "activeProcesses": 23,
        "successRate": 99.2,
        "avgResponseTime": 847,
        "errorRate": 0.8
    }

if __name__ == "__main__":
    print("🚀 Starting DataFlow AI Development Server...")
    print("📍 Backend will be available at: http://localhost:8081")
    print("📚 API docs available at: http://localhost:8081/docs")
    print("🛑 Press Ctrl+C to stop")
    
    uvicorn.run(
        "run_simple:app",
        host="0.0.0.0",
        port=8000,  # Changed to match your frontend expectations
        reload=True,
        log_level="info"
    )