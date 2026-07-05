# Query Understanding

## 职责

负责把用户原始问题整理成适合检索的查询文本，同时保留原始问题用于最终回答，避免检索归一化影响用户语义。

## 当前实现位置

- `backend/app/rag/pipeline.py`：`RAGPipeline.rewrite_query()` 目前做空白归一化。
- `backend/app/services/memory.py`：根据归一化查询召回相关长期记忆。

## 扩展方向

- 增加同义词扩展，例如“低保”与“最低生活保障”。
- 增加政策类意图识别，将办理条件、材料、流程、时限等问题转成检索提示。
- 保持“检索查询”和“回答问题”分离，最终 Prompt 仍注入用户原始问题。
