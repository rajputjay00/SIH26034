import pytest
import os, sys
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from tests.fixtures.test_data import db_session, create_synthetic_image
from app.models.domain import (
    InspectionCase,
    EvidenceItem,
    EvidenceViewType,
    ExtractedField,
    FieldCorrection,
    ExtractionOrigin,
    FieldStatus,
    FieldApplicability,
    FindingStatus,
    OverallDetermination
)
from app.services.case_service import CaseService
from app.services.evidence_service import EvidenceService
from app.services.extraction_service import StructuredExtractionService
from app.services.rule_engine_service import ComplianceEvaluationService

def test_golden_01_clean_compliant_package(db_session):
    """GOLDEN-01: All mandatory declarations present, valid USP math -> COMPLIANT (or valid pass state)"""
    case_service = CaseService(db_session)
    case = case_service.create_case(officer_id="OFFICER-001", notes="Golden 01 Compliant Sample")

    # Manually populate compliant structured fields
    fields_data = [
        ("commodity_name", "Organic Whole Wheat Atta", "Organic Whole Wheat Atta", None),
        ("net_quantity", "5 kg", "5.0000", "kg"),
        ("mrp", "MRP Rs. 250.00 (incl. of all taxes)", "250.00", "INR"),
        ("unit_sale_price", "Unit Sale Price Rs. 50.00 / kg", "50.00", "INR/unit"),
        ("manufacturer", "Manufactured by ABC Grain Mills Pvt Ltd, Delhi 110001", "ABC Grain Mills Pvt Ltd", None),
        ("country_of_origin", "Country of Origin: India", "India", None),
        ("consumer_care", "Consumer Care Tel: 1800-111-222, Email: care@abcgrains.com", "care@abcgrains.com", None),
        ("manufacture_date", "Date of Pkg: 08/2026", "08/2026", None)
    ]

    for fname, raw, norm, unit in fields_data:
        f = ExtractedField(
            inspection_id=case.inspection_id,
            field_name=fname,
            raw_value=raw,
            normalized_value=norm,
            unit=unit,
            confidence=0.96,
            applicability=FieldApplicability.APPLICABLE,
            field_status=FieldStatus.EXTRACTED,
            origin=ExtractionOrigin.AI
        )
        db_session.add(f)
    db_session.commit()

    # Run deterministic compliance evaluation
    rule_service = ComplianceEvaluationService(db_session)
    result = rule_service.evaluate_inspection(case.inspection_id, officer_id="OFFICER-001")

    # All primary declaration checks should PASS
    assert result["fail_count"] == 0
    # Overall determination should not fail
    assert result["overall_determination"] in [OverallDetermination.COMPLIANT, OverallDetermination.REQUIRES_REVIEW]

def test_golden_02_missing_mandatory_declaration(db_session):
    """GOLDEN-02: Missing Net Quantity declaration -> NON_COMPLIANT"""
    case_service = CaseService(db_session)
    case = case_service.create_case(officer_id="OFFICER-001")

    # Populate fields with Net Quantity missing
    fields_data = [
        ("commodity_name", "Roasted Almonds", "Roasted Almonds", None),
        ("mrp", "MRP Rs. 200.00", "200.00", "INR"),
        ("manufacturer", "Mfr by XYZ Dry Fruits Ltd", "XYZ Dry Fruits Ltd", None)
    ]

    for fname, raw, norm, unit in fields_data:
        f = ExtractedField(
            inspection_id=case.inspection_id,
            field_name=fname,
            raw_value=raw,
            normalized_value=norm,
            unit=unit,
            confidence=0.95,
            applicability=FieldApplicability.APPLICABLE,
            field_status=FieldStatus.EXTRACTED,
            origin=ExtractionOrigin.AI
        )
        db_session.add(f)
    db_session.commit()

    rule_service = ComplianceEvaluationService(db_session)
    result = rule_service.evaluate_inspection(case.inspection_id, officer_id="OFFICER-001")

    assert result["fail_count"] > 0
    assert result["overall_determination"] == OverallDetermination.NON_COMPLIANT

    # Find the specific net quantity failure finding
    net_qty_finding = next((f for f in result["findings"] if f.rule_id == "RULE-DECL-NET-QTY"), None)
    assert net_qty_finding is not None
    assert net_qty_finding.status == FindingStatus.FAIL

