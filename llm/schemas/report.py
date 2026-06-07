"""Report 数据模型。"""


from pydantic import BaseModel


class MetricSnapshot(BaseModel):
    metric_code: str
    metric_name: str
    value: float | None
    unit: str
    description: str
    chart_b64: str = ""


class ReportSection(BaseModel):
    title: str
    content: str
    chart_b64: str = ""


class Report(BaseModel):
    title: str
    period: str
    generated_at: str
    summary: str
    sections: list[ReportSection] = []
    metrics: list[MetricSnapshot] = []
    risks: list[dict[str, str]] = []
