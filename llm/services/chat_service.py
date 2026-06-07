from collections.abc import AsyncIterator

from llm.agent.llm import DevFlowAgent
from llm.schemas.chat import ChatRequest, ChatResponse


class ChatService:
    def __init__(self) -> None:
        self.agent = DevFlowAgent()

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
        """流式对话，返回 SSE 事件字符串生成器。"""
        async for event in self.agent.astream(
            session_id=request.session_id,
            message=request.message,
        ):
            yield event
