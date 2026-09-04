'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import {
  ArrowLeft,
  Camera,
  Layers,
  Scale,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileText
} from 'lucide-react';
import { EvidenceUploader } from '@/components/evidence/EvidenceUploader';
import { EvidenceGallery } from '@/components/evidence/EvidenceGallery';
import { OCRViewer } from '@/components/evidence/OCRViewer';
import { StructuredFieldsPanel } from '@/components/workbench/StructuredFieldsPanel';
import { ComplianceFindingsPanel } from '@/components/workbench/ComplianceFindingsPanel';
import CalibrationViewer from '@/components/workbench/CalibrationViewer';
import {
  EvidenceItem,
  OCRResult,
  ExtractedField,
  RuleFinding,
  CaseEvaluationSummary,
  CalibrationData,
  VisualMeasurement,
  VisualAnomaly
} from '@/types';
import {
  fetchCaseEvidence,
  processEvidenceOCR,
  fetchEvidenceOCR,
  extractCaseFields,
  fetchCaseFields,
  evaluateCaseCompliance,
  fetchCaseFindings,
  fetchCaseCalibrations,
  fetchCaseMeasurements,
  fetchCaseAnomalies
} from '@/lib/api';


export default function CaseWorkbenchPage() {
  const params = useParams();
  const inspectionId = (params?.id as string) || '';

  const [activeTab, setActiveTab] = useState<'evidence' | 'forensics' | 'fields' | 'compliance'>('evidence');
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [fieldsList, setFieldsList] = useState<ExtractedField[]>([]);
  const [findingsList, setFindingsList] = useState<RuleFinding[]>([]);
  const [evalSummary, setEvalSummary] = useState<CaseEvaluationSummary | null>(null);
  const [calibrationsList, setCalibrationsList] = useState<CalibrationData[]>([]);
  const [measurementsList, setMeasurementsList] = useState<VisualMeasurement[]>([]);
  const [anomaliesList, setAnomaliesList] = useState<VisualAnomaly[]>([]);

  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [evaluating, setEvaluating] = useState(false);

  const [inspectingEvidence, setInspectingEvidence] = useState<EvidenceItem | null>(null);
  const [inspectingOCR, setInspectingOCR] = useState<OCRResult[]>([]);

  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  const loadCaseData = async () => {
    if (!inspectionId || !isAuthenticated) return;
    try {
      setLoading(true);
      const [evidence, fields, findings, calibrations, measurements, anomalies] = await Promise.all([
        fetchCaseEvidence(inspectionId).catch(() => []),
        fetchCaseFields(inspectionId).catch(() => []),
        fetchCaseFindings(inspectionId).catch(() => []),
        fetchCaseCalibrations(inspectionId).catch(() => []),
        fetchCaseMeasurements(inspectionId).catch(() => []),
        fetchCaseAnomalies(inspectionId).catch(() => [])
      ]);
      setEvidenceList(evidence);
      setFieldsList(fields);
      setFindingsList(findings);
      setCalibrationsList(calibrations);
      setMeasurementsList(measurements);
      setAnomaliesList(anomalies);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      loadCaseData();
    }
  }, [inspectionId, isAuthenticated]);


  const handleEvidenceUploaded = (item: EvidenceItem) => {
    setEvidenceList((prev) => [...prev, item]);
  };

  const handleProcessOCR = async (item: EvidenceItem) => {
    setProcessingId(item.evidence_id);
    try {
      const updated = await processEvidenceOCR(item.evidence_id);
      setEvidenceList((prev) =>
        prev.map((e) => (e.evidence_id === updated.evidence_id ? updated : e))
      );
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Processing failed';
      alert(message);
    } finally {
      setProcessingId(null);
    }
  };

  const handleInspectOCR = async (item: EvidenceItem) => {
    setInspectingEvidence(item);
    try {
      const ocrResults = await fetchEvidenceOCR(item.evidence_id);
      setInspectingOCR(ocrResults);
    } catch {
      setInspectingOCR([]);
    }
  };

  const handleExtractFields = async () => {
    try {
      setExtracting(true);
      const fields = await extractCaseFields(inspectionId);
      setFieldsList(fields);
      setActiveTab('fields');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Field extraction failed';
      alert(message);
    } finally {
      setExtracting(false);
    }
  };

  const handleFieldUpdated = (updated: ExtractedField) => {
    setFieldsList((prev) =>
      prev.map((f) => (f.field_id === updated.field_id ? updated : f))
    );
  };

  const handleEvaluateCompliance = async () => {
    try {
      setEvaluating(true);
      const summary = await evaluateCaseCompliance(inspectionId);
      setEvalSummary(summary);
      setFindingsList(summary.findings);
      setActiveTab('compliance');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Compliance evaluation failed';
      alert(message);
    } finally {
      setEvaluating(false);
    }
  };

  const getDeterminationBadge = (determination?: string) => {
    switch (determination) {
      case 'COMPLIANT':
        return (
          <span className="bg-gov-pastelGreen text-green-800 border border-green-300 px-3 py-1 rounded-gov text-xs font-bold flex items-center space-x-1.5">
            <CheckCircle2 className="w-4 h-4 text-green-600" />
            <span>COMPLIANT</span>
          </span>
        );
      case 'NON_COMPLIANT':
        return (
          <span className="bg-gov-warningLight text-gov-warning border border-red-300 px-3 py-1 rounded-gov text-xs font-bold flex items-center space-x-1.5">
            <XCircle className="w-4 h-4 text-red-600" />
            <span>NON-COMPLIANT</span>
          </span>
        );
      case 'REQUIRES_REVIEW':
        return (
          <span className="bg-gov-pastelAmber text-amber-900 border border-amber-300 px-3 py-1 rounded-gov text-xs font-bold flex items-center space-x-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>REQUIRES REVIEW</span>
          </span>
        );
      default:
        return (
          <span className="bg-slate-100 text-slate-700 border border-slate-300 px-3 py-1 rounded-gov text-xs font-medium">
            PENDING EVALUATION
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Case Details */}
      <div className="bg-white border border-gov-border rounded-gov p-4 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <Link
            href="/"
            className="p-2 bg-gov-bg border border-gov-border rounded-gov hover:bg-slate-200 text-gov-navy transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="text-xs text-gov-muted flex items-center space-x-2">
              <span>Legal Metrology Inspection Case</span>
              <span>•</span>
              <span className="mono-code">{inspectionId}</span>
            </div>
            <h2 className="text-base font-bold text-gov-navy tracking-tight">
              Commodity Compliance & Forensic Inspection Workbench
            </h2>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {getDeterminationBadge(evalSummary?.overall_determination)}
          <button
            onClick={loadCaseData}
            title="Refresh case data"
            className="p-2 border border-gov-border rounded-gov hover:bg-gov-bg text-gov-muted hover:text-gov-text"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 4-Step Navigation Tabs */}
      <div className="flex border-b border-gov-border bg-white px-2 rounded-t-gov">
        <button
          onClick={() => setActiveTab('evidence')}
          className={`flex items-center space-x-2 py-3 px-4 text-xs font-semibold border-b-2 transition-all ${
            activeTab === 'evidence'
              ? 'border-gov-primary text-gov-primary bg-gov-pastelBlue/30'
              : 'border-transparent text-gov-muted hover:text-gov-text'
          }`}
        >
          <Camera className="w-4 h-4" />
          <span>1. Evidence Intake ({evidenceList.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('forensics')}
          className={`flex items-center space-x-2 py-3 px-4 text-xs font-semibold border-b-2 transition-all ${
            activeTab === 'forensics'
              ? 'border-gov-primary text-gov-primary bg-gov-pastelBlue/30'
              : 'border-transparent text-gov-muted hover:text-gov-text'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>2. CV Calibration & Forensics</span>
        </button>

        <button
          onClick={() => setActiveTab('fields')}
          className={`flex items-center space-x-2 py-3 px-4 text-xs font-semibold border-b-2 transition-all ${
            activeTab === 'fields'
              ? 'border-gov-primary text-gov-primary bg-gov-pastelBlue/30'
              : 'border-transparent text-gov-muted hover:text-gov-text'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>3. Structured Fields ({fieldsList.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('compliance')}
          className={`flex items-center space-x-2 py-3 px-4 text-xs font-semibold border-b-2 transition-all ${
            activeTab === 'compliance'
              ? 'border-gov-primary text-gov-primary bg-gov-pastelBlue/30'
              : 'border-transparent text-gov-muted hover:text-gov-text'
          }`}
        >
          <Scale className="w-4 h-4" />
          <span>4. Legal Rule Findings ({findingsList.length})</span>
        </button>
      </div>

      {/* Tab 1: Evidence & Image Quality */}
      {activeTab === 'evidence' && (
        <div className="space-y-6">
          <EvidenceUploader inspectionId={inspectionId} onUploaded={handleEvidenceUploaded} />
          <EvidenceGallery
            items={evidenceList}
            onSelectInspect={handleInspectOCR}
            onProcessOCR={handleProcessOCR}
            processingId={processingId}
          />
          {evidenceList.length > 0 && (
            <div className="flex justify-end p-4 bg-white border border-gov-border rounded-gov">
              <button
                type="button"
                onClick={() => setActiveTab('forensics')}
                className="inline-flex items-center space-x-2 bg-gov-navy text-white text-xs font-semibold px-4 py-2.5 rounded-gov hover:bg-blue-900 transition-colors shadow-xs"
              >
                <span>Proceed to Visual Forensics →</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Visual Forensics & Physical Calibration */}
      {activeTab === 'forensics' && (
        <div className="space-y-6">
          {evidenceList.length === 0 ? (
            <div className="p-8 bg-white border border-gov-border rounded-gov text-center text-xs text-gov-muted">
              Please upload evidence images in Step 1 first to run physical calibration and forensic checks.
            </div>
          ) : (
            evidenceList.map((ev) => {
              const calib = calibrationsList.find((c) => c.evidence_id === ev.evidence_id);
              const measurements = measurementsList.filter((m) => m.evidence_id === ev.evidence_id);
              const anomalies = anomaliesList.filter((a) => a.evidence_id === ev.evidence_id);
              return (
                <div key={ev.evidence_id} className="space-y-3">
                  <div className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                    Evidence View: {ev.view_type} ({ev.original_filename})
                  </div>
                  <CalibrationViewer
                    inspectionId={inspectionId}
                    evidenceId={ev.evidence_id}
                    calibration={calib}
                    measurements={measurements}
                    anomalies={anomalies}
                    onRefresh={loadCaseData}
                  />
                </div>
              );
            })
          )}
          {evidenceList.length > 0 && (
            <div className="flex justify-end p-4 bg-white border border-gov-border rounded-gov">
              <button
                type="button"
                onClick={handleExtractFields}
                disabled={extracting}
                className="inline-flex items-center space-x-2 bg-gov-navy text-white text-xs font-semibold px-4 py-2.5 rounded-gov hover:bg-blue-900 transition-colors shadow-xs"
              >
                <span>Proceed to Structured Extraction →</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Structured Declarations */}
      {activeTab === 'fields' && (
        <div className="space-y-6">
          <StructuredFieldsPanel
            inspectionId={inspectionId}
            fields={fieldsList}
            onExtract={handleExtractFields}
            onFieldUpdated={handleFieldUpdated}
            extracting={extracting}

          />
          {fieldsList.length > 0 && (
            <div className="flex justify-end p-4 bg-white border border-gov-border rounded-gov">
              <button
                type="button"
                onClick={handleEvaluateCompliance}
                disabled={evaluating}
                className="inline-flex items-center space-x-2 bg-gov-primary text-white text-xs font-semibold px-4 py-2.5 rounded-gov hover:bg-blue-600 transition-colors shadow-xs"
              >
                <Scale className="w-4 h-4" />
                <span>Evaluate Legal Metrology Compliance →</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Legal Rule Findings */}
      {activeTab === 'compliance' && (
        <div className="space-y-6">
          <ComplianceFindingsPanel
            summary={evalSummary}
            findings={findingsList}
            onEvaluate={handleEvaluateCompliance}
            evaluating={evaluating}
          />
        </div>
      )}

      {/* Interactive OCR Bounding Box Modal */}
      {inspectingEvidence && (
        <OCRViewer
          evidence={inspectingEvidence}
          ocrResults={inspectingOCR}
          onClose={() => {
            setInspectingEvidence(null);
            setInspectingOCR([]);
          }}
        />
      )}
    </div>
  );
}
