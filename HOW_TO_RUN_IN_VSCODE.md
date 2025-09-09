# 🚀 How to Run DataFlow AI in VS Code

## 🎯 Quick Start Options

### **Option 1: Simple Development Mode (Recommended for first run)**
```bash
# 1. Open VS Code in the project directory
code /workspace

# 2. Open terminal in VS Code (Ctrl+`)

# 3. Activate virtual environment
source venv/bin/activate

# 4. Start simple backend
python run_simple.py

# 5. In a new terminal, start frontend
npm run dev
```

### **Option 2: Full Backend (With all features)**
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install ML dependencies (optional, may take time)
pip install scikit-learn scipy

# 3. Start full backend
python start_dev.py
```

---

## 📋 Step-by-Step Setup

### 1. **Open Project in VS Code**
```bash
# Navigate to project and open VS Code
cd /workspace
code .
```

### 2. **Install VS Code Extensions**
Install these recommended extensions:
- **Python** (Microsoft)
- **Pylance** (Microsoft) 
- **Python Debugger** (Microsoft)
- **ES7+ React/Redux/React-Native snippets**
- **Tailwind CSS IntelliSense**
- **REST Client**

### 3. **Setup Python Environment**

#### **Activate Virtual Environment**
```bash
# In VS Code terminal (Ctrl+`)
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

#### **Verify Dependencies**
```bash
# Check if basic dependencies are installed
pip list | grep fastapi
pip list | grep pandas
```

### 4. **Start the Application**

#### **Method A: Using VS Code Tasks (Recommended)**

1. Open Command Palette (`Ctrl+Shift+P`)
2. Type "Tasks: Run Task"
3. Select "Start DataFlow AI Backend"
4. Open another terminal and select "Start DataFlow AI Frontend"

#### **Method B: Manual Terminal Commands**

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
python run_simple.py
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

#### **Method C: Using VS Code Debugger**

1. Go to Run and Debug panel (`Ctrl+Shift+D`)
2. Select "DataFlow AI Development Script"
3. Click the green play button

### 5. **Access the Application**

Once both servers are running:

- **🎨 Frontend**: http://localhost:5173
- **🔧 Backend API**: http://localhost:8000  
- **📚 API Documentation**: http://localhost:8000/docs
- **🔍 Health Check**: http://localhost:8000/health

---

## 🛠️ VS Code Configuration

### **Python Interpreter Setup**
1. Open Command Palette (`Ctrl+Shift+P`)
2. Type "Python: Select Interpreter"
3. Choose `./venv/bin/python`

### **Workspace Settings**
VS Code settings are already configured in `.vscode/settings.json` for:
- Python virtual environment
- Code formatting
- Linting
- Auto-imports

---

## 🔧 Troubleshooting

### **"Virtual environment not found"**
```bash
# Create new virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_minimal.txt
```

### **"Port already in use"**
```bash
# Kill processes on ports
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:5173 | xargs kill -9  # Frontend
```

### **"Module not found" errors**
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements_minimal.txt
pip install aiosmtplib jinja2 boto3 minio structlog
```

### **"Database connection failed"**
```bash
# The simple mode doesn't require database
# Just use python run_simple.py for development
```

### **Frontend build errors**
```bash
# Reinstall node modules
rm -rf node_modules
npm install
```

---

## 🎯 Development Workflow

### **1. Daily Development**
```bash
# Start your day
source venv/bin/activate
python run_simple.py

# In another terminal
npm run dev
```

### **2. Testing Features**
- Visit http://localhost:5173 for the frontend
- Visit http://localhost:8000/docs for API testing
- Use the React DevTools for frontend debugging

### **3. Making Changes**
- **Backend**: Edit files in `app/` directory
- **Frontend**: Edit files in `src/` directory  
- Both servers auto-reload on file changes

---

## 🚀 Production Setup (Later)

When you're ready for full production features:

### **1. Install Full Dependencies**
```bash
source venv/bin/activate
pip install scikit-learn scipy tensorflow torch
```

### **2. Setup Database**
```bash
# Start PostgreSQL and Redis
sudo service postgresql start
redis-server &

# Create database
sudo -u postgres createdb dataflow_ai
```

### **3. Run Full Backend**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📊 What You Can Test Right Now

### **Frontend Features**
- ✅ Dashboard with metrics
- ✅ Data Quality upload interface
- ✅ SQL Migration workspace
- ✅ Monitoring dashboard
- ✅ Settings and configuration

### **Backend Features (Simple Mode)**
- ✅ REST API endpoints
- ✅ CORS configuration
- ✅ Health monitoring
- ✅ Auto-reload development
- ✅ API documentation

### **Full Backend Features (After ML setup)**
- 🔄 Real file uploads and processing
- 🔄 AI-powered data analysis
- 🔄 SQL translation
- 🔄 Database connections
- 🔄 Background task processing

---

## 💡 Development Tips

### **VS Code Shortcuts**
- `Ctrl+` ` - Open terminal
- `Ctrl+Shift+P` - Command palette
- `Ctrl+Shift+D` - Debug panel
- `F5` - Start debugging
- `Ctrl+C` - Stop server (in terminal)

### **Hot Reload**
Both servers support hot reload:
- **Backend**: Automatically reloads on Python file changes
- **Frontend**: Automatically reloads on React file changes

### **Debugging**
- Use VS Code debugger for Python backend
- Use browser DevTools for React frontend
- Check terminal logs for errors

---

## 🎉 You're Ready!

Your DataFlow AI platform is now set up for development in VS Code. Start with the simple mode to test the frontend, then gradually add the full backend features as needed.

**Quick Start Command:**
```bash
source venv/bin/activate && python run_simple.py
```

Happy coding! 🚀