'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { WSMessage, WSMessageType } from '../types/game';

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

interface UseWebSocketOptions {
  roomId: string;
  clientId: string;
  onMessage: (msg: WSMessage) => void;
}

interface UseWebSocketReturn {
  connected: boolean;
  error: string | null;
  send: (type: WSMessageType, data?: Record<string, unknown>) => void;
}

/**
 * Custom hook for WebSocket communication with the game server
 * 
 * @example
 * ```tsx
 * const { connected, send } = useWebSocket({
 *   roomId: 'ABC123',
 *   clientId: 'player-1',
 *   onMessage: (msg) => console.log(msg)
 * });
 * ```
 */
export function useWebSocket({ roomId, clientId, onMessage }: UseWebSocketOptions): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const onMessageRef = useRef(onMessage);
  
  // Keep the callback reference up to date
  onMessageRef.current = onMessage;

  useEffect(() => {
    if (!roomId || !clientId) return;

    const url = `${WS_BASE}/ws/${roomId}/${clientId}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);
        onMessageRef.current(msg);
      } catch (e) {
        console.error('Failed to parse WS message', e);
      }
    };

    ws.onerror = () => {
      setError('Connection error. Please refresh.');
    };

    ws.onclose = () => {
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [roomId, clientId]);

  const send = useCallback((type: WSMessageType, data: Record<string, unknown> = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, data }));
    }
  }, []);

  return { connected, error, send };
}
