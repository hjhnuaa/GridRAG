# Monitoring

## 职责

监控服务可用性、检索质量、模型调用和前端体验。

## 当前实现位置

- `backend/app/api/v1/web_search.py`：提供联网搜索状态诊断。
- `backend/app/services/stats.py`：治理看板统计。
- `frontend/src/pages/Dashboard/DashboardPage.tsx`：前端总览页面。

## 扩展方向

- 增加 RAG 请求量、失败率、平均耗时。
- 增加 embedding、reranker、LLM 服务健康检查。
- 对队列积压和入库失败设置告警。
