#!/usr/bin/env python3
"""
Server startup script with dependency checking
"""
import subprocess
import sys
import os
import importlib.util

def check_package(package_name):
    """Check if a package is installed"""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def install_package(package_name):
    """Install a package using pip with --break-system-packages if needed"""
    try:
        print(f"Installing {package_name}...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--break-system-packages", package_name
        ])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package_name}: {e}")
        return False

def ensure_dependencies():
    """Ensure required dependencies are installed"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "websockets",
        "python-multipart"
    ]
    
    missing_packages = []
    for package in required_packages:
        if not check_package(package):
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required packages:", missing_packages)
        print("Attempting to install...")
        
        for package in missing_packages:
            if not install_package(package):
                print(f"❌ Failed to install {package}")
                return False
        
        print("✅ All packages installed successfully")
    else:
        print("✅ All required packages are available")
    
    return True

def start_simple_server():
    """Start the simple backend server"""
    print("🚀 Starting simple WebSocket test server...")
    
    try:
        # Change to the workspace directory
        os.chdir('/workspace')
        
        # Run the simple backend
        subprocess.run([
            sys.executable, "simple_backend.py"
        ])
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

def start_full_server():
    """Start the full FastAPI server"""
    print("🚀 Starting full FastAPI server...")
    
    try:
        # Change to the workspace directory
        os.chdir('/workspace')
        
        # Set environment variable for Python path
        env = os.environ.copy()
        env['PYTHONPATH'] = '/workspace'
        
        # Run the full server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], env=env)
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

def main():
    """Main function"""
    print("🔧 WebSocket Server Startup Tool")
    print("=" * 50)
    
    # Check dependencies
    if not ensure_dependencies():
        print("❌ Failed to install required dependencies")
        sys.exit(1)
    
    # Choose server type
    print("\nChoose server type:")
    print("1. Simple test server (recommended for debugging)")
    print("2. Full FastAPI server (complete application)")
    
    try:
        choice = input("\nEnter choice (1 or 2, default 1): ").strip()
        if choice == "2":
            start_full_server()
        else:
            start_simple_server()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()