# GridRAG

基于 RAG 的网格员智能管理与服务辅助系统。

本项目面向基层网格治理与社区服务场景，围绕知识查询、事件处置、居民档案、走访记录和治理总览构建一套可本地运行的业务辅助平台。系统把结构化治理数据与知识库文档结合起来，在保留业务台账能力的同时，引入基于 LangChain 的问答与辅助决策链路，用于提升政策检索、工单填写和走访建议的效率。

## 1. 项目内容

### 1.1 项目目标

项目主要解决以下几类实际问题：

- 政策文件、工作手册、案例材料和历史工单分散，现场检索成本高
- 工单流转、居民服务和走访记录缺少统一数据视图
- 基层治理数据沉淀后难以快速形成可视化分析结果
- 网格员在高频重复场景中缺少可直接使用的智能辅助能力

### 1.2 当前实现的业务模块

- 治理总览：展示近 30 天事件趋势、类型分布、状态分布、平均处理时长和知识卡片
- 智能问答：基于知识库文档进行 RAG 问答，并返回引用来源
- 事件工单：支持工单创建、筛选、更新、关闭和 AI 辅助填报
- 知识库管理：支持上传 `PDF / DOCX / TXT / XLSX / CSV` 并建立索引
- 居民档案：维护居民基本信息、重点标签、备注和关联事件
- 走访记录：记录走访内容，并生成 AI 走访建议

### 1.3 典型使用场景

- 居民来电咨询政策办理条件，网格员通过智能问答快速定位政策依据
- 巡查中发现噪声扰民、楼道堆物、消防隐患等问题时直接创建工单
- 针对独居老人、慢病居民、低保家庭等重点群体建立走访台账
- 管理端通过治理总览查看近期高频问题、闭环情况和处置效率

## 2. 系统架构

项目采用前后端分离架构，以 FastAPI 作为服务入口，MySQL 存储结构化业务数据，Chroma 存储向量索引，Redis 提供缓存和任务支撑，AI 链路使用 LangChain 统一封装模型调用能力。

```text
┌──────────────────────────────────────────────┐
│                  Frontend                    │
│ React + TypeScript + Ant Design + ECharts   │
└──────────────────────────────────────────────┘
                      │
                      │ HTTP / SSE
                      ▼
┌──────────────────────────────────────────────┐
│                 FastAPI API                  │
│ chat / events / knowledge / residents / stats│
└──────────────────────────────────────────────┘
          │                  │                 │
          ▼                  ▼                 ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────────┐
│     MySQL      │  │     Redis      │  │ LangChain + Qwen   │
│ 业务主数据库   │  │ 缓存 / Celery  │  │ 模型调用与流式输出 │
└────────────────┘  └────────────────┘  └────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────┐
│              RAG / AI Service Layer          │
│ Parser -> Chunker -> Embedding -> Retriever  │
│ -> Reranker -> Prompt -> LangChain Model     │
└──────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────┐
│                    Chroma                    │
│                向量索引持久化                │
└──────────────────────────────────────────────┘
```

### 2.1 分层说明

- 前端层：负责页面展示、表单交互、图表渲染和流式问答展示
- API 层：通过 FastAPI 对外提供 REST 接口和 SSE 问答流
- 服务层：封装居民、事件、知识库、统计和 AI 辅助逻辑
- 数据层：MySQL 保存结构化数据，Redis 提供缓存与任务中转，Chroma 保存向量索引
- AI 层：使用 LangChain 统一封装 Qwen 兼容模型调用，并与本地混合检索链路结合

### 2.2 关键数据流

#### 知识库数据流

1. 前端上传文档到 `/api/v1/knowledge/upload`
2. 后端校验格式和文档类型，并保存原始文件与文档元数据
3. 解析任务把原文切分为 chunk，并生成嵌入向量
4. Chunk 元数据写入 MySQL，向量写入 Chroma
5. 问答、事件辅助和后续检索链路复用这些知识片段

#### 智能问答数据流

1. 前端向 `/api/v1/chat/ask` 发送问题和可选过滤条件
2. 后端执行查询规范化、混合检索和重排
3. 组装上下文后交给 LangChain `ChatOpenAI` 链路生成回答
4. 回答通过 SSE 流式返回，同时保存聊天记录、检索日志和引用来源

