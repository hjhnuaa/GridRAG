import { fetchEventSource } from "@microsoft/fetch-event-source";

import type { ChatAskRequest, ChatDebugResponse, ChatMessage } from "../types/chat";
import type { PaginatedData } from "../types/common";
import { apiClient, unwrapResponse } from "./client";
import { API_BASE_URL } from "./config";

export interface ChatStreamHandlers {
  onChunk: (content: string) => void;
  onSources: (sources: ChatMessage["sources"]) => void;
  onError: (message: string) => void;
  onDone: () => void;
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
      handlers.onError(error instanceof Error ? error.message : "流式连接中断。");
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
