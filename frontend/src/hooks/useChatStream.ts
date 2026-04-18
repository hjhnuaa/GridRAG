import { message } from "antd";
import { useRef, useState } from "react";

import { startChatStream } from "../api/chat";
import type { ChatAskRequest, ChatMessage } from "../types/chat";
import { useChatStore } from "../stores/chatStore";

export function useChatStream(sessionId: string): {
  streaming: boolean;
  sendQuestion: (payload: ChatAskRequest) => Promise<void>;
  cancel: () => void;
} {
  const [streaming, setStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const { upsertMessage, patchAssistantMessage, attachSources } = useChatStore();

  const sendQuestion = async (payload: ChatAskRequest): Promise<void> => {
    const assistantId = crypto.randomUUID();
    upsertMessage(sessionId, {
      id: assistantId,
      session_id: sessionId,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString()
    });

    const controller = new AbortController();
    abortRef.current = controller;
    setStreaming(true);
    try {
      await startChatStream(
        payload,
        {
          onChunk: (content) => {
            const current = useChatStore.getState().messagesBySession[sessionId]?.find((item) => item.id === assistantId);
            patchAssistantMessage(sessionId, assistantId, `${current?.content ?? ""}${content}`);
          },
          onSources: (sources) => {
            attachSources(sessionId, assistantId, sources);
          },
          onError: (errorMessage) => {
            message.error(errorMessage);
          },
          onDone: () => {
            setStreaming(false);
          }
        },
        controller.signal
      );
    } catch (error) {
      message.error(error instanceof Error ? error.message : "问答失败。");
      setStreaming(false);
    }
  };

  const cancel = (): void => {
    abortRef.current?.abort();
    setStreaming(false);
  };

  return {
    streaming,
    sendQuestion,
    cancel
  };
}

