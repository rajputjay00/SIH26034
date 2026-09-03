from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class CharacterType(str, Enum):
    LETTER = "LETTER"
    NUMERAL = "NUMERAL"
    UNKNOWN = "UNKNOWN"

class DeclarationMethod(str, Enum):
    NORMAL_PRINT = "NORMAL_PRINT"
    BLOWN_MOULDED_EMBOSSED = "BLOWN_MOULDED_EMBOSSED"
    UNKNOWN = "UNKNOWN"

class PDPAreaSource(str, Enum):
    OFFICER_ENTERED = "OFFICER_ENTERED"
    PHYSICAL_MEASUREMENT = "PHYSICAL_MEASUREMENT"
    SYSTEM_MEASURED = "SYSTEM_MEASURED"
    UNKNOWN = "UNKNOWN"

class ThresholdVerificationStatus(str, Enum):
    VERIFIED_AUTHORITATIVE = "VERIFIED_AUTHORITATIVE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    UNVERIFIED = "UNVERIFIED"

@dataclass
class StatutoryFontThreshold:
    threshold_id: str
    rule_id: str
    rule_pack_version: str
    min_pdp_area_cm2: float
    max_pdp_area_cm2: float
    character_type: CharacterType
    declaration_method: DeclarationMethod
    minimum_height_mm: float
    legal_citation: str
    source_document: str
    source_table: str
    effective_date: str
    verification_status: ThresholdVerificationStatus

