export type CaseStatus = 'DRAFT' | 'PROCESSING' | 'PENDING_REVIEW' | 'FINALISED';
export type OverallDetermination = 'PENDING_EVALUATION' | 'COMPLIANT' | 'NON_COMPLIANT' | 'REQUIRES_REVIEW';
export type EvidenceViewType = 'FRONT' | 'BACK' | 'SIDE' | 'BASE' | 'OTHER';
export type EvidenceProcessingStatus = 'UPLOADED' | 'QUALITY_CHECK' | 'PREPROCESSING' | 'OCR_PROCESSING' | 'OCR_COMPLETE' | 'OCR_FAILED' | 'MANUAL_REVIEW';
export type QualityVerdict = 'UNCHECKED' | 'PASS' | 'WARN' | 'FAIL' | 'MANUAL_REVIEW';
export type ExtractionOrigin = 'AI' | 'OFFICER' | 'SYSTEM';
export type FieldApplicability = 'APPLICABLE' | 'NOT_APPLICABLE' | 'UNKNOWN';
export type FieldStatus = 'EXTRACTED' | 'MISSING' | 'UNCERTAIN' | 'CONFLICTING' | 'CORRECTED' | 'NOT_APPLICABLE' | 'MANUAL_REVIEW';
export type FindingStatus = 'PASS' | 'FAIL' | 'REVIEW' | 'NOT_APPLICABLE';
export type FindingSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
export type UserRole = 'ADMIN' | 'OFFICER' | 'REVIEWER';

export interface UserProfile {
  user_id: string;
  username: string;
  role: UserRole;
  full_name: string;
  badge_number?: string;
}

export interface QualityReport {
  verdict: QualityVerdict;
  blur_score: number;
  brightness_score: number;
  contrast_score: number;
  is_readable: boolean;
  diagnostics: string[];
  evaluated_at: string;
}

export interface OCRBoundingBox {
  text: string;
  confidence: number;
  bbox: number[][]; // [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
  char_height_px?: number;
  evidence_id?: string;
}

export interface OCRResult {
  ocr_id: string;
  evidence_id: string;
  inspection_id: string;
  engine: string;
  preprocessing_variant: string;
  full_text: string;
  boxes_json: OCRBoundingBox[];
  average_confidence: number;
  processing_time_ms: number;
  created_at: string;
}

export interface FieldCorrection {
  correction_id: string;
  field_id: string;
  previous_value?: string;
  corrected_value: string;
  unit?: string;
  officer_id: string;
  reason?: string;
  created_at: string;
}

export interface ExtractedField {
  field_id: string;
  inspection_id: string;
  source_evidence_id?: string;
  field_name: string;
  raw_value?: string;
  normalized_value?: string;
  unit?: string;
  confidence?: number;
  applicability: FieldApplicability;
  field_status: FieldStatus;
  bounding_box_json?: any;
  origin: ExtractionOrigin;
  status: string;
  created_at: string;
  updated_at: string;
  corrections?: FieldCorrection[];
}

export interface RuleFinding {
  finding_id: string;
  inspection_id: string;
  rule_id: string;
  rule_pack_version: string;
  title: string;
  legal_citation: string;
  status: FindingStatus;
  severity: FindingSeverity;
  message: string;
  field_references_json?: any;
  evidence_references_json?: any;
  calculation_metadata_json?: any;
  created_at: string;
}

export interface CaseEvaluationSummary {
  inspection_id: string;
  overall_determination: OverallDetermination;
  total_rules_evaluated: number;
  pass_count: number;
  fail_count: number;
  review_count: number;
  not_applicable_count: number;
  rule_pack_version: string;
  evaluated_at: string;
  findings: RuleFinding[];
}



export interface EvidenceItem {
  evidence_id: string;
  inspection_id: string;
  original_filename: string;
  media_type: string;
  file_reference: string;
  sha256: string;
  view_type: EvidenceViewType;
  processing_status: EvidenceProcessingStatus;
  quality_verdict: QualityVerdict;
  quality_report_json?: QualityReport;
  preprocessed_references_json?: Record<string, string>;
  ingested_at: string;
  dimensions_json?: { width: number; height: number };
  metadata_json?: Record<string, unknown>;
  ocr_results?: OCRResult[];
}

