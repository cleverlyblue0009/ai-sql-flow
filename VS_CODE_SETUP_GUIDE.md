# 🚀 VS Code Setup Guide

Complete guide to run the AI-Powered Data Cleaning and SQL Migration Platform in VS Code.

## 📋 Prerequisites

Before starting, ensure you have installed:

- **VS Code** (latest version)
- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **Docker Desktop** (optional, for full stack) ([Download](https://www.docker.com/products/docker-desktop))
- **Git** ([Download](https://git-scm.com/downloads))

## 🎯 Quick Start (Recommended for VS Code)

### Option 1: Development Mode (Easiest - No Docker Required)

This runs the backend with SQLite and the frontend with Vite dev server.

#### Step 1: Open in VS Code
```bash
# Open the project
code /workspace
```

#### Step 2: Install Backend Dependencies

Open a **new terminal** in VS Code (`` Ctrl+` `` or `Terminal` > `New Terminal`):

```bash
# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

#### Step 3: Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
# Create .env file with basic configuration
cat > .env << 'EOF'
# Database (SQLite for local development)
DATABASE_URL=sqlite:///./app_data.db

# Security
SECRET_KEY=your-secret-key-change-this-in-production
ENCRYPTION_KEY=your-encryption-key-32-chars-here!

# Firebase (if using Firebase auth)
FIREBASE_PROJECT_ID=your-firebase-project
FIREBASE_CREDENTIALS_PATH=./firebase-creds.json

# Application
DEBUG=True
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=100
EOF
```

#### Step 4: Initialize Database

```bash
# Create database tables with Alembic
alembic upgrade head
```

#### Step 5: Start Backend Server

In your terminal:

```bash
# Start FastAPI backend (port 8000)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

#### Step 6: Install Frontend Dependencies

Open a **second terminal** in VS Code (click the `+` icon in terminal panel):

```bash
# Install Node dependencies
npm install
```

#### Step 7: Start Frontend Dev Server

In the second terminal:

```bash
# Start Vite dev server (port 5173)
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

#### Step 8: Access the Application

Open your browser:
- **Frontend**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/docs
- **Backend Health Check**: http://localhost:8000/health

🎉 **You're all set!** The application should now be running.

---

### Option 2: Full Stack with Docker (Complete Environment)

This runs all services (PostgreSQL, Redis, Celery, MinIO, Prometheus, Grafana).

#### Step 1: Start All Services

```bash
# Start all services with Docker Compose
docker-compose up -d
```

Wait about 30 seconds for services to initialize.

#### Step 2: Check Service Status

```bash
# Check if all services are running
docker-compose ps
```

#### Step 3: Start Frontend

Open a terminal in VS Code:

```bash
# Install dependencies (if not done already)
npm install

# Start frontend dev server
npm run dev
```

#### Step 4: Access All Services

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/docs
- **Celery Flower** (Task Monitor): http://localhost:5555
- **Grafana** (Metrics): http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

#### Useful Docker Commands

```bash
# View logs
docker-compose logs -f api
docker-compose logs -f celery-worker

# Stop all services
docker-compose down

# Restart a service
docker-compose restart api

# Rebuild services after code changes
docker-compose up -d --build
```

---

## 🔧 VS Code Recommended Extensions

Install these extensions for the best development experience:

### Essential Extensions
1. **Python** (`ms-python.python`) - Python language support
2. **Pylance** (`ms-python.vscode-pylance`) - Python IntelliSense
3. **ES7+ React/Redux/React-Native snippets** - React snippets
4. **Tailwind CSS IntelliSense** - Tailwind CSS autocomplete
5. **ESLint** - JavaScript/TypeScript linting
6. **Prettier** - Code formatter
7. **Docker** (`ms-azuretools.vscode-docker`) - Docker management

### Optional but Helpful
- **Thunder Client** - API testing (alternative to Postman)
- **SQLite Viewer** - View SQLite database
- **GitLens** - Enhanced Git capabilities

Install from VS Code:
1. Press `Ctrl+Shift+X` (or `Cmd+Shift+X` on Mac)
2. Search for each extension
3. Click "Install"

---

## 🎨 VS Code Configuration

### Create `.vscode/settings.json`

Create this file for project-specific settings:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.tabSize": 4
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.pytest_cache": true,
    "**/node_modules": true
  }
}
```

### Create `.vscode/launch.json`

For debugging in VS Code:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": false,
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

### Create `.vscode/tasks.json`

For quick task running:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Backend",
      "type": "shell",
      "command": "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
      "problemMatcher": [],
      "group": {
        "kind": "build",
        "isDefault": false
      }
    },
    {
      "label": "Start Frontend",
      "type": "shell",
      "command": "npm run dev",
      "problemMatcher": [],
      "group": {
        "kind": "build",
        "isDefault": false
      }
    },
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "pytest",
      "problemMatcher": [],
      "group": {
        "kind": "test",
        "isDefault": true
      }
    }
  ]
}
```

---

## 🐛 Running and Debugging

### Using VS Code Debug Panel

1. **Set Breakpoints**: Click in the left margin of any Python file
2. **Start Debugging**: Press `F5` or click "Run and Debug" in the sidebar
3. **Choose**: "Python: FastAPI" configuration
4. **Debug**: Use debug controls to step through code

### Using Multiple Terminals

VS Code lets you run multiple terminals:

1. **Terminal 1**: Backend server
   ```bash
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **Terminal 2**: Frontend dev server
   ```bash
   npm run dev
   ```

3. **Terminal 3**: (Optional) Celery worker for background tasks
   ```bash
   source venv/bin/activate
   celery -A app.tasks.data_quality_tasks.celery_app worker --loglevel=info
   ```

---

## 🧪 Testing

### Run Python Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest test_integration.py -v
```

### Test API Endpoints

Using Thunder Client extension or curl:

```bash
# Health check
curl http://localhost:8000/health

# API docs (open in browser)
open http://localhost:8000/docs
```

---

## 📦 Building for Production

### Build Frontend
```bash
# Create production build
npm run build

# Preview production build
npm run preview
```

The build will be in the `dist/` directory.

### Backend Production
```bash
# Run with production settings
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🔥 Common Issues and Solutions

### Issue: `ModuleNotFoundError` in Python

**Solution**: Make sure virtual environment is activated
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Port 8000 or 5173 already in use

**Solution**: Kill the process using the port
```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn app.main:app --reload --port 8001
npm run dev -- --port 5174
```

### Issue: Database errors

**Solution**: Reset the database
```bash
# Delete existing database
rm app_data.db

# Recreate with migrations
alembic upgrade head
```

### Issue: Frontend can't connect to backend

**Solution**: Check CORS settings and backend URL

1. Ensure backend is running on http://localhost:8000
2. Check `vite.config.ts` proxy settings
3. Check browser console for errors

### Issue: Firebase authentication not working

**Solution**: Set up Firebase credentials

1. Get Firebase credentials from Firebase Console
2. Save to `firebase-creds.json`
3. Update `.env` file with correct paths

---

## 🎯 Development Workflow

### Typical Workflow

1. **Start Day**:
   ```bash
   source venv/bin/activate
   git pull
   ```

2. **Terminal Setup**:
   - Terminal 1: Backend → `uvicorn app.main:app --reload`
   - Terminal 2: Frontend → `npm run dev`

3. **Make Changes**: Edit files, save (auto-reload enabled)

4. **Test**: Check browser and API docs

5. **Commit**: Use Git integration in VS Code (Source Control panel)

### Hot Reload

Both backend and frontend support hot reload:
- **Backend**: `--reload` flag automatically restarts on file changes
- **Frontend**: Vite HMR (Hot Module Replacement) updates instantly

---

## 📚 Useful Commands Reference

### Backend Commands
```bash
# Start server
uvicorn app.main:app --reload

# Run tests
pytest

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Format code
black app/
isort app/

# Lint
flake8 app/
```

### Frontend Commands
```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

### Docker Commands
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after changes
docker-compose up -d --build

# Execute command in container
docker-compose exec api bash
```

---

## 🎓 Next Steps

1. **Explore API Docs**: http://localhost:8000/docs
2. **Check Project Structure**: Review `app/` and `src/` directories
3. **Read Documentation**: Check `README.md` and other `.md` files
4. **Try Features**: Upload data, run migrations, analyze data quality
5. **Customize**: Modify code and see changes instantly

---

## 💡 Pro Tips

1. **Use VS Code's Split Editor**: View backend and frontend code side by side
2. **Terminal Splitting**: Split terminals horizontally/vertically (`Ctrl+Shift+5`)
3. **Keyboard Shortcuts**: 
   - `` Ctrl+` `` - Toggle terminal
   - `Ctrl+P` - Quick file open
   - `Ctrl+Shift+P` - Command palette
   - `F5` - Start debugging
4. **Git Integration**: Use Source Control panel for commits
5. **Extensions**: Install recommended extensions for better DX
6. **Settings Sync**: Enable VS Code settings sync across devices

---

## 📞 Need Help?

- Check API documentation: http://localhost:8000/docs
- Review error logs in terminal
- Check Docker logs: `docker-compose logs -f`
- Consult `README.md` for more details

---

**Happy Coding! 🚀**
