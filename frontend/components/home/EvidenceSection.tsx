'use client';

import React from 'react';
import Link from 'next/link';
import { ShieldCheck, Lock, Eye, CheckCircle2, ArrowRight, FileSearch, Hash } from 'lucide-react';

export const EvidenceSection: React.FC = () => {
  return (
    <section className="py-16 bg-white border-b border-nirikshan-border" id="evidence">
      <div className="max-w-7xl mx-auto px-4 md:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column: Visual Evidence Card & Inspector Preview (6 cols) */}
          <div className="lg:col-span-6">
            <div className="bg-slate-900 rounded-brand p-6 text-white shadow-elevated border border-slate-800 space-y-4">
              {/* Header Bar */}
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                  <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
                  <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
                  <span className="text-xs font-medium text-slate-400 pl-2">Evidence Inspector • Multi-View Panel</span>
                </div>
                <span className="text-[11px] font-semibold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
                  SHA-256 VERIFIED
                </span>
              </div>

              {/* Mock Evidence Inspector Visual */}
              <div className="bg-slate-950 rounded p-4 border border-slate-800 space-y-3 text-xs">
                <div className="flex justify-between items-center text-slate-400 text-[11px]">
                  <span>VIEW: <strong>FRONT_PANEL</strong></span>
                  <span>FORMAT: <strong>JPEG (2400x1800)</strong></span>
                  <span className="text-emerald-400">QUALITY: <strong>PASS (VAR: 284.2)</strong></span>
                </div>

                <div className="bg-slate-900/90 rounded p-3 border border-slate-800 space-y-2">
                  <div className="text-[10px] text-slate-500 flex items-center space-x-1">
                    <Hash className="w-3 h-3 text-nirikshan-saffron" />
                    <span>AUTHORITATIVE SERVER SHA-256:</span>
                  </div>
                  <div className="text-[11px] text-blue-300 break-all bg-black/40 p-2 rounded border border-slate-800">
                    e4f192e0daed7f19e9d2c0a1f5c17dce1a9010ba4ef1fe7dc0cbf3c0e
                  </div>
                </div>

                {/* Extracted Polygons Showcase */}
                <div className="space-y-1.5 pt-1">
                  <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                    Extracted Declaration Polygons:
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div className="bg-slate-900 p-2 rounded border border-slate-800 flex items-center justify-between">
                      <span className="text-slate-300">MRP: ₹200.00</span>
                      <span className="text-emerald-400 text-[10px]">98.6%</span>
                    </div>
                    <div className="bg-slate-900 p-2 rounded border border-slate-800 flex items-center justify-between">
                      <span className="text-slate-300">Net Qty: 500 g</span>
                      <span className="text-emerald-400 text-[10px]">99.1%</span>
                    </div>
                    <div className="bg-slate-900 p-2 rounded border border-slate-800 flex items-center justify-between">
                      <span className="text-slate-300">USP: ₹0.40 / g</span>
                      <span className="text-emerald-400 text-[10px]">97.8%</span>
                    </div>
                    <div className="bg-slate-900 p-2 rounded border border-slate-800 flex items-center justify-between">
                      <span className="text-slate-300">Mfg: 08/2026</span>
                      <span className="text-emerald-400 text-[10px]">98.4%</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-[11px] text-slate-400 flex items-center justify-between pt-1">
                <span>Original Raw Bytes: <strong>IMMUTABLE</strong></span>
                <span className="text-blue-400">Derived Artifacts Segregated</span>
              </div>
            </div>
          </div>

          {/* Right Column: Editorial Explanation (6 cols) */}
          <div className="lg:col-span-6 space-y-5">
            <div className="inline-flex items-center space-x-1.5 bg-blue-50 text-nirikshan-blue px-3 py-1 rounded-full text-xs font-semibold border border-blue-200">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>EVIDENCE &amp; TRACEABILITY</span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-bold text-nirikshan-navy tracking-tight leading-tight">
              Evidence-First Inspection Philosophy
            </h2>

            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              Every compliance determination in NIRIKSHAN is anchored to immutable source imagery. Unlike generic OCR scanners, every extracted declaration maintains coordinate-level provenance back to its exact pixel bounding box on the physical package.
            </p>

            <div className="space-y-3 pt-2">
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 flex-shrink-0 mt-0.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-nirikshan-navy">Authoritative Server-Side SHA-256</h4>
                  <p className="text-xs text-slate-500">Cryptographic hash is calculated immediately upon byte ingestion to ensure evidence integrity.</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 flex-shrink-0 mt-0.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-nirikshan-navy">Deterministic OpenCV Quality Gate</h4>
                  <p className="text-xs text-slate-500">Evaluates Laplacian blur variance, luminance glare, and contrast prior to OCR execution.</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 flex-shrink-0 mt-0.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-nirikshan-navy">Interactive "Show Me Where" Navigation</h4>
                  <p className="text-xs text-slate-500">Inspectors can click any declaration or violation finding to immediately highlight its source region.</p>
                </div>
              </div>
            </div>

            <div className="pt-3">
              <Link
                href="/inspections"
                className="inline-flex items-center space-x-2 bg-nirikshan-navy hover:bg-nirikshan-navyDark text-white text-xs font-semibold px-5 py-2.5 rounded-brand transition-colors shadow-xs"
              >
                <span>Open Evidence Workbench</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
