from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, RequireRole
from app.models.domain import (
    CalibrationData,
    VisualMeasurement,
    VisualAnomaly,
    UserRole
)
from app.schemas.pydantic_models import (
    CalibrationResponse,
    VisualMeasurementResponse,
    VisualAnomalyResponse,
    UserProfile
)
from app.services.calibration_service import CalibrationService
from app.services.measurement_service import VisualMeasurementService
from app.services.anomaly_service import VisualAnomalyService

router = APIRouter(prefix="/cases", tags=["Advanced CV, Calibration & Forensics"])

# 1. Physical Reference Calibration Endpoints
@router.post("/{inspection_id}/calibration/{evidence_id}", response_model=CalibrationResponse)
def calibrate_evidence_view(
    inspection_id: str,
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(RequireRole([UserRole.ADMIN, UserRole.OFFICER]))
):
    """
    Executes OpenCV coin detection to establish physical reference calibration (standard Indian Rs 5 coin).
    """
    return CalibrationService.calibrate_evidence_image(
        db=db,
        inspection_id=inspection_id,
        evidence_id=evidence_id,
        officer_id=current_user.user_id
    )

@router.get("/{inspection_id}/calibration", response_model=List[CalibrationResponse])
def get_case_calibrations(
    inspection_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve all physical calibrations established for evidence views in an inspection case."""
    return db.query(CalibrationData).filter(CalibrationData.inspection_id == inspection_id).all()

# 2. Font & Character Height Measurement Endpoints
@router.post("/{inspection_id}/measurements/{evidence_id}", response_model=List[VisualMeasurementResponse])
def measure_evidence_fonts(
    inspection_id: str,
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(RequireRole([UserRole.ADMIN, UserRole.OFFICER]))
):
    """
    Calculates physical font heights (in mm) for OCR regions using active physical calibration.
    """
    return VisualMeasurementService.measure_evidence_fonts(
        db=db,
        inspection_id=inspection_id,
        evidence_id=evidence_id,
        officer_id=current_user.user_id
    )

@router.get("/{inspection_id}/measurements", response_model=List[VisualMeasurementResponse])
def get_case_measurements(
    inspection_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve all physical font measurements for an inspection case."""
    return db.query(VisualMeasurement).filter(VisualMeasurement.inspection_id == inspection_id).all()

# 3. Visual Sticker / Overlay Anomaly Detection Endpoints
@router.post("/{inspection_id}/visual-anomalies/{evidence_id}", response_model=List[VisualAnomalyResponse])
def detect_visual_anomalies(
    inspection_id: str,
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(RequireRole([UserRole.ADMIN, UserRole.OFFICER]))
):
    """
    Executes OpenCV anomaly detection for suspected price label stickers and overlay patches.
    Visual suspicion signals require authoritative officer verification.
    """
    return VisualAnomalyService.detect_visual_anomalies(
        db=db,
        inspection_id=inspection_id,
        evidence_id=evidence_id,
        officer_id=current_user.user_id
    )

@router.get("/{inspection_id}/visual-anomalies", response_model=List[VisualAnomalyResponse])
def get_case_visual_anomalies(
    inspection_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieve all visual anomaly suspicion signals detected for an inspection case."""
    return db.query(VisualAnomaly).filter(VisualAnomaly.inspection_id == inspection_id).all()
