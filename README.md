# NIRIKSHAN — Legal Metrology Compliance & Inspection System
### Problem Statement Reference: SIH26034

> **Legal Metrology (Packaged Commodities) Rules, 2011 — Field Evidence Ingestion, Perception Pipeline, Deterministic Statutory Rule Engine & Officer Decision-Support Platform.**

---

## 1. Problem Statement & Context

Under the **Legal Metrology Act, 2009** and the **Legal Metrology (Packaged Commodities) Rules, 2011 (as amended)**, every pre-packaged commodity manufactured, packed, imported, or offered for sale in India must bear clear, prominent, and accurate statutory declarations:
1. Generic name of the commodity.
2. Net quantity in standard metric units (mass/volume/length/number).
3. Maximum Retail Price (MRP), inclusive of all taxes.
4. Unit Sale Price (USP) per standard base unit (₹/kg, ₹/g, ₹/L, ₹/ml, ₹/piece).
5. Name and complete address of the manufacturer, packer, or importer.
6. Country of origin for imported goods.
7. Consumer care contact details (designation, address, telephone, email).
8. Month and year of manufacture / packing / import.
9. Compliance with Rule 7 Principal Display Panel (PDP) area and minimum numeral font height standards.

### Challenges in Field Enforcement:
- **Manual Overhead**: Field inspectors must manually inspect thousands of retail SKUs, calculate unit sale price fractions, verify numeral heights with calipers, and transcribe addresses.
- **Miscalculation & Inconsistency**: Complex USP arithmetic across multi-unit conversions (e.g., ₹1.40/g vs ₹1400.00/kg) leads to human error.
- **Deceptive Packaging & Overlays**: Unauthorised price stickers superimposed over original MRP declarations.
- **Evidentiary Integrity**: Traditional paper memos lack cryptographic proof of physical packaging condition at the moment of inspection.

---

## 2. Project Overview

**NIRIKSHAN** is an institutional-grade, full-stack decision-support system designed to empower field inspection teams:
- **Multi-View Evidence Ingestion**: In-app camera and multi-panel upload (Front, Back, Side, Base) with SHA-256 hashing at ingestion.
- **Resilient Multi-Engine OCR**: High-speed local optical character recognition via ONNX Runtime (`rapidocr_onnxruntime`) and PaddleOCR.
- **Structured Semantic Extraction**: Advanced multi-line parsing of all 9 mandatory declarations with provenance tracking back to bounding boxes.
- **Deterministic Legal Metrology Rule Engine**: Pure Python `Decimal` arithmetic evaluation of Rules 6, 7, 8, and statutory amendments—**zero LLM hallucination in legal compliance judgments**.
- **Physical Coin Calibration**: Physical reference calibration (Standard ₹5 Indian coin, 23.0 mm) for physical millimeter-per-pixel scaling of font numerals.
- **Visual Forensic Tampering Checks**: Edge disparity and color variance heuristics to detect sticker overlay anomalies over printed prices.
- **Human-in-the-Loop Officer Review Desk**: Complete transparency allowing authorized officers to review extraction confidences, make logged manual corrections, and sign authoritative statutory determinations.
- **Cryptographic PDF Reports & QR Portal**: 3-part statutory inspection report with SHA-256 audit ledger hash chain and instant QR verification.

---

## 3. System Architecture

