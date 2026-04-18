import { BulbOutlined, PlusOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Col,
  Descriptions,
  Form,
  Input,
  Modal,
  Row,
  Space,
  Spin,
  Table,
  Timeline,
  Typography,
  message
} from "antd";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";

import { createVisit, fetchResidentDetail, fetchVisitSuggest } from "../../api/residents";
import type { VisitCreatePayload } from "../../types/resident";
import { categoryLabel, formatDateTime, statusLabel } from "../../utils/presenters";

export function ResidentDetailPage(): JSX.Element {
  const { residentId = "" } = useParams();
  const [visitModalOpen, setVisitModalOpen] = useState(false);
  const queryClient = useQueryClient();

  const detailQuery = useQuery({
    queryKey: ["resident-detail", residentId],
    queryFn: () => fetchResidentDetail(residentId),
    enabled: Boolean(residentId)
  });

  const suggestMutation = useMutation({
    mutationFn: () => fetchVisitSuggest(residentId),
    onError: (error) => {
      message.error(error instanceof Error ? error.message : "获取 AI 走访建议失败。");
    }
  });

  const visitMutation = useMutation({
    mutationFn: (payload: VisitCreatePayload) => createVisit(residentId, payload),
    onSuccess: () => {
      message.success("走访记录已保存。");
      setVisitModalOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["resident-detail", residentId] });
    },
    onError: (error) => {
      message.error(error instanceof Error ? error.message : "走访记录保存失败。");
    }
  });

  if (detailQuery.isLoading || !detailQuery.data) {
    return <Spin />;
  }

  const resident = detailQuery.data;

  return (
    <div className="page-shell">
      <section className="page-hero">
        <div className="page-kicker">服务视图</div>
        <h1 className="page-title">{resident.name} 的走访与服务视图</h1>
        <p className="page-subtitle">聚合基础档案、走访时间轴和关联工单，并通过 AI 生成本次上门重点。</p>
      </section>

      <Row gutter={[18, 18]}>
        <Col xs={24} xl={16}>
          <Card className="glass-card" style={{ borderRadius: 24 }}>
            <Descriptions
              title="基础信息"
              column={2}
              items={[
                { key: "name", label: "姓名", children: resident.name },
                { key: "id", label: "证件号", children: resident.id_number },
                { key: "phone", label: "电话", children: resident.phone },
                { key: "address", label: "地址", children: resident.address },
                { key: "tags", label: "标签", children: resident.tags.join("、") || "暂无" },
                { key: "notes", label: "备注", children: resident.notes || "暂无" }
              ]}
            />
          </Card>

          <Card
            className="glass-card"
            style={{ borderRadius: 24, marginTop: 18 }}
            title="走访记录时间轴"
            extra={
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setVisitModalOpen(true)}>
                记录走访
              </Button>
            }
          >
            <Timeline
              items={resident.visits.map((item) => ({
                color: "red",
                children: (
                  <div>
                    <div style={{ fontWeight: 700 }}>{formatDateTime(item.created_at)}</div>
                    <div style={{ color: "rgba(34,23,16,0.72)", marginTop: 6 }}>{item.content}</div>
                    {item.summary ? <div style={{ marginTop: 6 }}>摘要：{item.summary}</div> : null}
                  </div>
                )
              }))}
            />
          </Card>
        </Col>
        <Col xs={24} xl={8}>
          <Card
            className="glass-card"
            style={{ borderRadius: 24 }}
            title="AI 走访建议"
            extra={
              <Button
                icon={<BulbOutlined />}
                loading={suggestMutation.isPending}
                onClick={() => suggestMutation.mutate()}
              >
                获取建议
              </Button>
            }
          >
            {suggestMutation.data ? (
              <Space direction="vertical" size={14} style={{ width: "100%" }}>
                <Typography.Paragraph strong>{suggestMutation.data.risk_summary}</Typography.Paragraph>
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {suggestMutation.data.suggestions.map((item) => (
                    <li key={item} style={{ marginBottom: 8 }}>
                      {item}
                    </li>
                  ))}
                </ul>
              </Space>
            ) : suggestMutation.isError ? (
              <Typography.Text type="danger">生成建议失败，请稍后重试。</Typography.Text>
            ) : (
              <Typography.Text type="secondary">点击按钮后生成本次走访关注要点。</Typography.Text>
            )}
          </Card>

          <Card className="glass-card" style={{ borderRadius: 24, marginTop: 18 }} title="关联工单">
            <Table
              rowKey="id"
              dataSource={resident.related_events}
              pagination={false}
              size="small"
              columns={[
                {
                  title: "标题",
                  dataIndex: "title",
                  key: "title"
                },
                {
                  title: "类型",
                  dataIndex: "category",
                  key: "category",
                  render: (value: string) => categoryLabel(value)
                },
                {
                  title: "状态",
                  dataIndex: "status",
                  key: "status",
                  render: (value: string) => statusLabel(value)
                }
              ]}
            />
          </Card>
        </Col>
      </Row>

      <Modal
        title="记录走访"
        open={visitModalOpen}
        onCancel={() => setVisitModalOpen(false)}
        footer={null}
      >
        <Form<VisitCreatePayload> layout="vertical" onFinish={(values) => visitMutation.mutate(values)}>
          <Form.Item label="走访人" name="visitor_name" rules={[{ required: true, message: "请输入走访人。" }]}>
            <Input />
          </Form.Item>
          <Form.Item label="走访内容" name="content" rules={[{ required: true, message: "请输入走访内容。" }]}>
            <Input.TextArea rows={5} />
          </Form.Item>
          <Form.Item label="简要摘要" name="summary">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Button type="primary" htmlType="submit" block loading={visitMutation.isPending}>
            保存走访记录
          </Button>
        </Form>
      </Modal>
    </div>
  );
}
