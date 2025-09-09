#!/bin/bash
# DataFlow AI - Start Both Backend and Frontend

echo "🚀 Starting DataFlow AI Platform..."
echo "=================================="

# Function to cleanup on exit
cleanup() {
    echo "🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment and start backend
echo "🔧 Starting backend server..."
source venv/bin/activate
python run_simple.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend server..."
npm run dev &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 5

echo ""
echo "✅ DataFlow AI Platform is running!"
echo "=================================="
echo "🎨 Frontend: http://localhost:5173"
echo "🔧 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID