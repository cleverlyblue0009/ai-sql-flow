import { useState, useEffect, useCallback, useRef } from "react";

interface MigrationProgressData {
  migration_id: string;
  progress_percentage: number;
  current_phase: string;
  current_step?: string;
  status: string;
}

interface MigrationProgressHookParams {
  token?: string;
  onProgress?: (progress: MigrationProgressData) => void;
  onStatusChange?: (migrationId: string, status: string, message: string) => void;
  onError?: (error: any) => void;
}

export const useMigrationProgress = (params: MigrationProgressHookParams = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [progressData, setProgressData] = useState<MigrationProgressData | null>(null);
  const [errors, setErrors] = useState<any[]>([]);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const subscriptionsRef = useRef<Set<string>>(new Set());

  const { token, onProgress, onStatusChange, onError } = params;

  const connect = useCallback(() => {
    if (!token) {
      console.warn('No token provided for WebSocket connection');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    setConnectionState('connecting');
    
    try {
      const wsUrl = `ws://localhost:8000/ws/migration?token=${encodeURIComponent(token)}`;
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
              type: 'subscribe_migration',
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
            case 'migration_status_change':
              if (data.data) {
                onStatusChange?.(data.migration_id, data.data.status, data.data.message || '');
              }
              break;
              
            case 'migration_error':
              const errorData = { error: data.data?.error || data.message, ...data };
              setErrors(prev => [...prev, errorData]);
              onError?.(errorData);
              break;
              
            case 'error':
              const generalErrorData = { error: data.message, ...data };
              setErrors(prev => [...prev, generalErrorData]);
              onError?.(generalErrorData);
              break;
              
            case 'connection_established':
            case 'subscription_confirmed':
            case 'unsubscription_confirmed':
              console.log('WebSocket event:', data.type, data.message || data.migration_id);
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
        
        // Attempt to reconnect after a delay if not a normal closure
        if (event.code !== 1000 && token) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, 3000);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('Migration WebSocket error:', error);
        const errorData = { error: 'WebSocket connection error', originalError: error };
        setErrors(prev => [...prev, errorData]);
        onError?.(errorData);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionState('disconnected');
      onError?.(error);
    }
  }, [token, onProgress, onStatusChange, onError]);

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
        type: 'subscribe_migration',
        migration_id: migrationId
      }));
      console.log(`Subscribed to migration: ${migrationId}`);
    }
  }, []);

  const unsubscribeFromMigration = useCallback((migrationId: string) => {
    subscriptionsRef.current.delete(migrationId);
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'unsubscribe_migration',
        migration_id: migrationId
      }));
      console.log(`Unsubscribed from migration: ${migrationId}`);
    }
  }, []);

  // Connect when token is available
  useEffect(() => {
    if (token) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [token, connect, disconnect]);

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
