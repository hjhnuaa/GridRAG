import { PlusOutlined } from "@ant-design/icons";
import { Button, Drawer, Form, Input, Select, Space, Table, Tag, message } from "antd";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { createResident, fetchResidents } from "../../api/residents";
import type { ResidentCreatePayload, ResidentItem } from "../../types/resident";
import { formatDateTime } from "../../utils/presenters";

const residentTags = [
  { label: "独居老人", value: "ELDERLY_ALONE" },
  { label: "残障人士", value: "DISABLED" },
  { label: "低保家庭", value: "LOW_INCOME" },
  { label: "慢病重点", value: "CHRONIC_DISEASE" },
  { label: "留守儿童", value: "LEFT_BEHIND_CHILD" }
];

export function ResidentsPage(): JSX.Element {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const residentsQuery = useQuery({
    queryKey: ["residents", selectedTags],
    queryFn: () =>
      fetchResidents({
        page: 1,
        page_size: 100,
        tags: selectedTags.length ? selectedTags.join(",") : undefined
      })
  });

  const createMutation = useMutation({
    mutationFn: (payload: ResidentCreatePayload) => createResident(payload),
    onSuccess: () => {
      message.success("居民档案已创建。");
      setDrawerOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["residents"] });
    },
    onError: (error) => {
      message.error(error instanceof Error ? error.message : "档案创建失败。");
    }
  });

  return (
    <div className="page-shell">
      <section className="page-hero">
        <div className="page-kicker">居民台账</div>
        <h1 className="page-title">居民档案与重点人群走访管理</h1>
        <p className="page-subtitle">聚焦特殊人群台账、走访轨迹和关联工单，形成从人到事的闭环服务视图。</p>
      </section>

      <div className="glass-card" style={{ padding: 18 }}>
        <Space wrap style={{ width: "100%", justifyContent: "space-between" }}>
          <Select
            mode="multiple"
            allowClear
            placeholder="按标签筛选"
            style={{ minWidth: 340 }}
            options={residentTags}
            value={selectedTags}
            onChange={setSelectedTags}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setDrawerOpen(true)}>
            新建档案
          </Button>
        </Space>
      </div>

      <div className="glass-card" style={{ padding: 10 }}>
        <Table<ResidentItem>
          rowKey="id"
          loading={residentsQuery.isLoading}
          dataSource={residentsQuery.data?.items ?? []}
          columns={[
            {
              title: "姓名",
              dataIndex: "name",
              key: "name"
            },
            {
              title: "证件号",
              dataIndex: "id_number",
              key: "id_number"
            },
            {
              title: "电话",
              dataIndex: "phone",
              key: "phone"
            },
            {
              title: "地址",
              dataIndex: "address",
              key: "address"
            },
            {
              title: "标签",
              dataIndex: "tags",
              key: "tags",
              render: (value: string[]) => (
                <Space wrap>
                  {value.map((tag) => (
                    <Tag key={tag} color="gold">
                      {tag}
                    </Tag>
                  ))}
                </Space>
              )
            },
            {
              title: "最近走访",
              dataIndex: "last_visit_at",
              key: "last_visit_at",
              render: (value: string | null) => formatDateTime(value)
            },
            {
              title: "操作",
              key: "action",
              render: (_: unknown, record: ResidentItem) => (
                <Button type="link" onClick={() => navigate(`/residents/${record.id}`)}>
                  查看详情
                </Button>
              )
            }
          ]}
        />
      </div>

      <Drawer title="新建居民档案" width={520} open={drawerOpen} onClose={() => setDrawerOpen(false)}>
        <Form<ResidentCreatePayload> layout="vertical" onFinish={(values) => createMutation.mutate(values)}>
          <Form.Item label="姓名" name="name" rules={[{ required: true, message: "请输入姓名。" }]}>
            <Input />
          </Form.Item>
          <Form.Item label="身份证号" name="id_number" rules={[{ required: true, message: "请输入身份证号。" }]}>
            <Input />
          </Form.Item>
          <Form.Item label="联系电话" name="phone" rules={[{ required: true, message: "请输入联系电话。" }]}>
            <Input />
          </Form.Item>
          <Form.Item label="居住地址" name="address" rules={[{ required: true, message: "请输入居住地址。" }]}>
            <Input />
          </Form.Item>
          <Form.Item label="标签" name="tags">
            <Select mode="multiple" options={residentTags} />
          </Form.Item>
          <Form.Item label="备注" name="notes">
            <Input.TextArea rows={4} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={createMutation.isPending} block>
            保存档案
          </Button>
        </Form>
      </Drawer>
    </div>
  );
}
