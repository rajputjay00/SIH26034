import pytest
import io
import cv2
import numpy as np
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models.domain import (
    InspectionCase,
    CaseStatus,
    EvidenceItem,
    EvidenceViewType,
    EvidenceProcessingStatus,
    QualityVerdict,
    AuditEntry
)
from app.audit.hasher import compute_sha256_bytes
from tests.fixtures.test_data import db_session, create_synthetic_image

def get_auth_headers(role: str = "OFFICER", user_id: str = "OFFICER-IND-1001"):
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}

def test_01_camera_equivalent_frame_ingestion_and_sha256(db_session: Session):
    """Verify in-app camera captured frame is ingested into standard evidence pipeline with server-side SHA-256."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    # 1. Create a case
    c = InspectionCase(
        inspection_id="case-cam-001",
        case_number="CASE-CAM-001",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.PROCESSING
    )
    db_session.add(c)
    db_session.commit()

    # 2. Simulate high-res camera capture frame (1280x720 RGB)
    cam_img = np.full((720, 1280, 3), 240, dtype=np.uint8)
    cv2.putText(cam_img, "MRP Rs 250.00 Net Wt 500g", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (10, 10, 10), 2)
    _, encoded = cv2.imencode(".jpg", cam_img)
    camera_bytes = encoded.tobytes()

    expected_sha256 = compute_sha256_bytes(camera_bytes)

    # 3. Submit through evidence endpoint
    headers = get_auth_headers("OFFICER", "OFFICER-IND-1001")
    files = {"file": ("capture_front_20260903_120000.jpg", camera_bytes, "image/jpeg")}
    data = {"view_type": "FRONT"}

    resp = client.post("/api/v1/cases/case-cam-001/evidence", data=data, files=files, headers=headers)
    assert resp.status_code == 201
    ev_data = resp.json()

    # Verify server-side hash computation and view type
    assert ev_data["inspection_id"] == "case-cam-001"
    assert ev_data["view_type"] == "FRONT"
    assert ev_data["sha256"] == expected_sha256
    assert ev_data["processing_status"] == "UPLOADED"

    # Verify audit entry was created
    audit_entry = db_session.query(AuditEntry).filter(
        AuditEntry.inspection_id == "case-cam-001",
        AuditEntry.action == "INGEST_EVIDENCE"
    ).first()
    assert audit_entry is not None
    assert audit_entry.actor_id == "OFFICER-IND-1001"
    app.dependency_overrides.clear()

def test_02_camera_multi_view_ingestion(db_session: Session):
    """Verify all statutory camera capture views are supported (FRONT, BACK, SIDE, BASE, OTHER)."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    c = InspectionCase(
        inspection_id="case-cam-views",
        case_number="CASE-CAM-VIEWS",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.PROCESSING
    )
    db_session.add(c)
    db_session.commit()

    headers = get_auth_headers("OFFICER", "OFFICER-IND-1001")
    views = ["FRONT", "BACK", "SIDE", "BASE", "OTHER"]

    for v in views:
        img = create_synthetic_image(f"Camera frame for {v} view")
        files = {"file": (f"capture_{v.lower()}.jpg", img, "image/jpeg")}
        resp = client.post("/api/v1/cases/case-cam-views/evidence", data={"view_type": v}, files=files, headers=headers)
        assert resp.status_code == 201
        assert resp.json()["view_type"] == v

    # Verify all 5 evidence items are persisted
    items = db_session.query(EvidenceItem).filter(EvidenceItem.inspection_id == "case-cam-views").all()
    assert len(items) == 5
    persisted_views = {item.view_type.value for item in items}
    assert persisted_views == set(views)
    app.dependency_overrides.clear()

def test_03_quality_gate_execution_on_camera_evidence(db_session: Session):
    """Verify OpenCV quality gate runs on camera-captured frame and assesses sharpness/exposure."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    c = InspectionCase(
        inspection_id="case-cam-qg",
        case_number="CASE-CAM-QG",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.PROCESSING
    )
    db_session.add(c)
    db_session.commit()

    # Clear sharp image
    sharp_img = create_synthetic_image("Sharp commodity declaration label")
    headers = get_auth_headers("OFFICER", "OFFICER-IND-1001")
    upload_resp = client.post(
        "/api/v1/cases/case-cam-qg/evidence",
        data={"view_type": "FRONT"},
        files={"file": ("front_cam.jpg", sharp_img, "image/jpeg")},
        headers=headers
    )
    ev_id = upload_resp.json()["evidence_id"]

    # Process evidence OCR & Quality Gate
    proc_resp = client.post(f"/api/v1/evidence/{ev_id}/process", headers=headers)
    assert proc_resp.status_code == 200
    ev_detail = proc_resp.json()

    assert ev_detail["quality_verdict"] in ["PASS", "WARN", "MANUAL_REVIEW"]
    assert ev_detail["quality_report_json"] is not None
    assert "blur_score" in ev_detail["quality_report_json"]
    assert "brightness_score" in ev_detail["quality_report_json"]
    app.dependency_overrides.clear()

def test_04_corrupt_camera_frame_rejected(db_session: Session):
    """Verify invalid or corrupted camera byte stream is rejected with 400 Bad Request."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    c = InspectionCase(
        inspection_id="case-cam-corrupt",
        case_number="CASE-CAM-CORRUPT",
        officer_id="OFFICER-IND-1001"
    )
    db_session.add(c)
    db_session.commit()

    headers = get_auth_headers("OFFICER", "OFFICER-IND-1001")
    corrupt_bytes = b"NOT_A_VALID_JPEG_IMAGE_HEADER_DATA"

    resp = client.post(
        "/api/v1/cases/case-cam-corrupt/evidence",
        data={"view_type": "FRONT"},
        files={"file": ("corrupt_frame.jpg", corrupt_bytes, "image/jpeg")},
        headers=headers
    )
    assert resp.status_code == 400
    assert resp.json().get("error_code") == "INVALID_IMAGE_DATA"
    app.dependency_overrides.clear()


def test_05_unauthorized_user_cannot_ingest_camera_evidence(db_session: Session):
    """Verify RBAC rejects evidence ingestion from unauthorized roles (e.g. REVIEWER role)."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    c = InspectionCase(
        inspection_id="case-cam-unauth",
        case_number="CASE-CAM-UNAUTH",
        officer_id="OFFICER-IND-1001"
    )
    db_session.add(c)
    db_session.commit()

    # Reviewer role is read-only for evidence intake
    headers_rev = get_auth_headers("REVIEWER", "REVIEWER-IND-2001")
    img = create_synthetic_image("Sample")

    resp = client.post(
        "/api/v1/cases/case-cam-unauth/evidence",
        data={"view_type": "FRONT"},
        files={"file": ("frame.jpg", img, "image/jpeg")},
        headers=headers_rev
    )
    assert resp.status_code == 403
    app.dependency_overrides.clear()
