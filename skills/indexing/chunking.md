# Chunking

## 职责

把解析后的文档切成适合召回和引用的片段，并保留页码、章节和文档类型等元数据。

## 当前实现位置

- `backend/app/rag/chunker.py`：按政策、手册、工单、案例采用不同分块策略。
- `backend/app/rag/types.py`：定义 `ParsedDocument`、`ParsedBlock`、`Chunk` 和 `ChunkMetadata`。
- `backend/tests/test_chunker.py`：覆盖基础分块和来源过滤行为。

## 扩展方向

- 为政策条款增加更稳定的条号识别。
- 对超长表格、清单类文档做结构化分块。
- 在入库日志中记录分块数量和平均长度。
