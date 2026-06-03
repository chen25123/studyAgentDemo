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
