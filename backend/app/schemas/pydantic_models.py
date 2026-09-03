from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.domain import (
    CaseStatus,
    OverallDetermination,
    EvidenceViewType,
    EvidenceProcessingStatus,
    QualityVerdict,
    ExtractionOrigin,
    FieldApplicability,
    FieldStatus,
    FindingStatus,
    FindingSeverity,
    UserRole
)


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[UserRole] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class UserProfile(BaseModel):
    user_id: str
    username: str
    role: UserRole
    full_name: str
    badge_number: Optional[str] = None

# Case Schemas
class CaseCreate(BaseModel):
    case_number: Optional[str] = None
    notes: Optional[str] = None
    rule_pack_version: str = "v1.0.0"

class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inspection_id: str
    case_number: str
    officer_id: str
    status: CaseStatus
    overall_determination: OverallDetermination
    rule_pack_version: str
    created_at: datetime
    updated_at: datetime
    finalized_at: Optional[datetime] = None
    officer_decision: Optional[str] = None
    officer_remarks: Optional[str] = None
    notes: Optional[str] = None

class CaseStatusUpdate(BaseModel):
    status: CaseStatus
    notes: Optional[str] = None
    reason: Optional[str] = None


class CaseFinalizeRequest(BaseModel):
    officer_decision: OverallDetermination
    officer_remarks: Optional[str] = None
    acknowledged_review_findings: bool = False


# Quality Gate Schemas

class QualityReport(BaseModel):
    verdict: QualityVerdict
    blur_score: float
    brightness_score: float
    contrast_score: float
    is_readable: bool
    diagnostics: List[str] = Field(default_factory=list)
    evaluated_at: datetime

# OCR Schemas
class OCRBoundingBox(BaseModel):
    text: str
    confidence: float
    bbox: List[List[float]] # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    char_height_px: Optional[float] = None
    evidence_id: Optional[str] = None

class OCRResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ocr_id: str
    evidence_id: str
    inspection_id: str
    engine: str
    preprocessing_variant: str
    full_text: str
    boxes_json: List[Dict[str, Any]]
    average_confidence: float
    processing_time_ms: float
    created_at: datetime

# Evidence Schemas
class EvidenceCreate(BaseModel):
    original_filename: str
    media_type: str = "image/jpeg"
    view_type: EvidenceViewType = EvidenceViewType.FRONT

class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_id: str
    inspection_id: str
    original_filename: str
    media_type: str
    file_reference: str
    sha256: str
    view_type: EvidenceViewType
    processing_status: EvidenceProcessingStatus
    quality_verdict: QualityVerdict
    quality_report_json: Optional[Dict[str, Any]] = None
    preprocessed_references_json: Optional[Dict[str, Any]] = None
    ingested_at: datetime
    dimensions_json: Optional[Dict[str, Any]] = None
    metadata_json: Optional[Dict[str, Any]] = None
    ocr_results: List[OCRResultResponse] = Field(default_factory=list)


# Calibration Schemas
class CalibrationCreate(BaseModel):
    evidence_id: Optional[str] = None
    calibration_method: str = "PHYSICAL_REFERENCE"
    reference_object: Optional[str] = "INDIAN_5_RUPEE_COIN"
    reference_measurement_mm: Optional[float] = 23.0
    detected_pixel_measurement: Optional[float] = None
    mm_per_pixel: Optional[float] = None

class CalibrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    calibration_id: str
    inspection_id: str
    evidence_id: Optional[str] = None
    calibration_method: str
    reference_object: Optional[str] = None
    reference_measurement_mm: Optional[float] = None
    detected_pixel_measurement: Optional[float] = None
    mm_per_pixel: Optional[float] = None
    confidence: Optional[float] = None
    bounding_geometry_json: Optional[Any] = None
    status: str
    created_at: datetime

# Visual Measurement & Forensic Anomaly Schemas
class VisualMeasurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    measurement_id: str
    inspection_id: str
    evidence_id: str
    calibration_id: Optional[str] = None
    measurement_type: str
    target_text: Optional[str] = None
    character_type: str = "UNKNOWN"
    pdp_area_cm2: Optional[float] = None
    pdp_area_source: str = "UNKNOWN"
    declaration_method: str = "UNKNOWN"
    source_bbox_json: Optional[Any] = None
    pixel_value: float
    physical_value: Optional[float] = None
    unit: str
    confidence: float
    status: str
    method_version: str
    created_at: datetime



class VisualAnomalyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    anomaly_id: str
    inspection_id: str
    evidence_id: str
    anomaly_type: str
    bounding_box_json: Optional[Any] = None
    confidence: float
    metrics_json: Optional[Dict[str, Any]] = None
    status: str
    officer_review_required: str
    created_at: datetime


# Extracted Field & Provenance Schemas
class ExtractedFieldCreate(BaseModel):
    source_evidence_id: Optional[str] = None
    field_name: str
    raw_value: Optional[str] = None
    normalized_value: Optional[str] = None
    unit: Optional[str] = None
    confidence: Optional[float] = None
    applicability: FieldApplicability = FieldApplicability.APPLICABLE
    field_status: FieldStatus = FieldStatus.EXTRACTED
    bounding_box_json: Optional[Any] = None
    origin: ExtractionOrigin = ExtractionOrigin.AI

