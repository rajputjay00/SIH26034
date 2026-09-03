import cv2
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, List
from app.models.domain import QualityVerdict
from app.schemas.pydantic_models import QualityReport

class QualityAssessmentService:
    """
    OpenCV-based image quality gate for inspecting packaged commodity evidence images.
    Evaluates blur, brightness, contrast, and resolution prior to OCR.
    All diagnostic feedback uses strictly technical engineering terminology (no legal claims).
    """

    BLUR_THRESHOLD_FAIL = 50.0
    BLUR_THRESHOLD_WARN = 100.0

    BRIGHTNESS_MIN_FAIL = 30.0
    BRIGHTNESS_MIN_WARN = 50.0
    BRIGHTNESS_MAX_WARN = 215.0
    BRIGHTNESS_MAX_FAIL = 235.0

    CONTRAST_MIN_FAIL = 15.0
    CONTRAST_MIN_WARN = 28.0

    MIN_RESOLUTION_WIDTH = 400
    MIN_RESOLUTION_HEIGHT = 400

    @classmethod
    def evaluate_image(cls, image_bytes: bytes) -> QualityReport:
        """
        Decode raw image bytes and execute image quality analysis.
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return QualityReport(
                verdict=QualityVerdict.FAIL,
                blur_score=0.0,
                brightness_score=0.0,
                contrast_score=0.0,
                is_readable=False,
                diagnostics=["Image decoding failed: file data corrupted or format unsupported."],
                evaluated_at=datetime.now(timezone.utc)
            )

        height, width = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 1. Blur evaluation via Laplacian variance
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        # 2. Brightness evaluation (mean pixel intensity)
        brightness = float(np.mean(gray))

        # 3. Contrast evaluation (standard deviation of pixel intensity)
        contrast = float(np.std(gray))

        diagnostics: List[str] = []
        is_fail = False
        is_warn = False

        # Resolution checks
        if width < cls.MIN_RESOLUTION_WIDTH or height < cls.MIN_RESOLUTION_HEIGHT:
            is_warn = True
            diagnostics.append(f"Low resolution: {width}x{height}px (Recommended min: {cls.MIN_RESOLUTION_WIDTH}x{cls.MIN_RESOLUTION_HEIGHT}px).")

        # Blur checks
        if laplacian_var < cls.BLUR_THRESHOLD_FAIL:
            is_fail = True
            diagnostics.append(f"Image appears excessively blurry for reliable OCR (Laplacian score: {laplacian_var:.1f}).")
        elif laplacian_var < cls.BLUR_THRESHOLD_WARN:
            is_warn = True
            diagnostics.append(f"Moderate motion or focus blur detected (Laplacian score: {laplacian_var:.1f}).")

        # Brightness / Exposure checks
        if brightness < cls.BRIGHTNESS_MIN_FAIL:
            is_fail = True
            diagnostics.append(f"Severe underexposure / darkness detected (Brightness: {brightness:.1f}/255).")
        elif brightness < cls.BRIGHTNESS_MIN_WARN:
            is_warn = True
            diagnostics.append(f"Low ambient lighting detected (Brightness: {brightness:.1f}/255).")
        elif brightness > cls.BRIGHTNESS_MAX_FAIL:
            is_fail = True
            diagnostics.append(f"Severe overexposure / glare clipping detected (Brightness: {brightness:.1f}/255).")
        elif brightness > cls.BRIGHTNESS_MAX_WARN:
            is_warn = True
            diagnostics.append(f"High glare or overexposure detected (Brightness: {brightness:.1f}/255).")

        # Contrast checks
        if contrast < cls.CONTRAST_MIN_FAIL:
            is_fail = True
            diagnostics.append(f"Extremely low image contrast (Contrast score: {contrast:.1f}).")
        elif contrast < cls.CONTRAST_MIN_WARN:
            is_warn = True
            diagnostics.append(f"Low dynamic contrast between text and background (Contrast score: {contrast:.1f}).")

        # Determine final engineering verdict
        if is_fail:
            verdict = QualityVerdict.FAIL
            is_readable = False
        elif is_warn:
            verdict = QualityVerdict.WARN
            is_readable = True
        else:
            verdict = QualityVerdict.PASS
            is_readable = True
            diagnostics.append("Image resolution, sharpness, brightness, and contrast within acceptable parameters.")

        return QualityReport(
            verdict=verdict,
            blur_score=round(laplacian_var, 2),
            brightness_score=round(brightness, 2),
            contrast_score=round(contrast, 2),
            is_readable=is_readable,
            diagnostics=diagnostics,
            evaluated_at=datetime.now(timezone.utc)
        )
