// services/chatApi.ts

import { clientApi } from "@/services/api";

export type ApiParticipant = {
  user_id: number;
  username: string;
  full_name: string;
  is_admin: boolean;
  joined_at: string;
};

export type ApiConversation = {
  id: number;
  conversation_type: "private" | "group";
  name: string | null;
  participants: ApiParticipant[];
  created_at: string;
  updated_at: string;
};

export type ApiMessage = {
  id: number;
  conversation: number;
  sender_id: number;
  sender_username: string;
  content: string;
  message_type: "text" | "image" | "file" | "audio" | "video";
  file_url?: string | null;
  file_name?: string | null;
  file_size?: number | null;
  created_at: string;
  updated_at: string;
  is_edited: boolean;
  is_deleted: boolean;
};

export const chatApi = {
  listConversations: async () => {
    const { data } = await clientApi.get<ApiConversation[]>("/api/chat/conversations/");
    return data;
  },

  getConversation: async (id: number) => {
    const { data } = await clientApi.get<ApiConversation>(`/api/chat/conversations/${id}/`);
    return data;
  },

  getMessages: async (id: number) => {
    const { data } = await clientApi.get<ApiMessage[]>(`/api/chat/conversations/${id}/messages/`);
    return data;
  },

  // Starts (or reuses, per your ConversationService) a private conversation
  startPrivateConversation: async (otherUserId: number) => {
    const { data } = await clientApi.post<ApiConversation>("/api/chat/conversations/", {
      conversation_type: "private",
      user_id: otherUserId,
    });
    return data;
  },
  
  uploadFile: async (
    conversationId: number,
    file: { uri: string; name: string; type: string },
  ) => {
    const formData = new FormData();
    formData.append("file", {
      uri: file.uri,
      name: file.name,
      type: file.type,
    } as any);

    const { data } = await clientApi.post<ApiMessage>(
      `/api/chat/conversations/${conversationId}/messages/upload/`,
      formData,
    );
    return data;
  },
};
