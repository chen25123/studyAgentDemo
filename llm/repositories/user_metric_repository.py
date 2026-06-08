from typing import Any

from sqlalchemy import text

from llm.domain.user_metrics import (
    SUPPORTED_USER_FILTERS,
    SUPPORTED_USER_GROUP_BY,
    SUPPORTED_USER_METRICS,
)
from llm.repositories.db import get_engine
from llm.schemas.user_metric import UserMetricQuery, UserMetricRow


class UserMetricRepository:
    """执行用户/组织架构指标查询。"""

    def query_metrics(self, query: UserMetricQuery) -> list[UserMetricRow]:
        self._validate_query(query)

        # 列表模式：返回人员明细
        if query.list_mode:
            return self._query_member_list(query)

        select_parts: list[str] = []
        group_by_parts: list[str] = []
        join_parts: set[str] = set()

        for dimension in query.group_by:
            dim_def = SUPPORTED_USER_GROUP_BY[dimension]
            select_parts.append(f"{dim_def['sql_column']} AS {dimension}")
            group_by_parts.append(dim_def["sql_column"])
            join_parts.update(dim_def.get("requires_join", []))

        for metric in query.metrics:
            metric_def = SUPPORTED_USER_METRICS[metric]
            select_parts.append(f"{metric_def['sql']} AS {metric}")

        where_parts = ["users.deleted_at IS NULL"]
        params: dict[str, Any] = {}

        if query.time_range is not None:
            where_parts.append("users.created_at >= :start_date")
            where_parts.append("users.created_at < DATE_ADD(:end_date, INTERVAL 1 DAY)")
            params["start_date"] = query.time_range.start_date.isoformat()
            params["end_date"] = query.time_range.end_date.isoformat()

        for index, (filter_name, filter_value) in enumerate(query.filters.items()):
            filter_def = SUPPORTED_USER_FILTERS[filter_name]
            column = filter_def["sql_column"]
            param_name = f"filter_{index}"
            join_parts.update(filter_def.get("requires_join", []))

            if filter_def.get("operator") == "like":
                where_parts.append(f"{column} LIKE :{param_name}")
                params[param_name] = f"%{filter_value}%"
            elif isinstance(filter_value, list):
                if not filter_value:
                    continue
                bind_names = []
                for value_index, value in enumerate(filter_value):
                    item_param_name = f"{param_name}_{value_index}"
                    bind_names.append(f":{item_param_name}")
                    params[item_param_name] = value
                where_parts.append(f"{column} IN ({', '.join(bind_names)})")
            else:
                where_parts.append(f"{column} = :{param_name}")
                params[param_name] = filter_value

        sql = self._build_sql(
            select_parts=select_parts,
            where_parts=where_parts,
            group_by_parts=group_by_parts,
            join_parts=join_parts,
        )

        with get_engine().connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()

        return [
            self._row_to_metric_row(
                row=dict(row), group_by=query.group_by, metrics=query.metrics
            )
            for row in rows
        ]

    def _validate_query(self, query: UserMetricQuery) -> None:
        if not query.metrics:
            raise ValueError("至少需要一个 metrics")

        unknown_metrics = set(query.metrics) - set(SUPPORTED_USER_METRICS)
        if unknown_metrics:
            raise ValueError(f"不支持的用户指标：{sorted(unknown_metrics)}")

        unknown_filters = set(query.filters) - set(SUPPORTED_USER_FILTERS)
        if unknown_filters:
            raise ValueError(f"不支持的用户过滤条件：{sorted(unknown_filters)}")

        unknown_group_by = set(query.group_by) - set(SUPPORTED_USER_GROUP_BY)
        if unknown_group_by:
            raise ValueError(f"不支持的用户分组维度：{sorted(unknown_group_by)}")

    def _build_sql(
        self,
        select_parts: list[str],
        where_parts: list[str],
        group_by_parts: list[str],
        join_parts: set[str],
    ) -> str:
        from_clause = "FROM users"

        if "membership" in join_parts:
            from_clause += (
                "\nJOIN user_org_memberships "
                "ON users.id = user_org_memberships.user_id"
                "\n  AND user_org_memberships.ended_at IS NULL"
            )
        if "org" in join_parts:
            from_clause += (
                "\nJOIN org_units "
                "ON user_org_memberships.org_unit_id = org_units.id"
                "\n  AND org_units.deleted_at IS NULL"
            )

        sql = [
            "SELECT",
            ", ".join(select_parts),
            from_clause,
            "WHERE",
            " AND ".join(where_parts),
        ]

        if group_by_parts:
            sql.extend(["GROUP BY", ", ".join(group_by_parts)])

        return "\n".join(sql)

    def _query_member_list(self, query: UserMetricQuery) -> list[UserMetricRow]:
        """列表模式：返回人员明细而非聚合统计。"""
        join_parts: set[str] = {"membership", "org"}  # 列表模式总是 JOIN 组织表
        select_parts = [
            "users.display_name AS display_name",
            "users.job_title AS job_title",
            "users.department AS department",
            "users.role_code AS role_code",
            "user_org_memberships.position_title AS position_title",
            "org_units.org_name AS org_name",
        ]

        where_parts = ["users.deleted_at IS NULL"]
        params: dict[str, Any] = {}

        for index, (filter_name, filter_value) in enumerate(query.filters.items()):
            filter_def = SUPPORTED_USER_FILTERS[filter_name]
            column = filter_def["sql_column"]
            param_name = f"filter_{index}"
            join_parts.update(filter_def.get("requires_join", []))

            if filter_def.get("operator") == "like":
                where_parts.append(f"{column} LIKE :{param_name}")
                params[param_name] = f"%{filter_value}%"
            elif isinstance(filter_value, list):
                if not filter_value:
                    continue
                bind_names = []
                for vi, v in enumerate(filter_value):
                    bind_names.append(f":{param_name}_{vi}")
                    params[f"{param_name}_{vi}"] = v
                where_parts.append(f"{column} IN ({', '.join(bind_names)})")
            else:
                where_parts.append(f"{column} = :{param_name}")
                params[param_name] = filter_value

        from_clause = "FROM users"
        if "membership" in join_parts:
            from_clause += (
                "\nJOIN user_org_memberships "
                "ON users.id = user_org_memberships.user_id"
                "\n  AND user_org_memberships.ended_at IS NULL"
            )
        if "org" in join_parts:
            from_clause += (
                "\nJOIN org_units "
                "ON user_org_memberships.org_unit_id = org_units.id"
                "\n  AND org_units.deleted_at IS NULL"
            )

        sql = (
            f"SELECT {', '.join(select_parts)}\n"
            f"{from_clause}\n"
            f"WHERE {' AND '.join(where_parts)}\n"
            "ORDER BY org_units.org_name, users.display_name\n"
            "LIMIT 200"
        )

        with get_engine().connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()

        return [
            UserMetricRow(
                dimensions=dict(row),
                metrics={"user_count": 1},
            )
            for row in rows
        ]

    def _row_to_metric_row(
        self,
        row: dict[str, Any],
        group_by: list[str],
        metrics: list[str],
    ) -> UserMetricRow:
        dimensions = {dimension: row.get(dimension) for dimension in group_by}
        metric_values = {metric: row.get(metric) for metric in metrics}

        return UserMetricRow(dimensions=dimensions, metrics=metric_values)
