import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from tests.fixtures.test_data import db_session, create_synthetic_image
from app.models.domain import (
    InspectionCase,
    EvidenceItem,
    EvidenceViewType,
    EvidenceProcessingStatus,
    QualityVerdict,
    OCRResult
)
from app.services.case_service import CaseService
from app.services.evidence_service import EvidenceService
from app.services.quality_service import QualityAssessmentService
from app.services.preprocessing_service import ImagePreprocessingService
from app.services.ocr_service import OCRService
from app.audit.hasher import compute_sha256_bytes
from app.utils.errors import LegalMetrixException

def test_evidence_ingestion_and_sha256(db_session):
    case_service = CaseService(db_session)
    case = case_service.create_case(officer_id="OFFICER-001", notes="Evidence test case")

    image_bytes = create_synthetic_image()
    expected_hash = compute_sha256_bytes(image_bytes)

    evidence_service = EvidenceService(db_session)
    evidence = evidence_service.ingest_evidence(
        inspection_id=case.inspection_id,
        file_bytes=image_bytes,
        filename="package_front.jpg",
        content_type="image/jpeg",
        view_type=EvidenceViewType.FRONT,
        officer_id="OFFICER-001"
    )

    assert evidence.evidence_id is not None
    assert evidence.sha256 == expected_hash
    assert evidence.view_type == EvidenceViewType.FRONT
    assert evidence.processing_status == EvidenceProcessingStatus.UPLOADED
    assert os.path.exists(evidence.file_reference)

    # Verify original file content matches hash
    with open(evidence.file_reference, "rb") as f:
        stored_bytes = f.read()
    assert compute_sha256_bytes(stored_bytes) == expected_hash

def test_multi_image_evidence_views(db_session):
    case_service = CaseService(db_session)
    case = case_service.create_case(officer_id="OFFICER-001")
    evidence_service = EvidenceService(db_session)

    views = [
        EvidenceViewType.FRONT,
        EvidenceViewType.BACK,
        EvidenceViewType.SIDE,
        EvidenceViewType.BASE,
        EvidenceViewType.OTHER
    ]

    for view in views:
        img_bytes = create_synthetic_image(text=f"View {view.value}")
        evidence = evidence_service.ingest_evidence(
            inspection_id=case.inspection_id,
            file_bytes=img_bytes,
            filename=f"package_{view.value.lower()}.jpg",
            content_type="image/jpeg",
            view_type=view,
            officer_id="OFFICER-001"
        )
        assert evidence.view_type == view

    all_evidence = evidence_service.list_case_evidence(case.inspection_id)
    assert len(all_evidence) == 5

def test_file_validation_rejects_invalid_inputs(db_session):
    case_service = CaseService(db_session)
    case = case_service.create_case(officer_id="OFFICER-001")
    evidence_service = EvidenceService(db_session)

    # 1. Invalid Extension
    with pytest.raises(LegalMetrixException) as exc:
        evidence_service.ingest_evidence(
            inspection_id=case.inspection_id,
            file_bytes=b"fake data",
            filename="malicious.exe",
            content_type="application/octet-stream",
            view_type=EvidenceViewType.FRONT,
            officer_id="OFFICER-001"
        )
    assert exc.value.error_code == "UNSUPPORTED_FILE_EXTENSION"

    # 2. Corrupt / Undecodeable Image Bytes
    with pytest.raises(LegalMetrixException) as exc:
        evidence_service.ingest_evidence(
            inspection_id=case.inspection_id,
            file_bytes=b"NOT_A_REAL_IMAGE",
            filename="corrupted.jpg",
            content_type="image/jpeg",
            view_type=EvidenceViewType.FRONT,
            officer_id="OFFICER-001"
        )
    assert exc.value.error_code == "INVALID_IMAGE_DATA"

def test_quality_gate_evaluates_sharp_vs_blurry_vs_dark():
    # Sharp image -> PASS
    sharp_bytes = create_synthetic_image()
    report_sharp = QualityAssessmentService.evaluate_image(sharp_bytes)
    assert report_sharp.verdict in [QualityVerdict.PASS, QualityVerdict.WARN]
    assert report_sharp.is_readable is True
    assert report_sharp.blur_score > 50.0

    # Blurry image -> WARN / FAIL
    blurry_bytes = create_synthetic_image(blur=True)
    report_blurry = QualityAssessmentService.evaluate_image(blurry_bytes)
    assert report_blurry.blur_score < report_sharp.blur_score

    # Dark image -> WARN / FAIL
    dark_bytes = create_synthetic_image(dark=True)
    report_dark = QualityAssessmentService.evaluate_image(dark_bytes)
    assert report_dark.brightness_score < 40.0

def test_preprocessing_and_ocr_execution_pipeline(db_session):
    case_service = CaseService(db_session)
    case = case_service.create_case(officer_id="OFFICER-001")
    evidence_service = EvidenceService(db_session)

    img_bytes = create_synthetic_image(text="NET WEIGHT 500g MRP Rs 120.00")
    evidence = evidence_service.ingest_evidence(
        inspection_id=case.inspection_id,
        file_bytes=img_bytes,
        filename="sample_test.jpg",
        content_type="image/jpeg",
        view_type=EvidenceViewType.FRONT,
        officer_id="OFFICER-001"
    )

    # Process evidence through Quality Gate, Preprocessing & OCR
    processed = evidence_service.process_evidence(evidence.evidence_id, officer_id="OFFICER-001")
    assert processed.processing_status == EvidenceProcessingStatus.OCR_COMPLETE
    assert processed.quality_verdict in [QualityVerdict.PASS, QualityVerdict.WARN]
    assert processed.preprocessed_references_json is not None
    assert "grayscale" in processed.preprocessed_references_json
    assert "contrast_enhanced" in processed.preprocessed_references_json

    # Check persisted OCR result
    ocr_results = evidence_service.get_evidence_ocr(evidence.evidence_id)
    assert len(ocr_results) >= 1
    first_ocr = ocr_results[0]
    assert first_ocr.evidence_id == evidence.evidence_id
    assert first_ocr.inspection_id == case.inspection_id
    assert isinstance(first_ocr.boxes_json, list)
    assert first_ocr.average_confidence >= 0.0

def test_retry_evidence_processing(db_session):
    case_service = CaseService(db_session)
    case = case_service.create_case(officer_id="OFFICER-001")
    evidence_service = EvidenceService(db_session)

    img_bytes = create_synthetic_image()
    evidence = evidence_service.ingest_evidence(
        inspection_id=case.inspection_id,
        file_bytes=img_bytes,
        filename="retry_test.jpg",
        content_type="image/jpeg",
        view_type=EvidenceViewType.BACK,
        officer_id="OFFICER-001"
    )

    evidence_service.process_evidence(evidence.evidence_id, officer_id="OFFICER-001")
    retried = evidence_service.retry_evidence_processing(evidence.evidence_id, officer_id="OFFICER-001")
    assert retried.processing_status == EvidenceProcessingStatus.OCR_COMPLETE
