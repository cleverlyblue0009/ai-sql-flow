#!/bin/bash

# AI-Powered Data Cleaning and SQL Migration Platform
# Startup script for development environment

set -e

echo "🚀 Starting AI-Powered Data Migration Platform"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run the setup first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if Redis is running
echo "🔍 Checking Redis status..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis not running. Starting Redis server..."
    redis-server --daemonize yes
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis started successfully"
    else
        echo "❌ Failed to start Redis"
        exit 1
    fi
else
    echo "✅ Redis is already running"
fi

# Check database
echo "🗄️  Setting up database..."
python -c "
from app.database.config import create_tables
try:
    create_tables()
    print('✅ Database tables created/verified')
except Exception as e:
    print(f'❌ Database setup failed: {e}')
    exit(1)
"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    
    # Kill background processes
    if [ ! -z "$CELERY_PID" ] && kill -0 $CELERY_PID 2>/dev/null; then
        echo "Stopping Celery worker..."
        kill $CELERY_PID
    fi
    
    if [ ! -z "$FASTAPI_PID" ] && kill -0 $FASTAPI_PID 2>/dev/null; then
        echo "Stopping FastAPI server..."
        kill $FASTAPI_PID
    fi
    
    echo "✅ Cleanup completed"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

echo ""
echo "🔄 Starting Celery worker..."
celery -A app.tasks.migration_tasks.celery_app worker --loglevel=info --concurrency=2 &
CELERY_PID=$!
echo "✅ Celery worker started (PID: $CELERY_PID)"

echo ""
echo "🌐 Starting FastAPI server..."
python -m app.main &
FASTAPI_PID=$!
echo "✅ FastAPI server started (PID: $FASTAPI_PID)"

# Wait for services to start
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Test services
echo "🧪 Testing services..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ FastAPI server is responding"
else
    echo "❌ FastAPI server not responding"
    exit 1
fi

echo ""
echo "🎉 All services started successfully!"
echo ""
echo "📊 Service URLs:"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Health Check:      http://localhost:8000/health"
echo "  • System Info:       http://localhost:8000/info"
echo ""
echo "🔧 Available endpoints:"
echo "  • Migration:          /api/migration/*"
echo "  • Data Quality:       /api/data-quality/*"
echo "  • Authentication:     /api/auth/*"
echo ""
echo "📝 Logs:"
echo "  • FastAPI logs will appear below"
echo "  • Celery worker is running in background"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for FastAPI process and show logs
wait $FASTAPI_PID