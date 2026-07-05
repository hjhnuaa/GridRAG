# Embedding

## 职责

负责把文本片段转成向量，用于 Chroma 语义召回。

## 当前实现位置

- `backend/app/ingest/embedder.py`：封装 embedding 服务。
- `backend/app/ingest/tasks.py`：入库任务批量调用 `embed_texts()`。
- `backend/app/rag/retriever.py`：查询时调用 `embed_query()`。

## 扩展方向

- 增加批量大小配置，控制显存和内存占用。
- 记录 embedding 模型名称，保证索引可追溯。
- 模型切换时提供重建索引流程。
