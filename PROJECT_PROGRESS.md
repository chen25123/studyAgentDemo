# DevFlow Agent — 项目进度文档

> 最后更新：2026-06-03

---

## 1. 项目概述

**项目名称**：DevFlow Agent（研发流程智能助手）

**目标**：构建一个面向研发流程数据分析的 AI Agent 系统，能查询研发数据、解释统计口径、分析风险、生成报告，并逐步支持受控写操作。

**技术栈**：

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + TypeScript + Pinia + Vue Router |
| 后端 | Python 3.13 + FastAPI |
| Agent | LangChain + LangGraph |
| LLM | DashScope 兼容端点（阿里云），模型 qwen-plus |
| 数据库 | MySQL 8.0（agent_workflow） |
| ORM | SQLAlchemy 2.0 + Alembic |
| 配置 | pydantic-settings + .env |

---

## 2. 总体进度：阶段一已完成（基础对话闭环）

按设计文档 `dosc/agent_frontend_backend_design.md` 的 5 个阶段划分：

| 阶段 | 内容 | 状态 |
|---|---|---|
| 阶段一 | 基础对话闭环 | ✅ 完成 |
| 阶段二 | 只读数据分析 Agent | ❌ 未开始 |
| 阶段三 | 流式输出与工具过程展示 | ❌ 未开始 |
| 阶段四 | 报告生成 | ❌ 未开始 |
| 阶段五 | 受控写操作 | ❌ 未开始 |

---

## 3. 已完成内容详情

### 3.1 后端 Python（`llm/`）

```
llm/
├── __init__.py                          ✅ 包声明
├── config.py                            ✅ Pydantic Settings，.env 配置，数据库 URL 构建
├── api/
│   ├── __init__.py                      ✅
│   ├── app.py                           ✅ FastAPI 应用，CORS 中间件，/health 端点
│   ├── chat.py                          ✅ POST /api/chat — 基础对话接口
│   └── llm_trace.py                     ✅ GET /api/admin/llm-traces, GET /api/admin/llm-traces/{id}
├── agent/
│   ├── __init__.py                      ✅
│   └── llm.py                           ✅ DevFlowAgent：LangChain create_agent，会话管理，Trace 记录
├── services/
│   ├── __init__.py                      ✅
│   ├── chat_service.py                  ✅ ChatService：桥接 API → Agent
│   └── llm_trace_service.py             ✅ LlmTraceService：Trace 查询编排
├── repositories/
│   ├── __init__.py                      ✅
│   ├── database.py                      ✅ SQLAlchemy Engine + SessionLocal
│   ├── db.py                            ✅ 原始连接获取（兼容过渡期）
│   └── llm_trace_repository.py          ✅ 参数化 SQL，conversation CRUD + messages 写入/查询
├── schemas/
│   ├── __init__.py                      ✅
│   ├── chat.py                          ✅ ChatRequest / ChatResponse（Pydantic）
│   └── llm_trace.py                     ✅ LlmTraceSummary / LlmTraceMessage / LlmTraceDetail
├── migrations/
│   ├── env.py                           ✅ Alembic 在线/离线迁移配置
│   └── versions/.gitkeep                ✅ 待写入首次迁移
└── tests/
    └── test_app.py                      ✅ 基础测试：app title + /health 路由
```

**关键实现细节**：

- **Agent 记忆**：使用 LangChain `create_agent`，会话历史存储在 `DevFlowAgent.sessions` 字典中，每次保留最近 20 条消息（滑动窗口）。
- **LLM Trace**：每次对话自动记录到 `llm_conversations` + `llm_messages` 表，支持成功/失败状态、耗时、完整 messages 追溯。
- **配置安全**：API Key 通过环境变量注入，`.env.example` 提供模板，`.env` 不提交。

### 3.2 前端 Vue 3（`agent-ui/`）

