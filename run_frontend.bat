@echo off
echo 🚀 Starting DataFlow AI - Frontend Development Server
echo ====================================================

echo 📁 Current directory: %CD%
echo 📦 Node.js version:
node --version
echo 📦 NPM version:
npm --version

echo.
echo 📦 Installing dependencies...
npm install

echo.
echo 🔧 Starting Vite development server...
echo 🌐 Frontend will be available at: http://localhost:8080
echo.
echo ====================================================
echo Press Ctrl+C to stop the server
echo ====================================================
echo.

npm run dev

pause