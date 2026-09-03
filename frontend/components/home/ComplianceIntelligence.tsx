'use client';

import React from 'react';
import Link from 'next/link';
import { Scale, CheckCircle2, XCircle, AlertTriangle, ArrowRight, ShieldCheck, Ruler } from 'lucide-react';

export const ComplianceIntelligence: React.FC = () => {
  return (
    <section className="py-16 bg-nirikshan-lightBg border-b border-nirikshan-border" id="compliance">
      <div className="max-w-7xl mx-auto px-4 md:px-8">
        <div className="text-center max-w-3xl mx-auto space-y-3 mb-12">
          <div className="inline-flex items-center space-x-1.5 bg-emerald-50 text-emerald-800 px-3 py-1 rounded-full text-xs font-semibold border border-emerald-200">
            <Scale className="w-3.5 h-3.5 text-emerald-600" />
            <span>STATUTORY RULE ENGINE</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-nirikshan-navy tracking-tight">
            Compliance Intelligence &amp; Decision Support
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
            Deterministic rule execution strictly based on Legal Metrology (Packaged Commodities) Rules, 2011 and DCA Amendments. Pure algorithmic consistency without opaque probabilistic guesses.
          </p>
        </div>

        {/* 3 Determination Cards (Dual text + icon badges) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {/* Card 1: Compliant */}
          <div className="bg-white p-6 rounded-brand border-2 border-emerald-200/80 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center space-x-1.5 bg-emerald-50 text-emerald-800 px-2.5 py-1 rounded text-xs font-bold border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>COMPLIANT</span>
              </span>
              <span className="text-[11px] font-medium text-slate-500">Rule 6 &amp; 7 Pass</span>
            </div>

            <h3 className="text-sm font-bold text-nirikshan-navy">
              Statutory Declarations Fully Verified
            </h3>

            <p className="text-xs text-slate-500 leading-relaxed">
              All 8 mandatory declarations are present, Unit Sale Price arithmetic matches MRP/Net Quantity exactly, and character height meets Rule 7 Table 1 thresholds.
            </p>

            <div className="text-[11px] font-medium bg-slate-50 p-2.5 rounded border border-slate-100 text-slate-600">
              ✓ MRP + USP Math Consistent<br />
              ✓ Font Height ≥ Statutory Minimum
            </div>
          </div>

          {/* Card 2: Non-Compliant */}
          <div className="bg-white p-6 rounded-brand border-2 border-red-200/80 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center space-x-1.5 bg-red-50 text-red-800 px-2.5 py-1 rounded text-xs font-bold border border-red-200">
                <XCircle className="w-3.5 h-3.5 text-red-600" />
                <span>NON-COMPLIANT</span>
              </span>
              <span className="text-[11px] font-medium text-slate-500">Statutory Violation</span>
            </div>

            <h3 className="text-sm font-bold text-nirikshan-navy">
              Contradiction or Omission Detected
            </h3>

            <p className="text-xs text-slate-500 leading-relaxed">
              Missing mandatory declaration (e.g. manufacturer details) or mathematical inconsistency between stated Unit Sale Price and Maximum Retail Price.
            </p>

            <div className="text-[11px] font-medium bg-slate-50 p-2.5 rounded border border-slate-100 text-slate-600">
              ✕ Rule 6(11) USP Discrepancy<br />
              ✕ Rule 6(1) Missing Mandatory Field
            </div>
          </div>

          {/* Card 3: Requires Review */}
          <div className="bg-white p-6 rounded-brand border-2 border-amber-200/80 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center space-x-1.5 bg-amber-50 text-amber-800 px-2.5 py-1 rounded text-xs font-bold border border-amber-200">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                <span>REQUIRES REVIEW</span>
              </span>
              <span className="text-[11px] font-medium text-slate-500">Officer Verification</span>
            </div>

            <h3 className="text-sm font-bold text-nirikshan-navy">
              Ambiguous PDP Area or Anomaly
            </h3>

            <p className="text-xs text-slate-500 leading-relaxed">
              Principal Display Panel area is unverified, physical calibration is missing, or edge analysis detects suspected price relabeling requiring manual inspection.
            </p>

            <div className="text-[11px] font-medium bg-slate-50 p-2.5 rounded border border-slate-100 text-slate-600">
              ⚠ Rule 7 PDP Area Unverified<br />
              ⚠ Potential Price Sticker Overlay
            </div>
          </div>
        </div>

        {/* Institutional Safeguard Note */}
        <div className="bg-white p-5 rounded-brand border border-slate-200 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-brand bg-slate-100 flex items-center justify-center text-nirikshan-navy flex-shrink-0">
              <ShieldCheck className="w-5 h-5 text-nirikshan-blue" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-nirikshan-navy">
                Authoritative Legal Safeguard
              </h4>
              <p className="text-xs text-slate-500">
                NIRIKSHAN is an evidence-oriented decision-support terminal. The Authorised Officer remains the sole statutory authority for issuing legal orders under the Legal Metrology Act, 2009.
              </p>
            </div>
          </div>

          <Link
            href="/inspections"
            className="inline-flex items-center space-x-1.5 bg-nirikshan-navy hover:bg-nirikshan-navyDark text-white text-xs font-semibold px-4 py-2 rounded-brand transition-colors whitespace-nowrap"
          >
            <span>Review Active Findings</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </section>
  );
};
