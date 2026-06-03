from fastapi import APIRouter, HTTPException

from llm.schemas.chat import ChatRequest, ChatResponse
from llm.services.chat_service import ChatService

router = APIRouter(prefix="/api", tags=["chat"])

chat_service = ChatService()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        return chat_service.chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