#### 业务数据流

1. 居民、事件、走访记录写入 MySQL
2. 事件辅助填报和走访建议按需调用 AI 服务
3. 治理总览从事件表和知识库 chunk 表中实时聚合统计结果

## 3. 技术栈

### 3.1 后端技术栈

| 类别 | 技术 |
| --- | --- |
| 语言 | Python 3.11 |
| Web 框架 | FastAPI |
| ORM | SQLAlchemy 2.x Async |
| 数据库 | MySQL 8 |
| 缓存 / 队列 | Redis + Celery |
| 向量库 | Chroma |
| 嵌入模型 | BAAI `bge-large-zh-v1.5` |
| 重排模型 | BAAI `bge-reranker-large` |
| LLM 编排 | `langchain-core` |
| 模型接入 | `langchain-openai` + Qwen OpenAI 兼容接口 |
| Prompt 模板 | Jinja2 |
| 迁移工具 | Alembic |
| 测试 / 检查 | Pytest、Ruff、MyPy |

### 3.2 前端技术栈

| 类别 | 技术 |
| --- | --- |
| 框架 | React 18 |
| 语言 | TypeScript |
| 构建工具 | Vite |
| UI 组件 | Ant Design 5 |
| 路由 | React Router 6 |
| 状态管理 | Zustand |
| 服务端状态 | TanStack Query |
| 图表 | ECharts |
| 动效 | Framer Motion |
| HTTP | Axios |

## 4. 目录结构

```text
.
├─ backend/
│  ├─ app/
│  │  ├─ api/                 # API 路由层
│  │  ├─ core/                # 配置、数据库、缓存、日志、异常
│  │  ├─ ingest/              # 文档解析、向量化、入库任务
│  │  ├─ models/              # ORM 数据模型
│  │  ├─ rag/                 # 检索、重排、生成、向量存储、LangChain 适配
│  │  ├─ schemas/             # Pydantic 请求响应模型
│  │  └─ services/            # 业务逻辑层
│  ├─ alembic/                # 数据库迁移
│  ├─ prompts/                # Jinja2 Prompt 模板
│  ├─ scripts/                # 数据初始化脚本
│  ├─ tests/                  # 后端测试
│  ├─ README.md               # 后端包说明
│  └─ pyproject.toml
├─ frontend/
│  ├─ src/
│  │  ├─ api/                 # 前端接口封装
│  │  ├─ components/          # 通用组件
│  │  ├─ pages/               # 页面模块
│  │  ├─ stores/              # 状态管理
│  │  ├─ styles/              # 全局样式
│  │  ├─ types/               # TypeScript 类型
│  │  └─ router.tsx           # 路由入口
│  └─ package.json
├─ data/                      # 演示知识文档与结构化样例数据
├─ scripts/                   # 环境准备脚本
├─ storage/                   # 上传文件与 Chroma 持久化目录
├─ logs/                      # 日志目录
├─ environment.yml            # Conda 环境定义
├─ .env.example               # 环境变量模板
└─ README.md
```

### 4.1 关键目录职责

- `backend/app/api/v1/`：问答、事件、居民、知识库、统计等业务接口
- `backend/app/services/`：业务聚合逻辑和 AI 辅助服务
- `backend/app/rag/`：混合检索、重排、LangChain 模型调用和调试链路
- `backend/app/ingest/`：文档解析、分块、嵌入和向量入库
- `frontend/src/pages/`：治理总览、问答、事件、知识库、居民等页面模块

## 5. 快速启动

### 5.1 环境准备

启动前请先准备：

- MySQL 8.0+
- Redis 6+
- Conda / Miniconda
- Node.js 18+

并确保已经创建数据库：

