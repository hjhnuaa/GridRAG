# GridRAG Backend

GridRAG 后端服务包。

该目录通过 `pyproject.toml` 以 editable 方式安装，完整项目说明请查看仓库根目录下的 `README.md`。当前后端已接入 LangChain 作为模型调用层，保留原有 FastAPI、MySQL、Redis、Chroma 和自定义混合检索能力。

新增能力入口：

- 长期记忆：`/api/v1/memory`，对应 `app/services/memory.py` 和 `chat_memories` 表。
- 联网搜索：`/api/v1/web-search`，对应 `app/services/web_search.py`，默认由 `WEB_SEARCH_ENABLED=false` 关闭；`/api/v1/web-search/status?probe=true` 可诊断供应商连通性和认证状态。
- MCP 网关：`/api/v1/mcp` 和 `/api/v1/mcp/tools`，通过 JSON-RPC 暴露 `gridrag.memory.add`、`gridrag.memory.search`、`gridrag.web_search`。

启用新表请执行：

```powershell
alembic upgrade head
```
