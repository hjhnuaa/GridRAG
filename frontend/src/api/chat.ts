import { fetchEventSource } from "@microsoft/fetch-event-source";

import type {
  ChatAskRequest,
  ChatDebugResponse,
  ChatMessage,
  ChatSessionDeleteResponse,
  MemoryDeleteResponse,
  MemoryItem,
  MemorySearchResponse
} from "../types/chat";
import type { PaginatedData } from "../types/common";
import { API_BASE_URL, apiClient, unwrapResponse } from "./client";

export interface ChatStreamHandlers {
  onChunk: (content: string) => void;
  onSources: (sources: ChatMessage["sources"]) => void;
  onError: (message: string) => void;
  onDone: () => void;
}

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

export async function startChatStream(
  payload: ChatAskRequest,
  handlers: ChatStreamHandlers,
  signal: AbortSignal
): Promise<void> {
  await fetchEventSource(`${API_BASE_URL}/chat/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload),
    signal,
    async onopen(response) {
      if (!response.ok) {
        throw new Error("问答请求打开失败。");
      }
    },
    onmessage(event) {
      const data = JSON.parse(event.data) as
        | { type: "chunk"; content: string }
        | { type: "sources"; sources: ChatMessage["sources"] }
        | { type: "error"; message: string }
        | { type: "done" };
      if (data.type === "chunk") {
        handlers.onChunk(data.content);
      }
      if (data.type === "sources") {
        handlers.onSources(data.sources);
      }
      if (data.type === "error") {
        handlers.onError(data.message);
      }
      if (data.type === "done") {
        handlers.onDone();
      }
    },
    onerror(error) {
      if (!isAbortError(error)) {
        handlers.onError(error instanceof Error ? error.message : "流式连接中断。");
      }
      throw error;
    }
  });
}

export async function fetchChatHistory(sessionId: string): Promise<PaginatedData<ChatMessage>> {
  return unwrapResponse(
    apiClient.get(`/chat/history/${sessionId}`, {
      params: {
        page: 1,
        page_size: 200
      }
    })
  );
}

export async function fetchChatDebug(payload: ChatAskRequest): Promise<ChatDebugResponse> {
  return unwrapResponse(apiClient.post("/chat/debug", payload));
}

export async function deleteChatSession(sessionId: string): Promise<ChatSessionDeleteResponse> {
  return unwrapResponse(apiClient.delete(`/chat/sessions/${sessionId}`));
}

export async function fetchMemories(sessionId: string, query = ""): Promise<MemorySearchResponse> {
  return unwrapResponse(
    apiClient.get(`/memory/${sessionId}`, {
      params: {
        query,
        limit: 50
      }
    })
  );
}

export async function createMemory(sessionId: string, content: string): Promise<MemoryItem> {
  return unwrapResponse(
    apiClient.post("/memory", {
      session_id: sessionId,
      content,
      memory_type: "manual",
      metadata: { source: "manual" }
    })
  );
}

export async function deleteMemory(memoryId: string): Promise<{ deleted: boolean }> {
  return unwrapResponse(apiClient.delete(`/memory/${memoryId}`));
}

export async function clearSessionMemories(sessionId: string): Promise<MemoryDeleteResponse> {
  return unwrapResponse(apiClient.delete(`/memory/sessions/${sessionId}`));
}
