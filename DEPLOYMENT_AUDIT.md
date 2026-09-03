# NIRIKSHAN — Production Deployment Audit Report
**Problem Statement Reference**: SIH26034  
**Date**: September 3, 2026  
**Audited By**: Antigravity Deployment Assurance Subsystem

---

## 1. Executive Summary & Deployment Architecture Decision

NIRIKSHAN is an evidence-oriented Legal Metrology compliance verification and decision-support system. It consists of:
1. **Frontend**: Next.js 14 App Router, React 18, Tailwind CSS, TypeScript.
2. **Backend**: FastAPI (Python 3.11), SQLAlchemy 2.0, Pydantic v2, ReportLab, RapidOCR (ONNX Runtime CPU), OpenCV.

### Target Hosting Model:
- **Frontend**: **Vercel** (Global Edge CDN, serverless SSR, zero-configuration Next.js deployment).
- **Backend**: **Dedicated Container / PaaS with Persistent Volume** (e.g., Render, Railway, Fly.io, AWS EC2, or Docker VPS).

> [!WARNING]
> **CRITICAL ARCHITECTURAL ASSESSMENT: WHY BACKEND MUST NOT BE DEPLOYED ON VERCEL SERVERLESS**
> 1. **Heavy Computer Vision & Machine Learning Binaries**: RapidOCR, ONNX Runtime (`onnxruntime`), OpenCV (`opencv-python`), and Pillow exceed Vercel's Serverless Function size limit (50 MB zipped / 250 MB uncompressed).
> 2. **Ephemeral / Read-Only Filesystem**: Serverless execution environments possess no persistent disk (only ephemeral `/tmp` with limited lifecycle). NIRIKSHAN requires persistent evidence storage (SHA-256 packaging views), derived overlays, PDF reports, and SQLite database storage.
> 3. **Perception Pipeline Latency**: Multi-view high-resolution OCR and visual anomaly processing may take 2–5 seconds per multi-image batch, risking timeouts on serverless cold starts.
> 4. **Stateful Audit Ledger**: The SHA-256 hash-chained audit ledger and SQLite WAL journal require a persistent file handle.
> 
> **Conclusion**: The FastAPI backend MUST be deployed on a persistent container or VM runtime (Render / Railway / Docker / VPS). The Next.js frontend on Vercel communicates with the backend via HTTPS REST API.

---

## 2. Component Audits

### A. Next.js Frontend Audit
1. **API Abstraction**:
   - Centralized in `frontend/lib/api.ts`.
   - Reads backend URL from `process.env.NEXT_PUBLIC_API_URL` or `process.env.NEXT_PUBLIC_API_BASE_URL` with graceful fallback to `http://127.0.0.1:8000/api/v1`.
2. **Rewrites / Proxy**:
   - Configured in `frontend/next.config.js` (`/api/:path*` $\rightarrow$ `BACKEND_API_URL` or local).
3. **Client-Side Secrets**:
   - **Audit Result**: Zero secrets exposed. Authentication tokens (JWT) are stored in client `localStorage` after explicit login.
4. **Production Build Status**:
   - Compiles cleanly (`npm run build`) with zero TypeScript or CSS errors.

### B. FastAPI Backend Audit
1. **Entrypoint**:
   - `backend/app/main.py` exposes `app = FastAPI(...)`.
   - Production launch command: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT` or with `PYTHONPATH=".;backend" uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
2. **CORS Configuration**:
   - Configured in `backend/app/main.py` via `CORSMiddleware`.
   - Reads `ALLOWED_ORIGINS` from environment variable (comma-separated list of allowed origins).
   - Strict `allow_credentials=True` requires explicit origin matching (never wildcard `*` in production).
3. **Database & ORM**:
   - Uses SQLAlchemy 2.0 (`backend/app/core/database.py`).
   - SQLite with WAL (Write-Ahead Logging) mode and foreign keys enabled.
   - Automatically executes `Base.metadata.create_all(bind=engine)` on startup.
   - Compatible with PostgreSQL by supplying a `postgresql://` URI in `DATABASE_URL`.
4. **Storage & File System Paths**:
   - Evidence directory: `storage/evidence` (configured via `STORAGE_EVIDENCE_PATH`).
   - Derived overlays: `storage/derived` (configured via `STORAGE_DERIVED_PATH`).
   - PDF Reports: `storage/reports` (configured via `STORAGE_REPORTS_PATH`).
   - Static mounting: `/storage` mounted via `app.mount("/storage", StaticFiles(directory="storage"), name="storage")`.

---

## 3. Environment Variables Matrix

### Frontend Environment Variables (`frontend/.env.example`)
| Variable Name | Required / Optional | Description | Example Format |
| :--- | :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | **Required in Prod** | Base URL of the deployed FastAPI backend service | `https://nirikshan-api.onrender.com` |
| `NEXT_PUBLIC_APP_NAME` | Optional | Institutional brand title displayed in browser | `NIRIKSHAN — Legal Metrology Inspection System` |

