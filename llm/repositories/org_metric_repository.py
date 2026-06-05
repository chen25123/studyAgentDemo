from typing import Any

from sqlalchemy import text

from llm.domain.org_metrics import (
    SUPPORTED_ORG_FILTERS,
    SUPPORTED_ORG_GROUP_BY,
    SUPPORTED_ORG_METRICS,
)
from llm.repositories.db import get_engine
from llm.schemas.org_metric import OrgMetricQuery, OrgMetricRow


class OrgMetricRepository:
    """执行组织架构查询。"""

    def query_metrics(self, query: OrgMetricQuery) -> list[OrgMetricRow]:
        self._validate_query(query)

        select_parts: list[str] = []
        group_by_parts: list[str] = []

        for dimension in query.group_by:
            column = SUPPORTED_ORG_GROUP_BY[dimension]
            select_parts.append(f"{column} AS {dimension}")
            group_by_parts.append(column)

        for metric in query.metrics:
            metric_def = SUPPORTED_ORG_METRICS[metric]
            select_parts.append(f"{metric_def['sql']} AS {metric}")

        # 列表模式额外返回 org_code / org_name / level
        if query.list_mode:
            select_parts.insert(0, "org_units.org_name AS org_name")
            select_parts.insert(0, "org_units.org_code AS org_code")
            select_parts.insert(0, "org_units.id AS org_id")
            select_parts.insert(0, "org_units.level AS level")
            select_parts.insert(0, "org_units.parent_id AS parent_id")
            select_parts.insert(0, "org_units.path AS path")
            if not query.group_by:
                group_by_parts = [
                    "org_units.id",
                    "org_units.parent_id",
                    "org_units.path",
                    "org_units.level",
                    "org_units.org_code",
                    "org_units.org_name",
                ]

        where_parts = ["org_units.deleted_at IS NULL"]
        params: dict[str, Any] = {}

        for index, (filter_name, filter_value) in enumerate(query.filters.items()):
            filter_def = SUPPORTED_ORG_FILTERS[filter_name]
            column = filter_def["sql_column"]
            param_name = f"filter_{index}"

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
        )

        with get_engine().connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()

        dimension_keys = list(query.group_by)
        if query.list_mode:
            dimension_keys = [
                "org_id", "org_name", "org_code", "level", "parent_id", "path"
            ] + dimension_keys

        return [
            self._row_to_metric_row(
                row=dict(row), dimension_keys=dimension_keys, metrics=query.metrics
            )
            for row in rows
        ]

    def _validate_query(self, query: OrgMetricQuery) -> None:
        if not query.metrics:
            raise ValueError("至少需要一个 metrics")

        unknown_metrics = set(query.metrics) - set(SUPPORTED_ORG_METRICS)
        if unknown_metrics:
            raise ValueError(f"不支持的组织指标：{sorted(unknown_metrics)}")

        unknown_filters = set(query.filters) - set(SUPPORTED_ORG_FILTERS)
        if unknown_filters:
            raise ValueError(f"不支持的组织过滤条件：{sorted(unknown_filters)}")

        unknown_group_by = set(query.group_by) - set(SUPPORTED_ORG_GROUP_BY)
        if unknown_group_by:
            raise ValueError(f"不支持的组织分组维度：{sorted(unknown_group_by)}")

    def _build_sql(
        self,
        select_parts: list[str],
        where_parts: list[str],
        group_by_parts: list[str],
    ) -> str:
        sql = [
            "SELECT",
            ", ".join(select_parts),
            "FROM org_units",
            "WHERE",
            " AND ".join(where_parts),
        ]

        if group_by_parts:
            sql.extend(["GROUP BY", ", ".join(group_by_parts)])
        else:
            sql.append("ORDER BY org_units.level ASC, org_units.sort_order ASC")

        return "\n".join(sql)

    def _row_to_metric_row(
        self,
        row: dict[str, Any],
        dimension_keys: list[str],
        metrics: list[str],
    ) -> OrgMetricRow:
        dimensions = {key: row.get(key) for key in dimension_keys if key in row}
        metric_values = {metric: row.get(metric) for metric in metrics}

        return OrgMetricRow(dimensions=dimensions, metrics=metric_values)
