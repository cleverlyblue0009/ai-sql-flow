#!/usr/bin/env python3
"""
Development startup script for DataFlow AI Platform
This script starts the simplified backend server for development
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def main():
    print("🚀 Starting DataFlow AI Platform - Development Mode")
    print("=" * 50)
    
    # Change to the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print(f"📁 Working directory: {project_dir}")
    print(f"🐍 Python version: {sys.version}")
    
    try:
        # Start the simplified FastAPI server
        print("\n🔧 Starting FastAPI development server...")
        print("📚 API Documentation will be available at: http://localhost:8000/docs")
        print("🔍 Health check available at: http://localhost:8000/health")
        print("🌐 CORS enabled for frontend development")
        print("\n" + "=" * 50)
        print("Press Ctrl+C to stop the server")
        print("=" * 50 + "\n")
        
        # Run the simplified server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main_simple:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--log-level", "info"
        ])
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down development server...")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure you have FastAPI and Uvicorn installed:")
        print("   pip install fastapi uvicorn")
        print("2. Make sure you're in the correct directory")
        print("3. Check if port 8000 is available")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())