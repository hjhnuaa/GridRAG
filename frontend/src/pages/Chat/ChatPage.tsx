import {
  BugOutlined,
  ClearOutlined,
  DeleteOutlined,
  DatabaseOutlined,
  GlobalOutlined,
  MessageOutlined,
  PlusOutlined,
  SendOutlined
} from "@ant-design/icons";
import {
  Button,
  Drawer,
  Empty,
  Input,
  List,
  Popconfirm,
  Segmented,
  Select,
  Space,
  Spin,
  Switch,
  Tag,
  Typography,
  message
} from "antd";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import dayjs from "dayjs";
import { useEffect, useRef, useState } from "react";

import {
  clearSessionMemories,
  clearScopedMemories,
  createChatSession,
  createMemory,
  createScopedMemory,
  deleteChatSession,
  deleteMemory,
  fetchChatDebug,
  fetchChatHistory,
  fetchChatSessions,
  fetchMemories,
  fetchScopedMemories
} from "../../api/chat";
import { ChatWindow } from "../../components/ChatWindow/ChatWindow";
import { RagDebugPanel } from "../../components/RagDebugPanel/RagDebugPanel";
import { useChatStream } from "../../hooks/useChatStream";
import { useChatStore } from "../../stores/chatStore";
import type { ChatAskRequest, ChatSessionSummary, LocalSessionSummary, MemoryItem, MemoryScope } from "../../types/chat";
import { formatDateTime } from "../../utils/presenters";

type MemoryMode = "session" | "global";

const GLOBAL_MEMORY_SCOPE: MemoryScope = "global";

const docTypeOptions = [
  { label: "政策文件", value: "policy" },
  { label: "工作手册", value: "manual" },
  { label: "历史工单", value: "ticket" },
  { label: "典型案例", value: "case" }
];

function groupSessions(sessions: LocalSessionSummary[]): Array<{ label: string; items: LocalSessionSummary[] }> {
  const grouped = new Map<string, LocalSessionSummary[]>();
  sessions.forEach((item) => {
    const key = dayjs(item.updatedAt).format("YYYY-MM-DD");
    const bucket = grouped.get(key) ?? [];
    bucket.push(item);
    grouped.set(key, bucket);
  });
  return Array.from(grouped.entries()).map(([label, items]) => ({ label, items }));
}

function toLocalSession(item: ChatSessionSummary): LocalSessionSummary {
  return {
    id: item.id,
    title: item.title,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
    messageCount: item.message_count
  };
}

function getMemoryScopeLabel(item: MemoryItem): string {
  const scope = typeof item.metadata.scope === "string" ? item.metadata.scope : "session";
  const labels: Record<string, string> = {
    organization: "组织",
    project: "项目",
    personal: "个人",
    local: "本地",
    global: "全局",
    auto: "自动",
    session: "会话"
  };
  return labels[scope] ?? "会话";
}

