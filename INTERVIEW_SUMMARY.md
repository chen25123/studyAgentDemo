# DevFlow Agent — 面试项目总结

---

## 一、一句话概括

> **一个面向研发流程管理的 AI Agent 系统。团队用自然语言提问，Agent 自动查询数据库、解释口径、分析风险、生成报告，并在受控条件下执行工作流操作。当前完成第一阶段：全栈基础对话闭环。**

---

## 二、解决了什么问题

研发团队日常面对大量数据查询需求——"上个月关闭率多少？""哪些模块 Bug 重开率高？""延期需求集中在哪些人？"——每次都要写 SQL、导出 Excel、人为解读。DevFlow Agent 的核心价值：

1. **降低数据门槛**：PM、QA、TL 用自然语言直接问，不需要会 SQL。
2. **统一统计口径**：Agent 内置业务口径（如"新建 Bug = 创建时间在统计周期内"），避免不同人不同数。
3. **安全可控**：LLM 不能直接操作数据库，所有查询走受控工具层，写操作需要人工确认 + 状态机校验 + 事务保护。
4. **可观测**：每次 LLM 调用的完整 messages、耗时、状态都可追溯。

---

## 三、技术架构

```
┌─────────────────────────────────────────────┐
│  agent-ui (Vue 3 + Vite + TypeScript)       │
│  只负责展示和调用 API，不连数据库            │
└──────────────────┬──────────────────────────┘
                   │ HTTP + SSE
┌──────────────────▼──────────────────────────┐
│  FastAPI (Python)                            │
│  请求校验、CORS、错误处理、会话管理          │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Agent Runtime (LangGraph)                   │  ← 规划中
│  状态管理、节点流转、工具调用循环、中断确认   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Tools Layer                                 │  ← 规划中
│  受控工具：查 Bug 统计、查需求状态、生成报告  │
│  写操作需确认 + 状态机校验 + 事务            │
└──────────────────┬──────────────────────────┘
                   │ 参数化 SQL
┌──────────────────▼──────────────────────────┐
│  Repository Layer (SQLAlchemy)               │
│  数据访问层，只做参数化查询和事务管理         │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  MySQL (agent_workflow)                      │
│  users / requirements / bugs / 状态日志       │
└─────────────────────────────────────────────┘
```

**分层核心原则**：每层只做自己的事，不可跨层。前端不连数据库、Agent 不写 SQL、LLM 输出不进数据库。

---

## 四、技术选型及理由

| 选型 | 理由 |
|---|---|
| **FastAPI** | 原生异步、Pydantic 数据校验、自动 OpenAPI 文档 |
| **LangGraph**（规划） | 相比 LangChain AgentExecutor，LangGraph 提供显式状态图、条件分支、人工中断节点，更适合多步骤业务 Agent |
| **Vue 3 + Pinia** | 组合式 API 比 Options API 更灵活；Pinia 比 Vuex 更简洁，TypeScript 支持更好 |
| **SSE**（规划，非 WebSocket） | Agent 输出是单向流式推送，SSE 浏览器原生支持、实现简单、调试方便。需双向控制时再升级 WebSocket |
| **SQLAlchemy + Alembic** | 参数化查询防注入，Alembic 做数据库版本管理 |
| **pydantic-settings** | 12-Factor App 配置管理，环境变量注入，禁止硬编码密钥 |
| **qwen-plus + OpenAI 兼容端点** | 通过 DashScope 接入国产大模型，兼容 OpenAI SDK 接口标准，切换模型零成本 |

---

## 五、项目亮点（面试重点）

### 5.1 不是"套壳"聊天机器人

市场上很多 AI Agent 项目本质是 `input → LLM → output` 的简单包装。这个项目的关键区别：

- **Agent 不能直接操作数据库**。LLM 只负责理解意图和生成回复，数据库查询通过**工具白名单 + Repository 参数化 SQL** 执行。
- **Agent 不能绕过状态机**。Bug 从 `new → closed` 必须经过合法路径（`new → processing → fixed → closed`），写操作由后端规则校验，不是 LLM 决定。
- **口径设计**。比如"新建 Bug = 创建时间在统计周期内"，不是 `status = 'new'`。业务语义和数据库查询之间有一层显式映射。

### 5.2 LLM Trace 可观测性

自建了完整的 LLM 调用追踪系统：
- `llm_conversations` 表记录每次调用的 trace_id、模型、耗时、状态（success/failed）、token 消耗
- `llm_messages` 表记录完整的 system prompt + user + assistant + tool call 消息链
- 前端 `/admin/llm-traces` 页面可查看、回溯每次 LLM 交互

这个设计在面试中能体现**工程素养**——LLM 是不确定的，必须能追踪每一步推理过程。

### 5.3 安全设计前置

从设计阶段就定义了安全策略：

