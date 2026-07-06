import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { ChatMessage, LocalSessionSummary } from "../types/chat";

const DEFAULT_SESSION_TITLE = "新会话";
const MESSAGE_MATCH_WINDOW_MS = 5 * 60 * 1000;

interface ChatState {
  currentSessionId: string;
  sessions: LocalSessionSummary[];
  messagesBySession: Record<string, ChatMessage[]>;
  setCurrentSession: (sessionId: string) => void;
  createSession: () => string;
  hydrateSessions: (sessions: LocalSessionSummary[]) => void;
  hydrateHistory: (sessionId: string, messages: ChatMessage[]) => void;
  upsertMessage: (sessionId: string, message: ChatMessage) => void;
  patchAssistantMessage: (sessionId: string, messageId: string, content: string) => void;
  markMessageInterrupted: (sessionId: string, messageId: string) => void;
  attachSources: (sessionId: string, messageId: string, sources: ChatMessage["sources"]) => void;
  clearCurrentView: (sessionId: string) => void;
  deleteSession: (sessionId: string) => string;
}

function createSessionTitle(messages: ChatMessage[]): string {
  const firstUserMessage = messages.find((message) => message.role === "user");
  return firstUserMessage?.content.trim().slice(0, 24) || DEFAULT_SESSION_TITLE;
}

function sortSessions(sessions: LocalSessionSummary[]): LocalSessionSummary[] {
  return [...sessions].sort((a, b) => dayValue(b.updatedAt) - dayValue(a.updatedAt));
}

function sortMessages(messages: ChatMessage[]): ChatMessage[] {
  return [...messages].sort((a, b) => dayValue(a.created_at) - dayValue(b.created_at));
}

function dayValue(value: string | undefined): number {
  const time = value ? new Date(value).getTime() : Number.NaN;
  return Number.isNaN(time) ? 0 : time;
}

function isSamePersistedMessage(local: ChatMessage, remote: ChatMessage): boolean {
  if (local.id === remote.id) {
    return true;
  }
  if (local.role !== remote.role || local.content.trim() !== remote.content.trim()) {
    return false;
  }
  return Math.abs(dayValue(local.created_at) - dayValue(remote.created_at)) <= MESSAGE_MATCH_WINDOW_MS;
}

function mergeHistory(existing: ChatMessage[], remoteMessages: ChatMessage[]): ChatMessage[] {
  const pendingLocal = existing.filter(
    (local) => !remoteMessages.some((remote) => isSamePersistedMessage(local, remote))
  );
  return sortMessages([...remoteMessages, ...pendingLocal]);
}

function upsertSessionSummary(
  sessions: LocalSessionSummary[],
  summary: LocalSessionSummary
): LocalSessionSummary[] {
  return sortSessions([summary, ...sessions.filter((item) => item.id !== summary.id)]);
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
        const now = new Date().toISOString();
        set((state) => ({
          currentSessionId: sessionId,
          sessions: upsertSessionSummary(state.sessions, {
            id: sessionId,
            title: DEFAULT_SESSION_TITLE,
            createdAt: now,
            updatedAt: now,
            messageCount: 0
          })
        }));
        return sessionId;
      },
      hydrateSessions: (remoteSessions) =>
        set((state) => {
          const byId = new Map<string, LocalSessionSummary>();
          state.sessions.forEach((item) => byId.set(item.id, item));
          remoteSessions.forEach((item) => byId.set(item.id, { ...byId.get(item.id), ...item }));
          const nextSessions = sortSessions(Array.from(byId.values()));
          return {
            sessions: nextSessions,
            currentSessionId: state.currentSessionId || nextSessions[0]?.id || ""
          };
        }),
      hydrateHistory: (sessionId, messages) =>
        set((state) => {
          const existingMessages = state.messagesBySession[sessionId] ?? [];
          const nextMessages = mergeHistory(existingMessages, messages);
          const existingSummary = state.sessions.find((item) => item.id === sessionId);
          const latestMessageTime = nextMessages[nextMessages.length - 1]?.created_at;
          const summary: LocalSessionSummary = {
            id: sessionId,
            title: nextMessages.length ? createSessionTitle(nextMessages) : existingSummary?.title ?? DEFAULT_SESSION_TITLE,
            createdAt: existingSummary?.createdAt ?? nextMessages[0]?.created_at,
            updatedAt: latestMessageTime ?? existingSummary?.updatedAt ?? new Date().toISOString(),
            messageCount: nextMessages.length || existingSummary?.messageCount || 0
          };

          return {
            messagesBySession: {
              ...state.messagesBySession,
              [sessionId]: nextMessages
            },
            sessions: upsertSessionSummary(state.sessions, summary)
          };
        }),
      upsertMessage: (sessionId, message) =>
        set((state) => {
          const list = state.messagesBySession[sessionId] ?? [];
          const existingIndex = list.findIndex((item) => item.id === message.id);
          const nextMessages =
            existingIndex >= 0
              ? list.map((item, index) => (index === existingIndex ? message : item))
              : [...list, message];
          const existingSummary = state.sessions.find((item) => item.id === sessionId);
          return {
            messagesBySession: {
              ...state.messagesBySession,
              [sessionId]: nextMessages
            },
            sessions: upsertSessionSummary(state.sessions, {
              id: sessionId,
              title: createSessionTitle(nextMessages),
              createdAt: existingSummary?.createdAt ?? nextMessages[0]?.created_at,
              updatedAt: message.created_at,
              messageCount: nextMessages.length
            })
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
      markMessageInterrupted: (sessionId, messageId) =>
        set((state) => ({
          messagesBySession: {
            ...state.messagesBySession,
            [sessionId]: (state.messagesBySession[sessionId] ?? []).map((item) =>
              item.id === messageId ? { ...item, status: "interrupted" } : item
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
        })),
      deleteSession: (sessionId) => {
        const state = get();
        const nextSessions = state.sessions.filter((item) => item.id !== sessionId);
        const { [sessionId]: _removed, ...nextMessagesBySession } = state.messagesBySession;
        const nextCurrentSessionId =
          state.currentSessionId === sessionId ? nextSessions[0]?.id ?? "" : state.currentSessionId;

        set({
          currentSessionId: nextCurrentSessionId,
          sessions: nextSessions,
          messagesBySession: nextMessagesBySession
        });
        return nextCurrentSessionId;
      }
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
