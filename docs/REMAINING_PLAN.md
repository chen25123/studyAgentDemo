# DevFlow Agent 剩余工作迭代计划

> 生成日期：2026-06-07
> 当前完成度：约 60%
> 剩余迭代：6 个

---

## 迭代总览

| 迭代 | 内容 | 预计工作量 | 完成后累计 |
|---|---|---|---|
| I-1 | Agent Eval + 质量加固 | 中 | 65% |
| I-2 | 用户登录系统 | 中 | 70% |
| I-3 | 报告生成 | 大 | 78% |
| I-4 | 前端管理后台 | 中 | 85% |
| I-5 | 受控写操作 | 大 | 93% |
| I-6 | 部署与 CI/CD | 中 | 100% |

---

## I-1：Agent Eval + 质量加固

**目标**：量化 Agent 准确率，补测试缺口

### 任务

| # | 任务 | 验证方式 |
|---|---|---|
| 1 | 跑 `pytest -m llm` 测试意图分类准确率 | 输出「20 题中 X 题意图正确」 |
| 2 | 跑 `test_metric_matching` 测试指标匹配准确率 | 输出「X/6 指标匹配正确」 |
| 3 | 补充 `test_agent_eval.py` 增加端到端问题（含图表生成） | 3+ 条端到端 case |
| 4 | 补 SSE 流式 API 集成测试 | `test_api.py` 增加 SSE 事件解析测试 |
| 5 | 补 Trace API 鉴权通过/拒绝测试 | Admin 鉴权全覆盖 |
| 6 | 输出 Eval 报告 → `docs/eval_report.md` | 文档存在且数据完整 |

### 质量门禁

```bash
ruff check . && pytest -m "not llm" -q && npm --prefix agent-ui run build
```

---

## I-2：用户登录系统

**目标**：从 X-Admin-Token 升级到 JWT + RBAC

### 任务

| # | 任务 | 验证方式 |
|---|---|---|
| 1 | `.env` 新增 `JWT_SECRET` | config 读取成功 |
| 2 | `api/auth.py` — `POST /api/auth/login` 返回 JWT | curl 拿到 token |
| 3 | `api/auth.py` — `GET /api/auth/me` 返回当前用户 | token 解析正确 |
| 4 | `middleware.py` AdminAuth → JWT 鉴权中间件 | 无 token → 401 |
| 5 | `users` 表新增 `password_hash` 字段 + 种子密码 | 登录查询 users 表 |
| 6 | 前端 `LoginView.vue` + 路由守卫 | 未登录重定向到 /login |
| 7 | 前端 `http.ts` 拦截器自动带 `Authorization: Bearer` | 请求头含 token |

### 角色定义

