import pytest
import io
import cv2
import numpy as np
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models.domain import (
    InspectionCase,
    CaseStatus,
    EvidenceItem,
    EvidenceViewType,
    EvidenceProcessingStatus,
    QualityVerdict,
    ExtractedField,
    RuleFinding,
    FindingStatus,
    FindingSeverity,
    OverallDetermination,
    FieldApplicability,
    FieldStatus,
    ExtractionOrigin,
    CalibrationData,
    VisualMeasurement,
    VisualAnomaly,
    AuditEntry,
    UserRole
)
from app.core.security import create_access_token
from app.audit.hasher import compute_sha256_bytes
from app.services.rule_engine_service import ComplianceEvaluationService
from app.services.normalization_service import NormalizationService
from app.services.report_service import ReportService
from app.services.audit_service import AuditService
from tests.fixtures.test_data import db_session, create_synthetic_image

def get_auth_headers(role: str = "OFFICER", user_id: str = "OFFICER-IND-1001"):
    token = create_access_token(data={"sub": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}

def populate_all_mandatory_fields(db: Session, inspection_id: str, evidence_id: str, overrides: dict = None):
    defaults = {
        "commodity_name": ("Organic Atta", "Organic Atta", None),
        "net_quantity": ("500 g", "500.0", "g"),
        "mrp": ("Rs 100.00", "100.00", "INR"),
        "unit_sale_price": ("Rs 0.20 / g", "0.20", "INR/g"),
        "manufacturer": ("ABC Foods Ltd, Mumbai 400001", "ABC Foods Ltd", None),
        "country_of_origin": ("India", "India", None),
        "consumer_care": ("care@abcfoods.com", "care@abcfoods.com", None),
        "manufacture_date": ("08/2026", "08/2026", None)
    }
    if overrides:
        defaults.update(overrides)

    for fname, (raw, norm, unit) in defaults.items():
        if raw is not None:
            f = ExtractedField(
                field_id=f"f-{fname}-{inspection_id}",
                inspection_id=inspection_id,
                source_evidence_id=evidence_id,
                field_name=fname,
                raw_value=raw,
                normalized_value=norm,
                unit=unit,
                applicability=FieldApplicability.APPLICABLE,
                field_status=FieldStatus.EXTRACTED,
                origin=ExtractionOrigin.AI
            )
            db.add(f)
    db.commit()

# ==============================================================================
# 1. EVIDENCE INGESTION FAILURE MODES
# ==============================================================================
def test_fail_01_empty_zero_byte_upload(db_session: Session):
    """Uploading a 0-byte file must be rejected gracefully with 400."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    headers = get_auth_headers()
    
    c = client.post("/api/v1/cases", json={"notes": "0-byte test"}, headers=headers).json()
    case_id = c["inspection_id"]
    
    resp = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        data={"view_type": "FRONT"},
        files={"file": ("empty.jpg", b"", "image/jpeg")},
        headers=headers
    )
    assert resp.status_code == 400
    msg = resp.json().get("message") or resp.json().get("detail", "")
    assert "empty" in msg.lower()
    app.dependency_overrides.clear()

def test_fail_02_unsupported_file_extension(db_session: Session):
    """Uploading an executable or unsupported file must be rejected with 400."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    headers = get_auth_headers()
    
    c = client.post("/api/v1/cases", json={"notes": "Unsupported file"}, headers=headers).json()
    case_id = c["inspection_id"]
    
    resp = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        data={"view_type": "FRONT"},
        files={"file": ("payload.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/x-msdownload")},
        headers=headers
    )
    assert resp.status_code == 400
    app.dependency_overrides.clear()

