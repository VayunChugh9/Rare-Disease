# RefTriage — CCD/CCDA Mapping & Code Reference

> **Purpose**: Complete reference for building the CCD/CCDA XML parser. Contains every XPath pattern, section LOINC code, field mapping, date format rule, and code system lookup needed to extract structured data from C-CDA R2.1 documents (Synthea and real-world).

---

## 1. XML namespace setup

All CCD elements live in the `urn:hl7-org:v3` namespace. The parser MUST use namespace-aware queries or everything returns empty.

```python
NAMESPACES = {
    'cda': 'urn:hl7-org:v3',
    'sdtc': 'urn:hl7-org:sdtc',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}
```

All XPath expressions below assume these namespace prefixes.

---

## 2. Date format

CCD dates use HL7 format: `YYYYMMDDHHMMSS` with no separators. The parser must handle variable precision:

| Raw value | Parsed |
|---|---|
| `20250623215054` | `2025-06-23T21:50:54Z` |
| `20250623` | `2025-06-23` |
| `202506` | `2025-06-01` (first of month) |
| `2025` | `2025-01-01` (first of year) |
| empty / missing | `null` |

For stop/resolution dates, empty means "currently active."

---

## 3. Section-by-section extraction

### 3.1 Patient demographics

**XPath root**: `/cda:ClinicalDocument/cda:recordTarget/cda:patientRole`

| Field | XPath (relative to patientRole) | Notes |
|---|---|---|
| first_name | `cda:patient/cda:name/cda:given/text()` | |
| last_name | `cda:patient/cda:name/cda:family/text()` | |
| dob | `cda:patient/cda:birthTime/@value` | HL7 format |
| sex | `cda:patient/cda:administrativeGenderCode/@code` | M, F |
| race | `cda:patient/cda:raceCode/@displayName` | |
| ethnicity | `cda:patient/cda:ethnicGroupCode/@displayName` | |
| language | `cda:patient/cda:languageCommunication/cda:languageCode/@code` | |
| mrn | `cda:id/@extension` | |
| street | `cda:addr/cda:streetAddressLine/text()` | |
| city | `cda:addr/cda:city/text()` | |
| state | `cda:addr/cda:state/text()` | |
| zip | `cda:addr/cda:postalCode/text()` | |
| phone | `cda:telecom/@value` | May be `nullFlavor="NI"` — check for nullFlavor first |

### 3.2 Source organization

**XPath**: `/cda:ClinicalDocument/cda:author/cda:assignedAuthor/cda:representedOrganization`

| Field | XPath (relative) |
|---|---|
| name | `cda:name/text()` |
| street | `cda:addr/cda:streetAddressLine/text()` |
| city | `cda:addr/cda:city/text()` |
| state | `cda:addr/cda:state/text()` |
| zip | `cda:addr/cda:postalCode/text()` |
| phone | `cda:telecom/@value` |

### 3.3 Allergies

**Section locator**: `//cda:section[cda:code[@code='48765-2']]`
**templateId**: `2.16.840.1.113883.10.20.22.2.6.1`

**If section has `nullFlavor="NI"`**: No known allergies. Set `no_known_allergies = true`, `entries = []`.

**Otherwise, for each entry**:
```
XPath: section//cda:act/cda:entryRelationship/cda:observation
```

| Field | XPath (relative to observation) |
|---|---|
| substance | `cda:participant/cda:participantRole/cda:playingEntity/cda:code/@displayName` |
| substance_code | `cda:participant/cda:participantRole/cda:playingEntity/cda:code/@code` |
| reaction | `cda:entryRelationship/cda:observation/cda:value/@displayName` (reaction observation) |
| severity | `cda:entryRelationship/cda:observation/cda:value/@displayName` (severity observation) |
| status | `cda:entryRelationship/cda:observation/cda:statusCode/@code` |

### 3.4 Medications

**Section locator**: `//cda:section[cda:code[@code='10160-0']]`
**templateId**: `2.16.840.1.113883.10.20.22.2.1.1`

**For each entry**:
```
XPath: section//cda:substanceAdministration
```

