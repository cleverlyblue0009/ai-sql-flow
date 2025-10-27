# 🚀 Quick Reference - Running in VS Code

## ⚡ Fastest Way to Get Started

### 1. Run the setup script:
```bash
./quick-start.sh
```

### 2. Start the application:

**Option A: Use VS Code Tasks (Easiest)**
- Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
- Type "Tasks: Run Task"
- Select "Start Both (Backend + Frontend)"

**Option B: Manual Commands**

Terminal 1 (Backend):
```bash
source venv/bin/activate
uvicorn app.main:app --reload
```

Terminal 2 (Frontend):
```bash
npm run dev
```

### 3. Access the app:
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📝 Common Commands

### Backend (Python/FastAPI)
```bash
# Start server
uvicorn app.main:app --reload

# Run tests
pytest

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

### Frontend (React/Vite)
```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Run linter
npm run lint
```

### Docker (Full Stack)
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f api
```

---

## 🎯 VS Code Shortcuts

| Action | Shortcut |
|--------|----------|
| Open Command Palette | `Ctrl+Shift+P` / `Cmd+Shift+P` |
| Toggle Terminal | `` Ctrl+` `` |
| Run Task | `Ctrl+Shift+B` / `Cmd+Shift+B` |
| Start Debugging | `F5` |
| Quick File Open | `Ctrl+P` / `Cmd+P` |
| Split Terminal | `Ctrl+Shift+5` |

---

## 🐛 Debugging

### Start Debugging in VS Code:
1. Set breakpoints by clicking left margin in Python files
2. Press `F5` or click "Run and Debug"
3. Select "Python: FastAPI"
4. Debug away!

---

## 📦 Project Structure

```
/workspace/
├── app/                    # Backend (Python/FastAPI)
│   ├── main.py            # Entry point
│   ├── auth/              # Authentication
│   ├── data_quality/      # Data analysis & cleaning
│   ├── migration/         # SQL migration
│   ├── database/          # Database models
│   └── tasks/             # Background tasks
├── src/                    # Frontend (React/TypeScript)
│   ├── components/        # React components
│   ├── pages/             # Page components
│   ├── hooks/             # Custom hooks
│   └── lib/               # Utilities
├── .vscode/               # VS Code configuration
├── requirements.txt       # Python dependencies
└── package.json           # Node dependencies
```

---

## 🔥 Troubleshooting

### Port already in use
```bash
# Kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173 (frontend)
lsof -ti:5173 | xargs kill -9
```

### Python module not found
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Database errors
```bash
# Reset database
rm app_data.db
alembic upgrade head
```

### Frontend build errors
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

---

## 📚 Need More Help?

- **Full Setup Guide**: [VS_CODE_SETUP_GUIDE.md](VS_CODE_SETUP_GUIDE.md)
- **Project README**: [README.md](README.md)
- **API Documentation**: http://localhost:8000/docs (when running)

---

## 🎓 Key Features to Try

1. **Data Quality Analysis**
   - Upload CSV/Excel files
   - AI-powered duplicate detection
   - Outlier detection
   - Missing value analysis

2. **SQL Migration**
   - Translate SQL between dialects
   - MySQL to PostgreSQL
   - Oracle to SQL Server
   - And more!

3. **Real-time Updates**
   - WebSocket support
   - Live progress tracking
   - Background task processing

---

**Happy Coding! 🚀**

Need help? Check the [VS_CODE_SETUP_GUIDE.md](VS_CODE_SETUP_GUIDE.md) for detailed instructions.
