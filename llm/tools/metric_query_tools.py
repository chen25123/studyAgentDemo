from langchain_core.tools import tool

from llm.schemas.metric_query import MetricQuery
from llm.services.metric_engine import MetricEngine, MetricEngineError

_engine = MetricEngine()


@tool
def query_metric(query: MetricQuery) -> str:
    """查询业务指标。支持关闭率、完成率、统计计数等。

    使用步骤：
    1. 理解用户问题中的指标（如"关闭率"→ bug_close_rate）
    2. 解析时间范围（"本月"→ 具体起止日期）
    3. 解析过滤条件（"研发一部"→ filters={"assignee_org_name":"研发一部"}）
    4. 解析分组维度（"按模块"→ group_by=["module_name"]）

    参数说明：
    - metric_codes: 指标编码列表，例如 ["bug_close_rate"]
    - time_range: {start_date: "YYYY-MM-DD", end_date: "YYYY-MM-DD"}，可选
    - filters: 过滤条件，例如 {"status":"closed", "assignee_org_name":"研发一部"}
    - group_by: 分组维度列表，例如 ["module_name", "severity"]

    当前可用于过滤的维度：status / severity / priority / module_name /
    product_line / assignee_id / reporter_id / assignee_org_id / assignee_org_name
    当前可用于分组的维度：status / severity / priority / module_name /
    product_line / assignee_org_id / assignee_org_name
    当前可用指标：bug_close_rate（Bug 关闭率）
    """
    try:
        results, compiled_sql = _engine.execute(query)
    except MetricEngineError as exc:
        return f"查询失败：{exc}"

    if not results:
        return "未查询到符合条件的指标数据。"

    lines: list[str] = ["指标查询结果："]

    for r in results:
        dim_text = _format_dims(r.dimensions)
        value_text = (
            f"{r.value}{r.unit}" if r.value is not None else "无数据"
        )

        if dim_text:
            lines.append(f"- {dim_text}: **{r.metric_name}** = {value_text}")
        else:
            lines.append(f"- **{r.metric_name}** = {value_text}")

        # 附赠基础度量
        if r.measures:
            meas_parts = [
                f"{k}={v}" for k, v in r.measures.items() if v is not None
            ]
            if meas_parts:
                lines.append(f"  （{', '.join(meas_parts)}）")

    # 口径说明
    lines.append("")
    lines.append("口径说明：")
    for r in results:
        lines.append(f"- {r.metric_code}：{r.description}")

    return "\n".join(lines)


def _format_dims(dimensions: dict[str, str | int | None]) -> str:
    if not dimensions:
        return ""
    return "，".join(
        f"{k}={v}" for k, v in dimensions.items() if v is not None
    )
