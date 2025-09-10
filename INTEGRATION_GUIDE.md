# Frontend-Backend Integration Guide

## 🎉 Integration Status: COMPLETED ✅

The frontend and backend are now properly integrated and working together!

## 🚀 Quick Start

### Option 1: Automatic Startup (Recommended)
```bash
python start_integrated_services.py
```

### Option 2: Manual Startup

**Terminal 1 - Backend:**
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn python-multipart sqlalchemy pydantic-settings redis structlog requests

# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
# Install dependencies
npm install

# Start frontend
npm run dev
```

## 🔧 Configuration

### Ports
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs

### CORS Configuration
The backend is configured to accept requests from:
- `http://localhost:3000` (main frontend)
- `http://localhost:5173` (alternative Vite port)
- `http://localhost:8000` (backend self-reference)

## 🧪 Testing Integration

Run the integration test to verify everything is working:
```bash
python test_frontend_backend_integration.py
```

Expected output:
```
🚀 Frontend-Backend Integration Test
==================================================
✅ Backend Health Check: PASSED
✅ Frontend Availability: PASSED  
✅ CORS Integration: PASSED
✅ API Endpoints: 3/3 accessible
📊 Integration Test Results: 4/4 tests passed
🎉 All tests passed! Frontend and backend are properly integrated.
```

## 🔍 API Endpoints

The backend provides the following endpoints that the frontend can use:

### System Endpoints
- `GET /health` - Health check
- `GET /info` - System information
- `GET /` - Root endpoint with API info

### Frontend API Configuration
The frontend is configured to make API calls to `http://localhost:8000` via the `src/lib/api.ts` file.

Example API usage in frontend:
```typescript
import { api } from '@/lib/api';

// Health check
const health = await api.health();

// Dashboard data (when implemented)
const overview = await api.dashboard.getOverview();
```

## 🐛 Troubleshooting

### Port Conflicts
If you get port conflicts:
1. Check if any services are already running on ports 3000 or 8000
2. Kill existing processes: `pkill -f uvicorn` or `pkill -f vite`
3. Restart the services

### CORS Issues
If you see CORS errors in the browser console:
1. Verify the backend CORS configuration includes your frontend URL
2. Check that the frontend is making requests to the correct backend URL
3. Ensure both services are running

### Backend Import Errors
If the backend fails to start due to missing dependencies:
1. Make sure you're in the virtual environment: `source venv/bin/activate`
2. Install missing dependencies: `pip install -r requirements.txt`
3. For PostgreSQL issues, use SQLite (already configured as default)

## 📝 What Was Fixed

1. **Port Conflict**: Changed frontend from port 8000 to 3000
2. **CORS Configuration**: Added proper CORS origins for frontend
3. **Environment Configuration**: Fixed `.env` validation issues
4. **Dependencies**: Installed required packages for both services
5. **Integration Testing**: Created comprehensive test suite

## 🎯 Next Steps

The basic integration is complete. You can now:
1. Implement the actual API endpoints in the backend routers
2. Connect frontend components to real backend data
3. Add authentication and authorization
4. Implement data quality and migration features

## 📚 Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://react.dev/
- **Vite Documentation**: https://vitejs.dev/
- **API Documentation**: http://localhost:8000/docs (when backend is running)