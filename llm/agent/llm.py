import json
import time
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage
from langchain_openai import ChatOpenAI

from llm.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from llm.repositories.llm_trace_repository import LlmTraceRepository
from llm.tools.metric_meta_tools import list_available_metrics
from llm.tools.metric_query_tools import query_metric
from llm.tools.org_metric_tools import query_org_structure
from llm.tools.time_tool import get_now_date

DEVFLOW_SYSTEM_PROMPT = (
    "你是 DevFlow Agent，一个面向研发流程数据分析的 AI Agent。\n"
    "\n"
    "工具使用优先级：\n"
    "1. 用户问任何业务指标（关闭率/完成率/统计数/X率）-> 只用 query_metric\n"
    "2. 不清楚有哪些可用指标 -> 先用 list_available_metrics 查看\n"
    "3. 查组织架构/部门树 -> 用 query_org_structure\n"
    "4. 需要当前日期 -> 用 get_now_date\n"
    "\n"
    "重要：所有的指标类查询（Bug 数、关闭率、延期率等）都统一走 query_metric，\n"
    "不要尝试用其他工具替代。如果 query_metric 不支持，告知用户当前暂不支持该指标。\n"
    "\n"
    "规则：\n"
    "1. 查询数据必须使用工具，不要编造数字。\n"
    "2. 回答要简洁，先给结论再给依据。\n"
    "3. 统计口径要主动说明（如'新建 Bug = 创建时间在统计周期内'）。\n"
    "4. 你不能修改数据库，不能执行任意 SQL。\n"
)


