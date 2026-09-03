import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, RequireRole
from app.models.domain import (
    ExtractedField,
    FieldCorrection,
    ExtractionOrigin,
    FieldStatus,
    UserRole
)
from app.schemas.pydantic_models import (
    ExtractedFieldResponse,
    FieldCorrectionCreate,
    UserProfile
)
from app.services.extraction_service import StructuredExtractionService
from app.services.audit_service import AuditService
from app.services.provenance_service import ProvenanceService
from app.utils.errors import ResourceNotFoundError

router = APIRouter(tags=["Extraction & Provenance"])

@router.post("/cases/{inspection_id}/extract", response_model=List[ExtractedFieldResponse])
def extract_case_fields(
    inspection_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(RequireRole([UserRole.ADMIN, UserRole.OFFICER]))
):
    """
    Execute structured field extraction from OCR perception results across all evidence views.
    Note: Extraction is parsing only; compliance evaluation is executed separately by the rule engine.
    """
    service = StructuredExtractionService(db)
    return service.extract_case_fields(inspection_id, officer_id=current_user.user_id)

@router.get("/cases/{inspection_id}/fields", response_model=List[ExtractedFieldResponse])
def get_extracted_fields(
    inspection_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve all structured fields extracted for an inspection case."""
    fields = db.query(ExtractedField)\
        .filter(ExtractedField.inspection_id == inspection_id)\
        .order_by(ExtractedField.created_at.asc())\
        .all()
    return fields

@router.post("/cases/{inspection_id}/fields/{field_id}/correct", response_model=ExtractedFieldResponse)
def correct_field_value(
    inspection_id: str,
    field_id: str,
    payload: FieldCorrectionCreate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(RequireRole([UserRole.ADMIN, UserRole.OFFICER]))
):
    """
    Officer manual correction endpoint.
    Preserves historical raw extraction and logs a FieldCorrection record.
    Updates current normalized value and switches origin tracking to OFFICER.
    """
    from app.models.domain import InspectionCase, CaseStatus
    case = db.query(InspectionCase).filter(InspectionCase.inspection_id == inspection_id).first()
    if not case:
        raise ResourceNotFoundError("InspectionCase", inspection_id)

    if case.status == CaseStatus.FINALISED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify or correct declarations on a finalised inspection case."
        )

    field = db.query(ExtractedField)\
        .filter(ExtractedField.field_id == field_id, ExtractedField.inspection_id == inspection_id)\
        .first()

    if not field:
        raise ResourceNotFoundError("ExtractedField", field_id)

    previous_val = field.normalized_value or field.raw_value

    correction = FieldCorrection(
        correction_id=str(uuid.uuid4()),
        field_id=field.field_id,
        previous_value=previous_val,
        corrected_value=payload.corrected_value,
        officer_id=current_user.user_id,
        reason=payload.reason
    )

    # Update field state without erasing historical raw value
    field.normalized_value = payload.corrected_value
    if payload.unit:
        field.unit = payload.unit
    field.origin = ExtractionOrigin.OFFICER
    field.field_status = FieldStatus.CORRECTED
    field.status = "OFFICER_CORRECTED"

    db.add(correction)
    db.commit()
    db.refresh(field)

    # Log audit event
    AuditService.record_event(
        db=db,
        inspection_id=inspection_id,
        actor_id=current_user.user_id,
        action="CORRECT_FIELD",
        entity_type="ExtractedField",
        entity_id=field_id,
        metadata={
            "field_name": field.field_name,
            "previous_value": previous_val,
            "corrected_value": payload.corrected_value,
            "reason": payload.reason
        }
    )

    return field

@router.get("/fields/{field_id}/provenance", response_model=Dict[str, Any])
def get_field_provenance(
    field_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve full field provenance including evidence source, coordinates, origin, and correction audit history."""
    return ProvenanceService.get_field_provenance(db, field_id)
