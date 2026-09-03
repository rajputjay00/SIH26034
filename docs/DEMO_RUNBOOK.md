# LegalMetriX — Official SIH Demonstration Runbook

## 1. Overview
This runbook provides the definitive step-by-step procedure for demonstrating LegalMetriX during the Smart India Hackathon (SIH) evaluation. It details the complete 15-step demonstration flow, the underlying institutional architecture, and immediate contingency fallback procedures if live hardware or connectivity fluctuates.

---

## 2. Demonstration Flow: Step-by-Step

### Step 1: Login & Role Authentication
* **Action**: Open `http://localhost:3000` (or field deployment URL) and sign in as `officer@legalmetrix.gov.in` (`password123`).
* **Talking Points**: 
  - Strict PBKDF2-HMAC-SHA256 password hashing.
  - Role-Based Access Control (RBAC): Only Authorised Officers can sign final statutory orders.

### Step 2: Executive Dashboard & Operational Queues
* **Action**: Review dashboard summary cards, review queues (*High Priority*, *Ready for Finalisation*), and statutory violation distribution.
* **Talking Points**:
  - Direct SQL query-backed aggregations (no mock counters).
  - Clean institutional white-first UI designed for government workflow.

### Step 3: Create / Open Inspection Case
* **Action**: Click `+ New Inspection` (or open an existing case from `/inspections`).
* **Talking Points**:
  - Unique statutory Case Identifier with immutable creation timestamp.

### Step 4: Multi-View Evidence Intake & In-App Camera
* **Action**: Navigate to `Evidence Intake` tab. Open `Take Photo` camera modal.
* **Talking Points**:
  - In-app rear camera (`facingMode: 'environment'`) with live framing guide and brightness/glare feedback.
  - Retake safety: Only accepted captures are persisted.
  - Server-calculated authoritative SHA-256 evidence integrity hashing.

### Step 5: OpenCV Quality Gate & Preprocessing
* **Action**: Click `Process Evidence`.
* **Talking Points**:
  - Deterministic image quality gate: Laplacian variance (blur), luminance histogram (underexposure/glare), Michelson contrast.
  - Raw evidence bytes remain untouched; separate preprocessing variants (CLAHE, Otsu, Denoise) are created for OCR ingestion.

### Step 6: PaddleOCR Polygon Extraction
* **Action**: View extracted text polygons in the interactive workbench.
* **Talking Points**:
  - Accurate spatial bounding boxes for all packaged text regions.

### Step 7: Structured Declarations & Provenance
* **Action**: Navigate to `Declarations` tab.
* **Talking Points**:
  - Structured parsing of 8 mandatory declarations under Legal Metrology (Packaged Commodities) Rules, 2011.
  - Complete cryptographic provenance linking every declaration to its exact source image and polygon.

### Step 8: Interactive "Show Me Where" Navigation
* **Action**: Click `[Show Me Where]` on a declaration (e.g., MRP or Net Quantity).
* **Talking Points**:
  - Instantly loads the exact source image and highlights the corresponding bounding box overlay without manual image hunting.

### Step 9: Physical Calibration with Indian ₹5 Coin
* **Action**: Navigate to `Rule 7 Font Sizing` tab. Show coin calibration.
* **Talking Points**:
  - Standard 23.00mm physical coin diameter yields exact millimeter-per-pixel scale factor.

### Step 10: Authoritative Rule 7 PDP Font Sizing
* **Action**: Review font height check.
* **Talking Points**:
  - Evaluated strictly against statutory **$\text{PDP Area} + \text{Character Type} + \text{Declaration Method}$** under Rule 7 Table 1.
  - Net Quantity is not used as a proxy. Unverified PDP areas safely yield `REQUIRES_REVIEW`.

### Step 11: Visual Forensics & Sticker Anomaly Detection
* **Action**: Navigate to `Visual Forensics` tab.
* **Talking Points**:
  - Canny edge and contour analysis flags potential price stickers / relabeling as an officer review signal (not an automatic penalty).

### Step 12: Audited Officer Correction Loop
* **Action**: Edit an extracted declaration value (e.g. correct ₹199 to ₹189) with reason *"Printed declaration visually verified"*.
* **Talking Points**:
  - Original system extraction is permanently retained.
  - Officer correction, timestamp, reason, and identity are recorded in the audit log.
  - Automatic re-evaluation triggers deterministic rules immediately.

### Step 13: Finalisation Safeguards & Officer Statutory Decision
* **Action**: Finalise the inspection as `COMPLIANT` or `NON_COMPLIANT` with statutory officer remarks.
* **Talking Points**:
  - The system never makes the final legal decision. The Authorised Officer remains the sole statutory authority.
  - Finalisation locks the case against subsequent modification.

### Step 14: Forensic PDF Report Generation & QR Code
* **Action**: Generate and download the official 3-part PDF Inspection Report.
* **Talking Points**:
  - Includes institutional header, executive summary, declaration table, evidence SHA-256 register, and tamper-evident QR code.

### Step 15: Cryptographic Integrity Verification & Audit Chain
* **Action**: Scan QR code or navigate to `/verify/[reportId]`. View cryptographic audit chain.
* **Talking Points**:
  - Read-only public portal verifies PDF byte hash matching.
  - Hash-chained audit trail confirms tamper-evident immutability.

---

## 3. Contingency Fallbacks for Live Demo

| Scenario / Glitch | Immediate Fallback Action |
| :--- | :--- |
| **Camera Permission Blocked or Laptop Lacks Rear Camera** | Switch to standard `Upload File` button or webcam fallback directly in the evidence modal. |
| **No Internet / Network Disconnect** | Demonstrate Phase 7 **Offline Queue**: Photos captured while offline are stored locally in the browser and synced automatically when reconnected. |
| **OCR Processing Delay** | Use pre-ingested deterministic demo case (`CASE-QA-COMPLIANT` or `CASE-QA-NON-COMPLIANT`). |
| **Printer / PDF Viewer Blocked** | View report metadata directly in the `Reports` tab or open in built-in browser PDF preview. |
