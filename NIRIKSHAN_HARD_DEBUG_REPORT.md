# NIRIKSHAN — Hard Debugging & Failure Testing Report

**Date & Time**: 2026-09-03  
**Auditor**: Senior QA, Backend, Frontend Integration & Security Engineering  
**Scope**: Full Stack Systematic Audit, Failure Mode Injection, Edge-Case Verification & Regression Testing  

---

## 1. Environment & Baseline Status

| Component | Specification / Version | Test / Verification Result |
| :--- | :--- | :--- |
| **Operating System** | Windows 11 / x64 | Verified |
| **Python Runtime** | Python 3.11.16 | Active Virtual Environment (`.venv`) |
| **Backend Framework** | FastAPI 0.115.0 + SQLAlchemy 2.0 (SQLite WAL) | **115 / 115 Tests Passing (100%)** in 7.62s |
| **Node / Next.js** | Next.js 14.2.35 + TypeScript 5.4 | **Compiled successfully with 0 errors** (`next build`) |
| **Computer Vision / OCR** | OpenCV (opencv-python 4.10.0) + PaddleOCR | Verified |
| **Cryptographic Hashing** | SHA-256 Digest Engine + PBKDF2 Password Hashing | Verified |

---

## 2. Issues Found, Root Causes & Fixes

During the hard-failure testing phase, 2 genuine edge-case failure modes were identified, reproduced, fixed, and locked with automated regression tests:

### Issue 1: 0-Byte File Upload Causing Unhandled OpenCV Assertion
* **Severity**: `HIGH`
* **Component**: `backend/app/services/evidence_service.py`
* **Reproduction**: An empty 0-byte file payload (`b""`) was passed to `POST /api/v1/cases/{id}/evidence`.
* **Root Cause**: `np.frombuffer(b"", np.uint8)` produced an empty buffer `(0,)`, which caused OpenCV's `cv2.imdecode()` to raise an unhandled C++ assertion error (`(-215:Assertion failed) !buf.empty()`).
* **Fix**: Added explicit pre-decode validation check in `EvidenceService.ingest_evidence()` to verify `len(file_bytes) > 0` and raise standard `LegalMetrixException(status_code=400, error_code="EMPTY_FILE")`.
* **Regression Test**: `tests/integration/test_hard_failure_modes.py::test_fail_01_empty_zero_byte_upload`
* **Status**: **RESOLVED & VERIFIED (PASS)**

### Issue 2: Post-Finalisation Field Modification Permitted
* **Severity**: `HIGH`
* **Component**: `backend/app/api/v1/extraction.py`
* **Reproduction**: An officer attempted to submit manual field corrections on an already `FINALISED` inspection case.
* **Root Cause**: The `/cases/{inspection_id}/fields/{field_id}/correct` endpoint checked field existence but omitted checking whether `case.status == CaseStatus.FINALISED`.
* **Fix**: Enforced statutory immutability check requiring `case.status != CaseStatus.FINALISED`. If finalised, raises `HTTP 400 Bad Request` with message *"Cannot modify or correct declarations on a finalised inspection case."*
* **Regression Test**: `tests/integration/test_hard_failure_modes.py::test_fail_10_correction_on_finalised_case_blocked`
* **Status**: **RESOLVED & VERIFIED (PASS)**

---

## 3. Systematic Hard Failure Matrix

