from langchain_core.tools import tool

from llm.repositories.bug_metric_repository import BugMetricRepository
from llm.schemas.bug_metric import BugMetricQuery

_repo = BugMetricRepository()


@tool
def query_bug_metrics(query: BugMetricQuery) -> str:
    """查询 Bug 指标。

    适用问题：
    - 最近一个月创建了多少 Bug？
    - 其中多少已关闭？
    - 关闭率是多少？
    - 某个人处理了多少 Bug？
    - 某个模块 Bug 数量是多少？
    - 按状态、负责人、模块、严重级别统计 Bug。

    参数说明：
    - metrics: 指标列表，例如 created_bug_count、closed_bug_count、close_rate
    - time_range: 创建时间范围
    - filters: 过滤条件，例如 status、assignee_id、module_name
    - group_by: 分组维度，例如 status、assignee_id、module_name
    """
    try:
        rows = _repo.query_metrics(query)
    except ValueError as exc:
        return str(exc)

    if not rows:
        return "没有查询到符合条件的 Bug 数据。"

    lines = ["Bug 指标查询结果："]

    for row in rows:
        dimension_text = _format_dimensions(row.dimensions)
        metric_text = _format_metrics(row.metrics)

        if dimension_text:
            lines.append(f"- {dimension_text}: {metric_text}")
        else:
            lines.append(f"- {metric_text}")

    return "\n".join(lines)


def _format_dimensions(dimensions: dict[str, str | int | None]) -> str:
    if not dimensions:
        return ""

    return "，".join(
        f"{key}={value if value is not None else '未设置'}"
        for key, value in dimensions.items()
    )


def _format_metrics(metrics: dict[str, int | float | None]) -> str:
    return "，".join(
        f"{key}={value if value is not None else 0}"
        for key, value in metrics.items()
    )