from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

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


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE 流式对话端点。"""
    try:
        return StreamingResponse(
            chat_service.stream(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
