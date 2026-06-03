from pydantic import BaseModel


class LlmTraceSummary(BaseModel):
    id: int
    trace_id: str
    session_id: str
    user_input: str
    final_output: str | None
    model_name: str
    provider: str | None
    status: str
    duration_ms: int | None
    total_tokens: int | None
    created_at: str


class LlmTraceMessage(BaseModel):
    id: int
    trace_id: str
    session_id: str
    message_order: int
    role: str
    content: str
    message_type: str
    tool_name: str | None
    created_at: str


class LlmTraceDetail(BaseModel):
    conversation: LlmTraceSummary
    messages: list[LlmTraceMessage]