export interface InspectionCase {
  inspection_id: string;
  case_number: string;
  officer_id: string;
  status: CaseStatus;
  overall_determination?: OverallDetermination;
  officer_decision?: string;
  officer_remarks?: string;
  rule_pack_version: string;
  created_at: string;
  updated_at: string;
  finalized_at?: string;
  notes?: string;
}

export interface GeneratedReport {
  report_id: string;
  inspection_id: string;
  version: number;
  report_type: string;
  file_reference?: string;
  sha256?: string;
  status: string;
  generated_by: string;
  generated_at: string;
}


export interface AuditEntry {
  audit_id: string;
  inspection_id: string;
  actor_id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  timestamp: string;
  metadata_json?: Record<string, unknown>;
  previous_hash: string;
  entry_hash: string;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  environment: string;
  database_connected: boolean;
  server_time: string;
}

export type CalibrationStatus = 'UNCALIBRATED' | 'CALIBRATED' | 'CALIBRATION_UNAVAILABLE' | 'AMBIGUOUS_CALIBRATION';

export interface CalibrationData {
  calibration_id: string;
  inspection_id: string;
  evidence_id: string;
  calibration_method: string;
  reference_object: string;
  reference_measurement_mm: number;
  detected_pixel_measurement?: number;
  mm_per_pixel?: number;
  confidence: number;
  bounding_geometry_json?: any;
  status: CalibrationStatus;
  created_at: string;
}


export interface VisualMeasurement {
  measurement_id: string;
  inspection_id: string;
  evidence_id: string;
  calibration_id?: string;
  measurement_type: string;
  target_text: string;
  character_type?: string;
  pdp_area_cm2?: number;
  pdp_area_source?: string;
  declaration_method?: string;
  source_bbox_json?: any;
  pixel_value: number;
  physical_value?: number;
  unit: string;
  confidence: number;
  status: string;
  method_version: string;
  created_at: string;
}



export interface VisualAnomaly {
  anomaly_id: string;
  inspection_id: string;
  evidence_id: string;
  anomaly_type: string;
  bounding_box_json?: any;
  confidence: number;
  metrics_json?: any;
  status: string;
  officer_review_required: string;
  created_at: string;
}

// Phase 6: Dashboard & Officer Review Types
export interface DashboardSummary {
  total_inspections: number;
  processing_count: number;
  pending_review_count: number;
  requires_review_count: number;
  compliant_count: number;
  non_compliant_count: number;
  finalised_count: number;
  reports_generated_count: number;
}

export interface DashboardReviewQueue {
  high_priority_count: number;
  standard_review_count: number;
  ready_for_finalisation_count: number;
}

export interface FindingRuleBreakdownItem {
  rule_id: string;
  rule_name: string;
  pass_count: number;
  fail_count: number;
  review_count: number;
  total_evaluated: number;
}

export interface DashboardFindingsBreakdown {
  total_findings: number;
  rules: FindingRuleBreakdownItem[];
}

export interface DashboardTrendItem {
  date: string;
  inspections_created: number;
  inspections_finalised: number;
}

export interface InspectionSummaryItem {
  inspection_id: string;
  case_number: string;
  officer_id: string;
  status: CaseStatus;
  overall_determination: OverallDetermination;
  created_at: string;
  updated_at: string;
  finalized_at?: string;
  evidence_count: number;
  findings_count: number;
  pass_count: number;
  fail_count: number;
  review_count: number;
  extraction_status: string;
  review_queue: string;
  has_report: boolean;
}

export interface InspectionListResponse {
  items: InspectionSummaryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface CaseReviewSummary {
  case: InspectionCase;
  evidence: EvidenceItem[];
  extracted_fields: ExtractedField[];
  rule_findings: RuleFinding[];
  measurements: VisualMeasurement[];
  anomalies: VisualAnomaly[];
  calibrations: CalibrationData[];
  reports: GeneratedReport[];
  audit_entries: AuditEntry[];
  audit_valid: boolean;
  review_queue: string;
}



