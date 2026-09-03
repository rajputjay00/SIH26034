import pytest
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from tests.fixtures.test_data import db_session, create_synthetic_image
from app.models.domain import (
    InspectionCase,
    EvidenceItem,
    EvidenceViewType,
    CalibrationData,
    CalibrationStatus,
    VisualMeasurement,
    VisualAnomaly,
    ExtractedField,
    ExtractionOrigin,
    FieldStatus,
    FieldApplicability,
    FindingStatus,
    OverallDetermination
)
from app.services.case_service import CaseService
from app.services.evidence_service import EvidenceService
from app.services.calibration_service import CalibrationService
from app.services.measurement_service import VisualMeasurementService
from app.services.anomaly_service import VisualAnomalyService
from app.services.rule_engine_service import ComplianceEvaluationService

def test_coin_reference_calibration_success(db_session):
    """Test standard Indian ₹5 coin detection and scale calculation."""
    case_service = CaseService(db_session)
    case = case_service.create_case(officer_id="OFFICER-001")

    evidence_service = EvidenceService(db_session)
    coin_img_bytes = create_synthetic_image(with_coin=True)
    evidence = evidence_service.ingest_evidence(
        inspection_id=case.inspection_id,
        file_bytes=coin_img_bytes,
        filename="front_coin_sample.jpg",
        content_type="image/jpeg",
        view_type=EvidenceViewType.FRONT,
        officer_id="OFFICER-001"
    )

    calib = CalibrationService.calibrate_evidence_image(
        db=db_session,
        inspection_id=case.inspection_id,
        evidence_id=evidence.evidence_id,
        officer_id="OFFICER-001"
    )

    assert calib.status == CalibrationStatus.CALIBRATED
    assert calib.mm_per_pixel is not None
    assert 0.10 <= calib.mm_per_pixel <= 0.50
    assert calib.confidence >= 0.60
    assert calib.bounding_geometry_json is not None

def test_coin_calibration_unavailable_when_no_coin(db_session):
    """Test calibration fails gracefully when no reference coin is present in the image."""
    case_service = CaseService(db_session)
    case = case_service.create_case(officer_id="OFFICER-001")

    evidence_service = EvidenceService(db_session)
    no_coin_bytes = create_synthetic_image(with_coin=False)
    evidence = evidence_service.ingest_evidence(
        inspection_id=case.inspection_id,
        file_bytes=no_coin_bytes,
        filename="front_no_coin.jpg",
        content_type="image/jpeg",
        view_type=EvidenceViewType.FRONT,
        officer_id="OFFICER-001"
    )

    calib = CalibrationService.calibrate_evidence_image(
        db=db_session,
        inspection_id=case.inspection_id,
        evidence_id=evidence.evidence_id,
        officer_id="OFFICER-001"
    )

    assert calib.status == CalibrationStatus.CALIBRATION_UNAVAILABLE
    assert calib.mm_per_pixel is None

def test_font_measurement_with_and_without_calibration(db_session):
    """Test physical font measurement with active calibration vs fallback without calibration."""
    case_service = CaseService(db_session)
    case = case_service.create_case(officer_id="OFFICER-001")

    evidence_service = EvidenceService(db_session)
    img_bytes = create_synthetic_image(with_coin=True)
    evidence = evidence_service.ingest_evidence(
        inspection_id=case.inspection_id,
        file_bytes=img_bytes,
        filename="sample_measure.jpg",
        content_type="image/jpeg",
        view_type=EvidenceViewType.FRONT,
        officer_id="OFFICER-001"
    )
    # Process OCR
    evidence_service.process_evidence(evidence.evidence_id, officer_id="OFFICER-001")

    # 1. Measure without calibration
    uncalibrated_meas = VisualMeasurementService.measure_evidence_fonts(
        db=db_session,
        inspection_id=case.inspection_id,
        evidence_id=evidence.evidence_id,
        officer_id="OFFICER-001"
    )
    assert len(uncalibrated_meas) > 0
    for m in uncalibrated_meas:
        assert m.status == "CALIBRATION_REQUIRED"
        assert m.physical_value is None

    # 2. Calibrate coin
    CalibrationService.calibrate_evidence_image(
        db=db_session,
        inspection_id=case.inspection_id,
        evidence_id=evidence.evidence_id,
        officer_id="OFFICER-001"
    )

    # 3. Measure with calibration
    calibrated_meas = VisualMeasurementService.measure_evidence_fonts(
        db=db_session,
        inspection_id=case.inspection_id,
        evidence_id=evidence.evidence_id,
        officer_id="OFFICER-001"
    )
    assert len(calibrated_meas) > 0
    for m in calibrated_meas:
        assert m.status == "MEASURED"
        assert m.physical_value is not None
        assert m.physical_value > 0

