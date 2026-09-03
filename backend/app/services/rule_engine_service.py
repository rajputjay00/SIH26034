import uuid
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.domain import (
    InspectionCase,
    CaseStatus,
    ExtractedField,
    RuleFinding,
    FindingStatus,
    FindingSeverity,
    OverallDetermination,
    FieldApplicability,
    FieldStatus
)
from app.services.normalization_service import NormalizationService
from app.services.audit_service import AuditService
from app.utils.errors import ResourceNotFoundError, ValidationError

RULE_PACK_VERSION = "v1.0.0"

class ComplianceEvaluationService:
    """
    Pure deterministic Legal Metrology rule engine.
    Independent of LLM and computer vision; executes strictly on normalized structured fields.
    Maps findings directly to Legal Metrology (Packaged Commodities) Rules, 2011 & DCA Amendments.
    """

    def __init__(self, db: Session):
        self.db = db

    def evaluate_inspection(self, inspection_id: str, officer_id: str = "OFFICER-SYS") -> Dict[str, Any]:
        """
        Execute full deterministic compliance evaluation for an inspection case.
        """
        case = self.db.query(InspectionCase).filter(InspectionCase.inspection_id == inspection_id).first()
        if not case:
            raise ResourceNotFoundError("InspectionCase", inspection_id)

        if case.status == CaseStatus.FINALISED:
            raise ValidationError("Cannot re-evaluate compliance on a finalised inspection case.")

        # 1. Load all structured fields for this case
        fields = self.db.query(ExtractedField).filter(ExtractedField.inspection_id == inspection_id).all()
        field_map: Dict[str, ExtractedField] = {f.field_name: f for f in fields}

        # Clear existing findings for clean re-evaluation
        self.db.query(RuleFinding).filter(RuleFinding.inspection_id == inspection_id).delete()

        findings: List[RuleFinding] = []

        # Rule 1: Commodity Name Completeness
        findings.append(self._eval_commodity_name(inspection_id, field_map.get("commodity_name")))

        # Rule 2: Net Quantity Completeness & Format
        findings.append(self._eval_net_quantity(inspection_id, field_map.get("net_quantity")))

        # Rule 3: MRP (Maximum Retail Price) Presence & Syntax
        findings.append(self._eval_mrp(inspection_id, field_map.get("mrp")))

        # Rule 4: Manufacturer / Packer / Importer Details
        findings.append(self._eval_manufacturer(inspection_id, field_map.get("manufacturer")))

        # Rule 5: Country of Origin Declaration
        findings.append(self._eval_country_of_origin(inspection_id, field_map.get("country_of_origin")))

        # Rule 6: Consumer Care Executive Contact Details
        findings.append(self._eval_consumer_care(inspection_id, field_map.get("consumer_care")))

        # Rule 7: Month and Year of Manufacture / Packing
        findings.append(self._eval_manufacture_date(inspection_id, field_map.get("manufacture_date")))

        # Rule 8: Unit Sale Price (USP) Consistency
        findings.append(self._eval_unit_sale_price_consistency(inspection_id, field_map.get("mrp"), field_map.get("net_quantity"), field_map.get("unit_sale_price")))

        # Rule 9: Minimum Font Height Statutory Compliance (Requires Calibration)
        findings.append(self._eval_font_height_statutory(inspection_id, field_map.get("net_quantity")))

        # Rule 10: Price Overwrite / Sticker Anomaly Signal
        findings.append(self._eval_price_overwrite_signal(inspection_id, field_map.get("mrp")))

        # Persist findings to database
        for f in findings:
            self.db.add(f)

        # Compute Aggregated Overall Determination
        pass_count = sum(1 for f in findings if f.status == FindingStatus.PASS)
        fail_count = sum(1 for f in findings if f.status == FindingStatus.FAIL)
        review_count = sum(1 for f in findings if f.status == FindingStatus.REVIEW)
        na_count = sum(1 for f in findings if f.status == FindingStatus.NOT_APPLICABLE)

        if fail_count > 0:
            overall = OverallDetermination.NON_COMPLIANT
        elif review_count > 0:
            overall = OverallDetermination.REQUIRES_REVIEW
        else:
            overall = OverallDetermination.COMPLIANT

        case.overall_determination = overall
        self.db.commit()

        # Record Audit Event
        AuditService.record_event(
            db=self.db,
            inspection_id=inspection_id,
            actor_id=officer_id,
            action="EVALUATE_COMPLIANCE_RULES",
            entity_type="InspectionCase",
            entity_id=inspection_id,
            metadata={
                "overall_determination": overall.value,
                "total_rules": len(findings),
                "pass": pass_count,
                "fail": fail_count,
                "review": review_count,
                "not_applicable": na_count,
                "rule_pack_version": RULE_PACK_VERSION
            }
        )

        return {
            "inspection_id": inspection_id,
            "overall_determination": overall,
            "total_rules_evaluated": len(findings),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "review_count": review_count,
            "not_applicable_count": na_count,
            "rule_pack_version": RULE_PACK_VERSION,
            "evaluated_at": datetime.now(timezone.utc),
            "findings": findings
        }

    def _eval_commodity_name(self, inspection_id: str, field: Optional[ExtractedField]) -> RuleFinding:
        citation = "Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011"
        if not field or not field.raw_value or field.field_status == FieldStatus.MISSING:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-COMMODITY-NAME",
                rule_pack_version=RULE_PACK_VERSION,
                title="Common or Generic Commodity Name Declaration",
                legal_citation=citation,
                status=FindingStatus.FAIL,
                severity=FindingSeverity.HIGH,
                message="Mandatory generic/common name of commodity was not found on package.",
                field_references_json={"field_name": "commodity_name"}
            )

        if field.field_status in (FieldStatus.UNCERTAIN, FieldStatus.MANUAL_REVIEW):
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-COMMODITY-NAME",
                rule_pack_version=RULE_PACK_VERSION,
                title="Common or Generic Commodity Name Declaration",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.MEDIUM,
                message=f"Commodity name extraction uncertain. Observed: '{field.raw_value}'. Officer verification required.",
                field_references_json={"field_name": "commodity_name", "field_id": field.field_id}
            )

        if field.field_status == FieldStatus.CONFLICTING:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-COMMODITY-NAME",
                rule_pack_version=RULE_PACK_VERSION,
                title="Common or Generic Commodity Name Declaration",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.MEDIUM,
                message=f"Conflicting commodity names detected across views. Observed: '{field.raw_value}'. Officer confirmation required.",
                field_references_json={"field_name": "commodity_name", "field_id": field.field_id}
            )

        return RuleFinding(
            finding_id=str(uuid.uuid4()),
            inspection_id=inspection_id,
            rule_id="RULE-DECL-COMMODITY-NAME",
            rule_pack_version=RULE_PACK_VERSION,
            title="Common or Generic Commodity Name Declaration",
            legal_citation=citation,
            status=FindingStatus.PASS,
            severity=FindingSeverity.INFO,
            message=f"Commodity name declaration identified: '{field.raw_value}'.",
            field_references_json={"field_name": "commodity_name", "field_id": field.field_id}
        )

    def _eval_net_quantity(self, inspection_id: str, field: Optional[ExtractedField]) -> RuleFinding:
        citation = "Rule 6(1)(b), Legal Metrology (Packaged Commodities) Rules, 2011"
        if not field or not field.raw_value or field.field_status == FieldStatus.MISSING:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-NET-QTY",
                rule_pack_version=RULE_PACK_VERSION,
                title="Net Quantity Declaration and Standard Unit",
                legal_citation=citation,
                status=FindingStatus.FAIL,
                severity=FindingSeverity.CRITICAL,
                message="Mandatory net quantity declaration is missing from the package.",
                field_references_json={"field_name": "net_quantity"}
            )

        if field.field_status in (FieldStatus.UNCERTAIN, FieldStatus.MANUAL_REVIEW):
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-NET-QTY",
                rule_pack_version=RULE_PACK_VERSION,
                title="Net Quantity Declaration and Standard Unit",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.HIGH,
                message=f"Net quantity extraction uncertain: '{field.raw_value}'. Officer verification required.",
                field_references_json={"field_name": "net_quantity", "field_id": field.field_id}
            )

        if not field.normalized_value or not field.unit:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-NET-QTY",
                rule_pack_version=RULE_PACK_VERSION,
                title="Net Quantity Declaration and Standard Unit",
                legal_citation=citation,
                status=FindingStatus.FAIL,
                severity=FindingSeverity.HIGH,
                message=f"Net quantity '{field.raw_value}' does not use a recognized statutory standard unit (kg, g, L, ml, N).",
                field_references_json={"field_name": "net_quantity", "field_id": field.field_id}
            )

        return RuleFinding(
            finding_id=str(uuid.uuid4()),
            inspection_id=inspection_id,
            rule_id="RULE-DECL-NET-QTY",
            rule_pack_version=RULE_PACK_VERSION,
            title="Net Quantity Declaration and Standard Unit",
            legal_citation=citation,
            status=FindingStatus.PASS,
            severity=FindingSeverity.INFO,
            message=f"Net quantity valid: '{field.raw_value}' (Normalized: {field.normalized_value} {field.unit}).",
            field_references_json={"field_name": "net_quantity", "field_id": field.field_id}
        )

    def _eval_mrp(self, inspection_id: str, field: Optional[ExtractedField]) -> RuleFinding:
        citation = "Rule 6(1)(e), Legal Metrology (Packaged Commodities) Rules, 2011"
        if not field or not field.raw_value or field.field_status == FieldStatus.MISSING:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-MRP",
                rule_pack_version=RULE_PACK_VERSION,
                title="Maximum Retail Price (MRP) Declaration",
                legal_citation=citation,
                status=FindingStatus.FAIL,
                severity=FindingSeverity.CRITICAL,
                message="Mandatory retail sale price (MRP) declaration is missing.",
                field_references_json={"field_name": "mrp"}
            )

        if field.field_status in (FieldStatus.UNCERTAIN, FieldStatus.MANUAL_REVIEW):
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-MRP",
                rule_pack_version=RULE_PACK_VERSION,
                title="Maximum Retail Price (MRP) Declaration",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.HIGH,
                message=f"MRP extraction uncertain: '{field.raw_value}'. Requires officer review.",
                field_references_json={"field_name": "mrp", "field_id": field.field_id}
            )

        if field.field_status == FieldStatus.CONFLICTING:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-MRP",
                rule_pack_version=RULE_PACK_VERSION,
                title="Maximum Retail Price (MRP) Declaration",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.HIGH,
                message=f"Discrepancy in MRP detected across evidence views. Raw value: '{field.raw_value}'. Requires officer review.",
                field_references_json={"field_name": "mrp", "field_id": field.field_id}
            )

        return RuleFinding(
            finding_id=str(uuid.uuid4()),
            inspection_id=inspection_id,
            rule_id="RULE-DECL-MRP",
            rule_pack_version=RULE_PACK_VERSION,
            title="Maximum Retail Price (MRP) Declaration",
            legal_citation=citation,
            status=FindingStatus.PASS,
            severity=FindingSeverity.INFO,
            message=f"MRP declaration verified: '{field.raw_value}' (Normalized: ₹ {field.normalized_value}).",
            field_references_json={"field_name": "mrp", "field_id": field.field_id}
        )

    def _eval_manufacturer(self, inspection_id: str, field: Optional[ExtractedField]) -> RuleFinding:
        citation = "Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011"
        if not field or not field.raw_value or field.field_status == FieldStatus.MISSING:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-MFR-PACKER",
                rule_pack_version=RULE_PACK_VERSION,
                title="Manufacturer / Packer / Importer Details",
                legal_citation=citation,
                status=FindingStatus.FAIL,
                severity=FindingSeverity.HIGH,
                message="Name and complete address of the manufacturer or packer was not found.",
                field_references_json={"field_name": "manufacturer"}
            )

        if field.field_status in (FieldStatus.UNCERTAIN, FieldStatus.MANUAL_REVIEW):
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-MFR-PACKER",
                rule_pack_version=RULE_PACK_VERSION,
                title="Manufacturer / Packer / Importer Details",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.HIGH,
                message=f"Manufacturer/Packer details uncertain: '{field.raw_value}'. Officer verification required.",
                field_references_json={"field_name": "manufacturer", "field_id": field.field_id}
            )

        return RuleFinding(
            finding_id=str(uuid.uuid4()),
            inspection_id=inspection_id,
            rule_id="RULE-DECL-MFR-PACKER",
            rule_pack_version=RULE_PACK_VERSION,
            title="Manufacturer / Packer / Importer Details",
            legal_citation=citation,
            status=FindingStatus.PASS,
            severity=FindingSeverity.INFO,
            message=f"Manufacturer/Packer details identified: '{field.raw_value}'.",
            field_references_json={"field_name": "manufacturer", "field_id": field.field_id}
        )

    def _eval_country_of_origin(self, inspection_id: str, field: Optional[ExtractedField]) -> RuleFinding:
        citation = "Rule 6(10), Legal Metrology (Packaged Commodities) Rules, 2011"
        if not field or not field.raw_value:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-COUNTRY-ORIGIN",
                rule_pack_version=RULE_PACK_VERSION,
                title="Country of Origin Declaration",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.LOW,
                message="Country of origin not explicitly detected. Mandatory for imported goods; officer verification recommended.",
                field_references_json={"field_name": "country_of_origin"}
            )

        return RuleFinding(
            finding_id=str(uuid.uuid4()),
            inspection_id=inspection_id,
            rule_id="RULE-DECL-COUNTRY-ORIGIN",
            rule_pack_version=RULE_PACK_VERSION,
            title="Country of Origin Declaration",
            legal_citation=citation,
            status=FindingStatus.PASS,
            severity=FindingSeverity.INFO,
            message=f"Country of origin identified: '{field.raw_value}'.",
            field_references_json={"field_name": "country_of_origin", "field_id": field.field_id}
        )

    def _eval_consumer_care(self, inspection_id: str, field: Optional[ExtractedField]) -> RuleFinding:
        citation = "Rule 6(1)(f), Legal Metrology (Packaged Commodities) Rules, 2011"
        if not field or not field.raw_value or field.field_status == FieldStatus.MISSING:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-CONSUMER-CARE",
                rule_pack_version=RULE_PACK_VERSION,
                title="Consumer Care Executive Contact Details",
                legal_citation=citation,
                status=FindingStatus.FAIL,
                severity=FindingSeverity.HIGH,
                message="Consumer care contact details (telephone, email, or address) are missing.",
                field_references_json={"field_name": "consumer_care"}
            )

        if field.field_status in (FieldStatus.UNCERTAIN, FieldStatus.MANUAL_REVIEW):
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-CONSUMER-CARE",
                rule_pack_version=RULE_PACK_VERSION,
                title="Consumer Care Executive Contact Details",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.HIGH,
                message=f"Consumer care contact details uncertain: '{field.raw_value}'. Officer verification required.",
                field_references_json={"field_name": "consumer_care", "field_id": field.field_id}
            )

        return RuleFinding(
            finding_id=str(uuid.uuid4()),
            inspection_id=inspection_id,
            rule_id="RULE-DECL-CONSUMER-CARE",
            rule_pack_version=RULE_PACK_VERSION,
            title="Consumer Care Executive Contact Details",
            legal_citation=citation,
            status=FindingStatus.PASS,
            severity=FindingSeverity.INFO,
            message=f"Consumer care contact details identified: '{field.raw_value}'.",
            field_references_json={"field_name": "consumer_care", "field_id": field.field_id}
        )

    def _eval_manufacture_date(self, inspection_id: str, field: Optional[ExtractedField]) -> RuleFinding:
        citation = "Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011"
        if not field or not field.raw_value or field.field_status == FieldStatus.MISSING:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-DATE-MARKS",
                rule_pack_version=RULE_PACK_VERSION,
                title="Month and Year of Manufacture / Packing",
                legal_citation=citation,
                status=FindingStatus.FAIL,
                severity=FindingSeverity.HIGH,
                message="Month and year of manufacture or pre-packing is missing.",
                field_references_json={"field_name": "manufacture_date"}
            )

        if field.field_status in (FieldStatus.UNCERTAIN, FieldStatus.MANUAL_REVIEW):
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-DECL-DATE-MARKS",
                rule_pack_version=RULE_PACK_VERSION,
                title="Month and Year of Manufacture / Packing",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.HIGH,
                message=f"Month and year of manufacture/packing uncertain: '{field.raw_value}'. Officer verification required.",
                field_references_json={"field_name": "manufacture_date", "field_id": field.field_id}
            )

        return RuleFinding(
            finding_id=str(uuid.uuid4()),
            inspection_id=inspection_id,
            rule_id="RULE-DECL-DATE-MARKS",
            rule_pack_version=RULE_PACK_VERSION,
            title="Month and Year of Manufacture / Packing",
            legal_citation=citation,
            status=FindingStatus.PASS,
            severity=FindingSeverity.INFO,
            message=f"Date of manufacture/packing identified: '{field.raw_value}'.",
            field_references_json={"field_name": "manufacture_date", "field_id": field.field_id}
        )

    def _eval_unit_sale_price_consistency(
        self,
        inspection_id: str,
        mrp_field: Optional[ExtractedField],
        qty_field: Optional[ExtractedField],
        usp_field: Optional[ExtractedField]
    ) -> RuleFinding:
        citation = "Rule 6(1)(e) Proviso, Legal Metrology (Packaged Commodities) Rules, 2011 (Amendments)"
        if not mrp_field or not qty_field or not mrp_field.normalized_value or not qty_field.normalized_value:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-USP-CONSISTENCY",
                rule_pack_version=RULE_PACK_VERSION,
                title="Unit Sale Price (USP) Arithmetic Consistency",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.MEDIUM,
                message="Unit Sale Price calculation unavailable due to missing MRP or Net Quantity declaration.",
                field_references_json={"fields": ["mrp", "net_quantity"]}
            )

        try:
            mrp_dec = Decimal(mrp_field.normalized_value)
            qty_dec = Decimal(qty_field.normalized_value)
            base_unit = qty_field.unit or "unit"
        except (InvalidOperation, TypeError):
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-USP-CONSISTENCY",
                rule_pack_version=RULE_PACK_VERSION,
                title="Unit Sale Price (USP) Arithmetic Consistency",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.MEDIUM,
                message="Invalid numerical values for MRP or Net Quantity.",
                field_references_json={"fields": ["mrp", "net_quantity"]}
            )

        calc_result = NormalizationService.calculate_unit_sale_price(mrp_dec, qty_dec, base_unit)
        if not calc_result.get("is_computable"):
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-USP-CONSISTENCY",
                rule_pack_version=RULE_PACK_VERSION,
                title="Unit Sale Price (USP) Arithmetic Consistency",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.MEDIUM,
                message=f"Computation error: {calc_result.get('error')}",
                field_references_json={"fields": ["mrp", "net_quantity"]}
            )

        expected_usp = calc_result["calculated_usp"]

        # If a printed USP was extracted, compare arithmetic consistency
        if usp_field and usp_field.normalized_value:
            try:
                printed_usp = float(Decimal(usp_field.normalized_value))
                printed_raw = (usp_field.raw_value or "").lower()
                
                # Check for legal unit sub-scales (per g vs per kg, per ml vs per L, per 100g vs per kg)
                scale = 1.0
                if any(x in printed_raw for x in ["per g", "/g", "perg", "per gm", "/gm", "per gram"]):
                    if base_unit == "kg":
                        scale = 1000.0
                elif any(x in printed_raw for x in ["per 100g", "/100g", "/100 gm", "per 100 gm"]):
                    if base_unit == "kg":
                        scale = 10.0
                elif any(x in printed_raw for x in ["per ml", "/ml", "perml", "per millilitre"]):
                    if base_unit == "L":
                        scale = 1000.0
                elif any(x in printed_raw for x in ["per 100ml", "/100ml", "per 100 ml"]):
                    if base_unit == "L":
                        scale = 10.0

                printed_usp_scaled = printed_usp * scale
                diff = min(abs(expected_usp - printed_usp), abs(expected_usp - printed_usp_scaled))

                calc_metadata = {
                    "mrp": float(mrp_dec),
                    "normalized_quantity": float(qty_dec),
                    "base_unit": base_unit,
                    "expected_usp": expected_usp,
                    "printed_usp": printed_usp,
                    "scale_applied": scale,
                    "diff": round(diff, 2)
                }

                # Allow 5.0% tolerance for rounding difference
                if diff > 0.05 * expected_usp and diff > 0.05 * (expected_usp / scale):
                    return RuleFinding(
                        finding_id=str(uuid.uuid4()),
                        inspection_id=inspection_id,
                        rule_id="RULE-USP-CONSISTENCY",
                        rule_pack_version=RULE_PACK_VERSION,
                        title="Unit Sale Price (USP) Arithmetic Consistency",
                        legal_citation=citation,
                        status=FindingStatus.FAIL,
                        severity=FindingSeverity.HIGH,
                        message=f"Printed Unit Sale Price ₹{printed_usp:.2f} does not match computed price ₹{expected_usp:.2f}/{base_unit} (MRP ₹{mrp_dec} / {qty_dec} {base_unit}).",
                        field_references_json={"fields": ["mrp", "net_quantity", "unit_sale_price"]},
                        calculation_metadata_json=calc_metadata
                    )

                return RuleFinding(
                    finding_id=str(uuid.uuid4()),
                    inspection_id=inspection_id,
                    rule_id="RULE-USP-CONSISTENCY",
                    rule_pack_version=RULE_PACK_VERSION,
                    title="Unit Sale Price (USP) Arithmetic Consistency",
                    legal_citation=citation,
                    status=FindingStatus.PASS,
                    severity=FindingSeverity.INFO,
                    message=f"Printed Unit Sale Price '{usp_field.raw_value}' is consistent with calculated price ₹{expected_usp:.2f}/{base_unit}.",
                    field_references_json={"fields": ["mrp", "net_quantity", "unit_sale_price"]},
                    calculation_metadata_json=calc_metadata
                )
            except (InvalidOperation, ValueError):
                pass

        # If USP not printed, provide calculated arithmetic value
        return RuleFinding(
            finding_id=str(uuid.uuid4()),
            inspection_id=inspection_id,
            rule_id="RULE-USP-CONSISTENCY",
            rule_pack_version=RULE_PACK_VERSION,
            title="Unit Sale Price (USP) Arithmetic Consistency",
            legal_citation=citation,
            status=FindingStatus.PASS,
            severity=FindingSeverity.INFO,
            message=f"Calculated Unit Sale Price: {calc_result['unit_price_string']} (MRP ₹{mrp_dec} / {qty_dec} {base_unit}).",
            field_references_json={"fields": ["mrp", "net_quantity"]},
            calculation_metadata_json=calc_result
        )

    def _eval_font_height_statutory(self, inspection_id: str, qty_field: Optional[ExtractedField]) -> RuleFinding:
        citation = "Rule 7, Legal Metrology (Packaged Commodities) Rules, 2011"
        from app.models.domain import VisualMeasurement
        from app.services.font_threshold_config import (
            FontThresholdRegistry,
            CharacterType,
            DeclarationMethod,
            ThresholdVerificationStatus
        )

        # Gate 1: Check for active visual measurements in this case
        measurement = self.db.query(VisualMeasurement).filter(
            VisualMeasurement.inspection_id == inspection_id,
            VisualMeasurement.status == "MEASURED",
            VisualMeasurement.physical_value.isnot(None)
        ).first()

        if not measurement or not measurement.physical_value:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-FONT-HEIGHT-MINIMUM",
                rule_pack_version=RULE_PACK_VERSION,
                title="Minimum Declaration Font Height Check",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.LOW,
                message="Font-size verification requires a reliable physical calibration reference (e.g. standard Rs 5 coin).",
                field_references_json={"rule": "RULE-FONT-HEIGHT-MINIMUM"}
            )

        measured_mm = measurement.physical_value

        # Gate 2: Validate Principal Display Panel Area (A in cm²)
        # Statutorily required to index Rule 7 Table 1. Net Quantity must have NO surrogate role.
        pdp_area = getattr(measurement, "pdp_area_cm2", None)
        if pdp_area is None or pdp_area <= 0:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-FONT-HEIGHT-MINIMUM",
                rule_pack_version=RULE_PACK_VERSION,
                title="Minimum Declaration Font Height Check",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.LOW,
                message="Physical character height was measured, but Principal Display Panel area (A in cm²) is required under Rule 7 Table 1 to establish the statutory threshold. Officer manual verification required.",
                field_references_json={"rule": "RULE-FONT-HEIGHT-MINIMUM"},
                calculation_metadata_json={
                    "measured_font_height_mm": measured_mm,
                    "threshold_status": "PDP_AREA_UNAVAILABLE",
                    "pdp_area_cm2": None,
                    "pdp_area_source": getattr(measurement, "pdp_area_source", "UNKNOWN")
                }
            )

        # Gate 3: Validate Character Type applicability input
        char_type_str = getattr(measurement, "character_type", "UNKNOWN") or "UNKNOWN"
        try:
            char_type = CharacterType(char_type_str)
        except ValueError:
            char_type = CharacterType.UNKNOWN

        if char_type == CharacterType.UNKNOWN:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-FONT-HEIGHT-MINIMUM",
                rule_pack_version=RULE_PACK_VERSION,
                title="Minimum Declaration Font Height Check",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.LOW,
                message="Applicable Rule 7 statutory threshold could not be established: Character type (Letter vs Numeral) is undetermined. Officer manual verification required.",
                field_references_json={"rule": "RULE-FONT-HEIGHT-MINIMUM"},
                calculation_metadata_json={
                    "measured_font_height_mm": measured_mm,
                    "threshold_status": "CHARACTER_TYPE_UNKNOWN",
                    "pdp_area_cm2": pdp_area
                }
            )

        # Gate 4: Validate Declaration Method input
        decl_method_str = getattr(measurement, "declaration_method", "NORMAL_PRINT") or "NORMAL_PRINT"
        try:
            decl_method = DeclarationMethod(decl_method_str)
        except ValueError:
            decl_method = DeclarationMethod.UNKNOWN

        if decl_method == DeclarationMethod.UNKNOWN:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-FONT-HEIGHT-MINIMUM",
                rule_pack_version=RULE_PACK_VERSION,
                title="Minimum Declaration Font Height Check",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.LOW,
                message="Applicable Rule 7 statutory threshold could not be established: Declaration/substrate method is undetermined. Officer manual verification required.",
                field_references_json={"rule": "RULE-FONT-HEIGHT-MINIMUM"},
                calculation_metadata_json={
                    "measured_font_height_mm": measured_mm,
                    "threshold_status": "DECLARATION_METHOD_UNKNOWN",
                    "pdp_area_cm2": pdp_area
                }
            )

        # Gate 5: Strict Authoritative Threshold Lookup by PDP Area A (NO quantity surrogate / NO arbitrary fallback)
        statutory_threshold = FontThresholdRegistry.lookup_threshold(
            character_type=char_type,
            pdp_area_cm2=pdp_area,
            declaration_method=decl_method,
            rule_pack_version=RULE_PACK_VERSION
        )

        if not statutory_threshold or statutory_threshold.verification_status != ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-FONT-HEIGHT-MINIMUM",
                rule_pack_version=RULE_PACK_VERSION,
                title="Minimum Declaration Font Height Check",
                legal_citation=citation,
                status=FindingStatus.REVIEW,
                severity=FindingSeverity.LOW,
                message="Physical character height was measured, but the applicable Rule 7 statutory threshold could not be established from the verified rule configuration for the given PDP area. Officer manual verification required.",
                field_references_json={"rule": "RULE-FONT-HEIGHT-MINIMUM"},
                calculation_metadata_json={
                    "measured_font_height_mm": measured_mm,
                    "threshold_status": "NOT_CONFIGURED",
                    "pdp_area_cm2": pdp_area
                }
            )

        statutory_min_mm = statutory_threshold.minimum_height_mm
        calc_meta = {
            "measured_font_height_mm": measured_mm,
            "statutory_minimum_mm": statutory_min_mm,
            "pdp_area_cm2": pdp_area,
            "pdp_area_source": getattr(measurement, "pdp_area_source", "UNKNOWN"),
            "threshold_id": statutory_threshold.threshold_id,
            "legal_citation": statutory_threshold.legal_citation,
            "character_type": char_type.value,
            "declaration_method": decl_method.value,
            "measurement_id": measurement.measurement_id,
            "confidence": measurement.confidence
        }

        # Check Rule 7(3) width-to-height ratio (width must be >= 1/3 height, except '1', 'i', 'I', 'l')
        # If OCR bounding box width is available and target text is not an exception
        target_txt = getattr(measurement, "target_text", "") or ""
        if target_txt and target_txt not in ("1", "i", "I", "l") and measurement.source_bbox_json:
            bbox = measurement.source_bbox_json
            if isinstance(bbox, list) and len(bbox) >= 4:
                x_coords = [p[0] for p in bbox if isinstance(p, list) and len(p) >= 2]
                if x_coords:
                    char_w_px = float(max(x_coords) - min(x_coords))
                    char_h_px = measurement.pixel_value
                    if char_h_px > 0 and char_w_px < (char_h_px / 3.0):
                        calc_meta["width_check"] = "BELOW_RATIO"
                        calc_meta["width_px"] = char_w_px
                        calc_meta["height_px"] = char_h_px

        if measured_mm < statutory_min_mm:
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-FONT-HEIGHT-MINIMUM",
                rule_pack_version=RULE_PACK_VERSION,
                title="Minimum Declaration Font Height Check",
                legal_citation=statutory_threshold.legal_citation,
                status=FindingStatus.FAIL,
                severity=FindingSeverity.HIGH,
                message=f"Estimated declaration character height ({measured_mm:.1f} mm) is below the statutory minimum ({statutory_min_mm:.1f} mm) prescribed under {statutory_threshold.legal_citation} for PDP area {pdp_area:.1f} cm².",
                field_references_json={"rule": "RULE-FONT-HEIGHT-MINIMUM"},
                calculation_metadata_json=calc_meta
            )

        return RuleFinding(
            finding_id=str(uuid.uuid4()),
            inspection_id=inspection_id,
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version=RULE_PACK_VERSION,
            title="Minimum Declaration Font Height Check",
            legal_citation=statutory_threshold.legal_citation,
            status=FindingStatus.PASS,
            severity=FindingSeverity.INFO,
            message=f"Estimated declaration character height ({measured_mm:.1f} mm) satisfies statutory minimum threshold ({statutory_min_mm:.1f} mm) under {statutory_threshold.legal_citation} for PDP area {pdp_area:.1f} cm².",
            field_references_json={"rule": "RULE-FONT-HEIGHT-MINIMUM"},
            calculation_metadata_json=calc_meta
        )


    def _eval_price_overwrite_signal(self, inspection_id: str, mrp_field: Optional[ExtractedField]) -> RuleFinding:

        citation = "Rule 6(2), Legal Metrology (Packaged Commodities) Rules, 2011"
        from app.models.domain import VisualAnomaly

        anomalies = self.db.query(VisualAnomaly).filter(
            VisualAnomaly.inspection_id == inspection_id,
            VisualAnomaly.status == "DETECTED"
        ).all()

        if anomalies:
            anomaly_types = [a.anomaly_type for a in anomalies]
            return RuleFinding(
                finding_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                rule_id="RULE-OVERLAY-STICKER-FLAG",
                rule_pack_version=RULE_PACK_VERSION,
                title="Price Overwrite / Label Sticker Signal Check",
                legal_citation=citation,
                status=FindingStatus.REVIEW, # CRITICAL: Pure visual suspicion signal must NEVER produce FAIL
                severity=FindingSeverity.HIGH,
                message=f"Visual anomaly detected ({', '.join(anomaly_types)}). Officer verification required to confirm if sticker constitutes prohibited alteration.",
                field_references_json={"field_name": "mrp"},
                evidence_references_json={"anomalies_count": len(anomalies)}
            )

        return RuleFinding(
            finding_id=str(uuid.uuid4()),
            inspection_id=inspection_id,
            rule_id="RULE-OVERLAY-STICKER-FLAG",
            rule_pack_version=RULE_PACK_VERSION,
            title="Price Overwrite / Label Sticker Signal Check",
            legal_citation=citation,
            status=FindingStatus.PASS,
            severity=FindingSeverity.INFO,
            message="No obvious price label sticker overlay detected on package.",
            field_references_json={"field_name": "mrp"}
        )