| Field | XPath (relative to substanceAdministration) |
|---|---|
| name | `cda:consumable/cda:manufacturedProduct/cda:manufacturedMaterial/cda:code/@displayName` |
| code | `cda:consumable/cda:manufacturedProduct/cda:manufacturedMaterial/cda:code/@code` |
| code_system | `cda:consumable/cda:manufacturedProduct/cda:manufacturedMaterial/cda:code/@codeSystem` |
| start_date | `cda:effectiveTime/cda:low/@value` |
| stop_date | `cda:effectiveTime/cda:high/@value` |

**Active inference**: `is_active = (stop_date is null) OR (stop_date > today)`

**Code system mapping**: If `codeSystem="2.16.840.1.113883.6.88"` → RxNorm.

**Dedup note**: Synthea generates a new substanceAdministration for every renewal of the same medication. The deduplicator must collapse these (see recency_filter_config in schemas.json).

### 3.5 Problems / Conditions

**Section locator**: `//cda:section[cda:code[@code='11450-4']]`
**templateId**: `2.16.840.1.113883.10.20.22.2.5.1`

**For each entry**:
```
XPath: section//cda:act/cda:entryRelationship/cda:observation
```

| Field | XPath (relative to observation) |
|---|---|
| description | `cda:value/@displayName` |
| code | `cda:value/@code` |
| code_system_oid | `cda:value/@codeSystem` |
| onset_date | `cda:effectiveTime/cda:low/@value` |
| resolution_date | `cda:effectiveTime/cda:high/@value` |

**Code system mapping**: `codeSystem="2.16.840.1.113883.6.96"` → SNOMED CT.

**Critical filtering**: Many entries in this section are NOT clinical problems. Check each entry's SNOMED code against the `filter_out_snomed_codes` list in recency_filter_config. Route employment/education entries to `social_history` instead of `problem_list`.

**is_clinical logic**:
```python
NON_CLINICAL_SNOMEDS = {"160903007", "160904001", "473461003", "314529007", "105480006"}
is_clinical = code not in NON_CLINICAL_SNOMEDS
```

### 3.6 Diagnostic Results (Labs)

**Section locator**: `//cda:section[cda:code[@code='30954-2']]`
**templateId**: `2.16.840.1.113883.10.20.22.2.3.1`

This section has a nested structure: panels (organizers) contain individual test results (observations).

**For each panel**:
```
XPath: section//cda:organizer[@classCode='BATTERY']
```

| Field | XPath (relative to organizer) |
|---|---|
| panel_name | `cda:code/@displayName` |
| panel_loinc | `cda:code/@code` |
| date | `cda:effectiveTime/cda:low/@value` |

**For each result within a panel**:
```
XPath: organizer/cda:component/cda:observation
```

| Field | XPath (relative to observation) |
|---|---|
| test_name | `cda:code/@displayName` |
| loinc | `cda:code/@code` |
| value | `cda:value/@value` |
| unit | `cda:value/@unit` |
| date | `cda:effectiveTime/@value` |

**Value types**: Check `cda:value/@xsi:type`:
- `PQ` = physical quantity (has `@value` and `@unit`)
- `CD` = coded value (has `@displayName`)
- `ST` = string (text content)

**Screening instrument detection**: Panels with these LOINC codes are mental health/substance use screenings, NOT standard labs:

| LOINC | Instrument |
|---|---|
| 69737-5 | GAD-7 |
| 55757-9 | PHQ-2 |
| 44249-1 | PHQ-9 |
| 72109-2 | AUDIT-C |
| 82666-9 | DAST-10 |
| 76499-3 | HARK |

Route these to `functional_status_all` in the intermediate schema and `screenings` in the canonical schema.

### 3.7 Vital Signs

**Section locator**: `//cda:section[cda:code[@code='8716-3']]`
**templateId**: `2.16.840.1.113883.10.20.22.2.4.1`

**For each observation**:
```
XPath: section//cda:observation
```

