from datetime import date

from pydantic import BaseModel, Field


class TimeRange(BaseModel):
    """统计时间范围。"""

    start_date: date = Field(description="起始日期，格式 YYYY-MM-DD，包含当天")
    end_date: date = Field(description="结束日期，格式 YYYY-MM-DD，包含当天")


class MetricQuery(BaseModel):
    """统一指标查询计划 —— LLM 输出这个，不是 SQL。"""

    metric_codes: list[str] = Field(
        description="要查询的指标编码列表，例如 ['bug_close_rate']"
    )
    time_range: TimeRange | None = Field(
        default=None,
        description="统计时间范围；为空则查全量数据",
    )
    filters: dict[str, str | int | list[str] | list[int]] = Field(
        default_factory=dict,
        description="过滤条件，例如 {'assignee_org_name': '研发一部', 'status': 'closed'}",
    )
    group_by: list[str] = Field(
        default_factory=list,
        description="分组维度，例如 ['module_name', 'severity']",
    )


class MetricResultRow(BaseModel):
    """单个指标的一行查询结果。"""

    metric_code: str = Field(description="指标编码")
    metric_name: str = Field(description="指标名称")
    value: float | None = Field(description="指标值")
    unit: str = Field(default="", description="单位：% / 个 / 次")
    description: str = Field(default="", description="口径说明")
    dimensions: dict[str, str | int | None] = Field(
        default_factory=dict,
        description="分组维度值，例如 {'module_name': '订单'}",
    )
    measures: dict[str, int | float | None] = Field(
        default_factory=dict,
        description="组成指标的基础度量值，例如 {'bug_count': 26794, 'closed_bug_count': 3828}",
    )
