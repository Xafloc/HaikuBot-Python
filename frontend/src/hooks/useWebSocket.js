import { useState, useEffect, useRef, useCallback } from 'react';

// Determine WebSocket protocol based on current page protocol
const getWebSocketURL = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  return `${protocol}//${host}/ws/live`;
};

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [recentItems, setRecentItems] = useState([]); // Array of {type, data, receivedAt}
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);

  const connect = useCallback(() => {
    try {
      const wsUrl = getWebSocketURL();
      console.log('Connecting to WebSocket:', wsUrl);
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        // Send periodic pings to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send('ping');
          }
        }, 30000); // Ping every 30 seconds
        ws.current.pingInterval = pingInterval;
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);

          if (data.type === 'new_haiku' || data.type === 'new_line') {
            // Add new item to the beginning of the array with timestamp
            setRecentItems(prev => [{
              type: data.type,
              data: data.data,
              receivedAt: new Date().getTime()
            }, ...prev]);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        if (ws.current?.pingInterval) {
          clearInterval(ws.current.pingInterval);
        }
        // Attempt to reconnect after 5 seconds
        reconnectTimeout.current = setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, 5000);
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current?.pingInterval) {
        clearInterval(ws.current.pingInterval);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  const clearOldItems = useCallback((maxAgeMinutes) => {
    const now = new Date().getTime();
    const maxAgeMs = maxAgeMinutes * 60 * 1000;
    setRecentItems(prev => prev.filter(item => (now - item.receivedAt) < maxAgeMs));
  }, []);

  return {
    isConnected,
    lastMessage,
    recentItems,
    clearOldItems,
  };
}

