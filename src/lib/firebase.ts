import { initializeApp, FirebaseApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, Auth } from 'firebase/auth';

// Firebase configuration
// Replace these with your actual Firebase config values
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

// Validate Firebase configuration
const validateFirebaseConfig = () => {
  const requiredFields = ['apiKey', 'authDomain', 'projectId', 'appId'];
  const missingFields = requiredFields.filter(field => !firebaseConfig[field as keyof typeof firebaseConfig]);
  
  if (missingFields.length > 0) {
    console.error('Missing Firebase configuration fields:', missingFields);
    console.warn('Firebase authentication will not work without proper configuration');
    return false;
  }
  
  return true;
};

// Initialize Firebase with error handling
let app: FirebaseApp;
let auth: Auth;
let googleProvider: GoogleAuthProvider;

try {
  const isValid = validateFirebaseConfig();
  
  if (!isValid) {
    console.warn('Firebase configuration is incomplete. Using fallback configuration.');
  }
  
  app = initializeApp(firebaseConfig);
  auth = getAuth(app);
  
  // Initialize Google Auth Provider
  googleProvider = new GoogleAuthProvider();
  
  // Configure Google provider
  googleProvider.setCustomParameters({
    prompt: 'select_account'
  });
  
  console.log('Firebase initialized successfully');
} catch (error) {
  console.error('Failed to initialize Firebase:', error);
  throw new Error('Firebase initialization failed. Please check your configuration.');
}

export { auth, googleProvider };
export default app;