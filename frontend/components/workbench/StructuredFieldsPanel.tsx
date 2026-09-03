import React, { useState } from 'react';
import { Sparkles, Edit3, ShieldAlert, CheckCircle2, History, AlertCircle, RefreshCw, Layers } from 'lucide-react';
import { ExtractedField } from '../../types';
import { correctFieldValue } from '../../lib/api';

interface StructuredFieldsPanelProps {
  inspectionId: string;
  fields: ExtractedField[];
  onExtract: () => void;
  onFieldUpdated: (updated: ExtractedField) => void;
  extracting: boolean;
}

export const StructuredFieldsPanel: React.FC<StructuredFieldsPanelProps> = ({
  inspectionId,
  fields,
  onExtract,
  onFieldUpdated,
  extracting,
}) => {
  const [editingField, setEditingField] = useState<ExtractedField | null>(null);
  const [correctedValue, setCorrectedValue] = useState('');
  const [correctedUnit, setCorrectedUnit] = useState('');
  const [correctionReason, setCorrectionReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const openCorrectionModal = (field: ExtractedField) => {
    setEditingField(field);
    setCorrectedValue(field.normalized_value || field.raw_value || '');
    setCorrectedUnit(field.unit || '');
    setCorrectionReason('Officer manual review & verification');
  };

  const handleSaveCorrection = async () => {
    if (!editingField) return;
    setSubmitting(true);
    try {
      const updated = await correctFieldValue(inspectionId, editingField.field_id, {
        corrected_value: correctedValue,
        unit: correctedUnit || undefined,
        reason: correctionReason,
      });
      onFieldUpdated(updated);
      setEditingField(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Correction failed';
      alert(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: string, fieldStatus: string) => {
    if (fieldStatus === 'CONFLICTING') {
      return (
        <span className="bg-red-50 text-red-800 border border-red-200 px-2 py-0.5 rounded text-[10px] font-semibold flex items-center space-x-1">
          <ShieldAlert className="w-3 h-3 text-red-600" />
          <span>Conflicting Views</span>
        </span>
      );
    }
    if (status === 'OFFICER_CORRECTED' || fieldStatus === 'CORRECTED') {
      return (
        <span className="bg-purple-50 text-purple-800 border border-purple-200 px-2 py-0.5 rounded text-[10px] font-semibold flex items-center space-x-1">
          <History className="w-3 h-3 text-purple-600" />
          <span>Officer Corrected</span>
        </span>
      );
    }
    return (
      <span className="bg-gov-pastelBlue text-gov-navy border border-blue-200 px-2 py-0.5 rounded text-[10px] font-medium">
        Auto Extracted
      </span>
    );
  };

  return (
    <div className="bg-white border border-gov-border rounded-gov p-5 shadow-xs space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gov-border pb-3">
        <div>
          <h3 className="text-sm font-semibold text-gov-navy flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-gov-primary" />
            <span>Structured Field Declarations ({fields.length} Fields)</span>
          </h3>
          <p className="text-xs text-gov-muted mt-0.5">
            Preserves immutable original OCR text alongside normalized computational quantities.
          </p>
        </div>
        <button
          type="button"
          onClick={onExtract}
          disabled={extracting}
          className="inline-flex items-center space-x-1.5 bg-gov-navy text-white text-xs font-semibold px-3.5 py-2 rounded-gov hover:bg-blue-900 disabled:opacity-50 transition-colors shadow-xs"
        >
          {extracting ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Parsing OCR...</span>
            </>
          ) : (
            <>
              <Layers className="w-3.5 h-3.5" />
              <span>Extract Structured Fields</span>
            </>
          )}
        </button>
      </div>

      {fields.length === 0 ? (
        <div className="py-8 text-center text-xs text-gov-muted bg-gov-bg/50 rounded-gov border border-dashed border-gov-border space-y-2">
          <div>No structured fields parsed yet.</div>
          <p className="max-w-sm mx-auto text-[11px]">
            Ensure package evidence views are ingested &amp; processed via OCR, then click &quot;Extract Structured Fields&quot; above.
          </p>
        </div>
      ) : (
        <>
          {/* MOBILE VIEW: Stacked Responsive Cards */}
          <div className="sm:hidden space-y-3">
            {fields.map((f) => (
              <div
                key={f.field_id}
                className="bg-white border border-slate-200 rounded-brand p-3.5 space-y-2.5 shadow-2xs"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="font-bold text-xs text-nirikshan-navy capitalize">
                    {f.field_name.replace(/_/g, ' ')}
                  </div>
                  {getStatusBadge(f.status, f.field_status)}
                </div>

                <div className="space-y-1.5 text-xs bg-slate-50/70 p-2.5 rounded border border-slate-100">
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-400">Raw OCR Read</div>
                    <div className="text-slate-800 font-medium break-words mt-0.5 leading-snug">
                      {f.raw_value || '—'}
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1 border-t border-slate-200/60">
                    <div>
                      <span className="text-[10px] text-slate-400 font-bold uppercase">Normalized:</span>{' '}
                      <span className="font-bold text-nirikshan-navy">
                        {f.normalized_value || '—'} {f.unit && <span className="text-slate-500 font-normal">{f.unit}</span>}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-500 font-medium">
                      Conf: {f.confidence ? `${(f.confidence * 100).toFixed(1)}%` : '—'}
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => openCorrectionModal(f)}
                  className="w-full inline-flex items-center justify-center space-x-1.5 text-xs text-nirikshan-blue font-semibold bg-blue-50 hover:bg-blue-100 py-2 rounded-brand border border-blue-200 transition-colors"
                >
                  <Edit3 className="w-3.5 h-3.5" />
                  <span>Review / Edit Field</span>
                </button>
              </div>
            ))}
          </div>

          {/* DESKTOP VIEW: Structured Table */}
          <div className="hidden sm:block overflow-x-auto border border-gov-border rounded-gov">
            <table className="w-full text-left text-xs">
              <thead className="bg-gov-bg text-gov-muted font-semibold border-b border-gov-border">
                <tr>
                  <th className="py-2.5 px-3">Field Name</th>
                  <th className="py-2.5 px-3">Raw OCR Value (Preserved)</th>
                  <th className="py-2.5 px-3">Normalized Value</th>
                  <th className="py-2.5 px-3">Confidence</th>
                  <th className="py-2.5 px-3">Origin &amp; Status</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gov-border bg-white">
                {fields.map((f) => (
                  <tr key={f.field_id} className="hover:bg-slate-50/60">
                    <td className="py-2.5 px-3 font-semibold text-gov-navy capitalize">
                      {f.field_name.replace(/_/g, ' ')}
                    </td>
                    <td className="py-2.5 px-3 text-slate-700 max-w-xs break-words" title={f.raw_value}>
                      {f.raw_value || '—'}
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-gov-text">
                      {f.normalized_value ? (
                        <span>
                          {f.normalized_value} {f.unit && <span className="text-gov-muted font-normal text-[11px]">{f.unit}</span>}
                        </span>
                      ) : (
                        <span className="text-gov-muted font-normal">—</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-slate-600 text-[11px] font-medium">
                      {f.confidence ? `${(f.confidence * 100).toFixed(1)}%` : '—'}
                    </td>
                    <td className="py-2.5 px-3">
                      {getStatusBadge(f.status, f.field_status)}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        type="button"
                        onClick={() => openCorrectionModal(f)}
                        className="inline-flex items-center space-x-1 text-xs text-gov-primary font-medium hover:underline bg-gov-pastelBlue/50 hover:bg-gov-pastelBlue px-2.5 py-1 rounded border border-blue-200 transition-colors"
                      >
                        <Edit3 className="w-3 h-3" />
                        <span>Review / Edit</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Manual Officer Correction Modal */}
      {editingField && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-white rounded-gov border border-gov-border max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="border-b border-gov-border pb-3">
              <h4 className="text-sm font-bold text-gov-navy">
                Authoritative Officer Correction — {editingField.field_name.replace(/_/g, ' ').toUpperCase()}
              </h4>
              <p className="text-xs text-gov-muted mt-0.5">
                Manual corrections preserve historical extractions and are recorded in the SHA-256 audit ledger.
              </p>
            </div>

            <div className="space-y-3 text-xs">
              <div className="bg-gov-bg p-3 rounded-gov border border-gov-border">
                <div className="text-gov-muted text-[11px]">Original Raw OCR Value:</div>
                <div className="text-gov-text font-medium mt-0.5">{editingField.raw_value || '—'}</div>
              </div>

              <div>
                <label className="block font-semibold text-gov-text mb-1">Corrected Normalized Value</label>
                <input
                  type="text"
                  value={correctedValue}
                  onChange={(e) => setCorrectedValue(e.target.value)}
                  className="w-full p-2 border border-gov-border rounded-gov focus:ring-1 focus:ring-gov-primary outline-none"
                  placeholder="e.g. 200.00"
                />
              </div>

              <div>
                <label className="block font-semibold text-gov-text mb-1">Statutory Unit</label>
                <input
                  type="text"
                  value={correctedUnit}
                  onChange={(e) => setCorrectedUnit(e.target.value)}
                  className="w-full p-2 border border-gov-border rounded-gov focus:ring-1 focus:ring-gov-primary outline-none"
                  placeholder="e.g. INR, kg, L, N"
                />
              </div>

              <div>
                <label className="block font-semibold text-gov-text mb-1">Reason for Officer Override</label>
                <textarea
                  value={correctionReason}
                  onChange={(e) => setCorrectionReason(e.target.value)}
                  className="w-full p-2 border border-gov-border rounded-gov focus:ring-1 focus:ring-gov-primary outline-none"
                  rows={2}
                  placeholder="Provide authoritative audit reason for this correction"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-gov-border">
              <button
                type="button"
                onClick={() => setEditingField(null)}
                className="px-4 py-2 border border-gov-border rounded-gov text-xs text-gov-text hover:bg-gov-bg"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveCorrection}
                disabled={submitting || !correctedValue}
                className="px-4 py-2 bg-gov-navy text-white rounded-gov text-xs font-semibold hover:bg-blue-900 disabled:opacity-50"
              >
                {submitting ? 'Applying & Logging...' : 'Save Officer Correction'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
