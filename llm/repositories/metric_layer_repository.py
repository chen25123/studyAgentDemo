from typing import Any

from sqlalchemy import text

from llm.repositories.db import get_engine


class MetricLayerRepository:
    """语义层元数据访问 —— 从数据库表读取实体/维度/度量/指标定义。"""

    # ----- Entity -----

    def get_entity(self, entity_code: str) -> dict[str, Any] | None:
        sql = text(
            """
            SELECT id, entity_code, entity_name, base_table, primary_key,
                   default_time_field, default_filter, description, status
            FROM entity_definitions
            WHERE entity_code = :code AND status = 'active'
            """
        )
        with get_engine().connect() as conn:
            row = conn.execute(sql, {"code": entity_code}).mappings().first()
            return dict(row) if row is not None else None

    # ----- Dimension -----

    def get_dimensions(
        self, entity_code: str, dimension_codes: list[str] | None = None
    ) -> list[dict[str, Any]]:
        if dimension_codes is not None:
            if not dimension_codes:
                return []
            sql = text(
                """
                SELECT entity_code, dimension_code, dimension_name,
                       field_expression, join_config, data_type,
                       is_filterable, is_groupable, allowed_values
                FROM dimension_definitions
                WHERE entity_code = :code
                  AND dimension_code IN :dims
                  AND status = 'active'
                """
            )
            params = {"code": entity_code, "dims": tuple(dimension_codes)}
        else:
            sql = text(
                """
                SELECT entity_code, dimension_code, dimension_name,
                       field_expression, join_config, data_type,
                       is_filterable, is_groupable, allowed_values
                FROM dimension_definitions
                WHERE entity_code = :code AND status = 'active'
                """
            )
            params = {"code": entity_code}

        with get_engine().connect() as conn:
            rows = conn.execute(sql, params).mappings().all()
            return [dict(row) for row in rows]

    def get_filterable_dimension_codes(self, entity_code: str) -> list[str]:
        sql = text(
            """
            SELECT dimension_code
            FROM dimension_definitions
            WHERE entity_code = :code AND is_filterable = 1 AND status = 'active'
            """
        )
        with get_engine().connect() as conn:
            rows = conn.execute(sql, {"code": entity_code}).mappings().all()
            return [row["dimension_code"] for row in rows]

    def get_groupable_dimension_codes(self, entity_code: str) -> list[str]:
        sql = text(
            """
            SELECT dimension_code
            FROM dimension_definitions
            WHERE entity_code = :code AND is_groupable = 1 AND status = 'active'
            """
        )
        with get_engine().connect() as conn:
            rows = conn.execute(sql, {"code": entity_code}).mappings().all()
            return [row["dimension_code"] for row in rows]

    # ----- Measure -----

    def get_measure(self, measure_code: str) -> dict[str, Any] | None:
        sql = text(
            """
            SELECT measure_code, measure_name, entity_code,
                   aggregation, expression, filter_config, description
            FROM measure_definitions
            WHERE measure_code = :code AND status = 'active'
            """
        )
        with get_engine().connect() as conn:
            row = conn.execute(sql, {"code": measure_code}).mappings().first()
            return dict(row) if row is not None else None

    def get_measures(self, measure_codes: list[str]) -> dict[str, dict[str, Any]]:
        sql = text(
            """
            SELECT measure_code, measure_name, entity_code,
                   aggregation, expression, filter_config, description
            FROM measure_definitions
            WHERE measure_code IN :codes AND status = 'active'
            """
        )
        with get_engine().connect() as conn:
            rows = conn.execute(
                sql, {"codes": tuple(measure_codes)}
            ).mappings().all()
            return {row["measure_code"]: dict(row) for row in rows}

    # ----- Metric -----

    def get_active_metric(self, metric_code: str) -> dict[str, Any] | None:
        sql = text(
            """
            SELECT metric_code, metric_name, entity_code,
                   formula_type, formula_config, time_field,
                   format_type, description, version
            FROM metric_definitions
            WHERE metric_code = :code AND status = 'active' AND deleted_at IS NULL
            """
        )
        with get_engine().connect() as conn:
            row = conn.execute(sql, {"code": metric_code}).mappings().first()
            return dict(row) if row is not None else None

    def get_active_metrics(
        self, metric_codes: list[str]
    ) -> dict[str, dict[str, Any]]:
        if not metric_codes:
            return {}
        sql = text(
            """
            SELECT metric_code, metric_name, entity_code,
                   formula_type, formula_config, time_field,
                   format_type, description, version
            FROM metric_definitions
            WHERE metric_code IN :codes AND status = 'active' AND deleted_at IS NULL
            """
        )
        with get_engine().connect() as conn:
            rows = conn.execute(
                sql, {"codes": tuple(metric_codes)}
            ).mappings().all()
            return {row["metric_code"]: dict(row) for row in rows}

    def list_active_metrics(self) -> list[dict[str, Any]]:
        sql = text(
            """
            SELECT metric_code, metric_name, entity_code,
                   formula_type, format_type, description
            FROM metric_definitions
            WHERE status = 'active' AND deleted_at IS NULL
            ORDER BY entity_code, metric_code
            """
        )
        with get_engine().connect() as conn:
            rows = conn.execute(sql).mappings().all()
            return [dict(row) for row in rows]

    # ----- Query Log -----

    def save_query_log(
        self,
        trace_id: str,
        session_id: str,
        query_plan: dict[str, Any],
        compiled_sql: str,
        duration_ms: int,
        status: str = "success",
        error_message: str | None = None,
    ) -> None:
        import json

        sql = text(
            """
            INSERT INTO metric_query_logs (
                trace_id, session_id, query_plan, compiled_sql,
                duration_ms, status, error_message
            )
            VALUES (
                :trace_id, :session_id, :query_plan, :compiled_sql,
                :duration_ms, :status, :error_message
            )
            """
        )
        with get_engine().begin() as conn:
            conn.execute(
                sql,
                {
                    "trace_id": trace_id,
                    "session_id": session_id,
                    "query_plan": json.dumps(query_plan, ensure_ascii=False, default=str),
                    "compiled_sql": compiled_sql,
                    "duration_ms": duration_ms,
                    "status": status,
                    "error_message": error_message,
                },
            )
