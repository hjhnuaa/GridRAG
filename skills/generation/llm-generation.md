# LLM Generation

## 职责

负责调用大模型生成回答，并支持流式输出到前端。

## 当前实现位置

- `backend/app/rag/generator.py`：封装 Qwen OpenAI 兼容接口和流式生成。
- `backend/app/rag/pipeline.py`：消费增量 token 并保存助手消息。
- `backend/app/api/v1/chat.py`：返回 SSE 流。

## 扩展方向

- 增加模型超时和重试策略。
- 为不同任务配置不同温度和最大输出长度。
- 记录模型调用耗时和失败原因。
