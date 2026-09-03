'use client';

import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  Image as ImageIcon,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Camera,
  FolderOpen
} from 'lucide-react';
import { EvidenceViewType, EvidenceItem } from '../../types';
import { uploadEvidence } from '../../lib/api';
import { CameraCaptureModal } from './CameraCaptureModal';

interface EvidenceUploaderProps {
  inspectionId: string;
  onUploaded: (item: EvidenceItem) => void;
}

const VIEW_TYPES: { type: EvidenceViewType; label: string; description: string; required?: boolean }[] = [
  { type: 'FRONT', label: 'Front Panel', description: 'Mandatory principal display view', required: true },
  { type: 'BACK', label: 'Back Panel', description: 'Mandatory declarations & MRP view', required: true },
  { type: 'SIDE', label: 'Side Panel', description: 'Optional supplementary declarations' },
  { type: 'BASE', label: 'Base / Bottom', description: 'Optional batch / date marks' },
  { type: 'OTHER', label: 'Other View', description: 'Supplementary evidence angle' },
];

export const EvidenceUploader: React.FC<EvidenceUploaderProps> = ({ inspectionId, onUploaded }) => {
  const [selectedView, setSelectedView] = useState<EvidenceViewType>('FRONT');
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showCameraModal, setShowCameraModal] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    setSuccessMessage(null);
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (!selected.type.startsWith('image/')) {
        setError('Please select a valid image file (JPG, PNG, WebP).');
        return;
      }
      setFile(selected);
      setPreviewUrl(URL.createObjectURL(selected));
    }
  };

  const handleCameraCaptureAccepted = async (capturedFile: File) => {
    setShowCameraModal(false);
    setFile(capturedFile);
    setPreviewUrl(URL.createObjectURL(capturedFile));
    setError(null);
    setSuccessMessage(null);

    // If offline, store in offline queue immediately
    if (typeof navigator !== 'undefined' && !navigator.onLine) {
      try {
        const { OfflineEvidenceQueue } = await import('../../lib/offlineQueue');
        await OfflineEvidenceQueue.enqueue(inspectionId, selectedView, capturedFile);
        setSuccessMessage(`Offline mode: ${selectedView} evidence safely queued locally. It will synchronize automatically when online.`);
        setFile(null);
        setPreviewUrl(null);
      } catch (err: unknown) {
        setError('Failed to queue evidence locally while offline.');
      }
      return;
    }

    // Automatically trigger upload for captured camera photo when online
    setUploading(true);
    try {
      const item = await uploadEvidence(inspectionId, capturedFile, selectedView);
      setSuccessMessage(`Successfully ingested ${selectedView} evidence view from camera.`);
      setFile(null);
      setPreviewUrl(null);
      onUploaded(item);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Upload failed';
      // If network failed during upload attempt, fallback to queueing
      try {
        const { OfflineEvidenceQueue } = await import('../../lib/offlineQueue');
        await OfflineEvidenceQueue.enqueue(inspectionId, selectedView, capturedFile);
        setError(`${message}. Image preserved in offline queue for retry.`);
      } catch {
        setError(message);
      }
    } finally {
      setUploading(false);
    }
  };


  const handleUpload = async () => {
    if (!file) {
      setError('Please select or capture an image file first.');
      return;
    }
    setUploading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const item = await uploadEvidence(inspectionId, file, selectedView);
      setSuccessMessage(`Successfully ingested ${selectedView} evidence view.`);
      setFile(null);
      setPreviewUrl(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      onUploaded(item);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Upload failed';
      setError(message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white border border-gov-border rounded-gov p-5 shadow-xs space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-gov-navy tracking-tight">
            Evidence Intake &amp; View Selection
          </h3>
          <p className="text-xs text-gov-muted mt-0.5">
            Photograph directly using device camera or upload high-resolution images. SHA-256 calculated on server.
          </p>
        </div>

        {/* Primary Action Buttons */}
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={() => setShowCameraModal(true)}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-bold transition-colors shadow-xs"
          >
            <Camera className="w-4 h-4" />
            <span>Take Photo</span>
          </button>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300 rounded text-xs font-semibold transition-colors"
          >
            <FolderOpen className="w-4 h-4 text-slate-600" />
            <span>Upload File</span>
          </button>
        </div>
      </div>

      {/* View Type Selector Tabs */}
      <div>
        <label className="block text-xs font-semibold text-gov-text mb-2">Select Evidence View Role</label>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {VIEW_TYPES.map((v) => (
            <button
              key={v.type}
              type="button"
              onClick={() => setSelectedView(v.type)}
              className={`p-2.5 text-left rounded-gov border transition-all text-xs ${
                selectedView === v.type
                  ? 'border-gov-primary bg-gov-pastelBlue font-semibold text-gov-navy ring-1 ring-gov-primary'
                  : 'border-gov-border hover:bg-gov-bg text-gov-text'
              }`}
            >
              <div className="flex items-center justify-between">
                <span>{v.label}</span>
                {v.required && (
                  <span className="text-[10px] text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded font-semibold">Required</span>
                )}
              </div>
              <div className="text-[10px] text-gov-muted mt-0.5 line-clamp-1">{v.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Drag and drop / file selector area */}
      <div
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-gov p-6 text-center cursor-pointer transition-colors ${
          previewUrl ? 'border-gov-primary bg-slate-50/50' : 'border-gov-border hover:bg-gov-bg/80'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,image/bmp"
          onChange={handleFileChange}
          className="hidden"
        />

        {previewUrl ? (
          <div className="space-y-3">
            <img
              src={previewUrl}
              alt="Evidence Preview"
              className="max-h-48 mx-auto rounded-gov object-contain border border-gov-border shadow-xs"
            />
            <div className="text-xs font-medium text-gov-text">
              {file?.name} ({(file?.size ? file.size / 1024 : 0).toFixed(1)} KB)
            </div>
            <div className="text-[11px] text-gov-primary hover:underline">Click to choose a different image</div>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="w-10 h-10 bg-gov-pastelBlue text-gov-primary rounded-full flex items-center justify-center mx-auto">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div className="text-xs font-semibold text-gov-text">
              Click to select evidence image for <span className="text-gov-primary">{selectedView}</span> view
            </div>
            <div className="text-[11px] text-gov-muted">
              Supports high-resolution JPG, PNG, WebP (Max 25 MB)
            </div>
          </div>
        )}
      </div>

      {/* Status Messages */}
      {error && (
        <div className="p-3 bg-gov-warningLight/50 border border-gov-warning/30 rounded-gov flex items-center space-x-2 text-xs text-gov-warning">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-3 bg-gov-pastelGreen border border-green-200 rounded-gov flex items-center space-x-2 text-xs text-green-800 font-medium">
          <CheckCircle className="w-4 h-4 shrink-0 text-green-600" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Ingest Action Button (for manually selected files) */}
      <div className="flex justify-end">
        <button
          type="button"
          onClick={handleUpload}
          disabled={!file || uploading}
          className="inline-flex items-center space-x-2 bg-gov-navy text-white text-xs font-semibold px-4 py-2.5 rounded-gov hover:bg-blue-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-xs"
        >
          {uploading ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Ingesting &amp; Hashing...</span>
            </>
          ) : (
            <>
              <ImageIcon className="w-3.5 h-3.5" />
              <span>Ingest {selectedView} Evidence</span>
            </>
          )}
        </button>
      </div>

      {/* Camera Capture Modal */}
      {showCameraModal && (
        <CameraCaptureModal
          viewType={selectedView}
          onCaptureAccepted={handleCameraCaptureAccepted}
          onClose={() => setShowCameraModal(false)}
          onFallbackToUpload={() => {
            setShowCameraModal(false);
            fileInputRef.current?.click();
          }}
        />
      )}
    </div>
  );
};
