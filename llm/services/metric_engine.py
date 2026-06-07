import json
import time
from typing import Any

from sqlalchemy import text

from llm.repositories.db import get_engine
from llm.repositories.metric_layer_repository import MetricLayerRepository
from llm.schemas.metric_query import MetricQuery, MetricResultRow


class MetricEngineError(ValueError):
    """语义层校验失败。"""


class MetricEngine:
    """语义层指标引擎 —— 校验 QueryPlan + 编译 SQL + 执行查询。

    禁止 LLM 直接生成 SQL。所有 SQL 由此引擎根据语义层表定义编译。
    """

    def __init__(self) -> None:
        self._repo = MetricLayerRepository()

    def execute(
        self,
        query: MetricQuery,
        trace_id: str = "",
        session_id: str = "",
    ) -> tuple[list[MetricResultRow], str]:
        """执行 MetricQuery，返回结构化结果 + 编译 SQL（用于审计）。"""
        started_at = time.perf_counter()

        # 1. 校验
        metrics_map = self._validate_and_load(query)

        # 2. 编译
        compiled = self._compile(query, metrics_map)

        # 3. 执行
        rows = self._execute_sql(compiled["sql"], compiled["params"])
        duration_ms = int((time.perf_counter() - started_at) * 1000)

        # 4. 记录查询日志
        self._repo.save_query_log(
            trace_id=trace_id,
            session_id=session_id,
            query_plan=query.model_dump(mode="json"),
            compiled_sql=compiled["sql"],
            duration_ms=duration_ms,
            status="success",
        )

        # 5. 组装结果
        results = self._assemble_results(rows, query, metrics_map, compiled)

        return results, compiled["sql"]

    # ================================================================
    # 校验
    # ================================================================

    def _validate_and_load(
        self, query: MetricQuery
    ) -> dict[str, dict[str, Any]]:
        if not query.metric_codes:
            raise MetricEngineError("至少需要一个 metric_code")

        # 加载指标定义
        metrics_map = self._repo.get_active_metrics(query.metric_codes)
        missing = set(query.metric_codes) - set(metrics_map)
        if missing:
            raise MetricEngineError(f"指标不存在或未激活：{sorted(missing)}")

        # 校验所有指标属于同一实体（阶段一限制）
        entities = {m["entity_code"] for m in metrics_map.values()}
        if len(entities) > 1:
            raise MetricEngineError(
                f"阶段一只支持单实体查询，当前涉及实体：{sorted(entities)}。请分多次查询。"
            )
        entity_code = next(iter(entities))

        entity = self._repo.get_entity(entity_code)
        if entity is None:
            raise MetricEngineError(f"实体不存在：{entity_code}")

        # 校验 filters 的 key 都是可过滤维度
        filterable = self._repo.get_filterable_dimension_codes(entity_code)
        invalid_filters = set(query.filters) - set(filterable)
        if invalid_filters:
            raise MetricEngineError(
                f"不支持过滤的维度：{sorted(invalid_filters)}。"
                f"允许：{sorted(filterable)}"
            )

        # 校验 group_by 都是可分组维度
        groupable = self._repo.get_groupable_dimension_codes(entity_code)
        invalid_groups = set(query.group_by) - set(groupable)
        if invalid_groups:
            raise MetricEngineError(
                f"不支持分组的维度：{sorted(invalid_groups)}。"
                f"允许：{sorted(groupable)}"
            )

        return metrics_map

    # ================================================================
    # 编译 SQL
    # ================================================================

    def _compile(
        self, query: MetricQuery, metrics_map: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        entity_code = next(iter(metrics_map.values()))["entity_code"]
        entity = self._repo.get_entity(entity_code)
        base_table = entity["base_table"]
        time_field = entity.get("default_time_field") or "created_at"

        # 收集所有 measure
        all_measures: dict[str, dict] = {}
        for m in metrics_map.values():
            formula = m["formula_config"]
            if isinstance(formula, str):
                formula = json.loads(formula)
            if m["formula_type"] == "ratio":
                all_measures[formula["numerator"]] = {}
                all_measures[formula["denominator"]] = {}
            elif m["formula_type"] == "count":
                meas_code = formula.get("measure", "")
                if meas_code:
                    all_measures[meas_code] = {}
        if all_measures:
            loaded = self._repo.get_measures(list(all_measures))
            all_measures.update(loaded)

        # 收集所有引用的维度
        dim_codes = list(query.group_by) + list(query.filters)
        dims = self._repo.get_dimensions(entity_code, dim_codes)
        dims_map = {d["dimension_code"]: d for d in dims}

        # 收集 JOIN（替换表名为别名 b.）
        join_clauses: list[str] = []
        for d in dims:
            jc = d.get("join_config")
            if jc is None:
                continue
            if isinstance(jc, str):
                jc = json.loads(jc)
            for j in jc.get("joins", []):
                on_clause = j["on"].replace(f"{base_table}.", "b.")
                clause = f"JOIN {j['table']} ON {on_clause}"
                if clause not in join_clauses:
                    join_clauses.append(clause)

        # 构建子查询 SELECT
        inner_select: list[str] = []
        inner_group: list[str] = []

        # group_by 维度
        for dim_code in query.group_by:
            d = dims_map[dim_code]
            col = d["field_expression"].replace(f"{base_table}.", "b.")
            inner_select.append(f"{col} AS {dim_code}")
            inner_group.append(col)

        # 每个 measure 的聚合表达式
        measure_expressions: dict[str, str] = {}
        for meas_code, meas in all_measures.items():
            agg = meas.get("aggregation", "count")
            expr = meas.get("expression", "*")
            fc = meas.get("filter_config")
            if isinstance(fc, str):
                fc = json.loads(fc)

            # 构建 measure 级过滤条件
            meas_filter = ""
            if fc and fc.get("filters"):
                parts = []
                op_map = {
                    "eq": "=", "neq": "!=", "gt": ">",
                    "lt": "<", "gte": ">=", "lte": "<=",
                    "not_in": "NOT IN", "in": "IN",
                }
                for f in fc["filters"]:
                    sql_op = op_map.get(f.get("operator", "eq"), "=")
                    col = f["field"].replace(f"{base_table}.", "b.")
                    val = f.get("value")
                    if isinstance(val, list):
                        quoted = ", ".join(
                            f"'{v}'" if v != "NOW()" else v for v in val
                        )
                        parts.append(f"{col} {sql_op} ({quoted})")
                    elif isinstance(val, str) and val.upper() == "NOW()":
                        parts.append(f"{col} {sql_op} NOW()")
                    elif isinstance(val, str) and val.isdigit():
                        parts.append(f"{col} {sql_op} {val}")
                    else:
                        parts.append(f"{col} {sql_op} '{val}'")
                meas_filter = " AND ".join(parts)

            if agg.upper() == "COUNT":
                if meas_filter:
                    # COUNT 带过滤 → SUM(CASE WHEN ... THEN 1 ELSE 0 END)
                    sql_expr = (
                        f"SUM(CASE WHEN {meas_filter} THEN 1 ELSE 0 END)"
                    )
                elif expr == "*":
                    sql_expr = "COUNT(*)"
                else:
                    sql_expr = f"COUNT({expr})"
            else:
                sql_expr = f"{agg.upper()}({expr})"

            measure_expressions[meas_code] = sql_expr
            inner_select.append(f"{sql_expr} AS {meas_code}")

        # WHERE
        where_parts = ["b.deleted_at IS NULL"]
        params: dict[str, Any] = {}

        if query.time_range:
            where_parts.append(f"b.{time_field} >= :start_date")
            where_parts.append(
                f"b.{time_field} < DATE_ADD(:end_date, INTERVAL 1 DAY)"
            )
            params["start_date"] = query.time_range.start_date.isoformat()
            params["end_date"] = query.time_range.end_date.isoformat()

        for idx, (filter_name, filter_value) in enumerate(query.filters.items()):
            d = dims_map[filter_name]
            col = d["field_expression"].replace(f"{base_table}.", "b.")
            pname = f"filter_{idx}"

            # 组织名称走模糊匹配
            if filter_name.endswith("_name") and d["data_type"] == "string":
                where_parts.append(f"{col} LIKE :{pname}")
                params[pname] = f"%{filter_value}%"
            elif isinstance(filter_value, list):
                bind_names = []
                for vi, v in enumerate(filter_value):
                    ipn = f"{pname}_{vi}"
                    bind_names.append(f":{ipn}")
                    params[ipn] = v
                where_parts.append(f"{col} IN ({', '.join(bind_names)})")
            else:
                where_parts.append(f"{col} = :{pname}")
                params[pname] = filter_value

        # 组装子查询
        inner_sql = (
            f"SELECT {', '.join(inner_select)}\n"
            f"FROM {base_table} b\n"
            + ("\n".join(join_clauses) + "\n" if join_clauses else "")
            + f"WHERE {' AND '.join(where_parts)}"
        )
        if inner_group:
            inner_sql += f"\nGROUP BY {', '.join(inner_group)}"

        # 外层：计算 ratio
        outer_select: list[str] = []
        for g in query.group_by:
            outer_select.append(f"sub.{g}")

        for mc in query.metric_codes:
            m = metrics_map[mc]
            formula = m["formula_config"]
            if isinstance(formula, str):
                formula = json.loads(formula)

            if m["formula_type"] == "ratio":
                num = formula["numerator"]
                den = formula["denominator"]
                if m["format_type"] == "percent":
                    outer_select.append(
                        f"ROUND(sub.{num} / NULLIF(sub.{den}, 0) * 100, 2) "
                        f"AS {mc}"
                    )
                else:
                    outer_select.append(
                        f"sub.{num} / NULLIF(sub.{den}, 0) AS {mc}"
                    )
            elif m["formula_type"] == "count":
                meas_code = formula.get("measure", "")
                outer_select.append(f"sub.{meas_code} AS {mc}")
            else:
                outer_select.append(f"sub.{mc} AS {mc}")

            # 附赠基础度量
            for meas_code in all_measures:
                alias = f"_{meas_code}"
                outer_select.append(f"sub.{meas_code} AS {alias}")

        sql = (
            f"SELECT {', '.join(outer_select)}\n"
            f"FROM (\n{inner_sql}\n) sub"
        )

        return {"sql": sql, "params": params}

    # ================================================================
    # 执行
    # ================================================================

    def _execute_sql(
        self, sql: str, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        with get_engine().connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
            return [dict(row) for row in rows]

    # ================================================================
    # 组装结果
    # ================================================================

    def _assemble_results(
        self,
        rows: list[dict[str, Any]],
        query: MetricQuery,
        metrics_map: dict[str, dict[str, Any]],
        compiled: dict[str, Any],
    ) -> list[MetricResultRow]:
        results: list[MetricResultRow] = []

        for row in rows:
            # 维度值
            dims = {g: row.get(g) for g in query.group_by}

            for mc in query.metric_codes:
                m = metrics_map[mc]
                unit = "%" if m["format_type"] == "percent" else "个"
                value = row.get(mc)

                # 基础度量
                formula = m["formula_config"]
                if isinstance(formula, str):
                    formula = json.loads(formula)
                measure_values: dict[str, Any] = {}
                if m["formula_type"] == "ratio":
                    num = formula["numerator"]
                    den = formula["denominator"]
                    measure_values[num] = row.get(f"_{num}")
                    measure_values[den] = row.get(f"_{den}")
                elif m["formula_type"] == "count":
                    meas_code = formula.get("measure", "")
                    if meas_code:
                        measure_values[meas_code] = row.get(f"_{meas_code}")
                        # value 就是 measure 的值
                        value = row.get(f"_{meas_code}")

                results.append(
                    MetricResultRow(
                        metric_code=mc,
                        metric_name=m["metric_name"],
                        value=value,
                        unit=unit,
                        description=m["description"],
                        dimensions=dims,
                        measures=measure_values,
                    )
                )

        return results