```sql
CREATE DATABASE gridrag CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5.2 复制环境变量

```powershell
Copy-Item .env.example .env
```

默认配置使用本地地址：

- MySQL：`127.0.0.1:3306`
- Redis：`127.0.0.1:6379`

### 5.3 创建后端环境

```powershell
conda env create -f environment.yml
conda activate gridrag
```

环境文件会通过 `pip -e ./backend[dev]` 安装后端依赖，其中已包含 `langchain-core` 和 `langchain-openai`。

### 5.4 初始化数据库

```powershell
cd backend
alembic upgrade head
cd ..
```

### 5.5 启动后端

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5.6 启动前端

新开一个终端窗口执行：

```powershell
cd frontend
npm install
npm run dev
```

### 5.7 初始化演示数据

如果需要快速跑出业务页面数据，可以执行：

```powershell
cd backend
python scripts/init_core_data.py --residents 100 --events 5 --visits 20 --reset
```

如需导入 `data/structured/` 中的结构化样例数据：

```powershell
cd backend
python scripts/seed_demo_data.py --dry-run
python scripts/seed_demo_data.py
```

### 5.8 访问地址

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`
- 接口文档：`http://127.0.0.1:8000/docs`

## 6. 重点功能实现的详细解读

### 6.1 智能问答与 LangChain RAG 链路

核心入口位于：

- `backend/app/api/v1/chat.py`
- `backend/app/rag/pipeline.py`
- `backend/app/rag/retriever.py`
- `backend/app/rag/generator.py`

整体流程如下：

1. 前端向 `/api/v1/chat/ask` 发起提问，请求体中包含 `session_id`、`question` 和可选文档过滤条件。
2. `chat.py` 保存用户消息后，把请求交给 `RAGPipeline.stream_answer()`。
3. `RAGPipeline` 先做查询规范化，并基于问题与过滤条件生成缓存键；若 Redis 已命中答案，则直接返回缓存结果。
4. 若未命中缓存，则调用 `HybridRetriever.retrieve()` 执行混合检索：
   - 稠密检索：对问题向量化后到 Chroma 中做相似度查询
   - 稀疏检索：从 MySQL chunk 表中读取文本，使用 BM25 做关键词检索
   - 融合：使用 RRF 合并两路候选
5. 候选结果进入 `BGEReranker` 做二次排序，只保留更相关片段。
6. 经过筛选的 `Chunk` 会保留原始元数据，同时可通过 `to_langchain_document()` 转换为 LangChain `Document`，供后续链路复用。
7. `QwenGenerator` 负责把 Jinja2 Prompt 模板与 LangChain 模型运行时衔接起来：
   - `PromptRenderer` 渲染 `qa_system.j2`
   - `ChatPromptTemplate` 组装模型输入
   - `ChatOpenAI` 通过 Qwen 的 OpenAI 兼容接口调用模型
   - `StrOutputParser` 输出纯文本
8. `stream_answer()` 对 LangChain 的流式输出进行 SSE 封装，持续把增量回答返回前端。
9. 回答完成后，系统把引用标记映射回原始文档片段，并保存聊天记录、检索日志和引用来源。

这个版本和原先自写模型请求层的差异在于：

- 模型调用已经统一切到 LangChain Runnable 方式
- 检索结果提供了 LangChain `BaseRetriever` 适配接口，便于后续扩展标准链路
- 保留了原项目已有的混合检索、重排、缓存、日志和 SSE 输出能力

### 6.2 知识库上传、解析与索引

核心入口位于：

- `backend/app/api/v1/knowledge.py`
- `backend/app/ingest/tasks.py`

实现过程如下：

1. 前端上传文档到 `/api/v1/knowledge/upload`
2. 后端校验文件后缀，只允许 `.pdf`、`.docx`、`.txt`、`.xlsx`、`.csv`
3. 原始文件保存到 `storage/uploads`，同时在 MySQL 中创建文档记录
4. 上传成功后触发 `trigger_document_ingestion()` 执行索引任务
5. `ingest_document()` 依次完成：
   - 文档解析
   - 文本分块
   - 向量生成
   - Chunk 元数据写入 MySQL
   - 向量写入 Chroma
   - 文档状态更新为完成或失败

这里的核心设计是把原始文档、结构化 chunk 元数据和向量索引分开管理，既便于检索，也便于后台管理和统计。

### 6.3 事件工单与 AI 辅助填报

核心入口位于：

