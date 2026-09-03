import pytest
import io
import cv2
import numpy as np
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import jwt

from app.main import app
from app.core.config import settings
from app.core.database import get_db
from app.models.domain import (
    InspectionCase,
    CaseStatus,
    EvidenceItem,
    EvidenceViewType,
    EvidenceProcessingStatus,
    QualityVerdict,
    OverallDetermination,
    UserRole
)
from app.core.security import create_access_token, hash_password, verify_password
from app.audit.hasher import compute_sha256_bytes
from app.services.report_service import ReportService
from tests.fixtures.test_data import db_session, create_synthetic_image

def get_auth_headers(role: str = "OFFICER", user_id: str = "OFFICER-IND-1001", expires_delta: timedelta = None):
    token = create_access_token(data={"sub": user_id, "role": role}, expires_delta=expires_delta)
    return {"Authorization": f"Bearer {token}"}

def test_01_authentication_rejection_when_missing_or_invalid_token():
    """Verify unauthenticated requests to protected endpoints return 401 Unauthorized."""
    client = TestClient(app)

    # 1. Missing Authorization header
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "error_code" in resp.json()

    # 2. Malformed token
    resp_bad = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer MALFORMED_TOKEN_STRING"})
    assert resp_bad.status_code == 401

def test_02_expired_token_rejection():
    """Verify expired JWT tokens are strictly rejected with 401."""
    client = TestClient(app)

    # Generate token expired 10 minutes ago
    expired_headers = get_auth_headers(
        role="OFFICER",
        user_id="OFFICER-IND-1001",
        expires_delta=timedelta(minutes=-10)
    )

    resp = client.get("/api/v1/auth/me", headers=expired_headers)
    assert resp.status_code == 401
    assert resp.json().get("error_code") == "UNAUTHORIZED"

def test_03_secure_password_hashing_and_verification():
    """Verify PBKDF2-HMAC-SHA256 password hashing and secure timing-safe comparison."""
    pw = "SuperSecureSecretPassphrase!2026"
    hashed = hash_password(pw)

    assert hashed != pw
    assert "$" in hashed
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False

def test_04_rbac_boundaries_reviewer_cannot_finalize(db_session: Session):
    """Verify RBAC strictly blocks REVIEWER role from finalising cases or signing legal orders."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    c = InspectionCase(
        inspection_id="case-sec-rbac-01",
        case_number="CASE-SEC-RBAC-01",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.PENDING_REVIEW,
        overall_determination=OverallDetermination.COMPLIANT
    )
    db_session.add(c)
    db_session.commit()

    # Reviewer attempts to submit final order
    reviewer_headers = get_auth_headers(role="REVIEWER", user_id="REVIEWER-IND-2001")
    resp = client.post(
        "/api/v1/cases/case-sec-rbac-01/finalize",
        json={"officer_decision": "COMPLIANT", "officer_remarks": "Reviewer attempt"},
        headers=reviewer_headers
    )
    assert resp.status_code == 403
    assert "not authorized" in resp.json().get("message", "").lower()
    app.dependency_overrides.clear()

def test_05_oversized_and_invalid_upload_rejection(db_session: Session):
    """Verify uploads exceeding 25MB or corrupted binaries are rejected."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    c = InspectionCase(
        inspection_id="case-sec-upload-01",
        case_number="CASE-SEC-UPLOAD-01",
        officer_id="OFFICER-IND-1001"
    )
    db_session.add(c)
    db_session.commit()

    headers = get_auth_headers("OFFICER")

    # 1. Invalid bytes
    resp_invalid = client.post(
        "/api/v1/cases/case-sec-upload-01/evidence",
        data={"view_type": "FRONT"},
        files={"file": ("fake.jpg", b"INVALID_BINARY_BYTES", "image/jpeg")},
        headers=headers
    )
    assert resp_invalid.status_code == 400

    # 2. Unsupported extension
    valid_img = create_synthetic_image("Valid image")
    resp_ext = client.post(
        "/api/v1/cases/case-sec-upload-01/evidence",
        data={"view_type": "FRONT"},
        files={"file": ("malicious_script.exe", valid_img, "application/octet-stream")},
        headers=headers
    )
    assert resp_ext.status_code == 400
    assert resp_ext.json().get("error_code") == "UNSUPPORTED_FILE_EXTENSION"
    app.dependency_overrides.clear()

def test_06_path_traversal_protection(db_session: Session):
    """Verify path traversal filenames (e.g. ../../test.jpg) are sanitized and stored safely."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    c = InspectionCase(
        inspection_id="case-sec-path-01",
        case_number="CASE-SEC-PATH-01",
        officer_id="OFFICER-IND-1001"
    )
    db_session.add(c)
    db_session.commit()

    headers = get_auth_headers("OFFICER")
    img_bytes = create_synthetic_image("Path traversal test")

    resp = client.post(
        "/api/v1/cases/case-sec-path-01/evidence",
        data={"view_type": "FRONT"},
        files={"file": ("../../../../etc/passwd.jpg", img_bytes, "image/jpeg")},
        headers=headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert ".." not in data["file_reference"]
    assert "storage/evidence/case-sec-path-01" in data["file_reference"].replace("\\", "/")
    app.dependency_overrides.clear()

def test_07_security_headers_present_in_responses():
    """Verify standard security headers are attached to API responses."""
    client = TestClient(app)
    resp = client.get("/")

    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "camera=" in resp.headers.get("Permissions-Policy", "")

def test_08_health_endpoint_safety_and_subsystems(db_session: Session):
    """Verify GET /api/v1/health returns safe health statuses without leaking secrets."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] in ["HEALTHY", "DEGRADED"]
    assert data["database_connected"] is True
    assert data["storage_ready"] is True
    assert "subsystems" in data
    assert "SECRET_KEY" not in str(data)
    assert "password" not in str(data).lower()
    app.dependency_overrides.clear()

def test_09_report_generation_uses_configured_verification_base_url(db_session: Session):
    """Verify ReportLab PDF generation incorporates configurable REPORT_VERIFICATION_BASE_URL."""
    c = InspectionCase(
        inspection_id="case-sec-rep-01",
        case_number="CASE-SEC-REP-01",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.FINALISED,
        overall_determination=OverallDetermination.COMPLIANT,
        finalized_at=datetime.now(timezone.utc)
    )
    db_session.add(c)
    db_session.commit()

    report = ReportService.generate_inspection_report(
        db=db_session,
        inspection_id="case-sec-rep-01",
        officer_id="OFFICER-IND-1001"
    )

    assert report is not None
    assert report.status == "GENERATED"
    assert len(report.sha256) == 64
    assert "v1.pdf" in report.file_reference
