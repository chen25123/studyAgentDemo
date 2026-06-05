from typing import Any

from sqlalchemy import text

from llm.domain.bug_metrics import (
    SUPPORTED_BUG_FILTERS,
    SUPPORTED_BUG_GROUP_BY,
    SUPPORTED_BUG_METRICS,
)
from llm.repositories.db import get_engine
from llm.schemas.bug_metric import BugMetricQuery, BugMetricRow

class BugMetricRepository:
    """执行bug指标查询"""

    def query_metrics(self, query: BugMetricQuery) -> list[BugMetricRow]:
        self._validate_query(query)

        select_parts: list[str] = []
        group_by_parts: list[str] = []

        for dimension in query.group_by:
            column = SUPPORTED_BUG_GROUP_BY[dimension]
            select_parts.append(f"{column} AS {dimension}")
            group_by_parts.append(column)

        for metric in query.metrics:
            metric_def = SUPPORTED_BUG_METRICS[metric]
            select_parts.append(f"{metric_def['sql']} AS {metric}")

        where_parts = ["bugs.deleted_at  IS NULL"]
        params: dict[str, Any] = {}

        if query.time_range is not None:
            where_parts.append("bugs.created_at >= :start_date")
            where_parts.append("bugs.created_at < DATE_ADD(:end_date, INTERVAL 1 DAY)")
            params["start_date"] = query.time_range.start_date.isoformat()
            params["end_date"] = query.time_range.end_date.isoformat()

        for index, (filter_name, filter_value) in enumerate(query.filters.items()):
            column = SUPPORTED_BUG_FILTERS[filter_name]
            param_name = f"filter_{index}"

            if isinstance(filter_value, list):
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

        return [
            self._row_to_metric_row(row=dict(row), group_by=query.group_by, metrics=query.metrics)
            for row in rows
        ]
            

    def _validate_query(self, query: BugMetricQuery) -> None:
        if not query.metrics:
            raise ValueError("至少需要一个metrics")
        
        unknown_metrices = set(query.metrics) - set(SUPPORTED_BUG_METRICS)
        if unknown_metrices:
            raise ValueError(f"不支持的bug指标：{sorted(unknown_metrices)}")

        unknown_filters = set(query.filters) - set(SUPPORTED_BUG_FILTERS)
        if unknown_filters:
            raise ValueError(f"不支持的bug过滤条件：{sorted(unknown_filters)}")
        
        unknown_group_by = set(query.group_by) - set(SUPPORTED_BUG_GROUP_BY)
        if unknown_group_by:
            raise ValueError(f"不支持的bug分组维度： {sorted(unknown_group_by)}")
        
    def _build_sql(self, select_parts: list[str], where_parts: list[str], group_by_parts: list[str]) -> str:
        sql = [
            "SELECT",
            ",".join(select_parts),
            "FROM bugs",
            "WHERE",
            " AND ".join(where_parts),
        ]

        if group_by_parts:
            sql.extend(
                [
                    "GROUP BY",
                    ",".join(group_by_parts)
                ]
            )

        return "\n".join(sql)
    
    def _row_to_metric_row(
        self,
        row: dict[str, Any],
        group_by: list[str],
        metrics: list[str]
    ) -> BugMetricRow:
        dimensions = {
            dimension: row.get(dimension) for dimension in group_by
        }

        metric_values = { metric: row.get(metric) for metric in metrics }

        return BugMetricRow(
            dimensions=dimensions,
            metrics=metric_values,
        )
        