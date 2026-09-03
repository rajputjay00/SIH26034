from typing import List, Dict, Any
from app.models.domain import FieldStatus

class ConflictDetectionService:
    """
    Detects cross-view evidentiary conflicts (e.g., Front MRP differing from Back MRP).
    Flags conflicting extractions as CONFLICTING and prepares them for human officer review.
    """

    @staticmethod
    def resolve_and_flag_conflicts(extracted_fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group extracted fields by field_name and identify conflicting normalized values across views.
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for field in extracted_fields:
            name = field.get("field_name", "")
            grouped.setdefault(name, []).append(field)

        for name, fields in grouped.items():
            if len(fields) > 1:
                # Check for value discrepancies across distinct evidence sources
                distinct_values = {
                    (f.get("normalized_value") or f.get("raw_value") or "").strip().lower()
                    for f in fields
                    if (f.get("normalized_value") or f.get("raw_value"))
                }
                if len(distinct_values) > 1:
                    for f in fields:
                        f["field_status"] = FieldStatus.CONFLICTING
                        f["conflict_sources"] = [x.get("source_evidence_id") for x in fields]

        return extracted_fields
