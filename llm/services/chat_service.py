from collections.abc import AsyncIterator

from llm.agent.llm import DevFlowAgent
from llm.agent.metric_graph import MetricQueryGraph
from llm.schemas.chat import ChatRequest, ChatResponse


class ChatService:
    def __init__(self) -> None:
        self.agent = DevFlowAgent()
        self.metric_graph = MetricQueryGraph()

    def chat(self, request: ChatRequest) -> ChatResponse:
        reply = self.agent.ask(
            session_id=request.session_id,
            message=request.message,
        )
        return ChatResponse(
            session_id=request.session_id,
            reply=reply,
        )

    async def stream(self, request: ChatRequest) -> AsyncIterator[str]:
        """流式对话 —— 优先生效 MetricQueryGraph，fallback 到原 Agent。"""
        async for event in self.metric_graph.astream(
            session_id=request.session_id,
            message=request.message,
        ):
            yield event
