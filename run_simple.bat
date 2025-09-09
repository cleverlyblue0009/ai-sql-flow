@echo off
echo 🚀 Starting DataFlow AI - Simple Development Mode
echo ================================================

echo 📁 Current directory: %CD%
echo 🐍 Python version:
python --version

echo.
echo 🔧 Starting simplified FastAPI server...
echo 📚 API Documentation: http://localhost:8000/docs
echo 🔍 Health check: http://localhost:8000/health
echo 🌐 CORS enabled for frontend development
echo.
echo ================================================
echo Press Ctrl+C to stop the server
echo ================================================
echo.

python -m uvicorn app.main_simple:app --reload --host 0.0.0.0 --port 8000

pause