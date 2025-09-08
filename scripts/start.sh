#!/bin/bash

# DataFlow AI Enterprise Platform - Startup Script
# This script starts all necessary services for the backend

set -e

echo "🚀 Starting DataFlow AI Enterprise Platform Backend..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if Docker is available
check_docker() {
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Start with Docker Compose
start_with_docker() {
    print_header "🐳 Starting with Docker Compose..."
    
    # Check if .env exists
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.example..."
        cp .env.example .env
        print_warning "Please edit .env file with your configuration and restart."
        return 1
    fi
    
    # Start services
    print_status "Starting all services..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    sleep 10
    
    # Check service health
    print_status "Checking service health..."
    
    # Check PostgreSQL
    if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        print_status "✅ PostgreSQL is ready"
    else
        print_error "❌ PostgreSQL is not ready"
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_status "✅ Redis is ready"
    else
        print_error "❌ Redis is not ready"
    fi
    
    # Check API
    sleep 5
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_status "✅ API is ready"
    else
        print_warning "⚠️  API is starting up (may take a few more seconds)"
    fi
    
    print_header "🎉 Services started successfully!"
    echo
    print_status "Available endpoints:"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • API Health Check: http://localhost:8000/health"
    echo "  • Celery Flower: http://localhost:5555"
    echo "  • Grafana: http://localhost:3000 (admin/admin)"
    echo "  • Prometheus: http://localhost:9090"
    echo
    print_status "To generate mock data, run:"
    echo "  docker-compose exec api python scripts/generate_mock_data.py"
    echo
    print_status "To view logs, run:"
    echo "  docker-compose logs -f api"
    echo
    print_status "To stop services, run:"
    echo "  docker-compose down"
}

# Start manually (development mode)
start_manual() {
    print_header "🛠️  Starting in development mode..."
    
    # Check Python version
    if ! python3 --version | grep -q "3\.[9-9]\|3\.1[0-9]"; then
        print_error "Python 3.9+ is required"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing dependencies..."
    pip install -r requirements.txt
    
    # Check if .env exists
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.example..."
        cp .env.example .env
        print_warning "Please edit .env file with your database configuration."
    fi
    
    # Check database connection
    print_status "Checking database connection..."
    python3 -c "
from app.database.config import settings, engine
try:
    engine.connect()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('Please ensure PostgreSQL is running and configured correctly.')
    exit(1)
    " || exit 1
    
    # Create database tables
    print_status "Creating database tables..."
    python3 -c "from app.database import create_tables; create_tables()"
    
    # Start services in background
    print_status "Starting API server..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    API_PID=$!
    
    print_status "Starting Celery worker..."
    celery -A app.tasks.data_quality_tasks.celery_app worker --loglevel=info &
    CELERY_PID=$!
    
    print_status "Starting Celery Flower..."
    celery -A app.tasks.data_quality_tasks.celery_app flower --port=5555 &
    FLOWER_PID=$!
    
    # Wait a moment for services to start
    sleep 5
    
    print_header "🎉 Development server started!"
    echo
    print_status "Available endpoints:"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • API Health Check: http://localhost:8000/health"
    echo "  • Celery Flower: http://localhost:5555"
    echo
    print_status "Process IDs:"
    echo "  • API Server: $API_PID"
    echo "  • Celery Worker: $CELERY_PID"
    echo "  • Celery Flower: $FLOWER_PID"
    echo
    print_status "To generate mock data, run:"
    echo "  python scripts/generate_mock_data.py"
    echo
    print_status "To stop all services:"
    echo "  kill $API_PID $CELERY_PID $FLOWER_PID"
    
    # Keep script running
    wait
}

# Generate mock data
generate_mock_data() {
    print_header "📊 Generating mock data..."
    
    if check_docker && docker-compose ps | grep -q "api.*Up"; then
        # Use Docker
        docker-compose exec api python scripts/generate_mock_data.py
    else
        # Use local Python
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        python scripts/generate_mock_data.py
    fi
    
    print_status "✅ Mock data generation completed!"
}

# Show help
show_help() {
    echo "DataFlow AI Enterprise Platform - Startup Script"
    echo
    echo "Usage: $0 [OPTION]"
    echo
    echo "Options:"
    echo "  docker     Start with Docker Compose (recommended)"
    echo "  dev        Start in development mode (manual setup)"
    echo "  mock       Generate mock data"
    echo "  help       Show this help message"
    echo
    echo "Examples:"
    echo "  $0 docker    # Start with Docker Compose"
    echo "  $0 dev       # Start in development mode"
    echo "  $0 mock      # Generate mock data"
}

# Main script logic
case "${1:-docker}" in
    "docker")
        if check_docker; then
            start_with_docker
        else
            print_error "Docker or Docker Compose not found!"
            print_status "Please install Docker and Docker Compose, or use 'dev' mode."
            print_status "Run '$0 dev' to start in development mode."
            exit 1
        fi
        ;;
    "dev")
        start_manual
        ;;
    "mock")
        generate_mock_data
        ;;
    "help")
        show_help
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac