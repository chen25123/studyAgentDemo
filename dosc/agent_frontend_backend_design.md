# DevFlow Agent 前后端技术方案与详细设计

## 1. 背景与目标

当前项目已有三类核心业务数据：

- 用户表
- 需求表
- Bug 表

后期目标是构建一个研发流程 AI Agent 系统：

- 前端使用 Vue 3 + Vite，提供对话、指标、风险、报告和操作确认界面。
- 后端使用 Python，基于 LangChain / LangGraph 搭建 Agent。
- Agent 能查询研发数据、解释统计口径、分析风险、生成报告，并逐步支持受控写操作。

本方案强调架构边界、可扩展性、安全性和可测试性，不把 LLM 调用、数据库查询、业务规则和前端展示混在一起。

## 2. 总体架构

推荐采用分层架构：

```text
agent-ui
  Vue 3 + Vite 前端
  只负责展示、交互、调用后端 API

backend api
  FastAPI HTTP 服务
  负责请求校验、鉴权、会话、流式响应、错误处理

agent runtime
  LangGraph 编排层
  负责 Agent 状态、节点流转、多步骤推理、工具调用

agent services
  LangChain 模型、Prompt、结构化输出、工具绑定

tools
  受控工具层
  例如查询 Bug 统计、查询需求风险、生成报告、状态流转

repositories
  数据访问层
  只负责参数化 SQL、事务、数据库映射

database
  MySQL
  存用户、需求、Bug、状态日志、评论、附件、Agent 会话记录
```

核心原则：

- 前端不能直接连接数据库。
- Agent 不能执行任意 SQL。
- LLM 输出不能直接进入数据库写操作。
- 数据库读写必须经过工具层和 repository 层。
- 查询类能力默认只读，写操作必须走确认、权限、审计和事务。

## 3. 技术选型

### 3.1 前端

| 模块 | 技术 |
|---|---|
| 框架 | Vue 3 |
| 构建 | Vite |
| 语言 | TypeScript |
| 状态 | 初期用 Vue 组合式 API，复杂后再引入 Pinia |
| 通信 | HTTP + SSE，后期可加 WebSocket |
| UI | 先自研轻量组件，后期按需要引入组件库 |

前端职责：

- 展示 Agent 对话。
- 展示 Agent 分析过程、工具调用摘要、结果。
- 展示指标卡片、风险列表、报告内容。
- 对写操作做二次确认。
- 不保存密钥，不直接拼 SQL，不直接访问 MySQL。

### 3.2 后端

| 模块 | 技术 |
|---|---|
| Web 框架 | FastAPI |
| 数据校验 | Pydantic |
| Agent 框架 | LangChain + LangGraph |
| LLM 接入 | langchain-openai / OpenAI compatible endpoint |
| 数据库 | MySQL |
| 数据访问 | SQLAlchemy Core 或自定义 repository |
| 配置 | `.env` + 环境变量 |
| 日志 | Python logging，后期接结构化日志 |

后端职责：

- 暴露对话接口。
- 管理会话和上下文。
- 调用 LangGraph Agent。
- 执行受控工具。
- 统一异常处理。
- 做权限、安全和审计。

### 3.3 Agent

LangChain 负责：

- Chat model 接入。
- Tool 定义与绑定。
- Prompt 模板。
- 结构化输出。

LangGraph 负责：

- Agent 状态管理。
- 多节点流程编排。
- 工具调用循环。
- 条件分支。
- 中断与人工确认。
- 后期持久化 checkpoint。

## 4. 后端模块设计

推荐目录结构：

```text
backend 或 llm
  api
    routes
      chat.py
      health.py
      reports.py
    dependencies.py
  core
    config.py
    logging.py
    security.py
  agent
    graph.py
    state.py
    prompts.py
    llm.py
    memory.py
  tools
    bug_tools.py
    requirement_tools.py
    report_tools.py
    workflow_tools.py
  repositories
    bug_repository.py
    requirement_repository.py
    user_repository.py
    workflow_log_repository.py
  schemas
    chat.py
    bug.py
    requirement.py
    common.py
  services
    chat_service.py
    report_service.py
    permission_service.py
```

各层职责：

