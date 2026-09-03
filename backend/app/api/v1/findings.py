from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, RequireRole
from app.models.domain import RuleFinding, UserRole
from app.schemas.pydantic_models import (
    RuleFindingResponse,
    CaseEvaluationSummary,
    UserProfile
)
from app.services.rule_engine_service import ComplianceEvaluationService

router = APIRouter(prefix="/cases", tags=["Deterministic Rule Engine & Findings"])

@router.post("/{inspection_id}/evaluate", response_model=CaseEvaluationSummary)
def evaluate_case_compliance(
    inspection_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(RequireRole([UserRole.ADMIN, UserRole.OFFICER, UserRole.REVIEWER]))
):
    """
    Execute deterministic Legal Metrology compliance evaluation across structured fields.
    Evaluates mandatory declarations, Unit Sale Price arithmetic, and font height calibration status.
    """
    service = ComplianceEvaluationService(db)
    result = service.evaluate_inspection(inspection_id, officer_id=current_user.user_id)
    return CaseEvaluationSummary(
        inspection_id=result["inspection_id"],
        overall_determination=result["overall_determination"],
        total_rules_evaluated=result["total_rules_evaluated"],
        pass_count=result["pass_count"],
        fail_count=result["fail_count"],
        review_count=result["review_count"],
        not_applicable_count=result["not_applicable_count"],
        rule_pack_version=result["rule_pack_version"],
        evaluated_at=result["evaluated_at"],
        findings=result["findings"]
    )

@router.post("/{inspection_id}/evaluate/rerun", response_model=CaseEvaluationSummary)
def rerun_case_compliance(
    inspection_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(RequireRole([UserRole.ADMIN, UserRole.OFFICER, UserRole.REVIEWER]))
):
    """
    Re-evaluate deterministic compliance rules following manual officer field corrections.
    """
    service = ComplianceEvaluationService(db)
    result = service.evaluate_inspection(inspection_id, officer_id=current_user.user_id)
    return CaseEvaluationSummary(
        inspection_id=result["inspection_id"],
        overall_determination=result["overall_determination"],
        total_rules_evaluated=result["total_rules_evaluated"],
        pass_count=result["pass_count"],
        fail_count=result["fail_count"],
        review_count=result["review_count"],
        not_applicable_count=result["not_applicable_count"],
        rule_pack_version=result["rule_pack_version"],
        evaluated_at=result["evaluated_at"],
        findings=result["findings"]
    )

@router.get("/{inspection_id}/findings", response_model=List[RuleFindingResponse])
def get_case_findings(
    inspection_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve all deterministic rule findings with calculation metadata and evidence links."""
    findings = db.query(RuleFinding)\
        .filter(RuleFinding.inspection_id == inspection_id)\
        .order_by(RuleFinding.created_at.asc())\
        .all()
    return findings
