# GridRAG Skills Index

这个索引对应根目录 `skills/`，按 RAG 系统能力组织项目说明。运行时代码仍保留在 `backend/` 和 `frontend/`，本索引用于快速理解、答辩讲解和二次开发定位。

## Retrieval / 检索能力

- [query-understanding](skills/retrieval/query-understanding.md)：查询归一化与记忆召回入口。
- [query-rewrite](skills/retrieval/query-rewrite.md)：查询改写策略和后续扩展。
- [retriever-selection](skills/retrieval/retriever-selection.md)：检索通道和文档类型过滤。
- [hybrid-search](skills/retrieval/hybrid-search.md)：Chroma + BM25 + RRF 混合检索。
- [rerank](skills/retrieval/rerank.md)：BGE 重排和 grounded 判断。

## Indexing / 索引构建

- [document-loader](skills/indexing/document-loader.md)：多格式文档解析。
- [chunking](skills/indexing/chunking.md)：分块策略和元数据保留。
- [embedding](skills/indexing/embedding.md)：文本向量化。
- [index-builder](skills/indexing/index-builder.md)：MySQL 分块与 Chroma 索引同步。
- [metadata](skills/indexing/metadata.md)：来源元数据和引用追溯。

## Knowledge Base / 知识库管理

- [data-sources](skills/knowledge-base/data-sources.md)：知识来源。
- [corpus-management](skills/knowledge-base/corpus-management.md)：文档列表、统计和删除。
- [update-sync](skills/knowledge-base/update-sync.md)：更新同步。
- [quality-control](skills/knowledge-base/quality-control.md)：质量控制。
- [versioning](skills/knowledge-base/versioning.md)：版本策略。

## Generation / 生成能力

- [prompt-template](skills/generation/prompt-template.md)：Prompt 模板。
- [context-assembly](skills/generation/context-assembly.md)：上下文组装。
- [llm-generation](skills/generation/llm-generation.md)：模型调用与流式输出。
- [citation](skills/generation/citation.md)：引用来源映射。
- [hallucination-control](skills/generation/hallucination-control.md)：幻觉控制与依据不足兜底。

## Evaluation / 评估能力

- [retrieval-eval](skills/evaluation/retrieval-eval.md)：检索评估。
- [generation-eval](skills/evaluation/generation-eval.md)：生成评估。
- [rag-e2e-eval](skills/evaluation/rag-e2e-eval.md)：端到端评估。
- [metrics](skills/evaluation/metrics.md)：指标定义。
- [benchmark](skills/evaluation/benchmark.md)：基准集规划。

## Observability / 观测与监控

- [logging](skills/observability/logging.md)：日志。
- [tracing](skills/observability/tracing.md)：链路追踪。
- [monitoring](skills/observability/monitoring.md)：监控。
- [alerting](skills/observability/alerting.md)：告警。
- [dashboard](skills/observability/dashboard.md)：可视化面板。

## Integration / 集成与部署

- [api-integration](skills/integration/api-integration.md)：API、SSE 和前端调用。
- [agent-integration](skills/integration/agent-integration.md)：MCP 和外部智能体接入。
- [workflow-examples](skills/integration/workflow-examples.md)：业务工作流示例。
- [tool-usage](skills/integration/tool-usage.md)：工具使用说明。
- [deployment](skills/integration/deployment.md)：部署和环境配置。
