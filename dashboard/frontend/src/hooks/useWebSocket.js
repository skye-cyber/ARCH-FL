import { useState, useEffect, useCallback, useRef } from "react";

export const useWebSocket = (experimentId, options = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const [connectionStats, setConnectionStats] = useState({
    reconnectAttempts: 0,
    lastPing: null,
    lastPong: null,
  });

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const pingIntervalRef = useRef(null);

  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    pingInterval = 30000, // 30 seconds
  } = options;

  const connect = useCallback(() => {
    try {
      // Construct WebSocket URL
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//${window.location.host}/ws/monitoring?client_id=experiment_${experimentId}`;

      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log(`WebSocket connected for experiment ${experimentId}`);
        setIsConnected(true);
        setError(null);
        setConnectionStats((prev) => ({ ...prev, reconnectAttempts: 0 }));

        // Send subscription message
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(
            JSON.stringify({
              type: "subscribe",
              topics: [
                "progress",
                "metrics",
                "round_complete",
                "client_update",
              ],
            }),
          );
        }

        // Start ping interval
        pingIntervalRef.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(
              JSON.stringify({
                type: "ping",
                timestamp: Date.now(),
              }),
            );
            setConnectionStats((prev) => ({ ...prev, lastPing: Date.now() }));
          }
        }, pingInterval);

        onConnect?.();
      };

      wsRef.current.onclose = () => {
        console.log(`WebSocket disconnected for experiment ${experimentId}`);
        setIsConnected(false);

        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
        }

        // Attempt reconnect
        if (connectionStats.reconnectAttempts < maxReconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            setConnectionStats((prev) => ({
              ...prev,
              reconnectAttempts: prev.reconnectAttempts + 1,
            }));
            connect();
          }, reconnectInterval);
        }

        onDisconnect?.();
      };

      wsRef.current.onerror = (event) => {
        console.error("WebSocket error:", event);
        setError("WebSocket connection error");
        onError?.(event);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Handle pong messages
          if (data.type === "pong") {
            setConnectionStats((prev) => ({ ...prev, lastPong: Date.now() }));
          }

          setLastMessage(data);
          onMessage?.(data);
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      };
    } catch (err) {
      console.error("WebSocket connection error:", err);
      setError(err.message);
    }
  }, [
    experimentId,
    onConnect,
    onDisconnect,
    onMessage,
    onError,
    reconnectInterval,
    maxReconnectAttempts,
    pingInterval,
  ]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
    }
  }, []);

  const sendMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
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
    lastMessage,
    error,
    sendMessage,
    disconnect,
    reconnect: connect,
    connectionStats,
  };
};
