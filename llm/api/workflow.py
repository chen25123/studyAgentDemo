"""Workflow API —— 写操作确认 + 执行。"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from llm.domain.workflow_state_machine import is_valid_transition
from llm.repositories.db import get_engine

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


class ConfirmRequest(BaseModel):
    entity_type: str = Field(description="bug 或 requirement")
    entity_no: str
    from_status: str
    to_status: str
    reason: str = ""
    operator_id: int = 1
    confirmation_token: str = Field(default="")


class ConfirmResponse(BaseModel):
    success: bool
    message: str
    entity_type: str
    entity_no: str
    from_status: str
    to_status: str


@router.post("/confirm", response_model=ConfirmResponse)
def confirm(req: ConfirmRequest):
    # 校验状态机
    if not is_valid_transition(req.entity_type, req.from_status, req.to_status):
        raise HTTPException(
            status_code=400,
            detail=f"非法状态流转：{req.from_status} → {req.to_status}",
        )

    engine = get_engine()
    with engine.begin() as conn:
        # 查询实体
        table = "bugs" if req.entity_type == "bug" else "requirements"
        no_col = "bug_no" if req.entity_type == "bug" else "requirement_no"

        row = conn.execute(
            text(
                f"SELECT id, status FROM {table} "
                f"WHERE {no_col} = :no AND deleted_at IS NULL FOR UPDATE"
            ),
            {"no": req.entity_no},
        ).mappings().first()

        if row is None:
            raise HTTPException(status_code=404, detail=f"{req.entity_no} 不存在")

        if row["status"] != req.from_status:
            raise HTTPException(
                status_code=409,
                detail=f"状态已变更为 {row['status']}，请刷新后重试",
            )

        entity_id = row["id"]

        # 更新主表
        conn.execute(
            text(f"UPDATE {table} SET status = :s, updated_at = NOW() WHERE id = :id"),
            {"s": req.to_status, "id": entity_id},
        )

        # 写状态日志
        conn.execute(
            text(
                "INSERT INTO workflow_status_logs "
                "(entity_type, entity_id, from_status, to_status, reason, operator_id) "
                "VALUES (:et, :eid, :fs, :ts, :reason, :oid)"
            ),
            {
                "et": req.entity_type,
                "eid": entity_id,
                "fs": req.from_status,
                "ts": req.to_status,
                "reason": req.reason,
                "oid": req.operator_id,
            },
        )

    return ConfirmResponse(
        success=True,
        message=f"{req.entity_no}：{req.from_status} → {req.to_status}",
        entity_type=req.entity_type,
        entity_no=req.entity_no,
        from_status=req.from_status,
        to_status=req.to_status,
    )
