from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, RequireRole
from app.models.domain import UserRole
from app.schemas.pydantic_models import (
    CaseCreate,
    CaseResponse,
    CaseStatusUpdate,
    CaseFinalizeRequest,
    UserProfile,
    InspectionListResponse,
    CaseReviewSummaryResponse
)
from app.services.case_service import CaseService


router = APIRouter(prefix="/cases", tags=["Inspection Cases"])

@router.post("", response_model=CaseResponse, status_code=201)
def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(RequireRole([UserRole.ADMIN, UserRole.OFFICER]))
):
    """Create a new inspection case assigned to the requesting officer."""
    service = CaseService(db)
    return service.create_case(
        officer_id=current_user.user_id,
        case_number=payload.case_number,
        notes=payload.notes,
        rule_pack_version=payload.rule_pack_version
    )

@router.get("", response_model=List[CaseResponse])
def list_cases(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve list of inspection cases."""
    service = CaseService(db)
    return service.list_cases(limit=limit, offset=offset)

@router.get("/summary", response_model=InspectionListResponse)
def list_inspections_summary(
    status: Optional[str] = Query(None, description="Case status filter"),
    determination: Optional[str] = Query(None, description="Overall determination filter"),
    review_queue: Optional[str] = Query(None, description="Review queue category filter"),
    officer_id: Optional[str] = Query(None, description="Officer ID filter"),
    search: Optional[str] = Query(None, description="Search across case number, ID, or notes"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve filtered and paginated inspection summaries for the officer review table."""
    service = CaseService(db)
    items, total = service.list_inspections_summary(
        status=status,
        determination=determination,
        review_queue=review_queue,
        officer_id=officer_id,
        search=search,
        limit=limit,
        offset=offset
    )
    return InspectionListResponse(items=items, total=total, limit=limit, offset=offset)

@router.get("/{inspection_id}/review-summary", response_model=CaseReviewSummaryResponse)
def get_case_review_summary(
    inspection_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve comprehensive multi-view data model for the complete officer review workbench."""
    service = CaseService(db)
    return service.get_review_summary(inspection_id)

@router.get("/{inspection_id}", response_model=CaseResponse)
def get_case(
    inspection_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve details for a specific inspection case by ID."""
    service = CaseService(db)
    return service.get_case(inspection_id)


@router.patch("/{inspection_id}/status", response_model=CaseResponse)
def update_case_status(
    inspection_id: str,
    payload: CaseStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(RequireRole([UserRole.ADMIN, UserRole.OFFICER, UserRole.REVIEWER]))
):
    """Transition status of an inspection case through the lifecycle."""
    service = CaseService(db)
    return service.update_case_status(
        inspection_id=inspection_id,
        new_status=payload.status,
        officer_id=current_user.user_id,
        notes=payload.notes
    )

@router.post("/{inspection_id}/finalize", response_model=CaseResponse)
def finalize_case(
    inspection_id: str,
    payload: CaseFinalizeRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(RequireRole([UserRole.ADMIN, UserRole.OFFICER]))
):
    """
    Finalise an inspection case with authoritative officer decision, remarks, and automatic report generation.
    """
    service = CaseService(db)
    return service.finalize_case(
        inspection_id=inspection_id,
        officer_id=current_user.user_id,
        officer_decision=payload.officer_decision.value if hasattr(payload.officer_decision, "value") else str(payload.officer_decision),
        officer_remarks=payload.officer_remarks,
        acknowledged_review_findings=payload.acknowledged_review_findings
    )

