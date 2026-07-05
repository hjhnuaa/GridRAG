# Tool Usage

## 职责

说明系统内部和外部工具如何被调用，包括联网搜索、MCP 工具和前端调试工具。

## 当前实现位置

- `backend/app/services/web_search.py`：SearXNG、Bing、Serper 供应商封装。
- `backend/app/api/v1/mcp.py`：工具列表和工具调用。
- `frontend/src/components/RagDebugPanel/`：前端调试工具。

## 扩展方向

- 为每个工具补充输入、输出和失败模式说明。
- 对联网搜索默认关闭策略做部署说明。
- 增加工具调用日志，方便排查外部集成问题。