| Field | XPath (relative to observation) |
|---|---|
| measure | `cda:code/@displayName` |
| loinc | `cda:code/@code` |
| value | `cda:value/@value` |
| unit | `cda:value/@unit` |
| date | `cda:effectiveTime/@value` |

**Known LOINC codes for vital signs**:

| LOINC | Measure | Typical unit |
|---|---|---|
| 8302-2 | Body Height | cm |
| 29463-7 | Body Weight | kg |
| 39156-5 | BMI | kg/m2 |
| 8867-4 | Heart Rate | /min |
| 9279-1 | Respiratory Rate | /min |
| 8480-6 | Systolic BP | mm[Hg] |
| 8462-4 | Diastolic BP | mm[Hg] |
| 72514-3 | Pain Severity (0-10) | {score} |
| 8310-5 | Body Temperature | Cel |
| 2708-6 | O2 Saturation | % |

**Note**: Synthea may not include BP as separate systolic/diastolic in the vital signs section. Check both observation-level and organizer-level patterns.

### 3.8 Procedures / Surgeries

**Section locator**: `//cda:section[cda:code[@code='47519-4']]`
**templateId**: `2.16.840.1.113883.10.20.22.2.7.1`

**For each entry**:
```
XPath: section//cda:procedure
```

| Field | XPath (relative to procedure) |
|---|---|
| description | `cda:code/@displayName` |
| code | `cda:code/@code` |
| code_system_oid | `cda:code/@codeSystem` |
| start_date | `cda:effectiveTime/cda:low/@value` or `cda:effectiveTime/@value` |
| end_date | `cda:effectiveTime/cda:high/@value` |

**Surgical vs assessment classification**: Synthea includes assessments and screenings in this section (e.g., "Assessment of anxiety", "Depression screening"). These are NOT surgical procedures. Use heuristics:
- Contains "assessment", "screening", "evaluation", "counseling", "education" → `is_surgical = false`
- Contains "surgery", "repair", "replacement", "excision", "removal", "implant", "biopsy", "graft", "-ectomy", "-otomy", "-plasty", "-oscopy" → `is_surgical = true`
- Default: `is_surgical = false`

### 3.9 Encounters

**Section locator**: `//cda:section[cda:code[@code='46240-8']]`
**templateId**: `2.16.840.1.113883.10.20.22.2.22.1`

**For each entry**:
```
XPath: section//cda:encounter
```

| Field | XPath (relative to encounter) |
|---|---|
| description | `cda:code/@displayName` |
| code | `cda:code/@code` |
| start_date | `cda:effectiveTime/cda:low/@value` |
| end_date | `cda:effectiveTime/cda:high/@value` |
| provider | `cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name` |
| location | `cda:participant/cda:participantRole/cda:addr` |

### 3.10 Immunizations

**Section locator**: `//cda:section[cda:code[@code='11369-6']]`
**templateId**: `2.16.840.1.113883.10.20.22.2.2.1`

**For each entry**:
```
XPath: section//cda:substanceAdministration
```

| Field | XPath |
|---|---|
| vaccine | `cda:consumable/cda:manufacturedProduct/cda:manufacturedMaterial/cda:code/@displayName` |
| code | `cda:consumable/cda:manufacturedProduct/cda:manufacturedMaterial/cda:code/@code` |
| date | `cda:effectiveTime/@value` |
| status | `cda:statusCode/@code` |

### 3.11 Social History

**Section locator**: `//cda:section[cda:code[@code='29762-2']]`
**templateId**: `2.16.840.1.113883.10.20.22.2.17`

Typically contains only smoking status in Synthea:

```
XPath: section//cda:observation[cda:code[@code='72166-2']]
```

| Field | XPath (relative to observation) |
|---|---|
| smoking_status | `cda:value/@displayName` |
| smoking_code | `cda:value/@code` |
| date | `cda:effectiveTime/@value` |

**Enrich from Problems section**: Employment status and education level entries filtered out of the problems section should be routed here.

### 3.12 Functional Status (Survey/Screening Scores)

**Section locator**: `//cda:section[cda:code[@code='47420-5']]`
**templateId**: `2.16.840.1.113883.10.20.22.2.14`

