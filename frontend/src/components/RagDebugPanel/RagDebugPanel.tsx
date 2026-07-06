import {
  CheckCircleOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  GlobalOutlined,
  SearchOutlined,
  WarningOutlined
} from "@ant-design/icons";
import { Empty, Spin, Tabs, Tag, Typography } from "antd";
import type { ReactNode } from "react";

import type { ChatDebugResponse, RetrievalCandidate, SourceItem } from "../../types/chat";
import { docTypeLabel } from "../../utils/presenters";

interface RagDebugPanelProps {
  data?: ChatDebugResponse;
  loading: boolean;
}

interface DebugMetricProps {
  icon: ReactNode;
  label: string;
  value: ReactNode;
  note: string;
  tone?: "success" | "warning" | "neutral";
}

interface CandidateListProps {
  items: RetrievalCandidate[];
}

interface SourceListProps {
  items: SourceItem[];
  title: string;
  emptyText: string;
  icon: ReactNode;
}

const SCORE_LABELS: Array<{ key: keyof RetrievalCandidate; label: string }> = [
  { key: "dense_score", label: "向量" },
  { key: "sparse_score", label: "关键词" },
  { key: "fused_score", label: "融合" },
  { key: "rerank_score", label: "重排" }
];

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function formatScore(value?: number | null): string {
  return isNumber(value) ? value.toFixed(3) : "-";
}

function scoreToPercent(value?: number | null): number {
  if (!isNumber(value)) {
    return 0;
  }
  const normalized = value <= 1 ? value * 100 : value;
  return Math.max(4, Math.min(100, normalized));
}

function primaryScore(item: RetrievalCandidate): number | null {
  return item.rerank_score ?? item.fused_score ?? item.dense_score ?? item.sparse_score ?? null;
}

function bestScore(items: RetrievalCandidate[]): number | null {
  const scores = items.map((item) => primaryScore(item)).filter(isNumber);
  return scores.length ? Math.max(...scores) : null;
}

function sourceTypeLabel(value: string): string {
  if (value.startsWith("web:")) {
    return "联网搜索";
  }
  return docTypeLabel(value);
}

function DebugMetric({ icon, label, value, note, tone = "neutral" }: DebugMetricProps): JSX.Element {
  return (
    <div className={`rag-debug-metric is-${tone}`}>
      <div className="rag-debug-metric-icon">{icon}</div>
      <div className="rag-debug-metric-copy">
        <div className="rag-debug-metric-label">{label}</div>
        <div className="rag-debug-metric-value">{value}</div>
        <div className="rag-debug-metric-note">{note}</div>
      </div>
    </div>
  );
}

function CandidateList({ items }: CandidateListProps): JSX.Element {
  if (!items.length) {
    return <Empty className="rag-debug-empty" description="暂无候选结果" />;
  }

  return (
    <div className="rag-candidate-list">
      {items.map((item, index) => {
        const score = primaryScore(item);
        return (
          <article className="rag-candidate-item" key={`${item.chunk_id}-${index}`}>
            <div className="rag-candidate-index">{String(index + 1).padStart(2, "0")}</div>
            <div className="rag-candidate-body">
              <div className="rag-candidate-header">
                <div className="rag-candidate-title">
                  <span>{item.doc_name}</span>
                  {item.page ? <em>P{item.page}</em> : null}
                </div>
                <Tag color="geekblue">{sourceTypeLabel(item.doc_type)}</Tag>
              </div>
              <div className="rag-score-meter" aria-label={`候选分数 ${formatScore(score)}`}>
                <span style={{ width: `${scoreToPercent(score)}%` }} />
              </div>
              <div className="rag-score-row">
                {SCORE_LABELS.map(({ key, label }) => {
                  const value = item[key];
                  return isNumber(value) ? (
                    <span className="rag-score-pill" key={key}>
                      {label} <strong>{formatScore(value)}</strong>
                    </span>
                  ) : null;
                })}
              </div>
              {item.section ? <div className="rag-candidate-section">{item.section}</div> : null}
              <Typography.Paragraph className="rag-candidate-text" ellipsis={{ rows: 4, expandable: true }}>
                {item.text}
              </Typography.Paragraph>
            </div>
          </article>
        );
      })}
    </div>
  );
}

function SourceList({ items, title, emptyText, icon }: SourceListProps): JSX.Element {
  return (
    <section className="rag-source-panel">
      <div className="rag-section-head compact">
        <div>
          <div className="rag-section-kicker">{title}</div>
          <h3>{items.length} 条</h3>
        </div>
        <div className="rag-section-icon">{icon}</div>
      </div>
      {items.length ? (
        <div className="rag-source-list">
          {items.map((item, index) => (
            <article className="rag-source-item" key={`${item.doc_name}-${item.chunk_id ?? item.url ?? index}`}>
              <div className="rag-source-topline">
                <strong>{item.doc_name}</strong>
                <Tag>{sourceTypeLabel(item.doc_type)}</Tag>
              </div>
              <div className="rag-source-meta">
                {item.page ? <span>P{item.page}</span> : null}
                {item.section ? <span>{item.section}</span> : null}
                {isNumber(item.score) ? <span>score {formatScore(item.score)}</span> : null}
              </div>
              <p>{item.excerpt}</p>
              {item.url ? (
                <a href={item.url} target="_blank" rel="noreferrer">
                  {item.url}
                </a>
              ) : null}
            </article>
          ))}
        </div>
      ) : (
        <Empty className="rag-debug-empty" description={emptyText} />
      )}
    </section>
  );
}

