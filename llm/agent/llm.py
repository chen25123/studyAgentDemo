import time
from uuid import uuid4

from langchain.agents import create_agent
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from llm.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from llm.repositories.llm_trace_repository import LlmTraceRepository
from llm.tools.bug_tools import get_bug_count_by_time, get_bug_status
from llm.tools.time_tool import get_now_date

DEVFLOW_SYSTEM_PROMPT = (
    "你是 DevFlow Agent，一个面向研发流程数据分析的 AI Agent。"
    "当前阶段你只能进行普通对话，查询数据使用工具，修改数据请使用工具，如无工具可用，则说目前没有这个能力，后续改进。"
    "回答必须客观、简洁、基于事实和清晰逻辑。"
    "当用户提到统计口径时，要主动说明你的理解；"
    "例如“新建 Bug”默认表示创建时间在统计周期内的 Bug，"
    "不是当前状态为 new 的 Bug。"
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
            tools=[get_bug_count_by_time, get_bug_status, get_now_date],
            system_prompt=DEVFLOW_SYSTEM_PROMPT,
        )

        self.sessions = {}
        self.trace_repository = LlmTraceRepository()

    def ask(self, session_id: str, message: str) -> str:
        trace_id = uuid4().hex
        started_at = time.perf_counter()
        history = self.sessions.get(session_id, [])

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

    def _message_to_dict(self, message: BaseMessage | dict[str, str]) -> dict[str, str]:
        """把 LangChain message 或普通 dict 转成可以写入 llm_messages 的结构。"""

        if isinstance(message, dict):
            return {
                "role": message["role"],
                "content": message["content"],
            }

        return {
            "role": message.type,
            "content": str(message.content),
        }
