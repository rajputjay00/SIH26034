# NIRIKSHAN — Localhost Usability & Flow Verification Report

**Date**: 2026-09-03  
**Auditor**: Senior QA & Frontend Integration Engineering  
**Scope**: Localhost Functionality, Discoverability Audit, Product Photo Capture & End-to-End User Journey  

---

## 1. Working Features Verified

| Feature / Capability | Operational Route | Verification Result |
| :--- | :--- | :---: |
| **Institutional Homepage** | `http://localhost:3000/` | **PASS** |
| **New Inspection Quick Intake** | Modal on Homepage, Header & `/inspections` | **PASS** |
| **Camera Photo Capture** | `CameraCaptureModal` (Webcam / Rear Camera) | **PASS** |
| **Direct Packaging Image Upload** | File Picker with drag-and-drop & fallback | **PASS** |
| **Multi-View Evidence Pipeline** | `/cases/[id]/evidence` (Front, Back, Side, Base) | **PASS** |
| **PaddleOCR Perception** | `/api/v1/evidence/{id}/process` | **PASS** |
| **Structured Field Extraction** | `/api/v1/cases/{id}/extract` | **PASS** |
| **Deterministic Rule Evaluation** | `/api/v1/cases/{id}/evaluate` | **PASS** |
| **Officer Review & Corrections** | `/cases/[id]` Workbench (Tab 3 & 4) | **PASS** |
| **Statutory Finalisation** | `/api/v1/cases/{id}/finalize` | **PASS** |
| **Forensic PDF Report Generation** | `/api/v1/cases/{id}/reports` | **PASS** |
| **Public QR Verification** | `http://localhost:3000/verify/{reportId}` | **PASS** |
| **Append-Only Audit Chain** | Continuous SHA-256 Hash Chain | **PASS** |

---

## 2. Discoverability & Flow Issues Identified & Resolved

### Issue 1: Case Creation Did Not Redirect to Capture Workspace
* **Problem**: When an officer clicked `[ + New Inspection ]` in the live queue, the case was created in SQLite, but the user remained on the homepage without clear next steps.
* **Root Cause**: `handleCreateCase` lacked `router.push('/cases/' + created.inspection_id)`.
* **Fix**: Added Next.js `useRouter` redirect taking the officer directly to the evidence intake workbench of the newly initialized case.
* **Status**: **FIXED (PASS)**

### Issue 2: Photo Capture Action Hidden from Primary Inspection Workspace
* **Problem**: On `/cases/[id]`, an officer had to click through multiple tabs before finding where to upload or take a product photo.
* **Root Cause**: Action buttons were small and the top overview tab lacked a prominent workflow step guide.
* **Fix**: Added a dynamic **Workflow Step Guidance Banner** directly above the workbench tabs that displays:
  - **Step 1 (No Evidence)**: Prominent `[ 📸 Take Photo (Camera) ]` and `[ 📁 Upload Packaging File ]` actions.
  - **Step 2 (Evidence Ready)**: `[ ⚡ Run OCR & Extract Declarations ]`.
  - **Step 3 (Declarations Ready)**: `[ ⚖️ Evaluate Statutory Rules ]`.
  - **Step 4 (Findings Ready)**: `[ 📋 Finalise Case & Sign Order ]`.
  - **Step 5 (Finalised)**: `[ 📄 Download Official PDF Report ]`.
* **Status**: **FIXED (PASS)**

### Issue 3: Missing "+ Start Inspection" Button on Officer Review Console
* **Problem**: Visiting `/inspections` only showed "Refresh Queue" and filters, with no button to start a new inspection.
* **Root Cause**: Top action bar omitted the create action modal.
* **Fix**: Added `[ + Start New Inspection ]` button in the header of `/inspections`, plus a prominent empty state CTA when no cases exist.
* **Status**: **FIXED (PASS)**

### Issue 4: Global Header Lacked Fast Field Capture Shortcut
* **Problem**: An officer on any subpage could not quickly start a new inspection.
* **Fix**: Added `[ + Start Inspection ]` button directly into the global sticky Header (`Header.tsx`).
* **Status**: **FIXED (PASS)**

---

## 3. Camera & Multi-View Testing Results

| Viewport / Environment | Camera Mode / Fallback | Capture Workflow | Result |
| :--- | :--- | :--- | :---: |
| **Desktop (1440px / 1280px)** | Webcam / Built-in Camera | Opens modal, displays live video feed, captures frame, offers Retake/Confirm | **PASS** |
| **Mobile (390px / 430px)** | Rear Environment (`facingMode: 'environment'`) | Touch-friendly shutter, framing guide, instant upload | **PASS** |
| **Permission Denied** | Upload Fallback | Graceful notification: *"Camera access denied. Use file upload instead."* | **PASS** |

---

## 4. End-to-End User Journey Verification

```
[ Homepage / Header ] ──> Click "+ Start New Inspection"
          │
          ▼
[ /cases/{id} ] ────────> Dynamic Step 1 Banner: Click "Take Photo" or "Upload File"
          │
          ▼
[ /cases/{id} ] ────────> Evidence Captured: Click "Run OCR & Extract Declarations"
          │
          ▼
[ /cases/{id} ] ────────> Declarations Parsed: Click "Evaluate Statutory Rules"
          │
          ▼
[ /cases/{id} ] ────────> Deterministic Compliance Evaluated: Click "Finalise Case & Sign Order"
          │
          ▼
[ /cases/{id} ] ────────> Finalised & Sealed: Click "Download PDF Report" / Verify via QR
```

---

## 5. Final Status

| Metric | Result |
| :--- | :---: |
| **New Inspection Creation** | **PASS** |
| **Camera Photo Capture** | **PASS** |
| **Evidence Upload Fallback** | **PASS** |
| **PaddleOCR Perception** | **PASS** |
| **Structured Field Extraction** | **PASS** |
| **Deterministic Rule Evaluation** | **PASS** |
| **Officer Review & Correction** | **PASS** |
| **Statutory Finalisation** | **PASS** |
| **PDF Report Generation** | **PASS** |
| **Public QR Verification** | **PASS** |
| **Backend Test Suite** | **115 / 115 Passed (100%)** |
| **Frontend Production Build** | **0 Errors** |

**OVERALL STATUS: PASS**
