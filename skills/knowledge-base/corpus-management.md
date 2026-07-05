# Corpus Management

## 职责

负责知识库文档列表、统计、删除、重建和状态管理。

## 当前实现位置

- `backend/app/services/documents.py`：文档分页、创建、状态更新、删除和统计。
- `backend/app/api/v1/knowledge.py`：知识库 REST 接口。
- `frontend/src/pages/Knowledge/KnowledgePage.tsx`：前端知识库页面。

## 扩展方向

- 增加批量重建索引。
- 增加失败文档的重试入口。
- 展示每个文档的分块数量、入库时间和错误信息。
