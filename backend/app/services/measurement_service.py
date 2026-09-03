import os
import cv2
import numpy as np
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.domain import (
    VisualMeasurement,
    CalibrationData,
    CalibrationStatus,
    OCRResult,
    EvidenceItem
)
from app.services.audit_service import AuditService
from app.utils.errors import ResourceNotFoundError

class VisualMeasurementService:
    """
    Measures physical font and character heights by combining OCR bounding geometry with calibrated mm-per-pixel ratios.
    Preserves original evidence immutability and generates derived visual overlays.
    """

    @classmethod
    def measure_evidence_fonts(
        cls,
        db: Session,
        inspection_id: str,
        evidence_id: str,
        officer_id: str = "OFFICER-SYS"
    ) -> List[VisualMeasurement]:
        """
        Calculates physical character heights in millimeters for all OCR detected text regions in an evidence view.
        """
        evidence = db.query(EvidenceItem).filter(
            EvidenceItem.evidence_id == evidence_id,
            EvidenceItem.inspection_id == inspection_id
        ).first()

        if not evidence:
            raise ResourceNotFoundError("EvidenceItem", evidence_id)

        # Retrieve active calibration for this evidence image
        calib = db.query(CalibrationData).filter(
            CalibrationData.evidence_id == evidence_id,
            CalibrationData.inspection_id == inspection_id
        ).order_by(CalibrationData.created_at.desc()).first()

        # Retrieve OCR Results
        ocr = db.query(OCRResult).filter(
            OCRResult.evidence_id == evidence_id,
            OCRResult.inspection_id == inspection_id
        ).first()

        if not ocr or not ocr.boxes_json:
            return []

        # Clear existing measurements for this evidence view
        db.query(VisualMeasurement).filter(
            VisualMeasurement.evidence_id == evidence_id,
            VisualMeasurement.inspection_id == inspection_id
        ).delete()

        is_calibrated = (
            calib is not None
            and calib.status == CalibrationStatus.CALIBRATED
            and calib.mm_per_pixel is not None
            and calib.mm_per_pixel > 0
        )
        scale = calib.mm_per_pixel if is_calibrated else None

        measurements: List[VisualMeasurement] = []

        # Read original image for overlay generation
        img = None
        if os.path.exists(evidence.file_reference):
            img = cv2.imread(evidence.file_reference)

        for box_item in ocr.boxes_json:
            bbox = box_item.get("bbox", [])
            text = box_item.get("text", "")
            conf = box_item.get("confidence", 0.90)

            pixel_height = 0.0
            if len(bbox) >= 4:
                # Bounding box polygon [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                y_coords = [p[1] for p in bbox]
                pixel_height = float(max(y_coords) - min(y_coords))
            else:
                pixel_height = float(box_item.get("char_height_px", 20.0))

            if pixel_height <= 0:
                continue

            physical_height_mm = None
            meas_status = "CALIBRATION_REQUIRED"

            if is_calibrated and scale:
                physical_height_mm = round(pixel_height * scale, 2)
                meas_status = "MEASURED"

            # Determine character type conservatively
            clean_text = "".join(ch for ch in text if ch.isalnum())
            if clean_text.isdigit():
                char_type = "NUMERAL"
            elif clean_text.isalpha():
                char_type = "LETTER"
            else:
                char_type = "UNKNOWN"

            m = VisualMeasurement(
                measurement_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                evidence_id=evidence_id,
                calibration_id=calib.calibration_id if calib else None,
                measurement_type="FONT_HEIGHT",
                target_text=text[:250],
                character_type=char_type,
                pdp_area_cm2=None, # PDP area requires dedicated surface measurement; never guessed
                declaration_method="NORMAL_PRINT",
                source_bbox_json=bbox,
                pixel_value=round(pixel_height, 2),
                physical_value=physical_height_mm,
                unit="mm",
                confidence=round(conf * (0.95 if is_calibrated else 0.70), 2),
                status=meas_status,
                method_version="v1.0.0",
                created_at=datetime.now(timezone.utc)
            )
            db.add(m)
            measurements.append(m)


        db.commit()

        # Generate derived measurement overlay
        if img is not None:
            derived_dir = os.path.join("storage", "derived", inspection_id, evidence_id)
            os.makedirs(derived_dir, exist_ok=True)
            overlay_path = os.path.join(derived_dir, "measurement_overlay.jpg")
            cls._create_measurement_overlay(img, measurements, is_calibrated, overlay_path)

        # Audit Event
        AuditService.record_event(
            db=db,
            inspection_id=inspection_id,
            actor_id=officer_id,
            action="VISUAL_FONT_MEASUREMENT",
            entity_type="VisualMeasurement",
            entity_id=evidence_id,
            metadata={
                "measurements_count": len(measurements),
                "is_calibrated": is_calibrated,
                "scale_mm_per_px": scale
            }
        )

        return measurements

    @classmethod
    def _create_measurement_overlay(
        cls,
        img: np.ndarray,
        measurements: List[VisualMeasurement],
        is_calibrated: bool,
        output_path: str
    ):
        """Generates derived visualization overlay with bounding boxes and font height annotations."""
        overlay = img.copy()
        for m in measurements:
            bbox = m.source_bbox_json
            if bbox and len(bbox) >= 4:
                pts = np.array(bbox, np.int32).reshape((-1, 1, 2))
                color = (0, 200, 0) if is_calibrated else (200, 150, 0)
                cv2.polylines(overlay, [pts], isClosed=True, color=color, thickness=2)

                x1, y1 = int(bbox[0][0]), int(bbox[0][1])
                label = f"{m.physical_value}mm ({int(m.pixel_value)}px)" if is_calibrated else f"{int(m.pixel_value)}px"
                cv2.putText(overlay, label, (x1, max(12, y1 - 4)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(overlay, label, (x1, max(12, y1 - 4)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)

        cv2.imwrite(output_path, overlay)