**For each observation**:
```
XPath: section//cda:observation
```

| Field | XPath (relative to observation) |
|---|---|
| instrument | `cda:code/@displayName` |
| loinc | `cda:code/@code` |
| score | `cda:value/@value` |
| unit | `cda:value/@unit` |
| date | `cda:effectiveTime/@value` |

**Note**: Screening results appear in BOTH the Diagnostic Results section (as organizer panels) and the Functional Status section (as individual scores). The parser should deduplicate by LOINC code + date, preferring the version with the individual score value.

### 3.13 Plan of Care

**Section locator**: `//cda:section[cda:code[@code='18776-5']]`
**templateId**: `2.16.840.1.113883.10.20.22.2.10`

Parse any active care plan entries. Structure varies widely across implementations.

---

## 4. Code system OID reference

When the parser encounters a `codeSystem` attribute, use this lookup to identify the coding system:

| OID | Code system | Used for |
|---|---|---|
| 2.16.840.1.113883.6.96 | SNOMED CT | Conditions, procedures, findings |
| 2.16.840.1.113883.6.88 | RxNorm | Medications |
| 2.16.840.1.113883.6.1 | LOINC | Labs, vitals, screening instruments |
| 2.16.840.1.113883.6.90 | ICD-10-CM | Diagnoses (less common in CCDs) |
| 2.16.840.1.113883.6.12 | CPT | Procedures |
| 2.16.840.1.113883.6.59 | CVX | Vaccines |
| 2.16.840.1.113883.5.1 | HL7 AdministrativeGender | Sex (M, F) |
| 2.16.840.1.113883.6.238 | CDC Race and Ethnicity | Race, ethnicity |

---

## 5. Screening score interpretation reference

For use in the summarization prompt and the ScreeningScoreCard UI component:

| Instrument | Score range | Interpretation |
|---|---|---|
| **GAD-7** | 0–4 | Minimal anxiety |
| | 5–9 | Mild anxiety |
| | 10–14 | Moderate anxiety |
| | 15–21 | Severe anxiety |
| **PHQ-2** | 0–2 | Negative screen |
| | ≥3 | Positive (warrants full PHQ-9) |
| **PHQ-9** | 0–4 | Minimal depression |
| | 5–9 | Mild depression |
| | 10–14 | Moderate depression |
| | 15–19 | Moderately severe depression |
| | 20–27 | Severe depression |
| **AUDIT-C** | 0–3 (men) / 0–2 (women) | Negative screen |
| | ≥4 (men) / ≥3 (women) | Positive for unhealthy alcohol use |
| **DAST-10** | 0 | No problems reported |
| | 1–2 | Low level |
| | 3–5 | Moderate level |
| | 6–8 | Substantial level |
| | 9–10 | Severe level |
| **HARK** | 0 | Negative screen |
| | ≥1 | Positive for intimate partner violence |

---

## 6. Common parser pitfalls

1. **Namespace omission**: Every XPath query must use the `cda:` prefix. Bare element names return nothing.
2. **Multiple templateIds**: Sections often have 2 templateId elements (versioned and unversioned). Match on either.
3. **nullFlavor**: Check for `nullFlavor` attributes before trying to extract values. `telecom nullFlavor="NI"` means "no information" — don't try to parse a phone number.
4. **Nested effectiveTime**: Medications and conditions may have `effectiveTime` at multiple levels. Use the one directly under the entry element, not nested sub-observations.
5. **Value type checking**: Always check `xsi:type` on `<value>` elements. PQ has `@value` and `@unit`. CD has `@displayName` and `@code`. Accessing `@value` on a CD element returns the code, not a number.
6. **Duplicate data across sections**: Screening scores appear in both Diagnostic Results AND Functional Status. Deduplicate by LOINC + date.
7. **Synthea-specific quirks**: Organization names use `<name>` not `<n>` (but the element IS `<name>` — Synthea just abbreviates the tag occasionally). The parser should handle both. Also, Synthea postalCodes may be "00000" (synthetic placeholder).
