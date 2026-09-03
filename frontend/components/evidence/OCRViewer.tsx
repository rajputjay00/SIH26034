import React, { useState } from 'react';
import { X, Layers, CheckCircle, AlertTriangle, ShieldCheck, Tag } from 'lucide-react';
import { EvidenceItem, OCRResult, OCRBoundingBox } from '../../types';

interface OCRViewerProps {
  evidence: EvidenceItem;
  ocrResults: OCRResult[];
  onClose: () => void;
}

export const OCRViewer: React.FC<OCRViewerProps> = ({ evidence, ocrResults, onClose }) => {
  const [selectedBoxIndex, setSelectedBoxIndex] = useState<number | null>(null);
  const activeOCR = ocrResults[0] || null;
  const boxes: OCRBoundingBox[] = activeOCR ? activeOCR.boxes_json : [];

  const imgSrc = evidence.file_reference
    ? `http://127.0.0.1:8000/${evidence.file_reference.replace(/\\/g, '/')}`
    : '';

  const imgWidth = evidence.dimensions_json?.width || 800;
  const imgHeight = evidence.dimensions_json?.height || 600;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
      <div className="bg-white rounded-gov border border-gov-border max-w-5xl w-full max-h-[90vh] flex flex-col shadow-lg overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-3.5 border-b border-gov-border flex items-center justify-between bg-gov-bg">
          <div className="flex items-center space-x-3">
            <span className="text-xs font-bold text-gov-navy bg-white px-2.5 py-1 rounded border border-gov-border">
              {evidence.view_type} PANEL
            </span>
            <div>
              <h3 className="text-sm font-semibold text-gov-navy">
                OCR Perception & Bounding Box Inspection
              </h3>
              <p className="text-[11px] text-gov-muted mono-code">
                Evidence ID: {evidence.evidence_id} | SHA-256: {evidence.sha256.slice(0, 16)}...
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-gov hover:bg-slate-200 text-gov-muted hover:text-gov-text transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 overflow-hidden">
          {/* Left / Center Viewport (2 cols) */}
          <div className="lg:col-span-2 bg-slate-900 p-4 flex items-center justify-center overflow-auto relative">
            {imgSrc ? (
              <div className="relative inline-block max-w-full max-h-[70vh]">
                <img
                  src={imgSrc}
                  alt={evidence.original_filename}
                  className="max-h-[68vh] object-contain rounded-gov select-none"
                />

                {/* SVG Overlay for OCR Bounding Boxes */}
                <svg
                  className="absolute inset-0 w-full h-full pointer-events-none"
                  viewBox={`0 0 ${imgWidth} ${imgHeight}`}
                  preserveAspectRatio="xMidYMid meet"
                >
                  {boxes.map((b, idx) => {
                    if (!b.bbox || b.bbox.length < 4) return null;
                    const pointsStr = b.bbox.map((p) => `${p[0]},${p[1]}`).join(' ');
                    const isSelected = selectedBoxIndex === idx;

                    return (
                      <g key={idx} className="pointer-events-auto cursor-pointer" onClick={() => setSelectedBoxIndex(idx)}>
                        <polygon
                          points={pointsStr}
                          fill={isSelected ? 'rgba(37, 99, 235, 0.35)' : 'rgba(16, 185, 129, 0.15)'}
                          stroke={isSelected ? '#2563EB' : '#10B981'}
                          strokeWidth="2"
                          strokeDasharray={isSelected ? 'none' : '4,2'}
                        />
                        <text
                          x={b.bbox[0][0]}
                          y={Math.max(12, b.bbox[0][1] - 4)}
                          fill="#FFFFFF"
                          fontSize="14"
                          fontWeight="600"
                          className="mono-code"
                          filter="drop-shadow(0px 1px 2px rgba(0,0,0,0.8))"
                        >
                          #{idx + 1}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            ) : (
              <div className="text-white text-xs">No image preview available</div>
            )}
          </div>

          {/* Right Panel: Extraction List & Quality Diagnostics (1 col) */}
          <div className="border-l border-gov-border p-4 overflow-y-auto space-y-4 bg-white">
            {/* Image Quality Summary */}
            <div className="bg-gov-bg p-3 rounded-gov border border-gov-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-gov-text">Quality Assessment</span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                    evidence.quality_verdict === 'PASS'
                      ? 'bg-gov-pastelGreen text-green-800 border-green-200'
                      : 'bg-gov-pastelAmber text-amber-900 border-amber-300'
                  }`}
                >
                  {evidence.quality_verdict}
                </span>
              </div>
              {evidence.quality_report_json && (
                <div className="grid grid-cols-3 gap-1 text-[11px] mono-code text-gov-muted pt-1 border-t border-gov-border">
                  <div>Blur: {evidence.quality_report_json.blur_score}</div>
                  <div>Bri: {evidence.quality_report_json.brightness_score}</div>
                  <div>Con: {evidence.quality_report_json.contrast_score}</div>
                </div>
              )}
            </div>

            {/* OCR Extracted Text Regions */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-gov-navy">
                  Detected Text Spans ({boxes.length} Boxes)
                </span>
                {activeOCR && (
                  <span className="text-[10px] mono-code text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                    {activeOCR.engine} ({activeOCR.processing_time_ms}ms)
                  </span>
                )}
              </div>

              <div className="space-y-1.5 max-h-[42vh] overflow-y-auto pr-1">
                {boxes.map((b, idx) => {
                  const isSelected = selectedBoxIndex === idx;
                  return (
                    <div
                      key={idx}
                      onClick={() => setSelectedBoxIndex(idx)}
                      className={`p-2.5 rounded-gov border text-xs cursor-pointer transition-all ${
                        isSelected
                          ? 'border-gov-primary bg-gov-pastelBlue font-medium text-gov-navy ring-1 ring-gov-primary'
                          : 'border-gov-border hover:bg-slate-50 text-gov-text'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-gov-primary text-[11px]">#{idx + 1}</span>
                        <div className="flex items-center space-x-2 text-[10px] mono-code text-gov-muted">
                          <span>Conf: {(b.confidence * 100).toFixed(1)}%</span>
                          {b.char_height_px && <span>H: {b.char_height_px}px</span>}
                        </div>
                      </div>
                      <div className="text-xs font-mono bg-white p-1.5 rounded border border-slate-200 break-words">
                        {b.text}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-2.5 border-t border-gov-border bg-gov-bg flex items-center justify-between text-xs text-gov-muted">
          <div>Phase 2 Machine Perception Output — OCR Text & Geometry Only</div>
          <button
            onClick={onClose}
            className="bg-gov-navy text-white px-4 py-1.5 rounded-gov text-xs font-semibold hover:bg-blue-900 transition-colors"
          >
            Close Viewer
          </button>
        </div>
      </div>
    </div>
  );
};
