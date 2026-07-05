# Agent Integration

## 职责

让外部智能体或工具复用 GridRAG 的记忆、搜索和知识能力。

## 当前实现位置

- `backend/app/api/v1/mcp.py`：MCP JSON-RPC 网关。
- `backend/app/schemas/mcp.py`：MCP 请求模型。
- `backend/app/services/memory.py`：记忆工具能力。
- `backend/app/services/web_search.py`：联网搜索工具能力。

## 扩展方向

- 增加知识库检索工具。
- 为工具调用增加权限和审计。
- 输出工具说明文档，便于外部 Agent 接入。
