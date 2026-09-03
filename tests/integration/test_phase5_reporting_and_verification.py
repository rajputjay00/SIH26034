import pytest
import os
import sys
import hashlib
from datetime import datetime, timezone
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from tests.fixtures.test_data import db_session, create_synthetic_image
from app.main import app
from app.models.domain import (
    InspectionCase,
    EvidenceItem,
    EvidenceViewType,
    EvidenceProcessingStatus,
    QualityVerdict,
    ExtractedField,
    ExtractionOrigin,
    RuleFinding,
    FindingStatus,
    FindingSeverity,
    GeneratedReport,
    CaseStatus,
    OverallDetermination
)
from app.services.case_service import CaseService
from app.services.report_service import ReportService
from app.services.audit_service import AuditService
from app.utils.errors import ValidationError

client = TestClient(app)

def create_mock_officer_token():
    from app.core.security import create_access_token
    return create_access_token(data={"sub": "OFFICER-SYS", "role": "OFFICER"})

def setup_case_with_data(db_session, case_status=CaseStatus.PENDING_REVIEW):
    case = CaseService(db_session).create_case(officer_id="OFFICER-SYS")
    case.status = case_status

    # Add evidence
    img_bytes = create_synthetic_image(with_coin=True)
    ev_path = os.path.join("storage", "evidence", case.inspection_id)
    os.makedirs(ev_path, exist_ok=True)
    file_path = os.path.join(ev_path, "front.jpg")
    with open(file_path, "wb") as f:
        f.write(img_bytes)

    ev_sha = hashlib.sha256(img_bytes).hexdigest()
    ev = EvidenceItem(
        evidence_id="ev-" + case.inspection_id[:8],
        inspection_id=case.inspection_id,
        original_filename="front.jpg",
        media_type="image/jpeg",
        file_reference=file_path,
        sha256=ev_sha,
        view_type=EvidenceViewType.FRONT,
        processing_status=EvidenceProcessingStatus.OCR_COMPLETE,
        quality_verdict=QualityVerdict.PASS

    )
    db_session.add(ev)

    # Add fields
    db_session.add(ExtractedField(
        inspection_id=case.inspection_id, field_name="commodity_name",
        raw_value="Almond Cookies", normalized_value="Almond Cookies", origin=ExtractionOrigin.AI
    ))
    db_session.add(ExtractedField(
        inspection_id=case.inspection_id, field_name="mrp",
        raw_value="150.00", normalized_value="150.00", unit="INR", origin=ExtractionOrigin.AI
    ))

    # Add findings
    db_session.add(RuleFinding(
        inspection_id=case.inspection_id, rule_id="RULE-DECL-COMMODITY-NAME",
        rule_pack_version="v1.0.0", title="Commodity Name Check",
        legal_citation="Rule 6(1)(a)", status=FindingStatus.PASS,
        severity=FindingSeverity.HIGH, message="Commodity name present."
    ))

    db_session.commit()
    db_session.refresh(case)
    return case, file_path, ev_sha

# TEST 1: Generate report successfully (PDF exists and is non-empty)
def test_01_generate_report_successfully(db_session):
    case, _, _ = setup_case_with_data(db_session)
    report = ReportService.generate_inspection_report(
        db=db_session,
        inspection_id=case.inspection_id,
        officer_id="OFFICER-SYS"
    )
    assert report is not None
    assert report.status == "GENERATED"
    assert report.file_reference is not None
    assert os.path.exists(report.file_reference)
    assert os.path.getsize(report.file_reference) > 1000

# TEST 2: Report SHA-256 (Stored hash == SHA-256 of exact PDF bytes)
def test_02_report_sha256_matches_pdf_bytes(db_session):
    case, _, _ = setup_case_with_data(db_session)
    report = ReportService.generate_inspection_report(
        db=db_session,
        inspection_id=case.inspection_id,
        officer_id="OFFICER-SYS"
    )
    with open(report.file_reference, "rb") as f:
        actual_bytes = f.read()
    computed_hash = hashlib.sha256(actual_bytes).hexdigest()

    assert report.sha256 == computed_hash
    assert len(report.sha256) == 64

# TEST 3: Evidence SHA-256 (Stored evidence hash == SHA-256 of original bytes)
def test_03_evidence_sha256_integrity(db_session):
    case, file_path, ev_sha = setup_case_with_data(db_session)
    ev = db_session.query(EvidenceItem).filter(EvidenceItem.inspection_id == case.inspection_id).first()

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    assert ev.sha256 == ev_sha
    assert hashlib.sha256(file_bytes).hexdigest() == ev.sha256

