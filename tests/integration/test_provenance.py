import pytest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from tests.fixtures.test_data import db_session
from app.models.domain import InspectionCase, EvidenceItem, ExtractedField, FieldCorrection, ExtractionOrigin, EvidenceViewType
from app.services.provenance_service import ProvenanceService

def test_field_provenance_retrieval(db_session):
    case = InspectionCase(case_number="CASE-PROV-01", officer_id="OFFICER-PROV")
    db_session.add(case)
    db_session.commit()

    evidence = EvidenceItem(
        inspection_id=case.inspection_id,
        original_filename="back.jpg",
        media_type="image/jpeg",
        file_reference="storage/back.jpg",
        sha256="abc123sha256",
        view_type=EvidenceViewType.BACK
    )
    db_session.add(evidence)
    db_session.commit()

    field = ExtractedField(
        inspection_id=case.inspection_id,
        source_evidence_id=evidence.evidence_id,
        field_name="net_quantity",
        raw_value="500 g",
        normalized_value="500 g",
        unit="g",
        confidence=0.95,
        bounding_box_json={"x": 10, "y": 20, "w": 100, "h": 30},
        origin=ExtractionOrigin.AI
    )
    db_session.add(field)
    db_session.commit()

    correction = FieldCorrection(
        field_id=field.field_id,
        previous_value="500 g",
        corrected_value="500 g",
        officer_id="OFFICER-PROV",
        reason="Verified accuracy"
    )
    db_session.add(correction)
    db_session.commit()

    prov = ProvenanceService.get_field_provenance(db_session, field.field_id)
    assert prov["field_name"] == "net_quantity"
    assert prov["raw_value"] == "500 g"
    assert prov["origin"] == "AI"
    assert prov["source_evidence"]["sha256"] == "abc123sha256"
    assert len(prov["correction_history"]) == 1
    assert prov["correction_history"][0]["officer_id"] == "OFFICER-PROV"
