# Retriever Selection

## 职责

负责选择合适的召回通道，并根据文档类型过滤政策、手册、工单和案例等知识。

## 当前实现位置

- `backend/app/rag/retriever.py`：`HybridRetriever.retrieve()` 同时执行 Chroma 向量检索和 BM25 关键词检索。
- `backend/app/models/enums.py`：定义知识文档类型。
- `backend/app/schemas/chat.py`：聊天请求中的 `filters.doc_types` 控制检索范围。

## 扩展方向

- 根据问题意图自动选择文档类型。
- 为结构化居民、事件数据增加专用检索通道。
- 在 Debug 面板展示各通道命中数量与耗时。
