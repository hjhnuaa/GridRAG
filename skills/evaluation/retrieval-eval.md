# Retrieval Eval

## 职责

评估检索阶段是否能召回正确片段，关注命中率、相关性和排序质量。

## 当前实现位置

- `backend/tests/test_chunker.py`：覆盖分块元数据和来源映射。
- `backend/app/rag/pipeline.py`：Debug 输出 dense、sparse、fused、reranked 候选。

## 扩展方向

- 增加固定问答集，检查 top-k 是否包含标准片段。
- 对 BM25、向量、RRF 分别记录指标。
- 对低保、走访、工单等业务场景建立样例集。
