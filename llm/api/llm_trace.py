from fastapi import APIRouter

from llm.schemas.llm_trace import LlmTraceDetail, LlmTraceSummary
from llm.services.llm_trace_service import LlmTraceService

router = APIRouter(prefix="/api/admin", tags=["llm-traces"])

trace_service = LlmTraceService()


@router.get("/llm-traces", response_model=list[LlmTraceSummary])
def list_llm_traces() -> list[LlmTraceSummary]:
    """查询最近 100 条 LLM 调用记录。"""
    return trace_service.list_traces()


@router.get("/llm-traces/{trace_id}", response_model=LlmTraceDetail)
def get_llm_trace_detail(trace_id: str) -> LlmTraceDetail:
    """查询某一次 LLM 调用的完整 messages。"""
    return trace_service.get_detail(trace_id)
