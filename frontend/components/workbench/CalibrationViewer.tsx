'use client';

import React, { useState } from 'react';
import { CalibrationData, VisualMeasurement, VisualAnomaly } from '@/types';
import {
  calibrateEvidence,
  measureEvidenceFonts,
  detectVisualAnomalies
} from '@/lib/api';

interface CalibrationViewerProps {
  inspectionId: string;
  evidenceId: string;
  calibration?: CalibrationData;
  measurements: VisualMeasurement[];
  anomalies: VisualAnomaly[];
  onRefresh: () => void;
}

export default function CalibrationViewer({
  inspectionId,
  evidenceId,
  calibration,
  measurements,
  anomalies,
  onRefresh
}: CalibrationViewerProps) {
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleCalibrate = async () => {
    setLoadingAction('calibrate');
    setErrorMsg(null);
    try {
      await calibrateEvidence(inspectionId, evidenceId);
      onRefresh();
    } catch (e: any) {
      setErrorMsg(e.message || 'Calibration failed');
    } finally {
      setLoadingAction(null);
    }
  };

  const handleMeasureFonts = async () => {
    setLoadingAction('measure');
    setErrorMsg(null);
    try {
      await measureEvidenceFonts(inspectionId, evidenceId);
      onRefresh();
    } catch (e: any) {
      setErrorMsg(e.message || 'Font measurement failed');
    } finally {
      setLoadingAction(null);
    }
  };

  const handleDetectAnomalies = async () => {
    setLoadingAction('anomaly');
    setErrorMsg(null);
    try {
      await detectVisualAnomalies(inspectionId, evidenceId);
      onRefresh();
    } catch (e: any) {
      setErrorMsg(e.message || 'Anomaly detection failed');
    } finally {
      setLoadingAction(null);
    }
  };

  const isCalibrated = calibration && calibration.status === 'CALIBRATED';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-6 text-slate-200">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            Physical Calibration & Visual Forensic Forecaster
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Indian ₹5 Coin Standard (23.00mm) Reference & Millimeter Font Height Verification
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleCalibrate}
            disabled={loadingAction !== null}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-xs font-semibold text-white rounded-lg transition-colors shadow-sm"
          >
            {loadingAction === 'calibrate' ? 'Calibrating...' : 'Calibrate ₹5 Coin'}
          </button>
          <button
            onClick={handleMeasureFonts}
            disabled={loadingAction !== null}
            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-xs font-semibold text-white rounded-lg transition-colors shadow-sm"
          >
            {loadingAction === 'measure' ? 'Measuring...' : 'Measure Font Heights'}
          </button>
          <button
            onClick={handleDetectAnomalies}
            disabled={loadingAction !== null}
            className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-xs font-semibold text-white rounded-lg transition-colors shadow-sm"
          >
            {loadingAction === 'anomaly' ? 'Scanning...' : 'Scan Sticker Overlays'}
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 bg-red-950/50 border border-red-800/80 rounded-lg text-xs text-red-300">
          {errorMsg}
        </div>
      )}

      {/* Calibration Status Badge */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-800/60 border border-slate-700/60 rounded-lg p-4">
          <span className="text-xs text-slate-400 block font-medium">Reference Calibration</span>
          <div className="mt-2 flex items-center gap-2">
            <span
              className={`px-2.5 py-0.5 rounded text-xs font-bold ${
                isCalibrated
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-700/60'
                  : calibration?.status === 'AMBIGUOUS_CALIBRATION'
                  ? 'bg-amber-950 text-amber-300 border border-amber-700/60'
                  : 'bg-slate-800 text-slate-400 border border-slate-700'
              }`}
            >
              {calibration ? calibration.status : 'UNCALIBRATED'}
            </span>
          </div>
          {isCalibrated && calibration.mm_per_pixel && (
            <p className="text-xs text-slate-300 mt-2">
              Scale Factor: <span className="text-emerald-400 font-bold">{calibration.mm_per_pixel.toFixed(4)}</span> mm/px
              (Conf: {Math.round(calibration.confidence * 100)}%)
            </p>
          )}
        </div>

        <div className="bg-slate-800/60 border border-slate-700/60 rounded-lg p-4">
          <span className="text-xs text-slate-400 block font-medium">Physical Font Measurements</span>
          <div className="mt-2 text-xl font-bold text-white">
            {measurements.filter((m) => m.status === 'MEASURED').length}
            <span className="text-xs font-normal text-slate-400 ml-1">/ {measurements.length} regions</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {isCalibrated ? 'Physical heights computed in mm' : 'Pending physical coin calibration'}
          </p>
        </div>

        <div className="bg-slate-800/60 border border-slate-700/60 rounded-lg p-4">
          <span className="text-xs text-slate-400 block font-medium">Visual Sticker / Overlay Suspicion</span>
          <div className="mt-2 flex items-center gap-2">
            {anomalies.length > 0 ? (
              <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-amber-950 text-amber-300 border border-amber-700/60">
                {anomalies.length} SUSPECTED OVERLAY(S)
              </span>
            ) : (
              <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-slate-800 text-slate-400 border border-slate-700">
                NO ANOMALIES DETECTED
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Visual suspicion only — requires officer verification
          </p>
        </div>
      </div>

      {/* Visual Anomaly Notice Alert */}
      {anomalies.length > 0 && (
        <div className="p-4 bg-amber-950/40 border border-amber-800/70 rounded-lg space-y-2">
          <div className="flex items-center gap-2 text-amber-300 font-bold text-xs">
            <span className="text-base">⚠️</span> Visual Anomaly Detected: Suspected Price Sticker / Alteration Patch
          </div>
          <p className="text-xs text-amber-200/90 leading-relaxed">
            OpenCV edge discontinuity analysis detected an adhesive label boundary over the package print.
            Per Legal Metrology Act & Rule 6(2), stickers require authoritative officer inspection to determine
            whether the overlay constitutes an unlawful price alteration or a legitimate authorized label.
          </p>
          <div className="mt-2 space-y-1">
            {anomalies.map((a) => (
              <div key={a.anomaly_id} className="text-xs text-amber-300/80 bg-amber-900/30 p-2 rounded">
                • {a.anomaly_type} (Confidence: {Math.round(a.confidence * 100)}%) — Bounding: {JSON.stringify(a.bounding_box_json)}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Principal Display Panel (PDP) Area Status Banner */}
      <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-300">Principal Display Panel Area (A)</span>
          <span className="text-xs font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
            {measurements.find((m) => m.pdp_area_cm2)?.pdp_area_cm2
              ? `${measurements.find((m) => m.pdp_area_cm2)?.pdp_area_cm2} cm²`
              : 'Not established'}
          </span>
        </div>
        <p className="text-[11px] text-slate-400">
          Principal Display Panel area is required under Rule 7 Table 1 to establish statutory font-height thresholds. 2D camera images cannot automatically infer 3D package surface area.
        </p>
      </div>

      {/* Font Measurement Results Table */}
      {measurements.length > 0 && (
        <div className="space-y-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              OCR Text Regions & Physical Character Heights
            </h4>
            <span className="text-[10px] text-slate-400 italic">
              Computer vision provides physical measurements. Legal compliance is determined only through verified statutory configuration.
            </span>
          </div>
          <div className="overflow-x-auto max-h-60 overflow-y-auto border border-slate-800 rounded-lg">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800 text-slate-400 uppercase text-[10px] sticky top-0">
                <tr>
                  <th className="py-2 px-3">Target Text</th>
                  <th className="py-2 px-3">Character Type</th>
                  <th className="py-2 px-3">Pixel Height</th>
                  <th className="py-2 px-3">Physical Height (mm)</th>
                  <th className="py-2 px-3">Measurement Status</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-800 text-slate-300">
                {measurements.map((m) => (
                  <tr key={m.measurement_id} className="hover:bg-slate-800/40">
                    <td className="py-2 px-3 font-medium max-w-xs truncate">{m.target_text}</td>
                    <td className="py-2 px-3">
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {m.character_type || 'UNKNOWN'}
                      </span>
                    </td>
                    <td className="py-2 px-3 font-medium">{m.pixel_value} px</td>
                    <td className="py-2 px-3 font-bold text-emerald-400">
                      {m.physical_value !== null && m.physical_value !== undefined
                        ? `${m.physical_value.toFixed(2)} mm`
                        : '—'}
                    </td>

                    <td className="py-2 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          m.status === 'MEASURED'
                            ? 'bg-emerald-950 text-emerald-400'
                            : 'bg-amber-950 text-amber-400'
                        }`}
                      >
                        {m.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

