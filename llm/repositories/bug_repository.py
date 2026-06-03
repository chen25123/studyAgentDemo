from datetime import date

from sqlalchemy import text

from llm.repositories.db import get_engine
from llm.schemas.bug import BugCountResult, BugStatusSummary


class BugRepository:
    def count_by_date_time(self, start_date: date, end_date: date) -> BugCountResult:
        """统计指定时间段内创建的 Bug 总数。

        Args:
            start_date: 起始日期（含）
            end_date: 结束日期（含），使用 < :end_date + 1 day 保证区间完整
        """

        sql = text(
            """
            SELECT COUNT(*) AS cnt
            FROM bugs
            WHERE created_at >= :start_date
               AND created_at < DATE_ADD(:end_date, INTERVAL 1 DAY)
               AND deleted_at IS NULL
            """
        )

        with get_engine().connect() as conn:
            row = (
                conn.execute(
                    sql,
                    {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    },
                )
                .mappings()
                .first()
            )

        count = row["cnt"] if row is not None else 0
        return BugCountResult(
            label=f"{start_date} 到 {end_date} 创建的 Bug",
            count=count,
            period_end=end_date,
            period_start=start_date,
        )

    def status_distribution(self) -> list[BugStatusSummary]:
        sql = text(
            """
            SELECT status, COUNT(*) as cnt
            FROM bugs
            WHERE deleted_at IS NULL
            GROUP BY status
            ORDER BY cnt DESC
            """
        )

        with get_engine().connect() as conn:
            rows = conn.execute(sql).mappings().all()

        return [BugStatusSummary(status=row["status"], count=row["cnt"]) for row in rows]
