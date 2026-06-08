# 改动前影响评估清单

> 每一个改动在执行前，必须检查以下项。避免「改好 A，改坏 B」。

---

## 改动前自检

### 1. 替换/重写某个方法时

```
- [ ] 旧方法做了哪些事？（不只读函数名，读完整实现）
- [ ] 旧方法的调用方是谁？（rg 搜索所有调用点）
- [ ] 新方法是否覆盖了旧方法的所有副作用？
  - [ ] 数据库写入（trace / log / audit）
  - [ ] 内存状态更新（session / cache）
  - [ ] 异常处理和错误码
  - [ ] 日志/Trace 记录
```

### 2. 修改 Agent 链路时

```
- [ ] chat_service 的 stream() 和 chat() 是否仍正常工作？
- [ ] 会话记忆是否仍持久化？（重启后上下文不丢）
- [ ] LLM Trace 是否仍记录？（llm_conversations + llm_messages）
- [ ] Metric Query Log 是否仍写入？
- [ ] 工具调用后的 Trace 是否包含 tool_call / tool_result？
```

### 3. 修改前端时

```
- [ ] npm run build 是否通过？
- [ ] 路由守卫是否仍生效？
- [ ] 登录/退出流程是否正常？
- [ ] SSE 流式事件是否仍被正确处理？
- [ ] 图表渲染是否正常？
```

### 4. 新增工具/Graph 节点时

```
- [ ] 工具是否通过 @tool 注册？
- [ ] Agent tools 列表是否更新？
- [ ] system prompt 是否需要更新？
- [ ] 新意图是否加入 _classify_intent？
- [ ] 意图路由是否在 graph builder 和 astream 两处都加了？
```

---

## 改动后验证

```bash
# 最小验证（每次改完必跑）
ruff check . && pytest -m "not llm" -q && npm --prefix agent-ui run build

# Agent 链路验证（改了 Agent/Graph/Chat 时必跑）
python -c "
from llm.services.chat_service import ChatService
from llm.schemas.chat import ChatRequest
# 1. 非流式
svc = ChatService()
r = svc.chat(ChatRequest(message='你好', session_id='test-check'))
print('Chat OK:', r.reply[:50])
# 2. 验证 Trace 写入
from llm.repositories.db import get_engine
from sqlalchemy import text
with get_engine().connect() as c:
    cnt = c.execute(text(\"SELECT COUNT(*) FROM llm_conversations WHERE session_id='test-check'\")).scalar()
    print(f'Trace rows: {cnt}')
"
```

---

## 改动规范

- **不替换，先并行**：新增 graph 时，先让新旧 agent 共存。stream 里同时尝试新 graph，失败 fallback 旧 agent。验证新 graph 稳定后，再移除旧的。
- **一个 PR 只做一件事**：工具扩展不改 graph，graph 改动不改工具，前端改动不碰后端。
- **改完立即验证**：不在同一轮改动中堆叠多个未验证的变更。
