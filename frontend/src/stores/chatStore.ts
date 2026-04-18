import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { ChatMessage, LocalSessionSummary } from "../types/chat";

interface ChatState {
  currentSessionId: string;
  sessions: LocalSessionSummary[];
  messagesBySession: Record<string, ChatMessage[]>;
  setCurrentSession: (sessionId: string) => void;
  createSession: () => string;
  hydrateHistory: (sessionId: string, messages: ChatMessage[]) => void;
  upsertMessage: (sessionId: string, message: ChatMessage) => void;
  patchAssistantMessage: (sessionId: string, messageId: string, content: string) => void;
  attachSources: (sessionId: string, messageId: string, sources: ChatMessage["sources"]) => void;
  clearCurrentView: (sessionId: string) => void;
}

function createSessionTitle(messages: ChatMessage[]): string {
  const firstUserMessage = messages.find((message) => message.role === "user");
  return firstUserMessage?.content.slice(0, 18) || "新会话";
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      currentSessionId: "",
      sessions: [],
      messagesBySession: {},
      setCurrentSession: (sessionId) => set({ currentSessionId: sessionId }),
      createSession: () => {
        const sessionId = crypto.randomUUID();
        set((state) => ({
          currentSessionId: sessionId,
          sessions: [
            {
              id: sessionId,
              title: "新会话",
              updatedAt: new Date().toISOString()
            },
            ...state.sessions
          ]
        }));
        return sessionId;
      },
      hydrateHistory: (sessionId, messages) =>
        set((state) => ({
          messagesBySession: {
            ...state.messagesBySession,
            [sessionId]: messages
          },
          sessions: [
            {
              id: sessionId,
              title: createSessionTitle(messages),
              updatedAt: messages[messages.length - 1]?.created_at ?? new Date().toISOString()
            },
            ...state.sessions.filter((item) => item.id !== sessionId)
          ]
        })),
      upsertMessage: (sessionId, message) =>
        set((state) => {
          const list = state.messagesBySession[sessionId] ?? [];
          const existingIndex = list.findIndex((item) => item.id === message.id);
          const nextMessages =
            existingIndex >= 0
              ? list.map((item, index) => (index === existingIndex ? message : item))
              : [...list, message];
          return {
            messagesBySession: {
              ...state.messagesBySession,
              [sessionId]: nextMessages
            },
            sessions: [
              {
                id: sessionId,
                title: createSessionTitle(nextMessages),
                updatedAt: message.created_at
              },
              ...state.sessions.filter((item) => item.id !== sessionId)
            ]
          };
        }),
      patchAssistantMessage: (sessionId, messageId, content) =>
        set((state) => ({
          messagesBySession: {
            ...state.messagesBySession,
            [sessionId]: (state.messagesBySession[sessionId] ?? []).map((item) =>
              item.id === messageId ? { ...item, content } : item
            )
          }
        })),
      attachSources: (sessionId, messageId, sources) =>
        set((state) => ({
          messagesBySession: {
            ...state.messagesBySession,
            [sessionId]: (state.messagesBySession[sessionId] ?? []).map((item) =>
              item.id === messageId ? { ...item, sources } : item
            )
          }
        })),
      clearCurrentView: (sessionId) =>
        set((state) => ({
          messagesBySession: {
            ...state.messagesBySession,
            [sessionId]: []
          }
        }))
    }),
    {
      name: "gridrag-chat-store",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        currentSessionId: state.currentSessionId,
        sessions: state.sessions,
        messagesBySession: state.messagesBySession
      })
    }
  )
);

