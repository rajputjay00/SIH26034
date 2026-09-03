import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.domain import (
    InspectionCase,
    CaseStatus,
    EvidenceItem,
    OCRResult,
    ExtractedField,
    ExtractionOrigin,
    FieldApplicability,
    FieldStatus
)
from app.services.extraction_provider import GeminiStructuredExtractor, DeterministicExtractionProvider
from app.services.conflict_service import ConflictDetectionService
from app.services.audit_service import AuditService
from app.utils.errors import ResourceNotFoundError, ValidationError

class StructuredExtractionService:
    """
    Orchestrates extraction of structured fields from OCR results across multi-view evidence.
    """

    def __init__(self, db: Session):
        self.db = db
        self.provider = GeminiStructuredExtractor(fallback_provider=DeterministicExtractionProvider())

    def extract_case_fields(self, inspection_id: str, officer_id: str = "OFFICER-SYS") -> List[ExtractedField]:
        """
        Load all OCR results for an inspection case, parse structured fields, flag conflicts, and persist.
        """
        case = self.db.query(InspectionCase).filter(InspectionCase.inspection_id == inspection_id).first()
        if not case:
            raise ResourceNotFoundError("InspectionCase", inspection_id)

        if case.status == CaseStatus.FINALISED:
            raise ValidationError("Cannot re-extract fields on a finalised inspection case.")

        evidence_items = self.db.query(EvidenceItem).filter(EvidenceItem.inspection_id == inspection_id).all()
        if not evidence_items:
            return []

        all_candidate_fields: List[Dict[str, Any]] = []

        for evidence in evidence_items:
            ocr_results = self.db.query(OCRResult).filter(OCRResult.evidence_id == evidence.evidence_id).all()
            for ocr in ocr_results:
                fields = self.provider.extract_fields(
                    ocr_text=ocr.full_text,
                    ocr_boxes=ocr.boxes_json or [],
                    evidence_id=evidence.evidence_id,
                    inspection_id=inspection_id
                )
                all_candidate_fields.extend(fields)

        # Flag cross-view conflicts (e.g. Front MRP vs Back MRP)
        resolved_candidates = ConflictDetectionService.resolve_and_flag_conflicts(all_candidate_fields)

        # Remove existing auto-extracted fields (preserve manual officer corrections)
        self.db.query(ExtractedField)\
            .filter(ExtractedField.inspection_id == inspection_id, ExtractedField.origin == ExtractionOrigin.AI)\
            .delete()

        persisted_fields: List[ExtractedField] = []
        for c in resolved_candidates:
            field = ExtractedField(
                field_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                source_evidence_id=c.get("source_evidence_id"),
                field_name=c["field_name"],
                raw_value=c.get("raw_value"),
                normalized_value=c.get("normalized_value"),
                unit=c.get("unit"),
                confidence=c.get("confidence", 0.90),
                applicability=c.get("applicability", FieldApplicability.APPLICABLE),
                field_status=c.get("field_status", FieldStatus.EXTRACTED),
                bounding_box_json=c.get("bounding_box_json"),
                origin=ExtractionOrigin.AI,
                status="EXTRACTED",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            self.db.add(field)
            persisted_fields.append(field)

        self.db.commit()

        # Audit Event
        AuditService.record_event(
            db=self.db,
            inspection_id=inspection_id,
            actor_id=officer_id,
            action="STRUCTURED_FIELD_EXTRACTION",
            entity_type="ExtractedField",
            entity_id=inspection_id,
            metadata={
                "fields_extracted": len(persisted_fields),
                "field_names": [f.field_name for f in persisted_fields]
            }
        )

        return persisted_fields
