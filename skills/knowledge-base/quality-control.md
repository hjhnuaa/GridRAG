# Quality Control

## 职责

控制知识内容质量，避免空文档、低质量片段和错误元数据影响生成结果。

## 当前实现位置

- `backend/app/ingest/tasks.py`：空分块保护。
- `backend/tests/test_ingest_tasks.py`：覆盖空文档保护。
- `backend/tests/test_prompts.py`：约束 Prompt 的依据和引用规则。

## 扩展方向

- 增加重复片段检测。
- 增加政策过期提示。
- 对低质量分块提供人工复核入口。
