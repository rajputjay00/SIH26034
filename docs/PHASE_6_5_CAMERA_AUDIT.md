# LegalMetriX — Phase 6.5 Camera Capture & Inspection Assistance Audit

## 1. Executive Summary & Objective
Phase 6.5 introduces an **in-app camera capture workflow** and **lightweight inspection copilot assistance** directly into the LegalMetriX evidence system. 
The objective is to allow authorised enforcement officers to capture multi-view product evidence on field devices (tablets, smartphones, laptops) without bypassing the existing evidence pipeline, cryptographic hashing, image quality gates, OCR, or provenance logging.

---

## 2. Current Evidence Architecture Audit

### Backend Pipeline
1. **Evidence Ingestion API**:
   - `POST /api/v1/cases/{inspection_id}/evidence` handled by [`evidence.py`](file:///c:/Users/rajpu/Desktop/SIH/backend/app/api/v1/evidence.py).
   - Ingests `multipart/form-data` with `file: UploadFile` and `view_type: EvidenceViewType` (`FRONT`, `BACK`, `SIDE`, `BASE`, `OTHER`).
   - Requires `ADMIN` or `OFFICER` role.
2. **Service Layer**:
   - [`EvidenceService.ingest_evidence`](file:///c:/Users/rajpu/Desktop/SIH/backend/app/services/evidence_service.py):
     - Validates extension (`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`) and MIME type.
     - Validates image decodability using OpenCV (`cv2.imdecode`).
     - Calculates authoritative SHA-256 hash on raw bytes (`compute_sha256_bytes`).
     - Writes original immutable file to `storage/evidence/{inspection_id}/{evidence_id}_{filename}`.
     - Creates `EvidenceItem` database record with `EvidenceProcessingStatus.UPLOADED` and `QualityVerdict.UNCHECKED`.
     - Appends cryptographic `AuditEntry` (`action="INGEST_EVIDENCE"`).
3. **Processing Pipeline**:
   - `POST /api/v1/evidence/{evidence_id}/process`:
     - Image Quality Gate ([`QualityAssessmentService`](file:///c:/Users/rajpu/Desktop/SIH/backend/app/services/quality_service.py)): Evaluates Laplacian blur variance ($\sigma^2$), brightness, and contrast.
     - Preprocessing ([`ImagePreprocessingService`](file:///c:/Users/rajpu/Desktop/SIH/backend/app/services/preprocessing_service.py)): Generates CLAHE, bilateral denoise, and adaptive Otsu derivatives.
     - OCR ([`OCRService`](file:///c:/Users/rajpu/Desktop/SIH/backend/app/services/ocr_service.py)): Extracts text polygons, character bounding boxes, and average confidence.
     - Structured Extraction ([`StructuredExtractionService`](file:///c:/Users/rajpu/Desktop/SIH/backend/app/services/extraction_service.py)): Automatically parses mandatory declarations under Rule 6.
     - Provenance ([`ProvenanceService`](file:///c:/Users/rajpu/Desktop/SIH/backend/app/services/provenance_service.py)): Links structured fields to source evidence image and bounding box coordinates.

### Frontend Components
1. **Evidence Uploader**: [`frontend/components/evidence/EvidenceUploader.tsx`](file:///c:/Users/rajpu/Desktop/SIH/frontend/components/evidence/EvidenceUploader.tsx) — currently handles standard file input selection.
2. **Evidence Gallery**: [`frontend/components/evidence/EvidenceGallery.tsx`](file:///c:/Users/rajpu/Desktop/SIH/frontend/components/evidence/EvidenceGallery.tsx) — displays evidence items per view type.
3. **Case Workbench**: [`frontend/app/cases/[id]/page.tsx`](file:///c:/Users/rajpu/Desktop/SIH/frontend/app/cases/%5Bid%5D/page.tsx) and [`frontend/app/cases/[id]/evidence/page.tsx`](file:///c:/Users/rajpu/Desktop/SIH/frontend/app/cases/%5Bid%5D/evidence/page.tsx).

---

## 3. Reusable Components & Services
* **Backend Ingestion API & Service**: 100% reusable without modification. Camera captured frames are converted to standard image Blobs/Files and sent to the exact same `POST /api/v1/cases/{inspection_id}/evidence` endpoint.
* **OpenCV Quality Gate**: Automated Laplacian blur, brightness, and contrast algorithms evaluate camera frames identically to file uploads.
* **Audit Chain**: Automatically logs `INGEST_EVIDENCE` events with server-calculated SHA-256 hashes.
* **Rule Engine & Provenance**: Seamlessly integrates captured views (`FRONT`, `BACK`, etc.) into Rule 6 and Rule 7 compliance workflows.

---

## 4. Proposed Camera Integration Architecture

```
[ FRONTEND CAMERA UI ]
  ├── View Selector (FRONT / BACK / SIDE / BASE / OTHER)
  ├── navigator.mediaDevices.getUserMedia ({ video: { facingMode: 'environment' } })
  ├── Live Video Preview + Framing Overlay Guide
  ├── Snapshot to HTML5 Canvas (high-res full sensor frame)
  ├── Client-side Framing & Quality Signals (Blur, Exposure checks)
  ├── Accept / Retake Flow
  └── Blob / File conversion (e.g. `camera_FRONT_20260903_120000.jpg`)
        │
        ▼
[ STANDARD EVIDENCE INTAKE API ]
  └── POST /api/v1/cases/{inspection_id}/evidence (Multipart form)
        ├── Server-side OpenCV Decode & Validation
        ├── Server-side SHA-256 Hash Computation
        ├── Immutable Storage in storage/evidence/
        ├── Quality Gate Assessment
        ├── Preprocessing & OCR Extraction
        └── Append Audit Log Chain
```

---

## 5. Exact Files to Create and Modify

### New Files:
1. `docs/PHASE_6_5_CAMERA_AUDIT.md` (this audit document)
2. `docs/PHASE_6_5_CAMERA_IMPLEMENTATION.md` (post-implementation report)
3. `frontend/components/evidence/CameraCaptureModal.tsx` — Reusable government-grade camera capture component with device enumeration, facingMode switching, subtle framing guidelines, instant preview, quality diagnostics, and retake controls.
4. `frontend/components/workbench/InspectionCopilot.tsx` — Lightweight deterministic workflow assistant checklist showing view completeness, mandatory declaration review status, and finalisation readiness.
5. `tests/integration/test_phase6_5_field_capture.py` — Integration tests validating evidence creation from camera-equivalent byte streams, SHA-256 immutability, quality assessment, and provenance links.

### Modified Files:
1. `frontend/components/evidence/EvidenceUploader.tsx` — Add dual mode toggles: `[ Take Photo ]` and `[ Upload Image ]` with seamless camera modal integration and permission fallback.
2. `frontend/app/cases/[id]/page.tsx` — Integrate "Show Me Where" bounding box highlighting when clicking evidence references in Findings & Declarations, and embed the Inspection Copilot.
3. `frontend/app/cases/[id]/evidence/page.tsx` — Embed camera capture actions and inspection progress copilot.

---

## 6. Browser & Device Constraints

* **HTTPS / Localhost Requirement**: Modern browsers restrict `navigator.mediaDevices.getUserMedia` to Secure Contexts (`https://` or `localhost`).
* **Camera Facing Mode**: Mobile devices should request `{ facingMode: { ideal: 'environment' } }` (rear camera), falling back to available webcams on desktops.
* **Camera Switching**: If multiple video input devices exist (`navigator.mediaDevices.enumerateDevices()`), provide a camera switcher button.
* **Permission Denied Handling**: If camera permission is denied or device has no camera, display a clean institutional warning message and gracefully fallback to standard file selection (`<input type="file" capture="environment">` or file upload).

---

## 7. Security Considerations

* **Server Authoritative**: Client never provides SHA-256 hashes or authoritative timestamps; the backend computes hashes on received byte streams.
* **MIME & Byte Validation**: Server decodes and verifies image headers with OpenCV before storing.
* **Role Authorization**: Ingestion requires valid JWT with `ADMIN` or `OFFICER` role.
* **No Fabricated Data**: No fake GPS, fake device identifiers, or simulated sensor metadata. If device metadata is absent, it is safely omitted/null.
* **AI Decision Safeguard**: The Inspection Copilot is strictly deterministic state tracking and does not use LLM or make legal decisions.
