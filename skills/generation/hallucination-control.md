# Hallucination Control

## 职责

降低依据不足时的幻觉风险，让系统在没有可信上下文时明确兜底。

## 当前实现位置

- `backend/app/rag/pipeline.py`：当本地和网页上下文都不足时返回固定兜底话术。
- `backend/prompts/qa_system.j2`：要求关键事实标注来源。
- `backend/app/rag/reranker.py`：相关性重排用于过滤低质量依据。

## 扩展方向

- 把低置信度原因返回给 Debug 面板。
- 为不同业务场景配置不同兜底话术。
- 对政策类问题优先提示查阅原文或联系上级部门。
