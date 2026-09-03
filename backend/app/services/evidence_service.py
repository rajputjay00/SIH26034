import os
import uuid
import cv2
import numpy as np
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.audit.hasher import compute_sha256_bytes
from app.models.domain import (
    EvidenceItem,
    EvidenceViewType,
    EvidenceProcessingStatus,
    QualityVerdict,
    OCRResult,
    InspectionCase,
    CaseStatus,
    AuditEntry
)
from app.services.audit_service import AuditService
from app.services.case_service import CaseService
from app.services.quality_service import QualityAssessmentService
from app.services.preprocessing_service import ImagePreprocessingService
from app.services.ocr_service import OCRService
from app.utils.errors import ResourceNotFoundError, LegalMetrixException

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB

class EvidenceService:
    STORAGE_BASE = "storage/evidence"
    DERIVED_BASE = "storage/derived"

    def __init__(self, db: Session):
        self.db = db
        self.case_service = CaseService(db)

    def ingest_evidence(
        self,
        inspection_id: str,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        view_type: EvidenceViewType,
        officer_id: str
    ) -> EvidenceItem:
        """
        Validate file, store immutable original, calculate SHA-256, and ingest evidence record.
        """
        case = self.case_service.get_case(inspection_id) # Validate case exists
        if case.status == CaseStatus.FINALISED:
            raise LegalMetrixException(
                status_code=400,
                detail="Cannot upload evidence to a finalised inspection case.",
                error_code="CASE_FINALISED"
            )

        # 1. Validation
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise LegalMetrixException(
                status_code=400,
                detail=f"Unsupported file extension '{ext}'. Allowed: {list(ALLOWED_EXTENSIONS)}",
                error_code="UNSUPPORTED_FILE_EXTENSION"
            )

        if not file_bytes or len(file_bytes) == 0:
            raise LegalMetrixException(
                status_code=400,
                detail="Uploaded file is empty (0 bytes).",
                error_code="EMPTY_FILE"
            )

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise LegalMetrixException(
                status_code=400,
                detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB.",
                error_code="FILE_TOO_LARGE"
            )

        # Validate decodeability with OpenCV
        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise LegalMetrixException(
                status_code=400,
                detail="Uploaded file is not a valid decodeable image.",
                error_code="INVALID_IMAGE_DATA"
            )

        height, width = img.shape[:2]

        # 2. SHA-256 Calculation
        sha256_hash = compute_sha256_bytes(file_bytes)

        # 3. Store Immutable Original File
        evidence_id = str(uuid.uuid4())
        sanitized_filename = f"{evidence_id}_{os.path.basename(filename)}"
        case_evidence_dir = os.path.join(self.STORAGE_BASE, inspection_id)
        os.makedirs(case_evidence_dir, exist_ok=True)
        original_file_path = os.path.join(case_evidence_dir, sanitized_filename)

        with open(original_file_path, "wb") as f:
            f.write(file_bytes)

        # 4. Save Database Record
        evidence = EvidenceItem(
            evidence_id=evidence_id,
            inspection_id=inspection_id,
            original_filename=filename,
            media_type=content_type or "image/jpeg",
            file_reference=original_file_path,
            sha256=sha256_hash,
            view_type=view_type,
            processing_status=EvidenceProcessingStatus.UPLOADED,
            quality_verdict=QualityVerdict.UNCHECKED,
            dimensions_json={"width": width, "height": height},
            metadata_json={"bytes": len(file_bytes), "format": ext.replace(".", "").upper()},
            ingested_at=datetime.now(timezone.utc)
        )

        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)

        # 5. Audit Ingestion
        AuditService.record_event(
            db=self.db,
            inspection_id=inspection_id,
            actor_id=officer_id,
            action="INGEST_EVIDENCE",
            entity_type="EvidenceItem",
            entity_id=evidence_id,
            metadata={
                "filename": filename,
                "sha256": sha256_hash,
                "view_type": view_type.value,
                "dimensions": f"{width}x{height}"
            }
        )

        return evidence

    def process_evidence(
        self,
        evidence_id: str,
        officer_id: str
    ) -> EvidenceItem:
        """
        Execute full image pipeline on ingested evidence:
        Quality Assessment -> Preprocessing -> OCR -> Result Persistence
        """
        evidence = self.get_evidence(evidence_id)
        inspection_id = evidence.inspection_id

        if not os.path.exists(evidence.file_reference):
            evidence.processing_status = EvidenceProcessingStatus.OCR_FAILED
            self.db.commit()
            raise ResourceNotFoundError("EvidenceFileOnDisk", evidence.file_reference)

        with open(evidence.file_reference, "rb") as f:
            file_bytes = f.read()

        # Step 1: Quality Check
        evidence.processing_status = EvidenceProcessingStatus.QUALITY_CHECK
        self.db.commit()

        quality_report = QualityAssessmentService.evaluate_image(file_bytes)
        evidence.quality_verdict = quality_report.verdict
        evidence.quality_report_json = quality_report.model_dump(mode="json")

        if quality_report.verdict == QualityVerdict.FAIL:
            evidence.processing_status = EvidenceProcessingStatus.MANUAL_REVIEW
            self.db.commit()
            AuditService.record_event(
                db=self.db,
                inspection_id=inspection_id,
                actor_id=officer_id,
                action="QUALITY_CHECK_FAILED",
                entity_type="EvidenceItem",
                entity_id=evidence_id,
                metadata={"verdict": quality_report.verdict.value, "diagnostics": quality_report.diagnostics}
            )
            return evidence

        # Step 2: Preprocessing
        evidence.processing_status = EvidenceProcessingStatus.PREPROCESSING
        self.db.commit()

        derived_dir = os.path.join(self.DERIVED_BASE, inspection_id, evidence_id)
        variants_map = ImagePreprocessingService.generate_variants(evidence.file_reference, derived_dir)
        evidence.preprocessed_references_json = variants_map

        # Step 3: OCR Processing
        evidence.processing_status = EvidenceProcessingStatus.OCR_PROCESSING
        self.db.commit()

        # Run OCR on the contrast-enhanced variant (or original)
        target_ocr_path = variants_map.get("contrast_enhanced", evidence.file_reference)
        ocr_data = OCRService.run_ocr(
            image_path=target_ocr_path,
            variant_name="contrast_enhanced",
            evidence_id=evidence_id,
            inspection_id=inspection_id
        )

        # Step 4: Persist OCR Result
        ocr_result = OCRResult(
            ocr_id=str(uuid.uuid4()),
            evidence_id=evidence_id,
            inspection_id=inspection_id,
            engine=ocr_data["engine"],
            preprocessing_variant=ocr_data["preprocessing_variant"],
            full_text=ocr_data["full_text"],
            boxes_json=ocr_data["boxes_json"],
            average_confidence=ocr_data["average_confidence"],
            processing_time_ms=ocr_data["processing_time_ms"],
            created_at=datetime.now(timezone.utc)
        )

        self.db.add(ocr_result)
        evidence.processing_status = EvidenceProcessingStatus.OCR_COMPLETE
        self.db.commit()
        self.db.refresh(evidence)

        # Step 5: Audit Event
        AuditService.record_event(
            db=self.db,
            inspection_id=inspection_id,
            actor_id=officer_id,
            action="OCR_COMPLETE",
            entity_type="OCRResult",
            entity_id=ocr_result.ocr_id,
            metadata={
                "evidence_id": evidence_id,
                "engine": ocr_data["engine"],
                "boxes_extracted": len(ocr_data["boxes_json"]),
                "avg_confidence": ocr_data["average_confidence"],
                "processing_time_ms": ocr_data["processing_time_ms"]
            }
        )

        return evidence

    def get_evidence(self, evidence_id: str) -> EvidenceItem:
        evidence = self.db.query(EvidenceItem).filter(EvidenceItem.evidence_id == evidence_id).first()
        if not evidence:
            raise ResourceNotFoundError("EvidenceItem", evidence_id)
        return evidence

    def list_case_evidence(self, inspection_id: str) -> List[EvidenceItem]:
        self.case_service.get_case(inspection_id)
        return self.db.query(EvidenceItem)\
            .filter(EvidenceItem.inspection_id == inspection_id)\
            .order_by(EvidenceItem.ingested_at.asc())\
            .all()

    def get_evidence_ocr(self, evidence_id: str) -> List[OCRResult]:
        evidence = self.get_evidence(evidence_id)
        return self.db.query(OCRResult)\
            .filter(OCRResult.evidence_id == evidence_id)\
            .order_by(OCRResult.created_at.desc())\
            .all()

    def retry_evidence_processing(self, evidence_id: str, officer_id: str) -> EvidenceItem:
        """Retry quality check and OCR processing on existing evidence image."""
        evidence = self.get_evidence(evidence_id)
        evidence.processing_status = EvidenceProcessingStatus.UPLOADED
        self.db.commit()

        AuditService.record_event(
            db=self.db,
            inspection_id=evidence.inspection_id,
            actor_id=officer_id,
            action="RETRY_EVIDENCE_PROCESSING",
            entity_type="EvidenceItem",
            entity_id=evidence_id,
            metadata={"previous_status": evidence.processing_status.value}
        )

        return self.process_evidence(evidence_id, officer_id)
