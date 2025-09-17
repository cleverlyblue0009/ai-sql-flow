import { useState, useEffect, useRef, useCallback } from 'react';
import { debugWebSocketConnection, logWebSocketError, getWebSocketStateString } from '../utils/websocket-debug';

interface WebSocketMessage {
  type: string;
  migration_id?: string;
  data?: any;
  message?: string;
  timestamp?: string;
}

interface UseWebSocketOptions {
  url: string;
  token?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export const useWebSocket = ({
  url,
  token,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  reconnectAttempts = 5,
  reconnectDelay = 3000
}: UseWebSocketOptions) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const ws = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = token ? `${url}?token=${token}` : url;
    
    // Debug connection attempt
    debugWebSocketConnection(wsUrl, token);
    
    setConnectionState('connecting');
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      setIsConnected(true);
      setConnectionState('connected');
      reconnectCount.current = 0;
      onConnect?.();
    };

    ws.current.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        onMessage?.(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.current.onclose = () => {
      setIsConnected(false);
      setConnectionState('disconnected');
      onDisconnect?.();

      // Attempt reconnection
      if (reconnectCount.current < reconnectAttempts) {
        reconnectCount.current++;
        reconnectTimeout.current = setTimeout(() => {
          connect();
        }, reconnectDelay);
      }
    };

    ws.current.onerror = (error) => {
      setConnectionState('error');
      logWebSocketError(error, 'Connection Error');
      
      // Check if this is a 403 authentication error
      if (ws.current?.readyState === WebSocket.CLOSED) {
        console.error('WebSocket connection closed. This might be due to:');
        console.error('1. Invalid or expired authentication token');
        console.error('2. Server not running or not accessible');
        console.error('3. Network connectivity issues');
        console.error('Current token:', token ? 'Present' : 'Missing');
        console.error('Current WebSocket state:', getWebSocketStateString(ws.current.readyState));
      }
      
      onError?.(error);
    };
  }, [url, token, onMessage, onConnect, onDisconnect, onError, reconnectAttempts, reconnectDelay]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }
    
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
    
    setIsConnected(false);
    setConnectionState('disconnected');
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    connectionState,
    sendMessage,
    connect,
    disconnect
  };
};