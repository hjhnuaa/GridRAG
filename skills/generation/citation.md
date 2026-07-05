# Citation

## 职责

负责把模型回答中的引用标记映射回本地知识片段或网页来源，生成前端来源卡片。

## 当前实现位置

- `backend/app/rag/sources.py`：构建本地来源、网页来源并按 `[1]`、`[W1]` 过滤。
- `backend/app/schemas/chat.py`：`SourceItem` 响应模型。
- `frontend/src/components/SourceCard/SourceCard.tsx`：来源卡片展示。

## 扩展方向

- 对缺失引用标记的回答进行质量提示。
- 增加来源去重和排序策略。
- 在来源卡片中展示页码、章节、URL 和置信分。