def test_fail_03_corrupted_image_bytes(db_session: Session):
    """Uploading corrupted image bytes must be rejected by OpenCV validation."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    headers = get_auth_headers()
    
    c = client.post("/api/v1/cases", json={"notes": "Corrupt image"}, headers=headers).json()
    case_id = c["inspection_id"]
    
    resp = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        data={"view_type": "FRONT"},
        files={"file": ("corrupt.jpg", b"NOT_AN_IMAGE_RANDOM_GARBAGE_BYTES_1234567890", "image/jpeg")},
        headers=headers
    )
    assert resp.status_code == 400
    app.dependency_overrides.clear()

# ==============================================================================
# 2. UNIT NORMALIZATION & USP ARITHMETIC HARD TESTS
# ==============================================================================
def test_fail_04_unsupported_or_ambiguous_units():
    """Unsupported units (e.g. 'boxes', 'widgets') must not normalize into valid metrology units."""
    res1 = NormalizationService.normalize_quantity("10 boxes")
    assert res1["is_valid"] is False

    res2 = NormalizationService.normalize_quantity("5 widgets")
    assert res2["is_valid"] is False

def test_fail_05_zero_and_negative_quantity_normalization():
    """Zero or negative quantities must not cause division by zero or negative USP."""
    res = NormalizationService.calculate_unit_sale_price(
        mrp_decimal=Decimal("100.00"),
        normalized_qty_decimal=Decimal("0.0"),
        base_unit="kg"
    )
    assert res["is_computable"] is False
    assert "greater than zero" in res["error"]

def test_fail_06_usp_decimal_precision_rounding():
    """USP calculation must preserve exact Decimal precision without floating point drift."""
    # ₹100 for 0.3 kg -> 100 / 0.3 = 333.33 INR / kg
    res = NormalizationService.calculate_unit_sale_price(
        mrp_decimal=Decimal("100.00"),
        normalized_qty_decimal=Decimal("0.3"),
        base_unit="kg"
    )
    assert res["is_computable"] is True
    assert res["calculated_usp"] == 333.33

# ==============================================================================
# 3. DETERMINISTIC RULE ENGINE AGGREGATION HARD TESTS
# ==============================================================================
def test_fail_07_rule_engine_fail_plus_review_yields_non_compliant(db_session: Session):
    """
    Statutory Principle: When one rule FAILS (e.g. Rule 6 missing manufacturer)
    and another rule is in REVIEW (e.g. Rule 7 PDP font height unverified),
    the aggregated determination MUST be NON_COMPLIANT (a statutory violation cannot be overridden by review).
    """
    case_id = "case-fail-plus-review"
    c = InspectionCase(inspection_id=case_id, case_number="CASE-F-PLUS-R", officer_id="OFFICER-IND-1001", status=CaseStatus.PENDING_REVIEW)
    ev = EvidenceItem(evidence_id=f"ev-{case_id}", inspection_id=case_id, original_filename="f.jpg", media_type="image/jpeg", file_reference="storage/f.jpg", sha256="a"*64, view_type=EvidenceViewType.FRONT)
    db_session.add_all([c, ev])
    db_session.commit()

    # All fields except manufacturer -> Rule 4 FAILS
    populate_all_mandatory_fields(db_session, case_id, f"ev-{case_id}", overrides={"manufacturer": (None, None, None)})
    
    # Missing PDP area -> Rule 7 in REVIEW
    meas = VisualMeasurement(
        measurement_id=f"m-{case_id}",
        inspection_id=case_id,
        evidence_id=f"ev-{case_id}",
        target_text="500 g",
        character_type="NUMERAL",
        declaration_method="NORMAL_PRINT",
        pdp_area_cm2=None, # Missing PDP area -> REVIEW
        pixel_value=20.0,
        physical_value=2.0,
        status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    eval_svc = ComplianceEvaluationService(db_session)
    res = eval_svc.evaluate_inspection(case_id)
    assert res["overall_determination"] == OverallDetermination.NON_COMPLIANT

def test_fail_08_rule7_font_height_exact_boundaries(db_session: Session):
    """
    Test Rule 7 Table 1 boundary condition:
    For PDP 40 cm², Numeral, Normal print -> statutory minimum is 1.5mm.
    1.49mm MUST FAIL.
    1.50mm MUST PASS.
    """
    # Boundary Fail (1.49mm)
    case_id_fail = "case-r7-boundary-fail"
    c1 = InspectionCase(inspection_id=case_id_fail, case_number="CASE-R7-149", officer_id="OFFICER-IND-1001")
    ev1 = EvidenceItem(evidence_id=f"ev-{case_id_fail}", inspection_id=case_id_fail, original_filename="f.jpg", media_type="image/jpeg", file_reference="storage/f.jpg", sha256="b"*64, view_type=EvidenceViewType.FRONT)
    db_session.add_all([c1, ev1])
    db_session.commit()
    populate_all_mandatory_fields(db_session, case_id_fail, f"ev-{case_id_fail}")
    meas1 = VisualMeasurement(
        measurement_id=f"m-{case_id_fail}", inspection_id=case_id_fail, evidence_id=f"ev-{case_id_fail}",
        target_text="50g", character_type="NUMERAL", declaration_method="NORMAL_PRINT",
        pdp_area_cm2=40.0, pixel_value=14.9, physical_value=1.49, status="MEASURED"
    )
    db_session.add(meas1)
    db_session.commit()

    # Boundary Pass (1.50mm)
    case_id_pass = "case-r7-boundary-pass"
    c2 = InspectionCase(inspection_id=case_id_pass, case_number="CASE-R7-150", officer_id="OFFICER-IND-1001")
    ev2 = EvidenceItem(evidence_id=f"ev-{case_id_pass}", inspection_id=case_id_pass, original_filename="f.jpg", media_type="image/jpeg", file_reference="storage/f.jpg", sha256="c"*64, view_type=EvidenceViewType.FRONT)
    db_session.add_all([c2, ev2])
    db_session.commit()
    populate_all_mandatory_fields(db_session, case_id_pass, f"ev-{case_id_pass}")
    meas2 = VisualMeasurement(
        measurement_id=f"m-{case_id_pass}", inspection_id=case_id_pass, evidence_id=f"ev-{case_id_pass}",
        target_text="50g", character_type="NUMERAL", declaration_method="NORMAL_PRINT",
        pdp_area_cm2=40.0, pixel_value=15.0, physical_value=1.50, status="MEASURED"
    )
    db_session.add(meas2)
    db_session.commit()

    eval_svc = ComplianceEvaluationService(db_session)
    res1 = eval_svc.evaluate_inspection(case_id_fail)
    finding1 = next(f for f in res1["findings"] if f.rule_id == "RULE-FONT-HEIGHT-MINIMUM")
    assert finding1.status == FindingStatus.FAIL

    res2 = eval_svc.evaluate_inspection(case_id_pass)
    finding2 = next(f for f in res2["findings"] if f.rule_id == "RULE-FONT-HEIGHT-MINIMUM")
    assert finding2.status == FindingStatus.PASS

# ==============================================================================
# 4. FINALISATION & MANUAL CORRECTION SAFETY TESTS
# ==============================================================================
def test_fail_09_finalisation_blocked_without_officer_decision(db_session: Session):
    """Attempting to finalise a case without officer_decision must return 400/422."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    headers = get_auth_headers()

    c = client.post("/api/v1/cases", json={"notes": "Finalise test"}, headers=headers).json()
    case_id = c["inspection_id"]

    resp = client.post(
        f"/api/v1/cases/{case_id}/finalize",
        json={"officer_decision": "", "officer_remarks": "Some remarks"},
        headers=headers
    )
    assert resp.status_code in [400, 422]
    app.dependency_overrides.clear()