- `backend/app/api/v1/events.py`
- `backend/app/services/events.py`
- `backend/app/services/assistants.py`
- `frontend/src/components/EventForm/EventForm.tsx`

事件模块分为普通工单流转和 AI 辅助填报两部分。

普通工单流转负责：

- 列表查询
- 创建工单
- 更新工单
- 关闭工单

AI 辅助填报负责把自然语言描述转成更规范的工单表单内容。具体过程如下：

1. 前端先提交事件描述到 `/api/v1/events/ai-assist`
2. `generate_event_assist()` 把检索范围限制为 `policy` 和 `manual` 两类知识文档
3. 混合检索取回候选片段，并通过重排保留高相关内容
4. 使用 `event_assist.j2` 模板生成 Prompt，再通过 LangChain `ChatOpenAI` 调用 Qwen
5. 模型返回 JSON 文本后，后端提取并校验结构化字段
6. 前端把类别、优先级、建议标题、处置动作和政策依据回填到表单中

这部分设计强调的是“辅助录入”和“降低格式不规范”，而不是完全替代人工判断。

### 6.4 居民档案、走访记录与 AI 走访建议

核心入口位于：

- `backend/app/api/v1/residents.py`
- `backend/app/services/residents.py`
- `backend/app/services/assistants.py`
- `frontend/src/pages/Residents/ResidentDetailPage.tsx`

这一模块主要包含三条链路：

#### 居民档案管理

居民创建和更新时会对身份证号、手机号做脱敏处理，同时维护：

- 标签 `tags`
- 备注 `notes`
- 最近走访时间 `last_visit_at`
- 走访次数 `visit_count`

#### 走访记录维护

新增走访记录时，系统会同步完成两件事：

1. 插入新的走访记录
2. 回写居民表中的 `last_visit_at` 和 `visit_count`

居民详情页会聚合同一居民的基础信息、走访时间轴和关联事件。

#### AI 走访建议

`generate_visit_suggest()` 的输入不是单一字段，而是三类信息组合：

- 居民基本档案
- 最近走访记录
- 关联事件工单

处理过程如下：

1. 用 `visit_suggest.j2` 渲染 Prompt
2. 通过 LangChain `ChatOpenAI` 调用 Qwen 返回 JSON 建议
3. 若模型不可用、API Key 未配置或结果异常，则退回本地规则生成

本地兜底规则会结合居民标签、未闭环事件和历史走访情况生成 3 到 5 条建议以及风险摘要，保证演示和离线环境下功能仍可用。

### 6.5 治理总览统计实现

核心入口位于：

- `backend/app/api/v1/stats.py`
- `backend/app/services/stats.py`
- `frontend/src/pages/Dashboard/DashboardPage.tsx`

治理总览的数据不是写死的，而是由后端实时聚合：

- 近 30 天事件趋势：按日期和事件类型聚合
- 事件类型分布：按 `category` 统计数量
- 事件状态分布：按 `status` 统计数量
- 平均处理时长：按月统计 `created_at -> resolved_at` 的平均小时数
- 知识卡片：按知识 chunk 的 `doc_type` 统计数量

`/api/v1/stats/dashboard` 同时使用 Redis 做短期缓存，降低高频刷新时的数据库压力。

### 6.6 前后端协作方式

整个系统不是简单的页面和接口堆叠，而是按清晰分层组织：

- 前端负责页面交互、状态管理和结果展示
- API 层负责暴露标准化接口
- 服务层负责聚合业务逻辑
- RAG 层负责检索、重排、模型调用和智能问答
- 数据层负责结构化数据与向量数据的分工存储

因此后续如果继续扩展，建议也沿着这条边界增加功能：页面进入 `frontend/src/pages`，业务规则进入 `backend/app/services`，智能能力进入 `backend/app/rag` 或 `backend/app/services/assistants.py`。

### 6.7 MCP、长期记忆与联网搜索扩展

本次扩展把 MCP、记忆和联网搜索都接入到后端服务层，并复用智能问答链路。

#### 长期记忆

核心入口位于：

- `backend/app/models/chat_history.py`
- `backend/app/services/memory.py`
- `backend/app/api/v1/memory.py`
- `backend/alembic/versions/20260424_0002_chat_memories.py`

