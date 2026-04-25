import { BookOutlined, FileTextOutlined, LinkOutlined } from "@ant-design/icons";
import { Collapse, Space, Tag, Typography } from "antd";

import type { SourceItem } from "../../types/chat";

interface SourceCardProps {
  sources: SourceItem[];
}

export function SourceCard({ sources }: SourceCardProps): JSX.Element | null {
  if (!sources.length) {
    return null;
  }

  return (
    <Collapse
      bordered={false}
      style={{
        marginTop: 14,
        border: "1px solid rgba(108, 73, 49, 0.18)",
        borderRadius: 18,
        background: "rgba(255, 250, 244, 0.82)"
      }}
      items={[
        {
          key: "sources",
          label: (
            <Space>
              <BookOutlined />
              <span>引用来源</span>
              <Tag color="gold">{sources.length} 条</Tag>
            </Space>
          ),
          children: (
            <div style={{ display: "grid", gap: 12 }}>
              {sources.map((source) => (
                <div
                  key={`${source.chunk_id ?? source.url ?? source.doc_name}-${source.page ?? "na"}`}
                  style={{
                    padding: 14,
                    border: "1px dashed rgba(108, 73, 49, 0.22)",
                    borderRadius: 16,
                    background: "rgba(255, 255, 255, 0.54)"
                  }}
                >
                  <Space size={8} wrap>
                    <Tag color="volcano" icon={<FileTextOutlined />}>
                      {source.doc_name}
                    </Tag>
                    <Tag>{source.doc_type}</Tag>
                    {source.page ? <Tag>第 {source.page} 页</Tag> : null}
                    {source.section ? <Tag>{source.section}</Tag> : null}
                  </Space>
                  {source.url ? (
                    <Typography.Link
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                      style={{ display: "block", marginTop: 8 }}
                    >
                      <LinkOutlined /> 打开网页来源
                    </Typography.Link>
                  ) : null}
                  <Typography.Paragraph
                    ellipsis={{ rows: 3, expandable: true, symbol: "展开片段" }}
                    style={{ margin: "12px 0 0", color: "rgba(34, 23, 16, 0.72)" }}
                  >
                    {source.excerpt}
                  </Typography.Paragraph>
                </div>
              ))}
            </div>
          )
        }
      ]}
    />
  );
}