export function ChatPage(): JSX.Element {
  const {
    currentSessionId,
    sessions,
    messagesBySession,
    createSession,
    hydrateSessions,
    hydrateHistory,
    setCurrentSession,
    upsertMessage,
    deleteSession
  } = useChatStore();
  const [question, setQuestion] = useState("");
  const [docTypes, setDocTypes] = useState<string[]>(["policy", "manual"]);
  const [enableWebSearch, setEnableWebSearch] = useState(false);
  const [debugOpen, setDebugOpen] = useState(false);
  const [memoryOpen, setMemoryOpen] = useState(false);
  const [memoryMode, setMemoryMode] = useState<MemoryMode>("session");
  const [memoryQuery, setMemoryQuery] = useState("");
  const [memoryContent, setMemoryContent] = useState("");
  const sendingRef = useRef(false);
  const queryClient = useQueryClient();

  const createSessionMutation = useMutation({
    mutationFn: (sessionId: string) => createChatSession({ session_id: sessionId }),
    onSuccess: (result) => {
      hydrateSessions([toLocalSession(result)]);
      void queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
    },
    onError: () => {
      message.warning("会话已先保存到本地，发送消息时会再次同步到数据库。");
    }
  });

  const sessionsQuery = useQuery({
    queryKey: ["chat-sessions"],
    queryFn: fetchChatSessions
  });

  useEffect(() => {
    if (sessionsQuery.data) {
      hydrateSessions(sessionsQuery.data.items.map(toLocalSession));
    }
  }, [hydrateSessions, sessionsQuery.data]);

  useEffect(() => {
    if (sessionsQuery.isLoading || currentSessionId) {
      return;
    }
    const existingSessionId = sessions[0]?.id;
    if (existingSessionId) {
      setCurrentSession(existingSessionId);
      return;
    }

    const sessionId = createSession();
    void createSessionMutation.mutateAsync(sessionId);
  }, [createSession, createSessionMutation, currentSessionId, sessions, sessionsQuery.isLoading, setCurrentSession]);

  const historyQuery = useQuery({
    queryKey: ["chat-history", currentSessionId],
    queryFn: () => fetchChatHistory(currentSessionId),
    enabled: Boolean(currentSessionId)
  });

  useEffect(() => {
    if (currentSessionId && historyQuery.data) {
      hydrateHistory(currentSessionId, historyQuery.data.items);
    }
  }, [currentSessionId, historyQuery.data, hydrateHistory]);

  const messages = currentSessionId ? messagesBySession[currentSessionId] ?? [] : [];
  const sessionGroups = groupSessions(sessions);
  const { sendQuestion, streaming, streamingMessageId, streamStatus, cancel } = useChatStream(currentSessionId);
  const debugMutation = useMutation({
    mutationFn: (payload: ChatAskRequest) => fetchChatDebug(payload)
  });
  const memoryQueryResult = useQuery({
    queryKey: ["memories", memoryMode, currentSessionId, memoryQuery],
    queryFn: () =>
      memoryMode === "global"
        ? fetchScopedMemories(GLOBAL_MEMORY_SCOPE, memoryQuery)
        : fetchMemories(currentSessionId, memoryQuery),
    enabled: memoryOpen && (memoryMode === "global" || Boolean(currentSessionId))
  });
  const createMemoryMutation = useMutation({
    mutationFn: ({ content, mode }: { content: string; mode: MemoryMode }) =>
      mode === "global" ? createScopedMemory(GLOBAL_MEMORY_SCOPE, content) : createMemory(currentSessionId, content),
    onSuccess: (_, variables) => {
      setMemoryContent("");
      void queryClient.invalidateQueries({ queryKey: ["memories", variables.mode] });
      message.success(variables.mode === "global" ? "全局记忆已保存。" : "会话记忆已保存。");
    }
  });
  const deleteMemoryMutation = useMutation({
    mutationFn: (memoryId: string) => deleteMemory(memoryId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["memories", memoryMode] });
      message.success("记忆已删除。");
    }
  });
  const clearMemoriesMutation = useMutation({
    mutationFn: ({ mode, sessionId }: { mode: MemoryMode; sessionId: string }) =>
      mode === "global" ? clearScopedMemories(GLOBAL_MEMORY_SCOPE) : clearSessionMemories(sessionId),
    onSuccess: (result, variables) => {
      void queryClient.invalidateQueries({ queryKey: ["memories", variables.mode] });
      const label = variables.mode === "global" ? "全局记忆" : "会话记忆";
      message.success(`已清空 ${result.deleted} 条${label}。`);
    }
  });
  const deleteSessionMutation = useMutation({
    mutationFn: (sessionId: string) => deleteChatSession(sessionId),
    onSuccess: (result) => {
      const nextSessionId = deleteSession(result.session_id);
      void queryClient.removeQueries({ queryKey: ["chat-history", result.session_id] });
      void queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
      if (nextSessionId) {
        void queryClient.invalidateQueries({ queryKey: ["chat-history", nextSessionId] });
      }
      message.success("会话已删除。");
    }
  });

  const handleSend = async (): Promise<void> => {
    const nextQuestion = question.trim();
    if (!nextQuestion || !currentSessionId || streaming || sendingRef.current) {
      return;
    }
    sendingRef.current = true;

    try {
      upsertMessage(currentSessionId, {
        id: crypto.randomUUID(),
        session_id: currentSessionId,
        role: "user",
        content: nextQuestion,
        created_at: new Date().toISOString()
      });

      const payload: ChatAskRequest = {
        session_id: currentSessionId,
        question: nextQuestion,
        filters: {
          doc_types: docTypes,
          enable_web_search: enableWebSearch
        }
      };

      setQuestion("");
      await sendQuestion(payload);
      void queryClient.invalidateQueries({ queryKey: ["chat-history", currentSessionId] });
      void queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
    } finally {
      sendingRef.current = false;
    }
  };

  const openDebug = async (): Promise<void> => {
    if (!currentSessionId) {
      return;
    }

    const lastUserQuestion = [...messages].reverse().find((item) => item.role === "user")?.content ?? question.trim();
    if (!lastUserQuestion) {
      message.warning("请先输入或发送一个问题。");
      return;
    }

    await debugMutation.mutateAsync({
      session_id: currentSessionId,
      question: lastUserQuestion,
      filters: { doc_types: docTypes, enable_web_search: enableWebSearch }
    });
    setDebugOpen(true);
  };

  const handleCreateSession = (): void => {
    const sessionId = createSession();
    setCurrentSession(sessionId);
    void createSessionMutation.mutateAsync(sessionId);
  };

  const handleDeleteSession = async (): Promise<void> => {
    if (!currentSessionId) {
      return;
    }
    cancel();
    await deleteSessionMutation.mutateAsync(currentSessionId);
  };

  const handleCreateMemory = async (): Promise<void> => {
    const content = memoryContent.trim();
    if (!content || (memoryMode === "session" && !currentSessionId)) {
      return;
    }
    await createMemoryMutation.mutateAsync({ content, mode: memoryMode });
  };

  const handleClearMemories = async (): Promise<void> => {
    if (memoryMode === "session" && !currentSessionId) {
      return;
    }
    await clearMemoriesMutation.mutateAsync({ mode: memoryMode, sessionId: currentSessionId });
  };

  const isGlobalMemory = memoryMode === "global";
  const memorySearchPlaceholder = isGlobalMemory ? "搜索全局记忆" : "搜索当前会话记忆";
  const memoryInputPlaceholder = isGlobalMemory
    ? "写入一条跨会话生效的全局记忆，例如：默认先按政策文件给出处理依据。"
    : "手动写入一条当前会话记忆，例如：本次对话重点关注低保申请材料。";
  const memoryEmptyDescription = memoryQuery ? "没有匹配的记忆" : isGlobalMemory ? "暂无全局记忆" : "当前会话暂无记忆";

  return (
    <div className="page-shell chat-page-shell">
      <section className="page-hero">
        <div className="page-kicker">问答中枢</div>
        <h1 className="page-title">智能问答与 RAG 调试台</h1>
        <p className="page-subtitle">
          面向政策、规程、历史工单和典型案例的混合检索问答，支持 SSE 流式输出、来源卡片和检索链路调试。
        </p>
      </section>

      <div className="chat-layout">
        <aside className="glass-card chat-sidebar">
          <div className="chat-sidebar-actions">
            <Button type="primary" icon={<PlusOutlined />} block onClick={handleCreateSession}>
              新建会话
            </Button>
            <Popconfirm
              title="删除当前会话？"
              description="会同时删除数据库中的消息、检索日志和会话记忆。"
              okText="删除"
              cancelText="取消"
              okButtonProps={{ danger: true }}
              onConfirm={() => void handleDeleteSession()}
            >
              <Button icon={<ClearOutlined />} danger block loading={deleteSessionMutation.isPending}>
                删除当前会话
              </Button>
            </Popconfirm>
          </div>

          <div>
            <div className="section-title" style={{ fontSize: 18 }}>
              历史会话
            </div>
            <div className="section-note">按本地时间分组，切换后自动回填数据库历史。</div>
          </div>

          <div className="chat-session-list">
            {sessionGroups.length ? (
              sessionGroups.map((group) => (
                <div key={group.label} style={{ display: "grid", gap: 8 }}>
                  <div className="chat-session-group-label">{group.label}</div>
                  <div style={{ display: "grid", gap: 8 }}>
                    {group.items.map((item) => (
                      <Button
                        className="chat-session-button"
                        key={item.id}
                        type={item.id === currentSessionId ? "primary" : "default"}
                        icon={<MessageOutlined />}
                        onClick={() => setCurrentSession(item.id)}
                      >
                        <div className="chat-session-button-copy">
                          <div className="chat-session-title">{item.title}</div>
                          <div className="chat-session-time">{formatDateTime(item.updatedAt)}</div>
                        </div>
                      </Button>
                    ))}
                  </div>
                </div>
              ))
            ) : (
              <Empty description="暂无会话" />
            )}
          </div>
        </aside>

        <section className="chat-main-panel">
          <div className="glass-card chat-toolbar">
            <Space wrap style={{ width: "100%", justifyContent: "space-between" }}>
              <Space wrap>
                <Select
                  mode="multiple"
                  style={{ minWidth: 260 }}
                  value={docTypes}
                  options={docTypeOptions}
                  onChange={setDocTypes}
                  placeholder="选择检索范围"
                />
                <Button icon={<BugOutlined />} onClick={() => void openDebug()} loading={debugMutation.isPending}>
                  查看 RAG Debug
                </Button>
                <Button icon={<DatabaseOutlined />} onClick={() => setMemoryOpen(true)}>
                  记忆管理
                </Button>
                <Switch
                  checked={enableWebSearch}
                  checkedChildren={<GlobalOutlined />}
                  unCheckedChildren={<GlobalOutlined />}
                  onChange={setEnableWebSearch}
                />
                <Typography.Text type="secondary">联网搜索</Typography.Text>
              </Space>
              {streaming ? (
                <Button danger onClick={cancel}>
                  停止生成
                </Button>
              ) : null}
            </Space>
          </div>

          <div className="chat-thread-shell">
            {historyQuery.isLoading ? (
              <div className="glass-card chat-loading-state">
                <Spin />
              </div>
            ) : (
              <ChatWindow messages={messages} streamingMessageId={streamingMessageId} streamStatus={streamStatus} />
            )}
          </div>

          <div className="glass-card chat-composer">
            <Input.TextArea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              autoSize={{ minRows: 2, maxRows: 8 }}
              style={{ resize: "none" }}
              placeholder="例如：低保申请需要哪些材料？若楼道照明损坏一周，网格员该如何处理？"
              onKeyDown={(event) => {
                if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                  void handleSend();
                }
              }}
            />
            <div className="chat-composer-footer">
              <Typography.Text type="secondary">按 Ctrl / Cmd + Enter 发送，支持流式返回。</Typography.Text>
              <Button
                type="primary"
                icon={<SendOutlined />}
                loading={streaming}
                disabled={!question.trim() || !currentSessionId}
                onClick={() => void handleSend()}
              >
                发送问题
              </Button>
            </div>
          </div>
        </section>
      </div>

      <Drawer
        className="rag-debug-drawer"
        width={980}
        title="RAG 调试详情"
        open={debugOpen}
        onClose={() => setDebugOpen(false)}
      >
        <RagDebugPanel data={debugMutation.data} loading={debugMutation.isPending} />
      </Drawer>

      <Drawer width={680} title="记忆管理" open={memoryOpen} onClose={() => setMemoryOpen(false)}>
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <div className="glass-card" style={{ padding: 16 }}>
            <Space direction="vertical" size={12} style={{ width: "100%" }}>
              <Segmented
                block
                value={memoryMode}
                options={[
                  { label: "当前会话", value: "session" },
                  { label: "全局记忆", value: "global" }
                ]}
                onChange={(value) => {
                  setMemoryMode(value as MemoryMode);
                  setMemoryQuery("");
                }}
              />
              <Input.Search
                allowClear
                value={memoryQuery}
                placeholder={memorySearchPlaceholder}
                onChange={(event) => setMemoryQuery(event.target.value)}
              />
              <Input.TextArea
                value={memoryContent}
                autoSize={{ minRows: 3, maxRows: 6 }}
                placeholder={memoryInputPlaceholder}
                onChange={(event) => setMemoryContent(event.target.value)}
              />
              <Space wrap>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  loading={createMemoryMutation.isPending}
                  disabled={!memoryContent.trim() || (memoryMode === "session" && !currentSessionId)}
                  onClick={() => void handleCreateMemory()}
                >
                  保存记忆
                </Button>
                <Popconfirm
                  title={isGlobalMemory ? "清空全部全局记忆？" : "清空当前会话记忆？"}
                  okText="清空"
                  cancelText="取消"
                  okButtonProps={{ danger: true }}
                  onConfirm={() => void handleClearMemories()}
                >
                  <Button danger icon={<ClearOutlined />} loading={clearMemoriesMutation.isPending}>
                    清空记忆
                  </Button>
                </Popconfirm>
              </Space>
            </Space>
          </div>

          {memoryQueryResult.isLoading ? (
            <Spin />
          ) : memoryQueryResult.data?.items.length ? (
            <List
              dataSource={memoryQueryResult.data.items}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Popconfirm
                      key="delete"
                      title="删除这条记忆？"
                      okText="删除"
                      cancelText="取消"
                      okButtonProps={{ danger: true }}
                      onConfirm={() => void deleteMemoryMutation.mutateAsync(item.id)}
                    >
                      <Button danger size="small" icon={<DeleteOutlined />} loading={deleteMemoryMutation.isPending} />
                    </Popconfirm>
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <Space wrap>
                        <Tag color={isGlobalMemory ? "green" : "geekblue"}>{getMemoryScopeLabel(item)}</Tag>
                        <Tag color={item.memory_type === "auto" ? "blue" : "volcano"}>{item.memory_type}</Tag>
                        <Typography.Text type="secondary">使用 {item.usage_count} 次</Typography.Text>
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size={4}>
                        <Typography.Text>{item.content}</Typography.Text>
                        <Typography.Text type="secondary">更新于 {formatDateTime(item.updated_at)}</Typography.Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          ) : (
            <Empty description={memoryEmptyDescription} />
          )}
        </Space>
      </Drawer>
    </div>
  );
}
