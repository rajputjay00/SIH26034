# LegalMetriX — Structured Extraction & Provenance Pipeline

## 1. Pipeline Overview & Trust Boundary
Under no circumstances does the extraction pipeline or LLM evaluate statutory compliance or issue PASS/FAIL determinations. The LLM is strictly confined to machine perception parsing and structured transformation from raw OCR strings into typed schema instances.

```
+----------------------------------------------------------------------------------------------------+
|                              STRUCTURED EXTRACTION & PROVENANCE FLOW                               |
+----------------------------------------------------------------------------------------------------+

   +----------------------------------------------------------------------------------------------+
   | 1. RAW OCR PERCEPTION RESULT                                                                 |
   | • Text lines, polygon bounding boxes [[x1,y1],[x2,y2],[x3,y3],[x4,y4]], confidence scores    |
   | • Source evidence ID & view orientation (FRONT / BACK / SIDE / BASE)                         |
   +----------------------------------------------+-----------------------------------------------+
                                                  |
                                                  v
   +----------------------------------------------------------------------------------------------+
   | 2. STRUCTURED EXTRACTION PROVIDER (LLM / REGEX ADAPTER)                                      |
   | • GeminiStructuredExtractor / DeterministicExtractionProvider                                |
   | • Strict Pydantic JSON Schema enforcement                                                    |
   | • Offline deterministic fallback for all standard declaration patterns                      |
   +----------------------------------------------+-----------------------------------------------+
                                                  |
                                                  v
   +----------------------------------------------------------------------------------------------+
   | 3. DECIMAL-SAFE NORMALIZATION ENGINE                                                         |
   | • Mass: mg -> g -> kg                                                                        |
   | • Volume: ml -> cl -> L                                                                      |
   | • Count: N / units / pcs -> N                                                                |
   | • Currency: ₹ / Rs / INR -> Decimal('0.00'), 'INR'                                           |
   | * Original raw text string is preserved unaltered                                            |
   +----------------------------------------------+-----------------------------------------------+
                                                  |
                                                  v
   +----------------------------------------------------------------------------------------------+
   | 4. MULTI-VIEW CONFLICT DETECTION                                                             |
   | • Groups duplicate declarations across distinct views (e.g., Front MRP vs Back MRP)          |
   | • Sets field_status = CONFLICTING if normalized values mismatch                              |
   | • Preserves provenance links to all conflicting evidence images                              |
   +----------------------------------------------+-----------------------------------------------+
                                                  |
                                                  v
   +----------------------------------------------------------------------------------------------+
   | 5. AUTHORITATIVE OFFICER REVIEW & CORRECTION                                                 |
   | • Officer can review extracted fields and override incorrect OCR misreads                    |
   | • Generates an immutable FieldCorrection audit record                                        |
   | • Updates origin to OFFICER without destroying historical raw OCR text                       |
   +----------------------------------------------------------------------------------------------+
```

---

## 2. Declaration Categories & Schema

| Field Name | Description | Example Raw OCR | Normalized Value | Unit |
| :--- | :--- | :--- | :--- | :--- |
| `commodity_name` | Generic or common name of commodity | "Organic Wheat Flour" | "Organic Wheat Flour" | — |
| `net_quantity` | Standard weight, measure, or number | "Net Wt: 500 g" | "0.5000" | `kg` |
| `mrp` | Maximum Retail Price incl. taxes | "MRP Rs. 150.00 incl taxes" | "150.00" | `INR` |
| `unit_sale_price` | Unit Sale Price per standard unit | "USP Rs. 300.00 / kg" | "300.00" | `INR/unit` |
| `manufacturer` | Name and address of manufacturer | "Mfr by ABC Foods Pvt Ltd" | "ABC Foods Pvt Ltd" | — |
| `country_of_origin` | Country of origin | "Country of Origin: India" | "India" | — |
| `consumer_care` | Customer care executive contacts | "Care: care@abc.com, Tel 1800"| "care@abc.com" | — |
| `manufacture_date` | Month & Year of manufacture | "Pkg: 08/2026" | "08/2026" | — |
| `best_before_date` | Expiry or Best-Before duration | "Best before 12 months" | "12 months" | — |
| `dimensions` | Physical dimensions of commodity | "Size: 10cm x 20cm" | "10cm x 20cm" | — |

---

## 3. Field Status Model
* `EXTRACTED`: Automatically extracted by perception adapter.
* `MISSING`: Declaration was not located on available evidence.
* `UNCERTAIN`: Extraction confidence is below threshold ($< 0.85$).
* `CONFLICTING`: Mismatch detected across multiple evidence views.
* `CORRECTED`: Corrected by an authoritative human officer.
* `NOT_APPLICABLE`: Legally established as exempt or not applicable.
* `MANUAL_REVIEW`: Requires human verification.
