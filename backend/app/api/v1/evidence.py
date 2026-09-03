from typing import List
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, RequireRole
from app.models.domain import EvidenceViewType, UserRole
from app.schemas.pydantic_models import EvidenceResponse, OCRResultResponse, UserProfile
from app.services.evidence_service import EvidenceService

router = APIRouter(tags=["Evidence Ingestion & OCR"])

@router.post("/cases/{inspection_id}/evidence", response_model=EvidenceResponse, status_code=201)
async def upload_evidence(
    inspection_id: str,
    view_type: EvidenceViewType = Form(EvidenceViewType.FRONT),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(RequireRole([UserRole.ADMIN, UserRole.OFFICER]))
):
    """
    Ingest multi-image evidence item for an inspection case.
    Validates image file, stores immutable original, and calculates SHA-256 hash immediately.
    """
    service = EvidenceService(db)
    contents = await file.read()
    return service.ingest_evidence(
        inspection_id=inspection_id,
        file_bytes=contents,
        filename=file.filename or "uploaded_evidence.jpg",
        content_type=file.content_type or "image/jpeg",
        view_type=view_type,
        officer_id=current_user.user_id
    )

@router.get("/cases/{inspection_id}/evidence", response_model=List[EvidenceResponse])
def list_case_evidence(
    inspection_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve all evidence items uploaded for an inspection case."""
    service = EvidenceService(db)
    return service.list_case_evidence(inspection_id)

@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
def get_evidence_detail(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve detailed metadata, quality report, and OCR status for a specific evidence item."""
    service = EvidenceService(db)
    return service.get_evidence(evidence_id)

@router.post("/evidence/{evidence_id}/process", response_model=EvidenceResponse)
def process_evidence_ocr(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(RequireRole([UserRole.ADMIN, UserRole.OFFICER]))
):
    """
    Execute image quality gate, OpenCV preprocessing, and PaddleOCR text/bounding-box extraction.
    """
    service = EvidenceService(db)
    return service.process_evidence(evidence_id, officer_id=current_user.user_id)

@router.get("/evidence/{evidence_id}/ocr", response_model=List[OCRResultResponse])
def get_evidence_ocr_results(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve extracted OCR text, bounding boxes, character heights, and confidence scores."""
    service = EvidenceService(db)
    return service.get_evidence_ocr(evidence_id)

@router.post("/evidence/{evidence_id}/retry", response_model=EvidenceResponse)
def retry_evidence_processing(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(RequireRole([UserRole.ADMIN, UserRole.OFFICER]))
):
    """Retry quality check and OCR processing for an evidence item."""
    service = EvidenceService(db)
    return service.retry_evidence_processing(evidence_id, officer_id=current_user.user_id)
