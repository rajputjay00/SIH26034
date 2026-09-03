import pytest
from decimal import Decimal
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.services.normalization_service import NormalizationService

def test_mrp_normalization():
    # Various standard and messy representations
    test_cases = [
        ("₹ 150.00", Decimal("150.00"), "INR"),
        ("MRP Rs. 120 (incl. of all taxes)", Decimal("120.00"), "INR"),
        ("Maximum Retail Price Rs 99.50", Decimal("99.50"), "INR"),
        ("Rs. 250/-", Decimal("250.00"), "INR"),
        ("1500", Decimal("1500.00"), "INR"),
        ("", None, None),
        ("Invalid text", None, None),
    ]

    for raw, expected_amount, expected_curr in test_cases:
        amt, curr = NormalizationService.normalize_mrp(raw)
        assert amt == expected_amount, f"Failed on raw '{raw}': got {amt}"
        assert curr == expected_curr

def test_quantity_normalization():
    # Mass
    q1 = NormalizationService.normalize_quantity("500 g")
    assert q1["is_valid"] is True
    assert q1["normalized_value"] == Decimal("0.5000")
    assert q1["normalized_unit"] == "kg"
    assert q1["base_type"] == "MASS"

    q2 = NormalizationService.normalize_quantity("1.25 kg")
    assert q2["is_valid"] is True
    assert q2["normalized_value"] == Decimal("1.2500")
    assert q2["normalized_unit"] == "kg"

    # Volume
    q3 = NormalizationService.normalize_quantity("750 ml")
    assert q3["is_valid"] is True
    assert q3["normalized_value"] == Decimal("0.7500")
    assert q3["normalized_unit"] == "L"
    assert q3["base_type"] == "VOLUME"

    q4 = NormalizationService.normalize_quantity("2 L")
    assert q4["is_valid"] is True
    assert q4["normalized_value"] == Decimal("2.0000")
    assert q4["normalized_unit"] == "L"

    # Count
    q5 = NormalizationService.normalize_quantity("10 N")
    assert q5["is_valid"] is True
    assert q5["normalized_value"] == Decimal("10")
    assert q5["normalized_unit"] == "N"

def test_decimal_unit_sale_price_arithmetic():
    # Case 1: MRP ₹100, Qty 500g (0.5 kg) -> USP ₹200.00 / kg
    usp1 = NormalizationService.calculate_unit_sale_price(Decimal("100.00"), Decimal("0.5000"), "kg")
    assert usp1["is_computable"] is True
    assert usp1["calculated_usp"] == 200.00
    assert usp1["unit_price_string"] == "₹ 200.00 / kg"

    # Case 2: MRP ₹150, Qty 750ml (0.75 L) -> USP ₹200.00 / L
    usp2 = NormalizationService.calculate_unit_sale_price(Decimal("150.00"), Decimal("0.7500"), "L")
    assert usp2["is_computable"] is True
    assert usp2["calculated_usp"] == 200.00

    # Case 3: Zero or negative quantity handling
    usp_zero = NormalizationService.calculate_unit_sale_price(Decimal("100.00"), Decimal("0.0000"), "kg")
    assert usp_zero["is_computable"] is False
    assert "greater than zero" in usp_zero["error"]
