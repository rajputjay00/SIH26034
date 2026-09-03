import re
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Dict, Any, Optional, Tuple

class NormalizationService:
    """
    Deterministic, decimal-safe normalization service for Legal Metrology inspections.
    Preserves original raw values while generating precise computational representations.
    """

    # Mass conversion factors to standard base unit: kg (or g for sub-gram)
    MASS_TO_KG = {
        "kg": Decimal("1.0"),
        "kilogram": Decimal("1.0"),
        "kilograms": Decimal("1.0"),
        "g": Decimal("0.001"),
        "gram": Decimal("0.001"),
        "grams": Decimal("0.001"),
        "gm": Decimal("0.001"),
        "gms": Decimal("0.001"),
        "mg": Decimal("0.000001"),
        "milligram": Decimal("0.000001"),
        "milligrams": Decimal("0.000001"),
    }

    # Volume conversion factors to standard base unit: L
    VOLUME_TO_L = {
        "l": Decimal("1.0"),
        "ltr": Decimal("1.0"),
        "liter": Decimal("1.0"),
        "liters": Decimal("1.0"),
        "litre": Decimal("1.0"),
        "litres": Decimal("1.0"),
        "ml": Decimal("0.001"),
        "milliliter": Decimal("0.001"),
        "milliliters": Decimal("0.001"),
        "millilitre": Decimal("0.001"),
        "millilitres": Decimal("0.001"),
        "cl": Decimal("0.01"),
        "centiliter": Decimal("0.01"),
    }

    # Number / Count conversion factors to standard base unit: N
    COUNT_UNITS = {"n", "number", "numbers", "unit", "units", "pc", "pcs", "piece", "pieces", "u"}

    @classmethod
    def normalize_mrp(cls, raw_mrp_str: Optional[str]) -> Tuple[Optional[Decimal], Optional[str]]:
        """
        Parse raw MRP text string and extract numeric Decimal amount and currency code.
        Examples: 'MRP ₹150.00 (incl. of all taxes)', 'Rs. 120/-', '150' -> (Decimal('150.00'), 'INR')
        """
        if not raw_mrp_str:
            return None, None

        # Clean string: replace comma separators
        cleaned = raw_mrp_str.strip()
        # Regex search for numeric monetary value
        match = re.search(r'(?:₹|rs\.?|inr|mrp)?\s*[:\-\s]*([0-9]+(?:\.[0-9]{1,2})?)', cleaned, re.IGNORECASE)
        if match:
            try:
                num_str = match.group(1)
                amount = Decimal(num_str).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                return amount, "INR"
            except InvalidOperation:
                return None, None
        return None, None

    @classmethod
    def normalize_quantity(cls, raw_qty_str: Optional[str]) -> Dict[str, Any]:
        """
        Parse raw net quantity string and convert to standard base unit (kg, L, or N).
        Examples:
          '500 g'  -> {'raw_value': '500 g', 'numeric_value': Decimal('500'), 'unit': 'g', 'normalized_value': Decimal('0.5'), 'normalized_unit': 'kg', 'base_type': 'MASS'}
          '1.5 L'  -> {'raw_value': '1.5 L', 'numeric_value': Decimal('1.5'), 'unit': 'L', 'normalized_value': Decimal('1.5'), 'normalized_unit': 'L', 'base_type': 'VOLUME'}
          '10 N'   -> {'raw_value': '10 N', 'numeric_value': Decimal('10'), 'unit': 'N', 'normalized_value': Decimal('10'), 'normalized_unit': 'N', 'base_type': 'COUNT'}
        """
        result = {
            "raw_value": raw_qty_str,
            "numeric_value": None,
            "unit": None,
            "normalized_value": None,
            "normalized_unit": None,
            "base_type": None,
            "is_valid": False
        }

        if not raw_qty_str:
            return result

        cleaned = raw_qty_str.strip().lower()
        # Match pattern: number followed by unit
        match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*([a-z]+)', cleaned)
        if not match:
            return result

        num_part = match.group(1)
        unit_part = match.group(2).lower()

        try:
            val = Decimal(num_part)
        except InvalidOperation:
            return result

        result["numeric_value"] = val
        result["unit"] = unit_part

        # Mass normalization
        if unit_part in cls.MASS_TO_KG:
            factor = cls.MASS_TO_KG[unit_part]
            normalized = (val * factor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            result["normalized_value"] = normalized
            result["normalized_unit"] = "kg"
            result["base_type"] = "MASS"
            result["is_valid"] = True

        # Volume normalization
        elif unit_part in cls.VOLUME_TO_L:
            factor = cls.VOLUME_TO_L[unit_part]
            normalized = (val * factor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            result["normalized_value"] = normalized
            result["normalized_unit"] = "L"
            result["base_type"] = "VOLUME"
            result["is_valid"] = True

        # Count normalization
        elif unit_part in cls.COUNT_UNITS:
            result["normalized_value"] = val
            result["normalized_unit"] = "N"
            result["base_type"] = "COUNT"
            result["is_valid"] = True

        return result

    @classmethod
    def calculate_unit_sale_price(
        cls,
        mrp_decimal: Optional[Decimal],
        normalized_qty_decimal: Optional[Decimal],
        base_unit: Optional[str]
    ) -> Dict[str, Any]:
        """
        Deterministic Unit Sale Price arithmetic calculation.
        Calculates expected price per standard base unit: USP = MRP / Normalized Quantity
        Example: ₹100 / 0.5 kg = ₹200.00 / kg
        """
        calc_result = {
            "mrp": float(mrp_decimal) if mrp_decimal is not None else None,
            "normalized_quantity": float(normalized_qty_decimal) if normalized_qty_decimal is not None else None,
            "base_unit": base_unit,
            "calculated_usp": None,
            "unit_price_string": None,
            "is_computable": False,
            "error": None
        }

        if mrp_decimal is None or normalized_qty_decimal is None or not base_unit:
            calc_result["error"] = "Missing MRP or Net Quantity inputs."
            return calc_result

        if normalized_qty_decimal <= Decimal("0"):
            calc_result["error"] = "Net Quantity must be strictly greater than zero."
            return calc_result

        try:
            usp = (mrp_decimal / normalized_qty_decimal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            calc_result["calculated_usp"] = float(usp)
            calc_result["unit_price_string"] = f"₹ {usp:.2f} / {base_unit}"
            calc_result["is_computable"] = True
        except Exception as e:
            calc_result["error"] = str(e)

        return calc_result
