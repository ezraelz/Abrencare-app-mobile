// context/ChatContext.tsx

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { chatApi, type ApiConversation, type ApiMessage } from "@/services/chatApi";
import { useChatSocket } from "@/hooks/useChatSocket";
import { getCurrentUserId } from "@/services/api";

type TypingState = { userId: number; username: string } | null;

type ChatContextValue = {
  conversation: ApiConversation | null;
  messages: ApiMessage[];
  loading: boolean;
  connected: boolean;
  typing: TypingState;
  currentUserId: number | null;
  startConversationWith: (otherUserId: number) => Promise<void>;
  sendMessage: (content: string) => void;
};

const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [conversation, setConversation] = useState<ApiConversation | null>(null);
  const [messages, setMessages] = useState<ApiMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [typing, setTyping] = useState<TypingState>(null);
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);

  useEffect(() => {
    getCurrentUserId().then(setCurrentUserId);
  }, []);

  const handleIncoming = useCallback((msg: ApiMessage) => {
    setMessages((current) => {
      // Guard against duplicates if the socket echoes a message you already appended optimistically
      if (current.some((m) => m.id === msg.id)) return current;
      return [...current, msg];
    });
  }, []);

  const handleTyping = useCallback(
    (userId: number, username: string, isTyping: boolean) => {
      setTyping(isTyping ? { userId, username } : null);
    },
    [],
  );

  const { connected, sendMessage: sendSocketMessage, sendTyping } = useChatSocket(
    conversation?.id ?? null,
    handleIncoming,
    handleTyping,
  );

  const startConversationWith = useCallback(async (otherUserId: number) => {
    setLoading(true);
    try {
      console.log("Starting conversation with user:", otherUserId);
      const conv = await chatApi.startPrivateConversation(otherUserId);
      console.log("Conversation ready:", conv.id);
      setConversation(conv);

      const history = await chatApi.getMessages(conv.id);
      setMessages(history);
    } catch (err) {
      console.error("Failed to start conversation:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const sendMessage = useCallback(
    (content: string) => {
      sendSocketMessage(content); // server broadcasts it back; handleIncoming appends it
      sendTyping(false);
    },
    [sendSocketMessage, sendTyping],
  );

  return (
    <ChatContext.Provider
      value={{
        conversation,
        messages,
        loading,
        connected,
        typing,
        currentUserId,
        startConversationWith,
        sendMessage,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used within a ChatProvider");
  return ctx;
}