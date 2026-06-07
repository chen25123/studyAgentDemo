"""报告生成工具 —— Agent 可调用此工具生成周报/月报。"""

from datetime import date

from langchain_core.tools import tool

from llm.services.report_service import ReportService

_svc = ReportService()


@tool
def generate_weekly_report() -> str:
    """生成研发质量周报。包含 Bug 和需求的指标总览、图表、风险项。

    当用户要求"生成报告""来一份周报""质量报告"时调用此工具。
    """
    today = date.today()
    start = today - date.resolution * (today.weekday() + 7)
    report = _svc.generate_weekly(start, today)

    lines = [
        f"# {report.title}",
        f"周期：{report.period}",
        "",
        report.summary,
        "",
    ]

    for section in report.sections:
        lines.append(f"## {section.title}")
        lines.append(section.content)
        lines.append("")

    if report.risks:
        lines.append("## 风险提示")
        for r in report.risks:
            lines.append(f"- [{r['level']}] {r['title']}：{r['detail']}")

    if report.metrics:
        lines.append("")
        lines.append("## 指标明细")
        for m in report.metrics:
            val = f"{m.value}{m.unit}" if m.value is not None else "无数据"
            lines.append(f"- {m.metric_name}：{val} | 口径：{m.description}")

    return "\n".join(lines)
