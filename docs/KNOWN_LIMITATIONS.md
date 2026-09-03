# LegalMetriX — Known Limitations & System Boundaries

## 1. Statutory & Architectural Boundaries
* **Sole Statutory Decision-Maker**: LegalMetriX is an **evidence-oriented decision-support system**. The Authorised Officer remains the sole statutory authority for issuing legal orders or notices under the Legal Metrology Act, 2009. The system does not possess automated penal authority.
* **Rule 7 PDP Area Dependency**: Rule 7 font height thresholds depend strictly on the statutory Principal Display Panel (PDP) area ($A \text{ in cm}^2$). If the package dimensions or PDP area cannot be computed or provided, the system marks the font compliance check as `REQUIRES_REVIEW` rather than guessing a threshold.

---

## 2. Technical & Hardware Boundaries
* **Standalone Database**: Persistence is implemented on SQLite with WAL (Write-Ahead Logging) and Foreign Key pragma enforcement. High-throughput distributed multi-node clustering would require migrating to PostgreSQL in enterprise production phases.
* **Browser LocalStorage Quotas**: Offline evidence capture queue utilizes browser LocalStorage (~50MB quota). Field officers conducting large-batch offline inspections (e.g. >30 high-res photos) should synchronize whenever network connectivity is briefly restored.
* **Camera Hardware Limitations**: In-app camera capture is optimized for modern mobile browsers with `facingMode: 'environment'`. On laptops lacking autofocus rear cameras, users can utilize the built-in webcam fallback or high-resolution file upload.
* **Reference Object Alignment**: ₹5 coin physical calibration requires the coin to be placed on approximately the same plane as the declaration text for accurate millimeter-per-pixel scaling. Extreme perspective tilts require manual review.

---

## 3. Scope Exclusions (Phase 8 Locked)
* External live Indian State Department ERP integrations (e-Metrology state portals) are architecturally decoupled and reserved for enterprise deployment.
* Hardware PKI smartcard USB token digital signing is simulated via cryptographic SHA-256 hash chaining and institutional audit logs.
