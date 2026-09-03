import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from sqlalchemy import create_engine, text
from app.core.database import Base

def test_sqlite_database_initialization():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result.fetchall()]
        
    expected_tables = [
        "inspection_cases",
        "evidence_items",
        "calibration_data",
        "extracted_fields",
        "field_corrections",
        "rule_findings",
        "audit_entries",
        "generated_reports"
    ]
    
    for table in expected_tables:
        assert table in tables, f"Expected table '{table}' not created."
