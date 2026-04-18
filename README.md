# GridRAG

基于 RAG 的网格员智能管理与服务辅助系统。

本项目面向基层网格治理场景，围绕“知识查询、事件处置、居民服务、走访记录、治理总览”构建一套本地可运行的业务辅助平台。系统将知识库与结构化治理数据结合起来，让网格员既能查政策、看案例，也能直接维护工单、居民档案和走访记录。

## 1. 项目内容

### 1.1 项目目标

项目希望解决基层治理中的几个典型问题：

- 政策文件、工作手册、历史工单和案例资料分散，现场检索成本高
- 居民诉求、隐患巡查、入户走访等工作容易形成碎片化记录
- 工单从受理到闭环缺少统一视图
- 管理者难以从日常数据中快速看到趋势、分类分布和处置效率

### 1.2 当前实现的业务模块

- 治理总览：展示事件趋势、事件分布、知识库卡片和平均处理时长
- 智能问答：基于知识库做 RAG 问答，返回引用来源
- 事件工单：支持创建、筛选、更新、关闭工单，并提供 AI 辅助填报
- 知识库管理：支持上传 `PDF / DOCX / TXT / XLSX / CSV` 并建立索引
- 居民档案：维护居民信息、重点标签、备注和关联事件
- 走访记录：记录上门走访内容，并生成 AI 走访建议

### 1.3 面向的典型场景

- 居民来电咨询政策办理条件，网格员通过智能问答快速检索政策依据
- 巡查中发现楼道堆物、电梯噪声、消防隐患等问题，直接生成事件工单
- 针对独居老人、慢病居民、低保家庭等重点群体建立走访台账
- 管理端通过治理总览查看近 30 天高频问题、状态分布和处置效率

## 2. 系统架构

项目采用前后端分离架构，当前以本地部署方式运行，不依赖 Docker。

```text
┌──────────────────────────────────────────────┐
│                 Frontend                     │
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
          │                  │                 │
          ▼                  ▼                 ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────────┐
│     MySQL      │  │     Redis      │  │  Qwen Compatible   │
│ 业务主数据库   │  │ 缓存 / Celery  │  │  LLM API           │
└────────────────┘  └────────────────┘  └────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────┐
│                 RAG Pipeline                 │
│ Parser -> Chunker -> Embedding -> Retriever  │
│ -> Reranker -> Prompt -> Generator           │
└──────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────┐
│                    Chroma                    │
│                向量索引存储                  │
└──────────────────────────────────────────────┘
```

### 2.1 架构分层说明

- 前端层：负责页面展示、交互、图表、表单和流式问答渲染
- API 层：通过 FastAPI 提供 REST 接口和 SSE 问答流
- 服务层：封装事件、居民、知识库、统计等业务逻辑
- 数据层：MySQL 保存结构化数据，Redis 做缓存和任务中转，Chroma 保存向量索引
- AI 层：通过 OpenAI 兼容接口调用 Qwen，同时结合本地向量检索和重排

### 2.2 数据流说明

#### 知识库文档数据流

1. 前端上传文档到 `/api/v1/knowledge/upload`
2. 后端校验文件格式与文档类型
3. 文档元数据写入 MySQL
4. 触发解析、分块、向量化和 Chroma 入库
5. 问答时通过检索和重排取回相关片段

#### 智能问答数据流

1. 前端向 `/api/v1/chat/ask` 发起问题
2. 后端执行检索、重排、拼接提示词
3. 调用模型生成回答并通过 SSE 流式返回
4. 同步保存聊天记录、检索日志与引用来源

#### 业务数据流

1. 居民、工单、走访记录存入 MySQL
2. 看板统计从事件表和知识库分块表中聚合生成
3. 居民详情页额外聚合走访记录和关联工单

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
| 大模型调用 | OpenAI 兼容接口调用 Qwen |
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

### 3.3 当前运行方式

- 本地 Conda 环境运行后端
- 本地 Node 环境运行前端
- 本地 MySQL、Redis 提供基础服务
- 默认关闭鉴权，适合开发、演示和原型验证

## 4. 目录结构

```text
.
├─ backend/
│  ├─ app/
│  │  ├─ api/                 # API 路由层
│  │  ├─ core/                # 配置、数据库、缓存、日志、异常
│  │  ├─ ingest/              # 文档解析、向量化、入库任务
│  │  ├─ models/              # ORM 数据模型
│  │  ├─ rag/                 # 检索、重排、生成、向量存储
│  │  ├─ schemas/             # Pydantic 请求响应模型
│  │  └─ services/            # 业务逻辑层
│  ├─ alembic/                # 数据库迁移
│  ├─ prompts/                # Jinja2 Prompt 模板
│  ├─ scripts/                # 数据初始化脚本
│  ├─ tests/                  # 后端测试
│  └─ pyproject.toml
├─ frontend/
│  ├─ src/
│  │  ├─ api/                 # 前端接口封装
│  │  ├─ components/          # 通用组件
│  │  ├─ pages/               # 页面模块
│  │  ├─ stores/              # Zustand store
│  │  ├─ styles/              # 全局样式
│  │  ├─ types/               # TypeScript 类型
│  │  └─ router.tsx           # 前端路由入口
│  └─ package.json
├─ data/                      # 演示知识文档和结构化示例数据
├─ scripts/                   # 环境准备脚本
├─ storage/                   # 上传文件与 Chroma 持久化目录
├─ logs/                      # 日志目录
├─ environment.yml            # Conda 环境定义
├─ .env.example               # 环境变量模板
├─ GRIDRAG_SPEC.md            # 实现规范说明
└─ README.md
```

