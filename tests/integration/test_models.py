import pytest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from tests.fixtures.test_data import db_session
from app.models.domain import InspectionCase, EvidenceItem, CaseStatus, EvidenceViewType

def test_inspection_case_model_creation(db_session):
    case = InspectionCase(
        case_number="CASE-TEST-001",
        officer_id="OFFICER-101",
        status=CaseStatus.DRAFT,
        rule_pack_version="v1.0.0"
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    assert case.inspection_id is not None
    assert case.case_number == "CASE-TEST-001"
    assert case.status == CaseStatus.DRAFT

def test_evidence_relationship(db_session):
    case = InspectionCase(case_number="CASE-TEST-002", officer_id="OFFICER-102")
    db_session.add(case)
    db_session.commit()

    evidence = EvidenceItem(
        inspection_id=case.inspection_id,
        original_filename="front_pack.jpg",
        media_type="image/jpeg",
        file_reference="storage/front_pack.jpg",
        sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        view_type=EvidenceViewType.FRONT
    )
    db_session.add(evidence)
    db_session.commit()

    retrieved = db_session.query(InspectionCase).filter_by(case_number="CASE-TEST-002").first()
    assert len(retrieved.evidence_items) == 1
    assert retrieved.evidence_items[0].original_filename == "front_pack.jpg"