| 层 | 职责 |
|---|---|
| `api` | HTTP 路由、参数校验、响应格式、SSE 输出 |
| `services` | 业务编排，不直接写 SQL |
| `agent` | LangGraph 状态图、Prompt、节点、记忆 |
| `tools` | Agent 可调用工具，输入输出必须结构化 |
| `repositories` | 数据库访问、参数化 SQL、事务 |
| `schemas` | Pydantic 请求/响应模型 |
| `core` | 配置、日志、安全、公共依赖 |

## 5. 前端模块设计

推荐目录结构：

```text
agent-ui/src
  api
    chat.ts
    reports.ts
    metrics.ts
  components
    chat
      ChatPanel.vue
      MessageList.vue
      MessageInput.vue
      ToolCallTimeline.vue
    dashboard
      MetricCard.vue
      RiskList.vue
      ReportPreview.vue
  composables
    useChat.ts
    useSse.ts
  types
    chat.ts
    report.ts
    metrics.ts
  views
    AgentWorkspace.vue
  App.vue
```

前端页面能力：

- 对话输入与历史展示。
- 显示 Agent 当前状态：思考中、查询中、生成报告中、等待确认。
- 显示工具调用结果摘要。
- 显示错误状态。
- 支持中断或重试。
- 支持写操作确认弹窗。

## 6. API 设计

### 6.1 基础接口

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/health` | 健康检查 |
| `POST` | `/api/chat` | 普通非流式对话 |
| `POST` | `/api/chat/stream` | 流式对话，推荐后期主用 |
| `GET` | `/api/sessions/{session_id}` | 查询会话历史 |
| `DELETE` | `/api/sessions/{session_id}` | 清空会话 |

### 6.2 对话请求

字段设计：

```text
session_id       会话 ID
message          用户输入
mode             chat / analysis / report / operation
context          前端传入的可选上下文
confirm_token    写操作确认 token，可选
```

### 6.3 对话响应

非流式响应：

```text
session_id
reply
tool_calls
citations
needs_confirmation
confirmation_payload
```

流式响应事件：

```text
message_delta       模型文本增量
tool_start          工具开始
tool_result         工具结果摘要
analysis_step       分析步骤
confirmation_needed 需要用户确认
final               最终回答
error               错误
```

建议后期用 SSE 而不是 WebSocket 起步：

- SSE 更适合单向模型流式输出。
- 实现成本低。
- 前端更容易处理。
- 真正需要双向实时控制时再引入 WebSocket。

## 7. LangGraph Agent 详细设计

### 7.1 Agent 状态

AgentState 建议包含：

```text
session_id
messages
user_profile
intent
time_range
business_scope
tool_results
pending_action
needs_confirmation
final_answer
errors
```

不要只维护 messages。实际业务 Agent 需要显式状态，否则后期很难调试和控制。

### 7.2 节点设计

推荐初版 LangGraph 节点：

```text
receive_input
  接收用户输入，写入状态

classify_intent
  判断意图：闲聊、查数、分析、报告、写操作

clarify_if_needed
  口径不明确时追问

plan
  生成执行计划

tool_router
  选择可调用工具

execute_tool
  执行受控工具

analyze_result
  分析工具结果

confirm_action
  写操作前中断，等待用户确认

final_response
  生成最终回答
