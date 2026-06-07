from pydantic import BaseModel, Field


class MetricCard(BaseModel):
    label: str = Field(description="指标名称")
    value: str = Field(description="格式化后的数值")
    trend: str = Field(description="趋势/说明")


class RiskItem(BaseModel):
    title: str = Field(description="风险标题")
    detail: str = Field(description="风险详情")
    level: str = Field(description="风险等级：高/中/低")


class DashboardSummary(BaseModel):
    metrics: list[MetricCard]
    risks: list[RiskItem]
