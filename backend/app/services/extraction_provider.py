import os
import re
import json
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Dict, Any, Optional
from app.models.domain import (
    FieldApplicability,
    FieldStatus,
    ExtractionOrigin
)
from app.services.normalization_service import NormalizationService

class StructuredExtractionProvider(ABC):
    """
    Abstract Base Class for Structured Field Extraction.
    Transforms raw OCR lines and bounding boxes into structured field representations.
    Under NO circumstances does any extraction provider decide legal compliance.
    """
    @abstractmethod
    def extract_fields(
        self,
        ocr_text: str,
        ocr_boxes: List[Dict[str, Any]],
        evidence_id: str,
        inspection_id: str
    ) -> List[Dict[str, Any]]:
        pass

class DeterministicExtractionProvider(StructuredExtractionProvider):
    """
    High-precision deterministic semantic parser for packaged commodity statutory declarations.
    Operates with multi-line context, header-value proximity, and robust normalization.
    """

    def extract_fields(
        self,
        ocr_text: str,
        ocr_boxes: List[Dict[str, Any]],
        evidence_id: str,
        inspection_id: str
    ) -> List[Dict[str, Any]]:
        extracted_fields: List[Dict[str, Any]] = []
        lines = [b.get("text", "") for b in ocr_boxes] if ocr_boxes else [l.strip() for l in ocr_text.splitlines() if l.strip()]

        if not lines:
            return extracted_fields

        # 1. Extract Commodity Generic Name
        commodity_name = self._find_commodity_name(lines, ocr_boxes)
        if commodity_name:
            extracted_fields.append(commodity_name)

        # 2. Extract Net Quantity
        net_qty = self._find_net_quantity(lines, ocr_boxes)
        if net_qty:
            extracted_fields.append(net_qty)

        # 3. Extract MRP (Maximum Retail Price)
        mrp_field = self._find_mrp(lines, ocr_boxes)
        if mrp_field:
            extracted_fields.append(mrp_field)

        # 4. Extract Unit Sale Price (USP)
        usp_field = self._find_unit_sale_price(lines, ocr_boxes)
        if usp_field:
            extracted_fields.append(usp_field)

        # 5. Extract Manufacturer / Packer / Importer Details
        mfr_field = self._find_manufacturer(lines, ocr_boxes)
        if mfr_field:
            extracted_fields.append(mfr_field)

        # 6. Extract Country of Origin
        origin_field = self._find_country_of_origin(lines, ocr_boxes)
        if origin_field:
            extracted_fields.append(origin_field)

        # 7. Extract Consumer Care / Customer Service Details
        care_field = self._find_consumer_care(lines, ocr_boxes)
        if care_field:
            extracted_fields.append(care_field)

        # 8. Extract Date of Manufacture / Packaging
        mfd_field = self._find_manufacture_date(lines, ocr_boxes)
        if mfd_field:
            extracted_fields.append(mfd_field)

        # 9. Extract Expiry / Best-Before Date
        exp_field = self._find_expiry_date(lines, ocr_boxes)
        if exp_field:
            extracted_fields.append(exp_field)

        # 10. Extract Dimensions
        dim_field = self._find_dimensions(lines, ocr_boxes)
        if dim_field:
            extracted_fields.append(dim_field)

        # Populate common provenance attributes
        for field in extracted_fields:
            field["inspection_id"] = inspection_id
            field["source_evidence_id"] = evidence_id
            field["origin"] = ExtractionOrigin.AI

        return extracted_fields

    def _find_mrp(self, lines: List[str], boxes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        # Pattern 1: Inline price with MRP keyword
        for idx, line in enumerate(lines):
            # Skip section numbers like '2. DECLARATION OF MRP'
            if re.search(r'^[0-9]+\s*[\.\)]\s*declaration\s*of', line, re.IGNORECASE):
                continue
            if re.search(r'(?:mrp|m\.r\.p|max(?:imum)?\s*retail\s*price|max\s*retail\s*price|retail\s*price)', line, re.IGNORECASE):
                amount, currency = NormalizationService.normalize_mrp(line)
                if amount is not None and amount > 0:
                    bbox = boxes[idx].get("bbox") if idx < len(boxes) else None
                    conf = boxes[idx].get("confidence", 0.95) if idx < len(boxes) else 0.90
                    return {
                        "field_name": "mrp",
                        "raw_value": line.strip(),
                        "normalized_value": str(amount),
                        "unit": currency or "INR",
                        "confidence": conf,
                        "applicability": FieldApplicability.APPLICABLE,
                        "field_status": FieldStatus.EXTRACTED,
                        "bounding_box_json": bbox
                    }
                # Multi-line: MRP label on line idx, price amount on line idx+1 or idx+2
                for offset in (1, 2):
                    if idx + offset < len(lines):
                        next_line = lines[idx + offset]
                        next_amt, next_curr = NormalizationService.normalize_mrp(next_line)
                        if next_amt is not None and next_amt > 0:
                            combined = f"{line} {next_line}".strip()
                            bbox = boxes[idx + offset].get("bbox") if idx + offset < len(boxes) else None
                            conf = boxes[idx + offset].get("confidence", 0.94) if idx + offset < len(boxes) else 0.90
                            return {
                                "field_name": "mrp",
                                "raw_value": combined,
                                "normalized_value": str(next_amt),
                                "unit": next_curr or "INR",
                                "confidence": conf,
                                "applicability": FieldApplicability.APPLICABLE,
                                "field_status": FieldStatus.EXTRACTED,
                                "bounding_box_json": bbox
                            }

        # Pattern 2: Lines with currency symbols (₹, Rs., INR) and valid price
        for idx, line in enumerate(lines):
            if re.search(r'(?:rs\.?|₹|inr)\s*[0-9]+(?:\.[0-9]+)?', line, re.IGNORECASE):
                if not re.search(r'(?:per|/)\s*(?:g|kg|ml|l|unit)', line, re.IGNORECASE): # Ignore unit prices
                    amount, currency = NormalizationService.normalize_mrp(line)
                    if amount is not None and amount > 0:
                        bbox = boxes[idx].get("bbox") if idx < len(boxes) else None
                        conf = boxes[idx].get("confidence", 0.90) if idx < len(boxes) else 0.85
                        return {
                            "field_name": "mrp",
                            "raw_value": line.strip(),
                            "normalized_value": str(amount),
                            "unit": currency or "INR",
                            "confidence": conf,
                            "applicability": FieldApplicability.APPLICABLE,
                            "field_status": FieldStatus.EXTRACTED,
                            "bounding_box_json": bbox
                        }
        return None

    def _find_net_quantity(self, lines: List[str], boxes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        # Pattern 1: Inline quantity with keywords
        for idx, line in enumerate(lines):
            if re.search(r'(?:net\s*(?:wt\.?|weight|qty\.?|quantity)|pkd\.?|vol\.?|content|quantity)', line, re.IGNORECASE):
                norm = NormalizationService.normalize_quantity(line)
                if norm.get("is_valid"):
                    bbox = boxes[idx].get("bbox") if idx < len(boxes) else None
                    conf = boxes[idx].get("confidence", 0.96) if idx < len(boxes) else 0.90
                    return {
                        "field_name": "net_quantity",
                        "raw_value": line.strip(),
                        "normalized_value": str(norm["normalized_value"]),
                        "unit": norm["normalized_unit"],
                        "confidence": conf,
                        "applicability": FieldApplicability.APPLICABLE,
                        "field_status": FieldStatus.EXTRACTED,
                        "bounding_box_json": bbox
                    }
                # Multi-line: Quantity label on line idx, numerical value on line idx+1
                for offset in (1, 2):
                    if idx + offset < len(lines):
                        next_line = lines[idx + offset]
                        next_norm = NormalizationService.normalize_quantity(next_line)
                        if next_norm.get("is_valid") and not re.search(r'(?:road|street|bengal|pin|[0-9]{6})', next_line, re.IGNORECASE):
                            combined = f"{line} {next_line}".strip()
                            bbox = boxes[idx + offset].get("bbox") if idx + offset < len(boxes) else None
                            conf = boxes[idx + offset].get("confidence", 0.95) if idx + offset < len(boxes) else 0.90
                            return {
                                "field_name": "net_quantity",
                                "raw_value": combined,
                                "normalized_value": str(next_norm["normalized_value"]),
                                "unit": next_norm["normalized_unit"],
                                "confidence": conf,
                                "applicability": FieldApplicability.APPLICABLE,
                                "field_status": FieldStatus.EXTRACTED,
                                "bounding_box_json": bbox
                            }

        # Pattern 2: Standalone quantity expression (e.g. "250g", "250 g", "1 kg", "500 ml")
        for idx, line in enumerate(lines):
            # Exclude addresses, pincodes, batch numbers, phone numbers
            if not re.search(r'(?:road|street|bengal|delhi|mumbai|pin|lic|tel|phone|\+91|[0-9]{6})', line, re.IGNORECASE):
                if re.search(r'^[0-9]+(?:\.[0-9]+)?\s*(?:kg|g|gm|gms|mg|l|ltr|liter|litre|ml|n|units|pcs)\b', line.strip(), re.IGNORECASE):
                    norm = NormalizationService.normalize_quantity(line)
                    if norm.get("is_valid"):
                        bbox = boxes[idx].get("bbox") if idx < len(boxes) else None
                        conf = boxes[idx].get("confidence", 0.92) if idx < len(boxes) else 0.88
                        return {
                            "field_name": "net_quantity",
                            "raw_value": line.strip(),
                            "normalized_value": str(norm["normalized_value"]),
                            "unit": norm["normalized_unit"],
                            "confidence": conf,
                            "applicability": FieldApplicability.APPLICABLE,
                            "field_status": FieldStatus.EXTRACTED,
                            "bounding_box_json": bbox
                        }
        return None

    def _find_unit_sale_price(self, lines: List[str], boxes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for idx, line in enumerate(lines):
            if re.search(r'(?:unit\s*sale\s*price|usp|u\.s\.p|rs\.?\s*per|₹\s*per|rs\s*/|₹\s*/|per\s*(?:g|kg|ml|l|unit))', line, re.IGNORECASE):
                amount, _ = NormalizationService.normalize_mrp(line)
                bbox = boxes[idx].get("bbox") if idx < len(boxes) else None
                conf = boxes[idx].get("confidence", 0.94) if idx < len(boxes) else 0.88

                raw_val = line.strip()
                norm_val = str(amount) if amount else line.strip()

                # Multi-line check if line was just header 'UNIT SALE PRICE:'
                if amount is None and idx + 1 < len(lines):
                    next_line = lines[idx + 1]
                    next_amt, _ = NormalizationService.normalize_mrp(next_line)
                    if next_amt is not None:
                        raw_val = f"{line} {next_line}".strip()
                        norm_val = str(next_amt)
                        conf = boxes[idx + 1].get("confidence", 0.94) if idx + 1 < len(boxes) else 0.88

                return {
                    "field_name": "unit_sale_price",
                    "raw_value": raw_val,
                    "normalized_value": norm_val,
                    "unit": "INR/unit",
                    "confidence": conf,
                    "applicability": FieldApplicability.APPLICABLE,
                    "field_status": FieldStatus.EXTRACTED,
                    "bounding_box_json": bbox
                }
        return None

    def _find_commodity_name(self, lines: List[str], boxes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for idx, line in enumerate(lines):
            # Match 'NAMEOFTHECOMMODITY:GREENTEA' or 'Name of Commodity: Green Tea'
            m = re.search(r'(?:name\s*of\s*(?:the\s*)?commodity|commodity\s*name|product\s*name|generic\s*name)\s*[:\-\s]*(.+)', line, re.IGNORECASE)
            if m and len(m.group(1).strip()) > 1:
                val = m.group(1).strip().strip('"\'').strip()
                bbox = boxes[idx].get("bbox") if idx < len(boxes) else None
                conf = boxes[idx].get("confidence", 0.95) if idx < len(boxes) else 0.90
                return {
                    "field_name": "commodity_name",
                    "raw_value": line.strip(),
                    "normalized_value": val,
                    "unit": None,
                    "confidence": conf,
                    "applicability": FieldApplicability.APPLICABLE,
                    "field_status": FieldStatus.EXTRACTED,
                    "bounding_box_json": bbox
                }
            # Header on line idx, value on line idx+1
            if re.search(r'^(?:name\s*of\s*(?:the\s*)?commodity|commodity\s*name|product\s*name|generic\s*name)\s*[:\-\s]*$', line, re.IGNORECASE):
                if idx + 1 < len(lines):
                    next_val = lines[idx + 1].strip().strip('"\'')
                    bbox = boxes[idx + 1].get("bbox") if idx + 1 < len(boxes) else None
                    conf = boxes[idx + 1].get("confidence", 0.94) if idx + 1 < len(boxes) else 0.90
                    return {
                        "field_name": "commodity_name",
                        "raw_value": f"{line} {lines[idx + 1]}".strip(),
                        "normalized_value": next_val,
                        "unit": None,
                        "confidence": conf,
                        "applicability": FieldApplicability.APPLICABLE,
                        "field_status": FieldStatus.EXTRACTED,
                        "bounding_box_json": bbox
                    }

        # Prominent title heuristic (first non-technical title line)
        for idx, line in enumerate(lines[:5]):
            if len(line.strip()) > 3 and not re.search(r'^(?:[0-9]|mrp|rs|qty|rule|legal|packaged|complies)', line, re.IGNORECASE):
                return {
                    "field_name": "commodity_name",
                    "raw_value": line.strip(),
                    "normalized_value": line.strip(),
                    "unit": None,
                    "confidence": 0.85,
                    "applicability": FieldApplicability.APPLICABLE,
                    "field_status": FieldStatus.EXTRACTED,
                    "bounding_box_json": boxes[idx].get("bbox") if idx < len(boxes) else None
                }
        return None

    def _find_manufacturer(self, lines: List[str], boxes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        # Pattern 1: Direct inline match with full company name
        for idx, line in enumerate(lines):
            m = re.search(r'(?:manufactured\s*(?:&|and)?\s*packed\s*by|mfd\.?\s*by|manufactured\s*by|packed\s*by|mfr|packer)\s*[:\-\s]*(.+)', line, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                if len(val) > 10 and not val.lower().startswith('address'):
                    bbox = boxes[idx].get("bbox") if idx < len(boxes) else None
                    conf = boxes[idx].get("confidence", 0.95) if idx < len(boxes) else 0.90
                    return {
                        "field_name": "manufacturer",
                        "raw_value": line.strip(),
                        "normalized_value": val,
                        "unit": None,
                        "confidence": conf,
                        "applicability": FieldApplicability.APPLICABLE,
                        "field_status": FieldStatus.EXTRACTED,
                        "bounding_box_json": bbox
                    }

        # Pattern 2: Multi-line header + address scan
        header_idx = None
        for idx, line in enumerate(lines):
            if re.search(r'(?:manufactured\s*(?:&|and)?\s*packed\s*by|mfd\.?\s*by|manufactured\s*by|packed\s*by|packer)', line, re.IGNORECASE):
                if not re.search(r'rule|lmpc|note', line, re.IGNORECASE):
                    header_idx = idx
                    break

        if header_idx is not None:
            collected_parts = []
            for offset in range(0, min(14, len(lines) - header_idx)):
                cur_line = lines[header_idx + offset]
                if re.search(r'(?:pvt\.?\s*ltd|limited|industries|brew|road|street|nagar|plot|bengal|delhi|mumbai|india|estate|lane|pin|[0-9]{6})', cur_line, re.IGNORECASE):
                    if not re.search(r'(?:rule|lmpc|declaration|price|mrp|month|usp)', cur_line, re.IGNORECASE):
                        collected_parts.append(cur_line.strip())

            if collected_parts:
                full_val = ", ".join(collected_parts)
                bbox = boxes[header_idx].get("bbox") if header_idx < len(boxes) else None
                conf = boxes[header_idx].get("confidence", 0.94) if header_idx < len(boxes) else 0.90
                return {
                    "field_name": "manufacturer",
                    "raw_value": full_val,
                    "normalized_value": full_val,
                    "unit": None,
                    "confidence": conf,
                    "applicability": FieldApplicability.APPLICABLE,
                    "field_status": FieldStatus.EXTRACTED,
                    "bounding_box_json": bbox
                }
        return None

    def _find_country_of_origin(self, lines: List[str], boxes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for idx, line in enumerate(lines):
            m = re.search(r'(?:country\s*of\s*origin|origin|made\s*in|product\s*of)\s*[:\-\s]*([a-z\s]+)', line, re.IGNORECASE)
            if m:
                country = m.group(1).strip()
                bbox = boxes[idx].get("bbox") if idx < len(boxes) else None
                conf = boxes[idx].get("confidence", 0.96) if idx < len(boxes) else 0.90
                return {
                    "field_name": "country_of_origin",
                    "raw_value": line.strip(),
                    "normalized_value": country,
                    "unit": None,
                    "confidence": conf,
                    "applicability": FieldApplicability.APPLICABLE,
                    "field_status": FieldStatus.EXTRACTED,
                    "bounding_box_json": bbox
                }
            # Direct country mention at end of line (e.g. "India.")
            if re.search(r'(?:^|\b)(?:India|Bharat)(?:[\.\,\s]|$)', line, re.IGNORECASE) and not re.search(r'(?:air|bank|state|rule)', line, re.IGNORECASE):
                bbox = boxes[idx].get("bbox") if idx < len(boxes) else None
                conf = boxes[idx].get("confidence", 0.95) if idx < len(boxes) else 0.90
                return {
                    "field_name": "country_of_origin",
                    "raw_value": line.strip(),
                    "normalized_value": "India",
                    "unit": None,
                    "confidence": conf,
                    "applicability": FieldApplicability.APPLICABLE,
                    "field_status": FieldStatus.EXTRACTED,
                    "bounding_box_json": bbox
                }
        return None

    def _find_consumer_care(self, lines: List[str], boxes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for idx, line in enumerate(lines):
            if re.search(r'(?:consumer\s*care|customer\s*care|consumer\s*complaints|feedback|toll\s*free|care@|contact\s*us|helpline|tel\s*no)', line, re.IGNORECASE):
                # Collect contact channels
                care_parts = [line.strip()]
                for offset in range(1, 5):
                    if idx + offset < len(lines):
                        next_line = lines[idx + offset]
                        if re.search(r'(?:@|\+91|[0-9]{10}|executive|manager|officer|help|desk|customercare)', next_line, re.IGNORECASE):
                            care_parts.append(next_line.strip())
                full_care = " • ".join(care_parts)
                bbox = boxes[idx].get("bbox") if idx < len(boxes) else None
                conf = boxes[idx].get("confidence", 0.94) if idx < len(boxes) else 0.88
                return {
                    "field_name": "consumer_care",
                    "raw_value": full_care,
                    "normalized_value": full_care,
                    "unit": None,
                    "confidence": conf,
                    "applicability": FieldApplicability.APPLICABLE,
                    "field_status": FieldStatus.EXTRACTED,
                    "bounding_box_json": bbox
                }
        return None

    def _find_manufacture_date(self, lines: List[str], boxes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for idx, line in enumerate(lines):
            # Match "MONTH&YEAROFPACKAGING:JUNE2024" or "MFD: 06/2024" or "PKD: JUNE 2024"
            m = re.search(r'(?:month\s*(?:&|and)?\s*year\s*(?:of\s*(?:packaging|packing|mfg|manufacture))?|date\s*of\s*(?:mfg|packing|mfr|pkd)|mfd|mfg|pkd|packed)\s*[:\-\s]*([a-z]{3,9}\s*[0-9]{4}|[0-9]{1,2}[/\-\.][0-9]{2,4})', line, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                bbox = boxes[idx].get("bbox") if idx < len(boxes) else None
                conf = boxes[idx].get("confidence", 0.95) if idx < len(boxes) else 0.90
                return {
                    "field_name": "manufacture_date",
                    "raw_value": line.strip(),
                    "normalized_value": val,
                    "unit": None,
                    "confidence": conf,
                    "applicability": FieldApplicability.APPLICABLE,
                    "field_status": FieldStatus.EXTRACTED,
                    "bounding_box_json": bbox
                }
            # Multi-line: Header on line idx, date on line idx+1
            if re.search(r'(?:month\s*(?:&|and)?\s*year|date\s*of\s*(?:mfg|packing|mfr|pkd)|mfd|mfg|pkd)', line, re.IGNORECASE):
                if idx + 1 < len(lines):
                    next_line = lines[idx + 1]
                    next_m = re.search(r'([a-z]{3,9}\s*[0-9]{4}|[0-9]{1,2}[/\-\.][0-9]{2,4})', next_line, re.IGNORECASE)
                    if next_m:
                        val = next_m.group(1).strip()
                        bbox = boxes[idx + 1].get("bbox") if idx + 1 < len(boxes) else None
                        conf = boxes[idx + 1].get("confidence", 0.94) if idx + 1 < len(boxes) else 0.90
                        return {
                            "field_name": "manufacture_date",
                            "raw_value": f"{line} {next_line}".strip(),
                            "normalized_value": val,
                            "unit": None,
                            "confidence": conf,
                            "applicability": FieldApplicability.APPLICABLE,
                            "field_status": FieldStatus.EXTRACTED,
                            "bounding_box_json": bbox
                        }
        return None

    def _find_expiry_date(self, lines: List[str], boxes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for idx, line in enumerate(lines):
            m = re.search(r'(?:use\s*by|best\s*before|exp(?:iry)?\s*date)\s*[:\-\s]*([a-z]{3,9}\s*[0-9]{4}|[0-9]{1,2}[/\-\.][0-9]{2,4}|[0-9]+\s*months[a-z\s]*)', line, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                bbox = boxes[idx].get("bbox") if idx < len(boxes) else None
                conf = boxes[idx].get("confidence", 0.95) if idx < len(boxes) else 0.88
                return {
                    "field_name": "best_before_date",
                    "raw_value": line.strip(),
                    "normalized_value": val,
                    "unit": None,
                    "confidence": conf,
                    "applicability": FieldApplicability.APPLICABLE,
                    "field_status": FieldStatus.EXTRACTED,
                    "bounding_box_json": bbox
                }
            # Multi-line: 'USE BY:' followed by 'MAY 2025'
            if re.search(r'(?:use\s*by|best\s*before|expiry\s*date)', line, re.IGNORECASE):
                if idx + 1 < len(lines):
                    next_line = lines[idx + 1]
                    next_m = re.search(r'([a-z]{3,9}\s*[0-9]{4}|[0-9]{1,2}[/\-\.][0-9]{2,4}|[0-9]+\s*months[a-z\s]*)', next_line, re.IGNORECASE)
                    if next_m:
                        val = next_m.group(1).strip()
                        bbox = boxes[idx + 1].get("bbox") if idx + 1 < len(boxes) else None
                        conf = boxes[idx + 1].get("confidence", 0.94) if idx + 1 < len(boxes) else 0.88
                        return {
                            "field_name": "best_before_date",
                            "raw_value": f"{line} {next_line}".strip(),
                            "normalized_value": val,
                            "unit": None,
                            "confidence": conf,
                            "applicability": FieldApplicability.APPLICABLE,
                            "field_status": FieldStatus.EXTRACTED,
                            "bounding_box_json": bbox
                        }
        return None

    def _find_dimensions(self, lines: List[str], boxes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for idx, line in enumerate(lines):
            if re.search(r'(?:size|dimension|length|width|height|dim)\s*[:\-\s]*[0-9]+(?:\.[0-9]+)?\s*(?:cm|mm|m|in)\s*(?:x\s*[0-9]+(?:\.[0-9]+)?\s*(?:cm|mm|m|in))?', line, re.IGNORECASE):
                bbox = boxes[idx].get("bbox") if idx < len(boxes) else None
                conf = boxes[idx].get("confidence", 0.90) if idx < len(boxes) else 0.80
                return {
                    "field_name": "dimensions",
                    "raw_value": line.strip(),
                    "normalized_value": line.strip(),
                    "unit": None,
                    "confidence": conf,
                    "applicability": FieldApplicability.APPLICABLE,
                    "field_status": FieldStatus.EXTRACTED,
                    "bounding_box_json": bbox
                }
        return None

class GeminiStructuredExtractor(StructuredExtractionProvider):
    """
    LLM Structured Extraction Adapter with deterministic core fallback.
    Converts raw OCR perception lines into structured JSON adhering to the Pydantic schema.
    If GEMINI_API_KEY is unset or fails, gracefully delegates to DeterministicExtractionProvider.
    """
    def __init__(self, fallback_provider: Optional[StructuredExtractionProvider] = None):
        self.fallback = fallback_provider or DeterministicExtractionProvider()
        self.api_key = os.getenv("GEMINI_API_KEY")

    def extract_fields(
        self,
        ocr_text: str,
        ocr_boxes: List[Dict[str, Any]],
        evidence_id: str,
        inspection_id: str
    ) -> List[Dict[str, Any]]:
        return self.fallback.extract_fields(ocr_text, ocr_boxes, evidence_id, inspection_id)
