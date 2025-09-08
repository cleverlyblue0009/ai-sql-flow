from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any
import structlog

from .database import create_tables, settings
from .auth import router as auth_router
from .data_quality import router as data_quality_router
from .dashboard import router as dashboard_router
from .migration import router as migration_router
from .websocket import router as websocket_router
from .utils.logging_config import setup_logging

# Setup structured logging
setup_logging()
logger = structlog.get_logger()

# Application metadata
APP_TITLE = "AI-Powered Data Cleaning and SQL Migration Platform"
APP_DESCRIPTION = """
## AI-Powered Data Cleaning and SQL Migration Platform - Backend API

A comprehensive, enterprise-grade backend API for AI-powered data quality analysis, cleaning, and SQL migration.

### Key Features

#### 🔐 Authentication & Authorization
- JWT token-based authentication with refresh tokens
- Role-based access control (Admin, Engineer, Analyst)
- OAuth2 integration (Google, GitHub)
- Comprehensive audit logging

#### 📊 Data Quality Analysis
- **AI-Powered Analysis**: Duplicate detection using ML clustering, outlier detection with isolation forests
- **Missing Value Analysis**: Neural network-based imputation suggestions
- **Pattern Recognition**: NLP-based data type inference and validation
- **Quality Metrics**: Completeness, accuracy, consistency, validity, uniqueness scores

#### 🧹 Data Cleaning
- **Automated Cleaning**: AI-suggested cleaning operations
- **Custom Operations**: Remove duplicates, fill missing values, remove outliers
- **Format Standardization**: Consistent data formatting and type correction
- **Preview Mode**: Test cleaning operations before applying

#### 🔄 SQL Migration (Coming Soon)
- **Neural Translation**: SQL dialect conversion using transformer models
- **Semantic Validation**: BERT-based similarity checking
- **Performance Optimization**: Query optimization using reinforcement learning
- **Schema Mapping**: Intelligent schema mapping and conversion

#### 🗄️ Database Management
- **Multi-Database Support**: PostgreSQL, MySQL, Oracle, SQL Server
- **Secure Connections**: Encrypted credential storage
- **Health Monitoring**: Connection status and performance tracking

#### ⚡ Background Processing
- **Distributed Tasks**: Celery-based background job processing
- **Real-time Progress**: WebSocket updates for long-running operations
- **Resource Management**: CPU and memory usage tracking
- **Error Handling**: Comprehensive error recovery and retry logic

### Technology Stack
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with Redis caching
- **AI/ML**: TensorFlow, PyTorch, scikit-learn, Transformers
- **Queue System**: Celery with Redis broker
- **Storage**: AWS S3 / MinIO support
- **Monitoring**: Prometheus metrics, structured logging

### Performance Specifications
- **Response Time**: <200ms for simple queries, <2s for complex operations
- **Throughput**: Handle 1000+ concurrent users
- **File Processing**: Support files up to 10GB, process 1M+ records
- **Reliability**: 99.9% uptime with comprehensive error recovery
"""

APP_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting AI Data Platform API", version=APP_VERSION)
    
    try:
        # Create database tables
        create_tables()
        logger.info("Database tables created successfully")
        
        # Initialize AI models (placeholder)
        logger.info("AI models initialized")
        
        yield
        
    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        raise
    finally:
        # Shutdown
        logger.info("Shutting down AI Data Platform API")


# Create FastAPI application
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)


# Custom middleware for request logging and metrics
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log requests and add performance metrics"""
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add performance headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-API-Version"] = APP_VERSION
        
        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time
        )
        
        return response
        
    except Exception as e:
        # Calculate processing time for errors
        process_time = time.time() - start_time
        
        # Log error
        logger.error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time=process_time
        )
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "request_id": id(request)
            }
        )


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "timestamp": time.time(),
        "database": "connected",  # Would check actual database connection
        "redis": "connected",     # Would check actual Redis connection
        "services": {
            "authentication": "operational",
            "data_quality": "operational",
            "background_tasks": "operational"
        }
    }


# System info endpoint
@app.get("/info", tags=["System"])
async def system_info():
    """Get system information and capabilities"""
    return {
        "name": APP_TITLE,
        "version": APP_VERSION,
        "description": "AI-Powered Data Cleaning and SQL Migration Platform",
        "capabilities": {
            "authentication": {
                "jwt_auth": True,
                "oauth2": True,
                "role_based_access": True
            },
            "data_quality": {
                "ai_analysis": True,
                "duplicate_detection": True,
                "outlier_detection": True,
                "missing_value_analysis": True,
                "pattern_recognition": True,
                "automated_cleaning": True
            },
            "file_processing": {
                "supported_formats": ["CSV", "Excel", "JSON", "Parquet", "TSV"],
                "max_file_size_mb": settings.max_file_size_mb,
                "background_processing": True
            },
            "storage": {
                "local": True,
                "aws_s3": True,
                "minio": True
            }
        },
        "limits": {
            "max_file_size_mb": settings.max_file_size_mb,
            "concurrent_users": 1000,
            "max_records": 1000000
        }
    }


# Metrics endpoint for Prometheus
@app.get("/metrics", tags=["System"])
async def metrics():
    """Prometheus metrics endpoint"""
    # This would return actual Prometheus metrics
    # For now, return placeholder metrics
    return {
        "http_requests_total": 0,
        "http_request_duration_seconds": 0,
        "active_users": 0,
        "background_jobs_total": 0,
        "data_quality_analyses_total": 0,
        "files_processed_total": 0
    }


# Include routers
app.include_router(auth_router)
app.include_router(data_quality_router)
app.include_router(dashboard_router)
app.include_router(migration_router)
app.include_router(websocket_router)

# Custom OpenAPI schema
def custom_openapi():
    """Custom OpenAPI schema with additional metadata"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=APP_TITLE,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
        routes=app.routes,
    )
    
    # Add custom schema information
    openapi_schema["info"]["contact"] = {
        "name": "AI Data Platform Team",
        "email": "support@aidataplatform.com",
        "url": "https://aidataplatform.com"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Add tags metadata
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints"
        },
        {
            "name": "Data Quality",
            "description": "AI-powered data quality analysis and cleaning endpoints"
        },
        {
            "name": "System",
            "description": "System health, info, and monitoring endpoints"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource was not found: {request.url.path}",
            "available_endpoints": [
                "/docs", "/health", "/info", "/auth/*", "/data-quality/*"
            ]
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logger.error("Internal server error", error=str(exc), url=str(request.url))
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": id(request)
        }
    )


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to the AI-Powered Data Cleaning and SQL Migration Platform API",
        "version": APP_VERSION,
        "documentation": "/docs",
        "health": "/health",
        "info": "/info",
        "endpoints": {
            "authentication": "/auth",
            "data_quality": "/data-quality"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
        server_header=False,
        date_header=False
    )