from typing import Any

from sqlalchemy import text

from llm.repositories.db import get_engine


class LlmTraceRepository:
    """Repository for LLM trace persistence and lookup."""

    def create_conversation(
        self,
        trace_id: str,
        session_id: str,
        user_input: str,
        model_name: str,
        provider: str | None,
    ) -> None:
        sql = text(
            """
            INSERT INTO llm_conversations (
                trace_id,
                session_id,
                user_input,
                model_name,
                provider,
                status
            )
            VALUES (
                :trace_id,
                :session_id,
                :user_input,
                :model_name,
                :provider,
                'running'
            )
            """
        )

        with get_engine().begin() as conn:
            conn.execute(
                sql,
                {
                    "trace_id": trace_id,
                    "session_id": session_id,
                    "user_input": user_input,
                    "model_name": model_name,
                    "provider": provider,
                },
            )

    def save_messages(
        self,
        trace_id: str,
        session_id: str,
        messages: list[dict[str, str | None]],
    ) -> None:
        if not messages:
            return

        sql = text(
            """
            INSERT INTO llm_messages (
                trace_id,
                session_id,
                message_order,
                role,
                content,
                message_type,
                tool_name
            )
            VALUES (
                :trace_id,
                :session_id,
                :message_order,
                :role,
                :content,
                :message_type,
                :tool_name
            )
            """
        )

        rows = [
            {
                "trace_id": trace_id,
                "session_id": session_id,
                "message_order": index + 1,
                "role": message["role"],
                "content": message["content"],
                "message_type": message.get("message_type", "chat"),
                "tool_name": message.get("tool_name"),
            }
            for index, message in enumerate(messages)
        ]

        with get_engine().begin() as conn:
            conn.execute(sql, rows)

    def finish_conversation(
        self,
        trace_id: str,
        final_output: str,
        duration_ms: int,
        total_tokens: int | None = None,
    ) -> None:
        sql = text(
            """
            UPDATE llm_conversations
            SET
                final_output = :final_output,
                status = 'success',
                duration_ms = :duration_ms,
                total_tokens = :total_tokens
            WHERE trace_id = :trace_id
            """
        )

        with get_engine().begin() as conn:
            conn.execute(
                sql,
                {
                    "final_output": final_output,
                    "duration_ms": duration_ms,
                    "total_tokens": total_tokens,
                    "trace_id": trace_id,
                },
            )

    def fail_conversation(
        self,
        trace_id: str,
        error_message: str,
        duration_ms: int,
    ) -> None:
        sql = text(
            """
            UPDATE llm_conversations
            SET
                status = 'failed',
                error_message = :error_message,
                duration_ms = :duration_ms
            WHERE trace_id = :trace_id
            """
        )

        with get_engine().begin() as conn:
            conn.execute(
                sql,
                {
                    "error_message": error_message,
                    "duration_ms": duration_ms,
                    "trace_id": trace_id,
                },
            )

    def list_traces(self, limit: int = 100) -> list[dict[str, Any]]:
        sql = text(
            """
            SELECT
                id,
                trace_id,
                session_id,
                user_input,
                final_output,
                model_name,
                provider,
                status,
                duration_ms,
                total_tokens,
                DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') AS created_at
            FROM llm_conversations
            ORDER BY id DESC
            LIMIT :limit
            """
        )

        with get_engine().connect() as conn:
            rows = conn.execute(sql, {"limit": limit}).mappings().all()
            return [dict(row) for row in rows]

    def get_conversation(self, trace_id: str) -> dict[str, Any] | None:
        sql = text(
            """
            SELECT
                id,
                trace_id,
                session_id,
                user_input,
                final_output,
                model_name,
                provider,
                status,
                duration_ms,
                total_tokens,
                DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') AS created_at
            FROM llm_conversations
            WHERE trace_id = :trace_id
            """
        )

        with get_engine().connect() as conn:
            row = conn.execute(sql, {"trace_id": trace_id}).mappings().first()
            return dict(row) if row is not None else None

    def list_messages(self, trace_id: str) -> list[dict[str, Any]]:
        sql = text(
            """
            SELECT
                id,
                trace_id,
                session_id,
                message_order,
                role,
                content,
                message_type,
                tool_name,
                DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') AS created_at
            FROM llm_messages
            WHERE trace_id = :trace_id
            ORDER BY message_order ASC
            """
        )

        with get_engine().connect() as conn:
            rows = conn.execute(sql, {"trace_id": trace_id}).mappings().all()
            return [dict(row) for row in rows]

    def get_recent_chat_messages(
        self, session_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """读取某 session 最近的 chat 类型消息，用于恢复会话上下文。

        只取 role 为 human/ai 的 message_type='chat' 记录，
        按 message_order 倒序取最近 N 条，再反转回正序。
        """
        sql = text(
            """
            SELECT role, content
            FROM llm_messages
            WHERE session_id = :session_id
              AND message_type = 'chat'
              AND role IN ('human', 'ai')
            ORDER BY id DESC
            LIMIT :limit
            """
        )
        with get_engine().connect() as conn:
            rows = conn.execute(
                sql, {"session_id": session_id, "limit": limit}
            ).mappings().all()
            # MySQL 返回的是倒序，反转回正序
            result = [dict(row) for row in rows]
            result.reverse()
            return result
