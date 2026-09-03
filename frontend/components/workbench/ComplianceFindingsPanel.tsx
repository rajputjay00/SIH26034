'use client';

import React, { useState } from 'react';
import {
  Scale,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  Calculator,
  RefreshCw,
  ShieldCheck,
  ShieldAlert
} from 'lucide-react';
import { RuleFinding, CaseEvaluationSummary } from '../../types';

interface ComplianceFindingsPanelProps {
  findings: RuleFinding[];
  summary?: CaseEvaluationSummary | null;
  evaluating: boolean;
  onEvaluate: () => void;
}


export const ComplianceFindingsPanel: React.FC<ComplianceFindingsPanelProps> = ({
  findings,
  summary,
  evaluating,
  onEvaluate,
}) => {
  const [selectedCalc, setSelectedCalc] = useState<any | null>(null);

  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'PASS':
        return (
          <span className="inline-flex items-center space-x-1 text-xs font-bold text-green-700 bg-green-50 px-2 py-0.5 rounded border border-green-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-green-600" />
            <span>PASS</span>
          </span>
        );
      case 'FAIL':
        return (
          <span className="inline-flex items-center space-x-1 text-xs font-bold text-red-700 bg-red-50 px-2 py-0.5 rounded border border-red-200">
            <XCircle className="w-3.5 h-3.5 text-red-600" />
            <span>FAIL</span>
          </span>
        );
      case 'REVIEW':
        return (
          <span className="inline-flex items-center space-x-1 text-xs font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>REVIEW</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 text-xs font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
            <span>UNTESTED</span>
          </span>
        );
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return <span className="text-[10px] uppercase font-bold text-red-700 bg-red-100 px-1.5 py-0.5 rounded">Critical</span>;
      case 'HIGH':
        return <span className="text-[10px] uppercase font-bold text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded">High</span>;
      case 'MEDIUM':
        return <span className="text-[10px] uppercase font-semibold text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded">Medium</span>;
      default:
        return <span className="text-[10px] uppercase font-semibold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">Info</span>;
    }
  };

  const getOverallBanner = (determination?: string) => {
    if (!determination || determination === 'PENDING_EVALUATION') {
      return (
        <div className="p-4 bg-slate-50 border border-gov-border rounded-gov flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Scale className="w-6 h-6 text-gov-muted" />
            <div>
              <div className="text-xs font-bold text-gov-navy uppercase tracking-wider">Evaluation Pending</div>
              <div className="text-xs text-gov-muted">Click &quot;Evaluate Legal Compliance&quot; to execute statutory rules.</div>
            </div>
          </div>
        </div>
      );
    }

    if (determination === 'COMPLIANT') {
      return (
        <div className="p-4 bg-gov-pastelGreen border border-green-300 rounded-gov flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <ShieldCheck className="w-7 h-7 text-green-700" />
            <div>
              <div className="text-xs font-bold text-green-900 uppercase tracking-wider">Determination: COMPLIANT</div>
              <div className="text-xs text-green-800">All applicable mandatory declarations verified under Legal Metrology Rules, 2011.</div>
            </div>
          </div>
          <div className="flex items-center space-x-2 text-xs">
            <span className="bg-white/80 text-green-900 px-2.5 py-1 rounded font-bold border border-green-200">
              {summary?.pass_count} Passed
            </span>
          </div>
        </div>
      );
    }

    if (determination === 'NON_COMPLIANT') {
      return (
        <div className="p-4 bg-gov-warningLight border border-red-300 rounded-gov flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <ShieldAlert className="w-7 h-7 text-red-700" />
            <div>
              <div className="text-xs font-bold text-red-900 uppercase tracking-wider">Determination: NON-COMPLIANT</div>
              <div className="text-xs text-red-800">One or more mandatory statutory requirements were established as violated.</div>
            </div>
          </div>
          <div className="flex items-center space-x-2 text-xs">
            <span className="bg-white/90 text-red-800 px-2.5 py-1 rounded font-bold border border-red-200">
              {summary?.fail_count} Failed
            </span>
          </div>
        </div>
      );
    }

    return (
      <div className="p-4 bg-gov-pastelAmber border border-amber-300 rounded-gov flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <AlertTriangle className="w-7 h-7 text-amber-700" />
          <div>
            <div className="text-xs font-bold text-amber-900 uppercase tracking-wider">Determination: REQUIRES REVIEW</div>
            <div className="text-xs text-amber-800">Uncertain values, uncalibrated dimensions, or cross-view conflicts require officer confirmation.</div>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-xs">
          <span className="bg-white/80 text-amber-900 px-2.5 py-1 rounded font-bold border border-amber-200">
            {summary?.review_count} Under Review
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Header with Evaluate Action */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gov-navy flex items-center space-x-2">
            <Scale className="w-4 h-4 text-gov-primary" />
            <span>Deterministic Legal Rule Findings ({findings.length} Evaluated)</span>
          </h3>
          <p className="text-xs text-gov-muted mt-0.5">
            Rule Pack: <span className="text-gov-text font-semibold">{summary?.rule_pack_version || 'v1.0.0'}</span> | Statutory Reference: Legal Metrology (PC) Rules, 2011 &amp; DCA
          </p>
        </div>
        <button
          type="button"
          onClick={onEvaluate}
          disabled={evaluating}
          className="inline-flex items-center space-x-1.5 bg-gov-navy text-white text-xs font-semibold px-4 py-2 rounded-gov hover:bg-blue-900 disabled:opacity-50 transition-colors shadow-xs"
        >
          {evaluating ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Evaluating Rules...</span>
            </>
          ) : (
            <>
              <Scale className="w-3.5 h-3.5" />
              <span>Evaluate Legal Compliance</span>
            </>
          )}
        </button>
      </div>

      {/* Overall Aggregation Status Banner */}
      {getOverallBanner(summary?.overall_determination)}

      {/* Rule Findings Grid / List */}
      {findings.length === 0 ? (
        <div className="py-8 text-center text-xs text-gov-muted bg-gov-bg/50 rounded-gov border border-dashed border-gov-border">
          Click &quot;Evaluate Legal Compliance&quot; to execute the deterministic rule pack against all structured fields.
        </div>
      ) : (
        <div className="space-y-3">
          {findings.map((f) => (
            <div
              key={f.finding_id}
              className="p-3.5 bg-white border border-gov-border rounded-gov hover:border-slate-300 transition-colors space-y-2"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-0.5">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-xs text-gov-navy">{f.title}</span>
                    <span className="text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded font-medium">
                      {f.rule_id}
                    </span>
                    {getSeverityBadge(f.severity)}
                  </div>
                  <div className="text-[11px] text-gov-primary font-medium">{f.legal_citation}</div>
                </div>
                <div>{getStatusDisplay(f.status)}</div>
              </div>

              <p className="text-xs text-gov-text bg-gov-bg p-2.5 rounded border border-gov-border/60 leading-relaxed">
                {f.message}
              </p>

              {/* Show arithmetic breakdown button if calculation metadata exists */}
              {f.calculation_metadata_json && (
                <div className="pt-1 flex items-center justify-between text-[11px] text-gov-muted border-t border-gov-border">
                  <div className="flex items-center space-x-1">
                    <Calculator className="w-3.5 h-3.5 text-gov-primary" />
                    <span>Unit Sale Price Arithmetic:</span>
                    <span className="text-gov-text font-semibold">
                      MRP ₹{f.calculation_metadata_json.mrp} / {f.calculation_metadata_json.normalized_quantity} {f.calculation_metadata_json.base_unit}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedCalc(f.calculation_metadata_json)}
                    className="text-xs text-gov-primary font-semibold hover:underline"
                  >
                    View Math Breakdown →
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Arithmetic Breakdown Modal */}
      {selectedCalc && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-white rounded-gov border border-gov-border max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="border-b border-gov-border pb-2">
              <h4 className="text-sm font-bold text-gov-navy flex items-center space-x-2">
                <Calculator className="w-4 h-4 text-gov-primary" />
                <span>Deterministic Unit Sale Price Arithmetic</span>
              </h4>
              <p className="text-xs text-gov-muted mt-0.5">
                Pure Decimal computation with 1% rounding tolerance under PC Rules 2011 Amendments.
              </p>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1.5 border-b border-gov-border">
                <span className="text-gov-muted">Maximum Retail Price (Numerator):</span>
                <span className="font-bold text-gov-text">₹ {selectedCalc.mrp?.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-gov-border">
                <span className="text-gov-muted">Normalized Net Quantity (Denominator):</span>
                <span className="font-bold text-gov-text">{selectedCalc.normalized_quantity} {selectedCalc.base_unit}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-gov-border">
                <span className="text-gov-muted">Calculated Unit Sale Price:</span>
                <span className="font-bold text-green-700">₹ {(selectedCalc.calculated_usp || selectedCalc.expected_usp)?.toFixed(2)} / {selectedCalc.base_unit}</span>
              </div>
              {selectedCalc.printed_usp && (
                <div className="flex justify-between py-1.5 border-b border-gov-border">
                  <span className="text-gov-muted">Printed Unit Sale Price on Package:</span>
                  <span className="font-bold text-gov-text">₹ {selectedCalc.printed_usp?.toFixed(2)} / {selectedCalc.base_unit}</span>
                </div>
              )}
              {selectedCalc.diff !== undefined && (
                <div className="flex justify-between py-1.5">
                  <span className="text-gov-muted">Arithmetic Discrepancy:</span>
                  <span className="font-bold text-gov-navy">₹ {selectedCalc.diff?.toFixed(2)}</span>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2 border-t border-gov-border">
              <button
                type="button"
                onClick={() => setSelectedCalc(null)}
                className="px-4 py-2 bg-gov-navy text-white text-xs font-semibold rounded-gov hover:bg-blue-900 transition-colors"
              >
                Close Breakdown
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
