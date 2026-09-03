import os
import cv2
import numpy as np
from typing import Dict, Any

class ImagePreprocessingService:
    """
    OpenCV image preprocessing pipeline for legal metrology package images.
    Creates normalized and enhanced derived variants without modifying the original immutable evidence.
    """

    @staticmethod
    def generate_variants(
        original_image_path: str,
        output_dir: str
    ) -> Dict[str, str]:
        """
        Generate multiple image variants optimized for OCR perception:
        1. grayscale
        2. contrast_enhanced (CLAHE)
        3. denoised (Bilateral filter)
        4. adaptive_threshold (Otsu thresholding)

        Returns dictionary mapping variant name to relative file path.
        """
        os.makedirs(output_dir, exist_ok=True)
        img = cv2.imread(original_image_path)
        if img is None:
            raise ValueError(f"Unable to read image at '{original_image_path}'.")

        variants_map: Dict[str, str] = {}

        # 1. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_path = os.path.join(output_dir, "grayscale.jpg")
        cv2.imwrite(gray_path, gray)
        variants_map["grayscale"] = gray_path

        # 2. Contrast Enhanced (CLAHE - Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(gray)
        contrast_path = os.path.join(output_dir, "contrast_enhanced.jpg")
        cv2.imwrite(contrast_path, contrast_enhanced)
        variants_map["contrast_enhanced"] = contrast_path

        # 3. Denoised (Bilateral Filter preserves edges while smoothing background noise)
        denoised = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
        denoised_path = os.path.join(output_dir, "denoised.jpg")
        cv2.imwrite(denoised_path, denoised)
        variants_map["denoised"] = denoised_path

        # 4. Adaptive / Otsu Thresholding
        _, thresh = cv2.threshold(contrast_enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        thresh_path = os.path.join(output_dir, "adaptive_threshold.jpg")
        cv2.imwrite(thresh_path, thresh)
        variants_map["adaptive_threshold"] = thresh_path

        return variants_map
