# Phase 4 — Advanced Computer Vision, Physical Reference Calibration & Visual Forensics

## Executive Summary

Phase 4 of the **LegalMetriX** system implements the visual inspection, physical calibration, and forensic anomaly detection pipeline. It bridges optical character recognition (OCR) and deterministic legal rule evaluation by providing verified physical scale estimation ($23.00\text{ mm}$ standard Indian ₹5 coin reference target) and localized sticker overlay suspicion analysis.

---

## 1. System Boundaries & Legal Principles

```
  +-----------------------------------------------------------------------------------+
  |                                PERCEPTION & CV LAYER                             |
  |  - Indian ₹5 Coin Detection (23.00mm physical reference)                          |
  |  - Scale Factor Calculation (mm_per_pixel = 23.00 / pixel_diameter)               |
  |  - Physical Font Height Estimation (mm = pixel_height * mm_per_pixel)             |
  |  - Edge Discontinuity & Adhesive Label Overlay Suspicion Analysis                 |
  +-----------------------------------------------------------------------------------+
                                         │
                                         ▼
  +-----------------------------------------------------------------------------------+
  |                             DETERMINISTIC COMPLIANCE                              |
  |  - RULE-FONT-HEIGHT-MINIMUM: Evaluates measured font against Rule 7 Table        |
  |  - RULE-OVERLAY-STICKER-FLAG: Suspicion signals yield REQUIRES_REVIEW (Never FAIL)|
  +-----------------------------------------------------------------------------------+
                                         │
                                         ▼
  +-----------------------------------------------------------------------------------+
  |                           AUTHORITATIVE OFFICER VERIFICATION                      |
  |  - Inspecting officer retains sole statutory authority to confirm violations     |
  +-----------------------------------------------------------------------------------+
```

### Critical Boundaries
1. **Engineering Measurement Aid Only**: Calibration is an engineering measurement aid; it is not legal proof by itself or an automatic compliance decision.
2. **Missing Calibration Handling**: When calibration cannot be established (`CALIBRATION_UNAVAILABLE` or `AMBIGUOUS_CALIBRATION`), font measurement defaults to `status = CALIBRATION_REQUIRED` and downstream rules evaluate to `REQUIRES_REVIEW`. The system **never** guesses a calibration scale.
3. **Sticker / Overlay Safety**: Adhesive label signals generate `SUSPECTED_OVERLAY` and yield `FindingStatus.REVIEW`. Under no circumstances does a visual suspicion signal independently produce `FAIL` or `NON_COMPLIANT`.
4. **Evidence Immutability**: All original uploaded evidence items remain strictly immutable. Overlays (calibration circles, font measurement boxes, anomaly boundaries) are generated as derived copies in `storage/derived/{inspection_id}/{evidence_id}/`.
5. **Multi-View Isolation**: Calibration is established per individual evidence view (`evidence_id`) and is never silently propagated across angles.

---

## 2. OpenCV Physical Calibration Pipeline

- **Target Object**: Standard Indian ₹5 coin ($23.00\text{ mm}$ physical diameter).
- **Computer Vision Algorithm**:
  1. Grayscale conversion with Gaussian blur kernel $(5, 5, 1.2)$.
  2. Edge map calculation via Canny edge detector with morphological closing.
  3. Closed contour extraction and circularity verification:
     $$\text{Circularity} = 4\pi \frac{\text{Area}}{\text{Perimeter}^2} \ge 0.75$$
     $$\text{Aspect Ratio} = \frac{\text{Width}}{\text{Height}} \in [0.82, 1.22]$$
  4. Deduplication of concentric detections ($< 30\text{px}$ center distance).
  5. Calculation of calibration scale:
     $$\text{mm\_per\_pixel} = \frac{23.00}{2 \times r}$$
  6. Status assignment:
     - 1 validated reference $\rightarrow$ `CALIBRATED`.
     - $> 2$ distinct conflicting circles $\rightarrow$ `AMBIGUOUS_CALIBRATION`.
     - No circles found $\rightarrow$ `CALIBRATION_UNAVAILABLE`.

---

## 3. Physical Font Height Estimation & Statutory Schedule (Phase 4.1 Safety Architecture)

> **Core Boundary Principle**:
> "Computer vision provides physical measurements. Legal compliance is determined only through verified statutory configuration and deterministic rule evaluation."

Using active calibration data, OCR bounding box pixel heights are converted to physical millimeters:
$$\text{physical\_height\_mm} = \text{height\_px} \times \text{mm\_per\_pixel}$$

### Rule 7(1) Table 1 Statutory Character Height Schedule (G.S.R. 202(E))
| Net Quantity Range ($Q$) | Normal Print (Letters) | Normal Print (Numerals) | Blown / Moulded / Perforated | Status in LegalMetriX |
| :--- | :--- | :--- | :--- | :--- |
| $\le 50\text{ g / ml}$ | $1.0\text{ mm}$ | $1.5\text{ mm}$ | $2.0\text{ mm}$ | `VERIFIED_AUTHORITATIVE` |
| $> 50\text{ g / ml} \le 100\text{ g / ml}$ | $1.5\text{ mm}$ | $2.0\text{ mm}$ | $4.0\text{ mm}$ | `VERIFIED_AUTHORITATIVE` |
| $> 100\text{ g / ml} \le 500\text{ g / ml}$ | $2.5\text{ mm}$ | $4.0\text{ mm}$ | $6.0\text{ mm}$ | `VERIFIED_AUTHORITATIVE` |
| $> 500\text{ g / ml} \le 1\text{ kg / L}$ | $4.0\text{ mm}$ | $4.0\text{ mm}$ | $6.0\text{ mm}$ | `VERIFIED_AUTHORITATIVE` |
| $> 1\text{ kg / L}$ | $6.0\text{ mm}$ | $6.0\text{ mm}$ | $6.0\text{ mm}$ | `VERIFIED_AUTHORITATIVE` |
| *Indeterminate applicability / Unknown character type* | *N/A* | *N/A* | *N/A* | **`REQUIRES_REVIEW`** |


---

## 4. API Endpoints

- `POST /api/v1/cases/{id}/calibration/{evidence_id}`: Executes ₹5 coin detection.
- `GET /api/v1/cases/{id}/calibration`: Retrieves calibrations for a case.
- `POST /api/v1/cases/{id}/measurements/{evidence_id}`: Measures physical font heights.
- `GET /api/v1/cases/{id}/measurements`: Retrieves case visual measurements.
- `POST /api/v1/cases/{id}/visual-anomalies/{evidence_id}`: Scans for sticker overlays.
- `GET /api/v1/cases/{id}/visual-anomalies`: Retrieves visual anomalies for a case.

---

## 5. Verification & Test Suite

All 30 automated integration and contract tests pass with 100% compliance:
- `test_coin_reference_calibration_success`: PASS
- `test_coin_calibration_unavailable_when_no_coin`: PASS
- `test_font_measurement_with_and_without_calibration`: PASS
- `test_sticker_overlay_anomaly_detection_and_rule_integration`: PASS
- `test_multi_view_calibration_isolation`: PASS
- `test_golden_01` through `test_golden_05`: PASS
