import pytest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.models.domain import CaseStatus, EvidenceViewType, ExtractionOrigin, FindingStatus, UserRole

def test_enum_values():
    assert CaseStatus.DRAFT.value == "DRAFT"
    assert CaseStatus.PROCESSING.value == "PROCESSING"
    assert CaseStatus.PENDING_REVIEW.value == "PENDING_REVIEW"
    assert CaseStatus.FINALISED.value == "FINALISED"

    assert EvidenceViewType.FRONT.value == "FRONT"
    assert EvidenceViewType.BACK.value == "BACK"
    assert EvidenceViewType.SIDE.value == "SIDE"
    assert EvidenceViewType.BASE.value == "BASE"

    assert ExtractionOrigin.AI.value == "AI"
    assert ExtractionOrigin.OFFICER.value == "OFFICER"

    assert FindingStatus.PASS.value == "PASS"
    assert FindingStatus.FAIL.value == "FAIL"

    assert UserRole.ADMIN.value == "ADMIN"
    assert UserRole.OFFICER.value == "OFFICER"
    assert UserRole.REVIEWER.value == "REVIEWER"
