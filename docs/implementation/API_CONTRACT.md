# LegalMetriX — REST API Contract (v1 Frozen)

**Base URL:** `/api/v1`  
**Authentication:** HTTP Bearer Token (JWT)

---

## 1. Health & Status
### `GET /api/v1/health`
* **Purpose:** System readiness, database connectivity, and authoritative server timestamp check.
* **Auth:** None (Public)
* **Response (200 OK):**
```json
{
  "status": "HEALTHY",
  "app_name": "LegalMetriX Backend API",
  "environment": "development",
  "database_connected": true,
  "server_time": "2026-09-02T01:50:00.000000Z"
}
```

---

## 2. Authentication
### `POST /api/v1/auth/login`
* **Purpose:** Officer credentials login and token issuance.
* **Auth:** None (Public)
* **Request:**
```json
{
  "username": "officer1",
  "password": "password123"
}
```
* **Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in_seconds": 28800
}
```

### `GET /api/v1/auth/me`
* **Purpose:** Retrieve profile of current authenticated officer.
* **Auth:** Bearer Token

---

## 3. Inspection Cases
### `POST /api/v1/cases`
* **Purpose:** Create new inspection case.
* **Auth:** `OFFICER`, `ADMIN`
* **Request:**
```json
{
  "case_number": "CASE-LM-20260902-001",
  "notes": "Retail market inspection batch 4",
  "rule_pack_version": "v1.0.0"
}
```
* **Response (201 Created):** `CaseResponse`

### `GET /api/v1/cases`
* **Purpose:** Retrieve paginated list of inspection cases.
* **Query Params:** `limit` (default: 50), `offset` (default: 0)
* **Response (200 OK):** `List[CaseResponse]`

### `GET /api/v1/cases/{inspection_id}`
* **Purpose:** Retrieve single inspection case details.
* **Response (200 OK):** `CaseResponse`

### `PATCH /api/v1/cases/{inspection_id}/status`
* **Purpose:** Transition case status (`DRAFT` $\rightarrow$ `PROCESSING` $\rightarrow$ `PENDING_REVIEW` $\rightarrow$ `FINALISED`).
* **Request:**
```json
{
  "status": "PROCESSING",
  "notes": "Evidence ingestion initiated"
}
```

---

## 4. Evidence Ingestion & OCR
### `POST /api/v1/cases/{inspection_id}/evidence`
* **Purpose:** Upload and ingest evidence image; computes SHA-256 hash immediately upon arrival and stores immutable original.
* **Auth:** `OFFICER`, `ADMIN`
* **Content-Type:** `multipart/form-data`
* **Form Fields:** `view_type` (`FRONT`, `BACK`, `SIDE`, `BASE`, `OTHER`), `file` (Binary Image)
* **Response (201 Created):** `EvidenceResponse`

### `GET /api/v1/cases/{inspection_id}/evidence`
* **Purpose:** List all uploaded evidence items for an inspection case.
* **Response (200 OK):** `List[EvidenceResponse]`

### `GET /api/v1/evidence/{evidence_id}`
* **Purpose:** Retrieve detailed metadata, quality report, and OCR status for a specific evidence item.
* **Response (200 OK):** `EvidenceResponse`

### `POST /api/v1/evidence/{evidence_id}/process`
* **Purpose:** Execute OpenCV image quality gate, preprocessing variant generation, and PaddleOCR text/bounding box extraction.
* **Auth:** `OFFICER`, `ADMIN`
* **Response (200 OK):** `EvidenceResponse`

### `GET /api/v1/evidence/{evidence_id}/ocr`
* **Purpose:** Retrieve extracted OCR text, polygon bounding boxes, character heights, and confidence scores.
* **Response (200 OK):** `List[OCRResultResponse]`

### `POST /api/v1/evidence/{evidence_id}/retry`
* **Purpose:** Retry quality check and OCR processing for an existing evidence item.
* **Auth:** `OFFICER`, `ADMIN`
* **Response (200 OK):** `EvidenceResponse`


---

## 5. Extraction & Provenance
### `POST /api/v1/cases/{inspection_id}/extract`
* **Purpose:** Run structured field extraction from OCR perception across all case evidence views.
* **Auth:** `OFFICER`, `ADMIN`
* **Response (200 OK):** `List[ExtractedFieldResponse]`

### `GET /api/v1/cases/{inspection_id}/fields`
* **Purpose:** List all structured fields extracted for an inspection case.
* **Response (200 OK):** `List[ExtractedFieldResponse]`

### `POST /api/v1/cases/{inspection_id}/fields/{field_id}/correct`
* **Purpose:** Officer manual field correction with audit logging and history preservation.
* **Auth:** `OFFICER`, `ADMIN`
* **Body:** `FieldCorrectionCreate` (`corrected_value`, `unit`, `reason`)
* **Response (200 OK):** `ExtractedFieldResponse`

### `GET /api/v1/fields/{field_id}/provenance`
* **Purpose:** Retrieve full field provenance (evidence ID, bounding box coordinates, origin, correction history).
* **Response (200 OK):** `FieldProvenanceResponse`

---

## 6. Deterministic Rule Engine & Compliance Evaluation
### `POST /api/v1/cases/{inspection_id}/evaluate`
* **Purpose:** Execute deterministic compliance rules against structured fields.
* **Auth:** `OFFICER`, `REVIEWER`, `ADMIN`
* **Response (200 OK):** `CaseEvaluationSummary`

### `POST /api/v1/cases/{inspection_id}/evaluate/rerun`
* **Purpose:** Re-evaluate compliance rules following officer manual field corrections.
* **Auth:** `OFFICER`, `REVIEWER`, `ADMIN`
* **Response (200 OK):** `CaseEvaluationSummary`

### `GET /api/v1/cases/{inspection_id}/findings`
* **Purpose:** Retrieve all statutory rule findings with severity, citations, and calculation metadata.
* **Response (200 OK):** `List[RuleFindingResponse]`


### `GET /api/v1/cases/{inspection_id}/audit/verify`
* **Purpose:** Run cryptographic SHA-256 hash-chain verification over the inspection case audit trail.
* **Response (200 OK):**
```json
{
  "inspection_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "is_valid": true,
  "total_entries": 6,
  "corrupted_sequence_index": null,
  "message": "Audit chain integrity verified successfully."
}
```

---

## 7. Reports Architecture (Placeholder)
### `GET /api/v1/cases/{inspection_id}/report/metadata`
* **Purpose:** Fetch report generation metadata. PDF generation implemented in Phase 5.
