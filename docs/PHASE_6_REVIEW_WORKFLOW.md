# LegalMetriX — Phase 6: Officer Review, Inspection History, Case Workflow & Government Dashboard

## 1. Overview
Phase 6 transforms the inspection workbench into a full officer-facing enforcement management platform. It institutes an evidence-oriented decision support architecture where automated computer vision, OCR, and deterministic rule evaluations provide structured intelligence, while the **Authorised Officer remains the final decision-maker**.

---

## 2. End-to-End Case Lifecycle

```
CASE INTAKE 
  → MULTI-VIEW EVIDENCE INGESTION (SHA-256 Immutability)
  → OPENCV QUALITY GATE (Blur / Exposure / Contrast)
  → PADDLEOCR POLYGON EXTRACTION
  → STRUCTURED FIELD PARSING & NORMALIZATION
  → DETERMINISTIC STATUTORY EVALUATION (Rule 6 & Rule 7 PC Rules 2011)
  → OFFICER REVIEW CONSOLE
  → MANUAL FIELD CORRECTIONS & AUDITED RE-EVALUATION
  → AUTHORITATIVE FINALISATION & OFFICER SIGN-OFF
  → CRYPTOGRAPHIC PDF REPORT CERTIFICATE
  → IMMUTABLE AUDIT TRAIL & PUBLIC INTEGRITY VERIFICATION
```

---

## 3. Operational Workload Queues & Calculations

All dashboard metrics and review queues are query-backed directly from the SQLite database with zero fabricated/hardcoded statistics.

### Queue Definitions:
* **PROCESSING**: Cases in `DRAFT` or `PROCESSING` state undergoing evidence upload or OCR processing.
* **PENDING_REVIEW**: Cases where automated extraction has finished and are awaiting officer inspection.
* **REQUIRES_REVIEW**: Cases with `OverallDetermination.REQUIRES_REVIEW` or containing statutory `REVIEW` findings (e.g. unverified PDP area, missing reference coin calibration, or sticker anomalies).
* **READY_FOR_FINALISATION**: Cases in `PENDING_REVIEW` where rule findings have been fully evaluated with zero failures or unresolved ambiguities.
* **FINALISED**: Cases sealed by authoritative officer decision with immutable timestamp, remarks, and generated legal PDF certificates.

---

## 4. Statutory Separation & Safety Controls

1. **Cognitive Separation**:
   - **System Extraction**: Preserved in original immutable `raw_value`.
   - **Officer Correction**: Recorded with timestamp, officer identity, and reason in `field_corrections`.
   - **System Evaluation**: Pure deterministic evaluation under Rule 6 and Rule 7 without subjective bias.
   - **Officer Final Determination**: Authoritative officer decision (`COMPLIANT`, `NON-COMPLIANT`, `REQUIRES_REVIEW`) with statutory remarks.

2. **Rule 7 Safety**:
   - Font height compliance is evaluated strictly on:
     $$\text{PDP Area (cm}^2\text{)} + \text{Character Type (Letter/Numeral)} + \text{Declaration Method (Normal/Blown/Embossed)}$$
   - Missing PDP area or calibration strictly yields `REQUIRES_REVIEW` and is never guessed or approximated.

3. **Finalisation Safeguard**:
   - Requires evidence completeness and evaluated statutory rules.
   - If unresolved `REVIEW` findings exist, the officer must explicitly acknowledge them before finalisation is permitted.

---

## 5. API Endpoints

* `GET /api/v1/dashboard/summary` — Aggregate KPI metrics.
* `GET /api/v1/dashboard/review-queue` — Review queue workload distribution.
* `GET /api/v1/dashboard/findings` — Rule-by-rule statutory violation counts.
* `GET /api/v1/dashboard/trends` — Historical inspection timeline.
* `GET /api/v1/cases/summary` — Paginated and filtered inspection records.
* `GET /api/v1/cases/{id}/review-summary` — Full 8-tab case review aggregate.
* `POST /api/v1/cases/{id}/fields/{field_id}/correct` — Audited manual field correction.
* `POST /api/v1/cases/{id}/evaluate/rerun` — Deterministic compliance re-evaluation.
* `POST /api/v1/cases/{id}/finalize` — Final decision submission and auto-report generation.

---

## 6. Testing & Validation

* 9 Phase 6 backend integration tests in `tests/integration/test_phase6_officer_review_and_dashboard.py`.
* 69 total backend tests passing across Phases 1 through 6 with 0 regressions.
* Next.js production build passing with strict TypeScript verification.
