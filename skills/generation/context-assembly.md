# Context Assembly

## 职责

负责把检索片段、长期记忆、联网搜索结果和用户问题组装成最终模型上下文。

## 当前实现位置

- `backend/app/rag/pipeline.py`：编排检索、重排、上下文裁剪、Prompt 渲染。
- `backend/app/services/memory.py`：渲染分层记忆上下文。
- `backend/app/services/web_search.py`：提供可选联网搜索结果。

## 扩展方向

- 为上下文预算增加更精确的 token 估算。
- 在 Debug 输出中标识每类上下文占比。
- 对低相关片段保持不注入策略，避免污染答案。
