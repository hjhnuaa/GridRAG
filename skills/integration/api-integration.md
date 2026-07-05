# API Integration

## 职责

定义前后端之间的 REST、SSE 和 JSON-RPC 接口边界。

## 当前实现位置

- `backend/app/api/v1/`：后端 API 路由。
- `backend/app/api/sse.py`：SSE 帧和流式输出 helper。
- `frontend/src/api/`：前端接口封装。

## 扩展方向

- 为关键接口补充 OpenAPI 示例。
- 对 SSE 错误事件增加统一前端处理。
- 保持 API 层只做请求响应编排，业务逻辑放到 service 或 RAG 层。