| 角色 | 权限 |
|---|---|
| admin | chat + admin/* + catalog |
| developer | chat + catalog |
| viewer | chat |

### 质量门禁

```bash
ruff check . && pytest -m "not llm" -q && npm --prefix agent-ui run build
```

---

## I-3：报告生成（阶段四）

**目标**：Agent 能自动生成研发质量周报/月报

### 任务

| # | 任务 | 验证方式 |
|---|---|---|
| 1 | `services/report_service.py` — 报告模板引擎 | 调用 `generate_weekly_report()` 返回结构化报告 |
| 2 | `schemas/report.py` — WeeklyReport / MonthlyReport 模型 | Pydantic 校验通过 |
| 3 | `domain/report_templates.py` — 周报/月报模板定义 | 模板含：指标总览、风险项、趋势对比、建议 |
| 4 | `agent/report_graph.py` — LangGraph 报告生成工作流 | 跟 MetricQueryGraph 同模式 |
| 5 | `api/report.py` — `POST /api/reports/generate` | 返回报告 JSON + 图表 base64 |
| 6 | 前端 ChatView 增加报告卡片：文字 + 多图表 | 对话输出报告格式 |
| 7 | 前端报告页面 `/reports` — 报告历史列表 | 页面数据从 API 加载 |

### 报告模板示例

```
# 研发质量周报（2026-W23）

## 指标总览
- Bug 关闭率：14.29%（↑ 2.1%）
- 重开率：14.52%（↓ 0.8%）
- 需求延期率：22.94%

## 风险项
- 延期需求偏高，建议关注

## 图表
[模块关闭率柱状图]
[趋势折线图]
```

### 质量门禁

```bash
ruff check . && pytest -m "not llm" -q && npm --prefix agent-ui run build
```

---

## I-4：前端管理后台

**目标**：完整的 Admin Console

### 任务

| # | 任务 | 验证方式 |
|---|---|---|
| 1 | `/admin/metrics` — 指标管理页（列表 + 搜索 + 状态筛选） | 页面可访问 |
| 2 | `/admin/metrics/:code` — 指标详情页（编辑口径/公式/状态） | 详情正确展示 |
| 3 | `/admin/entities` — 实体管理页 | 列表 + 维度列表 |
| 4 | 指标状态流转 UI：draft → review → active → deprecated | 按钮操作 + 确认 |
| 5 | 指标变更日志展示 | metric_change_logs 表数据渲染 |
| 6 | 前端路由守卫：admin 路由需登录 + admin 角色 | 未授权 → 403 |

### 质量门禁

```bash
npm --prefix agent-ui run build
```

---

## I-5：受控写操作（阶段五）

**目标**：Agent 在确认后能修改 Bug/需求状态

### 任务

| # | 任务 | 验证方式 |
|---|---|---|
| 1 | `domain/workflow_state_machine.py` — Bug/需求状态机白名单 | 合法流转通过，非法被拒 |
| 2 | `schemas/write_operation.py` — WriteOperation / ConfirmationToken | Pydantic 校验 |
| 3 | `tools/workflow_tools.py` — `update_bug_status` / `assign_bug_owner` | 工具定义 + 确认流程 |
| 4 | `agent/workflow_graph.py` — LangGraph 写操作工作流 | write_intent → confirm → execute → log |
| 5 | `api/workflow.py` — `POST /api/workflow/confirm` | 带 confirmation_token 的确认接口 |
| 6 | `repositories/workflow_log_repository.py` — 状态日志写入 | workflow_status_logs 有记录 |
| 7 | 事务保护：主表更新 + 日志写入同时成功/回滚 | 模拟失败验证回滚 |
| 8 | 前端 ChatView：写操作确认弹窗 | "确认将 BUG-001 状态改为 closed？" |
| 9 | 前端写操作结果展示 | 成功/失败 + 新状态 + 日志 |

### 状态机（Bug）

```
new → processing → fixed → closed
                   → suspended → processing
fixed → reopened
closed → reopened
```

### 质量门禁

```bash
ruff check . && pytest tests/test_workflow.py -v
```

---

## I-6：部署与 CI/CD

**目标**：一键部署 + 自动化质量门禁

### 任务

| # | 任务 | 验证方式 |
|---|---|---|
| 1 | `docker-compose.yml` 完善：MySQL + Backend + Frontend 一键启动 | `docker compose up` 成功 |
| 2 | `.github/workflows/ci.yml` — GitHub Actions | push 自动跑 ruff + pytest + build |
| 3 | Alembic migration 完整性检查（CI 步骤） | 新 migration 不破坏现有 schema |
| 4 | 前端 Nginx 配置完善（gzip + 缓存 + SPA fallback） | 刷新不 404 |
| 5 | 健康检查端点增强：`/health` 返回 DB 连接状态 | `{"status":"ok","db":"connected"}` |
| 6 | `scripts/seed.sh` — 一键初始化数据库 | 新环境 5 分钟可跑 |

### 质量门禁

```bash
docker compose up -d && curl http://localhost:8080/health
```

---

## 验收标准（最终）

- [ ] `ruff check .` 零问题
- [ ] `pytest -m "not llm"` 30+ passed
- [ ] `pytest -m "llm"` Agent Eval > 80% 准确率
- [ ] `npm --prefix agent-ui run build` 通过
- [ ] 用户可以自然语言查询 Bug/需求指标，获得文字 + 图表
- [ ] 用户可以请求生成周报，获得结构化报告
- [ ] 管理员可以在确认后修改 Bug 状态，操作为事务保护
- [ ] 管理员可以通过管理后台维护指标定义
- [ ] `docker compose up` 一键启动全部服务
- [ ] JWT 保护 /api/admin/* 路由
