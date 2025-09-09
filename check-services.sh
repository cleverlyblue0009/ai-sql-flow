#!/bin/bash

echo "Checking service status..."
echo "=========================="

# Check backend API
echo -n "Backend API (localhost:8000): "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# Check frontend
echo -n "Frontend (localhost:5173): "
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

echo ""
echo "If services are running, you can access:"
echo "• Frontend: http://localhost:5173"
echo "• Backend API Docs: http://localhost:8000/docs"
echo "• Backend Health: http://localhost:8000/health"