import os
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    Image as RLImage
)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import qr
from reportlab.pdfgen import canvas

from app.core.config import settings
from app.models.domain import (
    InspectionCase,
    EvidenceItem,
    ExtractedField,
    RuleFinding,
    VisualMeasurement,
    VisualAnomaly,
    GeneratedReport,
    CaseStatus,
    FindingStatus,
    OverallDetermination
)
from app.services.audit_service import AuditService
from app.utils.errors import ResourceNotFoundError, ValidationError


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and render total page count
    along with official footer metadata and running headers for page 2+.
    """
    case_number: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()

        # Running header on Page 2+
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(colors.HexColor("#0f2942"))
            self.drawString(36, A4[1] - 24, "NIRIKSHAN")

            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawString(88, A4[1] - 24, "•   Inspection & Evidence Report")

            if self.case_number:
                self.drawRightString(A4[0] - 36, A4[1] - 24, f"Case: {self.case_number}")

            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, A4[1] - 28, A4[0] - 36, A4[1] - 28)

        # Bottom Footer on all pages
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748b"))

        # Footer divider line
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 38, A4[0] - 36, 38)

        # Footer text
        disclaimer = "NIRIKSHAN — Legal Metrology Compliance & Inspection System  •  Statutory Decision-Support Record"
        self.drawString(36, 26, disclaimer)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 36, 26, page_str)
        self.restoreState()


class ReportService:
    """
    Government-Grade Evidence-Oriented PDF Inspection Report Generator & Integrity Verifier.
    Integrates SHA-256 hashing, immutable versioning, QR verification, and append-only audit chain.
    """

    BASE_STORAGE_PATH = os.path.join("storage", "reports")

    @classmethod
    def generate_inspection_report(
        cls,
        db: Session,
        inspection_id: str,
        officer_id: str,
        force_regenerate: bool = False
    ) -> GeneratedReport:
        case = db.query(InspectionCase).filter(InspectionCase.inspection_id == inspection_id).first()
        if not case:
            raise ResourceNotFoundError("InspectionCase", inspection_id)

        # Guard: Check case status. If finalised, enforce strict versioning
        existing_reports = db.query(GeneratedReport).filter(
            GeneratedReport.inspection_id == inspection_id
        ).order_by(GeneratedReport.version.desc()).all()

        current_version = 1
        if existing_reports:
            if not force_regenerate and existing_reports[0].status == "GENERATED":
                return existing_reports[0]
            current_version = existing_reports[0].version + 1

        report_id = str(uuid.uuid4())
        report_dir = os.path.join(cls.BASE_STORAGE_PATH, inspection_id, report_id)
        os.makedirs(report_dir, exist_ok=True)
        pdf_filename = f"v{current_version}.pdf"
        pdf_path = os.path.join(report_dir, pdf_filename)

        # Gather case details
        evidence_items = db.query(EvidenceItem).filter(EvidenceItem.inspection_id == inspection_id).all()
        extracted_fields = db.query(ExtractedField).filter(ExtractedField.inspection_id == inspection_id).all()
        findings = db.query(RuleFinding).filter(RuleFinding.inspection_id == inspection_id).all()
        measurements = db.query(VisualMeasurement).filter(VisualMeasurement.inspection_id == inspection_id).all()
        anomalies = db.query(VisualAnomaly).filter(VisualAnomaly.inspection_id == inspection_id).all()

        # Build PDF with ReportLab
        cls._build_pdf(
            pdf_path=pdf_path,
            case=case,
            report_id=report_id,
            version=current_version,
            evidence_items=evidence_items,
            extracted_fields=extracted_fields,
            findings=findings,
            measurements=measurements,
            anomalies=anomalies,
            generated_at=datetime.now(timezone.utc)
        )

        # Compute SHA-256 of exact PDF bytes
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        report_sha256 = hashlib.sha256(pdf_bytes).hexdigest()

        # Save Report Record in Database
        report_record = GeneratedReport(
            report_id=report_id,
            inspection_id=inspection_id,
            version=current_version,
            report_type="INSPECTION_SUMMARY",
            file_reference=pdf_path,
            sha256=report_sha256,
            status="GENERATED",
            generated_by=officer_id,
            generated_at=datetime.now(timezone.utc)
        )
        db.add(report_record)
        db.commit()
        db.refresh(report_record)

        # Record in Append-Only Audit Chain
        action_name = "REPORT_REGENERATED" if current_version > 1 else "REPORT_GENERATED"
        AuditService.record_event(
            db=db,
            inspection_id=inspection_id,
            actor_id=officer_id,
            action=action_name,
            entity_type="GeneratedReport",
            entity_id=report_id,
            metadata={
                "version": current_version,
                "report_sha256": report_sha256,
                "file_reference": pdf_path,
                "force_regenerate": force_regenerate
            }
        )

        return report_record

    @classmethod
    def verify_report_integrity(cls, db: Session, report_id: str, actor_id: str = "PUBLIC_VERIFIER") -> Dict[str, Any]:
        """
        Public/safe verification endpoint verifying computed PDF bytes against stored SHA-256 fingerprint.
        """
        report = db.query(GeneratedReport).filter(GeneratedReport.report_id == report_id).first()
        if not report:
            return {
                "report_id": report_id,
                "version": 0,
                "exists": False,
                "integrity_status": "REPORT_NOT_FOUND",
                "message": "Report record not found in system repository."
            }

        case = db.query(InspectionCase).filter(InspectionCase.inspection_id == report.inspection_id).first()

        if not os.path.exists(report.file_reference):
            return {
                "report_id": report_id,
                "version": report.version,
                "exists": True,
                "integrity_status": "FILE_MISSING",
                "stored_hash": report.sha256,
                "computed_hash": None,
                "message": "Report record exists but PDF artifact is unavailable on server storage."
            }

        with open(report.file_reference, "rb") as f:
            pdf_bytes = f.read()
        computed_hash = hashlib.sha256(pdf_bytes).hexdigest()

        is_valid = (computed_hash == report.sha256)
        integrity_status = "VALID" if is_valid else "INTEGRITY_MISMATCH"

        msg = (
            "Integrity verification successful: the retrieved report bytes match the stored SHA-256 fingerprint."
            if is_valid else
            "Integrity mismatch detected: report bytes on storage do not match the registered cryptographic SHA-256 hash."
        )

        # Audit Event for Verification
        AuditService.record_event(
            db=db,
            inspection_id=report.inspection_id,
            actor_id=actor_id,
            action="REPORT_VERIFIED",
            entity_type="GeneratedReport",
            entity_id=report_id,
            metadata={
                "version": report.version,
                "is_valid": is_valid,
                "stored_hash": report.sha256,
                "computed_hash": computed_hash
            }
        )

        return {
            "report_id": report.report_id,
            "version": report.version,
            "exists": True,
            "integrity_status": integrity_status,
            "stored_hash": report.sha256,
            "computed_hash": computed_hash,
            "generated_at": report.generated_at,
            "finalized_at": case.finalized_at if case else None,
            "case_number": case.case_number if case else None,
            "overall_determination": case.overall_determination.value if case else None,
            "officer_id": case.officer_id if case else None,
            "message": msg
        }

    @classmethod
    def _build_pdf(
        cls,
        pdf_path: str,
        case: InspectionCase,
        report_id: str,
        version: int,
        evidence_items: List[EvidenceItem],
        extracted_fields: List[ExtractedField],
        findings: List[RuleFinding],
        measurements: List[VisualMeasurement],
        anomalies: List[VisualAnomaly],
        generated_at: datetime
    ):
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=44
        )

        # Pass case_number to NumberedCanvas for Page 2+ running header
        NumberedCanvas.case_number = case.case_number or ""

        # Locate NIRIKSHAN logo
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(backend_dir, "assets", "nirikshan-logo.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.abspath(os.path.join("frontend", "public", "assets", "branding", "nirikshan-logo.png"))

        styles = getSampleStyleSheet()

        # Typography & Styles
        sec_heading_style = ParagraphStyle(
            "GovSecHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#0f2942"),
            spaceBefore=7,
            spaceAfter=3
        )
        body_style = ParagraphStyle(
            "GovBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1e293b")
        )
        bold_style = ParagraphStyle(
            "GovBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#0f172a")
        )
        code_style = ParagraphStyle(
            "GovCode",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#0f172a")
        )

        elements = []

        # =========================================================================
        # 1. CLEAN HORIZONTAL BRAND HEADER (NIRIKSHAN)
        # =========================================================================
        brand_flowables = []
        if os.path.exists(logo_path):
            logo_img = RLImage(logo_path, width=130, height=31.3)
            brand_flowables.append(logo_img)
            brand_flowables.append(Spacer(1, 1.5 * mm))
        else:
            brand_flowables.append(Paragraph("<b><font size='13' color='#0f2942'>NIRIKSHAN</font></b>", ParagraphStyle("LogoAlt", fontName="Helvetica-Bold", fontSize=13, leading=15)))

        brand_flowables.append(Paragraph("<font color='#475569' size='7.5'>Legal Metrology Compliance &amp; Inspection System</font>", ParagraphStyle("BrandDesc", fontName="Helvetica", fontSize=7.5, leading=10)))
        brand_flowables.append(Paragraph("<font color='#64748b' size='6.5'>Statutory Framework: Legal Metrology (Packaged Commodities) Rules, 2011</font>", ParagraphStyle("BrandRule", fontName="Helvetica", fontSize=6.5, leading=8.5)))

        # QR Code Generation for Verification
        base_verify_url = getattr(settings, "REPORT_VERIFICATION_BASE_URL", "http://localhost:3000/verify").rstrip("/")
        verify_url = f"{base_verify_url}/{report_id}"
        qr_widget = qr.QrCodeWidget(verify_url)
        qr_bounds = qr_widget.getBounds()
        qr_w = qr_bounds[2] - qr_bounds[0]
        qr_h = qr_bounds[3] - qr_bounds[1]
        qr_size = 46
        qr_drawing = Drawing(qr_size, qr_size, transform=[qr_size / qr_w, 0, 0, qr_size / qr_h, 0, 0])
        qr_drawing.add(qr_widget)

        gen_short_date = generated_at.strftime("%d %b %Y, %H:%M UTC")
        meta_right = [
            Paragraph("<font color='#64748b' size='6'>DOCUMENT CLASSIFICATION</font><br/><b><font color='#0f2942' size='7.5'>INSPECTION REPORT</font></b>", ParagraphStyle("MetaDoc", fontName="Helvetica", fontSize=7, leading=9)),
            Spacer(1, 1 * mm),
            Paragraph(f"<font color='#64748b' size='6'>REPORT ID</font><br/><font color='#0f172a' size='6.5' face='Courier'><b>{report_id[:13]}...</b></font>", ParagraphStyle("MetaId", fontName="Helvetica", fontSize=6.5, leading=8)),
            Spacer(1, 1 * mm),
            Paragraph(f"<font color='#64748b' size='6'>DATE GENERATED</font><br/><font color='#0f172a' size='6.5'><b>{gen_short_date}</b></font>", ParagraphStyle("MetaDate", fontName="Helvetica", fontSize=6.5, leading=8)),
        ]

        meta_right_table = Table([[meta_right, qr_drawing]], colWidths=[130, 52])
        meta_right_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ]))

        top_header_table = Table([[brand_flowables, meta_right_table]], colWidths=[338, 185])
        top_header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(top_header_table)
        elements.append(Spacer(1, 2 * mm))

        # Brand Accent Rule (Saffron & Navy dual line)
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f2942"), spaceBefore=1, spaceAfter=1))
        elements.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor("#f59e0b"), spaceBefore=0, spaceAfter=5))

        # Document Title (Crisp, Premium, Uncongested)
        elements.append(Paragraph("INSPECTION &amp; EVIDENCE REPORT", ParagraphStyle(
            "DocTitle", fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=colors.HexColor("#0f2942")
        )))
        elements.append(Paragraph("Packaged Commodity Statutory Verification &amp; Compliance Record", ParagraphStyle(
            "DocSubTitle", fontName="Helvetica", fontSize=8, leading=10.5, textColor=colors.HexColor("#475569")
        )))
        elements.append(Spacer(1, 2.5 * mm))

        # =========================================================================
        # 2. CASE PROVENANCE & IDENTIFICATION CARD
        # =========================================================================
        final_date_str = case.finalized_at.strftime("%d %b %Y, %H:%M UTC") if case.finalized_at else "IN PROGRESS"

        ident_data = [
            [
                Paragraph("<b>Case Number:</b>", body_style), Paragraph(case.case_number, bold_style),
                Paragraph("<b>Inspection ID:</b>", body_style), Paragraph(case.inspection_id, code_style)
            ],
            [
                Paragraph("<b>Inspecting Officer:</b>", body_style), Paragraph(case.officer_id, body_style),
                Paragraph("<b>Report Version:</b>", body_style), Paragraph(f"v{version} (Final)" if case.status == CaseStatus.FINALISED else f"v{version} (Draft)", bold_style)
            ],
            [
                Paragraph("<b>Case Status:</b>", body_style), Paragraph(f"<b>{case.status.value}</b>", bold_style),
                Paragraph("<b>Finalised At:</b>", body_style), Paragraph(final_date_str, body_style)
            ],
            [
                Paragraph("<b>Commodity Sample:</b>", body_style), Paragraph(case.notes or "Packaged Commodity Sample", body_style),
                Paragraph("<b>Rule Pack:</b>", body_style), Paragraph(case.rule_pack_version, code_style)
            ]
        ]
        ident_table = Table(ident_data, colWidths=[85, 175, 85, 178])
        ident_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0"))
        ]))
        elements.append(ident_table)
        elements.append(Spacer(1, 3.5 * mm))

        # =========================================================================
        # 3. SECTION 1: STATUTORY DETERMINATION & ENFORCEMENT SUMMARY
        # =========================================================================
        elements.append(Paragraph("1. STATUTORY DETERMINATION &amp; OFFICER DECISION", sec_heading_style))
        det_val = case.overall_determination.value
        det_color = colors.HexColor("#15803d") if det_val == "COMPLIANT" else (colors.HexColor("#b91c1c") if det_val == "NON_COMPLIANT" else colors.HexColor("#b45309"))
        det_bg = colors.HexColor("#f0fdf4") if det_val == "COMPLIANT" else (colors.HexColor("#fef2f2") if det_val == "NON_COMPLIANT" else colors.HexColor("#fffbeb"))

        decision_data = [
            [
                Paragraph("<b>Overall Finding:</b>", body_style),
                Paragraph(f"<font color='{det_color.hexval()}'><b>[ {det_val} ]</b></font>", bold_style),
                Paragraph("<b>Officer Decision:</b>", body_style),
                Paragraph(case.officer_decision or det_val, bold_style)
            ],
            [
                Paragraph("<b>Officer Remarks:</b>", body_style),
                Paragraph(case.officer_remarks or "No additional remarks recorded.", body_style),
                Paragraph("<b>Rule Pack:</b>", body_style),
                Paragraph(case.rule_pack_version, code_style)
            ]
        ]
        decision_table = Table(decision_data, colWidths=[90, 160, 90, 183])
        decision_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), det_bg),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(decision_table)
        elements.append(Spacer(1, 3 * mm))

        # =========================================================================
        # 4. SECTION 2: STRUCTURED DECLARATIONS & PROVENANCE
        # =========================================================================
        elements.append(Paragraph("2. EXTRACTED PACKAGED COMMODITY DECLARATIONS", sec_heading_style))
        field_rows = [
            [
                Paragraph("<b>Mandatory Field</b>", bold_style),
                Paragraph("<b>Declared / Extracted Value</b>", bold_style),
                Paragraph("<b>Status</b>", bold_style),
                Paragraph("<b>Origin</b>", bold_style),
                Paragraph("<b>Confidence</b>", bold_style)
            ]
        ]
        for f in extracted_fields:
            conf_str = f"{int((f.confidence or 0.90) * 100)}%"
            val_str = f.normalized_value or f.raw_value or "—"
            if f.unit:
                val_str += f" {f.unit}"
            field_rows.append([
                Paragraph(f.field_name.replace("_", " ").title(), body_style),
                Paragraph(val_str, bold_style),
                Paragraph(f.field_status.value if hasattr(f.field_status, "value") else str(f.field_status), body_style),
                Paragraph(f.origin.value if hasattr(f.origin, "value") else str(f.origin), body_style),
                Paragraph(conf_str, body_style)
            ])

        if len(field_rows) == 1:
            field_rows.append([Paragraph("No declarations extracted.", body_style), Paragraph("—", body_style), Paragraph("—", body_style), Paragraph("—", body_style), Paragraph("—", body_style)])

        fields_table = Table(field_rows, colWidths=[120, 183, 80, 80, 60])
        fields_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2942")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")])
        ]))
        elements.append(fields_table)
        elements.append(Spacer(1, 3 * mm))

        # =========================================================================
        # 5. SECTION 3: STATUTORY RULE COMPLIANCE FINDINGS
        # =========================================================================
        elements.append(Paragraph("3. STATUTORY RULE COMPLIANCE FINDINGS", sec_heading_style))
        finding_rows = [
            [
                Paragraph("<b>Rule ID / Citation</b>", bold_style),
                Paragraph("<b>Rule Title</b>", bold_style),
                Paragraph("<b>Verdict</b>", bold_style),
                Paragraph("<b>Observed Finding &amp; Evaluation Detail</b>", bold_style)
            ]
        ]
        for r in findings:
            st = r.status.value if hasattr(r.status, "value") else str(r.status)
            st_color = "#15803d" if st == "PASS" else ("#b91c1c" if st == "FAIL" else "#b45309")
            finding_rows.append([
                Paragraph(f"<b>{r.rule_id}</b><br/>{r.legal_citation}", body_style),
                Paragraph(r.title, body_style),
                Paragraph(f"<font color='{st_color}'><b>{st}</b></font>", bold_style),
                Paragraph(r.message, body_style)
            ])

        if len(finding_rows) == 1:
            finding_rows.append([Paragraph("No rule findings evaluated.", body_style), Paragraph("—", body_style), Paragraph("—", body_style), Paragraph("—", body_style)])

        findings_table = Table(finding_rows, colWidths=[130, 110, 60, 223])
        findings_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2942")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")])
        ]))
        elements.append(findings_table)
        elements.append(Spacer(1, 3 * mm))

        # =========================================================================
        # 6. SECTION 4: EVIDENCE INTEGRITY & SHA-256 HASH REGISTER
        # =========================================================================
        elements.append(Paragraph("4. EVIDENCE INGESTION &amp; SHA-256 INTEGRITY REGISTER", sec_heading_style))
        ev_rows = [
            [
                Paragraph("<b>Evidence ID</b>", bold_style),
                Paragraph("<b>View</b>", bold_style),
                Paragraph("<b>Original Filename</b>", bold_style),
                Paragraph("<b>Quality</b>", bold_style),
                Paragraph("<b>Cryptographic SHA-256 Hash</b>", bold_style)
            ]
        ]
        for ev in evidence_items:
            ev_rows.append([
                Paragraph(ev.evidence_id[:8] + "...", code_style),
                Paragraph(ev.view_type.value if hasattr(ev.view_type, "value") else str(ev.view_type), body_style),
                Paragraph(ev.original_filename, body_style),
                Paragraph(ev.quality_verdict.value if hasattr(ev.quality_verdict, "value") else str(ev.quality_verdict), body_style),
                Paragraph(ev.sha256, code_style)
            ])

        if len(ev_rows) == 1:
            ev_rows.append([Paragraph("No evidence files registered.", body_style), Paragraph("—", body_style), Paragraph("—", body_style), Paragraph("—", body_style), Paragraph("—", body_style)])

        ev_table = Table(ev_rows, colWidths=[65, 55, 110, 60, 233])
        ev_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2942")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")])
        ]))
        elements.append(ev_table)
        elements.append(Spacer(1, 4 * mm))

        # =========================================================================
        # 7. SECTION 5: STATUTORY DISCLAIMER & TRUST BOUNDARY
        # =========================================================================
        elements.append(Paragraph("5. STATUTORY DISCLAIMER &amp; TRUST BOUNDARY", sec_heading_style))
        disclaimer_text = (
            "<b>STATUTORY DISCLAIMER &amp; REGULATORY NOTICE:</b> "
            "This document is generated by NIRIKSHAN (Legal Metrology Compliance &amp; Inspection System) as an evidentiary "
            "and statutory decision-support record for authorised Legal Metrology inspection officers. Automated perception, OCR, "
            "and visual measurements provide objective preliminary data under the Legal Metrology (Packaged Commodities) Rules, 2011. "
            "The authorised inspecting officer retains sole statutory authority for final enforcement determinations and orders."
        )
        elements.append(Paragraph(disclaimer_text, ParagraphStyle(
            "GovDisc", parent=styles["Normal"], fontSize=7, leading=9, textColor=colors.HexColor("#64748b")
        )))

        # Build document with NumberedCanvas
        doc.build(elements, canvasmaker=NumberedCanvas)
