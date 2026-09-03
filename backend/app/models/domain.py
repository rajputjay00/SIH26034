import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, JSON, Enum, Text, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    OFFICER = "OFFICER"
    REVIEWER = "REVIEWER"

class CaseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    PENDING_REVIEW = "PENDING_REVIEW"
    FINALISED = "FINALISED"

class EvidenceViewType(str, enum.Enum):
    FRONT = "FRONT"
    BACK = "BACK"
    SIDE = "SIDE"
    BASE = "BASE"
    OTHER = "OTHER"

class EvidenceProcessingStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    QUALITY_CHECK = "QUALITY_CHECK"
    PREPROCESSING = "PREPROCESSING"
    OCR_PROCESSING = "OCR_PROCESSING"
    OCR_COMPLETE = "OCR_COMPLETE"
    OCR_FAILED = "OCR_FAILED"
    MANUAL_REVIEW = "MANUAL_REVIEW"

class QualityVerdict(str, enum.Enum):
    UNCHECKED = "UNCHECKED"
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    MANUAL_REVIEW = "MANUAL_REVIEW"

class ExtractionOrigin(str, enum.Enum):
    AI = "AI"
    OFFICER = "OFFICER"
    SYSTEM = "SYSTEM"

class FindingStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"
    NOT_APPLICABLE = "NOT_APPLICABLE"

class FindingSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class FieldApplicability(str, enum.Enum):
    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"

class FieldStatus(str, enum.Enum):
    EXTRACTED = "EXTRACTED"
    MISSING = "MISSING"
    UNCERTAIN = "UNCERTAIN"
    CONFLICTING = "CONFLICTING"
    CORRECTED = "CORRECTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    MANUAL_REVIEW = "MANUAL_REVIEW"

class OverallDetermination(str, enum.Enum):
    PENDING_EVALUATION = "PENDING_EVALUATION"
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"

class InspectionCase(Base):
    __tablename__ = "inspection_cases"

    inspection_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_number = Column(String(64), unique=True, nullable=False, index=True)
    officer_id = Column(String(64), nullable=False, index=True)
    status = Column(Enum(CaseStatus), nullable=False, default=CaseStatus.DRAFT, index=True)
    overall_determination = Column(Enum(OverallDetermination), nullable=False, default=OverallDetermination.PENDING_EVALUATION, index=True)
    rule_pack_version = Column(String(32), nullable=False, default="v1.0.0")
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    finalized_at = Column(DateTime, nullable=True)
    officer_decision = Column(String(32), nullable=True)
    officer_remarks = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)



    # Relationships
    evidence_items = relationship("EvidenceItem", back_populates="case", cascade="all, delete-orphan")
    calibrations = relationship("CalibrationData", back_populates="case", cascade="all, delete-orphan")
    visual_measurements = relationship("VisualMeasurement", back_populates="case", cascade="all, delete-orphan")
    visual_anomalies = relationship("VisualAnomaly", back_populates="case", cascade="all, delete-orphan")
    extracted_fields = relationship("ExtractedField", back_populates="case", cascade="all, delete-orphan")
    rule_findings = relationship("RuleFinding", back_populates="case", cascade="all, delete-orphan")
    audit_entries = relationship("AuditEntry", back_populates="case", cascade="all, delete-orphan")
    reports = relationship("GeneratedReport", back_populates="case", cascade="all, delete-orphan")
    ocr_results = relationship("OCRResult", back_populates="case", cascade="all, delete-orphan")

