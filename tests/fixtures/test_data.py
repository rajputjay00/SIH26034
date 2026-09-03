import pytest
import os
import sys
import cv2
import numpy as np

# Ensure backend app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.domain import InspectionCase, CaseStatus, UserRole

TEST_DATABASE_URL = "sqlite:///:memory:"

def create_synthetic_image(
    text: str = "MRP Rs 150.00 INCL OF ALL TAXES NET QTY 500g",
    width: int = 800,
    height: int = 600,
    blur: bool = False,
    dark: bool = False,
    corrupt: bool = False,
    with_coin: bool = False,
    with_sticker: bool = False
) -> bytes:
    """Create controlled in-memory synthetic image bytes for testing."""
    if corrupt:
        return b"NOT_A_VALID_IMAGE_BYTES_XYZ123"

    # Realistic packaged commodity sample background (neutral light grey/white)
    bg_val = 25 if dark else 200
    text_val = 70 if dark else 20
    img = np.full((height, width, 3), bg_val, dtype=np.uint8)

    # Render high-contrast text lines
    cv2.putText(img, "LEGAL METROLOGY INSPECTION SAMPLE", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (text_val, text_val, text_val), 2)
    cv2.putText(img, text, (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (text_val, text_val, text_val), 2)
    cv2.putText(img, "MFD: 08/2026 MFR: ABC PACKAGED FOODS LTD", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (text_val, text_val, text_val), 2)

    # Render ₹5 coin calibration reference circle
    if with_coin:
        coin_cx, coin_cy, coin_r = 650, 450, 46 # ~92px diameter -> ~0.25 mm/px
        cv2.circle(img, (coin_cx, coin_cy), coin_r, (160, 160, 160), -1)
        cv2.circle(img, (coin_cx, coin_cy), coin_r, (60, 60, 60), 2)
        cv2.putText(img, "5", (coin_cx - 10, coin_cy + 12), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (40, 40, 40), 2)

    # Render sticker / overlay patch
    if with_sticker:
        # Sharp rectangular patch over price area with contrast step
        sx, sy, sw, sh = 40, 160, 320, 65
        cv2.rectangle(img, (sx, sy), (sx + sw, sy + sh), (245, 245, 245), -1)
        cv2.rectangle(img, (sx, sy), (sx + sw, sy + sh), (10, 10, 10), 2)
        cv2.putText(img, "STICKER: MRP Rs. 199.00", (sx + 10, sy + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (10, 10, 10), 2)

    if blur:
        img = cv2.GaussianBlur(img, (25, 25), 10.0)

    _, encoded = cv2.imencode(".jpg", img)
    return encoded.tobytes()



from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


