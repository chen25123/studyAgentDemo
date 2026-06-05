# 语义层 Metric Layer 与 Agent 指标工作流需求文档

## 1. 背景

当前系统已经具备用户、组织、需求、Bug、LLM Trace 等基础能力。随着查询需求增长，如果继续为每个问题单独写工具，会出现工具数量膨胀和口径难维护的问题。

典型问题包括：

- 最近一个月创建了多少 Bug？
- 研发一部本月 Bug 关闭率是多少？
- 按模块统计本月 Bug 关闭率。
- 某个小组的 Bug 重开率是多少？
- 当月创建且已关闭 Bug 数 / 当月创建 Bug 总数。

这些问题本质不是不同工具，而是：

```text
指标 metric
  + 时间范围 time_range
  + 过滤条件 filters
  + 分组维度 group_by
```

因此系统应建设一套轻量语义层：

```text
Entity Layer
Dimension Layer
Measure Layer
Metric Layer
Query Layer
```

目标是让业务口径沉淀在语义层中，让 Agent 基于语义层生成结构化查询计划，而不是临时生成 SQL 或不断新增碎工具。

## 2. 总体目标

### 2.1 业务目标

- 支持用户提出新的指标需求。
- 支持开发人员通过 Agent 创建指标定义草案。
- 支持开发人员审核并发布指标。
- 支持用户通过自然语言直接查询已发布指标。
- 指标口径可复用、可追溯、可审计。
- 新增指标不要求新增 Agent 工具。

### 2.2 技术目标

- 建立 Entity、Dimension、Measure、Metric 四层元数据。
- 使用统一 `query_metric` 工具查询指标。
- Agent 负责生成结构化 QueryPlan。
- 后端 Metric Engine 负责校验 QueryPlan 并编译安全 SQL。
- 禁止 LLM 直接生成并执行任意 SQL。

## 3. 核心原则

```text
用户说业务语言。
Agent 生成 QueryPlan。
语义层解释指标口径。
Metric Engine 编译 SQL。
数据库只执行后端生成的安全 SQL。
结果必须返回口径说明。
```

## 4. 总体流程

### 4.1 指标建设流程

```text
用户提出指标需求
  -> 开发人员进入指标创建模式
  -> Agent 澄清指标口径
  -> Agent 生成指标草案
  -> 系统校验实体、维度、度量、公式
  -> 开发人员审核
  -> 指标进入 draft/review/active
  -> 用户可查询 active 指标
```

### 4.2 指标查询流程

```text
用户自然语言提问
  -> Agent 识别指标
  -> Agent 解析时间范围
  -> Agent 解析组织、人员、模块等过滤条件
  -> Agent 生成 QueryPlan
  -> 后端校验 QueryPlan
  -> Metric Engine 读取语义层定义
  -> Metric Engine 编译安全 SQL
  -> 执行查询
  -> Agent 解释结果和口径
```

## 5. 语义层模型

### 5.1 Entity Layer：实体层

Entity 表示业务对象，不直接暴露底层 SQL 表给 Agent。

第一阶段实体：

```text
bug
requirement
user
org_unit
```

Bug 实体示例：

```text
entity_code: bug
entity_name: Bug
base_table: bugs
primary_key: id
default_time_field: created_at
default_filter: deleted_at IS NULL
```

Entity 层解决：

```text
指标基于哪个业务对象？
默认时间字段是什么？
默认过滤条件是什么？
```

### 5.2 Dimension Layer：维度层

Dimension 表示可过滤、可分组、可展示的业务字段。

Bug 第一阶段维度：

```text
status
severity
priority
module_name
product_line
assignee_id
reporter_id
assignee_org_id
assignee_org_name
```

每个维度应定义：

```text
dimension_code
dimension_name
entity_code
field_expression
join_config
data_type
is_filterable
is_groupable
allowed_values
status
```

组织维度示例：

```text
dimension_code: assignee_org_name
entity_code: bug
field_expression: org_units.org_name
join_config:
  bugs.assignee_id -> user_org_memberships.user_id
  user_org_memberships.org_unit_id -> org_units.id
```

Dimension 层解决：

```text
用户说“研发一部”“按模块”“按负责人”，系统知道如何映射到数据库。
```

### 5.3 Measure Layer：度量层

Measure 是最小可复用统计能力。

Bug 第一阶段度量：

```text
bug_count
closed_bug_count
reopened_bug_count
suspended_bug_count
```

示例：

```text
bug_count:
  aggregation: count
  expression: *
  filters: {}

closed_bug_count:
  aggregation: count
  expression: *
  filters:
    status = closed

reopened_bug_count:
  aggregation: count
  expression: *
  filters:
    reopened_count > 0
```