实现方式如下：

1. 新增 `chat_memories` 表，按 `session_id` 保存长期记忆内容、类型、元数据、使用次数和最近使用时间。
2. `/api/v1/memory` 提供记忆写入、检索和删除接口。
3. `/api/v1/chat/ask` 保存用户消息后，会调用 `maybe_save_user_memory()`，当用户明确表达“记住、以后、偏好、默认、称呼”等语义时自动沉淀记忆。
4. `RAGPipeline.stream_answer()` 在生成回答前调用 `find_relevant_memories()`，把当前会话相关记忆渲染进 `qa_system.j2`。
5. Prompt 中明确要求记忆只作为用户偏好和上下文线索，不能作为政策依据。

相关配置：

```env
MEMORY_ENABLED=true
MEMORY_AUTO_SAVE=true
MEMORY_MIN_CONTENT_LENGTH=8
MEMORY_MAX_ITEMS=100
MEMORY_RELEVANCE_LIMIT=5
```

#### 联网搜索

核心入口位于：

- `backend/app/services/web_search.py`
- `backend/app/api/v1/web_search.py`
- `backend/app/rag/pipeline.py`
- `frontend/src/pages/Chat/ChatPage.tsx`
- `frontend/src/components/SourceCard/SourceCard.tsx`

实现方式如下：

1. `WebSearchService` 统一封装搜索供应商，目前支持 `searxng`、`bing`、`serper` 三种模式。
2. `/api/v1/web-search` 提供独立搜索接口，便于调试和被 MCP 工具复用。
3. `/api/v1/web-search/status?probe=true` 提供安全诊断接口，用于检查当前供应商、端点、API Key 是否配置，以及执行一次真实连通性测试。
4. 聊天页新增“联网搜索”开关，请求体通过 `filters.enable_web_search` 传给后端。
5. 后端仅在 `WEB_SEARCH_ENABLED=true` 且请求启用时执行联网搜索，默认关闭，避免离线部署误出网。
6. 搜索结果会以 `[W1] [W2]` 编号进入 Prompt，并作为 `doc_type=web:<provider>` 的来源返回前端。
7. 来源卡片支持 `url` 字段，前端可以直接打开网页来源。
8. 若搜索供应商返回 `401 / 403 / 429` 或网络错误，聊天链路会记录 warning 并自动降级到本地 RAG，不再中断整轮问答。

相关配置：

```env
WEB_SEARCH_ENABLED=false
WEB_SEARCH_PROVIDER=searxng
WEB_SEARCH_ENDPOINT=
WEB_SEARCH_API_KEY=
WEB_SEARCH_TIMEOUT_SECONDS=8
WEB_SEARCH_MAX_RESULTS=5
```

Serper 配置示例：

```env
WEB_SEARCH_ENABLED=true
WEB_SEARCH_PROVIDER=serper
WEB_SEARCH_ENDPOINT=
WEB_SEARCH_API_KEY=your-serper-api-key
```

诊断命令：

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/web-search/status?probe=true" `
  -TimeoutSec 15 |
  ConvertTo-Json -Depth 6
```

#### MCP 网关

核心入口位于：

- `backend/app/api/v1/mcp.py`
- `backend/app/schemas/mcp.py`

实现方式如下：

1. 新增 `/api/v1/mcp` JSON-RPC 入口，支持 MCP 常用方法：`initialize`、`ping`、`tools/list`、`tools/call`。
2. 新增 `/api/v1/mcp/tools` REST 入口，便于在浏览器或接口文档中查看当前暴露的 MCP 工具。
3. MCP 工具复用系统能力，目前包括：
   - `gridrag.memory.add`：为指定会话写入长期记忆
   - `gridrag.memory.search`：检索指定会话的长期记忆
   - `gridrag.web_search`：调用后端配置的联网搜索
4. MCP 返回遵循 JSON-RPC 结构，工具结果使用 `content: [{ type: "text", text: "..." }]` 形式输出。

相关配置：

```env
MCP_ENABLED=true
MCP_PROTOCOL_VERSION=2025-11-25
```

数据库升级：

```powershell
cd backend
alembic upgrade head
```
