# DevFlow Agent — 面试项目总结

> 最后更新：2026-06-05

---

## 一、一句话概括

> **一个数据库驱动的 AI 指标分析系统。团队用自然语言提问，Agent 基于语义层生成结构化 QueryPlan，后端白名单校验后编译参数化 SQL 执行。不是套壳聊天机器人，是 LLM + 语义层 + 安全引擎的完整闭环。**

---

## 二、解决了什么问题

1. **新增指标不用改代码**：指标定义存在数据库语义层表中，INSERT 一行即可上线，不需要改 Python 代码、不需要重启服务
2. **LLM 无权生成 SQL**：Agent 只输出 QueryPlan（结构化查询意图），后端 Metric Engine 校验后编译参数化 SQL，不存在 SQL 注入
3. **口径可审计**：每次查询的 QueryPlan + 编译 SQL + 耗时全部存入 `metric_query_logs`，可追溯
4. **维度可复用**：组织架构、模块、状态等维度定义一次，所有指标共享

---

## 三、技术架构（当前状态）

```
┌──────────────────────────────────────────────┐
│  agent-ui (Vue 3 + Vite + TypeScript)        │
│  对话界面 + 指标展示 + LLM Trace 管理         │
└──────────────────┬───────────────────────────┘
                   │ HTTP POST
┌──────────────────▼───────────────────────────┐
│  FastAPI (Python 3.13)                        │
│  /health  /api/chat  /api/admin/llm-traces   │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│  Agent Runtime (LangChain create_agent)       │
│  6 个工具：query_metric / query_bug_metrics / │
│  query_user_metrics / query_org_structure /   │
│  list_available_metrics / get_now_date        │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│  Metric Engine（核心）                        │
│  1. 校验 QueryPlan（白名单）                  │
│  2. 读取语义层定义（Entity/Dimension/Measure/ │
│     Metric 四层元数据表）                      │
│  3. 编译参数化 SQL（ratio → 子查询）          │
│  4. 执行 + 格式化结果 + 口径说明              │
└──────────────────┬───────────────────────────┘
                   │ 参数化 SQL
┌──────────────────▼───────────────────────────┐
│  Repository Layer (SQLAlchemy Core)           │
│  16 张表：业务表 + 语义层表 + 审计日志表      │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│  MySQL 8.0 (agent_workflow)                   │
│  500 用户 / 2 万需求 / 8 万 Bug / 48 组织节点 │
└──────────────────────────────────────────────┘
```

---

## 四、核心亮点（面试重点）

### 4.1 语义层（Metric Layer）— 数据库驱动的指标引擎

**不是简单的 if/else 白名单**，而是一套完整的四层元数据系统：

| 层 | 表 | 职责 | 示例 |
|---|---|---|---|
| Entity | `entity_definitions` | 定义业务对象 | `bug` → base_table=bugs |
| Dimension | `dimension_definitions` | 过滤/分组字段 + JOIN 配置 | `assignee_org_name` → JOIN org_units |
| Measure | `measure_definitions` | 最小聚合单元 | `closed_bug_count` → SUM(CASE WHEN...) |
| Metric | `metric_definitions` | 面向用户的业务指标 | `bug_close_rate` → ratio(closed/total) |

**新增一个指标只需一条 SQL**：
```sql
INSERT INTO metric_definitions (metric_code, metric_name, ...)
VALUES ('bug_reopen_rate', 'Bug 重开率', ...);
```

不需要改 Python 代码、不需要重启服务。

### 4.2 安全：LLM → QueryPlan → 白名单 → 编译 SQL

```
用户: "研发一部本月 Bug 关闭率是多少？"
  ↓
LLM 生成 QueryPlan（不是 SQL！）:
  { metric_codes: ["bug_close_rate"], time_range: {...},
    filters: {"assignee_org_name": "研发一部"} }
  ↓
Metric Engine 校验:
  - bug_close_rate 存在且 status=active? ✓
  - assignee_org_name 在白名单维度里? ✓
  - group_by 在白名单里? ✓
  ↓
Metric Engine 编译 SQL:
  - 读 entity_definitions → base_table=bugs
  - 读 dimension_definitions → JOIN user_org_memberships + org_units
  - 读 measure_definitions → SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END)
  - 读 metric_definitions → formula_type=ratio → 外层子查询
  ↓
参数化执行 → 返回 14.29% + 口径说明
```

LLM **从头到尾没见过一行 SQL**。它在白名单范围内选择指标和维度，后端负责编译和执行。

### 4.3 LLM Trace — 完整可观测

