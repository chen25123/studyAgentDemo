"""报告生成服务 —— 聚合多指标 + 图表 → 结构化报告。"""

from datetime import date

from llm.schemas.metric_query import MetricQuery, TimeRange
from llm.schemas.report import MetricSnapshot, Report, ReportSection
from llm.services.chart_service import ChartService
from llm.services.metric_engine import MetricEngine


class ReportService:
    def __init__(self):
        self.engine = MetricEngine()
        self.chart = ChartService()

    def generate_weekly(self, start: date, end: date) -> Report:
        tr = TimeRange(start_date=start, end_date=end)
        period = f"{start.isoformat()} ~ {end.isoformat()}"

        # 查询所有 Bug 指标
        bug_metrics = self._query_metrics(
            ["bug_count", "bug_close_rate", "bug_open_rate", "bug_reopen_rate"],
            tr,
        )

        # 查询需求指标
        req_metrics = self._query_metrics(
            ["requirement_delay_rate"], tr
        )

        all_metrics = bug_metrics + req_metrics

        # 生成图表
        sections = []
        if bug_metrics:
            labels = [m.metric_name for m in bug_metrics]
            values = [m.value or 0 for m in bug_metrics]
            chart_b64 = self.chart.render_bar_chart(
                labels=labels, values=values,
                title=f"Bug 指标总览（{period}）",
                ylabel="值",
            )
            sections.append(ReportSection(
                title="Bug 指标总览",
                content=self._format_metrics_text(bug_metrics),
                chart_b64=chart_b64,
            ))

        # 风险识别
        risks = self._identify_risks(all_metrics)

        summary = self._build_summary(all_metrics, risks, period)

        return Report(
            title="研发质量周报",
            period=period,
            generated_at=date.today().isoformat(),
            summary=summary,
            sections=sections,
            metrics=all_metrics,
            risks=risks,
        )

    def _query_metrics(
        self, codes: list[str], tr: TimeRange
    ) -> list[MetricSnapshot]:
        snapshots = []
        for code in codes:
            try:
                results, _ = self.engine.execute(
                    MetricQuery(
                        metric_codes=[code],
                        time_range=tr,
                        filters={},
                        group_by=[],
                    )
                )
                if results:
                    r = results[0]
                    # 生成单指标图表
                    chart_b64 = self.chart.render_metric_card(
                        metric_name=r.metric_name,
                        value=r.value or 0,
                        unit=r.unit,
                        sub_metrics=r.measures,
                    )
                    snapshots.append(MetricSnapshot(
                        metric_code=r.metric_code,
                        metric_name=r.metric_name,
                        value=r.value,
                        unit=r.unit,
                        description=r.description,
                        chart_b64=chart_b64,
                    ))
            except Exception:
                pass
        return snapshots

    @staticmethod
    def _format_metrics_text(metrics: list[MetricSnapshot]) -> str:
        lines = []
        for m in metrics:
            val = f"{m.value}{m.unit}" if m.value is not None else "无数据"
            lines.append(f"- {m.metric_name}：{val}")
        return "\n".join(lines)

    @staticmethod
    def _identify_risks(metrics: list[MetricSnapshot]) -> list[dict[str, str]]:
        risks = []
        for m in metrics:
            if m.value is None:
                continue
            name, val = m.metric_name, m.value
            if "close_rate" in m.metric_code and val < 30:
                risks.append({
                    "title": "关闭率偏低",
                    "detail": f"当前 {name} 仅 {val}%，建议排查积压原因",
                    "level": "高",
                })
            if "reopen_rate" in m.metric_code and val > 10:
                risks.append({
                    "title": "重开率偏高",
                    "detail": f"当前 {name} 为 {val}%，需关注 Bug 修复质量",
                    "level": "中",
                })
            if "delay_rate" in m.metric_code and val > 30:
                risks.append({
                    "title": "延期率偏高",
                    "detail": f"当前 {name} 为 {val}%，交付压力较大",
                    "level": "高",
                })
            if "open_rate" in m.metric_code and val > 80:
                risks.append({
                    "title": "未关闭积压",
                    "detail": f"当前 {name} 为 {val}%，大量 Bug 待处理",
                    "level": "高",
                })
        return risks[:5]

    @staticmethod
    def _build_summary(metrics: list[MetricSnapshot], risks: list[dict], period: str) -> str:
        num_metrics = len(metrics)
        num_risks = len(risks)
        high_risks = [r for r in risks if r.get("level") == "高"]
        return (
            f"本报告覆盖 {period}，共统计 {num_metrics} 项指标。"
            f"发现 {num_risks} 个风险项，其中 {len(high_risks)} 个高风险。"
        )
