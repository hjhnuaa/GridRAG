# Metadata

## 职责

负责维护文档和片段的来源信息，使回答可以回溯到文档、页码、章节和类型。

## 当前实现位置

- `backend/app/models/document.py`：文档和分块 ORM 模型。
- `backend/app/rag/types.py`：片段元数据结构。
- `backend/app/rag/sources.py`：把片段转成前端来源卡片。

## 扩展方向

- 增加上传人、版本号、有效期等治理字段。
- 对政策类文档维护发布机构和发布日期。
- 在前端来源卡片中展示更完整的元数据。
