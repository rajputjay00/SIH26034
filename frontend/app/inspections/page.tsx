'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Search,
  Filter,
  RefreshCw,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Layers,
  Inbox,
  FileCheck,
  SlidersHorizontal,
  Plus,
  Camera,
  FolderPlus
} from 'lucide-react';
import { Badge } from '../../components/ui/Badge';
import { InspectionSummaryItem } from '../../types';
import { fetchInspectionsSummary, createInspectionCase } from '../../lib/api';
import { formatDateTime } from '../../lib/utils';

type QueueTab = 'ALL' | 'PROCESSING' | 'PENDING_REVIEW' | 'REQUIRES_REVIEW' | 'READY_FOR_FINALISATION' | 'FINALISED';

export default function InspectionsPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<QueueTab>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [determinationFilter, setDeterminationFilter] = useState('');
  const [officerFilter, setOfficerFilter] = useState('');
  const [items, setItems] = useState<InspectionSummaryItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const pageSize = 20;

  // New Inspection Modal State
  const [showModal, setShowModal] = useState(false);
  const [caseNotes, setCaseNotes] = useState('');
  const [creating, setCreating] = useState(false);

  const loadInspections = async () => {
    try {
      setLoading(true);
      const res = await fetchInspectionsSummary({
        review_queue: activeTab === 'ALL' ? undefined : activeTab,
        determination: determinationFilter || undefined,
        officer_id: officerFilter || undefined,
        search: searchQuery || undefined,
        limit: pageSize,
        offset: page * pageSize
      });
      setItems(res.items || []);
      setTotalCount(res.total || 0);
    } catch (err) {
      console.error('Failed to load inspections:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInspections();
  }, [activeTab, determinationFilter, officerFilter, page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    loadInspections();
  };

  const handleCreateCase = async () => {
    try {
      setCreating(true);
      const created = await createInspectionCase(caseNotes || 'Packaged commodity sample inspection');
      setShowModal(false);
      setCaseNotes('');
      router.push(`/cases/${created.inspection_id}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Creation failed';
      alert(message);
    } finally {
      setCreating(false);
    }
  };

  const tabs: { id: QueueTab; label: string; countSuffix?: string }[] = [
    { id: 'ALL', label: 'All Inspections' },
    { id: 'PROCESSING', label: 'Processing' },
    { id: 'PENDING_REVIEW', label: 'Pending Review' },
    { id: 'REQUIRES_REVIEW', label: 'Requires Review (Ambiguity)' },
    { id: 'READY_FOR_FINALISATION', label: 'Ready For Finalisation' },
    { id: 'FINALISED', label: 'Finalised' },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 md:px-8 py-6">
      {/* Header */}
      <div className="bg-white rounded-brand border border-slate-200 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 bg-blue-50 px-2.5 py-1 rounded text-xs text-blue-900 font-semibold mb-1 border border-blue-200">
            <Layers className="w-3.5 h-3.5 text-blue-700" />
            <span>Official Legal Metrology Register</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Officer Review Console &amp; Inspection History
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Audit register of all packaged commodity enforcement cases with deterministic statutory findings.
          </p>
        </div>
        <div className="flex items-center space-x-2.5">
          <button
            onClick={loadInspections}
            className="inline-flex items-center space-x-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-2 rounded-brand transition-colors border border-slate-300"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center space-x-1.5 bg-nirikshan-saffron hover:bg-nirikshan-saffron/90 text-white text-xs font-bold px-4 py-2 rounded-brand transition-colors shadow-xs"
          >
            <Plus className="w-4 h-4" />
            <span>+ Start New Inspection</span>
          </button>
        </div>
      </div>

      {/* Queue Tabs */}
      <div className="flex border-b border-slate-200 bg-white px-3 rounded-t-brand overflow-x-auto">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setPage(0);
              }}
              className={`px-4 py-3 text-xs font-semibold border-b-2 whitespace-nowrap transition-colors ${
                isActive
                  ? 'border-blue-700 text-blue-900 bg-blue-50/40'
                  : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white p-4 rounded-b-brand border-x border-b border-slate-200 shadow-xs">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="relative md:col-span-2">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search Case Number, Commodity, or Officer..."
              className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-slate-800 outline-hidden"
            />
          </div>

          <div>
            <select
              value={determinationFilter}
              onChange={(e) => {
                setDeterminationFilter(e.target.value);
                setPage(0);
              }}
              className="w-full py-2 px-3 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-slate-800 outline-hidden bg-white"
            >
              <option value="">All Determinations</option>
              <option value="COMPLIANT">✓ COMPLIANT</option>
              <option value="NON_COMPLIANT">✕ NON-COMPLIANT</option>
              <option value="REQUIRES_REVIEW">⚠ REQUIRES REVIEW</option>
              <option value="PENDING_EVALUATION">○ PENDING EVALUATION</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <button
              type="submit"
              className="flex-1 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs py-2 rounded transition-colors"
            >
              Apply Filter
            </button>
            {(searchQuery || determinationFilter || officerFilter) && (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery('');
                  setDeterminationFilter('');
                  setOfficerFilter('');
                  setPage(0);
                }}
                className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded text-xs font-semibold"
              >
                Clear
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Inspections Table */}
      <div className="bg-white rounded-brand border border-slate-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">
            <RefreshCw className="w-8 h-8 mx-auto animate-spin mb-3 text-blue-600" />
            <div className="text-xs font-semibold">Loading Inspection Queue...</div>
          </div>
        ) : items.length > 0 ? (
          <>
            {/* MOBILE VIEW: Stacked Case Cards */}
            <div className="sm:hidden divide-y divide-slate-200">
              {items.map((item) => (
                <div key={item.inspection_id} className="p-4 space-y-3 hover:bg-slate-50/50 transition-colors">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <Link
                        href={`/cases/${item.inspection_id}`}
                        className="font-bold text-nirikshan-navy hover:text-nirikshan-blue text-sm break-all"
                      >
                        {item.case_number}
                      </Link>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        {formatDateTime(item.created_at)} • Officer: <span className="text-slate-700 font-medium">{item.officer_id}</span>
                      </div>
                    </div>
                    <Badge status={item.status} />
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs bg-slate-50 p-2.5 rounded border border-slate-100">
                    <div className="flex items-center space-x-1">
                      <span className="font-bold text-slate-700">{item.evidence_count}</span>
                      <span className="text-slate-500 text-[11px]">evidence views</span>
                    </div>

                    <div className="flex items-center space-x-1.5 text-[11px]">
                      <span className="text-emerald-700 font-medium">✓ {item.pass_count}</span>
                      <span className="text-slate-300">•</span>
                      <span className="text-rose-700 font-medium">✕ {item.fail_count}</span>
                      <span className="text-slate-300">•</span>
                      <span className="text-amber-700 font-medium">△ {item.review_count}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between gap-2 pt-1">
                    <div className="text-[11px]">
                      <span className="text-slate-400 mr-1">Result:</span>
                      <Badge status={item.overall_determination || 'PENDING_EVALUATION'} />
                    </div>

                    <Link
                      href={`/cases/${item.inspection_id}`}
                      className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 bg-nirikshan-navy text-white text-xs font-bold rounded-brand hover:bg-nirikshan-navyDark transition-colors shadow-2xs"
                    >
                      <span>Open Case</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>

            {/* DESKTOP VIEW: Structured Register Table */}
            <div className="hidden sm:block overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                    <th className="p-3">Case Number</th>
                    <th className="p-3">Created Date</th>
                    <th className="p-3">Assigned Officer</th>
                    <th className="p-3">Evidence</th>
                    <th className="p-3">Rule Breakdown</th>
                    <th className="p-3">Statutory Determination</th>
                    <th className="p-3">Status</th>
                    <th className="p-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {items.map((item) => (
                    <tr key={item.inspection_id} className="hover:bg-blue-50/40 transition-colors">
                      <td className="p-3">
                        <Link
                          href={`/cases/${item.inspection_id}`}
                          className="font-semibold text-nirikshan-navy hover:text-nirikshan-blue hover:underline text-xs"
                        >
                          {item.case_number}
                        </Link>
                      </td>
                      <td className="p-3 text-slate-600">
                        {formatDateTime(item.created_at)}
                      </td>
                      <td className="p-3 font-medium text-slate-700">
                        {item.officer_id}
                      </td>
                      <td className="p-3">
                        <span className="font-semibold text-slate-800">{item.evidence_count}</span>
                        <span className="text-slate-400 text-[10px] ml-1">views</span>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center space-x-1.5 text-[11px]">
                          <span className="text-emerald-700 font-medium" title="Passed Rules">✓ {item.pass_count} Pass</span>
                          <span className="text-slate-300">•</span>
                          <span className="text-rose-700 font-medium" title="Failed Rules">✕ {item.fail_count} Fail</span>
                          <span className="text-slate-300">•</span>
                          <span className="text-amber-700 font-medium" title="Requires Review">△ {item.review_count} Review</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <Badge status={item.overall_determination || 'PENDING_EVALUATION'} />
                      </td>
                      <td className="p-3">
                        <Badge status={item.status} />
                      </td>
                      <td className="p-3 text-right">
                        <Link
                          href={`/cases/${item.inspection_id}`}
                          className="inline-flex items-center space-x-1 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-900 border border-blue-200 rounded font-semibold text-xs transition-colors"
                        >
                          <span>Open Workbench</span>
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <div className="p-16 text-center text-slate-400 space-y-4">
            <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center mx-auto text-blue-600">
              <Camera className="w-6 h-6 text-nirikshan-blue" />
            </div>
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-slate-800">No inspections recorded in this view</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Begin a new packaged commodity compliance inspection by capturing or uploading product packaging photos.
              </p>
            </div>
            <button
              onClick={() => setShowModal(true)}
              className="inline-flex items-center space-x-1.5 bg-nirikshan-navy hover:bg-nirikshan-navyDark text-white text-xs font-bold px-4 py-2.5 rounded-brand transition-colors shadow-xs"
            >
              <Plus className="w-4 h-4 text-nirikshan-saffron" />
              <span>Start New Inspection</span>
            </button>
          </div>
        )}
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
                Start New Inspection Case
              </h3>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Initialize a new statutory verification record. You will be taken directly to the evidence capture workbench to photograph product packaging.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-nirikshan-navy mb-1">
                  Commodity Sample Description / Location Notes
                </label>
                <textarea
                  value={caseNotes}
                  onChange={(e) => setCaseNotes(e.target.value)}
                  placeholder="e.g. 500g Whole Wheat Flour packet sampled from Retail Mart, Shelf 3"
                  className="w-full text-xs p-3 border border-slate-200 rounded-brand focus:ring-2 focus:ring-nirikshan-blue/30 focus:border-nirikshan-blue outline-hidden"
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
                <span>Initialize &amp; Capture Photo</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
