'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  FileText,
  Camera,
  Layers,
  Sparkles,
  Edit3,
  RefreshCw,
  Download,
  ExternalLink,
  ChevronRight,
  UserCheck,
  CheckSquare,
  Scale,
  Eye,
  History,
  FileCheck,
  ArrowLeft,
  Crosshair,
  Upload,
  FolderOpen,
  ArrowRight,
  Zap,
  X
} from 'lucide-react';
import { Badge } from '../../../components/ui/Badge';
import { Card } from '../../../components/ui/Card';
import { CameraCaptureModal } from '../../../components/evidence/CameraCaptureModal';
import { InspectionCopilot } from '../../../components/workbench/InspectionCopilot';
import {
  CaseReviewSummary,
  ExtractedField,
  RuleFinding,
  EvidenceItem,
  GeneratedReport,
  AuditEntry,
  VisualMeasurement,
  VisualAnomaly,
  CalibrationData,
  EvidenceViewType
} from '../../../types';
import {
  fetchCaseReviewSummary,
  correctFieldValue,
  rerunCaseCompliance,
  finalizeCase,
  generateInspectionReport,
  uploadEvidence,
  processEvidenceOCR,
  extractCaseFields,
  evaluateCaseCompliance,
  downloadReportPdf
} from '../../../lib/api';
import { formatDateTime } from '../../../lib/utils';
import { useAuth } from '../../../hooks/useAuth';

type ActiveTab =
  | 'overview'
  | 'evidence'
  | 'declarations'
  | 'findings'
  | 'measurements'
  | 'forensics'
  | 'reports'
  | 'audit';

