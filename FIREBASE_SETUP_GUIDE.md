# Firebase Authentication Setup Guide

## 🚀 Quick Setup

Your Firebase authentication is now configured! Follow these steps to complete the setup:

### 1. Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project"
3. Enter a project name
4. Enable Google Analytics (optional)
5. Click "Create project"

### 2. Enable Authentication

1. In your Firebase project, go to **Authentication** > **Sign-in method**
2. Enable **Email/Password** authentication
3. Enable **Google** authentication:
   - Click on Google provider
   - Enable it
   - Add your project's domain (e.g., localhost:5173 for development)
   - Save your OAuth client configuration

### 3. Get Firebase Configuration

1. Go to **Project Settings** (gear icon)
2. Scroll down to "Your apps" section
3. Click "Add app" and select the web icon (</>)
4. Register your app with a nickname
5. Copy the Firebase configuration object

### 4. Update Environment Variables

Edit the `.env` file in your project root and replace the placeholder values with your actual Firebase config:

```env
VITE_FIREBASE_API_KEY=your_actual_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project_id.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_actual_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_actual_sender_id
VITE_FIREBASE_APP_ID=your_actual_app_id
```

### 5. Configure Google OAuth (for Google Sign-In)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your Firebase project
3. Go to **APIs & Services** > **Credentials**
4. Find your OAuth 2.0 client ID
5. Add authorized domains:
   - `localhost:5173` (for development)
   - Your production domain

### 6. Test the Setup

1. Start your development server: `npm run dev`
2. Navigate to `/login` or `/signup`
3. Try both email/password and Google sign-in

## ✨ Features Included

- **Email/Password Authentication**: Traditional signup and login
- **Google OAuth**: One-click Google sign-in
- **Protected Routes**: Automatic redirection for unauthenticated users
- **User Profile Display**: Shows user info in the sidebar
- **Logout Functionality**: Secure sign-out

## 🛡️ Security Notes

- Environment variables are automatically excluded from git
- Firebase handles all authentication security
- No emulator mode - connects directly to Firebase production
- HTTPS required for Google OAuth in production

## 🔧 Troubleshooting

### "Firebase: Error (auth/configuration-not-found)"
- Check that all environment variables are set correctly
- Ensure the Firebase project exists and is active

### "Firebase: Error (auth/unauthorized-domain)"
- Add your domain to Firebase Authentication settings
- For development, add `localhost:5173`

### Google Sign-In not working
- Verify Google OAuth is enabled in Firebase console
- Check authorized domains in Google Cloud Console
- Ensure correct OAuth client ID is configured

### App shows "Loading..." forever
- Check browser console for errors
- Verify Firebase configuration is correct
- Ensure internet connection is stable

## 📱 Next Steps

Your authentication is ready! Users will now:
1. Be redirected to `/login` when not authenticated
2. Access the full app after signing in
3. See their profile info in the sidebar
4. Be able to sign out securely

The emulator mode issue is resolved - your app now connects directly to Firebase production services.