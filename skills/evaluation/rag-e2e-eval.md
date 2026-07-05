# RAG E2E Eval

## 职责

从上传文档、入库、检索、重排、生成、来源展示全链路验证系统是否可用。

## 当前实现位置

- `backend/tests/`：覆盖核心单元行为。
- `frontend/src/components/RagDebugPanel/`：辅助人工检查链路。
- `demo/low_income_policy_demo.txt`：可用于本地演示和手工验证。

## 扩展方向

- 增加带临时数据库和临时 Chroma 目录的集成测试。
- 使用固定 demo 文档跑标准问题。
- 在 CI 中分离快速单测和重依赖集成测试。
