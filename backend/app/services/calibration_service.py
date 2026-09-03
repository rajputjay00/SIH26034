import os
import cv2
import numpy as np
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session

from app.models.domain import CalibrationData, CalibrationStatus, EvidenceItem
from app.services.audit_service import AuditService
from app.utils.errors import ResourceNotFoundError

# Official standard diameter of Indian ₹5 coin (Nickel-Brass / Stainless Steel series)
INDIAN_5_RUPEE_COIN_DIAMETER_MM = 23.00

class CalibrationService:
    """
    OpenCV-based physical reference calibration service.
    Detects standard Indian ₹5 coin reference target and calculates mm-per-pixel ratio.
    Original uploaded evidence images remain strictly immutable.
    """

    @classmethod
    def calibrate_evidence_image(
        cls,
        db: Session,
        inspection_id: str,
        evidence_id: str,
        officer_id: str = "OFFICER-SYS"
    ) -> CalibrationData:
        """
        Execute computer vision coin detection and establish physical calibration ratio for an evidence image.
        """
        evidence = db.query(EvidenceItem).filter(
            EvidenceItem.evidence_id == evidence_id,
            EvidenceItem.inspection_id == inspection_id
        ).first()

        if not evidence:
            raise ResourceNotFoundError("EvidenceItem", evidence_id)

        file_path = evidence.file_reference
        if not os.path.exists(file_path):
            raise ResourceNotFoundError("EvidenceFile", file_path)

        # Read original image in read-only mode via OpenCV
        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"Failed to decode evidence image at {file_path}")

        height, width = img.shape[:2]

        # Computer vision circle detection pipeline
        detection_result = cls._detect_coin_reference(img)

        # Remove previous calibration records for this specific evidence item
        db.query(CalibrationData).filter(
            CalibrationData.evidence_id == evidence_id,
            CalibrationData.inspection_id == inspection_id
        ).delete()

        # Generate derived visualization overlay
        derived_dir = os.path.join("storage", "derived", inspection_id, evidence_id)
        os.makedirs(derived_dir, exist_ok=True)
        overlay_path = os.path.join(derived_dir, "calibration_overlay.jpg")
        cls._create_calibration_overlay(img, detection_result, overlay_path)

        # Create persistent CalibrationData entity
        calib = CalibrationData(
            calibration_id=str(uuid.uuid4()),
            inspection_id=inspection_id,
            evidence_id=evidence_id,
            calibration_method="PHYSICAL_REFERENCE",
            reference_object="INDIAN_5_RUPEE_COIN",
            reference_measurement_mm=INDIAN_5_RUPEE_COIN_DIAMETER_MM,
            detected_pixel_measurement=detection_result.get("pixel_diameter"),
            mm_per_pixel=detection_result.get("mm_per_pixel"),
            confidence=detection_result.get("confidence", 0.0),
            bounding_geometry_json=detection_result.get("geometry"),
            status=detection_result.get("status", CalibrationStatus.CALIBRATION_UNAVAILABLE),
            created_at=datetime.now(timezone.utc)
        )

        db.add(calib)
        db.commit()
        db.refresh(calib)

        # Audit Event
        AuditService.record_event(
            db=db,
            inspection_id=inspection_id,
            actor_id=officer_id,
            action="PHYSICAL_REFERENCE_CALIBRATION",
            entity_type="CalibrationData",
            entity_id=calib.calibration_id,
            metadata={
                "evidence_id": evidence_id,
                "status": calib.status.value,
                "mm_per_pixel": calib.mm_per_pixel,
                "confidence": calib.confidence,
                "overlay_reference": overlay_path
            }
        )

        return calib

    @classmethod
    def _detect_coin_reference(cls, img: np.ndarray) -> Dict[str, Any]:
        """
        Locates circular ₹5 coin reference target using OpenCV contour circularity & Hough Circle analysis.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        min_dim = min(h, w)

        min_radius = max(28, int(min_dim * 0.04))
        max_radius = int(min_dim * 0.30)
        min_area = np.pi * (min_radius ** 2) * 0.70
        max_area = np.pi * (max_radius ** 2) * 1.30

        candidates: List[Dict[str, Any]] = []

        # 1. Primary Detector: Edge-based closed contour circularity
        blurred = cv2.GaussianBlur(gray, (5, 5), 1.2)
        edges = cv2.Canny(blurred, 40, 120)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area <= area <= max_area:
                perimeter = cv2.arcLength(cnt, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * (area / (perimeter * perimeter))
                    (cx, cy), radius = cv2.minEnclosingCircle(cnt)
                    r = int(radius)

                    x, y, bw, bh = cv2.boundingRect(cnt)
                    aspect = float(bw) / bh if bh > 0 else 0

                    # Standard ₹5 coin has aspect ratio ~1.0 and circularity >= 0.75
                    if circularity >= 0.75 and 0.82 <= aspect <= 1.22 and min_radius <= r <= max_radius:
                        diam_px = float(2 * r)
                        mm_per_px = round(INDIAN_5_RUPEE_COIN_DIAMETER_MM / diam_px, 6)
                        candidates.append({
                            "center": [int(cx), int(cy)],
                            "radius": r,
                            "pixel_diameter": diam_px,
                            "mm_per_pixel": mm_per_px,
                            "confidence": round(min(0.96, float(circularity * 0.95)), 2),
                            "geometry": {"center_x": int(cx), "center_y": int(cy), "radius_px": r}
                        })

        # Deduplicate candidates within 30px
        unique_candidates: List[Dict[str, Any]] = []

        for c in candidates:
            is_dup = False
            for u in unique_candidates:
                dist = np.hypot(c["center"][0] - u["center"][0], c["center"][1] - u["center"][1])
                if dist < 30:
                    is_dup = True
                    break
            if not is_dup:
                unique_candidates.append(c)

        if not unique_candidates:
            return {
                "status": CalibrationStatus.CALIBRATION_UNAVAILABLE,
                "pixel_diameter": None,
                "mm_per_pixel": None,
                "confidence": 0.0,
                "geometry": None
            }

        if len(unique_candidates) > 2:
            return {
                "status": CalibrationStatus.AMBIGUOUS_CALIBRATION,
                "pixel_diameter": unique_candidates[0]["pixel_diameter"],
                "mm_per_pixel": unique_candidates[0]["mm_per_pixel"],
                "confidence": 0.40,
                "geometry": unique_candidates[0]["geometry"],
                "candidate_count": len(unique_candidates)
            }

        best = max(unique_candidates, key=lambda c: c["confidence"])
        return {
            "status": CalibrationStatus.CALIBRATED,
            "pixel_diameter": best["pixel_diameter"],
            "mm_per_pixel": best["mm_per_pixel"],
            "confidence": best["confidence"],
            "geometry": best["geometry"]
        }






    @classmethod
    def _create_calibration_overlay(cls, img: np.ndarray, detection: Dict[str, Any], output_path: str):
        """Generates derived visualization overlay with circle annotations."""
        overlay = img.copy()
        geom = detection.get("geometry")
        if geom:
            cx = geom.get("center_x", 0)
            cy = geom.get("center_y", 0)
            r = geom.get("radius_px", 0)

            # Draw outer reference circle (Blue / Green)
            color = (37, 99, 235) if detection.get("status") == CalibrationStatus.CALIBRATED else (0, 165, 255)
            cv2.circle(overlay, (cx, cy), r, color, 3)
            cv2.circle(overlay, (cx, cy), 3, (0, 0, 255), -1)

            # Annotation text
            label = f"Ref: Rs 5 Coin (23.00mm) | scale: {detection.get('mm_per_pixel', 0):.4f} mm/px"
            cv2.putText(overlay, label, (max(10, cx - r), max(20, cy - r - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 3, cv2.LINE_AA)
            cv2.putText(overlay, label, (max(10, cx - r), max(20, cy - r - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

        cv2.imwrite(output_path, overlay)
