# Agent Eval 评测报告

> 日期：2026-06-07
> 模型：qwen-plus (DashScope)

---

## 1. 意图分类

| 指标 | 数值 |
|---|---|
| 总题数 | 20 |
| 正确 | 20 |
| 准确率 | **100%** |

结论：LLM 能可靠区分 `metric_query`（数据查询）和 `general_chat`（闲聊）。

---

## 2. 指标匹配

| 指标 | 数值 |
|---|---|
| 总题数 | 15 (有明确预期指标的题) |
| 正确 | 12 |
| 准确率 | **80%** |

### 错误分析

| 题号 | 用户问题 | 实际匹配 | 预期匹配 | 原因 |
|---|---|---|---|---|
| Q14 | 交易模块的 Bug 严重吗？ | (空) | bug_count | LLM 理解为"严重程度"查询，非"数量" |
| Q15 | 最近一周关闭了多少个 Bug？ | bug_count | bug_close_rate | "关闭了多少个"被理解为 count 而非 rate |
| Q18 | 上个季度的需求完成率怎么样？ | (空) | requirement_delay_rate | "完成率"≠"延期率"，语义相反 |

结论：
- 12/15 正确匹配，高于 60% 阈值
- 3 个错误均为语义歧义，非代码 bug
- 建议补充 `bug_close_count` 指标（关闭的绝对数量）和 `requirement_completion_rate`（完成率）

---

## 3. 端到端能力

| 能力 | 状态 |
|---|---|
| Chat API | ✅ |
| Chat SSE 流式 | ✅ |
| Dashboard API | ✅ |
| Metric Catalog API | ✅ |
| Metric Value API | ✅ |
| Admin Trace API（鉴权） | ✅ |

---

## 4. 建议

1. 新增 `bug_close_count` 指标（count 类型），应对"关闭了多少个"类问题
2. 新增 `requirement_completion_rate` 指标（ratio 类型），应对"完成率"类问题
3. 后续每季度跑一次 Eval，监控准确率变化
