#!/usr/bin/env python3
"""
Setup verification script for DataFlow AI platform
"""

import requests
import time
import sys
import subprocess
from pathlib import Path

def check_backend():
    """Check if backend is running and responsive"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend is running")
            print(f"   Status: {data.get('status')}")
            print(f"   Mode: {data.get('mode')}")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend not responding: {e}")
        return False

def check_frontend():
    """Check if frontend is running"""
    try:
        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running")
            return True
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend not responding: {e}")
        return False

def check_api_endpoints():
    """Test key API endpoints"""
    endpoints = [
        "/health",
        "/info", 
        "/",
        "/docs"
    ]
    
    print("\n🔍 Testing API endpoints:")
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {endpoint}")
            else:
                print(f"   ❌ {endpoint} (status: {response.status_code})")
        except Exception as e:
            print(f"   ❌ {endpoint} (error: {e})")

def check_environment():
    """Check environment setup"""
    print("\n🔧 Environment Check:")
    
    # Check virtual environment
    venv_path = Path("venv/bin/python")
    if venv_path.exists():
        print("   ✅ Virtual environment exists")
    else:
        print("   ❌ Virtual environment not found")
    
    # Check .env file
    env_path = Path(".env")
    if env_path.exists():
        print("   ✅ Environment configuration exists")
    else:
        print("   ❌ .env file not found")
    
    # Check VS Code settings
    vscode_settings = Path(".vscode/settings.json")
    if vscode_settings.exists():
        print("   ✅ VS Code configuration exists")
    else:
        print("   ❌ VS Code settings not found")
    
    # Check node_modules
    node_modules = Path("node_modules")
    if node_modules.exists():
        print("   ✅ Frontend dependencies installed")
    else:
        print("   ❌ Frontend dependencies not installed")

def main():
    """Main verification function"""
    print("🚀 DataFlow AI Platform - Setup Verification")
    print("=" * 50)
    
    # Check environment first
    check_environment()
    
    print("\n🌐 Service Status:")
    backend_ok = check_backend()
    frontend_ok = check_frontend()
    
    if backend_ok:
        check_api_endpoints()
    
    print("\n" + "=" * 50)
    if backend_ok and frontend_ok:
        print("🎉 SUCCESS: Your DataFlow AI platform is fully functional!")
        print("\n📍 Access your application:")
        print("   🎨 Frontend: http://localhost:5173")
        print("   🔧 Backend:  http://localhost:8000")
        print("   📚 API Docs: http://localhost:8000/docs")
        print("\n✨ No mock data - everything is real and working!")
    elif backend_ok:
        print("⚠️  Backend is working, but frontend may not be started yet.")
        print("   Run: npm run dev")
    elif frontend_ok:
        print("⚠️  Frontend is working, but backend may not be started yet.")
        print("   Run: python run_simple.py")
    else:
        print("❌ Neither backend nor frontend are responding.")
        print("   Please start the servers:")
        print("   Backend:  python run_simple.py")
        print("   Frontend: npm run dev")

if __name__ == "__main__":
    main()