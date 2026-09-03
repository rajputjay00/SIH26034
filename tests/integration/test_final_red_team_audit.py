import pytest
import io
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
    ExtractedField,
    RuleFinding,
    FindingStatus,
    OverallDetermination,
    UserRole
)
from app.core.security import create_access_token
from app.services.report_service import ReportService
from app.services.audit_service import AuditService
from tests.fixtures.test_data import db_session, create_synthetic_image

def get_auth_headers(role: str = "OFFICER", user_id: str = "OFFICER-IND-1001"):
    token = create_access_token(data={"sub": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}

# ==============================================================================
# 1. FINALISE-LOCK RED TEAM (MUTATION MATRIX ON FINALISED CASES)
# ==============================================================================
def test_redteam_01_finalised_case_blocks_evidence_upload(db_session: Session):
    """Attempting to upload evidence to a FINALISED case must return 400."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    headers = get_auth_headers()

    case_id = "case-fin-lock-01"
    c = InspectionCase(
        inspection_id=case_id,
        case_number="CASE-LOCK-01",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.FINALISED,
        overall_determination=OverallDetermination.COMPLIANT,
        officer_decision="COMPLIANT"
    )
    db_session.add(c)
    db_session.commit()

    img_bytes = create_synthetic_image()
    resp = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        data={"view_type": "FRONT"},
        files={"file": ("front.jpg", img_bytes, "image/jpeg")},
        headers=headers
    )
    assert resp.status_code == 400
    app.dependency_overrides.clear()

def test_redteam_02_finalised_case_blocks_re_extraction(db_session: Session):
    """Attempting to trigger structured field extraction on a FINALISED case must return 400."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    headers = get_auth_headers()

    case_id = "case-fin-lock-02"
    c = InspectionCase(
        inspection_id=case_id,
        case_number="CASE-LOCK-02",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.FINALISED,
        overall_determination=OverallDetermination.COMPLIANT,
        officer_decision="COMPLIANT"
    )
    db_session.add(c)
    db_session.commit()

    resp = client.post(f"/api/v1/cases/{case_id}/extract", headers=headers)
    assert resp.status_code == 400
    app.dependency_overrides.clear()

def test_redteam_03_finalised_case_blocks_field_correction(db_session: Session):
    """Attempting to modify/correct a field on a FINALISED case must return 400."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    headers = get_auth_headers()

    case_id = "case-fin-lock-03"
    c = InspectionCase(
        inspection_id=case_id,
        case_number="CASE-LOCK-03",
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
        json={"corrected_value": "150.00", "reason": "Unauthorized post-finalisation edit"},
        headers=headers
    )
    assert resp.status_code == 400
    app.dependency_overrides.clear()

def test_redteam_04_finalised_case_blocks_rule_evaluation(db_session: Session):
    """Attempting to re-evaluate compliance on a FINALISED case must return 400."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    headers = get_auth_headers()

    case_id = "case-fin-lock-04"
    c = InspectionCase(
        inspection_id=case_id,
        case_number="CASE-LOCK-04",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.FINALISED,
        overall_determination=OverallDetermination.COMPLIANT,
        officer_decision="COMPLIANT"
    )
    db_session.add(c)
    db_session.commit()

    resp = client.post(f"/api/v1/cases/{case_id}/evaluate", headers=headers)
    assert resp.status_code == 400
    app.dependency_overrides.clear()

def test_redteam_05_finalised_case_blocks_status_transition(db_session: Session):
    """Attempting to transition status away from FINALISED must return 400."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    headers = get_auth_headers()

    case_id = "case-fin-lock-05"
    c = InspectionCase(
        inspection_id=case_id,
        case_number="CASE-LOCK-05",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.FINALISED,
        overall_determination=OverallDetermination.COMPLIANT,
        officer_decision="COMPLIANT"
    )
    db_session.add(c)
    db_session.commit()

    resp = client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={"status": "DRAFT", "notes": "Illegal rollback"},
        headers=headers
    )
    assert resp.status_code == 400
    app.dependency_overrides.clear()

def test_redteam_06_finalised_case_blocks_re_finalisation(db_session: Session):
    """Attempting to re-finalise an already finalised case must return 400."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    headers = get_auth_headers()

    case_id = "case-fin-lock-06"
    c = InspectionCase(
        inspection_id=case_id,
        case_number="CASE-LOCK-06",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.FINALISED,
        overall_determination=OverallDetermination.COMPLIANT,
        officer_decision="COMPLIANT"
    )
    db_session.add(c)
    db_session.commit()

    resp = client.post(
        f"/api/v1/cases/{case_id}/finalize",
        json={"officer_decision": "NON_COMPLIANT", "officer_remarks": "Re-finalise attempt"},
        headers=headers
    )
    assert resp.status_code == 400
    app.dependency_overrides.clear()

# ==============================================================================
# 2. RBAC & OBJECT ISOLATION RED TEAM
# ==============================================================================
def test_redteam_07_unauthenticated_request_rejected(db_session: Session):
    """Requests with no authorization header must strictly return 401."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    resp1 = client.get("/api/v1/cases")
    assert resp1.status_code == 401

    resp2 = client.post("/api/v1/cases", json={"notes": "No auth"})
    assert resp2.status_code == 401
    app.dependency_overrides.clear()

def test_redteam_08_reviewer_cannot_finalise_case(db_session: Session):
    """User with REVIEWER role must be forbidden (403) from finalising a case."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    reviewer_headers = get_auth_headers(role="REVIEWER", user_id="REVIEWER-IND-2001")

    case_id = "case-rbac-reviewer"
    c = InspectionCase(
        inspection_id=case_id,
        case_number="CASE-RBAC-01",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.PENDING_REVIEW
    )
    db_session.add(c)
    db_session.commit()

    resp = client.post(
        f"/api/v1/cases/{case_id}/finalize",
        json={"officer_decision": "COMPLIANT", "officer_remarks": "Reviewer attempt"},
        headers=reviewer_headers
    )
    assert resp.status_code == 403
    app.dependency_overrides.clear()

def test_redteam_09_non_existent_case_returns_404(db_session: Session):
    """Requesting non-existent case or evidence must return 404."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    headers = get_auth_headers()

    resp = client.get("/api/v1/cases/non-existent-case-id-9999", headers=headers)
    assert resp.status_code == 404
    app.dependency_overrides.clear()

# ==============================================================================
# 3. AUDIT CHAIN INTEGRITY RED TEAM
# ==============================================================================
def test_redteam_10_audit_chain_continuous_hash_integrity(db_session: Session):
    """Audit service hash-chaining must remain cryptographically continuous."""
    case_id = "case-audit-integrity-test"
    AuditService.record_event(db_session, case_id, "OFFICER-IND-1001", "CASE_CREATED", "InspectionCase", case_id, {})
    AuditService.record_event(db_session, case_id, "OFFICER-IND-1001", "EVIDENCE_UPLOAD", "EvidenceItem", f"ev-{case_id}", {})
    AuditService.record_event(db_session, case_id, "OFFICER-IND-1001", "FINALIZED", "InspectionCase", case_id, {})

    # Verify audit chain integrity
    is_valid, count, bad_idx, msg = AuditService.verify_chain(db_session, case_id)
    assert is_valid is True
    assert bad_idx is None
    assert count == 3

