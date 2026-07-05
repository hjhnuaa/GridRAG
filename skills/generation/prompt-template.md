# Prompt Template

## 职责

集中管理生成阶段的系统提示词，约束回答风格、依据优先级、引用标注和兜底策略。

## 当前实现位置

- `backend/prompts/qa_system.j2`：问答 Prompt。
- `backend/prompts/event_assist.j2`：事件辅助填报 Prompt。
- `backend/prompts/visit_suggest.j2`：走访建议 Prompt。
- `backend/app/rag/generator.py`：Prompt 渲染器。

## 扩展方向

- 为不同文档类型准备专用回答模板。
- 增加 Prompt 版本标识，方便回归测试。
- 保持“记忆只做背景，不做政策依据”的约束。