### 4.1 关键目录职责

- `backend/app/api/v1/`：定义问答、工单、知识库、居民、统计接口
- `backend/app/services/`：封装业务规则和数据聚合逻辑
- `backend/app/rag/`：实现检索、重排、生成和调试链路
- `backend/app/ingest/`：负责文档解析、嵌入和索引建立
- `frontend/src/pages/`：对应系统的五个核心页面
- `data/`：用于演示的知识文档、居民数据、事件数据和走访数据

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

当前默认配置使用本地地址：

- MySQL：`127.0.0.1:3306`
- Redis：`127.0.0.1:6379`

### 5.3 创建后端环境

```powershell
conda env create -f environment.yml
conda activate gridrag
```

或者直接使用脚本：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_conda.ps1
conda activate gridrag
```

### 5.4 安装前端依赖

```powershell
cd frontend
npm install
cd ..
```

### 5.5 初始化数据库

```powershell
cd backend
alembic upgrade head
cd ..
```

### 5.6 启动后端

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5.7 启动前端

新开一个终端窗口执行：

```powershell
cd frontend
npm run dev
```

### 5.8 导入演示数据

如果需要快速把系统跑出可见数据，可以使用仓库中的初始化脚本：

```powershell
cd backend
python scripts/init_core_data.py --residents 100 --events 5 --visits 20 --reset
```

或者使用 `data/structured/` 中的结构化数据：

```powershell
cd backend
python scripts/seed_demo_data.py --dry-run
python scripts/seed_demo_data.py
```

### 5.9 访问地址

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`
- 接口文档：`http://127.0.0.1:8000/docs`

## 6. 重点功能实现的详细解读

### 6.1 智能问答与 RAG 链路

核心入口位于：

- `backend/app/api/v1/chat.py`
- `backend/app/rag/pipeline.py`
- `backend/app/rag/retriever.py`
- `backend/app/rag/generator.py`

实现过程如下：

1. 前端向 `/api/v1/chat/ask` 发送问题，请求体中包含 `session_id`、`question` 和可选的文档过滤条件。
2. `chat.py` 先保存用户消息，再把请求交给 `RAGPipeline.stream_answer()`。
3. `RAGPipeline` 会先做查询规范化，并用问题内容生成缓存键；如果 Redis 中已有答案，直接返回缓存结果。
4. 若无缓存，则调用 `HybridRetriever.retrieve()` 执行混合检索：
   - 稠密检索：先对问题做向量化，再到 Chroma 中做相似度查询
   - 稀疏检索：从 MySQL 中读取分块文本，使用 BM25 进行关键词检索
   - 融合：通过 RRF 把两路结果合并排序
5. 检索结果进入 `BGEReranker` 做二次排序，只保留更相关的片段。
6. `RAGPipeline` 按 token 预算截断上下文，并渲染 `qa_system.j2` 提示词模板。
7. `QwenGenerator.stream_completion()` 调用 Qwen，按 SSE 逐段返回回答文本。
8. 回答结束后，系统把引用标记映射回原始文档片段，并保存：
   - 助手消息
   - 检索日志
   - 最终引用来源
9. 同时把结果写入 Redis，后续相同问题可直接命中缓存。

这条链路的特点是：

- 同时兼顾语义检索和关键词检索
- 回答支持流式返回
- 每次问答都有引用来源
- 可以通过 `/api/v1/chat/debug` 查看检索与提示词细节

### 6.2 知识库上传、解析与索引

核心入口位于：

- `backend/app/api/v1/knowledge.py`
- `backend/app/ingest/tasks.py`

实现过程如下：

1. 前端上传文档到 `/api/v1/knowledge/upload`。
2. `knowledge.py` 校验文件后缀，只允许：
   - `.pdf`
   - `.docx`
   - `.txt`
   - `.xlsx`
   - `.csv`
3. 后端把原始文件保存到 `storage/uploads`，并在 MySQL 中创建文档记录。
4. 上传完成后，接口通过 `trigger_document_ingestion()` 触发索引任务。
5. `ingest_document()` 执行完整入库流程：
   - 使用 `DocumentParser` 解析文件内容
   - 使用 `DocumentChunker` 按规则分块
   - 使用嵌入服务生成向量
   - 把分块记录写入 MySQL
   - 把向量写入 Chroma
   - 更新文档状态为完成或失败

