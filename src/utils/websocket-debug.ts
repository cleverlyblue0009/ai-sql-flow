/**
 * WebSocket debugging utilities
 */

export function debugWebSocketConnection(url: string, token?: string) {
  console.group('WebSocket Connection Debug');
  console.log('URL:', url);
  console.log('Token present:', !!token);
  console.log('Token value:', token ? `${token.substring(0, 20)}...` : 'None');
  console.log('Browser WebSocket support:', typeof WebSocket !== 'undefined');
  console.log('Timestamp:', new Date().toISOString());
  console.groupEnd();
}

export function logWebSocketError(error: any, context?: string) {
  console.group(`WebSocket Error${context ? ` (${context})` : ''}`);
  console.error('Error object:', error);
  console.error('Error type:', error?.type);
  console.error('Error target:', error?.target);
  console.error('WebSocket state:', error?.target?.readyState);
  console.error('WebSocket states:', {
    CONNECTING: WebSocket.CONNECTING,
    OPEN: WebSocket.OPEN,
    CLOSING: WebSocket.CLOSING,
    CLOSED: WebSocket.CLOSED
  });
  console.groupEnd();
}

export function getWebSocketStateString(state: number): string {
  switch (state) {
    case WebSocket.CONNECTING: return 'CONNECTING';
    case WebSocket.OPEN: return 'OPEN';
    case WebSocket.CLOSING: return 'CLOSING';
    case WebSocket.CLOSED: return 'CLOSED';
    default: return `UNKNOWN(${state})`;
  }
}