function MemoryStrip({ items }: { items: string[] }): JSX.Element {
  return (
    <section className="rag-debug-section">
      <div className="rag-section-head">
        <div>
          <div className="rag-section-kicker">记忆注入</div>
          <h3>规则与记忆</h3>
        </div>
        <Tag color={items.length ? "cyan" : "default"}>{items.length} 条</Tag>
      </div>
      {items.length ? (
        <div className="rag-memory-list">
          {items.map((item, index) => (
            <div className="rag-memory-item" key={`${item}-${index}`}>
              {item}
            </div>
          ))}
        </div>
      ) : (
        <Empty className="rag-debug-empty" description="本次调试未注入会话记忆" />
      )}
    </section>
  );
}

function ConversationStrip({ summary, items }: { summary?: string | null; items: string[] }): JSX.Element {
  const total = items.length + (summary ? 1 : 0);
  return (
    <section className="rag-debug-section">
      <div className="rag-section-head">
        <div>
          <div className="rag-section-kicker">多轮上下文</div>
          <h3>会话历史</h3>
        </div>
        <Tag color={total ? "purple" : "default"}>{total} 条</Tag>
      </div>
      {total ? (
        <div className="rag-memory-list">
          {summary ? <div className="rag-memory-item">摘要：{summary}</div> : null}
          {items.map((item, index) => (
            <div className="rag-memory-item" key={`${item}-${index}`}>
              {item}
            </div>
          ))}
        </div>
      ) : (
        <Empty className="rag-debug-empty" description="本次调试未注入会话历史" />
      )}
    </section>
  );
}

export function RagDebugPanel({ data, loading }: RagDebugPanelProps): JSX.Element {
  if (loading) {
    return (
      <div className="rag-debug-loading">
        <Spin />
        <Typography.Text type="secondary">正在重放检索链路</Typography.Text>
      </div>
    );
  }

  if (!data) {
    return <Empty className="rag-debug-empty" description="暂无调试结果" />;
  }

  const topScore = bestScore(data.reranked_candidates);
  const localSourceCount = data.selected_sources.length;
  const webSourceCount = data.web_results.length;

  return (
    <div className="rag-debug-panel">
      <section className="rag-debug-hero">
        <div className="rag-query-panel">
          <div className="rag-section-kicker">Query</div>
          <Typography.Paragraph className="rag-query-text">{data.original_query}</Typography.Paragraph>
          <div className="rag-query-rewrite">
            <span>检索表达</span>
            <strong>{data.rewritten_query}</strong>
          </div>
        </div>

        <div className="rag-debug-metric-grid">
          <DebugMetric
            icon={data.grounded ? <CheckCircleOutlined /> : <WarningOutlined />}
            label="命中状态"
            value={data.grounded ? "有效依据" : "依据不足"}
            note={data.grounded ? "本地检索分数达到阈值" : "未达到本地依据阈值"}
            tone={data.grounded ? "success" : "warning"}
          />
          <DebugMetric
            icon={<DatabaseOutlined />}
            label="本地依据"
            value={localSourceCount}
            note={`${data.reranked_candidates.length} 条重排候选`}
          />
          <DebugMetric
            icon={<GlobalOutlined />}
            label="联网结果"
            value={webSourceCount}
            note={webSourceCount ? "已进入 Prompt" : "未使用联网结果"}
          />
          <DebugMetric
            icon={<SearchOutlined />}
            label="最高分"
            value={formatScore(topScore)}
            note="重排优先，其次融合/召回分"
          />
        </div>
      </section>

      <div className="rag-debug-columns">
        <section className="rag-debug-section rag-prompt-section">
          <div className="rag-section-head">
            <div>
              <div className="rag-section-kicker">Prompt</div>
              <h3>最终提示词预览</h3>
            </div>
            <Tag color="volcano">{data.prompt_preview.length} 字符</Tag>
          </div>
          <pre className="rag-prompt-preview">{data.prompt_preview}</pre>
        </section>

        <div style={{ display: "grid", gap: 16 }}>
          <ConversationStrip summary={data.conversation_summary} items={data.conversation_context} />
          <MemoryStrip items={data.memories} />
        </div>
      </div>

      <div className="rag-source-columns">
        <SourceList
          items={data.selected_sources}
          title="选中本地依据"
          emptyText="未选中本地依据"
          icon={<FileTextOutlined />}
        />
        <SourceList items={data.web_results} title="联网补充" emptyText="未返回联网结果" icon={<GlobalOutlined />} />
      </div>

      <section className="rag-debug-section">
        <div className="rag-section-head">
          <div>
            <div className="rag-section-kicker">Retrieval</div>
            <h3>候选链路</h3>
          </div>
          <Tag color="blue">
            {data.dense_candidates.length + data.sparse_candidates.length + data.fused_candidates.length} 条召回记录
          </Tag>
        </div>
        <Tabs
          className="rag-debug-tabs"
          items={[
            {
              key: "reranked",
              label: `重排结果 ${data.reranked_candidates.length}`,
              children: <CandidateList items={data.reranked_candidates} />
            },
            {
              key: "fused",
              label: `融合结果 ${data.fused_candidates.length}`,
              children: <CandidateList items={data.fused_candidates} />
            },
            {
              key: "dense",
              label: `向量检索 ${data.dense_candidates.length}`,
              children: <CandidateList items={data.dense_candidates} />
            },
            {
              key: "sparse",
              label: `BM25 ${data.sparse_candidates.length}`,
              children: <CandidateList items={data.sparse_candidates} />
            }
          ]}
        />
      </section>
    </div>
  );
}
