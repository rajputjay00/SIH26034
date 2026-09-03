# LegalMetriX — Architecture Lock & System Foundation

## 1. System Architecture Overview
LegalMetriX is a government-grade Legal Metrology packaged commodity compliance and inspection system designed with strict separation between machine perception, deterministic legal validation, and authoritative human officer review.

```
+----------------------------------------------------------------------------------------------------+
|                                    LEGALMETRIX SYSTEM ARCHITECTURE                                 |
+----------------------------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------------------------+
| FRONTEND LAYER (Next.js App Router, TypeScript, Tailwind CSS, Lucide Icons)                        |
| • White-First Modern Government Interface                                                          |
| • Viewfinder, Evidence Gallery & Bounding Box Inspection Workbench                                 |
| • Officer Manual Correction Loop (Marks determination STALE -> requests re-analysis)               |
+-------------------------------------------------+--------------------------------------------------+
                                                  | REST API (JSON / Multipart)
                                                  v
+----------------------------------------------------------------------------------------------------+
| BACKEND APPLICATION LAYER (FastAPI, Python 3.11+, Pydantic v2)                                     |
|                                                                                                    |
| +-------------------------+  +--------------------------+  +-------------------------------------+  |
| | API Router (/api/v1)    |  | Core Security & Auth     |  | Case Service & Lifecycle            |  |
| | Cases, Evidence, Auth,  |  | Role Enforcer            |  | State Transitions:                  |  |
| | Extraction, Audit,      |  | (ADMIN, OFFICER,         |  | DRAFT -> PROCESSING ->              |  |
| | Findings, Health        |  |  REVIEWER)               |  | PENDING_REVIEW -> FINALISED         |  |
| +-------------------------+  +--------------------------+  +-------------------------------------+  |
|                                                                                                    |
| +------------------------------------------------------------------------------------------------+ |
| | TRUST & PROCESSING BOUNDARIES                                                                  | |
| |                                                                                                | |
| | [ AI / MACHINE PERCEPTION ]        [ DETERMINISTIC RULE ENGINE ]    [ AUTHORITATIVE OFFICER ]  | |
| | • OpenCV Quality Gate (Phase 2)    • 10 Mandatory Declarations      • Verifies extracted data  | |
| | • PaddleOCR Text/Boxes (Phase 2)   • Unit Sale Price Math           • Overrides OCR mistakes   | |
| | • Structured Field Extraction      • Font Height Calculation        • Confirms sticker signals | |
| | • Character Region Proposal        • Rule Versioning (v1.0.0 DCA)   • Authoritative compliance | |
| | * AI NEVER DECIDES COMPLIANCE      * DETERMINISTIC EVALUATION ONLY  • Signs & Finalises Case   | |
| +------------------------------------------------------------------------------------------------+ |
|                                                                                                    |
| +----------------------------------+  +----------------------------------------------------------+ |
| | Audit Service & Hash Chain       |  | Provenance Tracking Service                              | |
| | • SHA-256 Append-Only Chain      |  | • Full Source Evidence Traceability                      | |
| | • verify_chain() Integrity Check |  | • Bounding Box Coordinates & Extraction Origin History   | |
| +----------------------------------+  +----------------------------------------------------------+ |
+-------------------------------------------------+--------------------------------------------------+
                                                  | SQLAlchemy 2.0 ORM
                                                  v
+----------------------------------------------------------------------------------------------------+
| PERSISTENCE LAYER (SQLite with Write-Ahead Logging [WAL] Mode)                                     |
| • Tables: inspection_cases, evidence_items, calibration_data, extracted_fields,                    |
|   field_corrections, rule_findings, audit_entries, generated_reports                               |
| • Clean ORM boundary preserved for future PostgreSQL migration (P2)                                |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Core Domain Entities & Relationships
1. **InspectionCase:** Primary aggregate root managing inspection state lifecycle (`DRAFT` $\rightarrow$ `PROCESSING` $\rightarrow$ `PENDING_REVIEW` $\rightarrow$ `FINALISED`).
2. **EvidenceItem:** Original evidence files with immediate SHA-256 hash calculation, view roles (`FRONT`, `BACK`, `SIDE`, `BASE`, `OTHER`), and immutable storage references.
3. **CalibrationData:** Physical scale reference measurements and pixel-to-millimeter ratio data.
4. **ExtractedField:** Field-level extraction preserving raw OCR value, normalized value, unit, confidence score, bounding box, and origin (`AI`, `OFFICER`, `SYSTEM`).
5. **FieldCorrection:** Officer audit record of corrections preserving previous value, corrected value, officer identifier, and correction timestamp.
6. **RuleFinding:** Statutory rule evaluation findings storing citation, severity, message, calculation metadata, and result state (`PASS`, `FAIL`, `REVIEW`, `NOT_APPLICABLE`).
7. **AuditEntry:** Cryptographic append-only hash-chained event entry linking actor, action, timestamp, payload hash, and previous entry hash.
8. **GeneratedReport:** Report metadata entity recording generated report number, canonical inspection hash, and output PDF file hash.

---

## 3. Trust & Operational Boundaries
* **AI & LLM Boundary:** AI algorithms perform optical character recognition and structured parsing only. Under no circumstances does AI issue legal compliance determinations or certify packages.
* **Deterministic Rule Engine:** Statutory validation is executed strictly through deterministic Python code mapping directly to Legal Metrology (Packaged Commodities) Rules, 2011 and DCA Gazette amendments.
* **Human Officer Review:** The enforcement officer holds final authority for reviewing evidence, correcting OCR errors, confirming sticker/price overwrite suspicions, and finalizing inspection cases.
* **Audit Chain Integrity:** The system implements an append-only SHA-256 hash chain with automated `verify_chain()` validation. The system explicitly refrains from claiming "tamper-proof" status.

---

## 4. Unresolved Statutory Items & Configuration Architecture
The reference audit identified category-specific net quantity tolerances (MPE) and the statutory font size threshold matrix as items requiring exact schedule verification from official DCA Gazette publications. In Phase 1:
- Configurable rule definitions (`LegalRuleDefinition` and `RulePackMetadata`) are implemented.
- No guessed or fabricated statutory thresholds are hardcoded.
- Statutory lookup tables will be populated from verified DCA Gazette sources in Phase 3.
