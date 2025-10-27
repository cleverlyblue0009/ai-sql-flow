#!/bin/bash

# Quick Start Script for VS Code Development
# This script helps you get started with the project quickly

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   AI-Powered Data Platform - VS Code Quick Start${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${GREEN}[1/6] Checking prerequisites...${NC}"
MISSING_DEPS=0

if ! command_exists python3; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    MISSING_DEPS=1
else
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"
fi

if ! command_exists node; then
    echo -e "${RED}✗ Node.js not found${NC}"
    MISSING_DEPS=1
else
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js ${NODE_VERSION} found${NC}"
fi

if ! command_exists npm; then
    echo -e "${RED}✗ npm not found${NC}"
    MISSING_DEPS=1
else
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓ npm ${NPM_VERSION} found${NC}"
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo -e "${RED}Please install missing dependencies and try again${NC}"
    exit 1
fi

echo ""

# Create Python virtual environment
echo -e "${GREEN}[2/6] Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo ""
echo -e "${GREEN}[3/6] Installing Python dependencies...${NC}"
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Install Node dependencies
echo ""
echo -e "${GREEN}[4/6] Installing Node.js dependencies...${NC}"
npm install
echo -e "${GREEN}✓ Node.js dependencies installed${NC}"

# Set up environment file
echo ""
echo -e "${GREEN}[5/6] Setting up environment variables...${NC}"
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Database (SQLite for local development)
DATABASE_URL=sqlite:///./app_data.db

# Security
SECRET_KEY=dev-secret-key-change-in-production-please
ENCRYPTION_KEY=dev-encryption-key-32-chars-long!

# Firebase (optional - only if using Firebase auth)
# FIREBASE_PROJECT_ID=your-firebase-project
# FIREBASE_CREDENTIALS_PATH=./firebase-creds.json

# Application
DEBUG=True
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=100

# CORS (allows frontend to communicate with backend)
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
else
    echo -e "${YELLOW}✓ .env file already exists${NC}"
fi

# Initialize database
echo ""
echo -e "${GREEN}[6/6] Initializing database...${NC}"
if [ ! -f "app_data.db" ]; then
    alembic upgrade head
    echo -e "${GREEN}✓ Database initialized${NC}"
else
    echo -e "${YELLOW}✓ Database already exists${NC}"
    read -p "Do you want to run migrations? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        alembic upgrade head
        echo -e "${GREEN}✓ Migrations applied${NC}"
    fi
fi

# Success message
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Setup complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo -e "  ${GREEN}Option 1: Use VS Code Tasks (Recommended)${NC}"
echo -e "    1. Press ${BLUE}Ctrl+Shift+P${NC} (or Cmd+Shift+P on Mac)"
echo -e "    2. Type ${BLUE}'Tasks: Run Task'${NC}"
echo -e "    3. Select ${BLUE}'Start Both (Backend + Frontend)'${NC}"
echo ""
echo -e "  ${GREEN}Option 2: Manual Start${NC}"
echo ""
echo -e "    Terminal 1 - Backend:"
echo -e "    ${BLUE}source venv/bin/activate${NC}"
echo -e "    ${BLUE}uvicorn app.main:app --reload${NC}"
echo ""
echo -e "    Terminal 2 - Frontend:"
echo -e "    ${BLUE}npm run dev${NC}"
echo ""
echo -e "${YELLOW}Access points:${NC}"
echo -e "  • Frontend:  ${BLUE}http://localhost:5173${NC}"
echo -e "  • API Docs:  ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  • Health:    ${BLUE}http://localhost:8000/health${NC}"
echo ""
echo -e "For more information, see: ${BLUE}VS_CODE_SETUP_GUIDE.md${NC}"
echo ""
