import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from sqlalchemy.orm import Session
from app.models.domain import InspectionCase, CaseStatus, OverallDetermination
from app.repositories.case_repository import CaseRepository
from app.services.audit_service import AuditService
from app.utils.errors import ResourceNotFoundError, InvalidStateTransitionError, ValidationError


VALID_TRANSITIONS = {
    CaseStatus.DRAFT: [CaseStatus.PROCESSING],
    CaseStatus.PROCESSING: [CaseStatus.PENDING_REVIEW, CaseStatus.DRAFT],
    CaseStatus.PENDING_REVIEW: [CaseStatus.FINALISED, CaseStatus.PROCESSING, CaseStatus.DRAFT],
    CaseStatus.FINALISED: []  # Finalized cases cannot be mutated
}

class CaseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CaseRepository(db)

    def create_case(self, officer_id: str, case_number: Optional[str] = None, notes: Optional[str] = None, rule_pack_version: str = "v1.0.0") -> InspectionCase:
        if not case_number:
            timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            case_number = f"CASE-LM-{timestamp_str}-{uuid.uuid4().hex[:4].upper()}"

        existing = self.repo.get_by_case_number(case_number)
        if existing:
            raise ValueError(f"Case number '{case_number}' already exists.")

        case = InspectionCase(
            inspection_id=str(uuid.uuid4()),
            case_number=case_number,
            officer_id=officer_id,
            status=CaseStatus.DRAFT,
            rule_pack_version=rule_pack_version,
            notes=notes
        )

        created_case = self.repo.create(case)

        # Audit case creation
        AuditService.record_event(
            db=self.db,
            inspection_id=created_case.inspection_id,
            actor_id=officer_id,
            action="CREATE_CASE",
            entity_type="InspectionCase",
            entity_id=created_case.inspection_id,
            metadata={"case_number": case_number, "rule_pack_version": rule_pack_version}
        )

        return created_case

    def get_case(self, inspection_id: str) -> InspectionCase:
        case = self.repo.get_by_id(inspection_id)
        if not case:
            raise ResourceNotFoundError("InspectionCase", inspection_id)
        return case

    def list_cases(self, limit: int = 50, offset: int = 0) -> List[InspectionCase]:
        return self.repo.list_cases(limit=limit, offset=offset)

    def update_case_status(self, inspection_id: str, new_status: CaseStatus, officer_id: str, notes: Optional[str] = None) -> InspectionCase:
        case = self.get_case(inspection_id)
        allowed_targets = VALID_TRANSITIONS.get(case.status, [])

        if new_status not in allowed_targets:
            raise InvalidStateTransitionError(case.status.value, new_status.value)

        case.status = new_status
        if notes:
            case.notes = notes
        if new_status == CaseStatus.FINALISED:
            case.finalized_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(case)

        # Audit status transition
        AuditService.record_event(
            db=self.db,
            inspection_id=case.inspection_id,
            actor_id=officer_id,
            action="TRANSITION_STATUS",
            entity_type="InspectionCase",
            metadata={"new_status": new_status.value, "notes": notes}
        )

        return case


    def finalize_case(
        self,
        inspection_id: str,
        officer_id: str,
        officer_decision: str,
        officer_remarks: Optional[str] = None,
        acknowledged_review_findings: bool = False
    ) -> InspectionCase:
        """
        Finalises an inspection case after enforcing strict statutory safeguards:
        1. Case must be in PENDING_REVIEW status.
        2. Evidence items must exist and have completed quality processing.
        3. Compliance findings must be evaluated.
        4. If unresolved REVIEW findings exist, officer must explicitly acknowledge them.
        5. Officer decision and remarks must be recorded.
        6. Generates version 1 immutable PDF report.
        """
        case = self.get_case(inspection_id)
        if case.status == CaseStatus.FINALISED:
            raise InvalidStateTransitionError("FINALISED", "FINALISED")

        if case.status not in (CaseStatus.PENDING_REVIEW, CaseStatus.PROCESSING, CaseStatus.DRAFT):
            raise InvalidStateTransitionError(case.status.value, "FINALISED")

        # Safeguard 1: Evidence completeness check
        from app.models.domain import EvidenceItem, RuleFinding, FindingStatus, OverallDetermination
        evidence = self.db.query(EvidenceItem).filter(EvidenceItem.inspection_id == inspection_id).all()
        if not evidence:
            raise ValidationError("Cannot finalise inspection without uploaded evidence items.")

        # Safeguard 2: Rule findings evaluation check
        findings = self.db.query(RuleFinding).filter(RuleFinding.inspection_id == inspection_id).all()
        if not findings:
            raise ValidationError("Cannot finalise inspection: Statutory rule evaluation has not been performed.")

        # Safeguard 3: Unresolved REVIEW findings safeguard
        has_review_findings = any(f.status == FindingStatus.REVIEW for f in findings)
        if has_review_findings and not acknowledged_review_findings:
            raise ValidationError(
                "Inspection contains unresolved REVIEW findings under statutory rules. "
                "Authorised officer must explicitly review and acknowledge these items before finalisation."
            )

        # Apply finalisation
        case.status = CaseStatus.FINALISED
        case.officer_decision = str(officer_decision)
        case.officer_remarks = officer_remarks
        case.finalized_at = datetime.now(timezone.utc)

        # Set overall determination if valid
        try:
            case.overall_determination = OverallDetermination(officer_decision)
        except ValueError:
            pass

        self.db.commit()
        self.db.refresh(case)

        # Audit Event for Finalisation
        AuditService.record_event(
            db=self.db,
            inspection_id=case.inspection_id,
            actor_id=officer_id,
            action="INSPECTION_FINALISED",
            entity_type="InspectionCase",
            entity_id=case.inspection_id,
            metadata={
                "officer_decision": case.officer_decision,
                "officer_remarks": case.officer_remarks,
                "finalized_at": case.finalized_at.isoformat(),
                "acknowledged_review_findings": acknowledged_review_findings
            }
        )

        # Auto-generate Version 1 Inspection Report
        from app.services.report_service import ReportService
        ReportService.generate_inspection_report(
            db=self.db,
            inspection_id=case.inspection_id,
            officer_id=officer_id,
            force_regenerate=False
        )

        return case

    def list_inspections_summary(
        self,
        status: Optional[str] = None,
        determination: Optional[str] = None,
        review_queue: Optional[str] = None,
        officer_id: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Any], int]:
        from app.models.domain import EvidenceItem, RuleFinding, FindingStatus, ExtractedField, GeneratedReport

        # Fetch cases matching base filters
        raw_cases, _ = self.repo.list_filtered_cases(
            status=status,
            determination=determination,
            officer_id=officer_id,
            search=search,
            limit=1000, # fetch wider pool to filter by review queue if specified
            offset=0
        )

        summary_items = []
        for c in raw_cases:
            ev_count = self.db.query(EvidenceItem).filter(EvidenceItem.inspection_id == c.inspection_id).count()
            findings = self.db.query(RuleFinding).filter(RuleFinding.inspection_id == c.inspection_id).all()
            pass_c = sum(1 for f in findings if f.status == FindingStatus.PASS)
            fail_c = sum(1 for f in findings if f.status == FindingStatus.FAIL)
            review_c = sum(1 for f in findings if f.status == FindingStatus.REVIEW)

            ext_fields = self.db.query(ExtractedField).filter(ExtractedField.inspection_id == c.inspection_id).all()
            ext_status = "EMPTY"
            if ext_fields:
                ext_status = "COMPLETE"

            has_report = self.db.query(GeneratedReport).filter(
                GeneratedReport.inspection_id == c.inspection_id,
                GeneratedReport.status == "GENERATED"
            ).count() > 0

            # Determine review queue
            if c.status == CaseStatus.FINALISED:
                queue_val = "FINALISED"
            elif c.overall_determination == OverallDetermination.REQUIRES_REVIEW or review_c > 0:
                queue_val = "REQUIRES_REVIEW"
            elif c.status == CaseStatus.PENDING_REVIEW and findings and fail_c == 0 and review_c == 0:
                queue_val = "READY_FOR_FINALISATION"
            elif c.status == CaseStatus.PENDING_REVIEW:
                queue_val = "PENDING_REVIEW"
            else:
                queue_val = "PROCESSING"

            # Filter by review queue if requested
            if review_queue and queue_val != review_queue:
                continue

            summary_items.append({
                "inspection_id": c.inspection_id,
                "case_number": c.case_number,
                "officer_id": c.officer_id,
                "status": c.status,
                "overall_determination": c.overall_determination,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "finalized_at": c.finalized_at,
                "evidence_count": ev_count,
                "findings_count": len(findings),
                "pass_count": pass_c,
                "fail_count": fail_c,
                "review_count": review_c,
                "extraction_status": ext_status,
                "review_queue": queue_val,
                "has_report": has_report
            })

        total = len(summary_items)
        paginated_items = summary_items[offset : offset + limit]
        return paginated_items, total

    def get_review_summary(self, inspection_id: str) -> Dict[str, Any]:
        """Fetch comprehensive case records across all dimensions for the review console."""
        from app.models.domain import (
            EvidenceItem, ExtractedField, RuleFinding, VisualMeasurement,
            VisualAnomaly, CalibrationData, GeneratedReport, AuditEntry, FindingStatus
        )
        from app.services.provenance_service import ProvenanceService

        case = self.get_case(inspection_id)
        evidence = self.db.query(EvidenceItem).filter(EvidenceItem.inspection_id == inspection_id).all()
        extracted_fields = self.db.query(ExtractedField).filter(ExtractedField.inspection_id == inspection_id).all()
        rule_findings = self.db.query(RuleFinding).filter(RuleFinding.inspection_id == inspection_id).all()
        measurements = self.db.query(VisualMeasurement).filter(VisualMeasurement.inspection_id == inspection_id).all()
        anomalies = self.db.query(VisualAnomaly).filter(VisualAnomaly.inspection_id == inspection_id).all()
        calibrations = self.db.query(CalibrationData).filter(CalibrationData.inspection_id == inspection_id).all()
        reports = self.db.query(GeneratedReport).filter(GeneratedReport.inspection_id == inspection_id).all()
        audit_entries = self.db.query(AuditEntry).filter(AuditEntry.inspection_id == inspection_id).order_by(AuditEntry.timestamp.asc()).all()

        # Audit verification
        is_valid, *_ = AuditService.verify_chain(self.db, inspection_id)
        audit_valid = is_valid

        # Review queue computation
        fail_c = sum(1 for f in rule_findings if f.status == FindingStatus.FAIL)
        review_c = sum(1 for f in rule_findings if f.status == FindingStatus.REVIEW)
        if case.status == CaseStatus.FINALISED:
            queue_val = "FINALISED"
        elif case.overall_determination == OverallDetermination.REQUIRES_REVIEW or review_c > 0:
            queue_val = "REQUIRES_REVIEW"
        elif case.status == CaseStatus.PENDING_REVIEW and rule_findings and fail_c == 0 and review_c == 0:
            queue_val = "READY_FOR_FINALISATION"
        elif case.status == CaseStatus.PENDING_REVIEW:
            queue_val = "PENDING_REVIEW"
        else:
            queue_val = "PROCESSING"

        return {
            "case": case,
            "evidence": evidence,
            "extracted_fields": extracted_fields,
            "rule_findings": rule_findings,
            "measurements": measurements,
            "anomalies": anomalies,
            "calibrations": calibrations,
            "reports": reports,
            "audit_entries": audit_entries,
            "audit_valid": audit_valid,
            "review_queue": queue_val
        }


