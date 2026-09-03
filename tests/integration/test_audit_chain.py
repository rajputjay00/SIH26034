import pytest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from tests.fixtures.test_data import db_session
from app.models.domain import InspectionCase, AuditEntry
from app.services.audit_service import AuditService

def test_audit_chain_creation_and_verification(db_session):
    case = InspectionCase(case_number="CASE-AUDIT-01", officer_id="OFFICER-AUDIT")
    db_session.add(case)
    db_session.commit()

    entry1 = AuditService.record_event(
        db=db_session,
        inspection_id=case.inspection_id,
        actor_id="OFFICER-AUDIT",
        action="CREATE_CASE",
        entity_type="InspectionCase",
        entity_id=case.inspection_id,
        metadata={"step": 1}
    )

    entry2 = AuditService.record_event(
        db=db_session,
        inspection_id=case.inspection_id,
        actor_id="OFFICER-AUDIT",
        action="INGEST_EVIDENCE",
        entity_type="EvidenceItem",
        entity_id="EVID-001",
        metadata={"step": 2}
    )

    is_valid, count, corrupted_idx, msg = AuditService.verify_chain(db_session, case.inspection_id)
    assert is_valid is True
    assert count == 2
    assert corrupted_idx is None

def test_audit_chain_tamper_detection(db_session):
    case = InspectionCase(case_number="CASE-AUDIT-TAMPER", officer_id="OFFICER-AUDIT")
    db_session.add(case)
    db_session.commit()

    AuditService.record_event(db_session, case.inspection_id, "OFFICER-AUDIT", "ACTION_1", "Entity", "1")
    entry2 = AuditService.record_event(db_session, case.inspection_id, "OFFICER-AUDIT", "ACTION_2", "Entity", "2")

    # Mutate second entry payload to simulate tampering
    entry2.action = "TAMPERED_ACTION"
    db_session.commit()

    is_valid, count, corrupted_idx, msg = AuditService.verify_chain(db_session, case.inspection_id)
    assert is_valid is False
    assert corrupted_idx == 1
    assert "Audit entry hash mismatch" in msg
