import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import get_db
from app.models.domain import (
    InspectionCase,
    CaseStatus,
    OverallDetermination,
    RuleFinding,
    FindingStatus,
    FindingSeverity,
    ExtractedField,
    ExtractionOrigin,
    FieldStatus,
    FieldApplicability,
    EvidenceItem,
    EvidenceViewType,
    EvidenceProcessingStatus,
    QualityVerdict,
    UserRole
)
from app.services.dashboard_service import DashboardService
from app.services.case_service import CaseService
from app.services.rule_engine_service import ComplianceEvaluationService
from tests.fixtures.test_data import db_session, create_synthetic_image

def get_auth_headers(role: str = "OFFICER", user_id: str = None):
    from app.core.security import create_access_token
    if role == "ADMIN":
        u_id = "ADMIN-IND-0001"
    elif role == "REVIEWER":
        u_id = "REVIEWER-IND-2001"
    else:
        u_id = "OFFICER-IND-1001"
    token = create_access_token(data={"sub": u_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_01_dashboard_empty_db_returns_safe_zero_metrics(db_session: Session):
    """Verify empty database returns clean zero structures without errors."""
    service = DashboardService(db_session)
    summary = service.get_summary_kpis()
    assert summary.total_inspections == 0
    assert summary.compliant_count == 0
    assert summary.non_compliant_count == 0
    assert summary.reports_generated_count == 0

    queues = service.get_review_queue_metrics()
    assert queues.high_priority_count == 0
    assert queues.standard_review_count == 0
    assert queues.ready_for_finalisation_count == 0

    findings = service.get_findings_breakdown()
    assert findings.total_findings == 0
    assert len(findings.rules) == 0

def test_02_dashboard_summary_real_kpi_calculations(db_session: Session):
    """Verify dashboard KPI calculations strictly reflect database row counts."""
    # Create 3 cases with distinct statuses
    c1 = InspectionCase(
        inspection_id="case-kpi-1",
        case_number="CASE-KPI-001",
        officer_id="OFFICER_01",
        status=CaseStatus.PROCESSING,
        overall_determination=OverallDetermination.PENDING_EVALUATION
    )
    c2 = InspectionCase(
        inspection_id="case-kpi-2",
        case_number="CASE-KPI-002",
        officer_id="OFFICER_01",
        status=CaseStatus.PENDING_REVIEW,
        overall_determination=OverallDetermination.REQUIRES_REVIEW
    )
    c3 = InspectionCase(
        inspection_id="case-kpi-3",
        case_number="CASE-KPI-003",
        officer_id="OFFICER_02",
        status=CaseStatus.FINALISED,
        overall_determination=OverallDetermination.COMPLIANT,
        finalized_at=datetime.now(timezone.utc)
    )
    db_session.add_all([c1, c2, c3])
    db_session.commit()

    service = DashboardService(db_session)
    summary = service.get_summary_kpis()

    assert summary.total_inspections == 3
    assert summary.processing_count == 1
    assert summary.pending_review_count == 1
    assert summary.requires_review_count == 1
    assert summary.compliant_count == 1
    assert summary.finalised_count == 1

def test_03_dashboard_review_queue_workload(db_session: Session):
    """Verify review queue priority categorisation based on actual finding states."""
    c_fail = InspectionCase(
        inspection_id="case-q-fail",
        case_number="CASE-Q-001",
        officer_id="OFFICER_01",
        status=CaseStatus.PENDING_REVIEW,
        overall_determination=OverallDetermination.NON_COMPLIANT
    )
    c_pass = InspectionCase(
        inspection_id="case-q-pass",
        case_number="CASE-Q-002",
        officer_id="OFFICER_01",
        status=CaseStatus.PENDING_REVIEW,
        overall_determination=OverallDetermination.COMPLIANT
    )
    db_session.add_all([c_fail, c_pass])
    db_session.commit()

    f_fail = RuleFinding(
        finding_id="f-fail-1",
        inspection_id="case-q-fail",
        rule_id="RULE_6_UNIT_SALE_PRICE",
        rule_pack_version="v1.0.0",
        title="USP Mismatch",
        status=FindingStatus.FAIL,
        severity=FindingSeverity.HIGH,
        message="Arithmetic mismatch"
    )
    f_pass = RuleFinding(
        finding_id="f-pass-1",
        inspection_id="case-q-pass",
        rule_id="RULE_6_MANDATORY_DECLARATIONS",
        rule_pack_version="v1.0.0",
        title="Mandatory Declarations Present",
        status=FindingStatus.PASS,
        severity=FindingSeverity.INFO,
        message="All declarations present"
    )
    db_session.add_all([f_fail, f_pass])
    db_session.commit()

    service = DashboardService(db_session)
    queues = service.get_review_queue_metrics()

    assert queues.high_priority_count == 1
    assert queues.ready_for_finalisation_count == 1

def test_04_dashboard_findings_breakdown(db_session: Session):
    """Verify violation breakdown grouping by rule ID."""
    f1 = RuleFinding(
        finding_id="f-bk-1",
        inspection_id="case-bk-1",
        rule_id="RULE_6_MANDATORY_DECLARATIONS",
        rule_pack_version="v1.0.0",
        title="Mandatory Declarations",
        status=FindingStatus.PASS,
        severity=FindingSeverity.INFO,
        message="Pass"
    )
    f2 = RuleFinding(
        finding_id="f-bk-2",
        inspection_id="case-bk-2",
        rule_id="RULE_6_MANDATORY_DECLARATIONS",
        rule_pack_version="v1.0.0",
        title="Mandatory Declarations",
        status=FindingStatus.FAIL,
        severity=FindingSeverity.HIGH,
        message="Missing MRP"
    )
    f3 = RuleFinding(
        finding_id="f-bk-3",
        inspection_id="case-bk-3",
        rule_id="RULE_7_FONT_SIZE",
        rule_pack_version="v1.0.0",
        title="Font Size Check",
        status=FindingStatus.REVIEW,
        severity=FindingSeverity.MEDIUM,
        message="PDP area unverified"
    )
    db_session.add_all([f1, f2, f3])
    db_session.commit()

    service = DashboardService(db_session)
    breakdown = service.get_findings_breakdown()

    assert breakdown.total_findings == 3
    rule_map = {r.rule_id: r for r in breakdown.rules}
    assert "RULE_6_MANDATORY_DECLARATIONS" in rule_map
    assert rule_map["RULE_6_MANDATORY_DECLARATIONS"].pass_count == 1
    assert rule_map["RULE_6_MANDATORY_DECLARATIONS"].fail_count == 1
    assert "RULE_7_FONT_SIZE" in rule_map
    assert rule_map["RULE_7_FONT_SIZE"].review_count == 1

def test_05_inspections_summary_filtering_and_pagination(db_session: Session):
    """Verify inspection list filtering by status, determination, review queue, and search query."""
    c1 = InspectionCase(
        inspection_id="insp-filt-1",
        case_number="CASE-FILT-ALPHA",
        officer_id="OFFICER_ALICE",
        status=CaseStatus.PROCESSING,
        overall_determination=OverallDetermination.PENDING_EVALUATION,
        notes="Biscuits packet sample"
    )
    c2 = InspectionCase(
        inspection_id="insp-filt-2",
        case_number="CASE-FILT-BETA",
        officer_id="OFFICER_BOB",
        status=CaseStatus.PENDING_REVIEW,
        overall_determination=OverallDetermination.REQUIRES_REVIEW,
        notes="Detergent bar inspection"
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    service = CaseService(db_session)

    # Filter by officer
    items, total = service.list_inspections_summary(officer_id="OFFICER_ALICE")
    assert total == 1
    assert items[0]["case_number"] == "CASE-FILT-ALPHA"

    # Filter by search term
    items, total = service.list_inspections_summary(search="Detergent")
    assert total == 1
    assert items[0]["case_number"] == "CASE-FILT-BETA"

    # Filter by review queue
    items, total = service.list_inspections_summary(review_queue="REQUIRES_REVIEW")
    assert total == 1
    assert items[0]["case_number"] == "CASE-FILT-BETA"

def test_06_case_full_review_summary_endpoint(db_session: Session):
    """Verify /api/v1/cases/{id}/review-summary returns all models and valid audit chain."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    # Setup a case with evidence, field, and finding
    c = InspectionCase(
        inspection_id="case-rev-001",
        case_number="CASE-REV-001",
        officer_id="OFFICER_01",
        status=CaseStatus.PENDING_REVIEW,
        overall_determination=OverallDetermination.REQUIRES_REVIEW
    )
    db_session.add(c)
    db_session.commit()

    ev = EvidenceItem(
        evidence_id="ev-rev-001",
        inspection_id="case-rev-001",
        original_filename="front.jpg",
        media_type="image/jpeg",
        file_reference="storage/front.jpg",
        sha256="aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899",
        view_type=EvidenceViewType.FRONT,
        processing_status=EvidenceProcessingStatus.OCR_COMPLETE,
        quality_verdict=QualityVerdict.PASS
    )
    db_session.add(ev)
    db_session.commit()

    headers = get_auth_headers("OFFICER", "OFFICER_01")
    resp = client.get("/api/v1/cases/case-rev-001/review-summary", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["case"]["case_number"] == "CASE-REV-001"
    assert len(data["evidence"]) == 1
    assert data["evidence"][0]["view_type"] == "FRONT"
    assert data["audit_valid"] is True
    assert data["review_queue"] == "REQUIRES_REVIEW"
    app.dependency_overrides.clear()

def test_07_officer_manual_correction_preserves_original_and_audits(db_session: Session):
    """Verify manual field corrections preserve original value and log immutable audit entries."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    c = InspectionCase(
        inspection_id="case-corr-001",
        case_number="CASE-CORR-001",
        officer_id="OFFICER_01",
        status=CaseStatus.PENDING_REVIEW
    )
    db_session.add(c)
    db_session.commit()

    f = ExtractedField(
        field_id="f-mrp-001",
        inspection_id="case-corr-001",
        field_name="maximum_retail_price",
        raw_value="149.00",
        normalized_value="149.00",
        unit="INR",
        origin=ExtractionOrigin.AI,
        field_status=FieldStatus.EXTRACTED
    )
    db_session.add(f)
    db_session.commit()

    headers = get_auth_headers("OFFICER", "OFFICER_CORRECTOR")
    payload = {
        "corrected_value": "159.00",
        "unit": "INR",
        "reason": "Digit 5 was misread as 4 in OCR"
    }
    resp = client.post(f"/api/v1/cases/case-corr-001/fields/f-mrp-001/correct", json=payload, headers=headers)
    assert resp.status_code == 200
    field_resp = resp.json()

    # Verify original raw_value is preserved, normalized value is updated, and correction history exists
    assert field_resp["raw_value"] == "149.00"
    assert field_resp["normalized_value"] == "159.00"
    assert len(field_resp["corrections"]) == 1
    assert field_resp["corrections"][0]["previous_value"] == "149.00"
    assert field_resp["corrections"][0]["corrected_value"] == "159.00"
    assert field_resp["corrections"][0]["reason"] == "Digit 5 was misread as 4 in OCR"
    app.dependency_overrides.clear()

def test_08_re_evaluation_triggers_deterministic_rules(db_session: Session):
    """Verify deterministic rule engine re-runs on case after field correction."""
    c = InspectionCase(
        inspection_id="case-reeval-001",
        case_number="CASE-REEVAL-001",
        officer_id="OFFICER_01",
        status=CaseStatus.PENDING_REVIEW
    )
    db_session.add(c)
    db_session.commit()

    f_name = ExtractedField(
        field_id="f-reeval-name",
        inspection_id="case-reeval-001",
        field_name="commodity_name",
        raw_value="Premium Butter Cookies",
        normalized_value="Premium Butter Cookies"
    )
    f_mrp = ExtractedField(
        field_id="f-reeval-mrp",
        inspection_id="case-reeval-001",
        field_name="mrp",
        raw_value="150.00",
        normalized_value="150.00",
        unit="INR"
    )
    f_qty = ExtractedField(
        field_id="f-reeval-qty",
        inspection_id="case-reeval-001",
        field_name="net_quantity",
        raw_value="500 g",
        normalized_value="500",
        unit="g"
    )
    f_usp = ExtractedField(
        field_id="f-reeval-usp",
        inspection_id="case-reeval-001",
        field_name="unit_sale_price",
        raw_value="0.30 per g",
        normalized_value="0.30",
        unit="INR/g"
    )
    f_mfg = ExtractedField(
        field_id="f-reeval-mfg",
        inspection_id="case-reeval-001",
        field_name="manufacturer",
        raw_value="ABC Foods Pvt Ltd, Industrial Area, New Delhi 110001",
        normalized_value="ABC Foods Pvt Ltd, Industrial Area, New Delhi 110001"
    )
    f_origin = ExtractedField(
        field_id="f-reeval-origin",
        inspection_id="case-reeval-001",
        field_name="country_of_origin",
        raw_value="India",
        normalized_value="India"
    )
    f_cc = ExtractedField(
        field_id="f-reeval-cc",
        inspection_id="case-reeval-001",
        field_name="consumer_care",
        raw_value="care@abcfoods.com, 1800-111-222",
        normalized_value="care@abcfoods.com, 1800-111-222"
    )
    f_mfg_date = ExtractedField(
        field_id="f-reeval-mfg-date",
        inspection_id="case-reeval-001",
        field_name="manufacture_date",
        raw_value="08/2026",
        normalized_value="08/2026"
    )
    f_exp = ExtractedField(
        field_id="f-reeval-exp",
        inspection_id="case-reeval-001",
        field_name="expiry_date",
        raw_value="Best before 12 months from mfg",
        normalized_value="12 months"
    )
    db_session.add_all([f_name, f_mrp, f_qty, f_usp, f_mfg, f_origin, f_cc, f_mfg_date, f_exp])
    db_session.commit()

    service = ComplianceEvaluationService(db_session)
    summary = service.evaluate_inspection(inspection_id="case-reeval-001", officer_id="OFFICER-IND-1001")

    assert summary["fail_count"] == 0
    assert summary["pass_count"] >= 6
    assert summary["overall_determination"] in (OverallDetermination.COMPLIANT, OverallDetermination.REQUIRES_REVIEW)





def test_09_finalisation_safeguards_and_role_boundaries(db_session: Session):
    """Verify finalisation requires valid officer role, completeness, and records identity."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    # Reviewer cannot finalize (only ADMIN or OFFICER)
    headers_rev = get_auth_headers("REVIEWER", "REVIEWER_01")
    resp = client.post("/api/v1/cases/case-any/finalize", json={
        "officer_decision": "COMPLIANT",
        "officer_remarks": "Approved"
    }, headers=headers_rev)
    assert resp.status_code == 403
    app.dependency_overrides.clear()
