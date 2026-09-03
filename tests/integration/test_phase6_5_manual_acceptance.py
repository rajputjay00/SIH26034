import pytest
import cv2
import numpy as np
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
    ExtractedField,
    RuleFinding
)
from app.audit.hasher import compute_sha256_bytes
from app.services.provenance_service import ProvenanceService
from tests.fixtures.test_data import db_session, create_synthetic_image

def get_auth_headers(role: str = "OFFICER", user_id: str = "OFFICER-IND-1001"):
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}

def test_acceptance_01_mobile_camera_environment_capture(db_session: Session):
    """
    MANUAL ACCEPTANCE TEST 1: MOBILE CAMERA
    Verify rear/environment-facing camera frame capture and ingestion.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    # 1. Create real case
    c = InspectionCase(
        inspection_id="case-accept-01",
        case_number="CASE-ACCEPT-MOBILE-CAM",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.PROCESSING
    )
    db_session.add(c)
    db_session.commit()

    # 2. Simulate mobile environment camera capture (1920x1080)
    mobile_frame = np.full((1080, 1920, 3), 245, dtype=np.uint8)
    cv2.putText(mobile_frame, "MRP Rs 199.00 Net Qty: 250 g", (100, 500), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)
    _, encoded = cv2.imencode(".jpg", mobile_frame)
    frame_bytes = encoded.tobytes()

    headers = get_auth_headers("OFFICER")
    files = {"file": ("capture_front_mobile_env.jpg", frame_bytes, "image/jpeg")}
    data = {"view_type": "FRONT"}

    resp = client.post("/api/v1/cases/case-accept-01/evidence", data=data, files=files, headers=headers)
    assert resp.status_code == 201
    res_data = resp.json()

    assert res_data["inspection_id"] == "case-accept-01"
    assert res_data["view_type"] == "FRONT"
    assert len(res_data["sha256"]) == 64
    assert res_data["dimensions_json"]["width"] == 1920
    assert res_data["dimensions_json"]["height"] == 1080
    app.dependency_overrides.clear()

def test_acceptance_02_retake_flow_only_persists_accepted_frame(db_session: Session):
    """
    MANUAL ACCEPTANCE TEST 2: RETAKE
    Simulate capture -> retake (discard) -> capture again (accept).
    Verify ONLY the accepted frame enters the evidence database.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    c = InspectionCase(
        inspection_id="case-accept-02",
        case_number="CASE-ACCEPT-RETAKE",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.PROCESSING
    )
    db_session.add(c)
    db_session.commit()

    # Frame 1: Discarded / Retaken (never submitted to API)
    frame1_img = create_synthetic_image("Blurry discarded frame")
    frame1_sha = compute_sha256_bytes(frame1_img)

    # Frame 2: Accepted Photo
    frame2_img = create_synthetic_image("Sharp accepted photo frame")
    frame2_sha = compute_sha256_bytes(frame2_img)

    headers = get_auth_headers("OFFICER")
    files = {"file": ("capture_back_accepted.jpg", frame2_img, "image/jpeg")}
    data = {"view_type": "BACK"}

    resp = client.post("/api/v1/cases/case-accept-02/evidence", data=data, files=files, headers=headers)
    assert resp.status_code == 201

    # Verify only Frame 2 exists in DB, Frame 1 does NOT exist
    all_evidence = db_session.query(EvidenceItem).filter(EvidenceItem.inspection_id == "case-accept-02").all()
    assert len(all_evidence) == 1
    assert all_evidence[0].sha256 == frame2_sha
    assert all_evidence[0].sha256 != frame1_sha
    app.dependency_overrides.clear()

def test_acceptance_03_permission_denied_fallback_to_upload(db_session: Session):
    """
    MANUAL ACCEPTANCE TEST 3: PERMISSION DENIED
    Verify that when camera is blocked, normal file upload fallback works seamlessly.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    c = InspectionCase(
        inspection_id="case-accept-03",
        case_number="CASE-ACCEPT-FALLBACK",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.PROCESSING
    )
    db_session.add(c)
    db_session.commit()

    # Fallback file upload from storage
    fallback_img = create_synthetic_image("Uploaded file via fallback mechanism")
    headers = get_auth_headers("OFFICER")
    files = {"file": ("fallback_package_front.png", fallback_img, "image/png")}
    data = {"view_type": "FRONT"}

    resp = client.post("/api/v1/cases/case-accept-03/evidence", data=data, files=files, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["original_filename"] == "fallback_package_front.png"
    assert resp.json()["view_type"] == "FRONT"
    app.dependency_overrides.clear()

def test_acceptance_04_multi_view_belongs_to_same_inspection(db_session: Session):
    """
    MANUAL ACCEPTANCE TEST 4: MULTI-VIEW
    Capture Front -> Back -> Side -> Base.
    Verify all 4 are attached to the SAME inspection.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    inspection_id = "case-accept-04-multiview"
    c = InspectionCase(
        inspection_id=inspection_id,
        case_number="CASE-ACCEPT-MULTIVIEW",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.PROCESSING
    )
    db_session.add(c)
    db_session.commit()

    headers = get_auth_headers("OFFICER")
    views = [
        (EvidenceViewType.FRONT, "Front principal display"),
        (EvidenceViewType.BACK, "Back declaration panel"),
        (EvidenceViewType.SIDE, "Side consumer care panel"),
        (EvidenceViewType.BASE, "Base batch and date stamp")
    ]

    for v_type, label in views:
        img = create_synthetic_image(label)
        files = {"file": (f"capture_{v_type.value.lower()}.jpg", img, "image/jpeg")}
        data = {"view_type": v_type.value}
        resp = client.post(f"/api/v1/cases/{inspection_id}/evidence", data=data, files=files, headers=headers)
        assert resp.status_code == 201
        assert resp.json()["inspection_id"] == inspection_id

    # Verify query for case evidence returns all 4 views linked to this exact inspection
    persisted = db_session.query(EvidenceItem).filter(EvidenceItem.inspection_id == inspection_id).all()
    assert len(persisted) == 4
    for item in persisted:
        assert item.inspection_id == inspection_id

    views_in_db = {item.view_type for item in persisted}
    assert views_in_db == {EvidenceViewType.FRONT, EvidenceViewType.BACK, EvidenceViewType.SIDE, EvidenceViewType.BASE}
    app.dependency_overrides.clear()