| Area | Injected Failure / Edge Case | Expected Hardened Behavior | Result |
| :--- | :--- | :--- | :---: |
| **Evidence Ingestion** | 0-byte upload (`b""`) | Graceful 400 rejection (`EMPTY_FILE`) | **PASS** |
| **Evidence Ingestion** | Executable / Unsupported format (`.exe`) | Graceful 400 rejection (`UNSUPPORTED_FILE_EXTENSION`) | **PASS** |
| **Evidence Ingestion** | Corrupted random byte payload | OpenCV decode gate catches invalid image, returns 400 | **PASS** |
| **Unit Normalization** | Unsupported / Ambiguous units ("boxes", "widgets") | `is_valid=False`, no fake normalization | **PASS** |
| **USP Arithmetic** | Net Quantity $\le 0$ / Zero division | `is_computable=False`, safe error string, no ZeroDivisionError | **PASS** |
| **USP Arithmetic** | Decimal precision rounding ($100 / 0.3$) | Exact Decimal arithmetic (`333.33 INR/kg`), no float drift | **PASS** |
| **Rule Engine Aggregation**| One FAIL + One REVIEW | Aggregated determination strictly `NON_COMPLIANT` | **PASS** |
| **Rule 7 Calibration** | Exact statutory boundary (1.49mm vs 1.50mm) | 1.49mm strictly `FAIL`, 1.50mm strictly `PASS` | **PASS** |
| **Finalisation Gate** | Finalise without officer decision / remarks | Blocked with 400/422 validation error | **PASS** |
| **Finalisation Immutability**| Modifying declarations on finalised case | Blocked with 400 rejection | **PASS** |
| **Report Verification** | Byte-level PDF modification on disk | Public verification returns `INTEGRITY_MISMATCH` | **PASS** |
| **Authentication & RBAC** | Expired JWT bearer token | Blocked with `401 Unauthorized` | **PASS** |
| **Visual Forensics** | Sticker anomaly detected alone | Flagged strictly as review signal, not automatic violation | **PASS** |
| **Multi-View Provenance** | Conflicting declarations across views | Surfaced as conflict requiring officer review | **PASS** |

---

## 4. FINAL RED-TEAM AUDIT & RELEASE GATE

### 4.1 Finalisation Mutation Matrix

| Endpoint | Method | Mutation Target | Before Finalisation | After Finalisation | Enforcement Result |
| :--- | :---: | :--- | :---: | :---: | :---: |
| `/cases/{id}/evidence` | `POST` | Ingest packaging image | Allowed (`201`) | **Blocked (`400`)** | **PASS** |
| `/cases/{id}/extract` | `POST` | Re-run AI field extraction | Allowed (`200`) | **Blocked (`400`)** | **PASS** |
| `/cases/{id}/fields/{fid}/correct` | `POST` | Officer declaration edit | Allowed (`200`) | **Blocked (`400`)** | **PASS** |
| `/cases/{id}/evaluate` | `POST` | Re-run rule engine | Allowed (`200`) | **Blocked (`400`)** | **PASS** |
| `/cases/{id}/status` | `PATCH` | Rollback status to Draft | Allowed (`200`) | **Blocked (`400`)** | **PASS** |
| `/cases/{id}/finalize` | `POST` | Re-finalise case | Allowed (`200`) | **Blocked (`400`)** | **PASS** |

### 4.2 Authorization & Role-Based Access Control (RBAC)

| Scenario / Endpoint | Unauthenticated | Reviewer Role | Officer Role | Admin Role | Result |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `GET /api/v1/cases` | `401 Unauthorized` | `200 OK` | `200 OK` | `200 OK` | **PASS** |
| `POST /api/v1/cases` | `401 Unauthorized` | `403 Forbidden` | `201 Created` | `201 Created` | **PASS** |
| `POST /api/v1/cases/{id}/finalize` | `401 Unauthorized` | `403 Forbidden` | `200 OK` | `200 OK` | **PASS** |
| `GET /api/v1/reports/{id}/verify` | `200 OK (Public)` | `200 OK` | `200 OK` | `200 OK` | **PASS** |

### 4.3 Object-Level Isolation & Audit Integrity

* **Object Isolation**: Non-existent case or evidence identifiers consistently return `404 Not Found` without data leakage.
* **Audit Chain Integrity**: Continuous SHA-256 hash chaining (`INITIAL_CHAIN_HASH` $\rightarrow H_1 \rightarrow H_2 \dots$) verified with `AuditService.verify_chain()` yielding `is_valid: True`.

### 4.4 Automated Test Suite & Build Summary

* **Backend Integration Suite**: **115 / 115 Tests Passing (100%)**
* **Frontend Production Build**: **Next.js 14.2.35 build succeeded with 0 errors**
* **Linting / TypeScript**: Verified with 0 syntax or type errors.

---

## 5. Release Gate Decision

```
============================================================
                   RELEASE STATUS: PASS
============================================================
```

1. **Zero Critical / High Issues**: All discovered defects resolved and regression-tested.
2. **Finalise-Lock Immutability**: All 6 mutation vectors blocked on finalised cases.
3. **Statutory Architecture Intact**: Deterministic rule engine is authoritative; AI remains perception/extraction only.
4. **Codebase Freeze**: Ready for SIH live demonstration and deployment.
