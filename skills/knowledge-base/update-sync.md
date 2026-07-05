# Update Sync

## 职责

保证文档记录、MySQL 分块和 Chroma 向量索引在上传、删除、重建时保持一致。

## 当前实现位置

- `backend/app/ingest/tasks.py`：入库时替换 MySQL 分块并写入 Chroma。
- `backend/app/services/documents.py`：删除文档和分块。
- `backend/app/rag/store.py`：按文档删除 Chroma 向量。

## 扩展方向

- 为重建索引增加事务型状态流转。
- 对 Chroma 删除失败增加告警和补偿任务。
- 在运维文档中记录索引重建流程。
