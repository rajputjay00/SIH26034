# LegalMetriX — Backup, Disaster Recovery & Evidence Lifecycle Guide

## 1. Overview
LegalMetriX operates as an **evidence-oriented decision-support and inspection system**. 
To ensure legal defensibility, inspection continuity, and audit trail integrity, this document establishes the backup strategy, data classification, and restoration sequence.

---

## 2. Data Classification & Recovery Hierarchy

| Data Asset | Location | Irreplaceable? | Can be Regenerated? | Backup Priority |
| :--- | :--- | :---: | :---: | :---: |
| **SQLite Database** (`legalmetrix.db`) | Workspace Root | **YES** | NO (contains case records, officer remarks, determinations, corrections, audit logs) | **CRITICAL** (Daily / Hourly WAL snapshots) |
| **Original Evidence Files** | `storage/evidence/{case_id}/*` | **YES** | NO (Original photograph bytes hashed via SHA-256) | **CRITICAL** (Continuous append replication) |
| **Generated Legal Reports** | `storage/reports/{case_id}/*` | **YES** | PARTIALLY (PDFs can be re-rendered, but exact timestamps/hashes must match database registration) | **HIGH** |
| **Derived Preprocessed Images** | `storage/derived/{case_id}/*` | NO | **YES** (Can be recomputed via OpenCV CLAHE/Otsu from original evidence) | MEDIUM |
| **Derived OCR Polygons** | Database records | NO | **YES** (Can be re-extracted via PaddleOCR from original evidence) | LOW |

---

## 3. Irreplaceable Evidence Preservation Principles

1. **Original Evidence Immutability**:
   - Original JPEG/PNG frames captured by officers or uploaded from files are stored with server-calculated SHA-256 hashes.
   - Files in `storage/evidence/` must **NEVER be modified, cropped, or overwritten in place**.
2. **Audit Trail Continuity**:
   - The SQLite database stores cryptographic SHA-256 hash chains linking sequential inspection events (`previous_hash -> current_hash`).
   - Restoring a database without its corresponding `storage/evidence/` directory will result in audit verification failure.

---

## 4. Standard Backup Procedures

### 4.1 Database Backup (SQLite WAL-Safe)
Because SQLite runs with `PRAGMA journal_mode=WAL;`, simply copying `legalmetrix.db` while transactions are active can cause inconsistency. Use SQLite's backup API or command line:

```bash
# Safely snapshot database
sqlite3 legalmetrix.db ".backup 'backups/db/legalmetrix_$(date +%Y%m%d_%H%M%S).db'"
```

### 4.2 Storage Artifacts Backup
```bash
# Synchronize immutable evidence files to secure backup volume
rsync -avz --ignore-existing storage/evidence/ backups/storage/evidence/
rsync -avz --ignore-existing storage/reports/ backups/storage/reports/
```

---

## 5. Disaster Recovery & Restoration Sequence

In the event of hardware failure, disk corruption, or server migration, follow this precise sequence:

```
[ STEP 1: RESTORE ENVIRONMENT & CONFIGURATION ]
  ├── Deploy application code and Python virtual environment
  └── Configure `.env` with production SECRET_KEY and REPORT_VERIFICATION_BASE_URL

[ STEP 2: RESTORE IRREPLACEABLE ORIGINAL EVIDENCE ]
  └── Copy backed up `storage/evidence/` directory into workspace storage

[ STEP 3: RESTORE DATABASE ]
  └── Copy backed up `legalmetrix.db` into workspace root

[ STEP 4: RESTORE OR REGENERATE REPORTS & DERIVED ARTIFACTS ]
  └── Copy backed up `storage/reports/` or trigger report regeneration

[ STEP 5: INTEGRITY VERIFICATION SCAN ]
  ├── Run backend test suite: `pytest tests/ -v`
  └── Execute audit chain verification on active cases (`AuditService.verify_chain`)
```

---

## 6. Retention Policies & Purging Guidelines

* **Active Cases**: Retained indefinitely during review and adjudication.
* **Finalised Cases**: Sealed with immutable officer decision, timestamp, remarks, and PDF certificates.
* **Derived Caches**: Preprocessing temporary files in `storage/derived/` may be safely purged during maintenance, as they can be reconstructed deterministically from original evidence.
