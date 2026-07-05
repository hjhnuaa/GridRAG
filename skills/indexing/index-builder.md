# Index Builder

## 职责

负责把分块文本、元数据和向量写入结构化数据库与向量数据库，保证两侧同步。

## 当前实现位置

- `backend/app/ingest/tasks.py`：Celery 入库任务。
- `backend/app/services/documents.py`：文档状态、分块替换和知识统计。
- `backend/app/rag/store.py`：Chroma upsert 和删除。

## 扩展方向

- 入库前删除旧索引，避免重复片段。
- 对空分块直接失败，避免写入脏索引。
- 记录每次入库的耗时、分块数量和失败原因。
