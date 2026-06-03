from fastapi import HTTPException

from llm.repositories.llm_trace_repository import LlmTraceRepository
from llm.schemas.llm_trace import LlmTraceDetail, LlmTraceMessage, LlmTraceSummary


class LlmTraceService:
    """组织 LLM Trace 查询结果，供 API 层使用。"""

    def __init__(self) -> None:
        self.repository = LlmTraceRepository()

    def list_traces(self) -> list[LlmTraceSummary]:
        rows = self.repository.list_traces(limit=100)
        return [LlmTraceSummary(**row) for row in rows]

    def get_detail(self, trace_id: str) -> LlmTraceDetail:
        conversation = self.repository.get_conversation(trace_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Trace not found")

        messages = self.repository.list_messages(trace_id)

        return LlmTraceDetail(
            conversation=LlmTraceSummary(**conversation),
            messages=[LlmTraceMessage(**row) for row in messages],
        )