class DevFlowAgent:
    def __init__(self) -> None:
        model = ChatOpenAI(
            model=LLM_MODEL,
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            temperature=0.2,
        )

        self.agent = create_agent(
            model=model,
            tools=[
                query_metric,
                list_available_metrics,
                get_now_date,
                query_org_structure,
            ],
            system_prompt=DEVFLOW_SYSTEM_PROMPT,
        )

        self.sessions: dict[str, list[dict[str, str]]] = {}
        self.trace_repository = LlmTraceRepository()

    def _load_history(self, session_id: str) -> list[dict[str, str]]:
        """获取会话历史。首次访问时从 DB 恢复，后续用内存。"""
        if session_id not in self.sessions:
            rows = self.trace_repository.get_recent_chat_messages(session_id, limit=20)
            self.sessions[session_id] = (
                [{"role": r["role"], "content": r["content"]} for r in rows]
                if rows
                else []
            )
        return self.sessions.get(session_id, [])

    def ask(self, session_id: str, message: str) -> str:
        trace_id = uuid4().hex
        started_at = time.perf_counter()
        history = self._load_history(session_id)

        input_messages = [
            *history,
            {"role": "user", "content": message},
        ]

        self.trace_repository.create_conversation(
            trace_id=trace_id,
            session_id=session_id,
            user_input=message,
            model_name=LLM_MODEL,
            provider="dashscope",
        )

        try:
            result = self.agent.invoke({"messages": input_messages})

            messages = result["messages"]
            self.sessions[session_id] = messages[-20:]
            reply = str(messages[-1].content)
            duration_ms = int((time.perf_counter() - started_at) * 1000)

            trace_messages = [
                {
                    "role": "system",
                    "content": DEVFLOW_SYSTEM_PROMPT,
                },
                *[self._message_to_dict(item) for item in messages],
            ]

            self.trace_repository.save_messages(
                trace_id=trace_id,
                session_id=session_id,
                messages=trace_messages,
            )

            self.trace_repository.finish_conversation(
                trace_id=trace_id,
                final_output=reply,
                duration_ms=duration_ms,
            )

            return reply
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started_at) * 1000)

            self.trace_repository.fail_conversation(
                trace_id=trace_id,
                error_message=str(exc),
                duration_ms=duration_ms,
            )

            raise

    async def astream(
        self, session_id: str, message: str
    ) -> AsyncIterator[str]:
        """异步流式对话，逐事件返回 SSE 格式字符串。"""
        trace_id = uuid4().hex
        started_at = time.perf_counter()
        history = self._load_history(session_id)

        input_messages: list[dict[str, str]] = [
            *history,
            {"role": "user", "content": message},
        ]

        self.trace_repository.create_conversation(
            trace_id=trace_id,
            session_id=session_id,
            user_input=message,
            model_name=LLM_MODEL,
            provider="dashscope",
        )

        try:
            collected_content: list[str] = []
            tool_calls_log: list[dict[str, Any]] = []
            final_reply = ""

            # 通知前端开始
            yield self._sse("thinking", {"message": "正在分析..."})

            async for event in self.agent.astream_events(
                {"messages": input_messages}, version="v2"
            ):
                kind = event["event"]

                if kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    yield self._sse(
                        "tool_start",
                        {"tool": tool_name, "message": f"正在调用 {tool_name}..."},
                    )

                elif kind == "on_tool_end":
                    tool_name = event.get("name", "")
                    output = event["data"].get("output", "")
                    output_str = (
                        str(output.content)
                        if hasattr(output, "content")
                        else str(output)
                    )
                    tool_calls_log.append({
                        "name": tool_name,
                        "result": output_str[:500],
                    })
                    yield self._sse(
                        "tool_result",
                        {"tool": tool_name, "summary": output_str[:300]},
                    )

                elif kind == "on_chat_model_stream":
                    chunk: AIMessage = event["data"]["chunk"]
                    if chunk.content:
                        collected_content.append(str(chunk.content))
                        yield self._sse(
                            "message_delta", {"content": str(chunk.content)}
                        )

            final_reply = "".join(collected_content)
            duration_ms = int((time.perf_counter() - started_at) * 1000)

            # 构建 trace messages
            trace_messages: list[dict[str, str | None]] = [
                {
                    "role": "system",
                    "content": DEVFLOW_SYSTEM_PROMPT,
                    "message_type": "chat",
                    "tool_name": None,
                },
                {
                    "role": "human",
                    "content": message,
                    "message_type": "chat",
                    "tool_name": None,
                },
            ]
            for tc in tool_calls_log:
                trace_messages.append({
                    "role": "ai",
                    "content": f"[调用工具: {tc['name']}]",
                    "message_type": "tool_call",
                    "tool_name": tc["name"],
                })
                trace_messages.append({
                    "role": "tool",
                    "content": tc["result"],
                    "message_type": "tool_result",
                    "tool_name": tc["name"],
                })
            trace_messages.append({
                "role": "ai",
                "content": final_reply,
                "message_type": "chat",
                "tool_name": None,
            })

            self.trace_repository.save_messages(
                trace_id=trace_id, session_id=session_id, messages=trace_messages
            )
            self.trace_repository.finish_conversation(
                trace_id=trace_id,
                final_output=final_reply,
                duration_ms=duration_ms,
            )

            # 更新会话记忆
            self.sessions[session_id] = (
                input_messages
                + [{"role": "assistant", "content": final_reply}]
            )[-20:]

            yield self._sse("final", {"message": "完成"})

        except Exception as exc:
            duration_ms = int((time.perf_counter() - started_at) * 1000)
            self.trace_repository.fail_conversation(
                trace_id=trace_id,
                error_message=str(exc),
                duration_ms=duration_ms,
            )
            yield self._sse("error", {"message": str(exc)})

    def _sse(self, event_type: str, data: dict[str, Any]) -> str:
        """构建单条 SSE 字符串。"""
        payload = json.dumps({"type": event_type, **data}, ensure_ascii=False)
        return f"data: {payload}\n\n"

    def _message_to_dict(
        self, message: BaseMessage | dict[str, str]
    ) -> dict[str, str | None]:
        """把 LangChain message 转成 llm_messages 行的结构。"""
        if isinstance(message, dict):
            return {
                "role": message["role"],
                "content": message.get("content", ""),
                "message_type": "chat",
                "tool_name": None,
            }

        # --- AI 消息（含 tool_calls）---
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            parts: list[str] = []
            for tc in tool_calls:
                name = tc.get("name", "")
                args = tc.get("args", {})
                parts.append(f"[调用工具: {name}]\n参数: {args}")
            return {
                "role": message.type,
                "content": "\n".join(parts),
                "message_type": "tool_call",
                "tool_name": ",".join(tc.get("name", "") for tc in tool_calls),
            }

        # --- Tool 返回消息 ---
        tool_call_id = getattr(message, "tool_call_id", None)
        if tool_call_id:
            return {
                "role": message.type,
                "content": str(message.content),
                "message_type": "tool_result",
                "tool_name": getattr(message, "name", None),
            }

        # --- 普通对话消息 ---
        return {
            "role": message.type,
            "content": str(message.content),
            "message_type": "chat",
            "tool_name": None,
        }