Measure 层解决：

```text
基础统计逻辑只定义一次，多个业务指标复用同一套度量。
```

### 5.4 Metric Layer：指标层

Metric 是面向用户的业务指标，通常由一个或多个 Measure 组合而成。

第一阶段支持：

```text
count
ratio
```

Bug 关闭率示例：

```text
metric_code: bug_close_rate
metric_name: Bug 关闭率
entity_code: bug
formula_type: ratio
numerator_measure: closed_bug_count
denominator_measure: bug_count
time_field: created_at
format_type: percent
description: 统计周期内创建的 Bug 中，当前状态为 closed 的占比。
```

Metric 层解决：

```text
用户使用“关闭率”“重开率”“按期完成率”等业务语言，而不是 SQL 或 COUNT。
```

### 5.5 Query Layer：查询计划层

Agent 输出 QueryPlan，而不是 SQL。

示例：

```json
{
  "metric_codes": ["bug_close_rate"],
  "time_range": {
    "start_date": "2026-06-01",
    "end_date": "2026-06-30"
  },
  "filters": {
    "assignee_org_name": "研发一部"
  },
  "group_by": ["module_name"]
}
```

QueryPlan 必须经过后端校验后才能执行。

## 6. 指标创建模式

### 6.1 用户故事：创建 Bug 关闭率

用户提出：

```text
我想看本月创建且已关闭 Bug 数 / 本月创建 Bug 总数。
```

Agent 应先澄清：

```text
关闭是 current status = closed，还是 closed_at 不为空？
时间字段是 created_at 还是 closed_at？
是否排除 deleted_at 不为空的数据？
是否支持按组织、模块、负责人拆分？
```

确认后生成草案：

```json
{
  "metric_code": "bug_close_rate",
  "metric_name": "Bug 关闭率",
  "entity_code": "bug",
  "formula_type": "ratio",
  "numerator_measure": "closed_bug_count",
  "denominator_measure": "bug_count",
  "time_field": "created_at",
  "format_type": "percent",
  "description": "统计周期内创建的 Bug 中，当前状态为 closed 的占比。"
}
```

开发人员确认后发布。

### 6.2 指标状态流转

```text
draft
  -> review
  -> active
  -> deprecated
```

只有 `active` 指标允许用户查询。

## 7. 指标查询模式

### 7.1 用户查询

用户输入：

```text
研发一部本月 Bug 关闭率是多少？
```

Agent 生成：

```json
{
  "metric_codes": ["bug_close_rate"],
  "time_range": {
    "start_date": "2026-06-01",
    "end_date": "2026-06-30"
  },
  "filters": {
    "assignee_org_name": "研发一部"
  },
  "group_by": []
}
```

系统返回：

```text
研发一部在 2026-06-01 至 2026-06-30 的 Bug 关闭率为 X%。

口径：统计周期内创建的 Bug 中，当前状态为 closed 的占比。
```

### 7.2 按维度拆分

用户输入：

```text
按模块看本月 Bug 关闭率。
```

Agent 生成：

```json
{
  "metric_codes": ["bug_close_rate"],
  "time_range": {
    "start_date": "2026-06-01",
    "end_date": "2026-06-30"
  },
  "filters": {},
  "group_by": ["module_name"]
}
```

## 8. Metric Engine 要求

Metric Engine 负责：

- 校验 `metric_code` 是否存在。
- 校验指标状态是否为 `active`。
- 校验 `filters` 是否是允许过滤的维度。
- 校验 `group_by` 是否是允许分组的维度。
- 根据 Entity 定义选择主表。
- 根据 Dimension 定义补充 join。
- 根据 Measure 定义生成聚合表达式。
- 根据 Metric 定义组合公式。
- 使用参数化 SQL 执行查询。
- 返回结构化结果和口径说明。

禁止：

```text
LLM 直接生成 SQL。
用户直接输入 SQL。
未在语义层注册的字段被查询。
未授权组织数据被查询。
```

## 9. 推荐表设计

### 9.1 entity_definitions

```text
id
entity_code
entity_name
base_table
primary_key
default_time_field
default_filter
description
status
created_at
updated_at
```

### 9.2 dimension_definitions

```text
id
entity_code
dimension_code
dimension_name
field_expression
join_config JSON
data_type
is_filterable
is_groupable
allowed_values JSON
status
created_at
updated_at
```

### 9.3 measure_definitions

```text
id
measure_code
measure_name
entity_code
aggregation
expression
filter_config JSON
description
status
created_at
updated_at
```

### 9.4 metric_definitions

```text
id
metric_code
metric_name
entity_code
formula_type
formula_config JSON
time_field
format_type
description
status
version
created_by
updated_by
created_at
updated_at
deleted_at
```

