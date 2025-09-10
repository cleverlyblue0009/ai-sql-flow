#!/usr/bin/env python3
"""
Integrated startup script for both frontend and backend services
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path

def print_banner():
    print("🚀 DataFlow AI - Integrated Services Startup")
    print("=" * 60)
    print("🔧 Backend: FastAPI on http://localhost:8000")
    print("🎨 Frontend: React on http://localhost:3000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 60)

def check_dependencies():
    """Check if required dependencies are installed"""
    print("📋 Checking dependencies...")
    
    # Check if virtual environment exists
    if not Path("venv").exists():
        print("❌ Virtual environment not found. Creating...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
        print("✅ Virtual environment created")
    
    # Check if node_modules exists
    if not Path("node_modules").exists():
        print("📦 Installing frontend dependencies...")
        subprocess.run(["npm", "install"])
        print("✅ Frontend dependencies installed")
    
    print("✅ Dependencies checked")

def start_backend():
    """Start the backend server"""
    print("🔧 Starting backend server...")
    
    # Activate virtual environment and start uvicorn
    if os.name == 'nt':  # Windows
        python_path = str(Path("venv/Scripts/python.exe").absolute())
        uvicorn_path = str(Path("venv/Scripts/uvicorn.exe").absolute())
    else:  # Unix/Linux/Mac
        python_path = str(Path("venv/bin/python").absolute())
        uvicorn_path = str(Path("venv/bin/uvicorn").absolute())
    
    # Install backend dependencies if needed
    subprocess.run([
        python_path, "-m", "pip", "install", 
        "fastapi", "uvicorn", "python-multipart", "sqlalchemy", 
        "pydantic-settings", "redis", "structlog", "requests"
    ], capture_output=True)
    
    # Start backend
    backend_process = subprocess.Popen([
        python_path, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])
    
    return backend_process

def start_frontend():
    """Start the frontend server"""
    print("🎨 Starting frontend server...")
    
    frontend_process = subprocess.Popen([
        "npm", "run", "dev"
    ])
    
    return frontend_process

def wait_for_services():
    """Wait for services to be ready"""
    print("⏳ Waiting for services to start...")
    time.sleep(5)
    
    # Test backend
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is ready")
        else:
            print("⚠️  Backend may not be fully ready")
    except:
        print("⚠️  Backend connection test failed")
    
    # Test frontend
    try:
        import requests
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is ready")
        else:
            print("⚠️  Frontend may not be fully ready")
    except:
        print("⚠️  Frontend connection test failed")

def main():
    """Main startup function"""
    print_banner()
    
    try:
        # Check dependencies
        check_dependencies()
        
        # Start services
        backend_process = start_backend()
        time.sleep(3)  # Give backend time to start
        frontend_process = start_frontend()
        
        # Wait for services to be ready
        wait_for_services()
        
        print("\n🎉 Services started successfully!")
        print("\n📍 Access your application:")
        print("   • Frontend: http://localhost:3000")
        print("   • Backend API: http://localhost:8000")
        print("   • API Documentation: http://localhost:8000/docs")
        print("\n⚠️  Press Ctrl+C to stop both services")
        
        # Keep script running and handle shutdown
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down services...")
            backend_process.terminate()
            frontend_process.terminate()
            
            # Wait for processes to terminate
            backend_process.wait(timeout=10)
            frontend_process.wait(timeout=10)
            
            print("✅ Services stopped successfully")
            
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()