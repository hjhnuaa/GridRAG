# Tracing

## 职责

串联一次问答或一次入库任务中的关键阶段，形成可追踪链路。

## 当前实现位置

- `backend/app/rag/pipeline.py`：保存检索日志。
- `backend/app/services/chat.py`：持久化聊天、会话和检索记录。
- `backend/app/api/sse.py`：统一 SSE 流式帧输出。

## 扩展方向

- 为每次 `/chat/ask` 生成 request id。
- 在检索日志中记录 Prompt 版本和模型名称。
- 为 Celery 入库任务记录 task id。
