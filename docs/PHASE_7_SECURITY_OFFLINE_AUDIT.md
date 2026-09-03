# LegalMetriX — Phase 7 Security, Offline Readiness & Deployment Hardening Audit

## 1. Executive Summary
This audit provides a comprehensive evaluation of security controls, authentication mechanisms, evidence storage integrity, API hardening, offline field capabilities, and production readiness for LegalMetriX.

---

## 2. Comprehensive Security & Architecture Audit

### 1. Current Security Controls
* **Authentication & RBAC**: JWT-based authentication using PyJWT (`HS256`), with `RequireRole` dependency restricting endpoints based on user roles (`ADMIN`, `OFFICER`, `REVIEWER`).
* **Cryptographic Evidence Integrity**: Server calculates SHA-256 on raw incoming byte streams before writing to disk; original evidence files are stored in append-only storage.
* **Audit Chaining**: SHA-256 hash-chained immutable audit log with previous-hash pointers and `AuditService.verify_chain` validation.
* **Deterministic Rule Engine**: Pure rule execution without subjective AI/LLM decision-making.

### 2. Current Authentication Weaknesses
* **Unauthenticated Fallback in `get_current_user`**: If no Bearer token was provided, `get_current_user` defaulted to `DEMO_USERS["officer1"]` for developer convenience. In hardened mode, missing or invalid tokens must be strictly rejected with `HTTP 401 Unauthorized`.
* **Plaintext Password Storage in `DEMO_USERS`**: Passwords in memory were plain strings (`password123`) instead of salted hashes (e.g., PBKDF2/bcrypt/Argon2).
* **Static Fallback Secret Key**: Fallback secret key in `config.py` was a static development string.

### 3. Current Authorization Weaknesses
* **Role Separation**: `REVIEWER` role has inspection rights but must be strictly blocked from triggering case finalisation or authoring officer orders.
* **Case Assignment Ownership**: Officer assignment should be checked to ensure accountability during determinations and manual corrections.

### 4. Evidence Storage Risks
* **Static File Mount**: `app.mount("/storage", StaticFiles(directory="storage"))` allows unauthenticated access to files in `storage/` if paths are known.
* **Derived vs Original Separation**: Derived artifacts (CLAHE, Otsu, overlays) must remain strictly segregated in `storage/derived/` with foreign key pointers to original immutable evidence in `storage/evidence/`.

### 5. File Upload Risks
* **Extension vs MIME vs Magic Bytes**: Ingestion currently checks extension and decodes with OpenCV. Need explicit MIME validation, strict size limits (25 MB), dimension validation, and sanitation against path traversal.
* **Server-Controlled Naming**: Verified that uploaded filenames are sanitized and prepended with UUIDs to avoid collision or directory escape.

### 6. API Exposure Risks
* **Unhandled Exceptions**: Need a generic catch-all exception handler to ensure unhandled Python exceptions do not leak stack traces, database schemas, or filesystem paths to client applications.
* **Safe Error Schema**: Standardize structured error responses (`error_code`, `message`, `path`).

### 7. CORS Risks
* **Wildcard Origins**: Need explicit environment-driven `ALLOWED_ORIGINS` (defaulting to `http://localhost:3000`, `http://127.0.0.1:3000`), rejecting `*` when credentials are enabled.

### 8. Secret / Configuration Risks
* **Environment Variables**: Need a clear `.env.example` template detailing `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `DATABASE_URL`, `ALLOWED_ORIGINS`, and `REPORT_VERIFICATION_BASE_URL`.

### 9. Audit-Chain Risks
* **Chain Continuity**: Verify that audit entries cannot be modified or deleted, and broken links are flagged during integrity scans.

### 10. Report Verification Risks
* **Placeholder Government URLs**: ReportLab PDF generator previously embedded a placeholder URL (`https://legalmetrix.gov.in/verify/{id}`) and used official Government of India titles.
* **Hardening Measure**: Parameterize verification URLs via `REPORT_VERIFICATION_BASE_URL` (defaulting to local/configured deployment) and use institutional terminology ("LegalMetriX Inspection Report", "Integrity Verification") without claiming uncertified official government authority.

### 11. Offline / PWA Readiness
* **Field Evidence Capture**: Field officers on unstable mobile connections require an offline evidence queue to capture photos, record view types (`FRONT`, `BACK`, etc.), and queue them locally for sync.
* **PWA Application Shell**: Service worker and Web App Manifest (`manifest.json`) for caching UI assets while strictly never caching sensitive tokens or confidential inspection reports in unsafe browser caches.

### 12. Data Synchronization Risks
* **Deduplication**: When an offline device reconnects, retry loops must not create duplicate evidence records on the server.
* **Server Authoritative**: Client never computes final SHA-256 hashes; the backend validates and computes hashes upon upload.

### 13. Production Deployment Risks
* **Database Concurrency**: SQLite with WAL mode (`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;`) is sufficient for current standalone workloads.
* **Security Headers**: Content-Security-Policy, X-Content-Type-Options, Referrer-Policy, and X-Frame-Options must be configured.

### 14. Existing Technical Debt
* **Health Check**: `GET /api/v1/health` should return detailed subsystem status (database, storage, version).
* **Structured Logging**: Introduce standard structured logging for authentication, evidence ingestion, OCR processing, and case finalisation.

---

## 3. Implementation Roadmap for Phase 7
1. **Security & Auth Hardening**: Enforce strict token requirement, salted password hashing, and configurable JWT secrets.
2. **API & CORS Hardening**: Environment-driven CORS, safe generic exception handlers, and security headers.
3. **Report Verification Hardening**: Configurable base URL and institutional terminology.
4. **Offline Sync Queue & PWA Integration**: IndexedDB/LocalStorage sync queue in frontend with online/offline detection, retry controls, and PWA manifest.
5. **System Health & Logging**: Subsystem health checks and structured audit logs.
6. **Backup & Recovery Documentation**: Create `docs/BACKUP_AND_RECOVERY.md`.
7. **Comprehensive Testing**: Implement `tests/integration/test_phase7_security_offline.py` and run full test suite.