def test_sticker_overlay_anomaly_detection_and_rule_integration(db_session):
    """Test that sticker anomaly produces visual suspicion / REVIEW and NEVER NON_COMPLIANT by itself."""
    case_service = CaseService(db_session)
    case = case_service.create_case(officer_id="OFFICER-001")

    evidence_service = EvidenceService(db_session)
    sticker_img_bytes = create_synthetic_image(with_sticker=True)
    evidence = evidence_service.ingest_evidence(
        inspection_id=case.inspection_id,
        file_bytes=sticker_img_bytes,
        filename="sample_sticker.jpg",
        content_type="image/jpeg",
        view_type=EvidenceViewType.FRONT,
        officer_id="OFFICER-001"
    )

    anomalies = VisualAnomalyService.detect_visual_anomalies(
        db=db_session,
        inspection_id=case.inspection_id,
        evidence_id=evidence.evidence_id,
        officer_id="OFFICER-001"
    )
    assert len(anomalies) > 0
    assert anomalies[0].anomaly_type == "SUSPECTED_OVERLAY"
    assert anomalies[0].status == "DETECTED"

    # Evaluate compliance rules
    # Populate compliant fields except the sticker suspicion
    fields = [
        ExtractedField(inspection_id=case.inspection_id, field_name="commodity_name", raw_value="Biscuits", normalized_value="Biscuits", origin=ExtractionOrigin.AI),
        ExtractedField(inspection_id=case.inspection_id, field_name="net_quantity", raw_value="500 g", normalized_value="0.5000", unit="kg", origin=ExtractionOrigin.AI),
        ExtractedField(inspection_id=case.inspection_id, field_name="mrp", raw_value="MRP Rs. 199.00", normalized_value="199.00", unit="INR", origin=ExtractionOrigin.AI),
        ExtractedField(inspection_id=case.inspection_id, field_name="manufacturer", raw_value="Mfr by ABC Foods", normalized_value="ABC Foods", origin=ExtractionOrigin.AI),
        ExtractedField(inspection_id=case.inspection_id, field_name="consumer_care", raw_value="Tel 1800", normalized_value="1800", origin=ExtractionOrigin.AI),
        ExtractedField(inspection_id=case.inspection_id, field_name="manufacture_date", raw_value="08/2026", normalized_value="08/2026", origin=ExtractionOrigin.AI),
    ]
    db_session.add_all(fields)
    db_session.commit()

    rule_service = ComplianceEvaluationService(db_session)
    eval_result = rule_service.evaluate_inspection(case.inspection_id, officer_id="OFFICER-001")

    sticker_finding = next((f for f in eval_result["findings"] if f.rule_id == "RULE-OVERLAY-STICKER-FLAG"), None)
    assert sticker_finding is not None
    # CRITICAL: Must be REVIEW, never FAIL
    assert sticker_finding.status == FindingStatus.REVIEW
    assert "Visual anomaly detected" in sticker_finding.message
    # Overall determination cannot be NON_COMPLIANT solely from sticker suspicion (it should be REQUIRES_REVIEW)
    assert eval_result["overall_determination"] == OverallDetermination.REQUIRES_REVIEW


def test_multi_view_calibration_isolation(db_session):
    """Test that calibration on Front view is isolated and does not silently calibrate Back view."""
    case_service = CaseService(db_session)
    case = case_service.create_case(officer_id="OFFICER-001")

    evidence_service = EvidenceService(db_session)
    # Front with coin, Back without coin
    front_bytes = create_synthetic_image(with_coin=True)
    back_bytes = create_synthetic_image(with_coin=False)

    front_ev = evidence_service.ingest_evidence(
        inspection_id=case.inspection_id,
        file_bytes=front_bytes,
        filename="front.jpg",
        content_type="image/jpeg",
        view_type=EvidenceViewType.FRONT,
        officer_id="OFFICER-001"
    )
    back_ev = evidence_service.ingest_evidence(
        inspection_id=case.inspection_id,
        file_bytes=back_bytes,
        filename="back.jpg",
        content_type="image/jpeg",
        view_type=EvidenceViewType.BACK,
        officer_id="OFFICER-001"
    )

    # Calibrate Front
    calib_front = CalibrationService.calibrate_evidence_image(db_session, case.inspection_id, front_ev.evidence_id)
    assert calib_front.status == CalibrationStatus.CALIBRATED

    # Calibrate Back
    calib_back = CalibrationService.calibrate_evidence_image(db_session, case.inspection_id, back_ev.evidence_id)
    assert calib_back.status == CalibrationStatus.CALIBRATION_UNAVAILABLE

    # Ensure measurements on Back view remain uncalibrated
    evidence_service.process_evidence(back_ev.evidence_id, officer_id="OFFICER-001")
    back_measurements = VisualMeasurementService.measure_evidence_fonts(db_session, case.inspection_id, back_ev.evidence_id)
    for m in back_measurements:
        assert m.status == "CALIBRATION_REQUIRED"
        assert m.physical_value is None

