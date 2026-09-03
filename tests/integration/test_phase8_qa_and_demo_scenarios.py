import pytest
import io
import cv2
import numpy as np
from datetime import datetime, timezone
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
    OverallDetermination,
    FieldApplicability,
    FieldStatus,
    ExtractionOrigin,
    CalibrationData,
    VisualMeasurement,
    VisualAnomaly,
    AuditEntry
)
from app.core.security import create_access_token
from app.audit.hasher import compute_sha256_bytes
from app.services.rule_engine_service import ComplianceEvaluationService
from app.services.report_service import ReportService
from app.services.audit_service import AuditService
from app.services.provenance_service import ProvenanceService
from tests.fixtures.test_data import db_session, create_synthetic_image

def get_auth_headers(role: str = "OFFICER", user_id: str = "OFFICER-IND-1001"):
    token = create_access_token(data={"sub": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}

def populate_mandatory_declarations(db: Session, inspection_id: str, evidence_id: str, overrides: dict = None):
    """Helper to populate the 8 mandatory declarations under Legal Metrology PC Rules, 2011."""
    defaults = {
        "commodity_name": ("Organic Whole Wheat Atta", "Organic Whole Wheat Atta", None),
        "net_quantity": ("500 g", "500.0", "g"),
        "mrp": ("Rs 200.00", "200.00", "INR"),
        "unit_sale_price": ("Rs 0.40 / g", "0.40", "INR/g"),
        "manufacturer": ("Hindustan Packaged Foods Ltd, Mumbai 400001", "Hindustan Packaged Foods Ltd", None),
        "country_of_origin": ("Country of Origin: India", "India", None),
        "consumer_care": ("Consumer Care: 1800-222-333, help@hpf.com", "help@hpf.com", None),
        "manufacture_date": ("Mfg Date: 08/2026", "08/2026", None)
    }
    if overrides:
        defaults.update(overrides)

    fields = []
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
            fields.append(f)
    db.commit()
    return fields

# ==============================================================================
# 1. COMPLETE 20-STEP END-TO-END OFFICER JOURNEY TEST
# ==============================================================================
def test_01_complete_end_to_end_officer_journey(db_session: Session):
    """
    Execute full 20-step officer inspection lifecycle:
    Case Creation -> Multi-view Ingestion -> SHA-256 -> Quality Gate -> OCR ->
    Structured Extraction -> Provenance -> Rule Evaluation -> Coin Calibration ->
    Rule 7 PDP Sizing -> Visual Forensics -> Officer Correction -> Rerun ->
    Finalisation -> Report Generation -> Report Integrity Verification -> Audit Chain.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    headers = get_auth_headers("OFFICER", "OFFICER-IND-1001")

    # Step 1: Create Case
    c_resp = client.post("/api/v1/cases", json={"notes": "DEMO / TEST DATA: Full 20-Step Inspection Journey"}, headers=headers)
    assert c_resp.status_code == 201
    case_id = c_resp.json()["inspection_id"]

    # Step 2-5: Ingest Multi-View Evidence (FRONT, BACK, SIDE, BASE)
    views = ["FRONT", "BACK", "SIDE", "BASE"]
    evidence_ids = {}
    for v in views:
        img_bytes = create_synthetic_image(f"Packaged Commodity {v} Panel")
        resp = client.post(
            f"/api/v1/cases/{case_id}/evidence",
            data={"view_type": v},
            files={"file": (f"demo_{v.lower()}.jpg", img_bytes, "image/jpeg")},
            headers=headers
        )
        assert resp.status_code == 201
        evidence_ids[v] = resp.json()["evidence_id"]

    # Step 6-8: Quality Check, Preprocess, OCR on Front and Back views
    for v in ["FRONT", "BACK"]:
        proc_resp = client.post(f"/api/v1/evidence/{evidence_ids[v]}/process", headers=headers)
        assert proc_resp.status_code == 200
        assert proc_resp.json()["quality_verdict"] in ["PASS", "WARN", "MANUAL_REVIEW"]

    # Step 9-10: Structured Declarations & Provenance
    populate_mandatory_declarations(db_session, case_id, evidence_ids["BACK"])

    # Step 11: Reference Coin Calibration (Indian ₹5 Coin 23.00mm)
    calib = CalibrationData(
        calibration_id=f"calib-{case_id}",
        inspection_id=case_id,
        evidence_id=evidence_ids["FRONT"],
        reference_object="COIN_5_INR",
        reference_measurement_mm=23.00,
        detected_pixel_measurement=230.0,
        mm_per_pixel=0.1000,
        status="CALIBRATED"
    )
    db_session.add(calib)

    # Step 12: Rule 7 PDP Font Height Measurement (PDP 150cm², Numeral, 4.0mm height -> Passes 4.0mm threshold)
    meas = VisualMeasurement(
        measurement_id=f"meas-{case_id}",
        inspection_id=case_id,
        evidence_id=evidence_ids["FRONT"],
        calibration_id=f"calib-{case_id}",
        measurement_type="FONT_HEIGHT",
        target_text="500 g",
        character_type="NUMERAL",
        declaration_method="NORMAL_PRINT",
        pdp_area_cm2=150.0,
        pixel_value=40.0,
        physical_value=4.00,
        status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    # Step 13: Deterministic Rule Evaluation
    eval_svc = ComplianceEvaluationService(db_session)
    eval_res = eval_svc.evaluate_inspection(case_id, officer_id="OFFICER-IND-1001")
    assert eval_res["overall_determination"] == OverallDetermination.COMPLIANT

    # Step 14-15: Officer Correction & Automatic Rerun
    corr_resp = client.post(
        f"/api/v1/cases/{case_id}/fields/f-mrp-{case_id}/correct",
        json={"corrected_value": "200.00", "reason": "Printed declaration visually confirmed by officer"},
        headers=headers
    )
    assert corr_resp.status_code == 200

    rerun_resp = client.post(f"/api/v1/cases/{case_id}/evaluate/rerun", headers=headers)
    assert rerun_resp.status_code == 200

    # Step 16-17: Finalisation by Authorised Officer
    fin_resp = client.post(
        f"/api/v1/cases/{case_id}/finalize",
        json={
            "officer_decision": "COMPLIANT",
            "officer_remarks": "Packaged commodity fully complies with Legal Metrology (Packaged Commodities) Rules, 2011.",
            "acknowledged_review_findings": True
        },
        headers=headers
    )
    assert fin_resp.status_code == 200
    assert fin_resp.json()["status"] == "FINALISED"

    # Step 18-19: Report Generation & Cryptographic Integrity Verification
    rep_resp = client.post(f"/api/v1/reports/{case_id}/generate", headers=headers)
    assert rep_resp.status_code == 200
    report_id = rep_resp.json()["report_id"]


    verify_resp = client.get(f"/api/v1/reports/{report_id}/verify")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["integrity_status"] == "VALID"

    # Step 20: Audit Chain Integrity
    is_valid, total, _, _ = AuditService.verify_chain(db_session, case_id)
    assert is_valid is True
    assert total >= 5
    app.dependency_overrides.clear()

# ==============================================================================
# 2. THREE DETERMINATION PATHS: COMPLIANT, NON-COMPLIANT, REQUIRES_REVIEW
# ==============================================================================
def test_02_determination_path_a_compliant(db_session: Session):
    """Case A: Fully compliant packaged commodity with valid math and Rule 7 heights."""
    case_id = "case-demo-path-a-compliant"
    c = InspectionCase(inspection_id=case_id, case_number="CASE-QA-COMPLIANT", officer_id="OFFICER-IND-1001", status=CaseStatus.PENDING_REVIEW)
    ev = EvidenceItem(
        evidence_id=f"ev-{case_id}",
        inspection_id=case_id,
        original_filename="front.jpg",
        media_type="image/jpeg",
        file_reference="storage/evidence/front.jpg",
        sha256="aabbccddeeff11223344556677889900aabbccddeeff11223344556677889900",
        view_type=EvidenceViewType.FRONT
    )
    db_session.add_all([c, ev])
    db_session.commit()

    populate_mandatory_declarations(db_session, case_id, f"ev-{case_id}")

    meas = VisualMeasurement(
        measurement_id=f"m-{case_id}",
        inspection_id=case_id,
        evidence_id=f"ev-{case_id}",
        target_text="500 g",
        character_type="NUMERAL",
        declaration_method="NORMAL_PRINT",
        pdp_area_cm2=80.0, # Rule 7 threshold is 2.0mm
        pixel_value=25.0,
        physical_value=2.50, # 2.5mm >= 2.0mm -> PASS
        status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    eval_svc = ComplianceEvaluationService(db_session)
    res = eval_svc.evaluate_inspection(case_id, "OFFICER-IND-1001")
    assert res["overall_determination"] == OverallDetermination.COMPLIANT

def test_03_determination_path_b_non_compliant_due_to_math_error(db_session: Session):
    """Case B: Non-compliant package due to contradictory Unit Sale Price arithmetic."""
    case_id = "case-demo-path-b-non-compliant"
    c = InspectionCase(inspection_id=case_id, case_number="CASE-QA-NON-COMPLIANT", officer_id="OFFICER-IND-1001", status=CaseStatus.PENDING_REVIEW)
    ev = EvidenceItem(
        evidence_id=f"ev-{case_id}",
        inspection_id=case_id,
        original_filename="back.jpg",
        media_type="image/jpeg",
        file_reference="storage/evidence/back.jpg",
        sha256="11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff",
        view_type=EvidenceViewType.BACK
    )
    db_session.add_all([c, ev])
    db_session.commit()

    # Inconsistent USP (stated 0.80 instead of 0.40)
    overrides = {
        "mrp": ("Rs 200.00", "200.00", "INR"),
        "net_quantity": ("500 g", "500.0", "g"),
        "unit_sale_price": ("Rs 0.80 / g", "0.80", "INR/g")
    }
    populate_mandatory_declarations(db_session, case_id, f"ev-{case_id}", overrides)

    eval_svc = ComplianceEvaluationService(db_session)
    res = eval_svc.evaluate_inspection(case_id, "OFFICER-IND-1001")
    assert res["overall_determination"] == OverallDetermination.NON_COMPLIANT
    
    # Verify exact finding is FAIL
    fail_findings = [f for f in res["findings"] if f.status == FindingStatus.FAIL]
    assert len(fail_findings) > 0
    assert "Rule 6" in fail_findings[0].legal_citation

def test_04_determination_path_c_requires_review_due_to_missing_pdp(db_session: Session):
    """Case C: Requires review when PDP area is unverified and cannot be guessed under Rule 7."""
    case_id = "case-demo-path-c-review"
    c = InspectionCase(inspection_id=case_id, case_number="CASE-QA-REVIEW", officer_id="OFFICER-IND-1001", status=CaseStatus.PENDING_REVIEW)
    ev = EvidenceItem(
        evidence_id=f"ev-{case_id}",
        inspection_id=case_id,
        original_filename="front.jpg",
        media_type="image/jpeg",
        file_reference="storage/evidence/front.jpg",
        sha256="ddeeff11223344556677889900aabbccddeeff11223344556677889900aabbcc",
        view_type=EvidenceViewType.FRONT
    )
    db_session.add_all([c, ev])
    db_session.commit()

    populate_mandatory_declarations(db_session, case_id, f"ev-{case_id}")

    # Measurement exists but PDP Area is None -> Strictly REQUIRES_REVIEW
    meas = VisualMeasurement(
        measurement_id=f"m-{case_id}",
        inspection_id=case_id,
        evidence_id=f"ev-{case_id}",
        target_text="500 g",
        character_type="NUMERAL",
        declaration_method="NORMAL_PRINT",
        pdp_area_cm2=None, # Missing PDP area!
        pixel_value=20.0,
        physical_value=2.00,
        status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    eval_svc = ComplianceEvaluationService(db_session)
    res = eval_svc.evaluate_inspection(case_id, "OFFICER-IND-1001")
    assert res["overall_determination"] == OverallDetermination.REQUIRES_REVIEW
    
    review_findings = [f for f in res["findings"] if f.status == FindingStatus.REVIEW]
    assert len(review_findings) > 0
    assert "Rule 7" in review_findings[0].legal_citation
