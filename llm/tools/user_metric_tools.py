from langchain_core.tools import tool

from llm.repositories.user_metric_repository import UserMetricRepository
from llm.schemas.user_metric import UserMetricQuery

_repo = UserMetricRepository()


@tool
def query_user_metrics(query: UserMetricQuery) -> str:
    """查询员工/组织架构数据。

    适用问题：
    - XX 属于哪个部门？什么职位？
    - XX 部门下面有多少员工？
    - 当前人员组织架构是什么样子？
    - 各个部门/岗位的人员分布？
    - 在职/禁用员工数量？
    - 有多少产品经理/后端工程师/测试工程师？

    参数说明：
    - metrics: 指标列表，例如 user_count / active_user_count / disabled_user_count
    - time_range: 时间范围（按入职时间过滤），可选
    - filters: 过滤条件，例如 department / job_title / role_code / status / display_name
    - group_by: 分组维度，例如 department / job_title / role_code / status

    示例：
    - "研发一部多少人" → metrics=["user_count"], filters={"department":"研发一部"}
    - "组织架构" → metrics=["user_count"], group_by=["department"]
    - "张三在哪" → metrics=["user_count"], filters={"display_name":"张三"},
      group_by=["department","job_title"]
    """
    try:
        rows = _repo.query_metrics(query)
    except ValueError as exc:
        return str(exc)

    if not rows:
        return "没有查询到符合条件的员工数据。"

    lines = ["员工/组织架构查询结果："]

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