```
agent-ui/src/
├── main.ts                              ✅ 应用入口，挂载 Pinia + Router
├── App.vue                              ✅ 根组件
├── styles.css                           ✅ 全局样式 + 响应式布局（760px / 1100px 断点）
├── router/index.ts                      ✅ /chat（对话）, /admin/llm-traces（Trace 管理）
├── api/
│   ├── http.ts                          ✅ Axios 实例，baseURL /api，60s 超时
│   ├── chat.ts                          ✅ sendChatMessage()
│   └── llmTraces.ts                     ✅ fetchLlmTraces(), fetchLlmTraceDetail()
├── stores/
│   ├── chatStore.ts                     ✅ Pinia：消息列表、发送、加载状态、建议问题
│   └── traceStore.ts                    ✅ Pinia：Trace 列表、详情选择
├── views/
│   ├── ChatView.vue                     ✅ 对话区 + 指标卡片 + 风险面板（数据当前为 mock）
│   └── LlmTraceView.vue                 ✅ Trace 列表 + 详情面板
├── components/
│   ├── layout/AppShell.vue              ✅ 主布局：侧边栏 + RouterView
│   ├── layout/SidebarNav.vue            ✅ 导航 + 数据源信息展示
│   ├── chat/MessageList.vue             ✅ 消息列表渲染
│   ├── chat/MessageInput.vue            ✅ 输入框 + 快捷建议按钮
│   ├── traces/TraceList.vue             ✅ Trace 摘要列表
│   └── traces/TraceDetail.vue           ✅ Trace 详情（完整 messages）
└── types/
    ├── chat.ts                          ✅ ChatMessage, ChatResponse
    ├── llmTrace.ts                      ✅ LlmTraceSummary, LlmTraceMessage, LlmTraceDetail
    └── dashboard.ts                     ✅ Metric, RiskItem
```

**关键实现细节**：

- Vite 开发代理：`/api` → `http://127.0.0.1:8010`
- 前端类型与后端 Pydantic schema 一一对应
- 侧边栏部分导航项（需求巡检、Bug 质量、报告生成）仅为占位，无功能

### 3.3 数据库设计

**业务表**（`dosc/workflow_schema.sql`）：

| 表 | 说明 | 模拟数据量 |
|---|---|---|
| users | 用户表 | 500 |
| requirements | 需求表（8 种状态流转） | 20,000 |
| bugs | Bug 表（7 种状态流转） | 80,000 |
| workflow_status_logs | 状态流转日志 | 70,000 |
| workflow_comments | 评论 | 30,000 |
| workflow_attachments | 附件 | 12,000 |

**Trace 表**（已建表）：

| 表 | 说明 |
|---|---|
| llm_conversations | LLM 调用记录（trace_id, session_id, 状态, 耗时, tokens） |
| llm_messages | 每次调用的完整 messages（role, content, message_type） |

**种子数据脚本**：`dosc/seed_workflow_data.sql`（使用 CTE 递归生成模拟数据）

---

## 4. 待完成内容（按优先级）

### 4.1 高优先级 — 阶段二前置工作

- [ ] **工具层实现**：`tools/` 目录为空（设计文档定义了 7 个查询工具 + 3 个报告工具）
- [ ] **业务 Repository**：`bug_repository.py`, `requirement_repository.py`, `workflow_log_repository.py` 均未实现
- [ ] **LangGraph 状态图**：当前使用 `langchain.agents.create_agent`（简易 Agent），未使用 LangGraph 的 `StateGraph`。设计文档定义了 10 个节点的状态图（classify_intent → plan → tool_router → execute_tool → ...）
- [ ] **Agent State**：当前仅有 `sessions` 字典存消息历史，缺少设计文档定义的显式 AgentState（intent, time_range, tool_results, pending_action 等字段）
- [ ] **意图分类**：未实现 classify_intent 节点（general_chat / metric_query / risk_analysis / report_generation / workflow_operation）
- [ ] **Alembic 首次迁移**：`migrations/versions/` 为空，未生成 migration 脚本
- [ ] **数据库 schema 同步**：业务表（users, requirements, bugs 等）的建表 SQL 在 `dosc/` 中，需确认是否已在目标数据库执行

### 4.2 中优先级

