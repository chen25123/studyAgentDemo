from pydantic import BaseModel, Field


class OrgMetricQuery(BaseModel):
    """组织架构查询计划。"""

    metrics: list[str] = Field(
        description="要查询的指标，例如 org_unit_count / direct_children_count"
    )
    filters: dict[str, str | int | list[str] | list[int]] = Field(
        default_factory=dict,
        description="过滤条件，例如 org_name / org_type / parent_id / level",
    )
    group_by: list[str] = Field(
        default_factory=list,
        description="分组维度，例如 org_type / level / parent_id",
    )
    list_mode: bool = Field(
        default=False,
        description="是否以列表模式返回（展示部门列表而非统计数字），默认 False 只统计",
    )


class OrgMetricRow(BaseModel):
    """组织架构查询返回的单行数据。"""

    dimensions: dict[str, str | int | None]
    metrics: dict[str, int | float | None]
