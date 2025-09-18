# DataFlow AI Platform - Setup Guide

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### 1. Firebase Setup (Required)

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Enable Authentication and add Email/Password and Google providers
3. Get your Firebase configuration from Project Settings > General > Your apps
4. Copy `.env.example` to `.env` and fill in your Firebase configuration:

```bash
cp .env.example .env
```

Update `.env` with your Firebase credentials:
```env
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456789:web:abcdef123456
```

### 2. Automatic Setup & Start

Run the development script:
```bash
./start-dev.sh
```

This will:
- Create Python virtual environment
- Install all dependencies
- Start both backend and frontend servers
- Open the application at http://localhost:5173

### 3. Manual Setup (Alternative)

#### Backend Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup
```bash
# Install dependencies
npm install

# Start frontend
npm run dev
```

## Access Points

- **Frontend Application**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Features

### 🔐 Authentication
- Firebase Authentication with Email/Password
- Google OAuth sign-in
- Protected routes and real-time session management

### 🌐 Real-time Features
- WebSocket connections with authentication
- Real-time migration progress tracking
- Live data quality analysis updates

### 📊 Data Management
- AI-powered data quality analysis
- SQL migration with dialect translation
- Interactive dashboard and monitoring

## Troubleshooting

### Authentication Issues
1. Ensure Firebase configuration is correct in `.env`
2. Check that Firebase Authentication is enabled
3. Verify Email/Password and Google providers are configured

### WebSocket Connection Issues
1. Ensure backend is running on port 8000
2. Check browser console for authentication errors
3. Verify Firebase token is being passed correctly

### Port Conflicts
- Backend: Change port in `start-dev.sh` or run manually with different port
- Frontend: Vite will automatically use next available port

## Development

### Project Structure
```
├── app/                    # Backend (FastAPI)
│   ├── auth/              # Authentication routes & logic
│   ├── websocket/         # WebSocket managers
│   ├── database/          # Database models & config
│   └── main.py           # FastAPI application
├── src/                   # Frontend (React + TypeScript)
│   ├── components/        # UI components
│   ├── contexts/         # React contexts (Auth)
│   ├── hooks/            # Custom hooks
│   ├── lib/              # Utilities (Firebase, API client)
│   └── pages/            # Page components
└── start-dev.sh          # Development startup script
```

### Environment Variables
- Copy `.env.example` to `.env`
- Update Firebase configuration
- Restart servers after changes

## Next Steps

1. Complete Firebase setup with your project credentials
2. Run `./start-dev.sh` to start development environment
3. Visit http://localhost:5173 and create an account
4. Explore the data quality and SQL migration features

For issues or questions, check the console logs in both browser and terminal.