```
                                 NIRIKSHAN SYSTEM ARCHITECTURE
                                 
      +---------------------------------------------------------------------------------+
      |                           CLIENT / PRESENTATION LAYER                           |
      |   Next.js 14 App Router | React 18 | Tailwind CSS | Mobile Responsive UI (PWA) |
      |   Field Camera Stream | Multi-View Workbench | Review Desk | Verification Portal |
      +---------------------------------------+-----------------------------------------+
                                              | HTTPS / JSON REST API
                                              v
      +---------------------------------------------------------------------------------+
      |                             FASTAPI BACKEND SERVICE                             |
      |   Role-Based Access Control (JWT) | Case Lifecycle State Machine | SQLite / PG  |
      +-------------------+---------------------------------------+---------------------+
                          |                                       |
                          v                                       v
      +------------------------------------+   +----------------------------------------+
      |      PERCEPTION & VISION ENGINE    |   |     DETERMINISTIC STATUTORY ENGINE     |
      |  • RapidOCR (ONNX Runtime CPU)     |   |  • Legal Metrology (PC) Rules, 2011    |
      |  • PaddleOCR Fallback Engine       |   |  • Rule 6: Mandatory Declarations      |
      |  • OpenCV Adaptive Preprocessing   |   |  • Rule 6(1)(e): USP Decimal Math      |
      |  • Multi-Line Semantic Parser      |   |  • Rule 7: PDP Font Sizing Table       |
      |  • Sticker Anomaly Detector        |   |  • Rule 8: Non-Standard Metric Units   |
      |  • ₹5 Coin Physical Calibrator     |   |  • Pure Decimal Precision (No Float)   |
      +-------------------+----------------+   +-------------------+--------------------+
                          |                                        |
                          +-------------------+--------------------+
                                              |
                                              v
      +---------------------------------------------------------------------------------+
      |                     INTEGRITY, AUDIT & REPORTING SERVICES                       |
      |  • SHA-256 Cryptographic Hash-Chained Audit Ledger                              |
      |  • ReportLab 3-Part Statutory PDF Inspection Certificate Generator             |
      |  • Public Verification QR Engine with Cryptographic Digest                     |
      +---------------------------------------------------------------------------------+
```

---

## 4. Key Subsystems & Technical Details

### A. Resilient OCR & Semantic Extraction Pipeline
- **RapidOCR (ONNX Runtime)**: Operates locally on CPU without native C++ compilation bottlenecks, providing ~300ms execution per high-resolution packaging view.
- **Semantic Entity Recognizer**: Multi-line proximity scanner extracting:
  - Commodity Generic Name
  - Net Quantity with metric unit normalization
  - Maximum Retail Price (MRP)
  - Unit Sale Price (USP)
  - Manufacturer / Packer / Importer legal name and address block
  - Country of Origin
  - Consumer Care helpline phone and email
  - Month & Year of packaging / import and Best Before dates

### B. Deterministic Legal Metrology Rule Engine
- Legal compliance decisions are **never delegated to generative AI**.
- Uses pure deterministic rule packs with exact legal citations:
  - `RULE-DECL-COMMODITY-NAME`: Rule 6(1)(a)
  - `RULE-DECL-NET-QTY`: Rule 6(1)(b) & Second Schedule standard units
  - `RULE-DECL-MRP`: Rule 6(1)(c)
  - `RULE-DECL-MFR-PACKER`: Rule 6(1)(d)
  - `RULE-DECL-COUNTRY-ORIGIN`: Rule 6(1)(e)
  - `RULE-DECL-CONSUMER-CARE`: Rule 6(1)(g)
  - `RULE-DECL-DATE-MARKS`: Rule 6(1)(d) / Packaging date
  - `RULE-USP-CONSISTENCY`: Rule 6(1)(e) Proviso USP arithmetic
  - `RULE-FONT-HEIGHT-MINIMUM`: Rule 7 & Table 1 PDP font sizing
  - `RULE-OVERLAY-STICKER-FLAG`: Visual sticker overlay tampering detection

### C. Unit Sale Price (USP) Arithmetic Verification
Calculates statutory unit price using exact `Decimal` arithmetic:
$$\text{Calculated USP} = \frac{\text{Normalized MRP}}{\text{Normalized Net Quantity}}$$
Supports statutory sub-unit metric scaling (e.g. ₹1.40 / g vs ₹1400.00 / kg, or ₹0.15 / ml vs ₹150.00 / L) within a 5% rounding tolerance.

### D. Physical Reference Calibration (₹5 Coin)
- Calibrates pixel space against an Indian ₹5 coin (exact circular diameter: **23.0 mm**).
- Computes spatial scale factor:
  $$\text{Scale Factor} = \frac{23.0\text{ mm}}{\text{Detected Diameter in Pixels}}$$
- Enables accurate physical height measurement of printed numbers against Rule 7 minimum font height tables.