| 层 | 安全措施 |
|---|---|
| 前端 | 不存 API Key、不传 SQL、不直接连数据库 |
| 后端 | 环境变量管理密钥、CORS 限制来源、Pydantic 输入校验 |
| Agent | 不执行任意 SQL、不决定权限、不绕过状态机 |
| 数据库 | 参数化查询、建议分离只读/读写账号、写操作事务保护 |

面试中可以强调：**安全不是后期打补丁，而是在架构设计时就内建了。**

### 5.4 数据库设计规范

6 张业务表，设计体现实际研发管理经验：

- **软删除**（`deleted_at`）而非物理删除
- **乐观锁**（`version`）防止并发写冲突
- **状态日志**（`workflow_status_logs`）记录每次变更的 from_status、to_status、operator、time，实现完整审计
- **外键约束**保证引用完整性
- 20 万行种子数据（用 CTE 递归生成）方便开发和测试

### 5.5 前后端类型对应

后端 Pydantic Schema 和前端 TypeScript Interface 字段一一对应：

```python
# 后端 (Pydantic)
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(default="default")
```

```typescript
// 前端 (TypeScript)
export interface ChatResponse {
  session_id: string;
  reply: string;
}
```

减少了前后端字段不一致导致的运行时错误。

---

## 六、当前完成度与下一步

### 已完成（阶段一）

| 模块 | 完成情况 |
|---|---|
| Python 后端分层骨架 | API → Service → Agent → Repository → DB 五层全部搭建 |
| FastAPI 路由 | `/health`、`POST /api/chat`、`GET /api/admin/llm-traces` |
| Agent 核心 | LangChain create_agent + 会话记忆（滑动窗口 20 条） |
| LLM Trace | 完整记录每次 LLM 调用的 messages + 耗时 + 状态 |
| Vue 3 前端 | 对话界面 + Trace 管理 + 响应式布局 |
| MySQL 数据库 | 8 张表，含完整种子数据（500 用户、2 万需求、8 万 Bug） |
| 工程化 | pyproject.toml（Ruff + Pytest）、.gitignore、Alembic 迁移骨架 |

### 下一步（阶段二）

- 实现业务 Repository（bug/requirement 查询）
- 实现工具层（7 个只读查询工具）
- 搭建 LangGraph 状态图，替代当前简易 Agent
- 前端指标面板接入后端真实数据

---

## 七、高频面试问题预答

### Q1: 为什么用 LangGraph 而不是直接用 LangChain Agent？

LangChain 的 `create_agent` 适合快速原型，但它是个黑盒——调用工具、循环处理、返回结果都在框架内部。DevFlow 这个场景需要：
- **显式状态**（意图分类、时间范围、待确认操作）
- **条件分支**（闲聊直接回复、查数走工具、写操作走确认）
- **人工中断**（写操作前等待用户确认）
- **失败恢复**（工具调用失败后重试或降级）

这些用 LangGraph 的 `StateGraph` 显式建模更可控、更好调试。

### Q2: 为什么不让 LLM 直接生成 SQL？

四个原因：
1. **安全**：Prompt Injection 可能诱导生成恶意 SQL
2. **口径一致**："新建 Bug"的业务语义和 SQL `WHERE` 条件之间容易偏差
3. **权限**：一条万能 SQL 工具无法做细粒度权限控制
4. **测试**：有限工具的白名单比任意 SQL 好测得多

### Q3: 记忆管理怎么做的？

短期用滑动窗口（保留最近 20 条对话），超出窗口时计划用 LLM 压缩历史做摘要。长期规划引入向量数据库做语义检索，让 Agent 记住用户的偏好口径（如"报告用中文"、"默认统计过去 30 天"）。

### Q4: 写操作的安全性怎么保证？

五道防线：
1. Agent 解析意图 → 生成 `pending_action`
2. 前端展示确认弹窗
3. 用户确认 → 后端校验状态机合法性
4. 开启数据库事务
5. 主表更新 + 状态日志写入同时成功或回滚

### Q5: 前后端怎么通信？为什么选这样设计？

非流式用普通 POST JSON，流式用 SSE。选 SSE 而非 WebSocket 的原因：
- Agent 输出天然是单向推送（不需要前端持续发消息）
- 浏览器原生 `EventSource` 支持，不需要额外库
- FastAPI 的 `StreamingResponse` 实现成本极低
- 后期需要双向打断时再升级，优先用最简单的方案

---

## 八、技术栈速览

| 类别 | 技术 |
|---|---|
| 框架 | Vue 3, FastAPI |
| 语言 | TypeScript (strict), Python 3.13 |
| Agent | LangChain + LangGraph |
| LLM | qwen-plus (DashScope / OpenAI 兼容协议) |
| 数据库 | MySQL 8.0 |
| ORM | SQLAlchemy 2.0 + Alembic |
| 配置 | pydantic-settings, python-dotenv |
| 构建 | Vite 7 |
| 状态管理 | Pinia 3 |
| 代码质量 | Ruff (Python), vue-tsc (TypeScript) |
