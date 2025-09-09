"""
Simple FastAPI application for development
This version has minimal dependencies and can run without Redis, PostgreSQL, etc.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from typing import Dict, Any
import os

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application metadata
APP_TITLE = "DataFlow AI - Development Server"
APP_DESCRIPTION = """
## DataFlow AI Platform - Development Mode

A simplified version of the AI-powered data cleaning and SQL migration platform for development.

### Available Endpoints
- **Health Check**: Basic service health monitoring
- **System Info**: Application information
- **Mock Data**: Sample data endpoints for frontend development

### Development Features
- No database required (uses in-memory storage)
- No Redis required
- Simplified authentication (for testing only)
- CORS enabled for frontend development
"""

# Create FastAPI app
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version="1.0.0-dev",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080", 
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str

class SystemInfo(BaseModel):
    app_name: str
    version: str
    environment: str
    python_version: str
    features: list

class MockUser(BaseModel):
    id: int
    email: str
    name: str
    role: str

class MockProject(BaseModel):
    id: int
    name: str
    status: str
    created_at: str
    data_quality_score: float

# In-memory storage for development
mock_users = [
    {"id": 1, "email": "admin@dataflow.ai", "name": "Admin User", "role": "admin"},
    {"id": 2, "email": "engineer@dataflow.ai", "name": "Data Engineer", "role": "engineer"},
    {"id": 3, "email": "analyst@dataflow.ai", "name": "Data Analyst", "role": "analyst"},
]

mock_projects = [
    {"id": 1, "name": "Customer Data Cleanup", "status": "completed", "created_at": "2024-01-15", "data_quality_score": 0.92},
    {"id": 2, "name": "SQL Migration - MySQL to PostgreSQL", "status": "in_progress", "created_at": "2024-01-20", "data_quality_score": 0.78},
    {"id": 3, "name": "Sales Data Analysis", "status": "pending", "created_at": "2024-01-25", "data_quality_score": 0.65},
]

# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "DataFlow AI Platform - Development Server",
        "version": "1.0.0-dev",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="dataflow-ai-backend",
        version="1.0.0-dev",
        environment="development"
    )

@app.get("/info", response_model=SystemInfo)
async def system_info():
    """System information endpoint"""
    import sys
    return SystemInfo(
        app_name="DataFlow AI Platform",
        version="1.0.0-dev",
        environment="development",
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        features=[
            "Health Monitoring",
            "Mock Data API",
            "CORS Enabled",
            "Auto Documentation",
            "Development Mode"
        ]
    )

# Mock API endpoints for frontend development
@app.get("/api/users", response_model=list[MockUser])
async def get_users():
    """Get mock users for development"""
    return mock_users

@app.get("/api/projects", response_model=list[MockProject])
async def get_projects():
    """Get mock projects for development"""
    return mock_projects

@app.get("/api/dashboard/metrics")
async def get_dashboard_metrics():
    """Get mock dashboard metrics"""
    return {
        "total_projects": len(mock_projects),
        "active_users": len(mock_users),
        "data_quality_average": 0.78,
        "migrations_completed": 15,
        "storage_used_gb": 45.2,
        "cost_savings": 12500.00,
        "recent_activities": [
            {"id": 1, "type": "data_cleaning", "description": "Customer data cleanup completed", "timestamp": "2024-01-25T10:30:00Z"},
            {"id": 2, "type": "migration", "description": "SQL migration started", "timestamp": "2024-01-25T09:15:00Z"},
            {"id": 3, "type": "analysis", "description": "Data quality analysis finished", "timestamp": "2024-01-24T16:45:00Z"},
        ]
    }

@app.post("/api/auth/login")
async def mock_login(credentials: dict):
    """Mock login endpoint for development"""
    email = credentials.get("email", "")
    password = credentials.get("password", "")
    
    # Simple mock authentication
    if email and password == "password":
        user = next((u for u in mock_users if u["email"] == email), None)
        if user:
            return {
                "access_token": f"mock_token_{user['id']}",
                "token_type": "bearer",
                "user": user
            }
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/auth/me")
async def get_current_user():
    """Mock current user endpoint"""
    return mock_users[0]  # Return admin user for development

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Endpoint not found",
            "message": "This is a development server with limited endpoints",
            "available_endpoints": ["/", "/health", "/info", "/docs", "/api/users", "/api/projects"]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "An error occurred in the development server"
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 DataFlow AI Development Server starting up...")
    logger.info("📚 API Documentation available at: /docs")
    logger.info("🔍 Health check available at: /health")
    logger.info("📊 Mock data endpoints available for frontend development")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )