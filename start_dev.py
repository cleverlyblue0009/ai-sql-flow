#!/usr/bin/env python3
"""
Development startup script for DataFlow AI platform
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if required services are running"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running")
    except Exception as e:
        print(f"❌ Redis is not running: {e}")
        print("   Starting Redis...")
        subprocess.Popen(['redis-server'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
    
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="postgres"
        )
        conn.close()
        print("✅ PostgreSQL is running")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("   You may need to start PostgreSQL manually")

def setup_database():
    """Setup database and tables"""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Connect to postgres database to create our database
        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'dataflow_ai'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute('CREATE DATABASE dataflow_ai')
            print("✅ Created database 'dataflow_ai'")
        else:
            print("✅ Database 'dataflow_ai' already exists")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")

def start_backend():
    """Start the FastAPI backend"""
    print("\n🚀 Starting DataFlow AI Backend...")
    
    # Set environment variables
    os.environ["PYTHONPATH"] = str(Path(__file__).parent)
    
    try:
        # Start uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print("\n👋 Backend server stopped")

def start_frontend():
    """Start the React frontend"""
    print("\n🎨 Starting Frontend...")
    try:
        subprocess.run(["npm", "run", "dev"])
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped")

def main():
    """Main startup function"""
    print("🏗️  DataFlow AI Enterprise Platform - Development Setup")
    print("=" * 60)
    
    # Check if we're in virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("❌ Not in virtual environment!")
        print("   Please run: source venv/bin/activate")
        sys.exit(1)
    
    print("✅ Virtual environment detected")
    
    # Check dependencies
    print("\n📋 Checking dependencies...")
    check_dependencies()
    
    # Setup database
    print("\n🗄️  Setting up database...")
    setup_database()
    
    # Ask user what to start
    print("\n🚀 What would you like to start?")
    print("1. Backend only (FastAPI)")
    print("2. Frontend only (React)")
    print("3. Both (recommended)")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == "1":
        start_backend()
    elif choice == "2":
        start_frontend()
    elif choice == "3":
        print("\n🚀 Starting both backend and frontend...")
        print("   Backend will run on: http://localhost:8000")
        print("   Frontend will run on: http://localhost:3000")
        print("   API Documentation: http://localhost:8000/docs")
        print("\n   Press Ctrl+C to stop both services")
        
        # Start backend in background
        backend_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ])
        
        time.sleep(3)  # Give backend time to start
        
        try:
            # Start frontend
            subprocess.run(["npm", "run", "dev"])
        except KeyboardInterrupt:
            print("\n👋 Stopping services...")
            backend_process.terminate()
            backend_process.wait()
    else:
        print("❌ Invalid choice")
        sys.exit(1)

if __name__ == "__main__":
    main()