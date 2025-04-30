import { useCallback, useEffect, useRef, useState } from "react";
import { WS_ORIGIN } from "../constants/api";
import useAuth from "./useAuth";

// Define types for message type objects
export interface MessageTypes {
  receive?: Record<string, string>;
  send?: Record<string, string>;
}

export interface SendType {
  type: string;
}
export interface ReceiveType {
  type: string;
  data: object;
}

// Define the hook props
export interface UseWebSocketProps {
  path: string;
  enabled: boolean;
  messageTypes: MessageTypes;
  onOpen?: () => void;
  onClose?: (event: CloseEvent) => void;
  onMessage?: (data: ReceiveType) => void;
  onError?: (event: Event) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  ping?: boolean;
  pingInterval?: number;
}

// Define the hook return value
export interface UseWebSocketReturn {
  socketRef: React.RefObject<WebSocket | null>;
  send: (data: SendType) => void;
  isOpen: boolean;
  isReady: boolean;
}

export default function useWebSocket({
  path,
  enabled,
  messageTypes,
  onOpen,
  onClose,
  onMessage,
  onError,
  autoReconnect = true,
  reconnectInterval = 1000,
  ping = false,
  pingInterval = 30000,
}: UseWebSocketProps): UseWebSocketReturn {
  const { token } = useAuth();
  const socketRef = useRef<WebSocket | null>(null);
  const pingIntervalRef = useRef<number | null>(null);
  const messageTypesRef = useRef<MessageTypes>(messageTypes);

  // Tracks the underlying WebSocket connection state
  const [isOpen, setIsOpen] = useState(false);
  // Tracks the server readiness. This changes only after receiving a "ready" message.
  const [isReady, setIsReady] = useState(false);

  const connectSocket = useCallback(() => {
    // Note: the token is no longer sent via the URL
    const socketUrl = `${WS_ORIGIN + path}`;
    socketRef.current = new WebSocket(socketUrl);

    socketRef.current.onopen = () => {
      setIsOpen(true);
      console.log(`Connection to ${socketUrl} established`);

      // Send auth token as the first message for safer authentication
      if (token) {
        socketRef.current?.send(JSON.stringify({ type: "auth", token }));
      }

      if (onOpen) {
        onOpen();
      }

      if (ping) {
        pingIntervalRef.current = window.setInterval(() => {
          if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({ type: "ping" }));
          }
        }, pingInterval);
      }
    };

    socketRef.current.onmessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);

      // If the server sends a "ready" message, mark the connection as fully ready.
      if (data.type === "ready") {
        setIsReady(true);
        return;
      }

      // Check if the message type is valid according to the allowed receive types.
      if (
        !Object.values(messageTypesRef.current?.receive || {}).includes(
          data.type
        )
      ) {
        throw new Error(
          `Invalid message type received for path '${path}.': ${data.type}`
        );
      }

      if (onMessage) {
        onMessage(data);
      }
    };

    socketRef.current.onerror = (event: Event) => {
      if (onError) {
        onError(event);
      }
    };

    socketRef.current.onclose = (event: CloseEvent) => {
      setIsOpen(false);
      setIsReady(false);
      console.log(`Connection to ${socketUrl} closed`, event);
      if (onClose) {
        onClose(event);
      }

      if (pingIntervalRef.current !== null) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }

      // Attempt to reconnect if autoReconnect is enabled and the close wasn't normal (code 1000)
      if (autoReconnect && event.code !== 1000) {
        setTimeout(() => connectSocket(), reconnectInterval);
      }
    };
  }, [
    autoReconnect,
    onOpen,
    onClose,
    onMessage,
    onError,
    reconnectInterval,
    path,
    token,
    ping,
    pingInterval,
  ]);

  useEffect(() => {
    if (token && enabled) connectSocket();

    return () => {
      if (
        socketRef.current &&
        socketRef.current.readyState === WebSocket.OPEN
      ) {
        socketRef.current.close();
      }
      setIsOpen(false);
      setIsReady(false);
      if (pingIntervalRef.current !== null) {
        clearInterval(pingIntervalRef.current);
      }
    };
  }, [token, path, connectSocket, enabled]);

  const send = (data: SendType) => {
    const validSendTypes = Object.values(messageTypesRef.current?.send || {});
    if (!validSendTypes.includes(data.type)) {
      throw new Error(
        `Unable to send message of type '${data.type}': Invalid message type for path ${path}.`
      );
    } else if (
      socketRef.current &&
      socketRef.current.readyState === WebSocket.OPEN &&
      isReady
    ) {
      socketRef.current.send(JSON.stringify(data));
    } else {
      console.warn(
        `Unable to send message of type '${data.type}': WebSocket connection not established.`
      );
    }
  };

  return { socketRef, send, isOpen, isReady };
}
