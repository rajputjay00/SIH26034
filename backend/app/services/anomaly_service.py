import os
import cv2
import numpy as np
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.domain import VisualAnomaly, EvidenceItem, OCRResult
from app.services.audit_service import AuditService
from app.utils.errors import ResourceNotFoundError

class VisualAnomalyService:
    """
    OpenCV visual forensic anomaly analyzer for detecting suspected price overwrite stickers,
    local texture discontinuities, and rectangular overlay patches.
    Under NO circumstances does a visual suspicion signal independently establish a legal violation.
    """

    @classmethod
    def detect_visual_anomalies(
        cls,
        db: Session,
        inspection_id: str,
        evidence_id: str,
        officer_id: str = "OFFICER-SYS"
    ) -> List[VisualAnomaly]:
        """
        Executes edge discontinuity and local patch gradient analysis on an evidence view.
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

        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"Failed to decode evidence image at {file_path}")

        # Clear existing anomalies for this evidence item
        db.query(VisualAnomaly).filter(
            VisualAnomaly.evidence_id == evidence_id,
            VisualAnomaly.inspection_id == inspection_id
        ).delete()

        # Run OpenCV anomaly detection
        detected_anomalies_data = cls._analyze_image_for_overlays(img)

        persisted_anomalies: List[VisualAnomaly] = []
        for item in detected_anomalies_data:
            anomaly = VisualAnomaly(
                anomaly_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                evidence_id=evidence_id,
                anomaly_type=item.get("anomaly_type", "SUSPECTED_OVERLAY"),
                bounding_box_json=item.get("bounding_box"),
                confidence=item.get("confidence", 0.70),
                metrics_json=item.get("metrics"),
                status="DETECTED",
                officer_review_required="YES",
                created_at=datetime.now(timezone.utc)
            )
            db.add(anomaly)
            persisted_anomalies.append(anomaly)

        db.commit()

        # Generate derived overlay image
        derived_dir = os.path.join("storage", "derived", inspection_id, evidence_id)
        os.makedirs(derived_dir, exist_ok=True)
        overlay_path = os.path.join(derived_dir, "anomaly_overlay.jpg")
        cls._create_anomaly_overlay(img, persisted_anomalies, overlay_path)

        # Audit Event
        AuditService.record_event(
            db=db,
            inspection_id=inspection_id,
            actor_id=officer_id,
            action="VISUAL_ANOMALY_DETECTION",
            entity_type="VisualAnomaly",
            entity_id=evidence_id,
            metadata={
                "anomalies_found": len(persisted_anomalies),
                "overlay_path": overlay_path
            }
        )

        return persisted_anomalies

    @classmethod
    def _analyze_image_for_overlays(cls, img: np.ndarray) -> List[Dict[str, Any]]:
        """
        Analyzes edge steps, rectangular adhesive boundaries, and localized contrast differentials.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        img_area = h * w

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 30, 100)

        # Dilate slightly to connect broken sticker borders
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates: List[Dict[str, Any]] = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Plausible sticker patch dimensions (0.5% to 25% of image area)
            if area > (img_area * 0.005) and area < (img_area * 0.25):
                perimeter = cv2.arcLength(cnt, True)
                if perimeter > 0:
                    approx = cv2.approxPolyDP(cnt, 0.03 * perimeter, True)
                    # Rectangular or quadrilateral shape
                    if len(approx) == 4 or (len(approx) <= 8 and cv2.isContourConvex(approx)):
                        x, y, bw, bh = cv2.boundingRect(approx)
                        aspect_ratio = float(bw) / bh if bh > 0 else 0

                        if 0.4 <= aspect_ratio <= 6.0:
                            roi = gray[y: y + bh, x: x + bw]
                            if roi.size > 0:
                                roi_std = float(np.std(roi))
                                bbox_poly = [[x, y], [x + bw, y], [x + bw, y + bh], [x, y + bh]]
                                candidates.append({
                                    "anomaly_type": "SUSPECTED_OVERLAY",
                                    "bounding_box": bbox_poly,
                                    "confidence": round(min(0.88, max(0.68, 0.6 + (area / img_area) * 2)), 2),
                                    "metrics": {
                                        "patch_area_px": int(area),
                                        "aspect_ratio": round(aspect_ratio, 2),
                                        "local_contrast_std": round(roi_std, 2),
                                        "reason": "Rectangular edge discontinuity detected matching adhesive label geometry"
                                    }
                                })

        return candidates[:3] # Cap at top 3 suspicious candidates


    @classmethod
    def _create_anomaly_overlay(
        cls,
        img: np.ndarray,
        anomalies: List[VisualAnomaly],
        output_path: str
    ):
        """Generates derived visualization overlay with anomaly bounding boxes."""
        overlay = img.copy()
        for a in anomalies:
            bbox = a.bounding_box_json
            if bbox and len(bbox) >= 4:
                pts = np.array(bbox, np.int32).reshape((-1, 1, 2))
                cv2.polylines(overlay, [pts], isClosed=True, color=(0, 0, 230), thickness=2)

                x1, y1 = int(bbox[0][0]), int(bbox[0][1])
                label = f"SUSPECTED OVERLAY ({int(a.confidence * 100)}%)"
                cv2.putText(overlay, label, (x1, max(12, y1 - 4)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 3, cv2.LINE_AA)
                cv2.putText(overlay, label, (x1, max(12, y1 - 4)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 230), 1, cv2.LINE_AA)

        cv2.imwrite(output_path, overlay)
