# Dashboard

## 职责

用可视化方式展示治理业务和 RAG 链路状态，让管理端快速判断系统健康度。

## 当前实现位置

- `frontend/src/pages/Dashboard/DashboardPage.tsx`：治理总览。
- `frontend/src/components/RagDebugPanel/RagDebugPanel.tsx`：RAG Debug 信息。
- `backend/app/api/v1/stats.py`：统计接口。

## 扩展方向

- 增加知识库入库状态分布。
- 增加 RAG 请求趋势、失败趋势和平均耗时。
- 在 Debug 面板显示上下文预算和来源引用情况。
