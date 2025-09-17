/**
 * Authentication utilities for development
 * In production, this should be replaced with proper Firebase authentication
 */

export interface User {
  id: string;
  email: string;
  name: string;
  token: string;
}

// Mock user for development
const MOCK_USER: User = {
  id: '1',
  email: 'dev@example.com',
  name: 'Development User',
  token: 'mock-firebase-token-for-dev'
};

/**
 * Get current user token
 * In production, this should get the Firebase ID token
 */
export function getCurrentToken(): string | null {
  // First, try to get a real token from localStorage
  const storedToken = localStorage.getItem('token');
  if (storedToken && storedToken !== 'null' && storedToken !== 'undefined') {
    return storedToken;
  }

  // For development, return a mock token
  // This should be replaced with proper Firebase authentication
  console.warn('Using mock token for development. Please implement proper Firebase authentication.');
  return MOCK_USER.token;
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  const token = getCurrentToken();
  return token !== null && token !== 'null' && token !== 'undefined';
}

/**
 * Get current user
 * In production, this should validate the token and return user info
 */
export function getCurrentUser(): User | null {
  if (!isAuthenticated()) {
    return null;
  }

  // For development, return mock user
  return MOCK_USER;
}

/**
 * Mock login function
 * In production, this should handle Firebase authentication
 */
export function mockLogin(): void {
  localStorage.setItem('token', MOCK_USER.token);
  localStorage.setItem('user', JSON.stringify(MOCK_USER));
  console.log('Mock login successful');
}

/**
 * Logout function
 */
export function logout(): void {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  console.log('Logged out');
}

/**
 * Initialize authentication
 * Call this on app startup
 */
export function initializeAuth(): void {
  // Check if we have a token, if not, perform mock login for development
  if (!isAuthenticated()) {
    console.log('No authentication token found, performing mock login for development');
    mockLogin();
  }
}