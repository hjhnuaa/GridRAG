import { DownOutlined, RobotOutlined, UserOutlined } from "@ant-design/icons";
import { Avatar, Button, Empty } from "antd";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";

import type { ChatMessage } from "../../types/chat";
import { SourceCard } from "../SourceCard/SourceCard";

interface ChatWindowProps {
  messages: ChatMessage[];
}

const SCROLL_THRESHOLD = 96;

export function ChatWindow({ messages }: ChatWindowProps): JSX.Element {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [stickToBottom, setStickToBottom] = useState(true);
  const sessionMarker = messages.at(-1)?.session_id ?? "empty";
  const lastMessage = messages.at(-1);
  const lastMessageSignature = `${lastMessage?.id ?? "none"}:${lastMessage?.content.length ?? 0}:${
    lastMessage?.sources?.length ?? 0
  }`;

  const scrollToBottom = (behavior: ScrollBehavior = "auto"): void => {
    const element = scrollRef.current;
    if (!element) {
      return;
    }
    element.scrollTo({
      top: element.scrollHeight,
      behavior
    });
  };

  const handleScroll = (): void => {
    const element = scrollRef.current;
    if (!element) {
      return;
    }
    const distanceToBottom = element.scrollHeight - element.scrollTop - element.clientHeight;
    setStickToBottom(distanceToBottom <= SCROLL_THRESHOLD);
  };

  useEffect(() => {
    setStickToBottom(true);
    requestAnimationFrame(() => {
      scrollToBottom("auto");
    });
  }, [sessionMarker]);

  useEffect(() => {
    if (!messages.length || !stickToBottom) {
      return;
    }
    requestAnimationFrame(() => {
      scrollToBottom(messages.length > 1 ? "smooth" : "auto");
    });
  }, [lastMessageSignature, messages.length, stickToBottom]);

  return (
    <div className="glass-card chat-window-card">
      <div className="chat-window-scroll" ref={scrollRef} onScroll={handleScroll}>
        {messages.length ? (
          <div className="chat-message-stack">
            {messages.map((message) => {
              const isAssistant = message.role === "assistant";
              return (
                <div
                  className={`chat-message-row ${isAssistant ? "is-assistant" : "is-user"}`}
                  key={message.id}
                >
                  <div className={`chat-message-group ${isAssistant ? "is-assistant" : "is-user"}`}>
                    <Avatar
                      icon={isAssistant ? <RobotOutlined /> : <UserOutlined />}
                      style={{
                        flexShrink: 0,
                        background: isAssistant
                          ? "linear-gradient(135deg, rgba(175, 63, 45, 0.92), rgba(183, 139, 60, 0.82))"
                          : "rgba(34, 23, 16, 0.82)"
                      }}
                    />
                    <div className="chat-message-content">
                      <div className={`chat-bubble ${isAssistant ? "assistant" : "user"}`}>
                        {isAssistant ? (
                          <div className="markdown-body">
                            <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
                              {message.content || "正在生成中..."}
                            </ReactMarkdown>
                          </div>
                        ) : (
                          <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.8 }}>{message.content}</div>
                        )}
                      </div>
                      {isAssistant && message.sources?.length ? <SourceCard sources={message.sources} /> : null}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="chat-empty-state">
            <Empty description="输入问题后开始检索政策、手册与历史工单。" />
          </div>
        )}
      </div>

      {!stickToBottom && messages.length ? (
        <Button
          className="chat-scroll-button"
          icon={<DownOutlined />}
          onClick={() => {
            setStickToBottom(true);
            scrollToBottom("smooth");
          }}
          shape="round"
          type="default"
        >
          回到底部
        </Button>
      ) : null}
    </div>
  );
}
