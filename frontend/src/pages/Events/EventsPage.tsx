import {
  AppstoreOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
  TableOutlined
} from "@ant-design/icons";
import {
  Badge,
  Button,
  Card,
  Col,
  Drawer,
  Input,
  Rate,
  Row,
  Segmented,
  Select,
  Space,
  Table,
  Tag,
  message
} from "antd";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { closeEvent, createEvent, fetchEvents } from "../../api/events";
import { EventForm } from "../../components/EventForm/EventForm";
import type { EventCreatePayload, EventItem } from "../../types/event";
import { categoryLabel, formatDateTime, statusColor, statusLabel } from "../../utils/presenters";

type ViewMode = "table" | "cards";

export function EventsPage(): JSX.Element {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [keyword, setKeyword] = useState("");
  const [status, setStatus] = useState<string | undefined>();
  const [category, setCategory] = useState<string | undefined>();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["events", page, pageSize, keyword, status, category],
    queryFn: () =>
      fetchEvents({
        page,
        page_size: pageSize,
        keyword: keyword || undefined,
        status,
        category
      })
  });

  const createMutation = useMutation({
    mutationFn: (payload: EventCreatePayload) => createEvent(payload),
    onSuccess: () => {
      message.success("工单创建成功。");
      setDrawerOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["events"] });
    },
    onError: (error) => {
      message.error(error instanceof Error ? error.message : "工单创建失败。");
    }
  });

  const closeMutation = useMutation({
    mutationFn: (eventId: string) => closeEvent(eventId),
    onSuccess: () => {
      message.success("工单已关闭。");
      void queryClient.invalidateQueries({ queryKey: ["events"] });
    },
    onError: (error) => {
      message.error(error instanceof Error ? error.message : "工单关闭失败。");
    }
  });

  const items = data?.items ?? [];
  const metrics = [
    {
      label: "当前列表",
      value: items.length
    },
    {
      label: "待处理",
      value: items.filter((item) => item.status === "PENDING").length
    },
    {
      label: "处理中",
      value: items.filter((item) => item.status === "IN_PROGRESS").length
    },
    {
      label: "高优先级",
      value: items.filter((item) => item.priority >= 4).length
    }
  ];

  const columns = [
    {
      title: "编号",
      dataIndex: "id",
      key: "id",
      render: (value: string) => value.slice(0, 8)
    },
    {
      title: "标题",
      dataIndex: "title",
      key: "title"
    },
    {
      title: "类型",
      dataIndex: "category",
      key: "category",
      render: (value: string) => <Tag color="volcano">{categoryLabel(value)}</Tag>
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (value: string) => <Badge status={statusColor(value) as never} text={statusLabel(value)} />
    },
    {
      title: "优先级",
      dataIndex: "priority",
      key: "priority",
      render: (value: number) => <Rate disabled count={5} value={value} style={{ fontSize: 14 }} />
    },
    {
      title: "上报时间",
      dataIndex: "created_at",
      key: "created_at",
      render: (value: string) => formatDateTime(value)
    },
    {
      title: "操作",
      key: "action",
      render: (_: unknown, record: EventItem) => (
        <Button
          size="small"
          disabled={record.status === "CLOSED"}
          onClick={() => closeMutation.mutate(record.id)}
          loading={closeMutation.isPending}
        >
          关闭工单
        </Button>
      )
    }
  ];

  return (
    <div className="page-shell">
      <section className="page-hero">
        <div className="page-kicker">事件协同</div>
        <h1 className="page-title">事件工单与 AI 辅助填报</h1>
        <p className="page-subtitle">自然语言描述可直接转成工单草稿，保留人工校正空间，适合一线快速受理与派发。</p>
      </section>

      <div className="metric-strip">
        {metrics.map((item) => (
          <div className="metric-tile" key={item.label}>
            <div className="metric-label">{item.label}</div>
            <div className="metric-value">{item.value}</div>
          </div>
        ))}
      </div>

      <div className="glass-card" style={{ padding: 18 }}>
        <Space wrap style={{ width: "100%", justifyContent: "space-between" }}>
          <Space wrap>
            <Segmented<ViewMode>
              value={viewMode}
              options={[
                { label: "表格", value: "table", icon: <TableOutlined /> },
                { label: "卡片", value: "cards", icon: <AppstoreOutlined /> }
              ]}
              onChange={(value) => setViewMode(value)}
            />
            <Select
              allowClear
              placeholder="按状态筛选"
              style={{ width: 160 }}
              value={status}
              onChange={setStatus}
              options={[
                { label: "待处理", value: "PENDING" },
                { label: "处理中", value: "IN_PROGRESS" },
                { label: "已解决", value: "RESOLVED" },
                { label: "已关闭", value: "CLOSED" }
              ]}
            />
            <Select
              allowClear
              placeholder="按类型筛选"
              style={{ width: 160 }}
              value={category}
              onChange={setCategory}
              options={[
                { label: "投诉受理", value: "COMPLAINT" },
                { label: "安全隐患", value: "HAZARD" },
                { label: "矛盾纠纷", value: "DISPUTE" },
                { label: "走访服务", value: "VISIT" },
                { label: "其他事项", value: "OTHER" }
              ]}
            />
            <Input
              allowClear
              placeholder="搜索标题或描述"
              prefix={<SearchOutlined />}
              style={{ width: 220 }}
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
            />
          </Space>
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => void queryClient.invalidateQueries({ queryKey: ["events"] })}>
              刷新
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setDrawerOpen(true)}>
              新建工单
            </Button>
          </Space>
        </Space>
      </div>

      {viewMode === "table" ? (
        <div className="glass-card" style={{ padding: 10 }}>
          <Table<EventItem>
            rowKey="id"
            loading={isLoading}
            dataSource={data?.items ?? []}
            columns={columns}
            pagination={{
              current: page,
              pageSize,
              total: data?.meta.total ?? 0,
              onChange: (nextPage, nextPageSize) => {
                setPage(nextPage);
                setPageSize(nextPageSize);
              }
            }}
          />
        </div>
      ) : (
        <Row gutter={[18, 18]}>
          {(data?.items ?? []).map((item) => (
            <Col xs={24} md={12} xl={8} key={item.id}>
              <Card
                className="glass-card"
                style={{ borderRadius: 16 }}
                actions={[
                  <Button
                    key="close"
                    type="link"
                    disabled={item.status === "CLOSED"}
                    onClick={() => closeMutation.mutate(item.id)}
                  >
                    关闭工单
                  </Button>
                ]}
              >
                <Space wrap size={8} style={{ marginBottom: 10 }}>
                  <Tag color="volcano">{categoryLabel(item.category)}</Tag>
                  <Tag>{statusLabel(item.status)}</Tag>
                </Space>
                <h3 className="section-title" style={{ fontSize: 18 }}>
                  {item.title}
                </h3>
                <p className="section-note">{item.description}</p>
                <div style={{ marginTop: 14, display: "grid", gap: 8 }}>
                  <span>地址：{item.address}</span>
                  <span>上报人：{item.reporter_name}</span>
                  <span>时间：{formatDateTime(item.created_at)}</span>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      <Drawer
        title="新建工单"
        open={drawerOpen}
        width={520}
        onClose={() => setDrawerOpen(false)}
      >
        <EventForm
          loading={createMutation.isPending}
          onSubmit={async (values) => {
            await createMutation.mutateAsync(values);
          }}
        />
      </Drawer>
    </div>
  );
}
