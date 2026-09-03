'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  Plus,
  RefreshCw,
  FolderPlus,
  Inbox,
  Camera,
  Layers,
  Sparkles
} from 'lucide-react';
import {
  DashboardSummary,
  DashboardReviewQueue,
  InspectionSummaryItem
} from '../../types';
import {
  fetchDashboardSummary,
  fetchDashboardReviewQueue,
  fetchInspectionsSummary,
  createInspectionCase
} from '../../lib/api';
import { formatDateTime } from '../../lib/utils';

export const LiveActivityQueues: React.FC = () => {
  const router = useRouter();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [queue, setQueue] = useState<DashboardReviewQueue | null>(null);
  const [recentCases, setRecentCases] = useState<InspectionSummaryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newCaseNotes, setNewCaseNotes] = useState('');
  const [creating, setCreating] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sumData, qData, casesData] = await Promise.all([
        fetchDashboardSummary(),
        fetchDashboardReviewQueue(),
        fetchInspectionsSummary({ limit: 10 })
      ]);
      setSummary(sumData);
      setQueue(qData);
      setRecentCases(casesData.items || []);
    } catch (err) {
      console.error('Failed to load operational queue data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateCase = async () => {
    try {
      setCreating(true);
      const created = await createInspectionCase(newCaseNotes || 'Packaged commodity sample inspection');
      setShowModal(false);
      setNewCaseNotes('');
      // Immediately redirect officer to the new inspection workspace to capture evidence
      router.push(`/cases/${created.inspection_id}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Creation failed';
      alert(message);
    } finally {
      setCreating(false);
    }
  };

  const getStatusBadge = (status: string, determination?: string) => {
    if (status === 'FINALISED') {
      return (
        <span className="inline-flex items-center space-x-1 text-[10px] font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
          <CheckCircle2 className="w-3 h-3 text-slate-500" />
          <span>FINALISED</span>
        </span>
      );
    }
    if (determination === 'NON_COMPLIANT') {
      return (
        <span className="inline-flex items-center space-x-1 text-[10px] font-bold text-red-800 bg-red-50 px-2 py-0.5 rounded border border-red-200">
          <XCircle className="w-3 h-3 text-red-600" />
          <span>NON-COMPLIANT</span>
        </span>
      );
    }
    if (determination === 'REQUIRES_REVIEW') {
      return (
        <span className="inline-flex items-center space-x-1 text-[10px] font-bold text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
          <AlertTriangle className="w-3 h-3 text-amber-600" />
          <span>REQUIRES REVIEW</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 text-[10px] font-bold text-blue-800 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
        <Clock className="w-3 h-3 text-blue-600" />
        <span>{status}</span>
      </span>
    );
  };

  const highPriorityCases = recentCases.filter(
    (c) => c.review_queue === 'HIGH_PRIORITY' || c.overall_determination === 'REQUIRES_REVIEW'
  );
  const readyForFinalisationCases = recentCases.filter(
    (c) => c.review_queue === 'READY_FOR_FINALISATION' || (c.status === 'PENDING_REVIEW' && c.overall_determination === 'COMPLIANT')
  );

  return (
    <section className="py-16 bg-white border-b border-nirikshan-border" id="activity">
      <div className="max-w-7xl mx-auto px-4 md:px-8">
        {/* QUICK START HERO BANNER FOR INSPECTORS */}
        <div className="mb-12 bg-linear-to-r from-nirikshan-navy to-nirikshan-blue text-white rounded-brand p-6 md:p-8 shadow-elevated flex flex-col md:flex-row md:items-center justify-between gap-6 border border-white/10">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center space-x-2 bg-white/15 px-3 py-1 rounded-full text-xs font-semibold backdrop-blur-xs text-nirikshan-saffron">
              <Camera className="w-3.5 h-3.5" />
              <span>FIELD INSPECTION WORKFLOW</span>
            </div>
            <h3 className="text-xl md:text-2xl font-bold tracking-tight">
              Ready to Inspect a Packaged Commodity?
            </h3>
            <p className="text-xs md:text-sm text-slate-200 leading-relaxed">
              Start a new inspection to photograph packaging panels (Front, Back, Side, Base), automatically extract declarations with PaddleOCR, and evaluate Rule 6 &amp; Rule 7 compliance in real-time.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <button
              onClick={() => setShowModal(true)}
              className="inline-flex items-center space-x-2 bg-nirikshan-saffron hover:bg-nirikshan-saffron/90 text-white text-xs md:text-sm font-bold px-5 py-3 rounded-brand transition-all shadow-md transform hover:-translate-y-0.5"
            >
              <Plus className="w-4 h-4" />
              <span>+ Start New Inspection</span>
            </button>
            <Link
              href="/inspections"
              className="inline-flex items-center space-x-1.5 bg-white/10 hover:bg-white/20 text-white text-xs md:text-sm font-semibold px-4 py-3 rounded-brand transition-colors border border-white/20"
            >
              <Layers className="w-4 h-4" />
              <span>View All Cases</span>
            </Link>
          </div>
        </div>

        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div>
            <div className="inline-flex items-center space-x-1.5 bg-slate-100 text-nirikshan-navy px-3 py-1 rounded-full text-xs font-semibold border border-slate-200 mb-2">
              <Clock className="w-3.5 h-3.5 text-nirikshan-blue" />
              <span>LIVE OPERATIONAL QUEUES</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-nirikshan-navy tracking-tight">
              Active Field Inspections &amp; Review Desk
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              Direct database query aggregations for active inspection cases requiring statutory officer review.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={loadData}
              disabled={loading}
              className="p-2 border border-slate-200 rounded-brand text-slate-600 hover:text-nirikshan-navy hover:bg-slate-50 transition-colors"
              title="Refresh Queue Data"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-nirikshan-blue' : ''}`} />
            </button>
            <button
              onClick={() => setShowModal(true)}
              className="inline-flex items-center space-x-1.5 bg-nirikshan-navy hover:bg-nirikshan-navyDark text-white text-xs font-semibold px-4 py-2 rounded-brand transition-colors shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Inspection</span>
            </button>
          </div>
        </div>

        {/* 3 Activity Cards Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Card 1: High Priority Review Queue */}
          <div className="bg-slate-50/80 rounded-brand p-5 border border-slate-200 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-slate-200/80 pb-3 mb-4">
                <div className="flex items-center space-x-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-500"></div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-nirikshan-navy">
                    Review Required
                  </h3>
                </div>
                <span className="text-xs font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  {loading ? '...' : queue?.high_priority_count ?? 0} Cases
                </span>
              </div>

              {loading ? (
                <div className="space-y-3">
                  <div className="h-14 bg-white/70 animate-pulse rounded border border-slate-200/60"></div>
                  <div className="h-14 bg-white/70 animate-pulse rounded border border-slate-200/60"></div>
                </div>
              ) : highPriorityCases.length > 0 ? (
                <div className="space-y-2.5">
                  {highPriorityCases.slice(0, 3).map((c) => (
                    <Link
                      key={c.inspection_id}
                      href={`/cases/${c.inspection_id}`}
                      className="block bg-white p-3 rounded border border-slate-200 hover:border-amber-400 hover:shadow-xs transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-nirikshan-navy">{c.case_number}</span>
                        <span className="text-[10px] text-amber-700 font-medium">Flagged</span>
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1">
                        {c.evidence_count} Evidence • {c.review_count} Review Findings
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-400 text-xs space-y-2">
                  <Inbox className="w-6 h-6 mx-auto text-slate-300" />
                  <div>No cases currently require priority review</div>
                </div>
              )}
            </div>

            <div className="pt-4 mt-4 border-t border-slate-200/60">
              <Link
                href="/inspections"
                className="text-[11px] font-semibold text-nirikshan-blue hover:text-nirikshan-navy flex items-center justify-between"
              >
                <span>View All Review Queues</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Card 2: Ready for Finalisation Queue */}
          <div className="bg-slate-50/80 rounded-brand p-5 border border-slate-200 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-slate-200/80 pb-3 mb-4">
                <div className="flex items-center space-x-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-blue-500"></div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-nirikshan-navy">
                    Ready for Finalisation
                  </h3>
                </div>
                <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                  {loading ? '...' : queue?.ready_for_finalisation_count ?? 0} Cases
                </span>
              </div>

              {loading ? (
                <div className="space-y-3">
                  <div className="h-14 bg-white/70 animate-pulse rounded border border-slate-200/60"></div>
                  <div className="h-14 bg-white/70 animate-pulse rounded border border-slate-200/60"></div>
                </div>
              ) : readyForFinalisationCases.length > 0 ? (
                <div className="space-y-2.5">
                  {readyForFinalisationCases.slice(0, 3).map((c) => (
                    <Link
                      key={c.inspection_id}
                      href={`/cases/${c.inspection_id}`}
                      className="block bg-white p-3 rounded border border-slate-200 hover:border-blue-400 hover:shadow-xs transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-nirikshan-navy">{c.case_number}</span>
                        <span className="text-[10px] text-blue-700 font-medium">Ready</span>
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1">
                        {c.pass_count} Passed • Evaluated
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-400 text-xs space-y-2">
                  <Inbox className="w-6 h-6 mx-auto text-slate-300" />
                  <div>No cases currently awaiting officer signoff</div>
                </div>
              )}
            </div>

            <div className="pt-4 mt-4 border-t border-slate-200/60">
              <Link
                href="/inspections"
                className="text-[11px] font-semibold text-nirikshan-blue hover:text-nirikshan-navy flex items-center justify-between"
              >
                <span>Open Officer Review Desk</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Card 3: Recent Case Activity */}
          <div className="bg-slate-50/80 rounded-brand p-5 border border-slate-200 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-slate-200/80 pb-3 mb-4">
                <div className="flex items-center space-x-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-nirikshan-navy">
                    Recent Inspections
                  </h3>
                </div>
                <span className="text-xs font-semibold text-slate-600 bg-white px-2 py-0.5 rounded border border-slate-200">
                  {recentCases.length} Records
                </span>
              </div>

              {loading ? (
                <div className="space-y-3">
                  <div className="h-14 bg-white/70 animate-pulse rounded border border-slate-200/60"></div>
                  <div className="h-14 bg-white/70 animate-pulse rounded border border-slate-200/60"></div>
                </div>
              ) : recentCases.length > 0 ? (
                <div className="space-y-2.5">
                  {recentCases.slice(0, 3).map((c) => (
                    <Link
                      key={c.inspection_id}
                      href={`/cases/${c.inspection_id}`}
                      className="block bg-white p-3 rounded border border-slate-200 hover:border-nirikshan-blue hover:shadow-xs transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-nirikshan-navy">{c.case_number}</span>
                        {getStatusBadge(c.status, c.overall_determination)}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1">
                        {formatDateTime(c.created_at)} • {c.officer_id}
                      </div>
                    </Link>
                  ))}
                </div>

              ) : (
                <div className="text-center py-6 text-slate-400 text-xs space-y-3">
                  <Inbox className="w-6 h-6 mx-auto text-slate-300" />
                  <div>No inspections recorded in database yet</div>
                  <button
                    onClick={() => setShowModal(true)}
                    className="inline-flex items-center space-x-1 text-xs font-semibold text-nirikshan-blue hover:underline"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Create first inspection</span>
                  </button>
                </div>
              )}
            </div>

            <div className="pt-4 mt-4 border-t border-slate-200/60">
              <Link
                href="/inspections"
                className="text-[11px] font-semibold text-nirikshan-blue hover:text-nirikshan-navy flex items-center justify-between"
              >
                <span>View Full Inspection History</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* CREATE CASE MODAL */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
          <div className="bg-white rounded-brand max-w-md w-full p-6 shadow-elevated border border-slate-200">
            <div className="flex items-center space-x-2 text-nirikshan-navy mb-2">
              <div className="w-7 h-7 rounded-full bg-blue-50 flex items-center justify-center text-nirikshan-blue">
                <FolderPlus className="w-4 h-4" />
              </div>
              <h3 className="text-base font-bold">
                Start New Packaged Commodity Inspection
              </h3>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Initialize a new inspection case. After initialization, you will be taken directly to the evidence capture workbench to photograph or upload packaging panels.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-nirikshan-navy mb-1">
                  Commodity Sample Description / Location Notes
                </label>
                <textarea
                  value={newCaseNotes}
                  onChange={(e) => setNewCaseNotes(e.target.value)}
                  placeholder="e.g. 500g Whole Wheat Flour packet sampled from Retail Mart, Shelf 3"
                  className="w-full text-xs p-3 border border-slate-200 rounded-brand focus:ring-2 focus:ring-nirikshan-blue/30 focus:border-nirikshan-blue outline-none"
                  rows={3}
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 border border-slate-200 text-slate-600 text-xs font-semibold rounded-brand hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateCase}
                disabled={creating}
                className="px-4 py-2 bg-nirikshan-navy hover:bg-nirikshan-navyDark text-white text-xs font-bold rounded-brand transition-colors flex items-center space-x-1.5 shadow-xs"
              >
                {creating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Camera className="w-3.5 h-3.5 text-nirikshan-saffron" />}
                <span>Initialize &amp; Capture Evidence</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
