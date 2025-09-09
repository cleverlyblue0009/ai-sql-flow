# 🚀 DataFlow AI - VS Code Setup Guide

## Quick Start (TL;DR)

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Start the platform
python start_dev.py

# Choose option 3 (Both backend and frontend)
```

---

## 📋 Complete Setup Instructions

### 1. **Prerequisites**
- ✅ VS Code installed
- ✅ Python 3.8+ installed  
- ✅ Node.js 16+ installed
- ✅ Git installed

### 2. **Open in VS Code**
```bash
# Open the project in VS Code
code /workspace
```

### 3. **Install VS Code Extensions (Recommended)**
- **Python** (Microsoft) - For Python development
- **Pylance** (Microsoft) - Python language server
- **Python Debugger** (Microsoft) - For debugging
- **ES7+ React/Redux/React-Native snippets** - For React development
- **Tailwind CSS IntelliSense** - For styling
- **REST Client** - For API testing

### 4. **Backend Setup**

#### A. **Activate Virtual Environment**
```bash
# In VS Code terminal
source venv/bin/activate
```

#### B. **Install Dependencies**
```bash
# Install Python packages
pip install -r requirements_minimal.txt

# For full ML capabilities (optional - may require compilation)
pip install scikit-learn
```

#### C. **Environment Configuration**
The `.env` file is already created with default settings. Update if needed:
```bash
# Edit environment variables
code .env
```

### 5. **Frontend Setup**

#### A. **Install Node Dependencies**
```bash
# Install frontend packages
npm install
```

#### B. **Verify Installation**
```bash
# Check if all packages installed correctly
npm list --depth=0
```

### 6. **Database Setup**

#### A. **Start Services**
```bash
# Start PostgreSQL (if not running)
sudo service postgresql start

# Start Redis (if not running)
redis-server &
```

#### B. **Create Database**
The startup script will automatically create the database, or manually:
```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database
CREATE DATABASE dataflow_ai;
\q
```

### 7. **Running the Application**

#### **Option 1: Using the Startup Script (Recommended)**
```bash
# Activate virtual environment
source venv/bin/activate

# Run the startup script
python start_dev.py

# Choose option 3 for both backend and frontend
```

#### **Option 2: Manual Startup**

**Backend (Terminal 1):**
```bash
source venv/bin/activate
cd /workspace
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend (Terminal 2):**
```bash
cd /workspace
npm run dev
```

### 8. **Access the Application**

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc

## 🛠️ VS Code Configuration

### **Workspace Settings**
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "typescript.preferences.includePackageJsonAutoImports": "on",
    "eslint.workingDirectories": ["./"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/node_modules": true,
        "**/.pytest_cache": true
    }
}
```

### **Launch Configuration**
Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Backend",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "app.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ],
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        }
    ]
}
```

### **Tasks Configuration**
Create `.vscode/tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Start Backend",
            "type": "shell",
            "command": "${workspaceFolder}/venv/bin/python",
            "args": ["-m", "uvicorn", "app.main:app", "--reload"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "new"
            }
        },
        {
            "label": "Start Frontend", 
            "type": "shell",
            "command": "npm",
            "args": ["run", "dev"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always", 
                "focus": false,
                "panel": "new"
            }
        }
    ]
}
```

## 🧪 Testing the Setup

### 1. **Backend Health Check**
```bash
curl http://localhost:8000/health
```

### 2. **Frontend Check**
Open browser to http://localhost:5173

### 3. **API Documentation**
Open browser to http://localhost:8000/docs

## 🔧 Troubleshooting

### **Common Issues:**

#### **"Virtual environment not activated"**
```bash
source venv/bin/activate
```

#### **"Database connection failed"**
```bash
# Check if PostgreSQL is running
sudo service postgresql status

# Start if not running
sudo service postgresql start
```

#### **"Redis connection failed"**
```bash
# Check if Redis is running
redis-cli ping

# Start if not running
redis-server &
```

#### **"Port already in use"**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

#### **"Module not found" errors**
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements_minimal.txt
```

## 📁 Project Structure

```
/workspace/
├── app/                    # Backend (FastAPI)
│   ├── auth/              # Authentication & authorization
│   ├── data_quality/      # Data quality analysis & cleaning
│   ├── dashboard/         # Dashboard metrics & insights
│   ├── migration/         # SQL migration & translation
│   ├── monitoring/        # System monitoring & alerts
│   ├── settings/          # Configuration management
│   ├── websocket/         # Real-time updates
│   ├── database/          # Database models & config
│   ├── tasks/             # Background task processing
│   └── utils/             # Utility functions
├── src/                   # Frontend (React + TypeScript)
│   ├── components/        # React components
│   ├── pages/             # Page components
│   ├── hooks/             # Custom React hooks
│   └── lib/               # Utility libraries
├── venv/                  # Python virtual environment
├── .env                   # Environment configuration
├── start_dev.py          # Development startup script
└── requirements_minimal.txt  # Python dependencies
```

## 🎯 Key Features Available

### **Data Quality Management**
- Upload files (CSV, Excel, JSON) up to 500MB
- AI-powered data analysis and cleaning
- Real-time progress tracking
- Quality metrics and recommendations

### **SQL Migration Workspace**  
- Multi-database support (MySQL, PostgreSQL, Snowflake, etc.)
- AI-powered SQL dialect translation
- Performance optimization suggestions
- Migration progress tracking

### **Real-time Monitoring**
- System performance metrics
- Application health monitoring  
- Alert management and notifications
- Service status tracking

### **Settings & Configuration**
- Database connection management
- User role and permission management
- AI model configuration
- Integration settings (Slack, Email, Webhooks)

## 🌟 Next Steps

1. **Start the platform** using the startup script
2. **Upload sample data** to test data quality features
3. **Configure database connections** for SQL migration
4. **Explore the monitoring dashboard** for system insights
5. **Set up integrations** for notifications and alerts

Your DataFlow AI platform is now ready for enterprise use! 🎉