### 9.5 metric_change_logs

```text
id
metric_id
change_type
before_config JSON
after_config JSON
operator_id
reason
created_at
```

### 9.6 metric_query_logs

```text
id
trace_id
session_id
query_plan JSON
compiled_sql TEXT
duration_ms
status
error_message
created_at
```

## 10. Agent 能力要求

### 10.1 指标创建 Agent

输入：

```text
自然语言指标需求
```

输出：

```text
指标定义草案
口径说明
依赖的 Entity
依赖的 Measure
支持的 Dimension
可能存在的歧义
需要开发确认的问题
```

Agent 不能直接发布指标，只能生成草案。

### 10.2 指标查询 Agent

输入：

```text
用户自然语言问题
```

输出：

```text
QueryPlan
```

然后调用统一工具：

```text
query_metric
```

## 11. 功能需求

### 11.1 语义层管理

- 支持维护 Entity。
- 支持维护 Dimension。
- 支持维护 Measure。
- 支持维护 Metric。
- 支持指标状态流转。
- 支持指标版本。
- 支持指标变更日志。

### 11.2 指标创建

- 支持开发人员通过 Agent 创建指标草案。
- 支持开发人员审核和发布指标。
- 系统应校验指标引用的实体、维度和度量是否存在。
- 系统应校验 ratio 指标分子和分母是否完整。
- 系统应校验指标编码唯一性。

### 11.3 指标查询

- 支持用户自然语言查询已发布指标。
- 支持时间范围。
- 支持组织、人员、模块、状态、优先级等过滤条件。
- 支持按维度分组。
- 返回结果必须包含指标口径。

### 11.4 审计与追踪

- 指标创建应记录 Agent 草案。
- 指标修改应记录前后配置。
- 指标查询应记录 QueryPlan。
- 指标查询应记录编译 SQL。
- 指标查询应关联 LLM Trace。

## 12. 非功能需求

### 12.1 安全

- 不允许用户直接输入 SQL。
- 不允许 LLM 直接执行 SQL。
- 字段、过滤、分组必须来自语义层白名单。
- 指标创建仅对开发人员或管理员开放。
- 指标查询应遵守组织数据权限。

### 12.2 可扩展性

- 新增指标优先新增 Metric 定义。
- 新增基础统计能力优先新增 Measure。
- 新增人员、组织、模块等切片能力优先新增 Dimension。
- 新增实体时应先建立 Entity，再建立对应 Dimension、Measure、Metric。

### 12.3 可维护性

- 指标口径必须集中维护。
- 指标定义必须版本化。
- 指标变更必须可审计。
- 不允许重复定义语义相同但编码不同的指标。

### 12.4 性能

- 常用时间字段、组织字段、状态字段应建立索引。
- 大时间范围查询应限制跨度。
- 高频指标后期可缓存或预聚合。
- 分组维度过多时应限制返回行数。

## 13. 里程碑

### 阶段一：Bug 语义层 MVP

- 建 Entity、Dimension、Measure、Metric 表。
- 内置 `bug` 实体。
- 内置 Bug 常用维度。
- 内置 `bug_count`、`closed_bug_count`。
- 内置 `bug_close_rate`。
- 支持 `query_metric` 查询 Bug 关闭率。

### 阶段二：组织维度接入

- 支持 `assignee_org_id`。
- 支持 `assignee_org_name`。
- 支持按组织过滤。
- 支持按组织分组。

### 阶段三：Agent 查询指标

- Agent 能识别用户问题中的指标。
- Agent 能生成 QueryPlan。
- Agent 能调用 `query_metric`。
- LLM Trace 能记录 QueryPlan 和最终结果。

### 阶段四：Agent 创建指标

- 开发人员通过 Agent 创建指标草案。
- Agent 输出 Entity、Measure、Metric 依赖。
- 开发人员审核后发布。

### 阶段五：指标治理

- 指标版本管理。
- 指标变更日志。
- 指标权限。
- 指标缓存。
- 指标质量检测。

## 14. 验收标准

- 系统内存在 `bug` Entity。
- 系统内存在 `bug_count` 和 `closed_bug_count` Measure。
- 系统内存在 `bug_close_rate` Metric。
- 用户可以问“本月 Bug 关闭率是多少”，系统返回正确结果。
- 用户可以问“研发一部本月 Bug 关闭率是多少”，系统能按组织过滤。
- 用户可以问“按模块看本月 Bug 关闭率”，系统能按模块分组。
- 查询结果包含指标口径说明。
- LLM Trace 中可以看到用户问题、system prompt、QueryPlan、工具结果和最终回答。
