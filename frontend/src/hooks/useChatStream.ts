import { message } from "antd";
import { useRef, useState } from "react";

import { startChatStream } from "../api/chat";
import type { ChatAskRequest, ChatMessage } from "../types/chat";
import { useChatStore } from "../stores/chatStore";

export type ChatStreamStatus = "idle" | "connecting" | "answering" | "sources";

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

export function useChatStream(sessionId: string): {
  streaming: boolean;
  streamingMessageId: string | null;
  streamStatus: ChatStreamStatus;
  sendQuestion: (payload: ChatAskRequest) => Promise<void>;
  cancel: () => void;
} {
  const [streaming, setStreaming] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const [streamStatus, setStreamStatus] = useState<ChatStreamStatus>("idle");
  const abortRef = useRef<AbortController | null>(null);
  const activeAssistantIdRef = useRef<string | null>(null);
  const inFlightRef = useRef(false);
  const { upsertMessage, patchAssistantMessage, attachSources } = useChatStore();

  const sendQuestion = async (payload: ChatAskRequest): Promise<void> => {
    if (inFlightRef.current) {
      return;
    }
    inFlightRef.current = true;

    const assistantId = crypto.randomUUID();
    const targetSessionId = payload.session_id || sessionId;
    let errorReported = false;

    const reportError = (errorMessage: string): void => {
      if (!errorReported) {
        message.error(errorMessage);
        errorReported = true;
      }
      const current = useChatStore
        .getState()
        .messagesBySession[targetSessionId]?.find((item) => item.id === assistantId);
      if (!current?.content.trim()) {
        patchAssistantMessage(targetSessionId, assistantId, `回答生成失败：${errorMessage}`);
      }
    };

    upsertMessage(targetSessionId, {
      id: assistantId,
      session_id: targetSessionId,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString()
    });

    const controller = new AbortController();
    abortRef.current = controller;
    activeAssistantIdRef.current = assistantId;
    setStreamingMessageId(assistantId);
    setStreaming(true);
    setStreamStatus("connecting");
    try {
      await startChatStream(
        payload,
        {
          onOpen: () => {
            setStreamStatus("answering");
          },
          onChunk: (content) => {
            setStreamStatus("answering");
            const current = useChatStore
              .getState()
              .messagesBySession[targetSessionId]?.find((item) => item.id === assistantId);
            patchAssistantMessage(targetSessionId, assistantId, `${current?.content ?? ""}${content}`);
          },
          onSources: (sources) => {
            setStreamStatus("sources");
            attachSources(targetSessionId, assistantId, sources);
          },
          onError: (errorMessage) => {
            reportError(errorMessage);
          },
          onDone: () => {
            setStreaming(false);
            setStreamStatus("idle");
            setStreamingMessageId(null);
          }
        },
        controller.signal
      );
    } catch (error) {
      if (!isAbortError(error)) {
        reportError(error instanceof Error ? error.message : "问答失败。");
      }
      setStreaming(false);
      setStreamStatus("idle");
      setStreamingMessageId(null);
    } finally {
      abortRef.current = null;
      activeAssistantIdRef.current = null;
      inFlightRef.current = false;
    }
  };

  const cancel = (): void => {
    const assistantId = activeAssistantIdRef.current;
    if (assistantId && sessionId) {
      const current = useChatStore.getState().messagesBySession[sessionId]?.find((item) => item.id === assistantId);
      if (!current?.content.trim()) {
        patchAssistantMessage(sessionId, assistantId, "已停止生成。");
      }
    }
    abortRef.current?.abort();
    inFlightRef.current = false;
    setStreaming(false);
    setStreamStatus("idle");
    setStreamingMessageId(null);
  };

  return {
    streaming,
    streamingMessageId,
    streamStatus,
    sendQuestion,
    cancel
  };
}