# TEST 4: Report verification (VALID when bytes match stored hash)
def test_04_report_verification_valid(db_session):
    case, _, _ = setup_case_with_data(db_session)
    report = ReportService.generate_inspection_report(
        db=db_session,
        inspection_id=case.inspection_id,
        officer_id="OFFICER-SYS"
    )
    verification = ReportService.verify_report_integrity(db=db_session, report_id=report.report_id)

    assert verification["exists"] is True
    assert verification["integrity_status"] == "VALID"
    assert verification["stored_hash"] == report.sha256
    assert verification["computed_hash"] == report.sha256
    assert "Integrity verification successful" in verification["message"]

# TEST 5: Tampered report produces INTEGRITY_MISMATCH
def test_05_tampered_report_produces_integrity_mismatch(db_session):
    case, _, _ = setup_case_with_data(db_session)
    report = ReportService.generate_inspection_report(
        db=db_session,
        inspection_id=case.inspection_id,
        officer_id="OFFICER-SYS"
    )

    # Tamper with the PDF file on disk by appending arbitrary bytes
    with open(report.file_reference, "ab") as f:
        f.write(b"TAMPERED_MALICIOUS_BYTES")

    verification = ReportService.verify_report_integrity(db=db_session, report_id=report.report_id)

    assert verification["exists"] is True
    assert verification["integrity_status"] == "INTEGRITY_MISMATCH"
    assert verification["stored_hash"] != verification["computed_hash"]
    assert "Integrity mismatch detected" in verification["message"]

# TEST 6: Missing report produces REPORT_NOT_FOUND
def test_06_missing_report_produces_not_found(db_session):
    verification = ReportService.verify_report_integrity(db=db_session, report_id="non-existent-report-uuid")

    assert verification["exists"] is False
    assert verification["integrity_status"] == "REPORT_NOT_FOUND"

# TEST 7: Report versioning (v1 remains immutable, v2 created separately)
def test_07_report_versioning_and_immutability(db_session):
    case, _, _ = setup_case_with_data(db_session)
    r_v1 = ReportService.generate_inspection_report(
        db=db_session,
        inspection_id=case.inspection_id,
        officer_id="OFFICER-SYS",
        force_regenerate=False
    )
    assert r_v1.version == 1
    v1_file = r_v1.file_reference
    v1_sha = r_v1.sha256

    # Regenerate report as version 2
    r_v2 = ReportService.generate_inspection_report(
        db=db_session,
        inspection_id=case.inspection_id,
        officer_id="OFFICER-SYS",
        force_regenerate=True
    )
    assert r_v2.version == 2
    assert r_v2.report_id != r_v1.report_id
    assert r_v2.file_reference != v1_file

    # Verify v1 still exists untouched
    assert os.path.exists(v1_file)
    with open(v1_file, "rb") as f:
        assert hashlib.sha256(f.read()).hexdigest() == v1_sha

# TEST 8: QR payload contains verification route and no sensitive payload
def test_08_qr_payload_verification():
    from reportlab.graphics.barcode import qr
    report_id = "REP-TEST-12345"
    expected_url = f"https://legalmetrix.gov.in/verify/{report_id}"
    qr_w = qr.QrCodeWidget(expected_url)

    assert qr_w.value == expected_url
    assert "password" not in qr_w.value
    assert "key" not in qr_w.value

# TEST 9: Finalisation without required review resolution is rejected
def test_09_finalisation_safeguard_rejects_unresolved_review(db_session):
    case, _, _ = setup_case_with_data(db_session)

    # Add an unresolved REVIEW finding
    db_session.add(RuleFinding(
        inspection_id=case.inspection_id, rule_id="RULE-FONT-HEIGHT-MINIMUM",
        rule_pack_version="v1.0.0", title="Font Height Check",
        legal_citation="Rule 7", status=FindingStatus.REVIEW,
        severity=FindingSeverity.LOW, message="Requires calibration."
    ))
    db_session.commit()

    case_service = CaseService(db_session)
    with pytest.raises(ValidationError) as exc:
        case_service.finalize_case(
            inspection_id=case.inspection_id,
            officer_id="OFFICER-SYS",
            officer_decision="COMPLIANT",
            officer_remarks=None,
            acknowledged_review_findings=False # Not acknowledged!
        )
    assert "unresolved REVIEW findings" in str(exc.value)

