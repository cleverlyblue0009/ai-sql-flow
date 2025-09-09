from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

# Create FastAPI application
app = FastAPI(
    title="AI Data Platform API",
    description="A simple API for data cleaning and migration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000", "http://127.0.0.1:8080", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time(),
        "message": "API is running successfully"
    }

# System info endpoint
@app.get("/info")
async def system_info():
    """Get system information and capabilities"""
    return {
        "name": "AI Data Platform API",
        "version": "1.0.0",
        "description": "AI-Powered Data Cleaning and SQL Migration Platform",
        "status": "running"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to the AI-Powered Data Cleaning and SQL Migration Platform API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
        "info": "/info"
    }

# Test endpoint for frontend connection
@app.get("/api/test")
async def api_test():
    """Test endpoint to verify frontend-backend connection"""
    return {
        "message": "Backend API is working!",
        "timestamp": time.time(),
        "status": "success"
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )