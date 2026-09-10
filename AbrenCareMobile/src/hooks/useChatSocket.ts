// hooks/useChatSocket.ts

import { useCallback, useEffect, useRef, useState } from "react";
import { ensureValidToken, API_BASE } from "@/services/api";
import type { ApiMessage } from "@/services/chatApi";

const WS_BASE = API_BASE.replace(/^http/, "ws"); // http->ws, https->wss

type IncomingEvent =
  | { type: "connection"; message: string; conversation_id: number }
  | { type: "message"; message: ApiMessage }
  | { type: "typing"; user_id: number; username: string; is_typing: boolean }
  | { type: "error"; message: string };

export function useChatSocket(
  conversationId: number | null,
  onMessage: (msg: ApiMessage) => void,
  onTyping?: (userId: number, username: string, isTyping: boolean) => void,
) {
  const socketRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!conversationId) return;

    let cancelled = false;
    let retryTimeout: ReturnType<typeof setTimeout>;

    const connect = async () => {
      const token = await ensureValidToken();
      if (cancelled || !token) return;

      const ws = new WebSocket(
        `${WS_BASE}/ws/chat/${conversationId}/?token=${token}`,
      );

      ws.onopen = () => setConnected(true);

      ws.onclose = (event) => {
        setConnected(false);
        // 4001 = unauthenticated, 4003 = not a participant — don't retry those
        if (!cancelled && event.code !== 4001 && event.code !== 4003) {
          retryTimeout = setTimeout(connect, 2000);
        }
      };

      ws.onerror = () => setConnected(false);

      ws.onmessage = (event) => {
        const data: IncomingEvent = JSON.parse(event.data);

        if (data.type === "message") {
          onMessage(data.message);
        } else if (data.type === "typing" && onTyping) {
          onTyping(data.user_id, data.username, data.is_typing);
        } else if (data.type === "error") {
          console.warn("Chat socket error:", data.message);
        }
      };

      socketRef.current = ws;
    };

    connect();

    return () => {
      cancelled = true;
      clearTimeout(retryTimeout);
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [conversationId]);

  const sendMessage = useCallback((content: string) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: "message", content }));
    }
  }, []);

  const sendTyping = useCallback((isTyping: boolean) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: "typing", is_typing: isTyping }));
    }
  }, []);

  return { connected, sendMessage, sendTyping };
}
