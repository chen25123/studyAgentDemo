"""Workflow 写操作工具 —— 受控状态流转 + 确认机制。"""

from langchain_core.tools import tool
from sqlalchemy import text

from llm.domain.workflow_state_machine import get_allowed_targets
from llm.repositories.db import get_engine
from llm.schemas.write_operation import WriteOperation


@tool
def update_bug_status(
    bug_no: str,
    current_status: str,
    new_status: str,
    reason: str = "",
) -> str:
    """更新 Bug 状态。此工具**只生成操作草案**，不会直接修改数据库。

    调用后系统会返回一个确认令牌（confirmation_token），
    你需要告诉用户"操作待确认"，由用户在前端确认后才生效。

    Args:
        bug_no: Bug 编号，如 BUG-2026-000001
        current_status: 当前状态（必须先查询确认）
        new_status: 目标状态
        reason: 变更原因
    """
    # 校验状态机
    allowed = get_allowed_targets("bug", current_status)
    if new_status not in allowed:
        return (
            f"状态流转不合法：{current_status} → {new_status}。"
            f"允许的目标状态：{', '.join(allowed) if allowed else '无可变更状态'}"
        )

    # 查询 Bug 确认存在
    with get_engine().connect() as conn:
        row = conn.execute(
            text(
                "SELECT id, status FROM bugs "
                "WHERE bug_no = :no AND deleted_at IS NULL"
            ),
            {"no": bug_no},
        ).mappings().first()

    if row is None:
        return f"Bug {bug_no} 不存在或已删除"

    actual_status = row["status"]
    if actual_status != current_status:
        return (
            f"Bug {bug_no} 当前状态为 {actual_status}，"
            f"不是你提供的 {current_status}。请重新查询后操作。"
        )

    op = WriteOperation(
        entity_type="bug",
        entity_id=row["id"],
        entity_no=bug_no,
        from_status=current_status,
        to_status=new_status,
        reason=reason,
    )

    return (
        f"操作草案已生成（待用户确认）：\n"
        f"- 对象：{bug_no}\n"
        f"- 操作：{current_status} → {new_status}\n"
        f"- 原因：{reason or '（未填写）'}\n"
        f"- 确认令牌：{op.confirmation_token}\n"
        f"\n请告知用户此操作需要在前端确认。"
    )
