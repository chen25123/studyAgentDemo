"""Dashboard 概览统计服务。

注意：本模块使用原始 SQL 直查业务表。
这是概览页面的特例——它需要跨实体聚合（Bug + Requirement），
不适合走单实体的 MetricEngine。后续所有单实体指标查询必须通过 MetricEngine。
"""

from datetime import date

from sqlalchemy import text

from llm.repositories.db import get_engine
from llm.schemas.dashboard import DashboardSummary, MetricCard, RiskItem


class DashboardService:
    def get_summary(self) -> DashboardSummary:
        engine = get_engine()

        with engine.connect() as conn:
            # Bug 总量
            total_bugs = conn.execute(
                text(
                    "SELECT COUNT(*) FROM bugs WHERE deleted_at IS NULL"
                )
            ).scalar()

            # 本月创建 Bug
            today = date.today()
            month_start = today.replace(day=1)
            month_bugs = conn.execute(
                text(
                    "SELECT COUNT(*) FROM bugs "
                    "WHERE deleted_at IS NULL AND created_at >= :start"
                ),
                {"start": month_start.isoformat()},
            ).scalar()

            # 已关闭 Bug 数
            closed_bugs = conn.execute(
                text(
                    "SELECT COUNT(*) FROM bugs "
                    "WHERE deleted_at IS NULL AND status = 'closed'"
                )
            ).scalar()

            # 重开 Bug 数
            reopened_bugs = conn.execute(
                text(
                    "SELECT COUNT(*) FROM bugs "
                    "WHERE deleted_at IS NULL AND reopened_count > 0"
                )
            ).scalar()

            # 需求总量
            total_reqs = conn.execute(
                text(
                    "SELECT COUNT(*) FROM requirements WHERE deleted_at IS NULL"
                )
            ).scalar()

            # 未关闭 Bug
            open_bugs = total_bugs - closed_bugs

            # 延期需求
            delayed_reqs = conn.execute(
                text(
                    "SELECT COUNT(*) FROM requirements "
                    "WHERE deleted_at IS NULL "
                    "AND planned_due_at < NOW() "
                    "AND status NOT IN ('released', 'testing_done')"
                )
            ).scalar()

        close_rate = (
            round(closed_bugs / total_bugs * 100, 2) if total_bugs > 0 else 0
        )
        reopen_rate = (
            round(reopened_bugs / total_bugs * 100, 2) if total_bugs > 0 else 0
        )

        metrics = [
            MetricCard(
                label="Bug 总量",
                value=f"{total_bugs:,}",
                trend=f"关闭率 {close_rate}%",
            ),
            MetricCard(
                label="本月新建 Bug",
                value=f"{month_bugs:,}",
                trend=f"未关闭 {open_bugs:,}",
            ),
            MetricCard(
                label="需求总量",
                value=f"{total_reqs:,}",
                trend=f"延期 {delayed_reqs:,}",
            ),
            MetricCard(
                label="重开 Bug",
                value=f"{reopened_bugs:,}",
                trend=f"重开率 {reopen_rate}%",
            ),
        ]

        risks = [
            RiskItem(
                title="延期需求偏高",
                detail=f"当前有 {delayed_reqs:,} 条需求已超期未完成，交付压力大。",
                level="高" if delayed_reqs > 5000 else "中",
            ),
            RiskItem(
                title="重开 Bug 需关注",
                detail=f"重开 Bug {reopened_bugs:,} 条（重开率 {reopen_rate}%），建议分析归因。",
                level="高" if reopen_rate > 15 else "中",
            ),
            RiskItem(
                title="未关闭 Bug 积压",
                detail=f"当前有 {open_bugs:,} 条 Bug 未关闭，需关注清理进度。",
                level="高" if open_bugs > 40000 else "中",
            ),
        ]

        return DashboardSummary(metrics=metrics, risks=risks)