- [ ] **SSE 流式输出**（阶段三）：当前 chat 接口为普通 POST 非流式，设计文档规划了 `/api/chat/stream` SSE 端点
- [ ] **前端指标动态化**：ChatView.vue 中的 metrics 和 risks 为硬编码 mock 数据，需接入后端 API
- [ ] **前端侧边栏导航**：需求巡检、Bug 质量、报告生成 三个入口为占位
- [ ] **Logging**：当前无结构化日志，设计文档提到需要记录工具调用、数据库查询耗时等
- [ ] **测试补齐**：仅 2 个基础测试，设计文档定义了完整的测试策略（工具测试、状态机测试、集成测试）

### 4.3 低优先级 — 后期阶段

- [ ] **报告生成**（阶段四）：报告模板、聚合上下文、渲染
- [ ] **受控写操作**（阶段五）：确认流程、状态机校验、事务保护、审计日志
- [ ] **向量数据库**：长期记忆的语义检索（设计文档提到后期引入）
- [ ] **WebSocket**：实时双向控制（设计文档建议先用 SSE）
- [ ] **LangSmith / 自建观测**：全链路追踪

---

## 5. 目录结构总览

```
d:\chenxjAgent\python1\
├── .claude/settings.local.json          # Claude Code 权限配置
├── .env                                 # 环境变量（不提交）
├── .env.example                         # 环境变量模板
├── .ruff_cache/                         # Ruff lint 缓存
├── DEVELOPMENT_GUIDELINES.md            # 开发规范（优先级定义）
├── PROJECT_PROGRESS.md                  # 本文档
├── pyproject.toml                       # Ruff + Pytest 配置
├── requirements.txt                     # Python 依赖
├── alembic.ini                          # Alembic 迁移配置
├── llm/                                 # 后端 Python 包
│   ├── api/          (FastAPI 路由)
│   ├── agent/        (LLM Agent 核心)
│   ├── services/     (业务编排)
│   ├── repositories/ (数据访问)
│   └── schemas/      (Pydantic 模型)
├── migrations/                          # Alembic 迁移脚本
├── tests/                               # 测试
├── dosc/                                # 设计文档 + SQL 脚本
│   ├── agent_frontend_backend_design.md # 完整技术方案（770 行）
│   ├── someRead.md                      # 学习笔记
│   ├── workflow_schema.sql              # 业务表建表 SQL
│   ├── llm_trace_schema.sql             # LLM Trace 表建表 SQL
│   └── seed_workflow_data.sql           # 模拟数据生成脚本
└── agent-ui/                            # Vue 3 前端
    ├── src/          (源码)
    ├── dist/         (构建产物)
    └── node_modules/
```

---

## 6. 启动方式

### 后端

```bash
# 1. 配置 .env（复制 .env.example 并填入真实值）
cp .env.example .env

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动
uvicorn llm.api.app:app --host 127.0.0.1 --port 8010
```

### 前端

```bash
cd agent-ui
npm install
npm run dev        # 开发模式，Vite 代理 /api → 127.0.0.1:8010
npm run build      # 生产构建（含 vue-tsc 类型检查）
```

### 数据库

```bash
# 执行建表 SQL（业务表 + Trace 表）
mysql -u root -p < dosc/workflow_schema.sql
mysql -u root -p < dosc/llm_trace_schema.sql

# （可选）灌入模拟数据
mysql -u root -p < dosc/seed_workflow_data.sql
```

---

## 7. 关键设计决策（已定案）

1. **分层架构**：API → Service → Agent/Tools → Repository → DB，各层不可越界
2. **Agent 不执行任意 SQL**：工具层暴露有限查询能力，Repository 参数化 SQL
3. **流式先用 SSE**：单向推送模型输出，比 WebSocket 简单，后期按需升级
4. **Vue 3 组合式 API + Pinia**：状态管理用组合式 store
5. **TypeScript strict**：禁止 `any`，边界数据用 `unknown` + 类型守卫
6. **配置全部环境变量**：12-Factor App 风格，不硬编码敏感信息
