# NIRIKSHAN Homepage UI Audit & Brand Asset Integration Plan

## 1. Executive Summary & Objective
This audit analyzes the existing frontend structure of the NIRIKSHAN / Legal Metrology platform in preparation for a comprehensive homepage UI redesign and brand asset integration.
The redesign elevates the application to an institutional, premium, white-first government-grade portal inspired by high-standard institutional portals (with utility bar, main header, hero carousel, platform highlights, core capabilities, inspection workflow timeline, live activity queues, and structured footer) while strictly preserving all existing backend APIs, verification routes, inspection workflows, evidence pipelines, and statutory decision-support boundaries.

---

## 2. Current Frontend Architecture Audit

### 2.1 Existing Routes & Pages
* **`/` (Current Dashboard)**: Houses KPI summary metric cards, Operational Review Queues (High Priority, Ready for Finalisation, Standard Review), Statutory Violation Breakdown bars, and Recent Inspection feed.
* **`/inspections` (Inspection History & Queue Console)**: Filtered inspection table with search, status filters, and pagination.
* **`/cases/[id]` (8-Tab Case Review Workbench)**:
  - Tab 1: *Overview & Inspection Copilot*
  - Tab 2: *Evidence Gallery & Multi-View Ingestion*
  - Tab 3: *Structured Declarations & Audited Corrections*
  - Tab 4: *Rule Findings & "Show Me Where" Bounding Box Visualizer*
  - Tab 5: *Rule 7 Physical Sizing & ₹5 Coin Calibration*
  - Tab 6: *Visual Forensics & Sticker Anomaly Detection*
  - Tab 7: *Forensic PDF Reports*
  - Tab 8: *Cryptographic Audit Trail*
* **`/cases/[id]/evidence` (In-App Camera & Field Evidence Ingestion)**: Multi-view capture modal (`facingMode: 'environment'`, live framing, quality feedback) and offline sync queue (`OfflineEvidenceQueue`).
* **`/verify/[reportId]` (Public Read-Only Verification Portal)**: Independent public route confirming SHA-256 PDF byte hashes and statutory report authenticity.

### 2.2 Reusable Components
* `frontend/components/layout/Header.tsx` & `Footer.tsx` — To be upgraded to the institutional Utility Bar + Main Header + Navigation + Structured Footer with brand visual asset.
* `frontend/components/ui/NetworkStatusBanner.tsx` — Real-time offline/online sync queue indicator (maintained in root layout).
* `frontend/components/evidence/CameraCaptureModal.tsx` & `EvidenceUploader.tsx` — Field evidence capture tools (retained and linked).
* `frontend/components/cases/InspectionCopilot.tsx` — Case-level review copilot (retained).

---

## 3. Brand Identity & Asset Integration Plan

### 3.1 Brand Identity Standards
* **Primary Brand**: **NIRIKSHAN**
* **Descriptor**: **LEGAL METROLOGY COMPLIANCE & INSPECTION SYSTEM**
* **Tagline**: **INSPECT • VERIFY • ASSURE**
* **Color Palette**:
  - Primary Navy: `#0B2A4A`
  - Professional Blue: `#1769AA`
  - Saffron Accent: `#F28C28`
  - Green Confirmation: `#2F8F6B`
  - White Surface: `#FFFFFF`
  - Light Background: `#F7F9FC`
  - Subtle Border: `#E5EAF0`

### 3.2 Asset Directory Layout
```
frontend/public/assets/
├── branding/
│   ├── nirikshan-logo.png
│   ├── nirikshan-logo.svg
│   ├── nirikshan-logo-white.svg
│   └── nirikshan-mark.svg
├── banners/
│   ├── banner-01.png (Flow / 5 Key Steps: Capture, Verify, Assess, Record, Analyze)
│   ├── banner-02.png (Inspect. Verify. Assure Compliance. / Mobile Field App)
│   ├── banner-03.png (Precision in Every Inspection / Evidence-Led Pouch Scan)
│   ├── banner-04.png (Deterministic Compliance / Rule Engine & Sizing)
│   └── banner-05.png (Complete Inspection Traceability & Reporting)
└── footer/
    └── footer-visual.png
```

---

## 4. Homepage Structure (Editorial & Institutional Rhythm)

1. **Institutional Utility Bar** (28–34px): System identifier, Help, Accessibility, Language indicator.
2. **Main Header & Brand Area**: Final NIRIKSHAN logo with ruler-lens mark, quick case search, user status / Sign In.
3. **Primary Navigation Bar**: Home, Inspections, Evidence, Compliance, Reports, Analytics, Resources (with saffron active indicator).
4. **Hero Banner Carousel**: 5-second automatic crossfade with pause on hover/focus, dots pagination, previous/next controls, and touch swipe.
5. **Platform Highlight Strip**: Evidence First, Officer Driven, Deterministic Compliance, Transparent & Traceable, Insightful Analytics.
6. **About Nirikshan**: Editorial narrative with visual 6-step flow (`Product -> Evidence -> OCR -> Assessment -> Review -> Report`).
7. **Core Capabilities Grid**: 6 distinct capability blocks (Field Capture, Evidence Management, OCR Extraction, Compliance Engine, Visual Sizing, Forensic Reports).
8. **Inspection Workflow Timeline**: Horizontal interactive timeline on desktop, vertical on mobile (`Capture -> Verify -> Extract -> Assess -> Review -> Report`).
9. **Evidence & Traceability Split Section**: Deep dive into SHA-256 integrity, OpenCV quality gate, and bounding box provenance.
10. **Compliance Intelligence Section**: Rule 6 & Rule 7 deterministic rule execution and officer decision-support distinction.
11. **Live Activity & Review Queues**: Live query-backed database view of High Priority Review Cases, Ready for Finalisation, and Recent Reports.
12. **Resources & Guidance**: Official inspection guides, rule references (Legal Metrology PC Rules, 2011), and system documentation.
13. **Institutional Structured Footer**: Complete footer navigation with branding, disclaimer, copyright, and the uploaded footer visual asset.

---

## 5. Non-Destructive Guarantee
* Backend APIs (`/api/v1/...`), SQLite database, authentication, RBAC, Rule 7 algorithms, and existing `/cases/[id]` routes remain completely intact and functional.