export default function CaseDetailPage() {
  const params = useParams();
  const inspectionId = params.id as string;

  const [data, setData] = useState<CaseReviewSummary | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  // Field Correction Modal State
  const [selectedField, setSelectedField] = useState<ExtractedField | null>(null);
  const [correctedValue, setCorrectedValue] = useState('');
  const [correctionReason, setCorrectionReason] = useState('');
  const [showCorrectionModal, setShowCorrectionModal] = useState(false);

  // Camera Quick Capture Modal State
  const [showCameraModal, setShowCameraModal] = useState(false);
  const [cameraViewType, setCameraViewType] = useState<EvidenceViewType>('FRONT');

  // "Show Me Where" Evidence Inspection Modal State
  const [highlightEvidence, setHighlightEvidence] = useState<{
    evidence: EvidenceItem;
    title: string;
    bbox?: number[][];
    description?: string;
  } | null>(null);

  // Finalisation Modal State
  const [showFinalizeModal, setShowFinalizeModal] = useState(false);
  const [officerDecision, setOfficerDecision] = useState<'COMPLIANT' | 'NON_COMPLIANT' | 'REQUIRES_REVIEW'>('COMPLIANT');
  const [officerRemarks, setOfficerRemarks] = useState('');
  const [acknowledgeReviewFindings, setAcknowledgeReviewFindings] = useState(false);

  // File Upload Ref
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [pipelineMessage, setPipelineMessage] = useState<string>('');

  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  const loadCaseData = async () => {
    if (!isAuthenticated) return;
    try {
      setLoading(true);
      const res = await fetchCaseReviewSummary(inspectionId);
      setData(res);
      if (res.case?.overall_determination && res.case.overall_determination !== 'PENDING_EVALUATION') {
        setOfficerDecision(res.case.overall_determination as any);
      }
    } catch (err) {
      console.error('Failed to load case data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (inspectionId && isAuthenticated) {
      loadCaseData();
    }
  }, [inspectionId, isAuthenticated]);

  const handleDirectFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;
    const selected = e.target.files[0];
    try {
      setActionLoading(true);
      setPipelineMessage(`Uploading ${cameraViewType} evidence...`);
      await uploadEvidence(inspectionId, selected, cameraViewType);
      await loadCaseData();
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Upload failed';
      alert(message);
    } finally {
      setActionLoading(false);
      setPipelineMessage('');
    }
  };

  const handleRunFullPerception = async () => {
    if (!data?.evidence.length) return;
    if (data?.case.status === 'FINALISED') {
      alert('This inspection case is finalised and sealed. Mutations are disabled.');
      return;
    }
    try {
      setActionLoading(true);
      setPipelineMessage('Running OCR perception across evidence views...');
      for (const ev of data.evidence) {
        if (ev.processing_status !== 'OCR_COMPLETE') {
          await processEvidenceOCR(ev.evidence_id);
        }
      }

      setPipelineMessage('Extracting structured declarations...');
      await extractCaseFields(inspectionId);
      setPipelineMessage('Evaluating deterministic compliance rules...');
      await evaluateCaseCompliance(inspectionId);
      await loadCaseData();
      setActiveTab('findings');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Processing failed';
      alert(message);
    } finally {
      setActionLoading(false);
      setPipelineMessage('');
    }
  };

  const handleDownloadReport = async () => {
    try {
      setActionLoading(true);
      await downloadReportPdf(inspectionId);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Report download failed';
      alert(message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCorrectField = async () => {
    if (!selectedField) return;
    try {
      setActionLoading(true);
      await correctFieldValue(inspectionId, selectedField.field_id, {
        corrected_value: correctedValue,
        reason: correctionReason || 'Officer manual correction during statutory review'
      });
      // Automatically rerun rule evaluation after correction
      await rerunCaseCompliance(inspectionId);
      setShowCorrectionModal(false);
      setSelectedField(null);
      setCorrectedValue('');
      setCorrectionReason('');
      await loadCaseData();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Correction failed';
      alert(message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCameraCaptureAccepted = async (capturedFile: File) => {
    try {
      setActionLoading(true);
      setShowCameraModal(false);
      await uploadEvidence(inspectionId, capturedFile, cameraViewType);
      await loadCaseData();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Camera upload failed';
      alert(message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRerunEvaluation = async () => {
    try {
      setActionLoading(true);
      await rerunCaseCompliance(inspectionId);
      await loadCaseData();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Evaluation failed';
      alert(message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setActionLoading(true);
      await generateInspectionReport(inspectionId, true);
      await loadCaseData();
      setActiveTab('reports');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Report generation failed';
      alert(message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleFinalizeSubmit = async () => {
    try {
      setActionLoading(true);
      await finalizeCase(inspectionId, {
        officer_decision: officerDecision,
        officer_remarks: officerRemarks,
        acknowledged_review_findings: acknowledgeReviewFindings
      });
      setShowFinalizeModal(false);
      await loadCaseData();
      setActiveTab('reports');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Finalisation failed';
      alert(message);
    } finally {
      setActionLoading(false);
    }
  };

  // "Show Me Where" helper to locate source evidence and open inspection modal
  const handleShowMeWhere = (field: ExtractedField | RuleFinding) => {
    let targetEvidenceId: string | undefined;
    let title = '';
    let description = '';
    let bbox: number[][] | undefined;

    if ('field_name' in field) {
      targetEvidenceId = field.source_evidence_id;
      title = `Statutory Field: ${field.field_name}`;
      description = `Declared value: "${field.raw_value || field.normalized_value}" (Origin: ${field.origin})`;
      if (field.bounding_box_json && Array.isArray(field.bounding_box_json)) {
        bbox = field.bounding_box_json;
      }
    } else if ('rule_id' in field) {
      title = `${field.title} (${field.rule_id})`;
      description = field.message;
      if (field.evidence_references_json && Array.isArray(field.evidence_references_json) && field.evidence_references_json.length > 0) {
        targetEvidenceId = field.evidence_references_json[0];
      }
    }

    const matchedEvidence = data?.evidence.find((e) => e.evidence_id === targetEvidenceId) || data?.evidence[0];
    if (matchedEvidence) {
      setHighlightEvidence({
        evidence: matchedEvidence,
        title,
        description,
        bbox
      });
    }
  };

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-2">
          <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
          <div className="text-xs font-semibold text-slate-600">Loading Case Inspection Workbench...</div>
        </div>
      </div>
    );
  }

  const { case: caseObj, evidence, extracted_fields, rule_findings, measurements, anomalies, calibrations, reports, audit_entries, audit_valid, review_queue } = data;
  const isFinalised = caseObj.status === 'FINALISED';
  const hasReviewFindings = rule_findings.some((f) => f.status === 'REVIEW');

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-20 sm:pb-12 px-3 sm:px-4 md:px-8">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center space-x-2 text-xs text-slate-500">
        <Link href="/inspections" className="hover:text-blue-700 flex items-center space-x-1">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span className="hidden xs:inline">Back to Officer Review Console</span>
          <span className="xs:hidden">Back</span>
        </Link>
        <span className="text-slate-300">/</span>
        <span className="font-semibold text-slate-800 break-all">{caseObj.case_number}</span>
      </div>

      {/* Case Header Banner */}
      <div className="bg-white rounded-gov border border-slate-200 p-4 sm:p-6 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                Inspection Case
              </span>
              <span className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium">
                {caseObj.rule_pack_version}
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-nirikshan-navy tracking-tight mt-0.5 break-all">
              {caseObj.case_number}
            </h1>
            <div className="flex flex-wrap items-center gap-2 sm:gap-3 mt-2 text-xs text-slate-600">
              <div>
                <span className="text-slate-400">Created:</span>{' '}
                <span className="font-semibold">{formatDateTime(caseObj.created_at)}</span>
              </div>
              <span className="text-slate-300">•</span>
              <div>
                <span className="text-slate-400">Officer:</span>{' '}
                <span className="font-medium text-slate-800">{caseObj.officer_id}</span>
              </div>
              <span className="text-slate-300">•</span>
              <div className="flex items-center space-x-1.5">
                <span className="text-slate-400">Audit Chain:</span>
                {audit_valid ? (
                  <span className="text-emerald-700 font-semibold inline-flex items-center gap-0.5">
                    <ShieldCheck className="w-3.5 h-3.5" /> Verified
                  </span>
                ) : (
                  <span className="text-rose-700 font-semibold inline-flex items-center gap-0.5">
                    <AlertTriangle className="w-3.5 h-3.5" /> Broken
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <div className="flex flex-col items-start sm:items-end gap-1">
              <div className="text-[10px] uppercase font-bold text-slate-400">Statutory Determination</div>
              <Badge status={caseObj.overall_determination || 'PENDING_EVALUATION'} />
            </div>
            <div className="flex flex-col items-start sm:items-end gap-1">
              <div className="text-[10px] uppercase font-bold text-slate-400">Workflow State</div>
              <Badge status={caseObj.status} />
            </div>
          </div>
        </div>

        {/* Action Bar */}
        <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => {
                setCameraViewType('FRONT');
                setShowCameraModal(true);
              }}
              disabled={isFinalised || actionLoading}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-nirikshan-saffron hover:bg-nirikshan-saffron/90 text-white rounded-brand text-xs font-bold transition-all shadow-xs disabled:opacity-50"
            >
              <Camera className="w-4 h-4" />
              <span>Capture Photo (Camera)</span>
            </button>

            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isFinalised || actionLoading}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300 rounded-brand text-xs font-semibold transition-colors disabled:opacity-50"
            >
              <Upload className="w-4 h-4 text-blue-700" />
              <span>Upload Packaging File</span>
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/bmp"
              onChange={handleDirectFileUpload}
              className="hidden"
            />

            <Link
              href={`/cases/${caseObj.inspection_id}/evidence`}
              className="inline-flex items-center space-x-1.5 px-3 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-brand text-xs font-semibold transition-colors"
            >
              <Layers className="w-3.5 h-3.5 text-slate-500" />
              <span>Multi-View Workbench</span>
            </Link>

            {extracted_fields.length > 0 && (
              <button
                onClick={handleRerunEvaluation}
                disabled={actionLoading || isFinalised}
                className="inline-flex items-center space-x-1.5 px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-900 border border-blue-200 rounded-brand text-xs font-semibold transition-colors disabled:opacity-40"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${actionLoading ? 'animate-spin' : ''}`} />
                <span>Re-evaluate Rules</span>
              </button>
            )}

            {isFinalised && (
              <button
                onClick={handleDownloadReport}
                disabled={actionLoading}
                className="inline-flex items-center space-x-1.5 px-3 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-900 border border-emerald-300 rounded-brand text-xs font-semibold transition-colors shadow-xs"
              >
                <Download className="w-3.5 h-3.5 text-emerald-700" />
                <span>Download PDF Report</span>
              </button>
            )}
          </div>

          <div>
            {!isFinalised ? (
              <button
                onClick={() => setShowFinalizeModal(true)}
                disabled={rule_findings.length === 0}
                className={`inline-flex items-center space-x-1.5 px-4 py-2 text-white rounded-brand text-xs font-bold transition-all shadow-xs ${
                  rule_findings.length > 0 ? 'bg-blue-600 hover:bg-blue-500' : 'bg-slate-400 cursor-not-allowed'
                }`}
                title={rule_findings.length === 0 ? 'Evaluate statutory rules first before finalising' : 'Finalise case'}
              >
                <UserCheck className="w-4 h-4" />
                <span>Finalise Case &amp; Sign Order</span>
              </button>
            ) : (
              <div className="inline-flex items-center space-x-1 px-3 py-1.5 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-brand text-xs font-bold">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Case Finalised &amp; Sealed</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* DYNAMIC NEXT-STEP WORKFLOW GUIDANCE BANNER */}
      <div className="bg-linear-to-r from-nirikshan-navy to-slate-800 text-white rounded-brand p-5 shadow-sm border border-slate-700">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2 text-xs font-bold text-nirikshan-saffron">
              <Sparkles className="w-3.5 h-3.5" />
              <span>
                {isFinalised
                  ? 'WORKFLOW STEP 5: FINAL DETERMINATION SEALED & CERTIFIED'
                  : evidence.length === 0
                  ? 'WORKFLOW STEP 1: CAPTURE PACKAGING EVIDENCE'
                  : extracted_fields.length === 0
                  ? 'WORKFLOW STEP 2: RUN OCR & FIELD EXTRACTION'
                  : rule_findings.length === 0
                  ? 'WORKFLOW STEP 3: EVALUATE STATUTORY RULES'
                  : 'WORKFLOW STEP 4: OFFICER REVIEW & SIGN-OFF'}
              </span>
            </div>
            <h3 className="text-base font-bold text-white">
              {isFinalised
                ? 'Inspection Case Finalised & Legally Sealed'
                : evidence.length === 0
                ? 'No Packaging Evidence Uploaded Yet'
                : extracted_fields.length === 0
                ? `${evidence.length} Evidence View(s) Ready — Run Perception Pipeline`
                : rule_findings.length === 0
                ? `${extracted_fields.length} Declarations Extracted — Ready for Compliance Check`
                : `${rule_findings.length} Compliance Findings Evaluated — Ready for Sign-Off`}
            </h3>
            <p className="text-xs text-slate-300 max-w-2xl">
              {pipelineMessage
                ? pipelineMessage
                : isFinalised
                ? 'Official 3-part PDF inspection report with cryptographic SHA-256 digest and QR verification is available.'
                : evidence.length === 0
                ? 'Photograph or upload packaging panels (Front, Back, Side, or Base). In-app camera and file upload are both supported.'
                : extracted_fields.length === 0
                ? 'Execute PaddleOCR bounding box extraction and structure mandatory Rule 6 declarations with source provenance.'
                : rule_findings.length === 0
                ? 'Run deterministic rule engine to verify Rule 6 mandatory declarations, Unit Sale Price math, and Rule 7 font sizing.'
                : 'Review extracted fields and findings. Make officer manual corrections if required, then sign your final determination.'}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0">
            {isFinalised ? (
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleDownloadReport}
                  disabled={actionLoading}
                  className="inline-flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold px-5 py-2.5 rounded-brand transition-all shadow-xs"
                >
                  <Download className="w-4 h-4" />
                  <span>Download PDF Report</span>
                </button>
                {reports && reports.length > 0 && (
                  <Link
                    href={`/verify/${reports[0].report_id}`}
                    target="_blank"
                    className="inline-flex items-center space-x-1.5 bg-white/10 hover:bg-white/20 text-white border border-white/20 text-xs font-semibold px-4 py-2.5 rounded-brand transition-colors"
                  >
                    <ExternalLink className="w-4 h-4 text-blue-300" />
                    <span>Verify QR Portal</span>
                  </Link>
                )}
              </div>
            ) : evidence.length === 0 ? (
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => {
                    setCameraViewType('FRONT');
                    setShowCameraModal(true);
                  }}
                  className="inline-flex items-center space-x-1.5 bg-nirikshan-saffron hover:bg-nirikshan-saffron/90 text-white text-xs font-bold px-4 py-2.5 rounded-brand transition-all shadow-xs"
                >
                  <Camera className="w-4 h-4" />
                  <span>Take Photo</span>
                </button>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="inline-flex items-center space-x-1.5 bg-white/10 hover:bg-white/20 text-white border border-white/20 text-xs font-semibold px-4 py-2.5 rounded-brand transition-colors"
                >
                  <Upload className="w-4 h-4 text-blue-300" />
                  <span>Upload File</span>
                </button>
              </div>
            ) : extracted_fields.length === 0 ? (
              <button
                onClick={handleRunFullPerception}
                disabled={actionLoading}
                className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-5 py-2.5 rounded-brand transition-all shadow-xs disabled:opacity-50"
              >
                {actionLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4 text-amber-300" />}
                <span>Run OCR &amp; Extract Declarations</span>
              </button>
            ) : rule_findings.length === 0 ? (
              <button
                onClick={handleRerunEvaluation}
                disabled={actionLoading}
                className="inline-flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold px-5 py-2.5 rounded-brand transition-all shadow-xs disabled:opacity-50"
              >
                {actionLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Scale className="w-4 h-4" />}
                <span>Evaluate Statutory Rules</span>
              </button>
            ) : (
              <button
                onClick={() => setShowFinalizeModal(true)}
                className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-5 py-2.5 rounded-brand transition-all shadow-xs"
              >
                <UserCheck className="w-4 h-4 text-emerald-300" />
                <span>Finalise Case &amp; Sign Order</span>
              </button>
            )}
          </div>
        </div>
      </div>



      {/* Workbench Navigation Tabs */}
      <div className="flex border-b border-slate-200 bg-white px-2 rounded-t-gov overflow-x-auto shadow-2xs">
        {[
          { id: 'overview', label: 'Overview & Copilot' },
          { id: 'evidence', label: `Evidence (${evidence.length})` },
          { id: 'declarations', label: `Declarations & Corrections (${extracted_fields.length})` },
          { id: 'findings', label: `Rule Findings (${rule_findings.length})` },
          { id: 'measurements', label: `Rule 7 Font Sizing (${measurements.length})` },
          { id: 'forensics', label: `Visual Forensics (${anomalies.length})` },
          { id: 'reports', label: `Reports (${reports.length})` },
          { id: 'audit', label: `Audit Trail (${audit_entries.length})` },
        ].map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as ActiveTab)}
              className={`px-4 py-3 text-xs font-semibold border-b-2 whitespace-nowrap transition-colors ${
                isActive
                  ? 'border-blue-700 text-blue-900 bg-blue-50/40'
                  : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content Containers */}
      <div className="bg-white rounded-b-gov border-x border-b border-slate-200 p-6 shadow-xs">
        {/* TAB 1: OVERVIEW & INSPECTION COPILOT */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide border-b pb-2">
                  Sample &amp; Intake Information
                </h3>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Case Number:</span>
                    <span className="font-semibold text-slate-900">{caseObj.case_number}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Inspection ID:</span>
                    <span className="font-medium text-slate-700">{caseObj.inspection_id}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Assigned Officer:</span>
                    <span className="font-medium text-slate-900">{caseObj.officer_id}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Statutory Rule Pack:</span>
                    <span className="font-medium text-blue-700">{caseObj.rule_pack_version}</span>
                  </div>
                  <div className="py-1">
                    <span className="text-slate-500 block mb-1">Notes / Sample Description:</span>
                    <div className="p-2.5 bg-slate-50 rounded border border-slate-200 text-slate-800">
                      {caseObj.notes || 'No description notes recorded.'}
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide border-b pb-2">
                  Determination &amp; Officer Record
                </h3>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Current Determination:</span>
                    <Badge status={caseObj.overall_determination || 'PENDING_EVALUATION'} />
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Officer Decision:</span>
                    <span className="font-semibold text-slate-900">{caseObj.officer_decision || 'Pending Officer Decision'}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Finalised Date:</span>
                    <span className="font-semibold text-slate-900">
                      {caseObj.finalized_at ? formatDateTime(caseObj.finalized_at) : 'Not Yet Finalised'}
                    </span>
                  </div>
                  <div className="py-1">
                    <span className="text-slate-500 block mb-1">Officer Authoritative Remarks:</span>
                    <div className="p-2.5 bg-slate-50 rounded border border-slate-200 text-slate-800">
                      {caseObj.officer_remarks || 'No remarks entered.'}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Field Inspection Copilot Widget */}
            <div>
              <InspectionCopilot
                caseObj={caseObj}
                evidence={evidence}
                fields={extracted_fields}
                findings={rule_findings}
              />
            </div>
          </div>
        )}

        {/* TAB 2: EVIDENCE */}
        {activeTab === 'evidence' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b">
              <h3 className="text-sm font-bold text-slate-900 uppercase">
                Uploaded Evidence Gallery ({evidence.length} Views)
              </h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => {
                    setCameraViewType('FRONT');
                    setShowCameraModal(true);
                  }}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold inline-flex items-center gap-1 shadow-xs"
                >
                  <Camera className="w-3.5 h-3.5" />
                  <span>Take Photo</span>
                </button>
                <Link
                  href={`/cases/${caseObj.inspection_id}/evidence`}
                  className="text-xs text-blue-700 font-semibold hover:underline flex items-center gap-1"
                >
                  <span>Open Multi-View Ingestion Workbench</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            {evidence.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {evidence.map((ev) => (
                  <div key={ev.evidence_id} className="border border-slate-200 rounded-gov p-3 space-y-2 bg-slate-50/50">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-slate-900">{ev.view_type} View</span>
                      <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-blue-100 text-blue-800">
                        {ev.processing_status}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-500">
                      <div>File: <span className="font-medium text-slate-700">{ev.original_filename}</span></div>
                      <div className="truncate">SHA-256: <span className="font-mono text-[10px] text-slate-400">{ev.sha256}</span></div>
                    </div>
                    {ev.quality_report_json && (
                      <div className="p-2 bg-white rounded border border-slate-200 text-[11px] space-y-1">
                        <div className="flex justify-between">
                          <span className="text-slate-500">Quality Verdict:</span>
                          <span className="font-bold text-slate-800">{ev.quality_report_json.verdict}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Blur Score:</span>
                          <span className="font-semibold text-slate-700">{ev.quality_report_json.blur_score?.toFixed(1)}</span>
                        </div>
                      </div>
                    )}
                    <div className="pt-1 flex justify-end">
                      <button
                        onClick={() => {
                          setHighlightEvidence({
                            evidence: ev,
                            title: `${ev.view_type} Evidence Panel`,
                            description: `File: ${ev.original_filename} | SHA-256: ${ev.sha256.slice(0, 16)}...`
                          });
                        }}
                        className="text-xs text-blue-700 hover:underline font-semibold inline-flex items-center gap-1"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect Image</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-12 text-center text-slate-400">
                <Camera className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                <div>No evidence views uploaded yet. Click &quot;Take Photo&quot; to begin field capture.</div>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: DECLARATIONS & CORRECTIONS */}
        {activeTab === 'declarations' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b">
              <div>
                <h3 className="text-sm font-bold text-slate-900 uppercase">
                  Statutory Declarations &amp; Officer Correction Audit
                </h3>
                <p className="text-xs text-slate-500">
                  Strict separation of automated system extraction vs officer manual corrections. Click &quot;Show Where&quot; to inspect OCR location.
                </p>
              </div>
            </div>

            {extracted_fields.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                      <th className="p-3">Statutory Field</th>
                      <th className="p-3">System Extraction (Raw)</th>
                      <th className="p-3">Current / Normalized Value</th>
                      <th className="p-3">Origin</th>
                      <th className="p-3">Correction History</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {extracted_fields.map((f) => {
                      const hasCorrections = (f.corrections && f.corrections.length > 0);
                      return (
                        <tr key={f.field_id} className="hover:bg-slate-50/70">
                          <td className="p-3 font-semibold text-slate-900">
                            {f.field_name}
                          </td>
                          <td className="p-3 text-slate-600">
                            {f.raw_value || <span className="text-slate-400 italic">None</span>}
                          </td>
                          <td className="p-3">
                            <span className="font-bold text-slate-900">
                              {f.normalized_value || f.raw_value || '—'}
                            </span>
                            {f.unit && <span className="ml-1 text-slate-500 text-[11px]">{f.unit}</span>}
                          </td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                f.origin === 'OFFICER'
                                  ? 'bg-amber-100 text-amber-900 border border-amber-200'
                                  : 'bg-blue-50 text-blue-800'
                              }`}
                            >
                              {f.origin}
                            </span>
                          </td>
                          <td className="p-3">
                            {hasCorrections ? (
                              <div className="space-y-1 text-[11px]">
                                {f.corrections!.map((c) => (
                                  <div key={c.correction_id} className="p-1.5 bg-amber-50 rounded border border-amber-200 text-amber-950">
                                    <div><span className="font-semibold">Corrected to:</span> {c.corrected_value}</div>
                                    <div className="text-[10px] text-amber-800">Reason: {c.reason}</div>
                                    <div className="text-[10px] text-slate-500">By {c.officer_id} at {formatDateTime(c.created_at)}</div>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <span className="text-slate-400">Original value unchanged</span>
                            )}
                          </td>
                          <td className="p-3 text-right">
                            <div className="flex items-center justify-end space-x-2">
                              {f.source_evidence_id && (
                                <button
                                  onClick={() => handleShowMeWhere(f)}
                                  className="inline-flex items-center space-x-1 px-2.5 py-1 bg-blue-50 hover:bg-blue-100 text-blue-900 border border-blue-200 rounded font-semibold text-xs transition-colors"
                                  title="Locate extracted text in source evidence"
                                >
                                  <Crosshair className="w-3 h-3 text-blue-700" />
                                  <span>Show Where</span>
                                </button>
                              )}
                              <button
                                onClick={() => {
                                  setSelectedField(f);
                                  setCorrectedValue(f.normalized_value || f.raw_value || '');
                                  setCorrectionReason('');
                                  setShowCorrectionModal(true);
                                }}
                                disabled={isFinalised}
                                className="inline-flex items-center space-x-1 px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded font-semibold text-xs transition-colors disabled:opacity-40"
                              >
                                <Edit3 className="w-3 h-3 text-slate-600" />
                                <span>Correct</span>
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-12 text-center text-slate-400">
                <FileText className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                <div>No structured fields extracted yet. Run OCR extraction in the Evidence Workbench.</div>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: RULE FINDINGS */}
        {activeTab === 'findings' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b">
              <div>
                <h3 className="text-sm font-bold text-slate-900 uppercase">
                  Deterministic Statutory Findings (PC Rules, 2011)
                </h3>
                <p className="text-xs text-slate-500">
                  Rule evaluation results derived strictly from normalized declarations and verified physical measurements.
                </p>
              </div>
            </div>

            {rule_findings.length > 0 ? (
              <div className="space-y-3">
                {rule_findings.map((f) => (
                  <div key={f.finding_id} className="p-4 rounded-gov border border-slate-200 bg-slate-50/50 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-xs text-slate-900">{f.rule_id}</span>
                          <span className="text-xs text-slate-500 font-serif italic">({f.legal_citation})</span>
                        </div>
                        <h4 className="text-sm font-bold text-slate-900 mt-0.5">{f.title}</h4>
                      </div>
                      <Badge status={f.status} />
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed">{f.message}</p>
                    
                    <div className="flex items-center justify-between pt-1">
                      {f.calculation_metadata_json ? (
                        <div className="p-1.5 bg-white rounded border border-slate-200 text-[10px] mono-code text-slate-600 max-w-xl truncate">
                          {JSON.stringify(f.calculation_metadata_json)}
                        </div>
                      ) : <div />}
                      
                      <button
                        onClick={() => handleShowMeWhere(f)}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 rounded font-semibold text-xs transition-colors"
                      >
                        <Crosshair className="w-3 h-3 text-slate-600" />
                        <span>Inspect Evidence Source</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-12 text-center text-slate-400">
                <CheckSquare className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                <div>No rule evaluation findings recorded. Click &quot;Re-evaluate Rules&quot; to execute engine.</div>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: MEASUREMENTS & CALIBRATION (RULE 7) */}
        {activeTab === 'measurements' && (
          <div className="space-y-6">
            <div className="pb-2 border-b">
              <h3 className="text-sm font-bold text-slate-900 uppercase">
                Physical Calibration &amp; Rule 7 Font Compliance
              </h3>
              <p className="text-xs text-slate-500">
                Font heights verified under Rule 7 using Principal Display Panel (PDP) area, character type, and declaration method.
              </p>
            </div>

            {/* Coin Calibration */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-700 uppercase">Physical Reference Calibration</h4>
              {calibrations.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {calibrations.map((c) => (
                    <div key={c.calibration_id} className="p-3 bg-slate-50 rounded border border-slate-200 text-xs space-y-1">
                      <div className="flex justify-between font-semibold">
                        <span>Reference: {c.reference_object}</span>
                        <span className="text-emerald-700">{c.status}</span>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>Physical Dimension:</span>
                        <span className="font-mono">{c.reference_measurement_mm} mm</span>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>Scale Factor:</span>
                        <span className="font-mono text-blue-700 font-bold">{c.mm_per_pixel?.toFixed(4)} mm/px</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 bg-slate-50 rounded border text-xs text-slate-500 text-center">
                  No coin calibration records found for this case.
                </div>
              )}
            </div>

            {/* Visual Font Measurements */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-700 uppercase">Principal Display Panel Font Measurements</h4>
              {measurements.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                        <th className="p-2.5">Target Declaration</th>
                        <th className="p-2.5">Character Type</th>
                        <th className="p-2.5">PDP Area (cm²)</th>
                        <th className="p-2.5">Pixel Height</th>
                        <th className="p-2.5">Physical Height (mm)</th>
                        <th className="p-2.5">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {measurements.map((m) => (
                        <tr key={m.measurement_id} className="hover:bg-slate-50">
                          <td className="p-2.5 font-semibold text-slate-900">{m.target_text || 'Declared Quantity'}</td>
                          <td className="p-2.5 font-medium text-slate-700">{m.character_type || 'NUMERAL'}</td>
                          <td className="p-2.5 font-medium text-slate-700">{m.pdp_area_cm2 ? `${m.pdp_area_cm2} cm²` : 'Unspecified'}</td>
                          <td className="p-2.5 font-medium text-slate-700">{m.pixel_value.toFixed(1)} px</td>
                          <td className="p-2.5 font-bold text-blue-900">
                            {m.physical_value ? `${m.physical_value.toFixed(2)} mm` : 'Uncalibrated'}
                          </td>
                          <td className="p-2.5">
                            <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-100 text-emerald-800">
                              {m.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-4 bg-slate-50 rounded border text-xs text-slate-500 text-center">
                  No visual font measurements computed yet.
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 6: VISUAL FORENSICS */}
        {activeTab === 'forensics' && (
          <div className="space-y-4">
            <div className="pb-2 border-b">
              <h3 className="text-sm font-bold text-slate-900 uppercase">
                Visual Forensics &amp; Tampering Anomaly Signals
              </h3>
              <p className="text-xs text-slate-500">
                OpenCV multi-spectral and edge-density analysis for suspected price stickers and overlays.
              </p>
            </div>

            {anomalies.length > 0 ? (
              <div className="space-y-3">
                {anomalies.map((a) => (
                  <div key={a.anomaly_id} className="p-4 bg-amber-50/50 rounded-gov border border-amber-200 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <AlertTriangle className="w-4 h-4 text-amber-600" />
                        <span className="font-bold text-xs text-amber-950">{a.anomaly_type}</span>
                      </div>
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-amber-200 text-amber-900">
                        Officer Review Required: {a.officer_review_required}
                      </span>
                    </div>
                    <div className="text-xs text-amber-900">
                      Confidence: <span className="font-mono font-bold">{(a.confidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-12 text-center text-slate-400">
                <ShieldCheck className="w-8 h-8 mx-auto mb-2 text-emerald-500" />
                <div className="font-semibold text-slate-700">No Tampering or Sticker Overlays Detected</div>
                <p className="text-xs text-slate-400 mt-0.5">Visual surfaces appear clean and unaltered.</p>
              </div>
            )}
          </div>
        )}

        {/* TAB 7: REPORTS */}
        {activeTab === 'reports' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b">
              <div>
                <h3 className="text-sm font-bold text-slate-900 uppercase">
                  Generated Forensic Inspection Certificates
                </h3>
                <p className="text-xs text-slate-500">
                  Cryptographically hashed 3-part legal inspection summary documents.
                </p>
              </div>
              <button
                onClick={handleGenerateReport}
                disabled={actionLoading}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold"
              >
                Generate New Report Version
              </button>
            </div>

            {reports.length > 0 ? (
              <div className="space-y-3">
                {reports.map((r) => (
                  <div key={r.report_id} className="p-4 bg-slate-50 rounded-gov border border-slate-200 space-y-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-bold text-xs text-slate-900">Version {r.version} — {r.report_type}</span>
                        <div className="text-[11px] text-slate-500">
                          Generated: {formatDateTime(r.generated_at)} by {r.generated_by}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={handleDownloadReport}
                          disabled={actionLoading}
                          className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold inline-flex items-center gap-1 shadow-xs"
                        >
                          <Download className="w-3 h-3" />
                          <span>Download PDF</span>
                        </button>
                        <Link
                          href={`/verify/${r.report_id}`}
                          target="_blank"
                          className="px-2.5 py-1 bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 rounded text-xs font-semibold inline-flex items-center gap-1"
                        >
                          <ExternalLink className="w-3 h-3" />
                          <span>Verify Integrity</span>
                        </Link>
                      </div>
                    </div>
                    <div className="p-2 bg-white rounded border text-[11px] mono-code text-slate-600">
                      <span className="font-bold text-slate-800">SHA-256:</span> {r.sha256}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-12 text-center text-slate-400">
                <FileText className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                <div>No reports generated for this inspection yet.</div>
              </div>
            )}
          </div>
        )}

        {/* TAB 8: AUDIT TRAIL */}
        {activeTab === 'audit' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b">
              <div>
                <h3 className="text-sm font-bold text-slate-900 uppercase">
                  Immutable Cryptographic Audit Trail
                </h3>
                <p className="text-xs text-slate-500">
                  SHA-256 append-only hash chain recording all evidence uploads, extractions, officer edits, and determinations.
                </p>
              </div>
              <div className="flex items-center space-x-1.5 text-xs">
                <span className="text-slate-500">Chain Status:</span>
                {audit_valid ? (
                  <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    ✓ Valid Chain
                  </span>
                ) : (
                  <span className="text-rose-700 font-bold bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                    ✕ Tampered Chain
                  </span>
                )}
              </div>
            </div>

            {audit_entries.length > 0 ? (
              <div className="relative border-l-2 border-slate-200 ml-4 pl-4 space-y-4">
                {audit_entries.map((a, idx) => (
                  <div key={a.audit_id} className="relative space-y-1 text-xs">
                    <div className="absolute -left-[23px] top-1 w-3 h-3 rounded-full bg-blue-600 border-2 border-white" />
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900">{a.action}</span>
                      <span className="text-slate-400 text-[11px]">{formatDateTime(a.timestamp)}</span>
                    </div>
                    <div className="text-slate-600">
                      Actor: <span className="font-medium text-slate-800">{a.actor_id}</span> • Entity: {a.entity_type}
                    </div>
                    {a.metadata_json && (
                      <div className="p-2 bg-slate-50 rounded border text-[11px] mono-code text-slate-600">
                        {JSON.stringify(a.metadata_json)}
                      </div>
                    )}
                    <div className="text-[10px] text-slate-400 mono-code">
                      Hash: {a.entry_hash.slice(0, 16)}... | Prev: {a.previous_hash.slice(0, 16)}...
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-12 text-center text-slate-400">
                <History className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                <div>No audit entries recorded.</div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* "Show Me Where" Evidence Inspection Modal */}
      {highlightEvidence && (
        <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-gov border border-slate-300 max-w-2xl w-full p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b">
              <div className="flex items-center space-x-2">
                <Crosshair className="w-4 h-4 text-blue-700" />
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{highlightEvidence.title}</h3>
                  <div className="text-[11px] text-slate-500 font-mono">{highlightEvidence.evidence.view_type} View Evidence</div>
                </div>
              </div>
              <button
                onClick={() => setHighlightEvidence(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {highlightEvidence.description && (
              <div className="p-2 bg-blue-50/70 border border-blue-200 rounded text-xs text-blue-950 font-medium">
                {highlightEvidence.description}
              </div>
            )}

            <div className="relative bg-slate-950 rounded p-2 flex items-center justify-center min-h-[280px]">
              <div className="relative">
                {/* Reference to evidence image */}
                <div className="text-center p-8 text-slate-400 text-xs space-y-2">
                  <Camera className="w-8 h-8 mx-auto text-slate-500" />
                  <div className="font-semibold text-slate-200">{highlightEvidence.evidence.original_filename}</div>
                  <div className="mono-code text-[11px] text-slate-400 truncate max-w-md">
                    SHA-256: {highlightEvidence.evidence.sha256}
                  </div>
                  {highlightEvidence.bbox ? (
                    <div className="p-2 bg-slate-900 text-amber-300 font-mono text-[10px] rounded border border-amber-800/50">
                      OCR Target Box: {JSON.stringify(highlightEvidence.bbox)}
                    </div>
                  ) : (
                    <div className="text-[10px] text-slate-500">Source evidence panel identified without polygon offset</div>
                  )}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t text-xs">
              <span className="text-slate-500 font-mono text-[11px]">
                Quality: {highlightEvidence.evidence.quality_verdict}
              </span>
              <button
                onClick={() => setHighlightEvidence(null)}
                className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded font-semibold text-xs transition-colors"
              >
                Close Inspection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Field Correction Modal */}
      {showCorrectionModal && selectedField && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-gov border border-slate-300 p-6 max-w-md w-full shadow-lg space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 uppercase">Officer Field Correction</h3>
              <button
                onClick={() => setShowCorrectionModal(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>
            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-500">Statutory Field:</span>
                <div className="font-bold text-slate-900 mt-0.5">{selectedField.field_name}</div>
              </div>
              <div className="p-2.5 bg-slate-50 rounded border text-slate-700">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Original System Value</div>
                <div className="font-medium mt-0.5">{selectedField.raw_value || 'None'}</div>
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Authoritative Corrected Value
                </label>
                <input
                  type="text"
                  value={correctedValue}
                  onChange={(e) => setCorrectedValue(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded font-semibold text-slate-900 outline-hidden focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Correction Reason (Recorded to Audit Trail)
                </label>
                <input
                  type="text"
                  value={correctionReason}
                  onChange={(e) => setCorrectionReason(e.target.value)}
                  placeholder="e.g. Digit 5 was misread as 4 in OCR"
                  className="w-full p-2 border border-slate-300 rounded text-slate-800 outline-hidden focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="flex items-center justify-end space-x-2 pt-2 border-t">
              <button
                onClick={() => setShowCorrectionModal(false)}
                className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleCorrectField}
                disabled={actionLoading || !correctedValue}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold disabled:opacity-50"
              >
                {actionLoading ? 'Saving...' : 'Apply & Re-evaluate'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Camera Capture Modal */}
      {showCameraModal && (
        <CameraCaptureModal
          viewType={cameraViewType}
          onCaptureAccepted={handleCameraCaptureAccepted}
          onClose={() => setShowCameraModal(false)}
        />
      )}

      {/* Case Finalisation Modal */}
      {showFinalizeModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-gov border border-slate-300 p-6 max-w-lg w-full shadow-lg space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 uppercase">Authoritative Case Finalisation</h3>
              <button
                onClick={() => setShowFinalizeModal(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            {/* Statutory Checklist */}
            <div className="space-y-2 p-3 bg-slate-50 rounded border text-xs">
              <div className="font-bold text-slate-800 uppercase text-[10px] tracking-wider mb-1">
                Pre-Finalisation Statutory Checklist
              </div>
              <div className="space-y-1.5 text-slate-700">
                <div className="flex items-center space-x-2">
                  <CheckSquare className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Evidence processed ({evidence.length} views) and quality evaluated</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckSquare className="w-3.5 h-3.5 text-emerald-600" />
                  <span>OCR extracted declarations reviewed by officer</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckSquare className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Deterministic Rule 6 &amp; Rule 7 compliance evaluated</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckSquare className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Immutable cryptographic audit trail logged</span>
                </div>
              </div>
            </div>

            {/* Unresolved REVIEW findings warning */}
            {hasReviewFindings && (
              <div className="p-3 bg-amber-50 rounded border border-amber-300 text-xs text-amber-950 space-y-2">
                <div className="flex items-center space-x-1.5 font-bold text-amber-900">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  <span>Statutory Review Findings Require Acknowledgment</span>
                </div>
                <p className="text-[11px] text-amber-800 leading-relaxed">
                  This inspection contains unresolved REVIEW items under Legal Metrology Rules (e.g., unverified PDP area or calibration).
                </p>
                <label className="flex items-start space-x-2 cursor-pointer pt-1 font-semibold text-amber-950">
                  <input
                    type="checkbox"
                    checked={acknowledgeReviewFindings}
                    onChange={(e) => setAcknowledgeReviewFindings(e.target.checked)}
                    className="mt-0.5 rounded text-blue-600"
                  />
                  <span>I, as Authorised Officer, have reviewed and explicitly acknowledge the unresolved items.</span>
                </label>
              </div>
            )}

            {/* Officer Decision Selection */}
            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-bold text-slate-800 mb-1">
                  Final Statutory Determination (Authoritative Officer Order)
                </label>
                <select
                  value={officerDecision}
                  onChange={(e) => setOfficerDecision(e.target.value as any)}
                  className="w-full p-2 border border-slate-300 rounded font-bold text-slate-900 outline-hidden focus:ring-1 focus:ring-blue-500 bg-white"
                >
                  <option value="COMPLIANT">✓ COMPLIANT — Meets Legal Metrology Requirements</option>
                  <option value="NON_COMPLIANT">✕ NON-COMPLIANT — Violations Established</option>
                  <option value="REQUIRES_REVIEW">⚠ REQUIRES REVIEW — Escalated for Further Investigation</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-800 mb-1">
                  Authoritative Officer Remarks
                </label>
                <textarea
                  value={officerRemarks}
                  onChange={(e) => setOfficerRemarks(e.target.value)}
                  placeholder="Enter detailed statutory inspection findings and order remarks..."
                  rows={3}
                  className="w-full p-2.5 border border-slate-300 rounded text-slate-800 outline-hidden focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t">
              <button
                onClick={() => setShowFinalizeModal(false)}
                className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleFinalizeSubmit}
                disabled={actionLoading || (hasReviewFindings && !acknowledgeReviewFindings)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-bold transition-colors disabled:opacity-50 shadow-xs"
              >
                {actionLoading ? 'Finalising...' : 'Submit Authoritative Final Order'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STICKY MOBILE BOTTOM ACTION BAR */}
      <div className="sm:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-900/95 backdrop-blur border-t border-slate-700/80 px-3 py-2 flex items-center justify-between gap-2 shadow-elevated">
        <button
          onClick={() => {
            setCameraViewType('FRONT');
            setShowCameraModal(true);
          }}
          disabled={isFinalised || actionLoading}
          className="flex-1 inline-flex items-center justify-center space-x-1.5 py-2.5 bg-nirikshan-saffron hover:bg-nirikshan-saffron/90 text-white rounded-brand text-xs font-bold transition-all shadow-xs disabled:opacity-50"
        >
          <Camera className="w-4 h-4" />
          <span>Take Photo</span>
        </button>

        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isFinalised || actionLoading}
          className="inline-flex items-center justify-center p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 rounded-brand text-xs font-semibold transition-colors disabled:opacity-50"
          title="Upload Packaging File"
        >
          <Upload className="w-4 h-4 text-blue-400" />
        </button>

        {!isFinalised && rule_findings.length > 0 && (
          <button
            onClick={() => setShowFinalizeModal(true)}
            className="flex-1 inline-flex items-center justify-center space-x-1 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-brand text-xs font-bold transition-all shadow-xs"
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>Finalise</span>
          </button>
        )}

        {isFinalised && (
          <button
            onClick={handleDownloadReport}
            disabled={actionLoading}
            className="flex-1 inline-flex items-center justify-center space-x-1 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-brand text-xs font-bold transition-all shadow-xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>PDF Report</span>
          </button>
        )}
      </div>
    </div>
  );
}
