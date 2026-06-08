from pydantic import BaseModel, Field

from llm.schemas.bug_metric import TimeRange


class UserMetricQuery(BaseModel):
    """用户/组织架构查询计划。"""

    metrics: list[str] = Field(
        description="要查询的用户指标，例如 user_count / active_user_count / disabled_user_count"
    )
    time_range: TimeRange | None = Field(
        default=None,
        description="统计时间范围（按用户创建时间过滤）；为空则统计全部数据",
    )
    filters: dict[str, str | int | list[str] | list[int]] = Field(
        default_factory=dict,
        description="过滤条件，例如 department / job_title / role_code / status / org_name",
    )
    group_by: list[str] = Field(
        default_factory=list,
        description="分组维度，例如 department / job_title / role_code / status",
    )
    list_mode: bool = Field(
        default=False,
        description="True=返回人员明细列表（姓名/职位/部门），False=仅统计数字",
    )


class UserMetricRow(BaseModel):
    """用户指标查询返回的单行数据。"""

    dimensions: dict[str, str | int | None]
    metrics: dict[str, int | float | None]
