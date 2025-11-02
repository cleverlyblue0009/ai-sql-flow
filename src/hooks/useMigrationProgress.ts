import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";

interface MigrationProgressData {
  migration_id: string;
  progress_percentage: number;
  current_phase: string;
  current_step?: string;
  status: string;
}

interface MigrationProgressHookParams {
  onProgress?: (progress: MigrationProgressData) => void;
  onStatusChange?: (migrationId: string, status: string, message: string) => void;
  onError?: (error: any) => void;
}

export const useMigrationProgress = (params: MigrationProgressHookParams = {}) => {
  const { currentUser } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [progressData, setProgressData] = useState<MigrationProgressData | null>(null);
  const [errors, setErrors] = useState<any[]>([]);
  const [firebaseToken, setFirebaseToken] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const subscriptionsRef = useRef<Set<string>>(new Set());
  const lastErrorTime = useRef<number>(0);
  const errorThrottleDelay = 10000; // 10 seconds between error notifications

  const { onProgress, onStatusChange, onError } = params;

  // Get Firebase ID token when user changes
  useEffect(() => {
    const getToken = async () => {
      if (currentUser) {
        try {
          const token = await currentUser.getIdToken();
          setFirebaseToken(token);
        } catch (error) {
          console.error('Failed to get Firebase token:', error);
          setFirebaseToken(null);
        }
      } else {
        setFirebaseToken(null);
      }
    };

    getToken();
  }, [currentUser]);

  const connect = useCallback(() => {
    if (!firebaseToken) {
      // Don't connect without authentication
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    setConnectionState('connecting');
    
    try {
      const wsUrl = `ws://localhost:8000/ws/migration?token=${encodeURIComponent(firebaseToken)}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('Migration WebSocket connected');
        setIsConnected(true);
        setConnectionState('connected');
        setErrors([]);
        
        // Resubscribe to any active migrations
        subscriptionsRef.current.forEach(migrationId => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'subscribe',
              migration_id: migrationId
            }));
          }
        });
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);

          switch (data.type) {
            case 'migration_progress':
              if (data.data) {
                setProgressData(data.data);
                onProgress?.(data.data);
              }
              break;
              
            case 'migration_status':
              if (data.data) {
                onStatusChange?.(data.migration_id, data.data.status, data.data.message || '');
              }
              break;
              
            case 'error':
              const errorData = { error: data.message, ...data };
              setErrors(prev => {
                const newErrors = [...prev, errorData];
                return newErrors.slice(-2); // Keep only last 2 errors
              });
              
              // Throttle error callbacks to prevent spam
              const now = Date.now();
              if (now - lastErrorTime.current > errorThrottleDelay) {
                lastErrorTime.current = now;
                onError?.(errorData);
              }
              break;
              
            case 'connection':
              console.log('Connection status:', data.message);
              break;
              
            default:
              console.log('Unknown message type:', data.type);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
          onError?.(error);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('Migration WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setConnectionState('disconnected');
        
        // Only attempt to reconnect if it's not a normal closure and we have a Firebase token
        // Reduce spam by adding exponential backoff and limiting reconnection attempts
        if (event.code !== 1000 && event.code !== 1001 && firebaseToken) {
          const reconnectDelay = Math.min(30000, 5000 * Math.pow(2, errors.length)); // Max 30s delay
          if (errors.length < 5) { // Limit reconnection attempts
            reconnectTimeoutRef.current = setTimeout(() => {
              console.log('Attempting to reconnect to WebSocket...');
              connect();
            }, reconnectDelay);
          } else {
            console.warn('Max WebSocket reconnection attempts reached. Backend may be unavailable.');
          }
        }
      };

      wsRef.current.onerror = (error) => {
        // Silently handle WebSocket errors - backend status is shown in UI
        const errorData = { error: 'WebSocket connection failed - backend unavailable', originalError: error };
        setErrors(prev => {
          // Limit error accumulation to prevent spam
          const newErrors = [...prev, errorData];
          return newErrors.slice(-2); // Keep only last 2 errors
        });
        
        // Throttle error callbacks to prevent spam
        const now = Date.now();
        if (now - lastErrorTime.current > errorThrottleDelay && errors.length < 1) {
          lastErrorTime.current = now;
          onError?.(errorData);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionState('disconnected');
      onError?.(error);
    }
  }, [firebaseToken, onProgress, onStatusChange, onError, errors.length]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounting');
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionState('disconnected');
    subscriptionsRef.current.clear();
  }, []);

  const subscribeToMigration = useCallback((migrationId: string) => {
    subscriptionsRef.current.add(migrationId);
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        migration_id: migrationId
      }));
      console.log(`Subscribed to migration: ${migrationId}`);
    }
  }, []);

  const unsubscribeFromMigration = useCallback((migrationId: string) => {
    subscriptionsRef.current.delete(migrationId);
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        migration_id: migrationId
      }));
      console.log(`Unsubscribed from migration: ${migrationId}`);
    }
  }, []);

  // Connect when Firebase token is available
  useEffect(() => {
    if (firebaseToken) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [firebaseToken, connect, disconnect]);

  return {
    isConnected,
    connectionState,
    progressData,
    errors,
    subscribeToMigration,
    unsubscribeFromMigration,
    connect,
    disconnect
  };
};
