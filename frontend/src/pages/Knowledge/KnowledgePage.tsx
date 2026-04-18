import { DeleteOutlined, ReloadOutlined } from "@ant-design/icons";
import { Button, Popconfirm, Select, Space, Table, Tag, message } from "antd";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { deleteDocument, fetchDocuments, fetchKnowledgeStats, reindexDocument } from "../../api/knowledge";
import { DocUploader } from "../../components/DocUploader/DocUploader";
import type { DocumentItem, DocType } from "../../types/knowledge";
import { docTypeLabel, formatBytes, formatDateTime } from "../../utils/presenters";

function statusTag(status: string): JSX.Element {
  const colorMap: Record<string, string> = {
    PENDING: "default",
    PROCESSING: "processing",
    DONE: "success",
    FAILED: "error"
  };
  return <Tag color={colorMap[status] ?? "default"}>{status}</Tag>;
}

export function KnowledgePage(): JSX.Element {
  const [docTypeFilter, setDocTypeFilter] = useState<string | undefined>();
  const [uploadType, setUploadType] = useState<DocType>("policy");
  const queryClient = useQueryClient();

  const documentsQuery = useQuery({
    queryKey: ["documents", docTypeFilter],
    queryFn: () =>
      fetchDocuments({
        page: 1,
        page_size: 100,
        doc_type: docTypeFilter
      }),
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? [];
      return items.some((item) => item.status === "PENDING" || item.status === "PROCESSING") ? 5000 : false;
    }
  });

  const statsQuery = useQuery({
    queryKey: ["knowledge-stats"],
    queryFn: fetchKnowledgeStats,
    refetchInterval: (query) => ((query.state.data?.processing_documents ?? 0) > 0 ? 5000 : false)
  });

  const deleteMutation = useMutation({
    mutationFn: (documentId: string) => deleteDocument(documentId),
    onSuccess: () => {
      message.success("文档已删除，关联向量索引已同步清理。");
      void queryClient.invalidateQueries({ queryKey: ["documents"] });
      void queryClient.invalidateQueries({ queryKey: ["knowledge-stats"] });
    },
    onError: (error) => {
      message.error(error instanceof Error ? error.message : "删除失败。");
    }
  });

  const reindexMutation = useMutation({
    mutationFn: (documentId: string) => reindexDocument(documentId),
    onSuccess: () => {
      message.success("已提交重建索引任务。");
      void queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (error) => {
      message.error(error instanceof Error ? error.message : "重建索引失败。");
    }
  });

  return (
    <div className="page-shell">
      <section className="page-hero">
        <div className="page-kicker">知识中枢</div>
        <h1 className="page-title">知识库上传、建索引与状态追踪</h1>
        <p className="page-subtitle">
          支持 PDF、DOCX、TXT、XLSX、CSV 文档接入。上传后自动解析、分块、向量化，并纳入混合检索。
        </p>
      </section>

      <div className="metric-strip">
        <div className="metric-tile">
          <div className="metric-label">文档总数</div>
          <div className="metric-value">{statsQuery.data?.total_documents ?? 0}</div>
        </div>
        <div className="metric-tile">
          <div className="metric-label">Chunk 总数</div>
          <div className="metric-value">{statsQuery.data?.total_chunks ?? 0}</div>
        </div>
        <div className="metric-tile">
          <div className="metric-label">处理中</div>
          <div className="metric-value">{statsQuery.data?.processing_documents ?? 0}</div>
        </div>
      </div>

      <div className="glass-card" style={{ padding: 18 }}>
        <Space direction="vertical" style={{ width: "100%" }} size={16}>
          <Space wrap style={{ justifyContent: "space-between", width: "100%" }}>
            <Space>
              <Select<DocType>
                value={uploadType}
                style={{ width: 180 }}
                onChange={setUploadType}
                options={[
                  { label: "政策文件", value: "policy" },
                  { label: "工作手册", value: "manual" },
                  { label: "历史工单", value: "ticket" },
                  { label: "典型案例", value: "case" }
                ]}
              />
              <span className="section-note">上传时的文档类型</span>
            </Space>
            <Select
              allowClear
              placeholder="按文档类型筛选"
              style={{ width: 180 }}
              value={docTypeFilter}
              onChange={setDocTypeFilter}
              options={[
                { label: "政策文件", value: "policy" },
                { label: "工作手册", value: "manual" },
                { label: "历史工单", value: "ticket" },
                { label: "典型案例", value: "case" }
              ]}
            />
          </Space>
          <DocUploader
            docType={uploadType}
            onUploaded={() => {
              void queryClient.invalidateQueries({ queryKey: ["documents"] });
              void queryClient.invalidateQueries({ queryKey: ["knowledge-stats"] });
            }}
          />
        </Space>
      </div>

      <div className="glass-card" style={{ padding: 10 }}>
        <Table<DocumentItem>
          rowKey="id"
          loading={documentsQuery.isLoading}
          dataSource={documentsQuery.data?.items ?? []}
          columns={[
            {
              title: "文档名",
              dataIndex: "name",
              key: "name"
            },
            {
              title: "类型",
              dataIndex: "doc_type",
              key: "doc_type",
              render: (value: string) => <Tag color="volcano">{docTypeLabel(value)}</Tag>
            },
            {
              title: "大小",
              dataIndex: "file_size",
              key: "file_size",
              render: (value: number) => formatBytes(value)
            },
            {
              title: "状态",
              dataIndex: "status",
              key: "status",
              render: (value: string) => statusTag(value)
            },
            {
              title: "Chunk 数",
              dataIndex: "chunk_count",
              key: "chunk_count"
            },
            {
              title: "上传时间",
              dataIndex: "created_at",
              key: "created_at",
              render: (value: string) => formatDateTime(value)
            },
            {
              title: "操作",
              key: "action",
              render: (_: unknown, record: DocumentItem) => (
                <Space>
                  <Button
                    size="small"
                    icon={<ReloadOutlined />}
                    loading={reindexMutation.isPending}
                    onClick={() => reindexMutation.mutate(record.id)}
                  >
                    重建索引
                  </Button>
                  <Popconfirm
                    title="删除文档"
                    description="删除后会同步删除相关向量索引，确认继续吗？"
                    onConfirm={() => deleteMutation.mutate(record.id)}
                  >
                    <Button size="small" danger icon={<DeleteOutlined />} loading={deleteMutation.isPending}>
                      删除
                    </Button>
                  </Popconfirm>
                </Space>
              )
            }
          ]}
        />
      </div>
    </div>
  );
}
