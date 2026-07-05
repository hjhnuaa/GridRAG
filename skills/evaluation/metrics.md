# Metrics

## 职责

定义 RAG 链路的质量和性能指标，帮助定位召回、重排和生成问题。

## 当前实现位置

- `backend/app/services/chat.py`：保存检索日志。
- `backend/app/rag/pipeline.py`：记录 retrieval_ms、rerank_scores、top_chunks。
- `frontend/src/components/RagDebugPanel/`：展示调试数据。

## 扩展方向

- 增加召回命中率、重排分数分布、回答耗时和缓存命中率。
- 对失败请求按错误类型聚合。
- 对联网搜索降级次数做单独统计。
