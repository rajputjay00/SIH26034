import pytest
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from tests.fixtures.test_data import db_session
from app.models.domain import (
    InspectionCase,
    VisualMeasurement,
    VisualAnomaly,
    ExtractedField,
    ExtractionOrigin,
    FindingStatus,
    OverallDetermination
)
from app.services.case_service import CaseService
from app.services.rule_engine_service import ComplianceEvaluationService
from app.services.font_threshold_config import (
    FontThresholdRegistry,
    CharacterType,
    DeclarationMethod,
    ThresholdVerificationStatus
)

def test_01_pdp_40cm2_letter_normal_print_1_2mm_passes(db_session):
    """TEST 1: PDP area 40 cm², LETTER, NORMAL_PRINT, Measured height 1.2 mm -> PASS (min 1.0 mm)"""
    case = CaseService(db_session).create_case(officer_id="OFF-001")
    meas = VisualMeasurement(
        inspection_id=case.inspection_id, evidence_id="ev-1", measurement_type="FONT_HEIGHT",
        target_text="Net Wt", character_type="LETTER", pdp_area_cm2=40.0,
        declaration_method="NORMAL_PRINT", pixel_value=20.0, physical_value=1.2, status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    result = ComplianceEvaluationService(db_session).evaluate_inspection(case.inspection_id)
    finding = next(f for f in result["findings"] if f.rule_id == "RULE-FONT-HEIGHT-MINIMUM")

    assert finding.status == FindingStatus.PASS
    assert finding.calculation_metadata_json["statutory_minimum_mm"] == 1.0

def test_02_pdp_40cm2_numeral_normal_print_1_2mm_fails(db_session):
    """TEST 2: PDP area 40 cm², NUMERAL, NORMAL_PRINT, Measured height 1.2 mm -> FAIL (min 1.5 mm)"""
    case = CaseService(db_session).create_case(officer_id="OFF-001")
    meas = VisualMeasurement(
        inspection_id=case.inspection_id, evidence_id="ev-1", measurement_type="FONT_HEIGHT",
        target_text="50", character_type="NUMERAL", pdp_area_cm2=40.0,
        declaration_method="NORMAL_PRINT", pixel_value=20.0, physical_value=1.2, status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    result = ComplianceEvaluationService(db_session).evaluate_inspection(case.inspection_id)
    finding = next(f for f in result["findings"] if f.rule_id == "RULE-FONT-HEIGHT-MINIMUM")

    assert finding.status == FindingStatus.FAIL
    assert finding.calculation_metadata_json["statutory_minimum_mm"] == 1.5

def test_03_pdp_75cm2_letter_normal_print_1_6mm_passes(db_session):
    """TEST 3: PDP area 75 cm², LETTER, NORMAL_PRINT, Measured height 1.6 mm -> PASS (min 1.5 mm)"""
    case = CaseService(db_session).create_case(officer_id="OFF-001")
    meas = VisualMeasurement(
        inspection_id=case.inspection_id, evidence_id="ev-1", measurement_type="FONT_HEIGHT",
        target_text="Brand", character_type="LETTER", pdp_area_cm2=75.0,
        declaration_method="NORMAL_PRINT", pixel_value=25.0, physical_value=1.6, status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    result = ComplianceEvaluationService(db_session).evaluate_inspection(case.inspection_id)
    finding = next(f for f in result["findings"] if f.rule_id == "RULE-FONT-HEIGHT-MINIMUM")

    assert finding.status == FindingStatus.PASS
    assert finding.calculation_metadata_json["statutory_minimum_mm"] == 1.5

def test_04_pdp_75cm2_numeral_normal_print_1_9mm_fails(db_session):
    """TEST 4: PDP area 75 cm², NUMERAL, NORMAL_PRINT, Measured height 1.9 mm -> FAIL (min 2.0 mm)"""
    case = CaseService(db_session).create_case(officer_id="OFF-001")
    meas = VisualMeasurement(
        inspection_id=case.inspection_id, evidence_id="ev-1", measurement_type="FONT_HEIGHT",
        target_text="100", character_type="NUMERAL", pdp_area_cm2=75.0,
        declaration_method="NORMAL_PRINT", pixel_value=25.0, physical_value=1.9, status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    result = ComplianceEvaluationService(db_session).evaluate_inspection(case.inspection_id)
    finding = next(f for f in result["findings"] if f.rule_id == "RULE-FONT-HEIGHT-MINIMUM")

    assert finding.status == FindingStatus.FAIL
    assert finding.calculation_metadata_json["statutory_minimum_mm"] == 2.0

def test_05_pdp_300cm2_letter_normal_print_2_4mm_fails(db_session):
    """TEST 5: PDP area 300 cm², LETTER, NORMAL_PRINT, Measured height 2.4 mm -> FAIL (min 2.5 mm)"""
    case = CaseService(db_session).create_case(officer_id="OFF-001")
    meas = VisualMeasurement(
        inspection_id=case.inspection_id, evidence_id="ev-1", measurement_type="FONT_HEIGHT",
        target_text="Commodity", character_type="LETTER", pdp_area_cm2=300.0,
        declaration_method="NORMAL_PRINT", pixel_value=30.0, physical_value=2.4, status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    result = ComplianceEvaluationService(db_session).evaluate_inspection(case.inspection_id)
    finding = next(f for f in result["findings"] if f.rule_id == "RULE-FONT-HEIGHT-MINIMUM")

    assert finding.status == FindingStatus.FAIL
    assert finding.calculation_metadata_json["statutory_minimum_mm"] == 2.5

def test_06_pdp_300cm2_numeral_normal_print_4_0mm_passes(db_session):
    """TEST 6: PDP area 300 cm², NUMERAL, NORMAL_PRINT, Measured height 4.0 mm -> PASS (min 4.0 mm)"""
    case = CaseService(db_session).create_case(officer_id="OFF-001")
    meas = VisualMeasurement(
        inspection_id=case.inspection_id, evidence_id="ev-1", measurement_type="FONT_HEIGHT",
        target_text="500", character_type="NUMERAL", pdp_area_cm2=300.0,
        declaration_method="NORMAL_PRINT", pixel_value=40.0, physical_value=4.0, status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    result = ComplianceEvaluationService(db_session).evaluate_inspection(case.inspection_id)
    finding = next(f for f in result["findings"] if f.rule_id == "RULE-FONT-HEIGHT-MINIMUM")

    assert finding.status == FindingStatus.PASS
    assert finding.calculation_metadata_json["statutory_minimum_mm"] == 4.0

def test_07_pdp_700cm2_letter_normal_print_3_9mm_fails(db_session):
    """TEST 7: PDP area 700 cm², LETTER, NORMAL_PRINT, Measured height 3.9 mm -> FAIL (min 4.0 mm)"""
    case = CaseService(db_session).create_case(officer_id="OFF-001")
    meas = VisualMeasurement(
        inspection_id=case.inspection_id, evidence_id="ev-1", measurement_type="FONT_HEIGHT",
        target_text="Manufacturer", character_type="LETTER", pdp_area_cm2=700.0,
        declaration_method="NORMAL_PRINT", pixel_value=40.0, physical_value=3.9, status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    result = ComplianceEvaluationService(db_session).evaluate_inspection(case.inspection_id)
    finding = next(f for f in result["findings"] if f.rule_id == "RULE-FONT-HEIGHT-MINIMUM")

    assert finding.status == FindingStatus.FAIL
    assert finding.calculation_metadata_json["statutory_minimum_mm"] == 4.0

def test_08_pdp_700cm2_letter_normal_print_4_0mm_passes(db_session):
    """TEST 8: PDP area 700 cm², LETTER, NORMAL_PRINT, Measured height 4.0 mm -> PASS (min 4.0 mm)"""
    case = CaseService(db_session).create_case(officer_id="OFF-001")
    meas = VisualMeasurement(
        inspection_id=case.inspection_id, evidence_id="ev-1", measurement_type="FONT_HEIGHT",
        target_text="Manufacturer", character_type="LETTER", pdp_area_cm2=700.0,
        declaration_method="NORMAL_PRINT", pixel_value=40.0, physical_value=4.0, status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    result = ComplianceEvaluationService(db_session).evaluate_inspection(case.inspection_id)
    finding = next(f for f in result["findings"] if f.rule_id == "RULE-FONT-HEIGHT-MINIMUM")

    assert finding.status == FindingStatus.PASS
    assert finding.calculation_metadata_json["statutory_minimum_mm"] == 4.0

def test_09_pdp_1200cm2_numeral_normal_print_6_0mm_passes(db_session):
    """TEST 9: PDP area 1200 cm², NUMERAL, NORMAL_PRINT, Measured height 6.0 mm -> PASS (min 6.0 mm)"""
    case = CaseService(db_session).create_case(officer_id="OFF-001")
    meas = VisualMeasurement(
        inspection_id=case.inspection_id, evidence_id="ev-1", measurement_type="FONT_HEIGHT",
        target_text="2500", character_type="NUMERAL", pdp_area_cm2=1200.0,
        declaration_method="NORMAL_PRINT", pixel_value=60.0, physical_value=6.0, status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    result = ComplianceEvaluationService(db_session).evaluate_inspection(case.inspection_id)
    finding = next(f for f in result["findings"] if f.rule_id == "RULE-FONT-HEIGHT-MINIMUM")

    assert finding.status == FindingStatus.PASS
    assert finding.calculation_metadata_json["statutory_minimum_mm"] == 6.0

def test_10_missing_pdp_area_with_net_quantity_available_yields_review(db_session):
    """TEST 10: CRITICAL - PDP area missing, Net Quantity available, Measured height 10.0 mm -> REVIEW"""
    case = CaseService(db_session).create_case(officer_id="OFF-001")
    db_session.add(ExtractedField(inspection_id=case.inspection_id, field_name="net_quantity", raw_value="500g", normalized_value="0.500", unit="kg", origin=ExtractionOrigin.AI))

    # PDP area is None
    meas = VisualMeasurement(
        inspection_id=case.inspection_id, evidence_id="ev-1", measurement_type="FONT_HEIGHT",
        target_text="MRP", character_type="LETTER", pdp_area_cm2=None,
        declaration_method="NORMAL_PRINT", pixel_value=50.0, physical_value=10.0, status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    result = ComplianceEvaluationService(db_session).evaluate_inspection(case.inspection_id)
    finding = next(f for f in result["findings"] if f.rule_id == "RULE-FONT-HEIGHT-MINIMUM")

    assert finding.status == FindingStatus.REVIEW
    assert "Principal Display Panel area (A in cm²) is required" in finding.message
    assert finding.calculation_metadata_json["threshold_status"] == "PDP_AREA_UNAVAILABLE"

def test_11_missing_pdp_area_large_qty_small_height_yields_review(db_session):
    """TEST 11: PDP area missing, Net Quantity = 1000g, Measured height = 1.0 mm -> REVIEW (never FAIL without PDP)"""
    case = CaseService(db_session).create_case(officer_id="OFF-001")
    db_session.add(ExtractedField(inspection_id=case.inspection_id, field_name="net_quantity", raw_value="1000g", normalized_value="1.000", unit="kg", origin=ExtractionOrigin.AI))

    meas = VisualMeasurement(
        inspection_id=case.inspection_id, evidence_id="ev-1", measurement_type="FONT_HEIGHT",
        target_text="Net", character_type="LETTER", pdp_area_cm2=None,
        declaration_method="NORMAL_PRINT", pixel_value=10.0, physical_value=1.0, status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    result = ComplianceEvaluationService(db_session).evaluate_inspection(case.inspection_id)
    finding = next(f for f in result["findings"] if f.rule_id == "RULE-FONT-HEIGHT-MINIMUM")

    assert finding.status == FindingStatus.REVIEW
    assert finding.calculation_metadata_json["threshold_status"] == "PDP_AREA_UNAVAILABLE"

def test_12_pdp_area_present_unknown_character_type_yields_review(db_session):
    """TEST 12: PDP area present, Character Type UNKNOWN -> REVIEW"""
    case = CaseService(db_session).create_case(officer_id="OFF-001")
    meas = VisualMeasurement(
        inspection_id=case.inspection_id, evidence_id="ev-1", measurement_type="FONT_HEIGHT",
        target_text="???", character_type="UNKNOWN", pdp_area_cm2=300.0,
        declaration_method="NORMAL_PRINT", pixel_value=30.0, physical_value=3.5, status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    result = ComplianceEvaluationService(db_session).evaluate_inspection(case.inspection_id)
    finding = next(f for f in result["findings"] if f.rule_id == "RULE-FONT-HEIGHT-MINIMUM")

    assert finding.status == FindingStatus.REVIEW
    assert "Character type (Letter vs Numeral) is undetermined" in finding.message
    assert finding.calculation_metadata_json["threshold_status"] == "CHARACTER_TYPE_UNKNOWN"

def test_13_pdp_area_present_unknown_declaration_method_yields_review(db_session):
    """TEST 13: PDP area present, Declaration Method UNKNOWN -> REVIEW"""
    case = CaseService(db_session).create_case(officer_id="OFF-001")
    meas = VisualMeasurement(
        inspection_id=case.inspection_id, evidence_id="ev-1", measurement_type="FONT_HEIGHT",
        target_text="Biscuits", character_type="LETTER", pdp_area_cm2=300.0,
        declaration_method="UNKNOWN", pixel_value=30.0, physical_value=3.5, status="MEASURED"
    )
    db_session.add(meas)
    db_session.commit()

    result = ComplianceEvaluationService(db_session).evaluate_inspection(case.inspection_id)
    finding = next(f for f in result["findings"] if f.rule_id == "RULE-FONT-HEIGHT-MINIMUM")

    assert finding.status == FindingStatus.REVIEW
    assert "Declaration/substrate method is undetermined" in finding.message
    assert finding.calculation_metadata_json["threshold_status"] == "DECLARATION_METHOD_UNKNOWN"

def test_14_unverified_threshold_yields_review(db_session):
    """TEST 14: Non-configured / unverified threshold lookup -> REVIEW"""
    # Negative PDP area or unsupported range
    lookup_res = FontThresholdRegistry.lookup_threshold(
        character_type=CharacterType.LETTER,
        pdp_area_cm2=-5.0,
        declaration_method=DeclarationMethod.NORMAL_PRINT
    )
    assert lookup_res is None

def test_15_sticker_anomaly_alone_strictly_yields_review(db_session):
    """TEST 15: Sticker anomaly present -> REVIEW, never independently NON_COMPLIANT"""
    case = CaseService(db_session).create_case(officer_id="OFF-001")
    db_session.add(VisualAnomaly(
        inspection_id=case.inspection_id, evidence_id="ev-1", anomaly_type="SUSPECTED_OVERLAY",
        confidence=0.92, status="DETECTED", officer_review_required="YES"
    ))
    db_session.commit()

    result = ComplianceEvaluationService(db_session).evaluate_inspection(case.inspection_id)
    finding = next(f for f in result["findings"] if f.rule_id == "RULE-OVERLAY-STICKER-FLAG")

    assert finding.status == FindingStatus.REVIEW
    assert result["overall_determination"] in (OverallDetermination.REQUIRES_REVIEW, OverallDetermination.NON_COMPLIANT)
    # Ensure sticker finding itself is never FAIL
    assert finding.status != FindingStatus.FAIL