class FieldCorrectionCreate(BaseModel):
    corrected_value: str
    unit: Optional[str] = None
    reason: Optional[str] = "Officer manual review correction"

class FieldCorrectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    correction_id: str
    field_id: str
    previous_value: Optional[str] = None
    corrected_value: str
    unit: Optional[str] = None
    officer_id: str
    reason: Optional[str] = None
    created_at: datetime

class ExtractedFieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field_id: str
    inspection_id: str
    source_evidence_id: Optional[str] = None
    field_name: str
    raw_value: Optional[str] = None
    normalized_value: Optional[str] = None
    unit: Optional[str] = None
    confidence: Optional[float] = None
    applicability: FieldApplicability
    field_status: FieldStatus
    bounding_box_json: Optional[Any] = None
    origin: ExtractionOrigin
    status: str
    created_at: datetime
    updated_at: datetime
    corrections: List[FieldCorrectionResponse] = Field(default_factory=list)


# Rule Finding Schemas
class RuleFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    finding_id: str
    inspection_id: str
    rule_id: str
    rule_pack_version: str
    title: str
    legal_citation: str
    status: FindingStatus
    severity: FindingSeverity
    message: str
    field_references_json: Optional[Dict[str, Any]] = None
    evidence_references_json: Optional[Dict[str, Any]] = None
    calculation_metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

class CaseEvaluationSummary(BaseModel):
    inspection_id: str
    overall_determination: OverallDetermination
    total_rules_evaluated: int
    pass_count: int
    fail_count: int
    review_count: int
    not_applicable_count: int
    rule_pack_version: str
    evaluated_at: datetime
    findings: List[RuleFindingResponse] = Field(default_factory=list)

# Audit Schemas
class AuditEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_id: str
    inspection_id: str
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    timestamp: datetime
    metadata_json: Optional[Dict[str, Any]] = None
    previous_hash: str
    entry_hash: str

class AuditVerificationResponse(BaseModel):
    inspection_id: str
    is_valid: bool
    total_entries: int
    corrupted_sequence_index: Optional[int] = None
    message: str

# Report Metadata Schema
class ReportMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: str
    inspection_id: str
    version: int = 1
    report_type: str
    file_reference: Optional[str] = None
    sha256: Optional[str] = None
    status: str
    generated_by: str
    generated_at: datetime

class ReportVerificationResponse(BaseModel):
    report_id: str
    version: int
    exists: bool
    integrity_status: str # "VALID" | "INTEGRITY_MISMATCH" | "REPORT_NOT_FOUND"
    stored_hash: Optional[str] = None
    computed_hash: Optional[str] = None
    generated_at: Optional[datetime] = None
    finalized_at: Optional[datetime] = None
    case_number: Optional[str] = None
    overall_determination: Optional[str] = None
    officer_id: Optional[str] = None
    message: str


# Health Check Schema
class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    database_connected: bool
    server_time: datetime

# Phase 6: Dashboard & Officer Review Schemas
class DashboardSummaryResponse(BaseModel):
    total_inspections: int
    processing_count: int
    pending_review_count: int
    requires_review_count: int
    compliant_count: int
    non_compliant_count: int
    finalised_count: int
    reports_generated_count: int

class DashboardReviewQueueResponse(BaseModel):
    high_priority_count: int
    standard_review_count: int
    ready_for_finalisation_count: int

class FindingRuleBreakdownItem(BaseModel):
    rule_id: str
    rule_name: str
    pass_count: int
    fail_count: int
    review_count: int
    total_evaluated: int

class DashboardFindingsBreakdown(BaseModel):
    total_findings: int
    rules: List[FindingRuleBreakdownItem]

class DashboardTrendItem(BaseModel):
    date: str
    inspections_created: int
    inspections_finalised: int

class InspectionSummaryItemResponse(BaseModel):
    inspection_id: str
    case_number: str
    officer_id: str
    status: CaseStatus
    overall_determination: OverallDetermination
    created_at: datetime
    updated_at: datetime
    finalized_at: Optional[datetime] = None
    evidence_count: int = 0
    findings_count: int = 0
    pass_count: int = 0
    fail_count: int = 0
    review_count: int = 0
    extraction_status: str = "EMPTY"
    review_queue: str = "PROCESSING"
    has_report: bool = False

class InspectionListResponse(BaseModel):
    items: List[InspectionSummaryItemResponse]
    total: int
    limit: int
    offset: int

class CaseReviewSummaryResponse(BaseModel):
    case: CaseResponse
    evidence: List[EvidenceResponse] = Field(default_factory=list)
    extracted_fields: List[ExtractedFieldResponse] = Field(default_factory=list)
    rule_findings: List[RuleFindingResponse] = Field(default_factory=list)
    measurements: List[VisualMeasurementResponse] = Field(default_factory=list)
    anomalies: List[VisualAnomalyResponse] = Field(default_factory=list)
    calibrations: List[CalibrationResponse] = Field(default_factory=list)
    reports: List[ReportMetadataResponse] = Field(default_factory=list)
    audit_entries: List[AuditEntryResponse] = Field(default_factory=list)
    audit_valid: bool = True
    review_queue: str = "PROCESSING"

