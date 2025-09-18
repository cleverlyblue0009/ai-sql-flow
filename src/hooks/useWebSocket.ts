import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface UseWebSocketOptions {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket({
  url,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  reconnectInterval = 3000,
  maxReconnectAttempts = 5
}: UseWebSocketOptions) {
  const { currentUser } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const getWebSocketUrl = useCallback(async () => {
    if (!currentUser) return null;
    
    try {
      return await apiClient.getWebSocketUrl(url);
    } catch (error) {
      console.error('Failed to get WebSocket URL:', error);
      return null;
    }
  }, [currentUser, url]);

  const connect = useCallback(async () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const wsUrl = await getWebSocketUrl();
      if (!wsUrl) {
        console.log('Cannot connect to WebSocket: no auth token');
        return;
      }

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setReconnectAttempts(0);
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;
        onDisconnect?.();

        // Attempt to reconnect if not a manual close
        if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
          console.log(`Attempting to reconnect (${reconnectAttempts + 1}/${maxReconnectAttempts})...`);
          setReconnectAttempts(prev => prev + 1);
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }, [getWebSocketUrl, onMessage, onConnect, onDisconnect, onError, reconnectAttempts, maxReconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setReconnectAttempts(0);
  }, []);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    console.warn('WebSocket is not connected. Message not sent:', message);
    return false;
  }, []);

  // Connect when user is authenticated
  useEffect(() => {
    if (currentUser) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [currentUser, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    sendMessage,
    connect,
    disconnect,
    reconnectAttempts
  };
}