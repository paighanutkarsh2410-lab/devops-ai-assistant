'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { playAlertForSeverity } from './alertSound';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export interface WSMessage {
  type: string;
  data?: Record<string, unknown>;
  timestamp?: string;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: WSMessage | null;
  messages: WSMessage[];
  sendMessage: (msg: Record<string, unknown>) => void;
  connectionStatus: 'connected' | 'reconnecting' | 'disconnected';
}

export function useWebSocket(userId?: string): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'reconnecting' | 'disconnected'>('disconnected');
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const [messages, setMessages] = useState<WSMessage[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<NodeJS.Timeout>(undefined);
  const reconnectAttempts = useRef(0);
  const lastEventTime = useRef<string>('');

  const connect = useCallback(() => {
    const path = userId ? `${WS_URL}/ws/${userId}` : `${WS_URL}/ws`;
    const params = lastEventTime.current ? `?last_event=${lastEventTime.current}` : '';
    const ws = new WebSocket(`${path}${params}`);

    ws.onopen = () => {
      setIsConnected(true);
      setConnectionStatus('connected');
      reconnectAttempts.current = 0;

      // Request browser notification permission
      if (typeof Notification !== 'undefined' && Notification.permission === 'default') {
        Notification.requestPermission();
      }
    };

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);

        // Handle heartbeat
        if (msg.type === 'ping') {
          ws.send(JSON.stringify({ type: 'pong' }));
          return;
        }

        if (msg.timestamp) {
          lastEventTime.current = msg.timestamp;
        }

        setLastMessage(msg);
        setMessages(prev => [...prev.slice(-99), msg]);

        // Browser notification + audio alert for incidents
        if (msg.type === 'new_incident' || msg.type === 'new_alert') {
          const severity = (msg.data?.severity as string) || 'low';

          // Audio alarm for critical/high
          playAlertForSeverity(severity);

          // Browser notification for critical/high
          if (severity === 'critical' || severity === 'high') {
            showBrowserNotification(
              `${severity.toUpperCase()} Incident`,
              `${msg.data?.title || 'New incident detected'}`,
            );
          }
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;

      // Auto-reconnect with exponential backoff
      const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30000);
      reconnectAttempts.current++;
      setConnectionStatus('reconnecting');

      reconnectTimer.current = setTimeout(() => {
        connect();
      }, delay);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, [userId]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback((msg: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  return { isConnected, lastMessage, messages, sendMessage, connectionStatus };
}

function showBrowserNotification(title: string, body: string) {
  if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
    new Notification(title, { body, icon: '/favicon.ico' });
  }
}

export default useWebSocket;
