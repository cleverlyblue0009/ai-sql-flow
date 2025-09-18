import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';

interface MigrationProgress {
  migration_id: string;
  status: string;
  progress_percentage: number;
  current_phase: string;
  current_step?: string;
  estimated_completion?: string;
  tables_migrated?: number;
  total_tables?: number;
  records_migrated?: number;
  total_records?: number;
  current_table?: string;
}

interface MigrationError {
  migration_id: string;
  error: string;
  details?: any;
  timestamp: string;
}

interface UseMigrationProgressOptions {
  token?: string;
  onProgress?: (progress: MigrationProgress) => void;
  onStatusChange?: (migration_id: string, status: string, message: string) => void;
  onError?: (error: MigrationError) => void;
}

export const useMigrationProgress = ({
  token,
  onProgress,
  onStatusChange,
  onError
}: UseMigrationProgressOptions = {}) => {
  const [progressData, setProgressData] = useState<Record<string, MigrationProgress>>({});
  const [errors, setErrors] = useState<Record<string, MigrationError>>({});
  const [subscribedMigrations, setSubscribedMigrations] = useState<Set<string>>(new Set());

  const handleWebSocketMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'migration_progress':
        if (message.migration_id && message.data) {
          const progress: MigrationProgress = {
            migration_id: message.migration_id,
            ...message.data
          };
          
          setProgressData(prev => ({
            ...prev,
            [message.migration_id]: progress
          }));
          
          onProgress?.(progress);
        }
        break;

      case 'migration_status_change':
        if (message.migration_id && message.data) {
          const { status, message: statusMessage } = message.data;
          onStatusChange?.(message.migration_id, status, statusMessage);
          
          // Update progress data with new status
          setProgressData(prev => ({
            ...prev,
            [message.migration_id]: {
              ...prev[message.migration_id],
              status
            }
          }));
        }
        break;

      case 'migration_error':
        if (message.migration_id && message.data) {
          const error: MigrationError = {
            migration_id: message.migration_id,
            ...message.data
          };
          
          setErrors(prev => ({
            ...prev,
            [message.migration_id]: error
          }));
          
          onError?.(error);
        }
        break;

      case 'migration_completed':
        if (message.migration_id) {
          setProgressData(prev => ({
            ...prev,
            [message.migration_id]: {
              ...prev[message.migration_id],
              status: 'completed',
              progress_percentage: 100
            }
          }));
        }
        break;

      case 'subscription_confirmed':
      case 'unsubscription_confirmed':
        // Handle subscription confirmations if needed
        break;

      default:
        console.log('Unhandled migration WebSocket message:', message);
    }
  }, [onProgress, onStatusChange, onError]);

  const {
    isConnected,
    sendMessage
  } = useWebSocket({
    url: '/migration',
    onMessage: handleWebSocketMessage,
    onConnect: () => {
      console.log('Connected to migration WebSocket');
      // Re-subscribe to all migrations on reconnect
      subscribedMigrations.forEach(migrationId => {
        sendMessage({
          type: 'subscribe_migration',
          migration_id: migrationId
        });
      });
    },
    onDisconnect: () => {
      console.log('Disconnected from migration WebSocket');
    },
    onError: (error) => {
      console.error('Migration WebSocket error:', error);
    }
  });

  const subscribeToMigration = useCallback((migrationId: string) => {
    if (isConnected && !subscribedMigrations.has(migrationId)) {
      const success = sendMessage({
        type: 'subscribe_migration',
        migration_id: migrationId
      });

      if (success) {
        setSubscribedMigrations(prev => new Set([...prev, migrationId]));
      }

      return success;
    }
    return false;
  }, [isConnected, sendMessage, subscribedMigrations]);

  const unsubscribeFromMigration = useCallback((migrationId: string) => {
    if (isConnected && subscribedMigrations.has(migrationId)) {
      const success = sendMessage({
        type: 'unsubscribe_migration',
        migration_id: migrationId
      });

      if (success) {
        setSubscribedMigrations(prev => {
          const newSet = new Set(prev);
          newSet.delete(migrationId);
          return newSet;
        });
      }

      return success;
    }
    return false;
  }, [isConnected, sendMessage, subscribedMigrations]);

  const getMigrationStatus = useCallback((migrationId: string) => {
    if (isConnected) {
      return sendMessage({
        type: 'get_migration_status',
        migration_id: migrationId
      });
    }
    return false;
  }, [isConnected, sendMessage]);

  const clearMigrationData = useCallback((migrationId: string) => {
    setProgressData(prev => {
      const newData = { ...prev };
      delete newData[migrationId];
      return newData;
    });

    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[migrationId];
      return newErrors;
    });
  }, []);

  return {
    isConnected,
    progressData,
    errors,
    subscribedMigrations: Array.from(subscribedMigrations),
    subscribeToMigration,
    unsubscribeFromMigration,
    getMigrationStatus,
    clearMigrationData
  };
};