from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class LegalRuleDefinition(BaseModel):
    rule_id: str
    legal_citation: str
    title: str
    description: str
    required_inputs: List[str]
    is_active: bool = True
    # Configuration placeholders for unresolved statutory tables - populated strictly from DCA Gazette in future phase
    statutory_config: Optional[Dict[str, Any]] = None

class RulePackMetadata(BaseModel):
    rule_pack_id: str
    version: str
    effective_from: datetime
    effective_to: Optional[datetime] = None
    source_reference: str  # e.g., "Legal Metrology Act, 2009 & PC Rules, 2011 (DCA Gazette 2026)"
    status: str = "ACTIVE"
    rules: List[LegalRuleDefinition] = []

class RulePackInterface(ABC):
    """
    Abstract interface for Legal Rule Packs.
    Ensures clear separation between OCR perception and deterministic legal validation.
    No statutory threshold values are hardcoded in Phase 1.
    """
    @property
    @abstractmethod
    def metadata(self) -> RulePackMetadata:
        pass

    @abstractmethod
    def list_rules(self) -> List[LegalRuleDefinition]:
        pass

    @abstractmethod
    def evaluate_rule(self, rule_id: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a specific legal rule against extracted field inputs.
        Method signature reserved for Phase 3 rule engine implementation.
        """
        pass

class StandardLegalRulePackV1(RulePackInterface):
    """
    Phase 1 Rule Pack Foundation Shell.
    Defines structural rule references without populating guessed or unverified statutory thresholds.
    """
    def __init__(self):
        self._metadata = RulePackMetadata(
            rule_pack_id="RULE-PACK-LM-2026-V1",
            version="v1.0.0",
            effective_from=datetime(2026, 1, 1),
            source_reference="Legal Metrology (Packaged Commodities) Rules, 2011 & DCA Amendments",
            status="ACTIVE",
            rules=[
                LegalRuleDefinition(
                    rule_id="RULE-DECL-MANDATORY-10",
                    legal_citation="Rule 6(1), Legal Metrology (Packaged Commodities) Rules, 2011",
                    title="10 Mandatory Declarations Completeness",
                    description="Verifies presence of all 10 mandatory declarations on packaged commodity.",
                    required_inputs=["manufacturer_details", "country_of_origin", "commodity_name", "net_quantity", "manufacture_date", "mrp", "consumer_care", "dimensions", "unit_sale_price"],
                    statutory_config={"unresolved_note": "Exact statutory applicability per commodity category deferred to verified DCA source."}
                ),
                LegalRuleDefinition(
                    rule_id="RULE-USP-CONSISTENCY",
                    legal_citation="Rule 6(1)(e), PC Rules 2011 (Amendments)",
                    title="Unit Sale Price Consistency Check",
                    description="Calculates expected unit sale price from MRP and Net Quantity and compares to printed USP.",
                    required_inputs=["mrp", "net_quantity", "printed_unit_sale_price"],
                    statutory_config={"unresolved_note": "Rounding and tolerance percentages subject to category-specific schedule verification."}
                ),
                LegalRuleDefinition(
                    rule_id="RULE-FONT-HEIGHT-MINIMUM",
                    legal_citation="Rule 7, Legal Metrology (Packaged Commodities) Rules, 2011",
                    title="Minimum Declaration Font Height Check",
                    description="Validates physical character height in mm against statutory display area table.",
                    required_inputs=["measured_font_height_mm", "principal_display_area_sq_cm", "calibration_status"],
                    statutory_config={"unresolved_note": "Statutory font size height matrix requires valid calibration; otherwise returns MANUAL_REVIEW."}
                ),
                LegalRuleDefinition(
                    rule_id="RULE-OVERLAY-STICKER-DETECTION",
                    legal_citation="Rule 6(2), PC Rules 2011",
                    title="Price Overwrite / Sticker Signal Detection",
                    description="Flags suspected price overwrites or label overlays for officer confirmation.",
                    required_inputs=["bounding_box_overlay_flag"],
                    statutory_config={"unresolved_note": "Overlays represent suspicion tags for human review, not automatic violations."}
                )
            ]
        )

    @property
    def metadata(self) -> RulePackMetadata:
        return self._metadata

    def list_rules(self) -> List[LegalRuleDefinition]:
        return self._metadata.rules

    def evaluate_rule(self, rule_id: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "rule_id": rule_id,
            "status": "REVIEW",
            "message": "Phase 1 Foundation: Rule execution engine disabled until Phase 3.",
            "evaluation_metadata": {"extracted_data": extracted_data}
        }
