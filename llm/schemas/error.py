"""统一错误响应模型。"""

from enum import StrEnum

from pydantic import BaseModel, Field


class ErrorCode(StrEnum):
    LLM_CALL_FAILED = "LLM_CALL_FAILED"
    TOOL_CALL_FAILED = "TOOL_CALL_FAILED"
    INVALID_QUERY_PLAN = "INVALID_QUERY_PLAN"
    METRIC_NOT_FOUND = "METRIC_NOT_FOUND"
    DB_QUERY_FAILED = "DB_QUERY_FAILED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    TRACE_NOT_FOUND = "TRACE_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorResponse(BaseModel):
    error_code: ErrorCode = Field(description="机器可读错误码")
    message: str = Field(description="人类可读错误描述")
    trace_id: str = Field(default="", description="关联的 LLM Trace ID")
    retryable: bool = Field(default=False, description="是否可重试")
