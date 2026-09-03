import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import UserRole, GeneratedReport, InspectionCase

from app.schemas.pydantic_models import (
    UserProfile,
    ReportMetadataResponse,
    ReportVerificationResponse
)
from app.services.report_service import ReportService
from app.services.case_service import CaseService
from app.utils.errors import ResourceNotFoundError, ValidationError

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/{report_id}/verify", response_model=ReportVerificationResponse)
def verify_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Public read-only report cryptographic SHA-256 integrity verification endpoint.
    Returns safe verification metadata and matching verdict.
    """
    # Prevent path traversal in report_id input
    if ".." in report_id or "/" in report_id or "\\" in report_id:
        raise HTTPException(status_code=400, detail="Invalid report identifier.")

    result = ReportService.verify_report_integrity(db=db, report_id=report_id)
    return result

@router.get("/{inspection_id}/download")
def download_inspection_report(
    inspection_id: str,
    version: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Download official inspection report PDF.
    """
    if ".." in inspection_id or "/" in inspection_id or "\\" in inspection_id:
        raise HTTPException(status_code=400, detail="Invalid inspection identifier.")

    query = db.query(GeneratedReport).filter(GeneratedReport.inspection_id == inspection_id)
    if version:
        report = query.filter(GeneratedReport.version == version).first()
    else:
        report = query.order_by(GeneratedReport.version.desc()).first()

    if not report or not report.file_reference or not os.path.exists(report.file_reference):
        raise HTTPException(status_code=404, detail="Inspection report not found or not yet generated.")

    case = db.query(InspectionCase).filter(InspectionCase.inspection_id == inspection_id).first()
    case_num = case.case_number if case else inspection_id[:8]

    return FileResponse(
        path=report.file_reference,
        media_type="application/pdf",
        filename=f"Report_{case_num}_v{report.version}.pdf"
    )

@router.post("/{inspection_id}/generate", response_model=ReportMetadataResponse)
def generate_or_regenerate_report(
    inspection_id: str,
    force_regenerate: bool = False,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Generate or regenerate official inspection report PDF.
    """
    if current_user.role not in (UserRole.OFFICER, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions to generate inspection reports.")

    try:
        report = ReportService.generate_inspection_report(
            db=db,
            inspection_id=inspection_id,
            officer_id=current_user.user_id,
            force_regenerate=force_regenerate
        )
        return report
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{inspection_id}/versions", response_model=List[ReportMetadataResponse])
def list_report_versions(
    inspection_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):

    """
    List all generated report versions for an inspection case.
    """
    reports = db.query(GeneratedReport).filter(
        GeneratedReport.inspection_id == inspection_id
    ).order_by(GeneratedReport.version.desc()).all()

    return reports