class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    evidence_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey("inspection_cases.inspection_id"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    media_type = Column(String(64), nullable=False, default="image/jpeg")
    file_reference = Column(String(512), nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    view_type = Column(Enum(EvidenceViewType), nullable=False, default=EvidenceViewType.FRONT)
    processing_status = Column(Enum(EvidenceProcessingStatus), nullable=False, default=EvidenceProcessingStatus.UPLOADED)
    quality_verdict = Column(Enum(QualityVerdict), nullable=False, default=QualityVerdict.UNCHECKED)
    dimensions_json = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    quality_report_json = Column(JSON, nullable=True)
    preprocessed_references_json = Column(JSON, nullable=True)
    captured_at = Column(DateTime, nullable=True)
    ingested_at = Column(DateTime, nullable=False, default=utc_now)

    case = relationship("InspectionCase", back_populates="evidence_items")
    calibrations = relationship("CalibrationData", back_populates="evidence")
    visual_measurements = relationship("VisualMeasurement", back_populates="evidence", cascade="all, delete-orphan")
    visual_anomalies = relationship("VisualAnomaly", back_populates="evidence", cascade="all, delete-orphan")
    extracted_fields = relationship("ExtractedField", back_populates="evidence")
    ocr_results = relationship("OCRResult", back_populates="evidence", cascade="all, delete-orphan")


class OCRResult(Base):
    __tablename__ = "ocr_results"

    ocr_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evidence_id = Column(String(36), ForeignKey("evidence_items.evidence_id"), nullable=False, index=True)
    inspection_id = Column(String(36), ForeignKey("inspection_cases.inspection_id"), nullable=False, index=True)
    engine = Column(String(64), nullable=False, default="PaddleOCR-v4")
    preprocessing_variant = Column(String(64), nullable=False, default="original")
    full_text = Column(Text, nullable=False, default="")
    boxes_json = Column(JSON, nullable=False, default=list)
    average_confidence = Column(Float, nullable=False, default=0.0)
    processing_time_ms = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    evidence = relationship("EvidenceItem", back_populates="ocr_results")
    case = relationship("InspectionCase", back_populates="ocr_results")


class CalibrationStatus(str, enum.Enum):
    PENDING = "PENDING"
    CALIBRATED = "CALIBRATED"
    CALIBRATION_UNAVAILABLE = "CALIBRATION_UNAVAILABLE"
    AMBIGUOUS_CALIBRATION = "AMBIGUOUS_CALIBRATION"
    MANUAL_REVIEW = "MANUAL_REVIEW"

class CalibrationData(Base):
    __tablename__ = "calibration_data"

    calibration_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey("inspection_cases.inspection_id"), nullable=False, index=True)
    evidence_id = Column(String(36), ForeignKey("evidence_items.evidence_id"), nullable=True, index=True)
    calibration_method = Column(String(64), nullable=False, default="PHYSICAL_REFERENCE")
    reference_object = Column(String(64), nullable=True, default="INDIAN_5_RUPEE_COIN")
    reference_measurement_mm = Column(Float, nullable=True, default=23.0)
    detected_pixel_measurement = Column(Float, nullable=True)
    mm_per_pixel = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    bounding_geometry_json = Column(JSON, nullable=True)
    status = Column(Enum(CalibrationStatus), nullable=False, default=CalibrationStatus.PENDING)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    case = relationship("InspectionCase", back_populates="calibrations")
    evidence = relationship("EvidenceItem", back_populates="calibrations")
    measurements = relationship("VisualMeasurement", back_populates="calibration", cascade="all, delete-orphan")

class VisualMeasurement(Base):
    __tablename__ = "visual_measurements"

    measurement_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey("inspection_cases.inspection_id"), nullable=False, index=True)
    evidence_id = Column(String(36), ForeignKey("evidence_items.evidence_id"), nullable=False, index=True)
    calibration_id = Column(String(36), ForeignKey("calibration_data.calibration_id"), nullable=True, index=True)
    measurement_type = Column(String(64), nullable=False, default="FONT_HEIGHT")
    target_text = Column(String(255), nullable=True)
    character_type = Column(String(32), nullable=False, default="UNKNOWN")
    pdp_area_cm2 = Column(Float, nullable=True)
    pdp_area_source = Column(String(32), nullable=False, default="UNKNOWN")
    declaration_method = Column(String(32), nullable=False, default="UNKNOWN")
    source_bbox_json = Column(JSON, nullable=True)
    pixel_value = Column(Float, nullable=False)
    physical_value = Column(Float, nullable=True)
    unit = Column(String(32), nullable=False, default="mm")
    confidence = Column(Float, nullable=False, default=0.0)
    status = Column(String(32), nullable=False, default="MEASURED")
    method_version = Column(String(32), nullable=False, default="v1.0.0")
    created_at = Column(DateTime, nullable=False, default=utc_now)



    case = relationship("InspectionCase", back_populates="visual_measurements")
    evidence = relationship("EvidenceItem", back_populates="visual_measurements")
    calibration = relationship("CalibrationData", back_populates="measurements")

