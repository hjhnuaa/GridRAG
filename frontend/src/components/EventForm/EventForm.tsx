import { BulbOutlined } from "@ant-design/icons";
import { Button, Form, Input, InputNumber, Select, Space, message } from "antd";
import { useState } from "react";

import type { EventAIAssistResponse, EventCategory, EventCreatePayload } from "../../types/event";
import { fetchEventAIAssist } from "../../api/events";

interface EventFormProps {
  loading: boolean;
  onSubmit: (values: EventCreatePayload) => Promise<void>;
}

const categoryOptions: Array<{ label: string; value: EventCategory }> = [
  { label: "投诉受理", value: "COMPLAINT" },
  { label: "安全隐患", value: "HAZARD" },
  { label: "矛盾纠纷", value: "DISPUTE" },
  { label: "走访服务", value: "VISIT" },
  { label: "其他事项", value: "OTHER" }
];

export function EventForm({ loading, onSubmit }: EventFormProps): JSX.Element {
  const [form] = Form.useForm<EventCreatePayload>();
  const [aiLoading, setAiLoading] = useState(false);

  const applySuggestion = (suggestion: EventAIAssistResponse): void => {
    form.setFieldsValue({
      category: suggestion.suggested_category,
      priority: suggestion.suggested_priority,
      title: suggestion.suggested_title,
      ai_suggestion: `${suggestion.suggested_action}\n参考依据：${suggestion.relevant_policy}`
    });
  };

  const handleAIAssist = async (): Promise<void> => {
    const description = form.getFieldValue("description");
    if (!description) {
      message.warning("请先输入事件描述，再生成 AI 建议。");
      return;
    }
    setAiLoading(true);
    try {
      const suggestion = await fetchEventAIAssist({ description });
      applySuggestion(suggestion);
      message.success("已填入 AI 建议，可继续人工调整。");
    } catch (error) {
      message.error(error instanceof Error ? error.message : "AI 建议获取失败。");
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <Form<EventCreatePayload>
      form={form}
      layout="vertical"
      initialValues={{
        priority: 3,
        category: "OTHER",
        attachments: []
      }}
      onFinish={onSubmit}
    >
      <Form.Item label="自然语言描述" name="description" rules={[{ required: true, message: "请输入事件描述。" }]}>
        <Input.TextArea rows={4} placeholder="例如：居民反映楼道灯损坏一周未修复，夜间存在安全隐患。" />
      </Form.Item>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<BulbOutlined />} loading={aiLoading} onClick={handleAIAssist}>
          AI 建议
        </Button>
      </Space>
      <Form.Item label="工单标题" name="title" rules={[{ required: true, message: "请输入工单标题。" }]}>
        <Input placeholder="请输入工单标题" />
      </Form.Item>
      <Form.Item label="事件类型" name="category" rules={[{ required: true, message: "请选择事件类型。" }]}>
        <Select options={categoryOptions} />
      </Form.Item>
      <Form.Item label="优先级" name="priority" rules={[{ required: true, message: "请输入优先级。" }]}>
        <InputNumber min={1} max={5} style={{ width: "100%" }} />
      </Form.Item>
      <Form.Item label="发生地址" name="address" rules={[{ required: true, message: "请输入发生地址。" }]}>
        <Input placeholder="请输入详细地址" />
      </Form.Item>
      <Form.Item label="上报网格员" name="reporter_name" rules={[{ required: true, message: "请输入网格员姓名。" }]}>
        <Input placeholder="请输入上报人姓名" />
      </Form.Item>
      <Form.Item label="AI 处置建议" name="ai_suggestion">
        <Input.TextArea rows={5} placeholder="AI 建议会自动填充，也可手动修改。" />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading} block>
          提交工单
        </Button>
      </Form.Item>
    </Form>
  );
}