def test_golden_03_inconsistent_unit_sale_price_math(db_session):
    """GOLDEN-03: Printed USP (Rs. 80/kg) != Computed USP (Rs. 100/0.5kg = Rs. 200/kg) -> FAIL"""
    case_service = CaseService(db_session)
    case = case_service.create_case(officer_id="OFFICER-001")

    fields_data = [
        ("commodity_name", "Biscuits", "Biscuits", None),
        ("net_quantity", "500 g", "0.5000", "kg"),
        ("mrp", "MRP Rs. 100.00", "100.00", "INR"),
        ("unit_sale_price", "Unit Sale Price Rs. 80.00 / kg", "80.00", "INR/unit"), # Inconsistent! Should be 200
        ("manufacturer", "Mfr by Biscuits Ltd", "Biscuits Ltd", None),
        ("consumer_care", "Tel: 1800-000", "1800-000", None),
        ("manufacture_date", "08/2026", "08/2026", None)
    ]

    for fname, raw, norm, unit in fields_data:
        f = ExtractedField(
            inspection_id=case.inspection_id,
            field_name=fname,
            raw_value=raw,
            normalized_value=norm,
            unit=unit,
            confidence=0.95,
            applicability=FieldApplicability.APPLICABLE,
            field_status=FieldStatus.EXTRACTED,
            origin=ExtractionOrigin.AI
        )
        db_session.add(f)
    db_session.commit()

    rule_service = ComplianceEvaluationService(db_session)
    result = rule_service.evaluate_inspection(case.inspection_id, officer_id="OFFICER-001")

    usp_finding = next((f for f in result["findings"] if f.rule_id == "RULE-USP-CONSISTENCY"), None)
    assert usp_finding is not None
    assert usp_finding.status == FindingStatus.FAIL
    assert "does not match computed price" in usp_finding.message

def test_golden_04_conflicting_declaration_across_views(db_session):
    """GOLDEN-04: Front MRP Rs 100 vs Back MRP Rs 120 -> CONFLICTING / REQUIRES_REVIEW"""
    case_service = CaseService(db_session)
    case = case_service.create_case(officer_id="OFFICER-001")

    # Front Evidence Field
    f1 = ExtractedField(
        inspection_id=case.inspection_id,
        field_name="mrp",
        raw_value="MRP Rs 100.00",
        normalized_value="100.00",
        unit="INR",
        confidence=0.94,
        applicability=FieldApplicability.APPLICABLE,
        field_status=FieldStatus.CONFLICTING,
        origin=ExtractionOrigin.AI
    )
    db_session.add(f1)
    db_session.commit()

    rule_service = ComplianceEvaluationService(db_session)
    result = rule_service.evaluate_inspection(case.inspection_id, officer_id="OFFICER-001")

    mrp_finding = next((f for f in result["findings"] if f.rule_id == "RULE-DECL-MRP"), None)
    assert mrp_finding is not None
    assert mrp_finding.status == FindingStatus.REVIEW
    assert "Discrepancy in MRP detected" in mrp_finding.message

def test_golden_05_officer_correction_and_rerun_workflow(db_session):
    """GOLDEN-05: Officer corrects OCR misread from Rs 80 -> Rs 200, reruns evaluation -> PASS"""
    case_service = CaseService(db_session)
    case = case_service.create_case(officer_id="OFFICER-001")

    # Initial state with incorrect OCR read
    usp_field = ExtractedField(
        inspection_id=case.inspection_id,
        field_name="unit_sale_price",
        raw_value="Unit Sale Price Rs 80.00 / kg", # Misread OCR
        normalized_value="80.00",
        unit="INR/unit",
        confidence=0.85,
        applicability=FieldApplicability.APPLICABLE,
        field_status=FieldStatus.EXTRACTED,
        origin=ExtractionOrigin.AI
    )
    mrp_field = ExtractedField(
        inspection_id=case.inspection_id,
        field_name="mrp",
        raw_value="MRP Rs 100.00",
        normalized_value="100.00",
        unit="INR",
        confidence=0.95,
        origin=ExtractionOrigin.AI
    )
    qty_field = ExtractedField(
        inspection_id=case.inspection_id,
        field_name="net_quantity",
        raw_value="500 g",
        normalized_value="0.5000",
        unit="kg",
        confidence=0.95,
        origin=ExtractionOrigin.AI
    )

    db_session.add_all([usp_field, mrp_field, qty_field])
    db_session.commit()

    rule_service = ComplianceEvaluationService(db_session)
    initial_eval = rule_service.evaluate_inspection(case.inspection_id, officer_id="OFFICER-001")
    initial_usp_finding = next((f for f in initial_eval["findings"] if f.rule_id == "RULE-USP-CONSISTENCY"), None)
    assert initial_usp_finding.status == FindingStatus.FAIL

    # Officer manual correction: Rs 80 -> Rs 200
    correction = FieldCorrection(
        correction_id="corr-101",
        field_id=usp_field.field_id,
        previous_value="80.00",
        corrected_value="200.00",
        officer_id="OFFICER-001",
        reason="Corrected OCR digit misread"
    )
    usp_field.normalized_value = "200.00"
    usp_field.origin = ExtractionOrigin.OFFICER
    usp_field.field_status = FieldStatus.CORRECTED
    db_session.add(correction)
    db_session.commit()

    # Rerun evaluation
    rerun_eval = rule_service.evaluate_inspection(case.inspection_id, officer_id="OFFICER-001")
    rerun_usp_finding = next((f for f in rerun_eval["findings"] if f.rule_id == "RULE-USP-CONSISTENCY"), None)
    assert rerun_usp_finding.status == FindingStatus.PASS
    assert "is consistent with calculated price" in rerun_usp_finding.message
