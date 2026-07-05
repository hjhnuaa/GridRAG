# Rerank

## 职责

对融合后的候选片段重新排序，筛掉相关性不足的上下文，提升回答依据质量。

## 当前实现位置

- `backend/app/rag/reranker.py`：封装 BGE reranker。
- `backend/app/rag/pipeline.py`：根据 `rag_min_relevance_score` 判断是否 grounded。
- `backend/app/rag/pipeline.py`：`_select_context_chunks()` 控制最终进入 Prompt 的片段。

## 扩展方向

- 对重排失败保留降级逻辑，避免模型不可用导致整条问答链路失败。
- 在 RAG Debug 中观察 rerank score，辅助调参。
- 为低分候选返回“依据不足”提示，而不是强行生成答案。
