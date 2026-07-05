# GridRAG RAG 能力结构

这个目录按“检索、索引、知识库、生成、评估、观测、集成”的方式整理 GridRAG 的 RAG 能力。它不改变运行时代码目录，而是作为项目说明、答辩讲解和二次开发入口。

## 能力分层

| 目录 | 能力 | 当前代码入口 |
| --- | --- | --- |
| `retrieval/` | 查询理解、混合检索、重排与召回结果组织 | `backend/app/rag/retriever.py`、`backend/app/rag/reranker.py` |
| `indexing/` | 文档解析、分块、嵌入、向量索引写入 | `backend/app/ingest/`、`backend/app/rag/chunker.py`、`backend/app/rag/store.py` |
| `knowledge-base/` | 文档元数据、语料管理、更新同步与版本策略 | `backend/app/api/v1/knowledge.py`、`backend/app/services/documents.py` |
| `generation/` | Prompt、上下文组装、模型调用、引用来源过滤 | `backend/app/rag/pipeline.py`、`backend/app/rag/generator.py`、`backend/app/rag/sources.py` |
| `evaluation/` | 检索、生成和端到端链路测试 | `backend/tests/` |
| `observability/` | 日志、检索记录、Debug 面板和前端可视化 | `backend/app/core/logging.py`、`frontend/src/components/RagDebugPanel/` |
| `integration/` | API、SSE、MCP、前后端和外部搜索集成 | `backend/app/api/`、`frontend/src/api/` |

## 使用方式

- 想理解项目整体：先读根目录 `README.md` 和 `skills-index.md`。
- 想讲清 RAG 链路：按 `indexing -> retrieval -> generation -> observability` 阅读。
- 想做二次开发：从每个能力文档里的“当前实现位置”和“扩展方向”进入代码。
- 想验证质量：看 `evaluation/` 下的测试说明，再运行后端测试和前端构建。