- `llm_messages` 表记录三类消息：`chat` / `tool_call`（含完整 QueryPlan JSON）/ `tool_result`
- `metric_query_logs` 表记录每次指标查询的 QueryPlan + 编译后 SQL + 耗时
- 前端 `/admin/llm-traces` 页面可完整回溯每次 Agent 推理过程

### 4.4 组织架构 — 物化路径 + JOIN 按需加载

- `org_units` 表使用物化路径（`path`），支持树形查询
- `user_org_memberships` 表连接用户和组织
- Repository 根据查询维度**按需 JOIN**：不涉及组织字段时不 JOIN，零额外开销
- 工具层返回 Unicode 树形结构（`├──` `└──` `│`）

### 4.5 数据库设计

16 张表，21 万+行种子数据：

| 类别 | 表 |
|---|---|
| 业务 (6) | users / requirements / bugs / workflow_status_logs / workflow_comments / workflow_attachments |
| 组织 (2) | org_units / user_org_memberships |
| Trace (2) | llm_conversations / llm_messages |
| 语义层 (6) | entity_definitions / dimension_definitions / measure_definitions / metric_definitions / metric_change_logs / metric_query_logs |

设计规范：软删除（`deleted_at`）、乐观锁（`version`）、状态日志、外键约束、物化路径。

---

## 五、技术选型及理由

| 选型 | 理由 |
|---|---|
| **FastAPI** | 原生异步、Pydantic 校验、自动 OpenAPI 文档 |
| **LangChain create_agent** | 当前阶段：工具调用循环足够。后期升级 LangGraph 做显式状态管理 |
| **语义层数据库驱动** | 指标定义存 MySQL 而非 Python 代码，新增指标零代码零重启 |
| **SQLAlchemy Core** | 参数化查询防注入；只读查询用 Core 比 ORM 更直接，无 N+1 问题 |
| **Vue 3 + Pinia** | 组合式 API + TypeScript strict |
| **pydantic-settings** | 12-Factor App 配置，支持多模型（DashScope + DeepSeek） |

---

## 六、高频面试问题预答

### Q1: 为什么不让 LLM 直接生成 SQL？

- **安全**：LLM 只输出 QueryPlan，后端白名单校验后才编译 SQL，SQL 注入不可能
- **口径一致**：指标定义集中在 semantic layer，不会出现不同人问同样问题得到不同 SQL
- **可审计**：每次查询的 QueryPlan + 编译 SQL 存入 metric_query_logs

### Q2: 语义层和普通白名单有什么区别？

普通白名单（`if filter_name == "status": sql += ...`）是硬编码在 Python 里的。语义层把 Entity、Dimension、Measure、Metric 存在数据库，新增指标 INSERT 一行就行，维度 JOIN 配置是 JSON，不是 if/else。

### Q3: 新增一个指标需要做什么？

```sql
-- 1. 定义度量（如果不存在）
INSERT INTO measure_definitions ...;

-- 2. 定义指标
INSERT INTO metric_definitions (metric_code, metric_name, formula_type, formula_config, ...)
VALUES ('bug_reopen_rate', 'Bug 重开率', 'ratio', '{"numerator":"reopened_bug_count","denominator":"bug_count"}', ...);
```

改完即时生效，Agent 下次对话就能查到。

### Q4: ratio 指标的 SQL 怎么编译的？

```sql
-- 内层子查询：分别计算分子分母
SELECT module_name,
  SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END) AS closed_bug_count,
  COUNT(*) AS bug_count
FROM bugs b WHERE ...

-- 外层：除法
SELECT module_name,
  ROUND(closed_bug_count / NULLIF(bug_count, 0) * 100, 2) AS bug_close_rate
FROM (...) sub
```

### Q5: 组织架构查询怎么做 JOIN 的？

不是每次查询都 JOIN 组织表。Repository 会检测当前查询涉及的维度需要哪些 JOIN，只加必要的。查"本月 Bug 总数"时不 JOIN 组织表，查"研发一部 Bug 数"时才 JOIN。

---

## 七、技术栈速览

| 类别 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite 7 + TypeScript (strict) + Pinia 3 + Vue Router 4 |
| 后端 | Python 3.13 / FastAPI / LangChain / SQLAlchemy Core |
| LLM | DeepSeek v4-pro + qwen-plus（OpenAI 兼容协议，可切换） |
| 数据库 | MySQL 8.0（16 张表，21 万+行种子数据） |
| 语义层 | Entity → Dimension → Measure → Metric 四层元数据 |
| 工程化 | pyproject.toml (Ruff + Pytest) / Alembic / .gitignore |
| 配置 | pydantic-settings / 12-Factor App / .env 环境变量 |

---

## 八、GitHub

https://github.com/chen25123/studyAgentDemo
