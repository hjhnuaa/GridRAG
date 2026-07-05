# Logging

## 职责

记录系统运行状态和异常，帮助定位接口、入库、检索和生成失败。

## 当前实现位置

- `backend/app/core/logging.py`：结构化日志配置。
- `backend/app/core/exceptions.py`：统一异常处理。
- `backend/app/ingest/tasks.py`：记录文档入库失败。

## 扩展方向

- 为 RAG 每阶段增加统一 trace id。
- 将入库失败原因展示到前端。
- 区分用户错误、配置错误和模型服务错误。
