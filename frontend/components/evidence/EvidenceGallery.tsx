import React from 'react';
import { ShieldCheck, Play, RefreshCw, Eye, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { EvidenceItem } from '../../types';
import { formatDateTime, truncateHash } from '../../lib/utils';

interface EvidenceGalleryProps {
  items: EvidenceItem[];
  onSelectInspect: (item: EvidenceItem) => void;
  onProcessOCR: (item: EvidenceItem) => void;
  processingId: string | null;
}

export const EvidenceGallery: React.FC<EvidenceGalleryProps> = ({
  items,
  onSelectInspect,
  onProcessOCR,
  processingId,
}) => {
  if (items.length === 0) {
    return (
      <div className="bg-white border border-gov-border rounded-gov p-8 text-center text-xs text-gov-muted space-y-2 shadow-xs">
        <ShieldCheck className="w-8 h-8 text-slate-300 mx-auto" />
        <div className="font-semibold text-gov-text">No Evidence Ingested Yet</div>
        <p className="max-w-md mx-auto">
          Upload Front and Back mandatory package evidence panels above to start quality checks and OCR extraction.
        </p>
      </div>
    );
  }

  const getQualityBadge = (verdict: string) => {
    switch (verdict) {
      case 'PASS':
        return <span className="bg-gov-pastelGreen text-green-800 border border-green-200 px-2 py-0.5 rounded text-[10px] font-semibold flex items-center space-x-1"><CheckCircle2 className="w-3 h-3 text-green-600"/><span>Quality: Pass</span></span>;
      case 'WARN':
        return <span className="bg-gov-pastelAmber text-amber-900 border border-amber-300 px-2 py-0.5 rounded text-[10px] font-semibold flex items-center space-x-1"><AlertTriangle className="w-3 h-3 text-amber-600"/><span>Quality: Warning</span></span>;
      case 'FAIL':
        return <span className="bg-gov-warningLight text-gov-warning border border-red-200 px-2 py-0.5 rounded text-[10px] font-semibold flex items-center space-x-1"><AlertTriangle className="w-3 h-3 text-red-600"/><span>Quality: Failed</span></span>;
      default:
        return <span className="bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded text-[10px] font-medium">Unchecked</span>;
    }
  };

  const getProcessingBadge = (status: string) => {
    switch (status) {
      case 'OCR_COMPLETE':
        return <span className="bg-gov-pastelBlue text-gov-navy border border-blue-200 px-2 py-0.5 rounded text-[10px] font-semibold">OCR Complete</span>;
      case 'OCR_PROCESSING':
      case 'PREPROCESSING':
      case 'QUALITY_CHECK':
        return <span className="bg-purple-50 text-purple-800 border border-purple-200 px-2 py-0.5 rounded text-[10px] font-semibold animate-pulse">Processing...</span>;
      case 'MANUAL_REVIEW':
        return <span className="bg-amber-50 text-amber-900 border border-amber-300 px-2 py-0.5 rounded text-[10px] font-semibold">Manual Review</span>;
      case 'OCR_FAILED':
        return <span className="bg-red-50 text-red-800 border border-red-200 px-2 py-0.5 rounded text-[10px] font-semibold">OCR Failed</span>;
      default:
        return <span className="bg-slate-50 text-slate-600 border border-slate-200 px-2 py-0.5 rounded text-[10px] font-medium">Ingested</span>;
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gov-navy tracking-tight">
            Evidence Ingestion Register ({items.length} Views Ingested)
          </h3>
          <p className="text-xs text-gov-muted">
            Immutable original evidence items with SHA-256 provenance hashes.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item) => {
          const isProcessing = processingId === item.evidence_id;
          const previewSrc = item.file_reference
            ? `http://127.0.0.1:8000/${item.file_reference.replace(/\\/g, '/')}`
            : '';

          return (
            <div
              key={item.evidence_id}
              className="bg-white border border-gov-border rounded-gov p-4 shadow-xs flex flex-col justify-between space-y-3 hover:border-slate-300 transition-colors"
            >
              {/* Header: View Type & Badges */}
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gov-navy bg-gov-bg px-2.5 py-1 rounded border border-gov-border">
                  {item.view_type} VIEW
                </span>
                <div className="flex items-center space-x-1.5">
                  {getQualityBadge(item.quality_verdict)}
                  {getProcessingBadge(item.processing_status)}
                </div>
              </div>

              {/* Image Preview Thumbnail */}
              <div className="h-40 bg-slate-50 rounded-gov border border-gov-border overflow-hidden flex items-center justify-center relative">
                {previewSrc ? (
                  <img
                    src={previewSrc}
                    alt={item.original_filename}
                    className="w-full h-full object-contain"
                  />
                ) : (
                  <span className="text-xs text-gov-muted">Image preview</span>
                )}
              </div>

              {/* Metadata details */}
              <div className="space-y-1 text-xs text-gov-muted border-t border-gov-border pt-2">
                <div className="flex justify-between">
                  <span>Filename:</span>
                  <span className="font-medium text-gov-text truncate max-w-[160px]">{item.original_filename}</span>
                </div>
                <div className="flex justify-between">
                  <span>SHA-256:</span>
                  <span className="mono-code text-[11px] text-slate-700">{truncateHash(item.sha256, 8)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Ingested At:</span>
                  <span className="text-[11px] text-gov-text">{formatDateTime(item.ingested_at)}</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-2 pt-2 border-t border-gov-border">
                {item.processing_status === 'UPLOADED' || item.processing_status === 'OCR_FAILED' || item.processing_status === 'MANUAL_REVIEW' ? (
                  <button
                    type="button"
                    onClick={() => onProcessOCR(item)}
                    disabled={isProcessing}
                    className="flex-1 inline-flex items-center justify-center space-x-1.5 bg-gov-navy text-white text-xs font-medium py-1.5 rounded-gov hover:bg-blue-900 disabled:opacity-50 transition-colors"
                  >
                    {isProcessing ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Processing...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5" />
                        <span>Run Quality & OCR</span>
                      </>
                    )}
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => onSelectInspect(item)}
                    className="flex-1 inline-flex items-center justify-center space-x-1.5 bg-gov-pastelBlue text-gov-navy border border-blue-200 text-xs font-semibold py-1.5 rounded-gov hover:bg-blue-100 transition-colors"
                  >
                    <Eye className="w-3.5 h-3.5 text-gov-primary" />
                    <span>Inspect OCR & Boxes</span>
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => onProcessOCR(item)}
                  disabled={isProcessing}
                  title="Re-run / Retry processing"
                  className="p-1.5 border border-gov-border rounded-gov hover:bg-gov-bg text-gov-muted hover:text-gov-text transition-colors"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isProcessing ? 'animate-spin' : ''}`} />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
