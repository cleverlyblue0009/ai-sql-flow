@echo off
echo 🧹 Setting up Clean Python Environment for DataFlow AI
echo ====================================================

echo 📁 Current directory: %CD%

echo.
echo 🗑️ Removing old virtual environment if it exists...
if exist venv rmdir /s /q venv

echo.
echo 🐍 Creating new virtual environment...
python -m venv venv

echo.
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

echo.
echo 📋 Installing minimal dependencies for development...
pip install fastapi uvicorn[standard] pydantic pydantic-settings python-multipart websockets

echo.
echo ✅ Basic setup complete!
echo.
echo 🎯 To install full requirements later:
echo    call venv\Scripts\activate.bat
echo    pip install -r requirements_minimal.txt
echo.
echo 🚀 To start development server:
echo    call venv\Scripts\activate.bat
echo    python -m uvicorn app.main_simple:app --reload --host 0.0.0.0 --port 8000

pause