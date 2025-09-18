# Firebase Authentication Setup Guide

## 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project" or "Add project"
3. Enter your project name
4. Enable Google Analytics (optional)
5. Click "Create project"

## 2. Enable Authentication

1. In your Firebase project, go to "Authentication" in the left sidebar
2. Click "Get started"
3. Go to the "Sign-in method" tab
4. Enable the following providers:
   - **Email/Password**: Click on it and toggle "Enable"
   - **Google**: Click on it, toggle "Enable", and add your project's support email

## 3. Get Firebase Configuration

1. Go to Project Settings (gear icon in left sidebar)
2. Scroll down to "Your apps" section
3. Click "Add app" and select the web icon (`</>`)
4. Register your app with a nickname
5. Copy the `firebaseConfig` object

## 4. Update Firebase Configuration

Replace the placeholder values in `/workspace/src/lib/firebase.ts` with your actual Firebase config:

```typescript
const firebaseConfig = {
  apiKey: "your-actual-api-key",
  authDomain: "your-project-id.firebaseapp.com",
  projectId: "your-actual-project-id",
  storageBucket: "your-project-id.appspot.com",
  messagingSenderId: "your-actual-sender-id",
  appId: "your-actual-app-id"
};
```

## 5. Configure Google OAuth (for Google Sign-in)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your Firebase project
3. Go to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Choose "Web application"
6. Add your domain to "Authorized JavaScript origins":
   - `http://localhost:5173` (for development)
   - Your production domain (e.g., `https://yourdomain.com`)
7. Add redirect URIs to "Authorized redirect URIs":
   - `http://localhost:5173` (for development)
   - Your production domain (e.g., `https://yourdomain.com`)

## 6. Environment Variables (Optional)

For better security, you can use environment variables:

1. Create a `.env` file in your project root:
```env
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
```

2. Update `firebase.ts` to use environment variables:
```typescript
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID
};
```

## 7. Test Your Setup

1. Run your development server: `npm run dev`
2. Navigate to your app
3. You should see the authentication screen
4. Try signing up with email/password
5. Try signing in with Google

## Important Notes

- **Emulator Mode**: The current setup is configured for PRODUCTION use. Emulator connections are commented out in `firebase.ts`
- **Security**: Never commit your Firebase config with real credentials to public repositories
- **Domain Setup**: Make sure to add your production domain to Firebase Authentication settings
- **CORS**: If you encounter CORS issues, check your authorized domains in Firebase Authentication settings

## Troubleshooting

### "Firebase: Error (auth/configuration-not-found)"
- Make sure you've enabled Authentication in Firebase Console
- Check that your Firebase config is correct

### "Firebase: Error (auth/unauthorized-domain)"
- Add your domain to authorized domains in Firebase Authentication settings
- For development, add `localhost:5173`

### Google Sign-in not working
- Ensure Google provider is enabled in Firebase Authentication
- Check that your OAuth client ID is properly configured in Google Cloud Console
- Verify authorized domains match your setup