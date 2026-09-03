# LegalMetriX — Evidence Intake, Image Quality & OCR Pipeline

## 1. Pipeline Overview
The Phase 2 pipeline orchestrates the ingestion of multi-angle physical package evidence, calculates cryptographic SHA-256 provenance hashes immediately on arrival, performs automated OpenCV image quality assessment, executes image normalization/preprocessing variants, runs PaddleOCR text and polygon bounding box extraction, and persists structured machine perception records.

```
+----------------------------------------------------------------------------------------------------+
|                                    EVIDENCE & OCR PROCESSING PIPELINE                              |
+----------------------------------------------------------------------------------------------------+

   +----------------------------------------------------------------------------------------------+
   | 1. EVIDENCE INGESTION & SECURE VALIDATION                                                    |
   | • Validate file extension (.jpg, .jpeg, .png, .webp, .bmp)                                   |
   | • Enforce maximum file size (25 MB) & decodeability via OpenCV                               |
   | • Extract dimensional metadata (Width x Height, MIME format)                                 |
   | • Compute original evidence SHA-256 hash immediately upon server arrival                    |
   | • Store immutable original in storage/evidence/{inspection_id}/{evidence_id}_{filename}      |
   +----------------------------------------------+-----------------------------------------------+
                                                  |
                                                  v
   +----------------------------------------------------------------------------------------------+
   | 2. OPENCV IMAGE QUALITY GATE                                                                 |
   | • Blur detection via Laplacian Variance (Var(∇²I))                                           |
   | • Brightness evaluation via mean grayscale pixel intensity (0 - 255)                         |
   | • Dynamic contrast evaluation via RMS intensity standard deviation                           |
   | • Resolution adequacy check (Min 400x400px recommended)                                      |
   | • Quality Verdict: PASS / WARN / FAIL / MANUAL_REVIEW                                        |
   | * Note: All quality diagnostics are strictly engineering metrics (NO legal conclusions)      |
   +----------------------------------------------+-----------------------------------------------+
                                                  |
                                                  v
   +----------------------------------------------------------------------------------------------+
   | 3. OPENCV IMAGE PREPROCESSING & NORMALIZATION                                                |
   | • Derived copies generated in storage/derived/{inspection_id}/{evidence_id}/                 |
   |   1. grayscale.jpg                                                                           |
   |   2. contrast_enhanced.jpg (CLAHE: clipLimit=2.5, tileGridSize=8x8)                          |
   |   3. denoised.jpg (Bilateral Filter: d=9, sigmaColor=75, sigmaSpace=75)                      |
   |   4. adaptive_threshold.jpg (Otsu binarization)                                              |
   | * Original evidence remains strictly unaltered and immutable                                 |
   +----------------------------------------------+-----------------------------------------------+
                                                  |
                                                  v
   +----------------------------------------------------------------------------------------------+
   | 4. PADDLEOCR TEXT & BOUNDING BOX EXTRACTION                                                  |
   | • Multi-line detection using PaddleOCR-v4 (with OpenCV contour fallback)                     |
   | • Structured bounding box coordinates: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]                 |
   | • Word and line level confidence scores (0.0000 - 1.0000)                                    |
   | • Approximate character pixel height estimation (char_height_px)                             |
   | • Provenance preservation: source evidence_id, engine version, processing time ms            |
   +----------------------------------------------+-----------------------------------------------+
                                                  |
                                                  v
   +----------------------------------------------------------------------------------------------+
   | 5. PERSISTENCE & AUDIT TRAIL                                                                 |
   | • Record stored in ocr_results table with relationship to EvidenceItem and InspectionCase    |
   | • Append-only SHA-256 audit entry generated via AuditService.record_event                    |
   | • UI Bounding Box visualization overlay enabled                                              |
   +----------------------------------------------------------------------------------------------+
```

---

## 2. Supported Evidence Views
Multi-image evidence is associated with a single `InspectionCase`:
* **`FRONT`:** Mandatory principal display panel view.
* **`BACK`:** Mandatory consumer information and declarations panel view.
* **`SIDE`:** Optional supplementary side panel view.
* **`BASE`:** Optional bottom / batch marking view.
* **`OTHER`:** Supplementary inspection angle.

---

## 3. Image Quality Thresholds (Engineering Heuristics)

| Metric | Fail Threshold | Warn Threshold | Pass Condition |
| :--- | :--- | :--- | :--- |
| **Blur ($\sigma^2$)** | $< 50.0$ | $50.0 \le \sigma^2 < 100.0$ | $\ge 100.0$ (Sharp focus) |
| **Brightness** | $< 30.0$ or $> 235.0$ | $30.0 \le \text{Bri} < 50.0$ or $215.0 < \text{Bri} \le 235.0$ | $50.0 \le \text{Bri} \le 215.0$ |
| **Contrast ($\sigma$)** | $< 15.0$ | $15.0 \le \sigma < 28.0$ | $\ge 28.0$ |
| **Resolution** | $< 200 \times 200\text{px}$ | $< 400 \times 400\text{px}$ | $\ge 400 \times 400\text{px}$ |

---

## 4. OCR Result Schema
```json
{
  "ocr_id": "8f8b8989-1234-4567-89ab-cdef01234567",
  "evidence_id": "6563ee7e-491b-4e59-8bbe-5b1e215aeeba",
  "inspection_id": "c3617eb9-e8e6-4b4c-8ee6-4e6868d9c7c3",
  "engine": "PaddleOCR-v4",
  "preprocessing_variant": "contrast_enhanced",
  "full_text": "LEGAL METROLOGY INSPECTION SAMPLE\nMRP Rs 150.00 INCL OF ALL TAXES NET QTY 500g",
  "boxes_json": [
    {
      "text": "MRP Rs 150.00 INCL OF ALL TAXES NET QTY 500g",
      "confidence": 0.9624,
      "bbox": [[50.0, 200.0], [750.0, 200.0], [750.0, 235.0], [50.0, 235.0]],
      "char_height_px": 35.0,
      "evidence_id": "6563ee7e-491b-4e59-8bbe-5b1e215aeeba"
    }
  ],
  "average_confidence": 0.9624,
  "processing_time_ms": 145.2,
  "created_at": "2026-09-02T02:15:00Z"
}
```

---

## 5. Failure & Retry Handling
* **PaddleOCR / Hardware Failures:** Falls back to computer vision text-region detection; logs error category; preserves original evidence file.
* **Poor Quality Images:** Marked `MANUAL_REVIEW`; prevents silent downstream false negatives.
* **Retry Capability:** Endpoint `POST /api/v1/evidence/{evidence_id}/retry` re-executes quality checks, regeneration of preprocessing variants, and OCR extraction without requiring image re-upload.
