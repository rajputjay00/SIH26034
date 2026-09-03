import {
  HealthResponse,
  InspectionCase,
  EvidenceItem,
  EvidenceViewType,
  OCRResult,
  ExtractedField,
  RuleFinding,
  CaseEvaluationSummary,
  CalibrationData,
  VisualMeasurement,
  VisualAnomaly
} from '../types';

function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envUrl) {
    const clean = envUrl.trim().replace(/\/+$/, '');
    return clean.endsWith('/api/v1') ? clean : `${clean}/api/v1`;
  }
  return 'http://127.0.0.1:8000/api/v1';
}

const API_BASE = getApiBaseUrl();

let cachedToken: string | null = null;

function isTokenValid(token: string): boolean {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return false;
    const payload = JSON.parse(atob(parts[1]));
    if (!payload.exp) return true;
    // Check if token expires within the next 60 seconds
    return payload.exp * 1000 > Date.now() + 60000;
  } catch {
    return false;
  }
}

export async function getAuthToken(forceRefresh = false): Promise<string> {
  if (!forceRefresh && typeof window !== 'undefined') {
    const stored = localStorage.getItem('token');
    if (stored && isTokenValid(stored)) {
      cachedToken = stored;
      return stored;
    }
  }

  if (!forceRefresh && cachedToken && isTokenValid(cachedToken)) {
    return cachedToken;
  }

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'officer1', password: 'password123' }),
    });
    if (res.ok) {
      const data = await res.json();
      cachedToken = data.access_token;
      if (typeof window !== 'undefined' && cachedToken) {
        localStorage.setItem('token', cachedToken);
        localStorage.setItem('user_id', 'OFFICER-IND-1001');
        localStorage.setItem('role', 'OFFICER');
      }
      return cachedToken || '';
    }
  } catch (err) {
    console.error('Auto-login failed:', err);
  }
  return '';
}

export async function apiFetch(input: string, init: RequestInit = {}): Promise<Response> {
  let token = await getAuthToken();
  const headers = new Headers(init.headers || {});
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let res = await fetch(input, { ...init, headers });

  // Auto-refresh token and retry on 401 Unauthorized
  if (res.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
    cachedToken = null;
    token = await getAuthToken(true);
    if (token) {
      const retryHeaders = new Headers(init.headers || {});
      retryHeaders.set('Authorization', `Bearer ${token}`);
      res = await fetch(input, { ...init, headers: retryHeaders });
    }
  }

  return res;
}

export async function getAuthHeaders(extraHeaders: Record<string, string> = {}): Promise<Record<string, string>> {
  const token = await getAuthToken();
  const headers: Record<string, string> = { ...extraHeaders };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await apiFetch(`${API_BASE}/health`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchCases(): Promise<InspectionCase[]> {
  const res = await apiFetch(`${API_BASE}/cases`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch inspection cases');
  return res.json();
}

export async function createInspectionCase(notes?: string): Promise<InspectionCase> {
  const res = await apiFetch(`${API_BASE}/cases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes, rule_pack_version: 'v1.0.0' }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Failed to create inspection case' }));
    throw new Error(err.message || 'Failed to create inspection case');
  }
  return res.json();
}

export async function uploadEvidence(
  inspectionId: string,
  file: File,
  viewType: EvidenceViewType
): Promise<EvidenceItem> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('view_type', viewType);

  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/evidence`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Upload failed' }));
    throw new Error(err.message || 'Evidence upload failed');
  }
  return res.json();
}

export async function fetchCaseEvidence(inspectionId: string): Promise<EvidenceItem[]> {
  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/evidence`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch case evidence');
  return res.json();
}

export async function fetchEvidenceDetail(evidenceId: string): Promise<EvidenceItem> {
  const res = await apiFetch(`${API_BASE}/evidence/${evidenceId}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch evidence details');
  return res.json();
}

export async function processEvidenceOCR(evidenceId: string): Promise<EvidenceItem> {
  const res = await apiFetch(`${API_BASE}/evidence/${evidenceId}/process`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'OCR processing failed' }));
    throw new Error(err.message || 'OCR processing failed');
  }
  return res.json();
}

