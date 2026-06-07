"""Report API —— 报告生成。"""

from datetime import date

from fastapi import APIRouter

from llm.schemas.report import Report
from llm.services.report_service import ReportService

router = APIRouter(prefix="/api/reports", tags=["reports"])

_svc = ReportService()


@router.post("/weekly", response_model=Report)
def generate_weekly_report():
    """生成本周报告。"""
    today = date.today()
    start = today - date.resolution * (today.weekday() + 7)
    end = today
    return _svc.generate_weekly(start, end)


@router.post("/generate", response_model=Report)
def generate_report():
    """生成默认周报（同 /weekly）。"""
    return generate_weekly_report()
