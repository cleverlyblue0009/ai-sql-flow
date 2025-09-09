# 🚀 Running DataFlow AI Platform in VS Code

This guide will help you set up and run the DataFlow AI Platform in VS Code with minimal configuration.

## ✅ Fixed Issues

The **Pydantic validation error** has been resolved by:
1. Adding the missing `environment` field to the Settings model
2. Adding `extra = "ignore"` to handle additional environment variables
3. Creating a simplified development version that doesn't require complex dependencies

## 🎯 Quick Start (Recommended)

### Option 1: Simple Development Mode (No Database Required)

1. **Open the project in VS Code**
2. **Install basic Python dependencies**:
   ```bash
   pip install fastapi uvicorn pydantic pydantic-settings
   ```
3. **Start the simplified backend**:
   ```bash
   python -m uvicorn app.main_simple:app --reload --host 0.0.0.0 --port 8000
   ```
4. **Start the frontend** (in a new terminal):
   ```bash
   npm install
   npm run dev
   ```

### Option 2: Using VS Code Tasks

1. **Open Command Palette**: `Ctrl+Shift+P`
2. **Type**: `Tasks: Run Task`
3. **Select**: `Start Both Frontend and Backend (Simple)`

## 🌐 Access Your Application

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
📁 DataFlow AI Platform/
├── 📁 .vscode/              # VS Code configuration
├── 📁 app/                  # Python backend
│   ├── 📄 main.py          # Full backend (requires database)
│   ├── 📄 main_simple.py   # Simplified backend (no database)
│   └── 📁 ...
├── 📁 src/                  # React frontend
├── 📄 package.json          # Frontend dependencies
├── 📄 requirements.txt      # Backend dependencies
├── 📄 .env                  # Environment configuration
└── 📄 start_dev.py         # Development startup script
```

## 🔧 Development Modes

### 1. Simple Mode (Recommended for Development)
- ✅ No database setup required
- ✅ No Redis required
- ✅ Uses in-memory mock data
- ✅ Perfect for frontend development
- ✅ Fast startup

**Start with**:
```bash
python -m uvicorn app.main_simple:app --reload --host 0.0.0.0 --port 8000
```

### 2. Full Mode (Production-like)
- ⚙️ Requires PostgreSQL
- ⚙️ Requires Redis
- ⚙️ Full AI/ML features
- ⚙️ Complete authentication system

**Setup required**:
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install all dependencies
pip install -r requirements.txt

# Configure .env file with database credentials
# Start with full backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🛠️ VS Code Setup

### Required Extensions
- **Python** (Microsoft)
- **TypeScript Importer**
- **ES7+ React/Redux/React-Native snippets**
- **Tailwind CSS IntelliSense**

### Available VS Code Tasks
- `Start Frontend` - Starts React development server
- `Start Backend (Simple)` - Starts simplified backend
- `Start Backend (Full)` - Starts full backend with all features
- `Start Both Frontend and Backend (Simple)` - Starts both in simple mode
- `Install Frontend Dependencies` - Runs npm install
- `Setup Python Environment` - Creates virtual environment

### Debugging
1. Set breakpoints in your code
2. Press `F5` or use the Run and Debug panel
3. Choose "Debug FastAPI Backend" or "Debug Frontend (Chrome)"

## 🔍 API Endpoints (Simple Mode)

The simplified backend provides these endpoints for frontend development:

### Core Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /info` - System information

### Mock Data Endpoints
- `GET /api/users` - Mock users
- `GET /api/projects` - Mock projects
- `GET /api/dashboard/metrics` - Dashboard metrics
- `POST /api/auth/login` - Mock authentication
- `GET /api/auth/me` - Current user info

## 📊 Mock Data Available

The simple mode provides realistic mock data:
- **3 test users** (admin, engineer, analyst roles)
- **3 sample projects** with different statuses
- **Dashboard metrics** with realistic values
- **Activity feed** with sample activities

## 🚨 Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Change port in command
   python -m uvicorn app.main_simple:app --reload --port 8001
   ```

2. **Python not found**:
   - Make sure Python is installed and in PATH
   - Try `python3` instead of `python`

3. **FastAPI not installed**:
   ```bash
   pip install fastapi uvicorn
   ```

4. **Frontend not starting**:
   ```bash
   # Delete node_modules and reinstall
   rm -rf node_modules
   npm install
   npm run dev
   ```

5. **CORS errors**:
   - The simplified backend has CORS enabled for common development ports
   - Check that your frontend is running on http://localhost:8080

### Error Resolution

The original **Pydantic validation error** was caused by:
- Missing `environment` field in Settings model
- Strict validation not allowing extra fields

**Fixed by**:
- Adding `environment: str = "development"` field
- Adding `extra = "ignore"` to Config class
- Creating simplified development version

## 🎯 Next Steps

1. **Start with Simple Mode** for frontend development
2. **Use the VS Code tasks** for easy startup
3. **Explore the API docs** at http://localhost:8000/docs
4. **Build your frontend** against the mock API
5. **Upgrade to Full Mode** when you need real database features

## 💡 Pro Tips

1. **Use the integrated terminal** in VS Code
2. **Enable auto-save** for hot reloading
3. **Use the debugger** instead of print statements
4. **Check the health endpoint** to verify backend status
5. **Use Thunder Client extension** for API testing in VS Code

---

**🎉 You're all set!** The project should now run smoothly in VS Code without the Pydantic validation error.