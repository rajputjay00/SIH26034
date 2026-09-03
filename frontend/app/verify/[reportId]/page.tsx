'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';

interface VerificationData {
  report_id: string;
  version: number;
  exists: boolean;
  integrity_status: string;
  stored_hash?: string;
  computed_hash?: string;
  generated_at?: string;
  finalized_at?: string;
  case_number?: string;
  overall_determination?: string;
  officer_id?: string;
  message: string;
}

export default function ReportVerificationPage({ params }: { params: { reportId: string } }) {
  const [data, setData] = useState<VerificationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function verifyReport() {
      try {
        const res = await fetch(`http://localhost:8000/api/v1/reports/${encodeURIComponent(params.reportId)}/verify`);
        if (!res.ok) {
          throw new Error('Failed to retrieve verification record.');
        }
        const json = await res.json();
        setData(json);
      } catch (err: any) {
        setError(err.message || 'Verification service error.');
      } finally {
        setLoading(false);
      }
    }
    verifyReport();
  }, [params.reportId]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8 flex flex-col items-center justify-center">
      <div className="max-w-2xl w-full bg-slate-900 border border-slate-800 rounded-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-slate-950 p-6 border-b border-slate-800 text-center space-y-1">
          <p className="text-xs uppercase tracking-widest text-slate-400 font-semibold">Government of India</p>
          <p className="text-xs text-slate-400">Department of Consumer Affairs — Legal Metrology Division</p>
          <h1 className="text-lg font-bold text-slate-100 mt-2">Official Inspection Report Verification</h1>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {loading ? (
            <div className="text-center py-8 text-slate-400 animate-pulse text-sm">
              Verifying cryptographic report integrity...
            </div>
          ) : error ? (
            <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-lg text-red-300 text-sm">
              <p className="font-bold">Verification Error</p>
              <p className="text-xs mt-1">{error}</p>
            </div>
          ) : data ? (
            <div className="space-y-4">
              {/* Status Banner */}
              <div
                className={`p-4 rounded-lg border ${
                  data.integrity_status === 'VALID'
                    ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
                    : data.integrity_status === 'INTEGRITY_MISMATCH'
                    ? 'bg-red-950/40 border-red-800 text-red-300'
                    : 'bg-amber-950/40 border-amber-800 text-amber-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider">Integrity Status</span>
                  <span className="font-mono text-xs font-bold px-2.5 py-1 rounded bg-slate-900/80 border border-current">
                    {data.integrity_status}
                  </span>
                </div>
                <p className="text-xs mt-2 leading-relaxed">{data.message}</p>
              </div>

              {/* Details Table */}
              <div className="border border-slate-800 rounded-lg overflow-hidden text-xs divide-y divide-slate-800">
                <div className="flex justify-between p-3 bg-slate-950/50">
                  <span className="text-slate-400 font-medium">Report Identifier:</span>
                  <span className="font-mono text-slate-200">{data.report_id}</span>
                </div>
                <div className="flex justify-between p-3 bg-slate-900">
                  <span className="text-slate-400 font-medium">Report Version:</span>
                  <span className="font-mono text-slate-200">v{data.version}</span>
                </div>
                {data.case_number && (
                  <div className="flex justify-between p-3 bg-slate-950/50">
                    <span className="text-slate-400 font-medium">Case Number:</span>
                    <span className="font-medium text-slate-200">{data.case_number}</span>
                  </div>
                )}
                {data.overall_determination && (
                  <div className="flex justify-between p-3 bg-slate-900">
                    <span className="text-slate-400 font-medium">Statutory Determination:</span>
                    <span className="font-bold text-slate-200">{data.overall_determination}</span>
                  </div>
                )}
                {data.generated_at && (
                  <div className="flex justify-between p-3 bg-slate-950/50">
                    <span className="text-slate-400 font-medium">Generated Timestamp:</span>
                    <span className="text-slate-300">{new Date(data.generated_at).toLocaleString()}</span>
                  </div>
                )}
                {data.stored_hash && (
                  <div className="p-3 bg-slate-900 space-y-1">
                    <span className="text-slate-400 font-medium block">Registered Cryptographic SHA-256 Fingerprint:</span>
                    <span className="font-mono text-[11px] text-emerald-400 break-all block bg-slate-950 p-2 rounded border border-slate-800">
                      {data.stored_hash}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ) : null}

          {/* Footer & Disclaimer */}
          <div className="pt-4 border-t border-slate-800 text-center space-y-2">
            <p className="text-[11px] text-slate-500 leading-relaxed">
              This verification endpoint validates the exact binary authenticity of inspection documents generated by the
              LegalMetriX system. The inspecting officer remains the authoritative statutory decision maker.
            </p>
            <div className="pt-2">
              <Link href="/" className="text-xs text-blue-400 hover:underline">
                ← Return to LegalMetriX Workbench
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
