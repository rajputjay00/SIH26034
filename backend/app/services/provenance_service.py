from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.domain import ExtractedField, FieldCorrection, EvidenceItem, ExtractionOrigin
from app.utils.errors import ResourceNotFoundError

class ProvenanceService:
    @staticmethod
    def get_field_provenance(db: Session, field_id: str) -> Dict[str, Any]:
        """
        Build complete provenance record for an extracted field.
        Traceable to source image, coordinates/bounding box, origin, confidence, and officer audit history.
        """
        field = db.query(ExtractedField).filter(ExtractedField.field_id == field_id).first()
        if not field:
            raise ResourceNotFoundError("ExtractedField", field_id)

        evidence = None
        if field.source_evidence_id:
            evidence = db.query(EvidenceItem).filter(EvidenceItem.evidence_id == field.source_evidence_id).first()

        corrections = db.query(FieldCorrection)\
            .filter(FieldCorrection.field_id == field_id)\
            .order_by(FieldCorrection.created_at.asc())\
            .all()

        return {
            "field_id": field.field_id,
            "inspection_id": field.inspection_id,
            "field_name": field.field_name,
            "current_value": field.normalized_value or field.raw_value,
            "raw_value": field.raw_value,
            "normalized_value": field.normalized_value,
            "unit": field.unit,
            "confidence": field.confidence,
            "origin": field.origin.value if isinstance(field.origin, ExtractionOrigin) else field.origin,
            "bounding_box": field.bounding_box_json,
            "source_evidence": {
                "evidence_id": evidence.evidence_id,
                "original_filename": evidence.original_filename,
                "sha256": evidence.sha256,
                "view_type": evidence.view_type.value if hasattr(evidence.view_type, 'value') else evidence.view_type
            } if evidence else None,
            "correction_history": [
                {
                    "correction_id": c.correction_id,
                    "previous_value": c.previous_value,
                    "corrected_value": c.corrected_value,
                    "officer_id": c.officer_id,
                    "reason": c.reason,
                    "timestamp": c.created_at.isoformat()
                } for c in corrections
            ]
        }