def test_fail_10_correction_on_finalised_case_blocked(db_session: Session):
    """Modifying/correcting declarations on an already FINALISED case must be blocked with 400."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    headers = get_auth_headers()

    case_id = "case-finalised-immutable"
    c = InspectionCase(
        inspection_id=case_id,
        case_number="CASE-FIN-IMMUT",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.FINALISED,
        overall_determination=OverallDetermination.COMPLIANT,
        officer_decision="COMPLIANT"
    )
    f = ExtractedField(field_id=f"f-{case_id}", inspection_id=case_id, field_name="mrp", normalized_value="100.00", unit="INR")
    db_session.add_all([c, f])
    db_session.commit()

    resp = client.post(
        f"/api/v1/cases/{case_id}/fields/f-{case_id}/correct",
        json={"corrected_value": "120.00", "reason": "Post-finalisation attempt"},
        headers=headers
    )
    assert resp.status_code in [400, 403, 409]
    app.dependency_overrides.clear()

# ==============================================================================
# 5. REPORT INTEGRITY & AUTHENTICATION HARD TESTS
# ==============================================================================
def test_fail_11_tampered_report_bytes_detected(db_session: Session):
    """Modifying report bytes on disk causes verify_report to strictly return INTEGRITY_MISMATCH."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    headers = get_auth_headers()

    # Create & finalise case
    case_id = "case-tamper-test"
    c = InspectionCase(
        inspection_id=case_id,
        case_number="CASE-TAMPER",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.FINALISED,
        overall_determination=OverallDetermination.COMPLIANT,
        officer_decision="COMPLIANT",
        officer_remarks="Tamper test"
    )
    db_session.add(c)
    db_session.commit()

    # Generate report
    rep = ReportService.generate_inspection_report(db_session, case_id, "OFFICER-IND-1001")
    report_id = rep.report_id

    # Tamper with file
    with open(rep.file_reference, "ab") as f:
        f.write(b"\n%TAMPERED_MALICIOUS_INJECTION%")

    # Verify integrity
    ver_resp = client.get(f"/api/v1/reports/{report_id}/verify")
    assert ver_resp.status_code == 200
    assert ver_resp.json()["integrity_status"] == "INTEGRITY_MISMATCH"
    app.dependency_overrides.clear()

def test_fail_12_expired_jwt_token_rejection(db_session: Session):
    """Expired JWT token must be rejected with 401 Unauthorized."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    # Token expired 1 hour ago
    expired_token = create_access_token(
        data={"sub": "OFFICER-IND-1001", "role": "OFFICER"},
        expires_delta=timedelta(hours=-1)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}

    resp = client.get("/api/v1/cases", headers=headers)
    assert resp.status_code == 401
    app.dependency_overrides.clear()
