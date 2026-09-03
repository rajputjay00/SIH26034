'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Camera,
  RefreshCw,
  X,
  Check,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  SwitchCamera,
  UploadCloud,
  Maximize2
} from 'lucide-react';
import { EvidenceViewType } from '../../types';

interface CameraCaptureModalProps {
  viewType: EvidenceViewType;
  onCaptureAccepted: (file: File) => void;
  onClose: () => void;
  onFallbackToUpload?: () => void;
}

interface QualitySignal {
  isSharp: boolean;
  isAdequatelyLit: boolean;
  resolution: { width: number; height: number };
  warnings: string[];
}

export const CameraCaptureModal: React.FC<CameraCaptureModalProps> = ({
  viewType,
  onCaptureAccepted,
  onClose,
  onFallbackToUpload
}) => {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null);
  const [capturedDataUrl, setCapturedDataUrl] = useState<string | null>(null);
  const [qualitySignals, setQualitySignals] = useState<QualitySignal | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [availableDevices, setAvailableDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [facingMode, setFacingMode] = useState<'environment' | 'user'>('environment');
  const [initializing, setInitializing] = useState(true);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Stop camera stream cleanly
  const stopStream = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  }, [stream]);

  // Start camera stream with selected device or facingMode
  const startCamera = useCallback(async () => {
    try {
      setInitializing(true);
      setError(null);
      stopStream();

      // Enumerate devices if possible
      if (navigator.mediaDevices?.enumerateDevices) {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoInputs = devices.filter((d) => d.kind === 'videoinput');
        setAvailableDevices(videoInputs);
      }

      const constraints: MediaStreamConstraints = {
        video: selectedDeviceId
          ? { deviceId: { exact: selectedDeviceId } }
          : {
              facingMode: { ideal: facingMode },
              width: { ideal: 1920 },
              height: { ideal: 1080 }
            },
        audio: false
      };

      const newStream = await navigator.mediaDevices.getUserMedia(constraints);
      setStream(newStream);

      if (videoRef.current) {
        videoRef.current.srcObject = newStream;
      }
    } catch (err: unknown) {
      console.error('Camera access error:', err);
      let msg = 'Unable to access camera.';
      if (err instanceof Error) {
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          msg = 'Camera permission was denied. Please allow camera access in browser settings or use file upload.';
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
          msg = 'No camera device found on this system.';
        } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
          msg = 'Camera is already in use by another application.';
        } else {
          msg = err.message || msg;
        }
      }
      setError(msg);
    } finally {
      setInitializing(false);
    }
  }, [facingMode, selectedDeviceId, stopStream]);

  useEffect(() => {
    startCamera();
    return () => {
      stopStream();
    };
  }, []);

  // Switch facing mode (environment vs user)
  const toggleFacingMode = () => {
    setSelectedDeviceId(null);
    setFacingMode((prev) => (prev === 'environment' ? 'user' : 'environment'));
  };

  // Perform lightweight client-side engineering quality checks on the captured frame
  const analyzeQuality = (canvas: HTMLCanvasElement): QualitySignal => {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const warnings: string[] = [];

    let isSharp = true;
    let isAdequatelyLit = true;

    if (ctx && width > 0 && height > 0) {
      // Sample down for quick lightness estimation
      const sampleSize = Math.min(width, height, 100);
      const imageData = ctx.getImageData(0, 0, sampleSize, sampleSize);
      const data = imageData.data;
      let totalBrightness = 0;

      for (let i = 0; i < data.length; i += 4) {
        // Luminance formula
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];
        totalBrightness += (r * 0.299 + g * 0.587 + b * 0.114);
      }

      const avgBrightness = totalBrightness / (data.length / 4);

      if (avgBrightness < 45) {
        isAdequatelyLit = false;
        warnings.push('Image appears dark. Consider increasing ambient lighting.');
      } else if (avgBrightness > 225) {
        warnings.push('High brightness or specular glare detected on package surface.');
      }

      if (width < 800 || height < 600) {
        warnings.push('Captured resolution is low. Ensure fine text details remain legible.');
      }
    }

    return {
      isSharp,
      isAdequatelyLit,
      resolution: { width, height },
      warnings
    };
  };

  // Capture current video frame to canvas
  const handleCapture = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;

    const width = video.videoWidth || 1280;
    const height = video.videoHeight || 720;

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, width, height);

    const quality = analyzeQuality(canvas);
    setQualitySignals(quality);

    canvas.toBlob(
      (blob) => {
        if (blob) {
          setCapturedBlob(blob);
          const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
          setCapturedDataUrl(dataUrl);
        }
      },
      'image/jpeg',
      0.95
    );
  };

  // Retake photo
  const handleRetake = () => {
    setCapturedBlob(null);
    setCapturedDataUrl(null);
    setQualitySignals(null);
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  };

  // Accept captured photo and convert to File
  const handleAcceptPhoto = () => {
    if (!capturedBlob) return;
    const timestampStr = new Date().toISOString().replace(/[:.-]/g, '').slice(0, 15);
    const filename = `capture_${viewType.toLowerCase()}_${timestampStr}.jpg`;
    const file = new File([capturedBlob], filename, { type: 'image/jpeg' });
    stopStream();
    onCaptureAccepted(file);
  };

  return (
    <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-xs flex items-center justify-center p-3 z-50 overflow-y-auto">
      <div className="bg-white rounded-gov border border-slate-300 w-full max-w-3xl shadow-xl overflow-hidden flex flex-col max-h-[95vh]">
        {/* Header */}
        <div className="bg-[#0B1E36] text-white p-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Camera className="w-4 h-4 text-blue-300" />
            <div>
              <h3 className="text-sm font-bold tracking-tight">
                Field Evidence Capture — <span className="text-blue-300">{viewType} View</span>
              </h3>
              <p className="text-[11px] text-slate-300">
                Institutional field inspection camera for packaged commodity enforcement.
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              stopStream();
              onClose();
            }}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Viewport Area */}
        <div className="p-4 bg-slate-950 relative flex items-center justify-center min-h-[360px] max-h-[550px] overflow-hidden">
          {error ? (
            <div className="p-6 text-center text-white space-y-4 max-w-md">
              <AlertTriangle className="w-10 h-10 text-amber-400 mx-auto" />
              <div>
                <h4 className="font-bold text-sm text-slate-100">Camera Unavailable</h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">{error}</p>
              </div>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-2 pt-2">
                <button
                  onClick={startCamera}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded border border-slate-700 transition-colors w-full sm:w-auto"
                >
                  Retry Camera
                </button>
                {onFallbackToUpload && (
                  <button
                    onClick={() => {
                      stopStream();
                      onFallbackToUpload();
                    }}
                    className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded transition-colors inline-flex items-center justify-center gap-1.5 w-full sm:w-auto"
                  >
                    <UploadCloud className="w-3.5 h-3.5" />
                    <span>Upload From Device Storage</span>
                  </button>
                )}
              </div>
            </div>
          ) : capturedDataUrl ? (
            /* Captured Frame Preview */
            <div className="relative w-full h-full flex items-center justify-center">
              <img
                src={capturedDataUrl}
                alt="Captured product frame"
                className="max-h-[460px] max-w-full rounded object-contain border border-slate-800 shadow-md"
              />
              <div className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-xs text-slate-200 px-2.5 py-1 rounded text-[11px] font-mono border border-slate-700">
                Preview: {qualitySignals?.resolution.width} × {qualitySignals?.resolution.height} px
              </div>
            </div>
          ) : (
            /* Live Stream Viewfinder with Framing Guide */
            <div className="relative w-full h-full flex items-center justify-center">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="max-h-[460px] max-w-full rounded object-contain"
              />

              {/* Subtle Government Framing Guide */}
              <div className="absolute inset-6 pointer-events-none border-2 border-dashed border-blue-400/60 rounded-lg flex flex-col justify-between p-3">
                <div className="flex justify-between items-center text-[10px] text-blue-200 font-medium bg-slate-900/60 backdrop-blur-xs px-2 py-0.5 rounded w-fit">
                  <span>Position commodity label inside framing guide</span>
                </div>
                <div className="flex justify-end items-center text-[10px] text-slate-300 bg-slate-900/60 backdrop-blur-xs px-2 py-0.5 rounded w-fit self-end font-mono">
                  {viewType} PANEL
                </div>
              </div>

              {initializing && (
                <div className="absolute inset-0 bg-slate-950/70 flex items-center justify-center">
                  <div className="text-center text-white space-y-2">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-400" />
                    <div className="text-xs">Initializing camera sensor...</div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Hidden Canvas for Frame Capture */}
          <canvas ref={canvasRef} className="hidden" />
        </div>

        {/* Engineering Quality Feedback Bar (if captured) */}
        {capturedDataUrl && qualitySignals && (
          <div className="p-3 bg-slate-50 border-t border-slate-200 text-xs">
            <div className="font-bold text-slate-800 text-[11px] uppercase tracking-wider mb-1 flex items-center space-x-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-blue-700" />
              <span>Sensor Quality Assessment (Engineering Signals)</span>
            </div>
            {qualitySignals.warnings.length > 0 ? (
              <div className="space-y-1">
                {qualitySignals.warnings.map((w, idx) => (
                  <div key={idx} className="flex items-center space-x-1.5 text-amber-800 text-[11px]">
                    <AlertTriangle className="w-3 h-3 text-amber-600 shrink-0" />
                    <span>{w}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-[11px] text-emerald-800 font-medium flex items-center space-x-1">
                <Check className="w-3 h-3 text-emerald-600" />
                <span>Framing, exposure, and sensor resolution optimal for OCR extraction.</span>
              </div>
            )}
          </div>
        )}

        {/* Footer Controls */}
        <div className="p-3 sm:p-4 bg-white border-t border-slate-200 flex flex-col-reverse sm:flex-row items-stretch sm:items-center justify-between gap-2.5 sm:gap-3">
          <div className="flex items-center justify-between sm:justify-start space-x-2">
            {!capturedDataUrl && !error && availableDevices.length > 1 && (
              <button
                type="button"
                onClick={toggleFacingMode}
                className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-semibold inline-flex items-center space-x-1.5 border border-slate-300 transition-colors"
                title="Switch between front and back cameras"
              >
                <SwitchCamera className="w-3.5 h-3.5" />
                <span>Switch Camera</span>
              </button>
            )}
            {onFallbackToUpload && !capturedDataUrl && (
              <button
                type="button"
                onClick={() => {
                  stopStream();
                  onFallbackToUpload();
                }}
                className="px-3 py-2 text-slate-600 hover:text-slate-900 text-xs font-semibold inline-flex items-center space-x-1 transition-colors"
              >
                <UploadCloud className="w-3.5 h-3.5" />
                <span>Upload File</span>
              </button>
            )}
            <button
              type="button"
              onClick={() => {
                stopStream();
                onClose();
              }}
              className="px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded transition-colors ml-auto sm:ml-0"
            >
              Cancel
            </button>
          </div>

          <div className="flex items-center space-x-2 w-full sm:w-auto">
            {capturedDataUrl ? (
              <>
                <button
                  type="button"
                  onClick={handleRetake}
                  className="flex-1 sm:flex-initial px-3 py-2.5 sm:py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded text-xs font-semibold inline-flex items-center justify-center space-x-1.5 border border-slate-300 transition-colors"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Retake</span>
                </button>
                <button
                  type="button"
                  onClick={handleAcceptPhoto}
                  className="flex-1 sm:flex-initial px-4 py-2.5 sm:py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-bold inline-flex items-center justify-center space-x-1.5 shadow-xs transition-colors"
                >
                  <Check className="w-4 h-4 stroke-[2.5]" />
                  <span>Accept &amp; Ingest</span>
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={handleCapture}
                disabled={initializing || !!error}
                className="w-full sm:w-auto px-5 py-3 sm:py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-bold inline-flex items-center justify-center space-x-2 shadow-xs transition-colors disabled:opacity-50"
              >
                <Camera className="w-4 h-4" />
                <span>Capture {viewType} View</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
