import { auth } from './firebase';
import { connectivityState } from 'firebase/auth';

export const testFirebaseConnectivity = async (): Promise<boolean> => {
  try {
    console.log('Testing Firebase connectivity...');
    
    // Test 1: Check if Firebase is initialized
    console.log('Firebase Auth instance:', auth);
    console.log('Current user:', auth.currentUser);
    
    // Test 2: Try to get the current user (this makes a network request)
    return new Promise((resolve) => {
      const unsubscribe = auth.onAuthStateChanged(
        (user) => {
          console.log('Auth state changed:', user ? 'User logged in' : 'No user');
          unsubscribe();
          resolve(true);
        },
        (error) => {
          console.error('Auth state change error:', error);
          unsubscribe();
          resolve(false);
        }
      );
      
      // Timeout after 10 seconds
      setTimeout(() => {
        console.log('Firebase connectivity test timed out');
        unsubscribe();
        resolve(false);
      }, 10000);
    });
  } catch (error) {
    console.error('Firebase connectivity test failed:', error);
    return false;
  }
};

export const getFirebaseStatus = () => {
  return {
    isInitialized: !!auth,
    currentUser: auth.currentUser,
    config: {
      apiKey: auth.app.options.apiKey ? 'Set' : 'Missing',
      authDomain: auth.app.options.authDomain,
      projectId: auth.app.options.projectId,
    }
  };
};