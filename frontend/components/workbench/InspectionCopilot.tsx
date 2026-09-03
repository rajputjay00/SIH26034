'use client';

import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  Clock,
  Camera,
  FileText,
  Scale,
  ShieldCheck,
  UserCheck,
  Layers
} from 'lucide-react';
import {
  EvidenceItem,
  ExtractedField,
  RuleFinding,
  InspectionCase
} from '../../types';

interface InspectionCopilotProps {
  caseObj: InspectionCase;
  evidence: EvidenceItem[];
  fields: ExtractedField[];
  findings: RuleFinding[];
}

export const InspectionCopilot: React.FC<InspectionCopilotProps> = ({
  caseObj,
  evidence,
  fields,
  findings
}) => {
  // Check evidence view completeness
  const hasFront = evidence.some((e) => e.view_type === 'FRONT');
  const hasBack = evidence.some((e) => e.view_type === 'BACK');
  const hasSide = evidence.some((e) => e.view_type === 'SIDE');
  const hasBase = evidence.some((e) => e.view_type === 'BASE');

  // Quality check
  const hasQualityIssues = evidence.some((e) => e.quality_verdict === 'FAIL' || e.quality_verdict === 'WARN');

  // Declarations check
  const hasMrp = fields.some((f) => f.field_name === 'mrp' && (f.normalized_value || f.raw_value));
  const hasQty = fields.some((f) => f.field_name === 'net_quantity' && (f.normalized_value || f.raw_value));
  const hasUsp = fields.some((f) => f.field_name === 'unit_sale_price' && (f.normalized_value || f.raw_value));
  const hasMfg = fields.some((f) => f.field_name === 'manufacturer' && (f.normalized_value || f.raw_value));

  // Compliance findings check
  const hasFailFindings = findings.some((f) => f.status === 'FAIL');
  const hasReviewFindings = findings.some((f) => f.status === 'REVIEW');
  const allFindingsEvaluated = findings.length > 0;

  // Finalisation readiness
  const isFinalised = caseObj.status === 'FINALISED';
  const readyForDecision = (hasFront || hasBack) && allFindingsEvaluated && !isFinalised;

  return (
    <div className="bg-white rounded-gov border border-slate-200 p-4 shadow-xs space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-blue-700" />
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
            Field Inspection Copilot
          </h3>
        </div>
        <span className="text-[10px] text-slate-500 font-medium">Workflow Assistant</span>
      </div>

      {/* Step 1: Multi-view Evidence */}
      <div className="space-y-1.5">
        <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between">
          <span>1. Evidence Capture</span>
          <span className="text-[10px] text-slate-400 font-medium">{evidence.length} Views</span>
        </div>
        <div className="grid grid-cols-2 gap-1 text-[11px]">
          <div className={`flex items-center space-x-1.5 p-1.5 rounded border ${hasFront ? 'bg-emerald-50/60 border-emerald-200 text-emerald-950 font-medium' : 'bg-slate-50 border-slate-200 text-slate-500'}`}>
            {hasFront ? <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" /> : <Clock className="w-3 h-3 text-slate-400 shrink-0" />}
            <span>Front Panel</span>
          </div>
          <div className={`flex items-center space-x-1.5 p-1.5 rounded border ${hasBack ? 'bg-emerald-50/60 border-emerald-200 text-emerald-950 font-medium' : 'bg-slate-50 border-slate-200 text-slate-500'}`}>
            {hasBack ? <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" /> : <Clock className="w-3 h-3 text-slate-400 shrink-0" />}
            <span>Back Panel</span>
          </div>
          <div className={`flex items-center space-x-1.5 p-1.5 rounded border ${hasSide ? 'bg-emerald-50/60 border-emerald-200 text-emerald-950 font-medium' : 'bg-slate-50 border-slate-200 text-slate-500'}`}>
            {hasSide ? <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" /> : <Clock className="w-3 h-3 text-slate-400 shrink-0" />}
            <span>Side Panel</span>
          </div>
          <div className={`flex items-center space-x-1.5 p-1.5 rounded border ${hasBase ? 'bg-emerald-50/60 border-emerald-200 text-emerald-950 font-medium' : 'bg-slate-50 border-slate-200 text-slate-500'}`}>
            {hasBase ? <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" /> : <Clock className="w-3 h-3 text-slate-400 shrink-0" />}
            <span>Base / Mark</span>
          </div>
        </div>
      </div>

      {/* Step 2: Statutory Declaration Checks */}
      <div className="space-y-1.5">
        <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between">
          <span>2. Mandatory Declarations</span>
          <span className="text-[10px] text-slate-400 font-medium">{fields.length} Fields</span>
        </div>
        <div className="space-y-1 text-[11px]">
          <div className="flex items-center justify-between p-1.5 rounded bg-slate-50 border border-slate-100">
            <span className="text-slate-700">MRP &amp; Unit Sale Price:</span>
            {hasMrp && hasUsp ? (
              <span className="text-emerald-700 font-semibold flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Extracted</span>
            ) : (
              <span className="text-amber-700 font-medium flex items-center gap-1"><Clock className="w-3 h-3" /> Incomplete</span>
            )}
          </div>
          <div className="flex items-center justify-between p-1.5 rounded bg-slate-50 border border-slate-100">
            <span className="text-slate-700">Net Quantity:</span>
            {hasQty ? (
              <span className="text-emerald-700 font-semibold flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Extracted</span>
            ) : (
              <span className="text-amber-700 font-medium flex items-center gap-1"><Clock className="w-3 h-3" /> Missing</span>
            )}
          </div>
          <div className="flex items-center justify-between p-1.5 rounded bg-slate-50 border border-slate-100">
            <span className="text-slate-700">Manufacturer &amp; Origin:</span>
            {hasMfg ? (
              <span className="text-emerald-700 font-semibold flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Extracted</span>
            ) : (
              <span className="text-slate-400 flex items-center gap-1"><Clock className="w-3 h-3" /> Pending</span>
            )}
          </div>
        </div>
      </div>

      {/* Step 3: Statutory Rule Engine Evaluation */}
      <div className="space-y-1.5">
        <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between">
          <span>3. Statutory Findings</span>
          <span className="text-[10px] text-slate-400 font-medium">{findings.length} Rules</span>
        </div>
        <div className="space-y-1 text-[11px]">
          {allFindingsEvaluated ? (
            <>
              {hasFailFindings && (
                <div className="p-1.5 rounded bg-rose-50 border border-rose-200 text-rose-900 font-medium flex items-center justify-between">
                  <span>Violations Detected:</span>
                  <span className="font-bold">{findings.filter((f) => f.status === 'FAIL').length} FAIL</span>
                </div>
              )}
              {hasReviewFindings && (
                <div className="p-1.5 rounded bg-amber-50 border border-amber-200 text-amber-900 font-medium flex items-center justify-between">
                  <span>Officer Review Items:</span>
                  <span className="font-bold">{findings.filter((f) => f.status === 'REVIEW').length} REVIEW</span>
                </div>
              )}
              {!hasFailFindings && !hasReviewFindings && (
                <div className="p-1.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-900 font-medium flex items-center justify-between">
                  <span>All Evaluated Rules:</span>
                  <span className="font-bold">ALL PASS</span>
                </div>
              )}
            </>
          ) : (
            <div className="p-1.5 bg-slate-50 border border-slate-200 rounded text-slate-500 text-center">
              Awaiting deterministic evaluation
            </div>
          )}
        </div>
      </div>

      {/* Step 4: Finalisation Status */}
      <div className="pt-2 border-t border-slate-100">
        <div className="flex items-center justify-between text-xs">
          <span className="font-bold text-slate-800">Officer Finalisation:</span>
          {isFinalised ? (
            <span className="text-blue-900 font-bold bg-blue-50 px-2 py-0.5 rounded border border-blue-200 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-blue-700" /> Sealed
            </span>
          ) : readyForDecision ? (
            <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 flex items-center gap-1">
              <UserCheck className="w-3 h-3 text-emerald-600" /> Ready
            </span>
          ) : (
            <span className="text-slate-500 font-medium bg-slate-100 px-2 py-0.5 rounded">
              In Progress
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
