from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.pydantic_models import AuditEntryResponse, AuditVerificationResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/cases", tags=["Audit Trail & Verification"])

@router.get("/{inspection_id}/audit", response_model=List[AuditEntryResponse])
def get_case_audit_history(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve complete append-only audit trail history for an inspection case."""
    return AuditService.get_case_audit_history(db, inspection_id)

@router.get("/{inspection_id}/audit/verify", response_model=AuditVerificationResponse)
def verify_case_audit_chain(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    """
    Verify cryptographic SHA-256 hash-chain integrity for an inspection case audit trail.
    Detects if any audit entry, metadata, or previous hash link has been tampered with.
    """
    is_valid, total_entries, corrupted_index, msg = AuditService.verify_chain(db, inspection_id)
    return AuditVerificationResponse(
        inspection_id=inspection_id,
        is_valid=is_valid,
        total_entries=total_entries,
        corrupted_sequence_index=corrupted_index,
        message=msg
    )