这部分设计的作用是把“原始文档”和“可检索知识片段”分开管理：

- MySQL 管元数据和 chunk 记录
- Chroma 管向量索引
- 前端可以查看上传状态、删除文档、重新索引

### 6.3 事件工单与 AI 辅助填报

核心入口位于：

- `backend/app/api/v1/events.py`
- `backend/app/services/events.py`
- `backend/app/services/assistants.py`
- `frontend/src/components/EventForm/EventForm.tsx`

事件模块提供两类能力：

#### 第一类：普通工单流转

- 列表查询
- 创建工单
- 更新工单
- 关闭工单

这些数据都存储在 `events` 表中，字段包括标题、描述、类型、状态、优先级、地址、关联居民、AI 建议等。

#### 第二类：AI 辅助填报

前端在工单表单中允许用户先输入自然语言描述，再调用 `/api/v1/events/ai-assist`。

后端执行过程如下：

1. `generate_event_assist()` 接收工单描述。
2. 检索范围被限制在 `policy` 和 `manual` 两类知识文档中。
3. 使用混合检索先取 Top-K 候选，再通过重排保留更相关片段。
4. 把片段和描述一起送入 `event_assist.j2` 提示词。
5. 模型输出结构化 JSON，包括：
   - 建议工单类别
   - 建议优先级
   - 建议标题
   - 建议处置动作
   - 关联政策依据
6. 前端再把这些结果回填到表单中，用户可以继续手工修改后提交。

这意味着 AI 在这里扮演的是“辅助录入”和“提高规范性”的角色，而不是直接代替人工完成业务判断。

### 6.4 居民档案、走访记录与 AI 走访建议

核心入口位于：

- `backend/app/services/residents.py`
- `backend/app/api/v1/residents.py`
- `backend/app/services/assistants.py`
- `frontend/src/pages/Residents/ResidentDetailPage.tsx`

这一模块的实现逻辑主要分为三部分：

#### 第一部分：居民档案管理

`create_resident()` 和 `update_resident()` 在写入数据库前会对身份证号和手机号做脱敏处理，避免敏感信息明文保存。居民记录还维护：

- 标签 `tags`
- 备注 `notes`
- 最近走访时间 `last_visit_at`
- 走访次数 `visit_count`

#### 第二部分：走访记录

新增走访时，`add_visit_record()` 会同时完成两件事：

1. 插入一条新的走访记录
2. 回写居民表中的 `last_visit_at` 和 `visit_count`

居民详情页通过 `build_resident_detail()` 聚合同一居民的：

- 基础档案
- 走访时间轴
- 关联事件工单

#### 第三部分：AI 走访建议

走访建议的输入不是单一字段，而是三类信息组合：

- 居民基本档案
- 最近走访记录
- 关联事件工单

`generate_visit_suggest()` 的处理方式是：

1. 优先调用 `visit_suggest.j2` 提示词，由模型输出 JSON 结构建议
2. 如果模型不可用、API Key 未配置或返回异常，则回退到本地规则生成

当前本地规则会结合：

- 居民标签
- 是否存在未闭环事件
- 是否有历史走访记录

生成 3 到 5 条建议以及一段风险摘要。这样设计的好处是，即使演示环境没有接通大模型，功能也不会表现为“点击无反应”。

### 6.5 治理总览统计实现

核心入口位于：

- `backend/app/api/v1/stats.py`
- `backend/app/services/stats.py`
- `frontend/src/pages/Dashboard/DashboardPage.tsx`

治理总览不是写死数据，而是由后端实时聚合生成。

后端统计逻辑包括：

- 近 30 天事件趋势：按日期和事件类型聚合
- 事件类型分布：按 `category` 统计数量
- 事件状态分布：按 `status` 统计数量
- 平均处理时长：按月统计 `created_at -> resolved_at` 的平均小时数
- 知识卡片：按知识分块表中的 `doc_type` 统计数量

`/api/v1/stats/dashboard` 接口还做了 Redis 缓存：

- 缓存键：`stats:dashboard`
- TTL：300 秒

前端页面使用 React Query 拉取数据，使用 ECharts 渲染折线图、饼图和柱状图。看板页的中文展示层与后端枚举值是分开的，前端通过 presenter 把 `COMPLAINT / PENDING / policy` 等内部值映射成中文。

### 6.6 前后端协作方式

从整体实现上看，这个项目并不是“前端页面 + 后端接口”的简单堆叠，而是按以下思路组织的：

- 前端负责页面交互、状态管理和结果展示
- API 层负责暴露标准化接口
- 服务层负责核心业务逻辑
- RAG 层负责智能问答和知识检索
- 数据层负责结构化数据和向量数据的分工存储

因此在后续继续扩展时，通常也应沿着这条分层思路去加功能：

- 新页面优先落到 `frontend/src/pages`
- 新业务逻辑优先落到 `backend/app/services`
- 新智能能力优先落到 `backend/app/rag` 或 `backend/app/services/assistants.py`