export async function fetchEvidenceOCR(evidenceId: string): Promise<OCRResult[]> {
  const res = await apiFetch(`${API_BASE}/evidence/${evidenceId}/ocr`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch OCR results');
  return res.json();
}

export async function retryEvidenceProcessing(evidenceId: string): Promise<EvidenceItem> {
  const res = await apiFetch(`${API_BASE}/evidence/${evidenceId}/retry`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to retry evidence processing');
  return res.json();
}

// --------------------------------------------------------------------------
// Phase 3: Structured Extraction & Compliance Evaluation APIs
// --------------------------------------------------------------------------

export async function extractCaseFields(inspectionId: string): Promise<ExtractedField[]> {
  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/extract`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Extraction failed' }));
    throw new Error(err.message || 'Structured field extraction failed');
  }
  return res.json();
}

export async function fetchCaseFields(inspectionId: string): Promise<ExtractedField[]> {
  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/fields`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch case fields');
  return res.json();
}

export async function correctFieldValue(
  inspectionId: string,
  fieldId: string,
  payload: { corrected_value: string; unit?: string; reason?: string }
): Promise<ExtractedField> {
  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/fields/${fieldId}/correct`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Correction failed' }));
    throw new Error(err.message || 'Field correction failed');
  }
  return res.json();
}

export async function evaluateCaseCompliance(inspectionId: string): Promise<CaseEvaluationSummary> {
  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/evaluate`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Evaluation failed' }));
    throw new Error(err.message || 'Compliance evaluation failed');
  }
  return res.json();
}

export async function rerunCaseCompliance(inspectionId: string): Promise<CaseEvaluationSummary> {
  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/evaluate/rerun`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Rerun evaluation failed' }));
    throw new Error(err.message || 'Rerun compliance evaluation failed');
  }
  return res.json();
}

export async function fetchCaseFindings(inspectionId: string): Promise<RuleFinding[]> {
  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/findings`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch case findings');
  return res.json();
}

// --------------------------------------------------------------------------
// Phase 4: CV Calibration, Font Measurements & Forensics API
// --------------------------------------------------------------------------

export async function calibrateEvidence(inspectionId: string, evidenceId: string): Promise<CalibrationData> {
  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/calibration/${evidenceId}`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Calibration failed' }));
    throw new Error(err.message || 'Coin reference calibration failed');
  }
  return res.json();
}

export async function fetchCaseCalibrations(inspectionId: string): Promise<CalibrationData[]> {
  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/calibration`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch case calibrations');
  return res.json();
}

export async function measureEvidenceFonts(inspectionId: string, evidenceId: string): Promise<VisualMeasurement[]> {
  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/measurements/${evidenceId}`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Font measurement failed' }));
    throw new Error(err.message || 'Font measurement failed');
  }
  return res.json();
}

export async function fetchCaseMeasurements(inspectionId: string): Promise<VisualMeasurement[]> {
  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/measurements`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch case visual measurements');
  return res.json();
}

export async function detectVisualAnomalies(inspectionId: string, evidenceId: string): Promise<VisualAnomaly[]> {
  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/visual-anomalies/${evidenceId}`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Anomaly detection failed' }));
    throw new Error(err.message || 'Visual anomaly detection failed');
  }
  return res.json();
}

export async function fetchCaseAnomalies(inspectionId: string): Promise<VisualAnomaly[]> {
  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/visual-anomalies`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch case visual anomalies');
  return res.json();
}

// --------------------------------------------------------------------------
// Phase 5: Reporting & Verification APIs
// --------------------------------------------------------------------------

export async function generateInspectionReport(inspectionId: string, forceRegenerate: boolean = false): Promise<any> {
  const res = await apiFetch(`${API_BASE}/reports/${inspectionId}/generate?force_regenerate=${forceRegenerate}`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Report generation failed' }));
    throw new Error(err.detail || 'Report generation failed');
  }
  return res.json();
}

export async function fetchCaseReports(inspectionId: string): Promise<any[]> {
  const res = await apiFetch(`${API_BASE}/reports/${inspectionId}/versions`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch reports');
  return res.json();
}

export async function downloadReportPdf(inspectionId: string): Promise<void> {
  const res = await apiFetch(`${API_BASE}/reports/${inspectionId}/download`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Report download failed' }));
    throw new Error(err.detail || 'Inspection report not found or not yet generated.');
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Inspection_Report_${inspectionId.slice(0, 8)}.pdf`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

// --------------------------------------------------------------------------
// Phase 6: Government Dashboard & Officer Review APIs
// --------------------------------------------------------------------------

export async function fetchDashboardSummary(): Promise<any> {
  const res = await apiFetch(`${API_BASE}/dashboard/summary`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch dashboard summary');
  return res.json();
}

export async function fetchDashboardReviewQueue(): Promise<any> {
  const res = await apiFetch(`${API_BASE}/dashboard/review-queue`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch dashboard review queue');
  return res.json();
}

export async function fetchDashboardFindings(): Promise<any> {
  const res = await apiFetch(`${API_BASE}/dashboard/findings`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch dashboard findings');
  return res.json();
}

export async function fetchDashboardTrends(days: number = 14): Promise<any[]> {
  const res = await apiFetch(`${API_BASE}/dashboard/trends?days=${days}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch dashboard trends');
  return res.json();
}

export async function fetchInspectionsSummary(params?: {
  status?: string;
  determination?: string;
  review_queue?: string;
  officer_id?: string;
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<any> {
  const query = new URLSearchParams();
  if (params?.status) query.append('status', params.status);
  if (params?.determination) query.append('determination', params.determination);
  if (params?.review_queue) query.append('review_queue', params.review_queue);
  if (params?.officer_id) query.append('officer_id', params.officer_id);
  if (params?.search) query.append('search', params.search);
  if (params?.limit) query.append('limit', params.limit.toString());
  if (params?.offset) query.append('offset', params.offset.toString());

  const res = await apiFetch(`${API_BASE}/cases/summary?${query.toString()}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch inspection summaries');
  return res.json();
}

export async function fetchCaseReviewSummary(inspectionId: string): Promise<any> {
  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/review-summary`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch full case review summary');
  return res.json();
}

export async function finalizeCase(
  inspectionId: string,
  payload: {
    officer_decision: string;
    officer_remarks?: string;
    acknowledged_review_findings?: boolean;
  }
): Promise<any> {
  const res = await apiFetch(`${API_BASE}/cases/${inspectionId}/finalize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Finalisation failed' }));
    throw new Error(err.message || 'Inspection finalisation failed');
  }
  return res.json();
}