### E. Evidence Integrity & Cryptographic Audit Ledger
- Every uploaded image is hashed (`SHA-256`) immediately upon ingestion and stored immutably.
- Every state transition, OCR run, manual correction, and officer sign-off appends a new block to an **audit ledger hash chain**:
  $$\text{Block Hash}_n = \text{SHA-256}(\text{Block Hash}_{n-1} \,\|\, \text{Timestamp} \,\|\, \text{Action} \,\|\, \text{Payload})$$
- Ensures full tamper-evidence and chain-of-custody traceability.

### F. Mobile Field Responsiveness
- Fully responsive across **360×800**, **390×844**, and **412×915** mobile viewports.
- Stacked responsive cards for inspection queues and extracted field tables.
- Sticky mobile quick-action bar with one-tap camera capture for retail shelf operations.

---

## 5. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide Icons |
| **Backend** | Python 3.11, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.0 |
| **Perception / Vision** | RapidOCR (`rapidocr_onnxruntime`), OpenCV (`opencv-python`), Pillow, NumPy |
| **Document Generation** | ReportLab 4.x (PDF generation), PyQRCode |
| **Database** | SQLite 3 (WAL mode) / PostgreSQL compatible |
| **Testing** | pytest, pytest-asyncio, httpx, Playwright / Chrome subagent |

---

## 6. Installation & Setup

### Prerequisites
- **Python 3.11+** installed
- **Node.js 18+** & `npm` installed
- Git installed

### 1. Clone the Repository
```bash
git clone https://github.com/rajputjay00/SIH26034.git
cd SIH26034
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment variables
cp backend/.env.example backend/.env
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env.local
cd ..
```

---

## 7. Running Locally

### Option A: Using Windows Batch Scripts
```cmd
# Launch both backend and frontend concurrently
start-all.bat
```
*(Or run `start-backend.bat` and `start-frontend.bat` in separate terminals).*

### Option B: Manual Startup

**Terminal 1 (FastAPI Backend):**
```bash
# Windows PowerShell:
$env:PYTHONPATH=".;backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

# Linux/macOS:
# export PYTHONPATH=".:backend"
# uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 (Next.js Frontend):**
```bash
cd frontend
npm run dev
```

### Service Access URLs:
- **NIRIKSHAN Web Application**: `http://localhost:3000`
- **FastAPI REST API**: `http://127.0.0.1:8000`
- **Interactive Swagger Documentation**: `http://127.0.0.1:8000/docs`

---

## 8. Verification & Testing

### Run Backend Test Suite (115 Integration & Unit Tests)
```bash
$env:PYTHONPATH=".;backend"
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

### Run Frontend Production Build
```bash
cd frontend
npm run build
```

---

## 9. AI & Legal Decision Boundary Statement

> [!IMPORTANT]
> **STATUTORY BOUNDARY & LEGAL NOTICE**
> 
> 1. **Perception vs. Adjudication**: Artificial Intelligence and Computer Vision subsystems in NIRIKSHAN are strictly utilized for **optical character recognition, geometric bounding-box extraction, and visual quality assessment**.
> 2. **Deterministic Rules**: Legal compliance checks are evaluated by **deterministic, mathematically verifiable Python rule algorithms** reflecting published Legal Metrology Rules, 2011 schedules.
> 3. **Authorised Officer Primacy**: The system acts strictly as an **investigative decision-support tool**. The system **does not make autonomous legal determinations**. The final statutory order and legal determination remain the sole prerogative of the Authorised Legal Metrology Officer.
> 4. **Institutional Scope**: NIRIKSHAN is an independent software engineering prototype developed for Smart India Hackathon (SIH26034). It does not claim official Government of India endorsement, certification, or autonomous court admissibility.

---

## 10. Known Limitations

- **Complex Curved Packaging**: Highly reflective metallic foils or severely crumpled pouches may require manual lighting adjustment or manual field correction.
- **Extreme Font Angles**: Extreme perspective distortion (> 45°) requires image re-capture using the multi-view guidance frame.
- **Physical Scale Requirement**: Precise numeral millimeter measurement under Rule 7 requires placement of a standard physical calibration reference (e.g. standard ₹5 coin) on the same plane as the packaging label.

---

## 11. License

Developed for **Smart India Hackathon (SIH26034)**. Distributed under the MIT License. See [LICENSE](LICENSE) for details.
