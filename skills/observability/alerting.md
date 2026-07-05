# Alerting

## 职责

当入库、检索、模型或外部服务异常时给出可见提示，减少静默失败。

## 当前实现位置

- `backend/app/core/exceptions.py`：统一 API 错误响应。
- `backend/app/rag/pipeline.py`：联网搜索失败降级并记录 warning。
- `backend/app/ingest/tasks.py`：入库失败标记文档状态。

## 扩展方向

- 为入库失败在知识库页面展示重试按钮。
- 为模型不可用展示降级提示。
- 对连续失败的外部搜索供应商触发告警。
