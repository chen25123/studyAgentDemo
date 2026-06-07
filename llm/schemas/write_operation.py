"""Write Operation 模型 —— Agent 生成 pending_action，用户确认后执行。"""

import secrets

from pydantic import BaseModel, Field


class WriteOperation(BaseModel):
    """Agent 生成的待确认写操作。"""

    entity_type: str = Field(description="bug 或 requirement")
    entity_id: int = Field(gt=0)
    entity_no: str = Field(description="业务编号，如 BUG-2026-000001")
    from_status: str
    to_status: str
    reason: str = ""
    operator_id: int = 1
    confirmation_token: str = Field(default_factory=lambda: secrets.token_hex(16))


class WriteResult(BaseModel):
    success: bool
    entity_type: str
    entity_no: str
    from_status: str
    to_status: str
    message: str


def generate_token() -> str:
    return secrets.token_hex(16)
