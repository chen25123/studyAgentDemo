from fastapi import APIRouter

from llm.schemas.dashboard import DashboardSummary
from llm.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api", tags=["dashboard"])

dashboard_service = DashboardService()


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary() -> DashboardSummary:
    return dashboard_service.get_summary()
