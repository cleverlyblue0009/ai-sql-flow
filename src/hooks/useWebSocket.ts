import { useState, useEffect, useRef, useCallback } from 'react';
import { getAuth } from 'firebase/auth';

interface WebSocketMessage {
  type: string;
  migration_id?: string;
  data?: any;
  message?: string;
  timestamp?: string;
}

interface UseWebSocketOptions {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export const useWebSocket = ({
  url,
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

  const connect = useCallback(async () => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    setConnectionState('connecting');

    // 🔑 Get Firebase ID token
    let idToken: string | null = null;
    try {
      const auth = getAuth();
      const user = auth.currentUser;
      if (user) {
        idToken = await user.getIdToken();
      }
    } catch (err) {
      console.error('Failed to get Firebase ID token:', err);
    }

    if (!idToken) {
      console.warn('No Firebase ID token available for WebSocket connection');
      setConnectionState('error');
      return;
    }

    const wsUrl = `${url}?token=${idToken}`;
    console.log('Final WebSocket URL:', wsUrl.replace(/token=([^&]+)/, 'token=[REDACTED]'));

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

    ws.current.onclose = (event) => {
      setIsConnected(false);
      setConnectionState('disconnected');
      onDisconnect?.();

      console.log('WebSocket closed:', { code: event.code, reason: event.reason });

      if (event.code === 4001 || event.code === 4003) {
        console.error('WebSocket authentication failed:', event.reason);
        setConnectionState('error');
        return;
      }

      if (reconnectCount.current < reconnectAttempts) {
        reconnectCount.current++;
        console.log(`Reconnecting... attempt ${reconnectCount.current}/${reconnectAttempts}`);
        reconnectTimeout.current = setTimeout(() => {
          connect();
        }, reconnectDelay);
      } else {
        console.error('WebSocket reconnection attempts exhausted');
        setConnectionState('error');
      }
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionState('error');
      onError?.(error);
    };
  }, [url, onMessage, onConnect, onDisconnect, onError, reconnectAttempts, reconnectDelay]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);

    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }

    setIsConnected(false);
    setConnectionState('disconnected');
  }, []);

  const reconnect = useCallback(() => {
    console.log('Manual WebSocket reconnection initiated');
    disconnect();
    setTimeout(() => {
      reconnectCount.current = 0;
      connect();
    }, 1000);
  }, [connect, disconnect]);

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    connectionState,
    sendMessage,
    connect,
    disconnect,
    reconnect
  };
};
