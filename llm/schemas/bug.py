from datetime import date

from pydantic import BaseModel, Field


class BugCountResult(BaseModel):
    model_config = {"from_attributes": True}
    label: str = Field(description="统计口径说明，例如「2026年5月创建的Bug」")
    count: int = Field(ge=0, description="Bug 数量，不可能为负数")
    period_start: date = Field(description="统计区间起始日期")
    period_end: date = Field(description="统计区间结束日期")


class BugStatusSummary(BaseModel):
    status: str = Field(description="Bug 状态：new/processing/fixed/closed 等")
    count: int = Field(ge=0, description="该状态下的 Bug 数量")