```

### 7.3 意图分类

意图类型：

```text
general_chat
metric_query
risk_analysis
report_generation
workflow_operation
clarification
```

示例：

- “最近一个月新建了多少 Bug” -> `metric_query`
- “分析质量风险” -> `risk_analysis`
- “生成周报” -> `report_generation`
- “把这个 Bug 关闭” -> `workflow_operation`

### 7.4 口径澄清

必须内置业务口径：

- “新建 Bug”默认表示创建时间在统计周期内。
- “已关闭”表示当前状态为 `closed`，或有 `closed_at`，具体口径需固定。
- “最近一个月”需要明确是自然月还是过去 30 天。
- “延期需求”默认表示 `actual_done_at > planned_due_at`，未完成则按当前时间对比计划时间。

如果口径影响结果，Agent 应主动说明。

## 8. 工具设计

工具必须是小而明确的，不要设计一个万能 SQL 工具。

### 8.1 查询类工具

| 工具 | 说明 |
|---|---|
| `get_bug_count_by_period` | 按时间范围统计 Bug 创建量 |
| `get_bug_close_rate` | 统计关闭量和关闭率 |
| `get_bug_status_distribution` | Bug 状态分布 |
| `get_requirement_status_distribution` | 需求状态分布 |
| `get_delayed_requirements` | 查询延期需求 |
| `get_top_risk_modules` | 查询风险模块 Top N |
| `get_reopened_bug_summary` | 重开 Bug 分析 |

### 8.2 报告类工具

| 工具 | 说明 |
|---|---|
| `build_quality_report_context` | 聚合质量报告所需数据 |
| `build_delivery_report_context` | 聚合交付报告所需数据 |
| `render_report` | 根据结构化上下文生成报告 |

### 8.3 写操作工具

写操作后期再开放：

| 工具 | 说明 |
|---|---|
| `update_bug_status` | 更新 Bug 状态 |
| `assign_bug_owner` | 修改 Bug 负责人 |
| `update_requirement_status` | 更新需求状态 |
| `add_workflow_comment` | 添加评论 |

写操作要求：

- 必须先生成 `pending_action`。
- 前端必须展示确认信息。
- 用户确认后才执行。
- 执行必须开启事务。
- 主表更新和状态日志写入必须同时成功或同时失败。

## 9. SQL 与数据库安全设计

禁止：

- LLM 直接生成任意 SQL 并执行。
- 前端传 SQL 到后端。
- 用字符串拼接用户输入。
- 给 Agent 开放数据库管理员权限。

允许：

- 工具层暴露有限查询能力。
- Repository 使用参数化 SQL。
- 对只读查询做白名单。
- 对写操作做状态机校验。

数据库账号建议：

```text
agent_reader
  只读账号，用于查询类工具

agent_writer
  最小写权限账号，只能写指定业务表和日志表
```

初期可以先用一个账号，但代码结构必须为后续拆权限留位置。

## 10. 记忆设计

记忆分三层：

### 10.1 会话短期记忆

保存最近 N 轮对话。

用途：

- 多轮追问。
- 当前上下文延续。

### 10.2 业务口径记忆

保存用户确认过的统计口径。

例如：

```text
新建 Bug = 创建时间在统计周期内的 Bug
最近一个月 = 当前自然月，除非用户指定过去 30 天
```

### 10.3 长期偏好记忆

保存用户偏好。

例如：

```text
回答优先给结论，再给 SQL 口径
报告用中文
指标展示关闭率、重开率、延期率
```

初期建议先存在 MySQL，后期如果做语义检索，再引入向量库。

## 11. 前后端交互流程

### 11.1 普通问答流程

```text
用户输入
  -> Vue 调用 /api/chat
  -> FastAPI 校验请求
  -> ChatService 调用 LangGraph
  -> Agent 判断意图
  -> 调用查询工具
  -> Repository 查询 MySQL
  -> Agent 解释结果
  -> FastAPI 返回
  -> Vue 展示回答
```

### 11.2 流式回答流程

```text
用户输入
  -> Vue 调用 /api/chat/stream
  -> 后端建立 SSE
  -> Agent 输出步骤
  -> 前端逐步展示：
     正在理解问题
     正在查询数据
     正在分析结果
     最终结论
```

### 11.3 写操作流程

```text
用户要求修改状态
  -> Agent 解析操作意图
  -> 查询当前数据
  -> 校验状态机
  -> 生成 pending_action
  -> 返回 needs_confirmation
  -> 前端展示确认弹窗
  -> 用户确认
  -> 后端执行事务
  -> 写主表 + 写状态日志
  -> 返回操作结果