### Backend Environment Variables (`backend/.env.example`)
| Variable Name | Required / Optional | Description | Example Format |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | **Required** | Deployment environment mode | `production` (or `development`) |
| `DEBUG` | **Required** | Debug mode toggle (must be `False` in prod) | `False` |
| `SECRET_KEY` | **Required** | Cryptographic secret for signing JWT officer session tokens | `Generate a 64-char random hex string` |
| `ALGORITHM` | Optional | JWT signature algorithm (defaults to `HS256`) | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | Session expiration duration (default 1440 min = 24h) | `1440` |
| `DATABASE_URL` | Optional | Database connection URI (defaults to SQLite WAL) | `sqlite:///./legalmetrix.db` |
| `ALLOWED_ORIGINS` | **Required in Prod** | Comma-separated list of permitted frontend origins | `https://nirikshan.vercel.app,http://localhost:3000` |
| `REPORT_VERIFICATION_BASE_URL` | **Required in Prod** | Base URL embedded in report QR codes for public verification | `https://nirikshan.vercel.app/verify` |
| `STORAGE_EVIDENCE_PATH` | Optional | Filesystem path for ingested packaging evidence | `storage/evidence` |
| `STORAGE_DERIVED_PATH` | Optional | Filesystem path for derived bounding-box crops | `storage/derived` |
| `STORAGE_REPORTS_PATH` | Optional | Filesystem path for sealed ReportLab PDF files | `storage/reports` |
| `PORT` | Optional (PaaS injected) | Server listener port | `8000` |

---

## 4. Filesystem Storage Classification

| Storage Category | Specific Files | Storage Classification | Production Persistence Strategy |
| :--- | :--- | :--- | :--- |
| **Evidence Images** | `storage/evidence/*.jpg`, `*.png` | **Persistent Application Data** | Mounted Persistent Volume (Disk) on container / VM host |
| **Derived Crops & Overlays** | `storage/derived/*.jpg` | **Persistent Application Data** | Mounted Persistent Volume (Disk) on container / VM host |
| **Generated PDF Reports** | `storage/reports/*_verified.pdf` | **Persistent Application Data** | Mounted Persistent Volume (Disk) on container / VM host |
| **SQLite Database** | `legalmetrix.db`, `-wal`, `-shm` | **Persistent Application Data** | Mounted Persistent Volume (Disk) or PostgreSQL connection |
| **OCR Models / Cache** | RapidOCR ONNX model weights | **Static / Runtime Asset** | Cached in local image layer at container build time |
| **Temporary Uploads** | `tmp/`, `/tmp/` | **Temporary Runtime Storage** | Ephemeral system scratch directory |

---

## 5. Potential Deployment Blockers & Mitigation

1. **CORS Protocol Mismatch**:
   - *Risk*: Frontend deployed on HTTPS (`https://nirikshan.vercel.app`) calling an HTTP backend (`http://...`) results in browser Mixed Content blocks.
   - *Mitigation*: Backend MUST be deployed behind an SSL-terminating reverse proxy / PaaS domain with HTTPS enabled.
2. **String-vs-List Parsing in `pydantic-settings`**:
   - *Risk*: `ALLOWED_ORIGINS` passed as a comma-separated string in environment variables may fail validation in Pydantic v2 `BaseSettings`.
   - *Mitigation*: Implemented a robust pre-validator / parsing function in `backend/app/core/config.py` that safely splits comma-separated strings into lists.
3. **Relative Path Resolution on Linux Container**:
   - *Risk*: Windows backslashes `\` or working directory path differences between local Windows and Linux container.
   - *Mitigation*: All paths in `config.py` and `report_service.py` use `os.path` / `pathlib.Path` with POSIX forward slashes.

---

## 6. Recommended Production Deployment Topology

```
                  Internet Users / Officers (Mobile & Desktop)
                                     |
                                     v
                   +----------------------------------+
                   |          Vercel Edge CDN         |
                   |   (Next.js 14 Frontend PWA)      |
                   |   https://nirikshan.vercel.app   |
                   +-----------------+----------------+
                                     |
                                     | HTTPS REST API Calls
                                     v
                   +----------------------------------+
                   |    PaaS / Docker VPS (Linux)     |
                   |    (FastAPI + Uvicorn Worker)    |
                   | https://nirikshan-api.onrender   |
                   +-----------------+----------------+
                                     |
                                     +-------------------------------+
                                     |                               |
                                     v                               v
                     +-------------------------------+   +-----------------------+
                     |    Mounted Persistent Disk    |   |     RapidOCR ONNX     |
                     |  • Evidence Packaging Views   |   |   Local CPU Engine    |
                     |  • SHA-256 PDF Reports        |   |   Zero External API   |
                     |  • SQLite WAL Database        |   +-----------------------+
                     +-------------------------------+
```
