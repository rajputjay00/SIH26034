# LegalMetriX — Deterministic Compliance Rule Engine

## 1. Statutory Architecture & Legal Hierarchy
The deterministic rule engine is independent of LLMs, computer vision libraries, and UI frameworks. It evaluates normalized structured fields against versioned statutory rule packs adhering to the Legal Metrology (Packaged Commodities) Rules, 2011 and Department of Consumer Affairs amendments.

```
+----------------------------------------------------------------------------------------------------+
|                                DETERMINISTIC RULE ENGINE EXECUTION                                 |
+----------------------------------------------------------------------------------------------------+

   Structured Fields (Extracted & Corrected)
                        +
   Rule Pack Version: RULE-PACK-LM-2026-V1
                        ↓
   +----------------------------------------------------------------------------------------------+
   | DETERMINISTIC STATUTORY EVALUATION                                                           |
   |                                                                                              |
   | 1. RULE-DECL-COMMODITY-NAME (Rule 6(1)(a)) -> PASS / FAIL / REVIEW                           |
   | 2. RULE-DECL-NET-QTY        (Rule 6(1)(b)) -> PASS / FAIL                                    |
   | 3. RULE-DECL-MRP            (Rule 6(1)(e)) -> PASS / FAIL / REVIEW                           |
   | 4. RULE-DECL-MFR-PACKER     (Rule 6(1)(a)) -> PASS / FAIL                                    |
   | 5. RULE-DECL-COUNTRY-ORIGIN (Rule 6(10))   -> PASS / REVIEW                                  |
   | 6. RULE-DECL-CONSUMER-CARE  (Rule 6(1)(f)) -> PASS / FAIL                                    |
   | 7. RULE-DECL-DATE-MARKS     (Rule 6(1)(d)) -> PASS / FAIL                                    |
   | 8. RULE-USP-CONSISTENCY     (Rule 6(1)(e)) -> PASS / FAIL / REVIEW (Decimal Math: MRP / Qty)  |
   | 9. RULE-FONT-HEIGHT-MINIMUM (Rule 7)       -> REVIEW (Uncalibrated threshold)                |
   | 10. RULE-OVERLAY-STICKER-FLAG(Rule 6(2))   -> PASS / REVIEW (Suspicion flag)                 |
   +----------------------------------------------+-----------------------------------------------+
                        ↓
   +----------------------------------------------------------------------------------------------+
   | DETERMINISTIC DETERMINATION AGGREGATION                                                      |
   | • COMPLIANT: All applicable rules evaluate to PASS & 0 REVIEW conditions.                    |
   | • NON_COMPLIANT: Any applicable rule evaluates to FAIL.                                      |
   | • REQUIRES_REVIEW: Any rule evaluates to REVIEW, or unconfigured statutory thresholds exist. |
   +----------------------------------------------------------------------------------------------+
```

---

## 2. Statutory Rules Specification

| Rule ID | Statutory Citation | Evaluation Logic | Severity |
| :--- | :--- | :--- | :--- |
| `RULE-DECL-COMMODITY-NAME` | Rule 6(1)(a), PC Rules 2011 | Checks presence and readability of generic/common commodity name. | `HIGH` |
| `RULE-DECL-NET-QTY` | Rule 6(1)(b), PC Rules 2011 | Checks presence of net quantity in standard metric units (`kg`, `g`, `L`, `ml`, `N`). | `CRITICAL` |
| `RULE-DECL-MRP` | Rule 6(1)(e), PC Rules 2011 | Checks retail sale price declaration and format. Flags cross-view discrepancies. | `CRITICAL` |
| `RULE-DECL-MFR-PACKER` | Rule 6(1)(a), PC Rules 2011 | Checks presence of name and complete address of manufacturer/packer. | `HIGH` |
| `RULE-DECL-COUNTRY-ORIGIN` | Rule 6(10), PC Rules 2011 | Checks country of origin declaration (mandatory for imported commodities). | `LOW` |
| `RULE-DECL-CONSUMER-CARE` | Rule 6(1)(f), PC Rules 2011 | Checks name, address, telephone number, or email of consumer care executive. | `HIGH` |
## 4. Rule 7 Character Height Verification Architecture (Phase 4.1 Safety Architecture)

> **Core Boundary Principle**:
> Computer vision provides physical engineering measurements. Legal compliance is determined only through verified statutory configuration and deterministic rule evaluation.

### A. Applicability Inputs
The deterministic Rule 7 engine evaluates:
- **Character Type**: `LETTER` vs `NUMERAL` (under Rule 7 Table 1, letter vs numeral minimum heights differ, e.g. $2.5\text{ mm}$ for letters vs $4.0\text{ mm}$ for numerals in the $100\text{g}-500\text{g}$ range). If character type is `UNKNOWN`, evaluation yields `REQUIRES_REVIEW`.
- **Net Quantity ($Q$)**: Must be normalized to metric grams/millilitres. If missing or unparseable, yields `REQUIRES_REVIEW`.
- **Principal Display Panel Area ($A$)**: Used when area schedule applies; never guessed.
- **Declaration Method / Substrate**: `NORMAL_PRINT` vs `BLOWN_MOULDED_EMBOSSED`. If undetermined, yields `REQUIRES_REVIEW`.

### B. Removal of Arbitrary Fallback
* The legacy $2.0\text{ mm}$ arbitrary fallback has been completely removed.
* Any uncalibrated, unparseable, undetermined character type, or unconfigured threshold condition returns `FindingStatus.REVIEW` with explicit metadata explanation (`NOT_CONFIGURED`, `CHARACTER_TYPE_UNKNOWN`, etc.).
* Only verified authoritative statutory thresholds from the Gazette notification (`G.S.R. 202(E)`) generate deterministic `PASS` or `FAIL`.

