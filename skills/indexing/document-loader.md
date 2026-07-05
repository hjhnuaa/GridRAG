# Document Loader

## 职责

负责加载 PDF、DOCX、TXT、XLSX、CSV 等文件，并转成统一的文本块。

## 当前实现位置

- `backend/app/ingest/loader.py`：`DocumentLoader` 和 `DocumentParser`。
- `backend/app/api/v1/knowledge.py`：处理上传文件和文档类型。

## 扩展方向

- 增加 OCR 支持，用于扫描版 PDF。
- 增强异常信息，让前端能提示具体失败原因。
- 对空文档保持失败状态，不进入 embedding 和向量索引。
