from datetime import date

from langchain_core.tools import tool

from llm.repositories.bug_repository import BugRepository

_repo = BugRepository()


@tool
def get_bug_count_by_time(start_date: str, end_date: str) -> str:
    """查询指定时间段内创建的 Bug 数量。

    当你需要回答「XX 时间段内创建/新建了多少 Bug」这类问题时，
    必须调用此工具获取真实数据，不要编造数字。

    Args:
        start_date: 起始日期，格式 YYYY-MM-DD（含）。
        end_date: 结束日期，格式 YYYY-MM-DD（含）。
    """
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        return "日期格式错误，请使用 YYYY-MM-DD"

    result = _repo.count_by_date_time(start, end)
    return (
        f"{result.label}: 共 {result.count} 个。"
        f"统计区间为 {result.period_start} 至 {result.period_end}。"
    )


@tool
def get_bug_status() -> str:
    """查询当前所有 Bug 的状态分布。

    当你需要回答「Bug 状态分布如何」「各状态下有多少 Bug」时调用。
    """
    rows = _repo.status_distribution()
    if not rows:
        return "当前没有 Bug 记录"
    lines = ["当前 Bug 状态分布（不含已删除）："]
    for r in rows:
        lines.append(f" - {r.status}: {r.count}")
    return "\n".join(lines)
