@echo off
echo 🔧 Fixing Dependency Conflicts
echo ==============================

echo 📋 Current Python environment issues:
echo - chromadb needs httpx>=0.27.0 but you have httpx 0.25.2
echo - protobuf version conflicts with multiple packages
echo.

echo 🔄 Attempting to resolve conflicts...
echo.

echo 📦 Upgrading httpx to resolve chromadb conflict...
pip install --upgrade "httpx>=0.27.0"

echo.
echo 📦 Downgrading protobuf to resolve conflicts...
pip install "protobuf>=4.25.3,<5.0.0"

echo.
echo 📦 Reinstalling conflicting packages...
pip install --force-reinstall mediapipe grpcio-status

echo.
echo ✅ Dependency fixes attempted!
echo.
echo 🧪 Testing FastAPI import...
python -c "import fastapi; print('✅ FastAPI works')"

echo.
echo 🧪 Testing httpx import...
python -c "import httpx; print('✅ httpx works')"

echo.
echo 🧪 Testing protobuf...
python -c "import google.protobuf; print('✅ protobuf works')"

echo.
echo 🚀 Try starting the server now:
echo python -m uvicorn app.main_simple:app --reload --host 0.0.0.0 --port 8000

pause