```

## 12. 状态机设计

需求状态：

```text
clarifying
clarified
pending_development
developing
development_done
pending_testing
testing
testing_done
released
```

Bug 状态：

```text
new
processing
fixed
suspended
reopened
rejected
closed
```

状态流转不能只靠 LLM 判断，必须由后端规则控制。

例如：

- `new -> processing`
- `processing -> fixed`
- `fixed -> closed`
- `fixed -> reopened`
- `processing -> suspended`
- `suspended -> processing`

非法流转必须拒绝，并返回原因。

## 13. 错误处理设计

错误类型：

```text
validation_error
permission_denied
tool_error
database_error
llm_error
ambiguous_intent
confirmation_required
```

前端展示策略：

- 普通错误显示简洁中文。
- 工具错误显示“查询失败/操作失败”，不暴露数据库内部细节。
- LLM 错误允许重试。
- 写操作失败必须说明是否已回滚。

## 14. 观测与审计

需要记录：

- 用户输入
- Agent 意图分类
- 工具调用名称
- 工具入参摘要
- 工具耗时
- 数据库查询耗时
- LLM 耗时
- 写操作前后状态
- 操作者
- 错误信息

不要记录：

- API Key
- 数据库密码
- 大量完整 Prompt
- 不必要的敏感用户信息

后期可以引入 LangSmith 或自建 trace 表。

## 15. 安全策略

### 15.1 前端安全

- 前端不保存 LLM Key。
- 前端不保存数据库密码。
- 前端不传 SQL。
- 前端对写操作做明确确认。

### 15.2 后端安全

- 环境变量管理密钥。
- CORS 限制前端来源。
- API 请求做 Pydantic 校验。
- 工具白名单。
- SQL 参数化。
- 写操作事务保护。
- 权限校验。

### 15.3 Agent 安全

- LLM 不能决定最终权限。
- LLM 不能绕过状态机。
- LLM 不能直接执行任意 SQL。
- 工具结果返回给 LLM 时要控制字段，避免泄露无关信息。

## 16. 测试策略

### 16.1 后端测试

- API 请求校验测试。
- 工具输入输出测试。
- Repository SQL 测试。
- 状态机合法/非法流转测试。
- Agent 意图分类测试。
- 写操作事务回滚测试。

### 16.2 前端测试

- 对话发送测试。
- 错误展示测试。
- 流式消息展示测试。
- 确认弹窗测试。
- 移动端布局检查。

### 16.3 集成测试

- 前端调用后端。
- 后端调用 Agent。
- Agent 调工具。
- 工具查 MySQL。
- 返回结果可解释。

## 17. 开发阶段规划

### 阶段一：基础对话闭环

目标：

- Vue 前端可以和 Python 后端 LLM 对话。
- 后端 LangGraph 管理会话。
- 无数据库工具。

验收：

- 前端发送问题，后端返回 LLM 回复。
- 支持多轮上下文。
- 后端健康检查可用。

### 阶段二：只读数据分析 Agent

目标：

- Agent 可以通过工具查询 MySQL。
- 支持 Bug/需求统计问题。

验收：

- 最近一个月创建 Bug 数。
- 当前关闭率。
- 状态分布。
- 延期需求统计。

### 阶段三：流式输出与工具过程展示

目标：

- 前端展示 Agent 正在做什么。
- 支持 SSE 流式输出。

验收：

- 页面能看到“理解问题 -> 查询数据 -> 分析结果 -> 最终回答”。

### 阶段四：报告生成

目标：

- 生成质量周报、交付风险报告。

验收：

- 报告包含指标、风险、原因和建议。

### 阶段五：受控写操作

目标：

- 支持修改 Bug/需求状态。
- 支持负责人变更。

验收：

- 写操作必须确认。
- 状态机校验有效。
- 日志完整。
- 事务回滚有效。

## 18. 关键设计决策

### 18.1 为什么使用 LangGraph

普通 LangChain Agent 适合快速原型，但研发流程 Agent 需要：

- 状态控制
- 多步骤流程
- 条件分支
- 人工确认
- 工具调用循环
- 失败恢复

这些更适合用 LangGraph 显式建模。

### 18.2 为什么不开放万能 SQL 工具

万能 SQL 工具短期开发快，但风险高：

- 容易泄露数据。
- 容易被 prompt injection 诱导。
- 难以做权限控制。
- 难以测试。
- 难以保证统计口径一致。

因此初期必须用业务工具封装查询能力。

### 18.3 为什么先用 SSE

Agent 输出天然是服务端向客户端持续推送。

SSE 比 WebSocket 更简单：

- 适合流式文本。
- 浏览器原生支持。
- 后端实现成本低。
- 调试容易。

后期如果需要前端实时打断、双向协作，再引入 WebSocket。

## 19. 参考资料

- LangChain Python Overview: https://docs.langchain.com/oss/python/langchain/overview
- LangChain Agents: https://docs.langchain.com/oss/python/langchain/agents
- LangChain Chat Models: https://docs.langchain.com/oss/python/integrations/chat/
- LangGraph Graph API: https://docs.langchain.com/oss/python/langgraph/graph-api
- LangGraph Workflows and Agents: https://docs.langchain.com/oss/python/langgraph/workflows-agents
- FastAPI: https://fastapi.tiangolo.com/
- Vue Style Guide: https://vuejs.org/style-guide/rules-essential.html
- Vite Env and Mode: https://vite.dev/guide/env-and-mode/
- OWASP API Security Top 10: https://owasp.org/API-Security/editions/2023/en/0x00-header/
