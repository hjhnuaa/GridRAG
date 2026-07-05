# Hybrid Search

## 职责

结合语义召回和关键词召回，降低单一路径对短问题、口语化表达或专有名词不敏感的问题。

## 当前实现位置

- `backend/app/rag/retriever.py`：向量召回走 Chroma，关键词召回走 BM25。
- `backend/app/rag/retriever.py`：`_rrf_merge()` 使用 RRF 融合两路候选。
- `backend/app/rag/store.py`：封装 Chroma collection 查询。

## 扩展方向

- 缓存 BM25 语料索引，减少大语料下每次请求重建成本。
- 对不同文档类型配置不同 top-k。
- 增加检索耗时和候选数量指标。
