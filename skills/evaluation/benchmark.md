# Benchmark

## 职责

沉淀可重复运行的基准集，用于优化模型、Prompt、分块和检索参数。

## 当前实现位置

- 当前以 Pytest 单元测试和人工 demo 验证为主。
- `docs/resume_interview_qa.md` 可辅助项目答辩说明，但不是自动 benchmark。

## 扩展方向

- 建立 `question -> expected source -> expected answer points` 数据集。
- 比较不同 top-k、chunk size、rerank 阈值的效果。
- 输出中文评测报告，支持毕业设计或项目答辩。