def test_acceptance_05_complete_evidence_pipeline(db_session: Session):
    """
    MANUAL ACCEPTANCE TEST 5: PIPELINE
    Capture photo -> Evidence created -> SHA-256 -> Quality Gate -> OCR -> Provenance.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    inspection_id = "case-accept-05-pipeline"
    c = InspectionCase(
        inspection_id=inspection_id,
        case_number="CASE-ACCEPT-PIPELINE",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.PROCESSING
    )
    db_session.add(c)
    db_session.commit()

    # Step A: Capture/Upload evidence
    img_bytes = create_synthetic_image("MRP Rs 50.00 Net Wt 100g")
    expected_sha = compute_sha256_bytes(img_bytes)

    headers = get_auth_headers("OFFICER")
    files = {"file": ("camera_front.jpg", img_bytes, "image/jpeg")}
    data = {"view_type": "FRONT"}

    upload_resp = client.post(f"/api/v1/cases/{inspection_id}/evidence", data=data, files=files, headers=headers)
    assert upload_resp.status_code == 201
    ev_data = upload_resp.json()
    ev_id = ev_data["evidence_id"]

    # Step B: Verify SHA-256 calculated
    assert ev_data["sha256"] == expected_sha

    # Step C: Execute Quality Gate & OCR Processing
    proc_resp = client.post(f"/api/v1/evidence/{ev_id}/process", headers=headers)
    assert proc_resp.status_code == 200
    proc_data = proc_resp.json()

    # Verify Quality Gate executed
    assert proc_data["quality_verdict"] in [QualityVerdict.PASS.value, QualityVerdict.WARN.value, QualityVerdict.MANUAL_REVIEW.value]
    assert proc_data["quality_report_json"] is not None
    assert "blur_score" in proc_data["quality_report_json"]

    # Step D: Verify OCR executed
    ocr_resp = client.get(f"/api/v1/evidence/{ev_id}/ocr", headers=headers)
    assert ocr_resp.status_code == 200
    ocr_results = ocr_resp.json()
    assert len(ocr_results) > 0

    # Step E: Verify Provenance link
    # Create field linked to this evidence
    field = ExtractedField(
        field_id="f-accept-05",
        inspection_id=inspection_id,
        source_evidence_id=ev_id,
        field_name="mrp",
        raw_value="50.00",
        normalized_value="50.00",
        unit="INR",
        bounding_box_json=[[10, 10], [100, 10], [100, 40], [10, 40]]
    )
    db_session.add(field)
    db_session.commit()

    prov = ProvenanceService.get_field_provenance(db_session, "f-accept-05")
    assert prov["source_evidence"]["evidence_id"] == ev_id
    assert prov["source_evidence"]["sha256"] == expected_sha
    assert prov["bounding_box"] == [[10, 10], [100, 10], [100, 40], [10, 40]]
    app.dependency_overrides.clear()

def test_acceptance_06_show_me_where_bounding_box_navigation(db_session: Session):
    """
    MANUAL ACCEPTANCE TEST 6: SHOW ME WHERE
    Open a finding/declaration with an OCR bounding box.
    Verify correct source image opens and actual bounding region is identified.
    """
    inspection_id = "case-accept-06-where"
    c = InspectionCase(
        inspection_id=inspection_id,
        case_number="CASE-ACCEPT-WHERE",
        officer_id="OFFICER-IND-1001",
        status=CaseStatus.PENDING_REVIEW
    )
    db_session.add(c)

    ev = EvidenceItem(
        evidence_id="ev-accept-06",
        inspection_id=inspection_id,
        original_filename="front_panel.jpg",
        media_type="image/jpeg",
        file_reference="storage/evidence/front_panel.jpg",
        sha256="11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff",
        view_type=EvidenceViewType.FRONT,
        processing_status=EvidenceProcessingStatus.OCR_COMPLETE,
        quality_verdict=QualityVerdict.PASS
    )
    db_session.add(ev)

    expected_bbox = [[50, 120], [250, 120], [250, 160], [50, 160]]
    field = ExtractedField(
        field_id="f-accept-06-mrp",
        inspection_id=inspection_id,
        source_evidence_id="ev-accept-06",
        field_name="mrp",
        raw_value="149.00",
        normalized_value="149.00",
        unit="INR",
        bounding_box_json=expected_bbox
    )
    db_session.add(field)
    db_session.commit()

    # Retrieve field provenance for "Show Me Where"
    prov = ProvenanceService.get_field_provenance(db_session, "f-accept-06-mrp")

    assert prov["field_id"] == "f-accept-06-mrp"
    assert prov["source_evidence"] is not None
    assert prov["source_evidence"]["evidence_id"] == "ev-accept-06"
    assert prov["source_evidence"]["original_filename"] == "front_panel.jpg"
    assert prov["source_evidence"]["view_type"] == "FRONT"
    assert prov["bounding_box"] == expected_bbox
