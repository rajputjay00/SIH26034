from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.domain import (
    InspectionCase,
    CaseStatus,
    OverallDetermination,
    RuleFinding,
    FindingStatus,
    GeneratedReport,
    ExtractedField,
    EvidenceItem
)
from app.schemas.pydantic_models import (
    DashboardSummaryResponse,
    DashboardReviewQueueResponse,
    DashboardFindingsBreakdown,
    FindingRuleBreakdownItem,
    DashboardTrendItem
)

RULE_NAME_MAP = {
    "RULE_6_MANDATORY_DECLARATIONS": "Rule 6: Mandatory Declarations Presence",
    "RULE_6_UNIT_SALE_PRICE": "Rule 6: Unit Sale Price (USP) Arithmetic",
    "RULE_7_FONT_SIZE": "Rule 7: Minimum Font Size (PDP Area)",
    "RULE_6_EXPIRY_DATE": "Rule 6: Best Before / Expiry Indication",
    "RULE_6_NET_QUANTITY": "Rule 6: Standard Units of Weight/Measure",
    "RULE_6_MANUFACTURER_ADDRESS": "Rule 6: Manufacturer / Packer Complete Address",
    "RULE_6_CONSUMER_CARE": "Rule 6: Consumer Care Contact Details",
    "RULE_6_COUNTRY_OF_ORIGIN": "Rule 6: Country of Origin Declaration",
    "VISUAL_ANOMALY_OVERLAY": "Visual Forensics: Suspected Sticker / Overlay"
}

class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_summary_kpis(self) -> DashboardSummaryResponse:
        """Calculate real summary KPIs directly from the SQLite database."""
        total = self.db.query(InspectionCase).count()
        if total == 0:
            return DashboardSummaryResponse(
                total_inspections=0,
                processing_count=0,
                pending_review_count=0,
                requires_review_count=0,
                compliant_count=0,
                non_compliant_count=0,
                finalised_count=0,
                reports_generated_count=0
            )

        processing = self.db.query(InspectionCase).filter(
            InspectionCase.status.in_([CaseStatus.DRAFT, CaseStatus.PROCESSING])
        ).count()

        pending_review = self.db.query(InspectionCase).filter(
            InspectionCase.status == CaseStatus.PENDING_REVIEW
        ).count()

        requires_review = self.db.query(InspectionCase).filter(
            InspectionCase.overall_determination == OverallDetermination.REQUIRES_REVIEW
        ).count()

        compliant = self.db.query(InspectionCase).filter(
            InspectionCase.overall_determination == OverallDetermination.COMPLIANT
        ).count()

        non_compliant = self.db.query(InspectionCase).filter(
            InspectionCase.overall_determination == OverallDetermination.NON_COMPLIANT
        ).count()

        finalised = self.db.query(InspectionCase).filter(
            InspectionCase.status == CaseStatus.FINALISED
        ).count()

        reports_generated = self.db.query(GeneratedReport).filter(
            GeneratedReport.status == "GENERATED"
        ).count()

        return DashboardSummaryResponse(
            total_inspections=total,
            processing_count=processing,
            pending_review_count=pending_review,
            requires_review_count=requires_review,
            compliant_count=compliant,
            non_compliant_count=non_compliant,
            finalised_count=finalised,
            reports_generated_count=reports_generated
        )

    def get_review_queue_metrics(self) -> DashboardReviewQueueResponse:
        """Calculate review queue workload from actual case and finding state."""
        active_cases = self.db.query(InspectionCase).filter(
            InspectionCase.status != CaseStatus.FINALISED
        ).all()

        if not active_cases:
            return DashboardReviewQueueResponse(
                high_priority_count=0,
                standard_review_count=0,
                ready_for_finalisation_count=0
            )

        high_priority = 0
        ready_for_finalisation = 0
        standard_review = 0

        for case_obj in active_cases:
            # Check findings for this case
            findings = self.db.query(RuleFinding).filter(
                RuleFinding.inspection_id == case_obj.inspection_id
            ).all()

            has_fail = any(f.status == FindingStatus.FAIL for f in findings)
            has_review = any(f.status == FindingStatus.REVIEW for f in findings) or case_obj.overall_determination == OverallDetermination.REQUIRES_REVIEW

            if has_fail or case_obj.overall_determination == OverallDetermination.NON_COMPLIANT:
                high_priority += 1
            elif case_obj.status == CaseStatus.PENDING_REVIEW and findings and not has_fail:
                ready_for_finalisation += 1
            else:
                standard_review += 1

        return DashboardReviewQueueResponse(
            high_priority_count=high_priority,
            standard_review_count=standard_review,
            ready_for_finalisation_count=ready_for_finalisation
        )

    def get_findings_breakdown(self) -> DashboardFindingsBreakdown:
        """Group persisted rule findings by rule ID and calculate status distributions."""
        all_findings = self.db.query(RuleFinding).all()
        if not all_findings:
            return DashboardFindingsBreakdown(total_findings=0, rules=[])

        rule_stats: Dict[str, Dict[str, Any]] = {}
        for f in all_findings:
            r_id = f.rule_id
            if r_id not in rule_stats:
                rule_stats[r_id] = {
                    "rule_id": r_id,
                    "rule_name": RULE_NAME_MAP.get(r_id, r_id.replace("_", " ").title()),
                    "pass_count": 0,
                    "fail_count": 0,
                    "review_count": 0,
                    "total_evaluated": 0
                }

            rule_stats[r_id]["total_evaluated"] += 1
            if f.status == FindingStatus.PASS:
                rule_stats[r_id]["pass_count"] += 1
            elif f.status == FindingStatus.FAIL:
                rule_stats[r_id]["fail_count"] += 1
            elif f.status == FindingStatus.REVIEW:
                rule_stats[r_id]["review_count"] += 1

        items = [FindingRuleBreakdownItem(**data) for data in rule_stats.values()]
        items.sort(key=lambda x: x.fail_count + x.review_count, reverse=True)

        return DashboardFindingsBreakdown(
            total_findings=len(all_findings),
            rules=items
        )

    def get_inspection_trends(self, days: int = 14) -> List[DashboardTrendItem]:
        """Aggregate inspection creation and finalisation dates from actual database records."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)

        cases = self.db.query(InspectionCase).filter(
            InspectionCase.created_at >= start_date
        ).all()

        date_map: Dict[str, Dict[str, int]] = {}
        for i in range(days + 1):
            d_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            date_map[d_str] = {"created": 0, "finalised": 0}

        for c in cases:
            c_date = c.created_at.strftime("%Y-%m-%d")
            if c_date in date_map:
                date_map[c_date]["created"] += 1
            if c.finalized_at:
                f_date = c.finalized_at.strftime("%Y-%m-%d")
                if f_date in date_map:
                    date_map[f_date]["finalised"] += 1

        return [
            DashboardTrendItem(
                date=k,
                inspections_created=v["created"],
                inspections_finalised=v["finalised"]
            )
            for k, v in sorted(date_map.items())
        ]
