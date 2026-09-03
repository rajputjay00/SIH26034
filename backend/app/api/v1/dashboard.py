from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.pydantic_models import (
    UserProfile,
    DashboardSummaryResponse,
    DashboardReviewQueueResponse,
    DashboardFindingsBreakdown,
    DashboardTrendItem
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Government Dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve aggregate KPI statistics from the database for the executive dashboard."""
    service = DashboardService(db)
    return service.get_summary_kpis()

@router.get("/review-queue", response_model=DashboardReviewQueueResponse)
def get_review_queue_metrics(
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve active officer review workload metrics categorized by priority."""
    service = DashboardService(db)
    return service.get_review_queue_metrics()

@router.get("/findings", response_model=DashboardFindingsBreakdown)
def get_findings_breakdown(
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve rule-by-rule statutory violation and finding distributions."""
    service = DashboardService(db)
    return service.get_findings_breakdown()

@router.get("/trends", response_model=List[DashboardTrendItem])
def get_inspection_trends(
    days: int = Query(14, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve historical inspection creation and finalisation trends."""
    service = DashboardService(db)
    return service.get_inspection_trends(days=days)