class FontThresholdRegistry:
    """
    Versioned statutory threshold repository for Legal Metrology Rule 7 character heights.
    CRITICAL STATUTORY GROUNDING:
    Under Rule 7(2) read with Table 1 of the Legal Metrology (Packaged Commodities) Rules, 2011,
    the statutory minimum font height is strictly indexed by Principal Display Panel Area (A in cm²),
    Character Type (Letter vs Numeral), and Declaration Method (Normal Print vs Blown/Moulded/Embossed).
    Net Quantity has NO role in determining Table 1 font height thresholds.
    """

    _AUTHORITATIVE_SCHEDULE: List[StatutoryFontThreshold] = [
        # --- Normal Print: Letters ---
        StatutoryFontThreshold(
            threshold_id="RULE7-NP-LET-A-LE50",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=0.0,
            max_pdp_area_cm2=50.0,
            character_type=CharacterType.LETTER,
            declaration_method=DeclarationMethod.NORMAL_PRINT,
            minimum_height_mm=1.0,
            legal_citation="Rule 7(2), Table 1, Row 1, Col 2(a)",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-NP-LET-A-50-100",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=50.001,
            max_pdp_area_cm2=100.0,
            character_type=CharacterType.LETTER,
            declaration_method=DeclarationMethod.NORMAL_PRINT,
            minimum_height_mm=1.5,
            legal_citation="Rule 7(2), Table 1, Row 2, Col 2(a)",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-NP-LET-A-100-500",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=100.001,
            max_pdp_area_cm2=500.0,
            character_type=CharacterType.LETTER,
            declaration_method=DeclarationMethod.NORMAL_PRINT,
            minimum_height_mm=2.5,
            legal_citation="Rule 7(2), Table 1, Row 3, Col 2(a)",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-NP-LET-A-500-1000",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=500.001,
            max_pdp_area_cm2=1000.0,
            character_type=CharacterType.LETTER,
            declaration_method=DeclarationMethod.NORMAL_PRINT,
            minimum_height_mm=4.0,
            legal_citation="Rule 7(2), Table 1, Row 4, Col 2(a)",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-NP-LET-A-GT1000",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=1000.001,
            max_pdp_area_cm2=1e9,
            character_type=CharacterType.LETTER,
            declaration_method=DeclarationMethod.NORMAL_PRINT,
            minimum_height_mm=6.0,
            legal_citation="Rule 7(2), Table 1, Row 5, Col 2(a)",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),

        # --- Normal Print: Numerals ---
        StatutoryFontThreshold(
            threshold_id="RULE7-NP-NUM-A-LE50",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=0.0,
            max_pdp_area_cm2=50.0,
            character_type=CharacterType.NUMERAL,
            declaration_method=DeclarationMethod.NORMAL_PRINT,
            minimum_height_mm=1.5,
            legal_citation="Rule 7(2), Table 1, Row 1, Col 2(b)",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-NP-NUM-A-50-100",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=50.001,
            max_pdp_area_cm2=100.0,
            character_type=CharacterType.NUMERAL,
            declaration_method=DeclarationMethod.NORMAL_PRINT,
            minimum_height_mm=2.0,
            legal_citation="Rule 7(2), Table 1, Row 2, Col 2(b)",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-NP-NUM-A-100-500",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=100.001,
            max_pdp_area_cm2=500.0,
            character_type=CharacterType.NUMERAL,
            declaration_method=DeclarationMethod.NORMAL_PRINT,
            minimum_height_mm=4.0,
            legal_citation="Rule 7(2), Table 1, Row 3, Col 2(b)",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-NP-NUM-A-500-1000",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=500.001,
            max_pdp_area_cm2=1000.0,
            character_type=CharacterType.NUMERAL,
            declaration_method=DeclarationMethod.NORMAL_PRINT,
            minimum_height_mm=4.0,
            legal_citation="Rule 7(2), Table 1, Row 4, Col 2(b)",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-NP-NUM-A-GT1000",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=1000.001,
            max_pdp_area_cm2=1e9,
            character_type=CharacterType.NUMERAL,
            declaration_method=DeclarationMethod.NORMAL_PRINT,
            minimum_height_mm=6.0,
            legal_citation="Rule 7(2), Table 1, Row 5, Col 2(b)",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),

        # --- Blown, Formed, Moulded, Embossed or Perforated on Container ---
        StatutoryFontThreshold(
            threshold_id="RULE7-BLOWN-A-LE50",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=0.0,
            max_pdp_area_cm2=50.0,
            character_type=CharacterType.LETTER,
            declaration_method=DeclarationMethod.BLOWN_MOULDED_EMBOSSED,
            minimum_height_mm=2.0,
            legal_citation="Rule 7(2), Table 1, Row 1, Col 3",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-BLOWN-NUM-A-LE50",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=0.0,
            max_pdp_area_cm2=50.0,
            character_type=CharacterType.NUMERAL,
            declaration_method=DeclarationMethod.BLOWN_MOULDED_EMBOSSED,
            minimum_height_mm=2.0,
            legal_citation="Rule 7(2), Table 1, Row 1, Col 3",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-BLOWN-A-50-100",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=50.001,
            max_pdp_area_cm2=100.0,
            character_type=CharacterType.LETTER,
            declaration_method=DeclarationMethod.BLOWN_MOULDED_EMBOSSED,
            minimum_height_mm=4.0,
            legal_citation="Rule 7(2), Table 1, Row 2, Col 3",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-BLOWN-NUM-A-50-100",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=50.001,
            max_pdp_area_cm2=100.0,
            character_type=CharacterType.NUMERAL,
            declaration_method=DeclarationMethod.BLOWN_MOULDED_EMBOSSED,
            minimum_height_mm=4.0,
            legal_citation="Rule 7(2), Table 1, Row 2, Col 3",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-BLOWN-A-100-500",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=100.001,
            max_pdp_area_cm2=500.0,
            character_type=CharacterType.LETTER,
            declaration_method=DeclarationMethod.BLOWN_MOULDED_EMBOSSED,
            minimum_height_mm=6.0,
            legal_citation="Rule 7(2), Table 1, Row 3, Col 3",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-BLOWN-NUM-A-100-500",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=100.001,
            max_pdp_area_cm2=500.0,
            character_type=CharacterType.NUMERAL,
            declaration_method=DeclarationMethod.BLOWN_MOULDED_EMBOSSED,
            minimum_height_mm=6.0,
            legal_citation="Rule 7(2), Table 1, Row 3, Col 3",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-BLOWN-A-500-1000",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=500.001,
            max_pdp_area_cm2=1000.0,
            character_type=CharacterType.LETTER,
            declaration_method=DeclarationMethod.BLOWN_MOULDED_EMBOSSED,
            minimum_height_mm=6.0,
            legal_citation="Rule 7(2), Table 1, Row 4, Col 3",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-BLOWN-NUM-A-500-1000",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=500.001,
            max_pdp_area_cm2=1000.0,
            character_type=CharacterType.NUMERAL,
            declaration_method=DeclarationMethod.BLOWN_MOULDED_EMBOSSED,
            minimum_height_mm=6.0,
            legal_citation="Rule 7(2), Table 1, Row 4, Col 3",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-BLOWN-A-GT1000",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=1000.001,
            max_pdp_area_cm2=1e9,
            character_type=CharacterType.LETTER,
            declaration_method=DeclarationMethod.BLOWN_MOULDED_EMBOSSED,
            minimum_height_mm=6.0,
            legal_citation="Rule 7(2), Table 1, Row 5, Col 3",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
        StatutoryFontThreshold(
            threshold_id="RULE7-BLOWN-NUM-A-GT1000",
            rule_id="RULE-FONT-HEIGHT-MINIMUM",
            rule_pack_version="v1.0.0",
            min_pdp_area_cm2=1000.001,
            max_pdp_area_cm2=1e9,
            character_type=CharacterType.NUMERAL,
            declaration_method=DeclarationMethod.BLOWN_MOULDED_EMBOSSED,
            minimum_height_mm=6.0,
            legal_citation="Rule 7(2), Table 1, Row 5, Col 3",
            source_document="Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E) / G.S.R. 592(E))",
            source_table="Table 1: Minimum height of numeral and letters",
            effective_date="2011-04-01",
            verification_status=ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
        ),
    ]

    @classmethod
    def lookup_threshold(
        cls,
        character_type: CharacterType,
        pdp_area_cm2: Optional[float],
        declaration_method: DeclarationMethod = DeclarationMethod.NORMAL_PRINT,
        rule_pack_version: str = "v1.0.0"
    ) -> Optional[StatutoryFontThreshold]:
        """
        Locates a strictly verified statutory font height threshold under Rule 7 Table 1.
        CRITICAL:
        1. Character type must be explicitly LETTER or NUMERAL (never UNKNOWN).
        2. Principal Display Panel area (A in cm²) must be positive and present (never None / <= 0).
        3. Declaration method must be NORMAL_PRINT or BLOWN_MOULDED_EMBOSSED.
        4. Net Quantity has NO role in selecting Table 1 thresholds.
        Returns None if any applicability condition is missing, unknown, or unverified.
        """
        # Safety gate 1: Character type must be explicitly LETTER or NUMERAL
        if character_type not in (CharacterType.LETTER, CharacterType.NUMERAL):
            return None

        # Safety gate 2: PDP area (A) must be positive and present
        if pdp_area_cm2 is None or pdp_area_cm2 <= 0:
            return None

        # Safety gate 3: Declaration method must be known
        if declaration_method not in (DeclarationMethod.NORMAL_PRINT, DeclarationMethod.BLOWN_MOULDED_EMBOSSED):
            return None

        for item in cls._AUTHORITATIVE_SCHEDULE:
            if (
                item.verification_status == ThresholdVerificationStatus.VERIFIED_AUTHORITATIVE
                and item.character_type == character_type
                and item.declaration_method == declaration_method
                and item.min_pdp_area_cm2 <= pdp_area_cm2 <= item.max_pdp_area_cm2
            ):
                return item

        return None
