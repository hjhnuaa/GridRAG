import { message } from "antd";
import { useRef, useState } from "react";

import { startChatStream, startGuidedChatStream, type ChatStreamHandlers } from "../api/chat";
import type { ChatAskRequest, ChatGuideRequest } from "../types/chat";
import { useChatStore } from "../stores/chatStore";

export type ChatStreamStatus = "idle" | "connecting" | "answering" | "sources";

type StreamStarter = (
  payload: ChatAskRequest | ChatGuideRequest,
  handlers: ChatStreamHandlers,
  signal: AbortSignal
) => Promise<void>;

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

export function useChatStream(sessionId: string): {
  streaming: boolean;
  streamingMessageId: string | null;
  streamStatus: ChatStreamStatus;
  sendQuestion: (payload: ChatAskRequest) => Promise<void>;
  guideAnswer: (payload: ChatGuideRequest) => Promise<void>;
  getActiveAnswerContent: () => string;
  cancel: () => void;
} {
  const [streaming, setStreaming] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const [streamStatus, setStreamStatus] = useState<ChatStreamStatus>("idle");
  const abortRef = useRef<AbortController | null>(null);
  const activeAssistantIdRef = useRef<string | null>(null);
  const activeSessionIdRef = useRef<string | null>(null);
  const flushFrameRef = useRef<number | null>(null);
  const pendingContentRef = useRef("");
  const renderedContentRef = useRef("");
  const inFlightRef = useRef(false);
  const { upsertMessage, patchAssistantMessage, markMessageInterrupted, attachSources } = useChatStore();

  const flushPendingContent = (targetSessionId: string, assistantId: string): void => {
    if (flushFrameRef.current !== null) {
      cancelAnimationFrame(flushFrameRef.current);
      flushFrameRef.current = null;
    }
    if (!pendingContentRef.current) {
      return;
    }
    renderedContentRef.current += pendingContentRef.current;
    pendingContentRef.current = "";
    patchAssistantMessage(targetSessionId, assistantId, renderedContentRef.current);
  };

  const scheduleFlush = (targetSessionId: string, assistantId: string): void => {
    if (flushFrameRef.current !== null) {
      return;
    }
    flushFrameRef.current = requestAnimationFrame(() => {
      flushFrameRef.current = null;
      flushPendingContent(targetSessionId, assistantId);
    });
  };

  const runStream = async (
    payload: ChatAskRequest | ChatGuideRequest,
    startStream: StreamStarter,
    assistantId: string,
    targetSessionId: string
  ): Promise<void> => {
    let errorReported = false;
    const isActiveStream = (): boolean =>
      activeAssistantIdRef.current === assistantId && activeSessionIdRef.current === targetSessionId;

    const reportError = (errorMessage: string): void => {
      if (!isActiveStream()) {
        return;
      }
      flushPendingContent(targetSessionId, assistantId);
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

    const controller = new AbortController();
    abortRef.current = controller;
    activeAssistantIdRef.current = assistantId;
    activeSessionIdRef.current = targetSessionId;
    pendingContentRef.current = "";
    renderedContentRef.current = "";
    setStreamingMessageId(assistantId);
    setStreaming(true);
    setStreamStatus("connecting");

    try {
      await startStream(
        payload,
        {
          onOpen: () => {
            if (!isActiveStream()) {
              return;
            }
            setStreamStatus("answering");
          },
          onChunk: (content) => {
            if (!isActiveStream()) {
              return;
            }
            setStreamStatus("answering");
            pendingContentRef.current += content;
            scheduleFlush(targetSessionId, assistantId);
          },
          onSources: (sources) => {
            if (!isActiveStream()) {
              return;
            }
            flushPendingContent(targetSessionId, assistantId);
            setStreamStatus("sources");
            attachSources(targetSessionId, assistantId, sources);
          },
          onError: (errorMessage) => {
            reportError(errorMessage);
          },
          onDone: () => {
            if (!isActiveStream()) {
              return;
            }
            flushPendingContent(targetSessionId, assistantId);
            setStreaming(false);
            setStreamStatus("idle");
            setStreamingMessageId(null);
          }
        },
        controller.signal
      );
    } catch (error) {
      if (!isAbortError(error) && isActiveStream()) {
        reportError(error instanceof Error ? error.message : "问答失败。");
      }
      if (isActiveStream()) {
        setStreaming(false);
        setStreamStatus("idle");
        setStreamingMessageId(null);
      }
    } finally {
      if (isActiveStream()) {
        flushPendingContent(targetSessionId, assistantId);
        abortRef.current = null;
        activeAssistantIdRef.current = null;
        activeSessionIdRef.current = null;
        inFlightRef.current = false;
      }
    }
  };

  const sendQuestion = async (payload: ChatAskRequest): Promise<void> => {
    if (inFlightRef.current) {
      return;
    }
    inFlightRef.current = true;

    const assistantId = crypto.randomUUID();
    const targetSessionId = payload.session_id || sessionId;
    upsertMessage(targetSessionId, {
      id: assistantId,
      session_id: targetSessionId,
      role: "assistant",
      content: "",
      status: "complete",
      created_at: new Date().toISOString()
    });

    await runStream(payload, startChatStream as StreamStarter, assistantId, targetSessionId);
  };

  const guideAnswer = async (payload: ChatGuideRequest): Promise<void> => {
    const targetSessionId = payload.session_id || sessionId;
    const interruptedAssistantId = activeAssistantIdRef.current;
    if (interruptedAssistantId) {
      flushPendingContent(targetSessionId, interruptedAssistantId);
      markMessageInterrupted(targetSessionId, interruptedAssistantId);
    }
    abortRef.current?.abort();
    inFlightRef.current = true;

    upsertMessage(targetSessionId, {
      id: crypto.randomUUID(),
      session_id: targetSessionId,
      role: "user",
      content: `引导回答：${payload.instruction}`,
      status: "complete",
      created_at: new Date().toISOString()
    });

    const assistantId = crypto.randomUUID();
    upsertMessage(targetSessionId, {
      id: assistantId,
      session_id: targetSessionId,
      role: "assistant",
      content: "",
      status: "complete",
      created_at: new Date().toISOString()
    });

    await runStream(payload, startGuidedChatStream as StreamStarter, assistantId, targetSessionId);
  };

  const getActiveAnswerContent = (): string => {
    const assistantId = activeAssistantIdRef.current;
    const targetSessionId = activeSessionIdRef.current ?? sessionId;
    if (assistantId && targetSessionId) {
      flushPendingContent(targetSessionId, assistantId);
    }
    return renderedContentRef.current;
  };

  const cancel = (): void => {
    const assistantId = activeAssistantIdRef.current;
    const targetSessionId = activeSessionIdRef.current ?? sessionId;
    if (assistantId && targetSessionId) {
      flushPendingContent(targetSessionId, assistantId);
      const current = useChatStore
        .getState()
        .messagesBySession[targetSessionId]?.find((item) => item.id === assistantId);
      if (!current?.content.trim()) {
        patchAssistantMessage(targetSessionId, assistantId, "已停止生成。");
      }
      markMessageInterrupted(targetSessionId, assistantId);
    }
    abortRef.current?.abort();
    inFlightRef.current = false;
    setStreaming(false);
    setStreamStatus("idle");
    setStreamingMessageId(null);
    activeSessionIdRef.current = null;
    activeAssistantIdRef.current = null;
  };

  return {
    streaming,
    streamingMessageId,
    streamStatus,
    sendQuestion,
    guideAnswer,
    getActiveAnswerContent,
    cancel
  };
}