class VisualAnomaly(Base):
    __tablename__ = "visual_anomalies"

    anomaly_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey("inspection_cases.inspection_id"), nullable=False, index=True)
    evidence_id = Column(String(36), ForeignKey("evidence_items.evidence_id"), nullable=False, index=True)
    anomaly_type = Column(String(64), nullable=False, default="SUSPECTED_OVERLAY")
    bounding_box_json = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    metrics_json = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False, default="DETECTED")
    officer_review_required = Column(String(8), nullable=False, default="YES")
    created_at = Column(DateTime, nullable=False, default=utc_now)

    case = relationship("InspectionCase", back_populates="visual_anomalies")
    evidence = relationship("EvidenceItem", back_populates="visual_anomalies")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    field_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey("inspection_cases.inspection_id"), nullable=False, index=True)
    source_evidence_id = Column(String(36), ForeignKey("evidence_items.evidence_id"), nullable=True, index=True)
    field_name = Column(String(128), nullable=False, index=True)
    raw_value = Column(Text, nullable=True)
    normalized_value = Column(Text, nullable=True)
    unit = Column(String(32), nullable=True)
    confidence = Column(Float, nullable=True)
    applicability = Column(Enum(FieldApplicability), nullable=False, default=FieldApplicability.APPLICABLE)
    field_status = Column(Enum(FieldStatus), nullable=False, default=FieldStatus.EXTRACTED)
    bounding_box_json = Column(JSON, nullable=True)
    origin = Column(Enum(ExtractionOrigin), nullable=False, default=ExtractionOrigin.AI)
    status = Column(String(32), nullable=False, default="EXTRACTED")
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    case = relationship("InspectionCase", back_populates="extracted_fields")
    evidence = relationship("EvidenceItem", back_populates="extracted_fields")
    corrections = relationship("FieldCorrection", back_populates="field", cascade="all, delete-orphan")

class FieldCorrection(Base):
    __tablename__ = "field_corrections"

    correction_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    field_id = Column(String(36), ForeignKey("extracted_fields.field_id"), nullable=False, index=True)
    previous_value = Column(Text, nullable=True)
    corrected_value = Column(Text, nullable=False)
    officer_id = Column(String(64), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    field = relationship("ExtractedField", back_populates="corrections")

class RuleFinding(Base):
    __tablename__ = "rule_findings"

    finding_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey("inspection_cases.inspection_id"), nullable=False, index=True)
    rule_id = Column(String(64), nullable=False, index=True)
    rule_pack_version = Column(String(32), nullable=False)
    title = Column(String(255), nullable=False, default="")
    legal_citation = Column(String(255), nullable=False, default="")
    status = Column(Enum(FindingStatus), nullable=False, default=FindingStatus.REVIEW)
    severity = Column(Enum(FindingSeverity), nullable=False, default=FindingSeverity.MEDIUM)
    message = Column(Text, nullable=False)
    field_references_json = Column(JSON, nullable=True)
    evidence_references_json = Column(JSON, nullable=True)
    calculation_metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    case = relationship("InspectionCase", back_populates="rule_findings")


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    audit_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey("inspection_cases.inspection_id"), nullable=False, index=True)
    actor_id = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=utc_now)
    metadata_json = Column(JSON, nullable=True)
    previous_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False, index=True)

    case = relationship("InspectionCase", back_populates="audit_entries")

class GeneratedReport(Base):
    __tablename__ = "generated_reports"

    report_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey("inspection_cases.inspection_id"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    report_type = Column(String(64), nullable=False, default="INSPECTION_SUMMARY")
    file_reference = Column(String(512), nullable=True)
    sha256 = Column(String(64), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="NOT_GENERATED")
    generated_by = Column(String(64), nullable=False)
    generated_at = Column(DateTime, nullable=False, default=utc_now)


    case = relationship("InspectionCase", back_populates="reports")