# TEST 10: Finalisation with valid officer decision succeeds
def test_10_finalisation_with_valid_officer_decision(db_session):
    case, _, _ = setup_case_with_data(db_session)
    case_service = CaseService(db_session)

    finalised_case = case_service.finalize_case(
        inspection_id=case.inspection_id,
        officer_id="OFFICER-SYS",
        officer_decision="COMPLIANT",
        officer_remarks="Packaged commodity complies with all mandatory statutory declarations.",
        acknowledged_review_findings=True
    )

    assert finalised_case.status == CaseStatus.FINALISED
    assert finalised_case.officer_decision == "COMPLIANT"
    assert finalised_case.finalized_at is not None

    # Check auto-generated report
    report = db_session.query(GeneratedReport).filter(GeneratedReport.inspection_id == case.inspection_id).first()
    assert report is not None
    assert report.version == 1

# TEST 11: Finalised report overwrite attempt rejected
def test_11_finalised_case_re_finalisation_rejected(db_session):
    case, _, _ = setup_case_with_data(db_session)
    case_service = CaseService(db_session)
    case_service.finalize_case(
        inspection_id=case.inspection_id, officer_id="OFFICER-SYS",
        officer_decision="COMPLIANT", acknowledged_review_findings=True
    )

    from app.utils.errors import InvalidStateTransitionError
    with pytest.raises(InvalidStateTransitionError):
        case_service.finalize_case(
            inspection_id=case.inspection_id, officer_id="OFFICER-SYS",
            officer_decision="NON_COMPLIANT", acknowledged_review_findings=True
        )

# TEST 12: Audit chain records report generation & finalisation
def test_12_audit_chain_tracks_reporting_events(db_session):
    case, _, _ = setup_case_with_data(db_session)
    case_service = CaseService(db_session)
    case_service.finalize_case(
        inspection_id=case.inspection_id, officer_id="OFFICER-SYS",
        officer_decision="COMPLIANT", acknowledged_review_findings=True
    )

    is_valid, total_entries, _, _ = AuditService.verify_chain(db=db_session, inspection_id=case.inspection_id)
    assert is_valid is True
    assert total_entries >= 2

    from app.models.domain import AuditEntry
    actions = [e.action for e in db_session.query(AuditEntry).filter_by(inspection_id=case.inspection_id).all()]
    assert "INSPECTION_FINALISED" in actions
    assert "REPORT_GENERATED" in actions


# TEST 13: Path traversal attempt is rejected by API
def test_13_path_traversal_protection(db_session):
    from app.core.database import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        token = create_mock_officer_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Attempt path traversal on report verify
        resp = client.get("/api/v1/reports/..%2f..%2fetc%2fpasswd/verify")
        assert resp.status_code in (400, 404)

        # Attempt path traversal on download
        resp_dl = client.get("/api/v1/reports/..%2f..%2fevidence/download", headers=headers)
        assert resp_dl.status_code in (400, 404)
    finally:
        app.dependency_overrides.clear()

# TEST 14: Unauthorized report generation access rejected
def test_14_unauthorized_report_access_rejected(db_session):
    from app.core.database import get_db
    from app.core.security import create_access_token
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        case, _, _ = setup_case_with_data(db_session)

        # Create token with REVIEWER role (only OFFICER and ADMIN can generate)
        reviewer_token = create_access_token(data={"sub": "REVIEWER-IND-2001", "role": "REVIEWER"})
        resp = client.post(
            f"/api/v1/reports/{case.inspection_id}/generate",
            headers={"Authorization": f"Bearer {reviewer_token}"}
        )
        assert resp.status_code == 403

    finally:
        app.dependency_overrides.clear()

# TEST 15: Public verification returns only safe metadata
def test_15_public_verification_returns_safe_metadata(db_session):
    from app.core.database import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        case, _, _ = setup_case_with_data(db_session)
        report = ReportService.generate_inspection_report(
            db=db_session,
            inspection_id=case.inspection_id,
            officer_id="OFFICER-SYS"
        )

        resp = client.get(f"/api/v1/reports/{report.report_id}/verify")
        assert resp.status_code == 200
        data = resp.json()

        assert data["report_id"] == report.report_id
        assert data["integrity_status"] == "VALID"
        assert data["stored_hash"] == report.sha256
        assert "file_reference" not in data
        assert "password" not in data
        assert "token" not in data
    finally:
        app.dependency_overrides.clear()

