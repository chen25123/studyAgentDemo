from datetime import date, datetime

from pydantic import BaseModel, Field

class TimeRange(BaseModel):
    """统计时间范围。"""

    start_date: date = Field(description="起始日期，格式 YYYY-MM-DD，包含当天")
    end_date: date = Field(description="结束日期，格式 YYYY-MM-DD，包含当天")

class BugMetricQuery(BaseModel):
    """Bug 指标产讯计划。"""

    metrics: list[str] = Field(
        description="要查询的指标，例如 created_bug_count、closed_bug_count、close_rate"
    )
    time_range: TimeRange | None = Field(
        default=None,
        description="统计时间范围；如果为空，则统计全部数据",
    )
    filters: dict[str, str | int | list[str] | list[int]] = Field(
        default_factory=dict,
        description="过滤条件，例如 status、assignee_id、module_name",
    )
    group_by: list[str] = Field(
        default_factory=list,
        description="分组维度，例如 status、assignee_id、module_name",
    )

class BugMetricRow(BaseModel):
    """Bug 指标查询返回的单行数据。"""

    dimensions: dict[str, str | int | None]
    metrics: dict[str, int | float | None]
