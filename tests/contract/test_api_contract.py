import pytest
import io
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from fastapi.testclient import TestClient
from app.main import app
from tests.fixtures.test_data import create_synthetic_image

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["HEALTHY", "DEGRADED"]
    assert "app_name" in data
    assert "database_connected" in data
    assert "server_time" in data

def test_create_and_get_case_contract():
    login_resp = client.post("/api/v1/auth/login", json={"username": "officer1", "password": "password123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post(
        "/api/v1/cases",
        json={"notes": "Contract test case", "rule_pack_version": "v1.0.0"},
        headers=headers
    )
    assert create_resp.status_code == 201
    case_data = create_resp.json()
    assert "inspection_id" in case_data
    assert case_data["status"] == "DRAFT"

    inspection_id = case_data["inspection_id"]
    get_resp = client.get(f"/api/v1/cases/{inspection_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["inspection_id"] == inspection_id

def test_invalid_state_transition_handling():
    login_resp = client.post("/api/v1/auth/login", json={"username": "officer1", "password": "password123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post("/api/v1/cases", json={"notes": "State test"}, headers=headers)
    case_id = create_resp.json()["inspection_id"]

    # Attempt direct transition from DRAFT to FINALISED (Invalid state transition)
    patch_resp = client.patch(f"/api/v1/cases/{case_id}/status", json={"status": "FINALISED"}, headers=headers)
    assert patch_resp.status_code == 400
    err_data = patch_resp.json()
    assert err_data["error_code"] == "INVALID_STATE_TRANSITION"

def test_evidence_and_ocr_api_contract():
    login_resp = client.post("/api/v1/auth/login", json={"username": "officer1", "password": "password123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create inspection case
    case_resp = client.post("/api/v1/cases", json={"notes": "Evidence API Contract Test"}, headers=headers)
    case_id = case_resp.json()["inspection_id"]

    # 2. Upload Evidence Image
    img_bytes = create_synthetic_image(text="TEST BATCH 2026")
    files = {"file": ("test_package.jpg", io.BytesIO(img_bytes), "image/jpeg")}
    data = {"view_type": "FRONT"}

    upload_resp = client.post(f"/api/v1/cases/{case_id}/evidence", files=files, data=data, headers=headers)
    assert upload_resp.status_code == 201
    ev_data = upload_resp.json()
    assert "evidence_id" in ev_data
    assert ev_data["view_type"] == "FRONT"
    assert ev_data["processing_status"] == "UPLOADED"
    evidence_id = ev_data["evidence_id"]

    # 3. List Case Evidence
    list_resp = client.get(f"/api/v1/cases/{case_id}/evidence", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # 4. Get Single Evidence Detail
    detail_resp = client.get(f"/api/v1/evidence/{evidence_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["evidence_id"] == evidence_id

    # 5. Process Evidence (Quality + Preprocess + OCR)
    process_resp = client.post(f"/api/v1/evidence/{evidence_id}/process", headers=headers)
    assert process_resp.status_code == 200
    proc_data = process_resp.json()
    assert proc_data["processing_status"] == "OCR_COMPLETE"
    assert proc_data["quality_verdict"] in ["PASS", "WARN"]

    # 6. Get OCR Results
    ocr_resp = client.get(f"/api/v1/evidence/{evidence_id}/ocr", headers=headers)
    assert ocr_resp.status_code == 200
    ocr_list = ocr_resp.json()
    assert len(ocr_list) >= 1
    assert "boxes_json" in ocr_list[0]
    assert "average_confidence" in ocr_list[0]

    # 7. Retry Processing
    retry_resp = client.post(f"/api/v1/evidence/{evidence_id}/retry", headers=headers)
    assert retry_resp.status_code == 200
    assert retry_resp.json()["processing_status"] == "OCR_COMPLETE"

    # 8. Structured Field Extraction
    extract_resp = client.post(f"/api/v1/cases/{case_id}/extract", headers=headers)
    assert extract_resp.status_code == 200
    fields = extract_resp.json()
    assert isinstance(fields, list)

    # 9. List Case Fields
    fields_resp = client.get(f"/api/v1/cases/{case_id}/fields", headers=headers)
    assert fields_resp.status_code == 200

    # 10. Run Compliance Evaluation
    eval_resp = client.post(f"/api/v1/cases/{case_id}/evaluate", headers=headers)
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert "overall_determination" in eval_data
    assert "findings" in eval_data

    # 11. Get Findings
    findings_resp = client.get(f"/api/v1/cases/{case_id}/findings", headers=headers)
    assert findings_resp.status_code == 200
    assert isinstance(findings_resp.json(), list)


