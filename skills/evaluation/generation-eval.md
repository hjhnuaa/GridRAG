# Generation Eval

## 职责

评估模型回答是否遵守依据、引用、格式和业务边界。

## 当前实现位置

- `backend/tests/test_prompts.py`：验证 Prompt 中的引用和格式约束。
- `backend/app/rag/sources.py`：按引用标记过滤来源卡片。

## 扩展方向

- 增加端到端回答快照测试。
- 检查回答是否包含未引用的政策结论。
- 对 JSON 类输出增加 schema 校验。
