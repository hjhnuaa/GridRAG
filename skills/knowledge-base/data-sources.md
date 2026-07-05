# Data Sources

## 职责

说明知识库可接入的数据来源，以及它们如何进入 RAG 链路。

## 当前实现位置

- `backend/app/api/v1/knowledge.py`：知识文件上传、删除、重建索引。
- `demo/low_income_policy_demo.txt`：轻量演示知识文档。
- `backend/app/models/document.py`：持久化文档记录。

## 扩展方向

- 增加网页抓取或政务公开数据导入。
- 增加数据库表到知识片段的同步任务。
- 为不同来源设置可信等级和更新周期。
