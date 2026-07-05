# GridRAG

基于 RAG 的网格员智能管理与服务辅助系统。

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=111111)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8-4479A1?logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-6+-DC382D?logo=redis&logoColor=white)
![RAG](https://img.shields.io/badge/RAG-LangChain%20%2B%20Chroma-6B7280)

GridRAG 面向基层网格治理和社区服务场景，围绕政策知识查询、事件工单处置、居民档案、走访记录、治理总览和长期记忆构建一套可本地运行的业务辅助平台。系统把结构化治理数据、知识库文档、向量检索和大模型问答串联起来，让网格员在政策检索、工单填写、走访建议和日常复盘中获得更稳定的辅助能力。

## 目录

- [项目定位与应用场景](#项目定位与应用场景)
- [项目亮点](#项目亮点)
- [功能总览](#功能总览)
- [系统架构](#系统架构)
- [核心设计](#核心设计)
- [技术栈](#技术栈)
- [目录结构](#目录结构)
- [快速启动](#快速启动)
- [环境变量](#环境变量)
- [核心流程](#核心流程)
- [接口入口](#接口入口)
- [测试与构建](#测试与构建)
- [评估结果](#评估结果)
- [面试准备文档](#面试准备文档)
- [常见问题](#常见问题)
- [后续扩展建议](#后续扩展建议)

## 项目定位与应用场景

GridRAG 是一个面向基层网格治理的全栈 RAG 业务系统，不只是一个单轮知识库问答 Demo。项目把居民档案、事件工单、走访记录、知识库文档、长期记忆、联网搜索和治理看板放在同一条业务链路中，让网格员能围绕真实社区治理场景完成查询、研判、填报、跟进和复盘。

典型使用场景：

| 场景 | 业务问题 | 系统能力 |
| --- | --- | --- |
| 政策咨询 | 网格员需要快速确认办理条件、材料和流程 | 上传政策文件后，基于混合检索和引用标注回答 |
| 工单填报 | 居民描述口语化，录入工单耗时且分类不稳定 | AI 根据描述生成事件标题、类别、优先级和处置建议 |
| 重点人群走访 | 独居老人、低保户、慢病居民需要差异化提醒 | 结合居民标签、历史走访和关联事件生成走访建议 |
| 日常复盘 | 管理人员需要查看事件趋势和处理效率 | 统计看板展示事件趋势、状态分布和平均处理时长 |
| 个性化协作 | 同一网格员有固定辖区、表达偏好和历史经验 | 分层长期记忆在新会话中延续上下文，但不作为政策依据 |

如果写进简历，可以概括为：一个基于 FastAPI、React、Chroma、LangChain 和 Qwen 的社区治理智能辅助平台，核心亮点是混合检索 RAG、来源可追溯问答、分层长期记忆、AI 工单填报和面向业务闭环的全栈实现。

## 项目亮点

| 能力 | 说明 |
| --- | --- |
| 本地业务闭环 | 支持居民、事件、走访、知识库和统计看板，适合演示和二次开发。 |
| 混合检索 RAG | 同时使用 Chroma 向量检索和 BM25 关键词检索，再通过 RRF 融合与 BGE 重排模型筛选。 |
| 流式智能问答 | 后端通过 SSE 返回模型增量输出，前端实时展示回答和引用来源。 |
| AI 辅助填报 | 事件描述可自动转成工单字段建议，降低基层录入成本。 |
| AI 走访建议 | 结合居民档案、走访记录和关联事件生成走访提醒；模型不可用时有本地规则兜底。 |
| 长期记忆管理 | 支持组织、项目、个人、本地、全局、自动经验和会话记忆分层，支持手动新增、自动沉淀、搜索、删除和上下文预览。 |
| 联网搜索扩展 | 可选接入 SearXNG、Bing、Serper，默认关闭，避免离线部署误出网。 |
| MCP 网关 | 以 JSON-RPC 形式暴露记忆和联网搜索工具，便于被外部智能体复用。 |

## 功能总览

| 模块 | 当前能力 | 关键入口 |
| --- | --- | --- |
| 治理总览 | 近 30 天事件趋势、类型分布、状态分布、平均处理时长、知识卡片统计 | `frontend/src/pages/Dashboard/DashboardPage.tsx` |
| 智能问答 | RAG 问答、SSE 流式输出、来源卡片、联网搜索开关、RAG Debug、会话删除 | `backend/app/api/v1/chat.py` |
| 记忆管理 | 分层规则、自动记忆、手动记忆、搜索、删除、上下文预览、按会话清空 | `backend/app/api/v1/memory.py` |
| 知识库 | 上传 `PDF / DOCX / TXT / XLSX / CSV`、索引、重建索引、删除文档、知识统计 | `backend/app/api/v1/knowledge.py` |
| 事件工单 | 创建、筛选、更新、关闭、AI 辅助填报 | `backend/app/api/v1/events.py` |
| 居民档案 | 居民信息、重点标签、手机号和身份证脱敏、关联事件、走访时间轴 | `backend/app/api/v1/residents.py` |
| 走访建议 | 基于居民画像和关联事件生成走访建议，支持本地兜底 | `backend/app/services/assistants.py` |
| 联网搜索 | 独立搜索接口、供应商诊断、聊天链路降级保护 | `backend/app/api/v1/web_search.py` |
| MCP | `initialize`、`ping`、`tools/list`、`tools/call` | `backend/app/api/v1/mcp.py` |

## 系统架构

```mermaid
flowchart TB
    User[网格员 / 管理端] --> FE[React + TypeScript 前端]
    FE -->|REST / SSE| API[FastAPI API 层]

    API --> Service[业务服务层]
    Service --> MySQL[(MySQL 结构化数据)]
    Service --> Redis[(Redis 缓存 / Celery)]

    API --> RAG[RAG / AI 编排层]
    RAG --> Retriever[Hybrid Retriever]
    Retriever --> Chroma[(Chroma 向量索引)]
    Retriever --> MySQL
    RAG --> Reranker[BGE Reranker]
    RAG --> Prompt[Jinja2 Prompt]
    Prompt --> LLM[LangChain ChatOpenAI / Qwen]

    API --> MCP[MCP JSON-RPC 网关]
    API --> WebSearch[联网搜索 Provider]
```

### 分层边界

| 层级 | 职责 | 主要目录 |
| --- | --- | --- |
| 前端页面层 | 页面布局、表单交互、图表和流式问答展示 | `frontend/src/pages` |
| 前端接口层 | Axios、SSE、请求响应类型封装 | `frontend/src/api` |
| API 层 | 暴露 REST、SSE、MCP JSON-RPC 接口 | `backend/app/api/v1` |
| 服务层 | 居民、事件、知识库、统计、记忆和 AI 辅助业务逻辑 | `backend/app/services` |
| RAG 层 | 分块、检索、重排、Prompt、模型调用和来源映射 | `backend/app/rag` |
| 入库层 | 文档解析、向量化、索引任务 | `backend/app/ingest` |
| 数据层 | ORM 模型、迁移脚本、向量存储 | `backend/app/models`、`backend/alembic` |

## 核心设计

### RAG 问答链路

GridRAG 的问答链路按“可召回、可排序、可引用、可调试”的思路设计：

1. 用户问题先做轻量归一化，保留原始问题用于回答。
2. 检索侧同时执行 Chroma 向量召回和 BM25 关键词召回。
3. 两路候选通过 RRF 融合，降低不同评分尺度带来的偏差。
4. BGE Reranker 对融合候选重排，低于相关性阈值时走依据不足兜底。
5. Prompt 注入本地知识片段、分层记忆和可选联网搜索结果。
6. 回答要求使用 `[1]`、`[2]`、`[W1]` 等引用标记，后端再按引用标记过滤来源卡片。
7. RAG Debug 返回向量召回、BM25、融合、重排和 Prompt 预览，便于排查召回质量。

### 文档入库链路

知识库入库采用“原始文件保存 + 结构化元数据 + 向量索引”的双写模式。上传文档后，后端先写入文档记录，再触发 Celery 任务解析、分块、嵌入和写入 Chroma。MySQL 保存文档、分块文本和元数据，Chroma 保存向量索引，删除或重建索引时两侧保持同步。

### 长期记忆机制

长期记忆参考 Claude Code 的分层规则思路实现：

| 层级 | 典型内容 | 优先级 |
| --- | --- | --- |
| `organization` | 团队统一规范、回答边界、合规要求 | 低 |
| `project` | 项目内固定术语、模块约定、调试流程 | 中 |
| `personal` | 用户个人偏好、常用表达、职责范围 | 中高 |
| `local` | 本地环境配置、临时开发约定 | 高 |
| `global` | 跨会话生效的全局手动记忆 | 补充 |
| `auto` | 系统自动沉淀的偏好、项目模式、调试经验 | 补充 |
| `session` | 当前会话手动记忆和上下文 | 补充 |

同一主题可以用 `key` 表示，注入 Prompt 前按更具体层级覆盖更通用层级，并做压缩渲染，避免上下文膨胀。Prompt 明确要求记忆只能作为风格、偏好、辖区背景和历史经验线索，不能作为政策依据。

### Prompt 工程

Prompt 模板集中在 `backend/prompts`。问答模板强调证据优先级、引用标注、依据不足兜底和联网搜索降级；事件填报模板严格限制 JSON 字段、类别枚举和优先级规则；走访建议模板强调隐私保护、可执行建议和模型异常时的业务兜底。

### 工程质量

- 后端接口层、服务层、RAG 层和入库层职责拆分清晰。
- Pydantic 统一请求响应模型，SQLAlchemy 2.x Async 处理数据库访问。
- Pytest 覆盖分块、引用来源映射、Prompt 渲染契约、分层记忆和基础安全工具。
- Ruff 约束代码风格，README 保留本地启动、接口入口和常见问题。

## 技术栈

### 后端

| 类别 | 技术 |
| --- | --- |
| 语言 | Python 3.11 |
| Web 框架 | FastAPI |
| ORM | SQLAlchemy 2.x Async |
| 数据库 | MySQL 8 |
| 缓存 / 队列 | Redis + Celery |
| 向量库 | Chroma |
| 文档解析 | PyPDF、python-docx、openpyxl、CSV |
| 检索 | Chroma 向量检索 + BM25 + RRF |
| 嵌入模型 | BAAI `bge-large-zh-v1.5` |
| 重排模型 | BAAI `bge-reranker-large` |
| 模型编排 | LangChain Runnable |
| 大模型接入 | `langchain-openai` + Qwen OpenAI 兼容接口 |
| Prompt | Jinja2 |
| 迁移 | Alembic |
| 质量检查 | Pytest、Ruff、MyPy 配置 |

### 前端

| 类别 | 技术 |
| --- | --- |
| 框架 | React 18 |
| 语言 | TypeScript |
| 构建 | Vite |
| UI | Ant Design 5 |
| 路由 | React Router 6 |
| 服务端状态 | TanStack Query |
| 本地状态 | Zustand |
| 图表 | ECharts |
| 流式输出 | `@microsoft/fetch-event-source` |
| Markdown | react-markdown + rehype-highlight |

## 目录结构

```text
.
├─ backend/
│  ├─ app/
│  │  ├─ api/v1/              # REST、SSE、MCP 接口
│  │  ├─ core/                # 配置、数据库、缓存、日志、异常、安全
│  │  ├─ ingest/              # 文档解析、向量化、索引任务
│  │  ├─ models/              # SQLAlchemy ORM 模型
│  │  ├─ rag/                 # 检索、重排、生成、向量存储、LangChain 适配
│  │  ├─ schemas/             # Pydantic 请求和响应模型
│  │  └─ services/            # 业务服务与 AI 辅助逻辑
│  ├─ alembic/                # 数据库迁移
│  ├─ prompts/                # Jinja2 Prompt 模板
│  ├─ scripts/                # 初始化和演示数据脚本
│  ├─ tests/                  # 后端测试
│  └─ pyproject.toml
├─ frontend/
│  ├─ src/
│  │  ├─ api/                 # 前端接口封装
│  │  ├─ components/          # 通用组件
│  │  ├─ hooks/               # 前端业务 Hook
│  │  ├─ pages/               # 页面模块
│  │  ├─ stores/              # Zustand 状态
│  │  ├─ styles/              # 全局样式
│  │  ├─ types/               # TypeScript 类型
│  │  ├─ utils/               # 展示层工具函数
│  │  ├─ main.tsx             # 前端入口
│  │  └─ router.tsx           # 路由定义
│  ├─ package.json
│  └─ vite.config.ts
├─ demo/                      # 可直接上传测试的轻量知识文档
├─ skills/                    # 按 RAG 能力整理的中文说明文档
│  ├─ retrieval/              # 查询理解、混合检索、重排
│  ├─ indexing/               # 文档解析、分块、嵌入、索引构建
│  ├─ knowledge-base/         # 知识来源、语料管理、同步、质量和版本
│  ├─ generation/             # Prompt、上下文组装、生成、引用、幻觉控制
│  ├─ evaluation/             # 检索评估、生成评估、端到端评估和指标
│  ├─ observability/          # 日志、链路追踪、监控、告警和面板
│  ├─ integration/            # API、Agent、工具、工作流和部署
│  └─ README.md               # RAG 能力结构总览
├─ scripts/                   # 环境准备脚本
├─ storage/                   # 上传文件和 Chroma 持久化目录，默认不入库
├─ logs/                      # 运行日志，默认不入库
├─ .env.example               # 环境变量模板
├─ environment.yml            # Conda 环境定义
├─ skills-index.md            # RAG 能力文档索引
└─ README.md
```

## 快速启动

### 1. 准备基础服务

请先安装并启动：

- MySQL 8.0+
- Redis 6+
- Conda / Miniconda
- Node.js 18+

创建数据库：

```sql
CREATE DATABASE gridrag CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 创建环境变量

```powershell
Copy-Item .env.example .env
```

至少需要检查这些配置：

```env
DATABASE_URL=mysql+asyncmy://gridrag:gridrag@127.0.0.1:3306/gridrag
SYNC_DATABASE_URL=mysql+pymysql://gridrag:gridrag@127.0.0.1:3306/gridrag
REDIS_URL=redis://127.0.0.1:6379/0
QWEN_API_KEY=your-qwen-api-key
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 3. 创建后端环境

```powershell
conda env create -f environment.yml
conda activate gridrag
```

`environment.yml` 会通过 `pip -e ./backend[dev]` 安装后端包和开发依赖。

### 4. 初始化数据库

```powershell
cd backend
alembic upgrade head
cd ..
```

### 5. 启动后端

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 启动前端

新开一个终端：

```powershell
cd frontend
npm install
npm run dev
```

### 7. 访问系统

| 入口 | 地址 |
| --- | --- |
| 前端 | `http://127.0.0.1:5173` |
| 后端健康检查 | `http://127.0.0.1:8000/health` |
| Swagger API 文档 | `http://127.0.0.1:8000/docs` |
| OpenAPI JSON | `http://127.0.0.1:8000/openapi.json` |

## 演示数据

### 业务数据

快速生成居民、事件和走访记录：

```powershell
cd backend
python scripts/init_core_data.py --residents 100 --events 30 --visits 50 --reset
```

如果本地存在 `data/structured/`，可使用 CSV / XLSX 演示数据导入：

```powershell
cd backend
python scripts/seed_demo_data.py --dry-run
python scripts/seed_demo_data.py
```

### 知识库文档

仓库包含一个轻量测试文档：

```text
demo/low_income_policy_demo.txt
```

可在前端“知识库”页面上传，文档类型建议选择 `policy`。如果本地存在完整 `data/knowledge/` 演示目录，也可以按 `policy / manual / ticket / case` 分类上传。

## 环境变量

### 应用与安全

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `APP_NAME` | `GridRAG` | 应用名称 |
| `ENVIRONMENT` | `development` | 运行环境 |
| `DEBUG` | `true` | 是否开启调试 |
| `AUTH_DISABLED` | `true` | 是否禁用鉴权，演示环境默认禁用 |
| `SECRET_KEY` | 示例值 | JWT 签名密钥，生产环境必须替换 |

### 数据库与缓存

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | MySQL async URL | FastAPI 异步数据库连接 |
| `SYNC_DATABASE_URL` | MySQL sync URL | Alembic 迁移连接 |
| `DB_AUTO_CREATE` | `false` | 是否启动时自动建表，建议使用 Alembic |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | 缓存连接 |
| `CACHE_TTL_SECONDS` | `1800` | RAG 回答缓存时间 |

### 模型与 RAG

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `QWEN_API_KEY` | 空 | Qwen / OpenAI 兼容 API Key |
| `QWEN_BASE_URL` | DashScope 兼容地址 | 模型接口地址 |
| `QWEN_MODEL` | `qwen-plus` | 生成模型 |
| `EMBEDDING_MODEL` | `BAAI/bge-large-zh-v1.5` | 嵌入模型 |
| `EMBEDDING_DEVICE` | `cpu` | 嵌入模型运行设备 |
| `RERANKER_MODEL` | `BAAI/bge-reranker-large` | 重排模型 |
| `CHROMA_PERSIST_DIR` | `storage/chroma` | Chroma 持久化路径 |

### 长期记忆

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `MEMORY_ENABLED` | `true` | 是否启用长期记忆 |
| `MEMORY_AUTO_SAVE` | `true` | 是否从用户消息自动沉淀记忆 |
| `MEMORY_MIN_CONTENT_LENGTH` | `8` | 自动记忆最短文本长度 |
| `MEMORY_MAX_ITEMS` | `100` | 单次可加载的最大记忆数量 |
| `MEMORY_RELEVANCE_LIMIT` | `5` | 问答注入的相关记忆数量 |

### 联网搜索

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `WEB_SEARCH_ENABLED` | `false` | 是否允许聊天链路联网搜索 |
| `WEB_SEARCH_PROVIDER` | `searxng` | 可选 `searxng`、`bing`、`serper` |
| `WEB_SEARCH_ENDPOINT` | 空 | 自定义搜索端点 |
| `WEB_SEARCH_API_KEY` | 空 | 搜索供应商 API Key |
| `WEB_SEARCH_TIMEOUT_SECONDS` | `8` | 搜索超时时间 |
| `WEB_SEARCH_MAX_RESULTS` | `5` | 最大搜索结果数 |

## 核心流程

### 智能问答

1. 前端向 `/api/v1/chat/ask` 提交问题、会话 ID、文档类型过滤和联网搜索开关。
2. 后端保存用户消息，并按规则自动沉淀长期记忆。
3. RAGPipeline 读取相关记忆，生成缓存键。
4. 若缓存命中，直接返回缓存答案和来源。
5. 若未命中，执行向量检索、BM25 检索、RRF 融合和 BGE 重排。
6. 如启用联网搜索，搜索结果以 `[W1]`、`[W2]` 形式进入 Prompt。
7. LangChain 调用 Qwen 生成回答，通过 SSE 流式返回。
8. 回答结束后返回来源卡片，并保存助手消息和检索日志。

### 知识库入库

1. 前端上传文档到 `/api/v1/knowledge/upload`。
2. 后端校验扩展名，保存原始文件和文档记录。
3. `DocumentParser` 解析文档为标准文本块。
4. `DocumentChunker` 根据文档类型分块。
5. 嵌入模型生成向量。
6. Chunk 元数据写入 MySQL，向量写入 Chroma。
7. 文档状态更新为 `DONE` 或 `FAILED`。

### 长期记忆

1. 人写规则按 `organization < project < personal < local` 分层保存，跨会话手动背景写入 `global`，越具体的层级优先级越高。
2. 同一层级或跨层级可用 `key` 表示同一主题，注入 Prompt 前按类似 Git 配置的逻辑自动覆盖去重。
3. 用户消息中出现“记住、以后、偏好、默认、称呼”等触发词时，系统自动沉淀跨会话 `auto` 记忆，并标记为 `preference`、`project_pattern`、`debug_experience` 或 `note`。
4. 每次问答前同时加载规则层、全局记忆、自动经验层和当前会话相关记忆，再压缩为带标签的 Prompt 片段。
5. Prompt 明确要求记忆只作为回答风格、用户偏好、辖区背景和历史经验线索，不能作为政策依据。

### 事件辅助填报

1. 前端提交事件自然语言描述。
2. 后端限定检索 `policy` 和 `manual` 类型知识。
3. 结合检索片段和 `event_assist.j2` 生成结构化建议。
4. 前端回填标题、类别、优先级、处置建议和政策依据。

### 走访建议

1. 后端读取居民档案、最近走访记录和关联事件。
2. 优先使用模型生成建议。
3. 模型不可用或结果异常时，退回本地规则生成建议。

## 接口入口

| 模块 | 方法与路径 | 说明 |
| --- | --- | --- |
| 健康检查 | `GET /health` | 服务可用性检查 |
| 聊天问答 | `POST /api/v1/chat/ask` | SSE 流式问答 |
| 聊天历史 | `GET /api/v1/chat/history/{session_id}` | 查询会话历史 |
| 删除会话 | `DELETE /api/v1/chat/sessions/{session_id}` | 删除消息、检索日志和会话记忆 |
| RAG Debug | `POST /api/v1/chat/debug` | 返回检索、重排和 Prompt 预览 |
| 记忆列表 | `GET /api/v1/memory/{session_id}` | 查询或搜索记忆 |
| 新增记忆 | `POST /api/v1/memory` | 手动保存长期记忆 |
| 分层记忆列表 | `GET /api/v1/memory/scopes/{scope}` | 查询组织、项目、个人、本地、全局或自动记忆 |
| 新增分层记忆 | `POST /api/v1/memory/scopes/{scope}` | 写入 scoped 规则、全局记忆或自动记忆 |
| 记忆上下文预览 | `GET /api/v1/memory/{session_id}/context` | 预览最终注入 Prompt 的记忆片段 |
| 删除记忆 | `DELETE /api/v1/memory/{memory_id}` | 删除单条记忆 |
| 清空记忆 | `DELETE /api/v1/memory/sessions/{session_id}` | 清空当前会话记忆 |
| 清空分层记忆 | `DELETE /api/v1/memory/scopes/{scope}` | 清空指定 scoped 记忆 |
| 文档列表 | `GET /api/v1/knowledge/documents` | 查询知识库文档 |
| 上传文档 | `POST /api/v1/knowledge/upload` | 上传并索引文档 |
| 事件列表 | `GET /api/v1/events` | 查询事件 |
| AI 填报 | `POST /api/v1/events/ai-assist` | 生成事件填报建议 |
| 居民列表 | `GET /api/v1/residents` | 查询居民 |
| 走访建议 | `POST /api/v1/residents/{resident_id}/visit-suggest` | 生成走访建议 |
| 治理总览 | `GET /api/v1/stats/dashboard` | 获取统计看板 |
| 联网搜索 | `POST /api/v1/web-search` | 调用搜索供应商 |
| 搜索诊断 | `GET /api/v1/web-search/status?probe=true` | 检查联网搜索配置 |
| MCP | `POST /api/v1/mcp` | JSON-RPC 工具网关 |
| MCP 工具 | `GET /api/v1/mcp/tools` | 查看工具定义 |

## 测试与构建

### 后端检查

```powershell
cd backend
python -m ruff check .
python -m pytest
```

### 前端构建

```powershell
cd frontend
npm run build
```

### 前端预览

```powershell
cd frontend
npm run preview
```

<!-- RAG_EVAL_RESULTS_START -->
## 评估结果

- 生成时间：`2026-07-03T17:15:22.935584+00:00`
- 数据集：20 份知识文档，20 条问题
- 模型：Embedding `BAAI/bge-large-zh-v1.5`；Reranker `BAAI/bge-reranker-large`
- 范围：不包含大模型生成质量评估，只覆盖 RAG 检索、排序、重排、性能和入库链路。

### 指标总览

| 类别 | 指标 | 结果 |
| --- | --- | ---: |
| 入库能力 | 文档成功率 | 100.0% |
| 入库能力 | 总分块数 | 158 |
| 检索质量 | 融合 Recall@5 | 100.0% |
| 检索排序 | 融合 MRR | 0.9750 |
| 检索排序 | 融合 nDCG@5 | 0.9815 |
| 重排质量 | Rerank Recall@5 | 100.0% |
| 重排质量 | Grounded rate | 100.0% |
| 性能 | 端到端检索 p95 | 56666.27 ms |

### 检索与排序

| 通道 | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR | nDCG@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 向量 | 90.0% | 95.0% | 95.0% | 100.0% | 0.9333 | 0.9315 |
| 关键词 | 95.0% | 95.0% | 95.0% | 100.0% | 0.9563 | 0.9500 |
| 融合 | 95.0% | 100.0% | 100.0% | 100.0% | 0.9750 | 0.9815 |

### 重排质量

| Recall@1 | Recall@3 | Recall@5 | MRR | Grounded rate | Top score 均值 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 95.0% | 100.0% | 100.0% | 0.9750 | 100.0% | 0.7026 |

### 性能

| 阶段 | Avg | P50 | P95 |
| --- | ---: | ---: | ---: |
| 向量检索 | 452.72 ms | 422.95 ms | 573.58 ms |
| 关键词检索 | 0.67 ms | 0.56 ms | 1.17 ms |
| 融合 | 0.05 ms | 0.05 ms | 0.08 ms |
| 重排 | 22609.94 ms | 16723.07 ms | 56276.73 ms |
| 端到端检索 | 23063.39 ms | 17081.36 ms | 56666.27 ms |

### 入库能力

| 指标 | 结果 |
| --- | ---: |
| 文档总数 | 20 |
| 成功文档数 | 20 |
| 失败文档数 | 0 |
| 总分块数 | 158 |
| 平均分块数 / 文档 | 7.90 |
| 总入库耗时 | 149993.53 ms |
| 单文档入库 P95 | 24781.39 ms |

### 结论

固定演示集上，入库、融合检索和重排链路表现稳定，可作为项目展示和后续调参基线。
<!-- RAG_EVAL_RESULTS_END -->

## 面试准备文档

仓库提供一份面向简历和面试复盘的详细文档：

```text
docs/resume_interview_qa.md
```

文档包含项目介绍、简历写法、面试官高频追问、RAG / FastAPI / 数据库 / Redis / SSE / Prompt / 长期记忆等八股文问题和可直接组织语言回答的参考答案。

## 常用命令

| 场景 | 命令 |
| --- | --- |
| 创建 Conda 环境 | `conda env create -f environment.yml` |
| 激活环境 | `conda activate gridrag` |
| 升级数据库 | `cd backend; alembic upgrade head` |
| 启动后端 | `cd backend; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| 启动前端 | `cd frontend; npm run dev` |
| 初始化业务数据 | `cd backend; python scripts/init_core_data.py --residents 100 --events 30 --visits 50 --reset` |
| 导入结构化演示数据 | `cd backend; python scripts/seed_demo_data.py --dry-run` |
| 检查联网搜索 | `GET /api/v1/web-search/status?probe=true` |

## 常见问题

### 1. 后端启动时报数据库连接失败

检查：

- MySQL 是否已启动。
- `DATABASE_URL` 用户名、密码、库名是否正确。
- 是否执行过 `CREATE DATABASE gridrag ...`。
- 是否执行过 `alembic upgrade head`。

### 2. Redis 不可用

系统启动时会记录 `redis_unavailable` warning。Redis 不可用会影响缓存和 Celery，但基础接口仍可运行。建议本地开发时启动 Redis，并确认 `.env` 中的 `REDIS_URL` 正确。

### 3. 问答提示没有知识库依据

可能原因：

- 未上传知识库文档。
- 文档仍在 `PROCESSING` 或 `FAILED` 状态。
- 当前聊天页选择的 `doc_type` 与文档类型不匹配。
- 嵌入模型或 Chroma 持久化目录异常。

### 4. 模型调用失败

检查：

- `QWEN_API_KEY` 是否配置。
- `QWEN_BASE_URL` 是否为 OpenAI 兼容接口。
- 当前网络是否可访问模型供应商。
- 模型名 `QWEN_MODEL` 是否可用。

### 5. 联网搜索没有结果

默认 `WEB_SEARCH_ENABLED=false`。如果需要启用：

```env
WEB_SEARCH_ENABLED=true
WEB_SEARCH_PROVIDER=serper
WEB_SEARCH_API_KEY=your-serper-api-key
```

然后访问：

```text
http://127.0.0.1:8000/api/v1/web-search/status?probe=true
```

### 6. 前端请求后端失败

检查：

- 后端是否运行在 `http://127.0.0.1:8000`。
- `.env` 中 `VITE_API_BASE_URL` 是否为 `http://localhost:8000/api/v1` 或正确后端地址。
- 浏览器控制台是否有 CORS 或网络错误。

## 后续扩展建议

| 方向 | 建议 |
| --- | --- |
| 权限体系 | 当前演示环境默认 `AUTH_DISABLED=true`，生产环境应接入真实用户、角色和审计。 |
| 文档队列 | 大文档索引可从 eager Celery 切换到真实异步队列。 |
| 召回评估 | 增加标准问题集，记录 Recall、MRR、引用准确率。 |
| 记忆治理 | 增加记忆合并、过期、敏感词过滤和跨会话用户画像。 |
| 联网搜索 | 增加来源可信度分级、网页正文抽取和搜索结果缓存。 |
| 部署 | 增加 Docker Compose，统一 MySQL、Redis、后端和前端部署。 |
| 观测 | 增加请求耗时、模型耗时、检索命中率和错误率指标。 |

## 维护约定

- 页面功能优先放在 `frontend/src/pages`，可复用 UI 放在 `frontend/src/components`。
- 前端接口统一放在 `frontend/src/api`，类型放在 `frontend/src/types`。
- 后端接口只做请求响应编排，业务逻辑放在 `backend/app/services`。
- RAG 检索、重排、生成和引用处理放在 `backend/app/rag`。
- 数据库结构变更必须新增 Alembic migration。
- 提交前建议运行后端 Ruff、后端 Pytest 和前端 build。
