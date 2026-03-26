"""CCD/CCDA XML parser following reftriage_mappings.md.

Parses C-CDA R2.1 documents (Synthea and real-world) into the CCD intermediate schema.
All XPath queries use namespace-aware patterns.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional
from uuid import uuid4

from lxml import etree

from backend.app.models.schemas import (
    CCDAllergies,
    CCDAllergyEntry,
    CCDCarePlan,
    CCDCondition,
    CCDEncounter,
    CCDFunctionalStatus,
    CCDImmunization,
    CCDIntermediate,
    CCDLabComponent,
    CCDLabResult,
    CCDMedication,
    CCDPatient,
    CCDPatientAddress,
    CCDProcedure,
    CCDSocialHistory,
    CCDSourceOrganization,
    CCDVital,
)
from backend.app.utils.date_parser import parse_hl7_date, parse_hl7_datetime

# ---------------------------------------------------------------------------
# Namespace setup (§1)
# ---------------------------------------------------------------------------
NAMESPACES = {
    "cda": "urn:hl7-org:v3",
    "sdtc": "urn:hl7-org:sdtc",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

# ---------------------------------------------------------------------------
# Code system OID lookup (§4)
# ---------------------------------------------------------------------------
CODE_SYSTEM_MAP = {
    "2.16.840.1.113883.6.96": "SNOMED",
    "2.16.840.1.113883.6.88": "RxNorm",
    "2.16.840.1.113883.6.1": "LOINC",
    "2.16.840.1.113883.6.90": "ICD-10",
    "2.16.840.1.113883.6.12": "CPT",
    "2.16.840.1.113883.6.59": "CVX",
    "2.16.840.1.113883.12.292": "CVX",
    "2.16.840.1.113883.5.1": "HL7 AdministrativeGender",
    "2.16.840.1.113883.6.238": "CDC Race and Ethnicity",
}

# Non-clinical SNOMED codes to filter from problem list (§3.5)
NON_CLINICAL_SNOMEDS = {
    "160903007",  # Full-time employment
    "160904001",  # Part-time employment
    "473461003",  # Education level
    "314529007",  # Medication review due
    "105480006",  # Refusal of treatment
    "160245001",  # No current problems
    "266919005",  # Never smoked (goes to social_history)
    # Additional education-related codes found in Synthea
    "224299000",  # Received higher education
    "224298008",  # Received certificate of high school equivalency
    "741062008",  # Not in labor force
}

# Screening instrument LOINC codes (§3.6) — route to functional_status, not labs
SCREENING_PANEL_LOINCS = {
    "69737-5",  # GAD-7
    "55757-9",  # PHQ-2
    "44249-1",  # PHQ-9
    "72109-2",  # AUDIT-C
    "82666-9",  # DAST-10
    "76499-3",  # HARK
}

# Screening score LOINC codes (individual total scores in functional status)
SCREENING_SCORE_LOINCS = {
    "70274-6",  # GAD-7 total score
    "55758-7",  # PHQ-2 total score
    "44261-6",  # PHQ-9 total score
    "75626-2",  # AUDIT-C total score
    "82667-7",  # DAST-10 total score
    "76504-0",  # HARK total score
}

# Map screening score LOINCs to instrument names
SCREENING_LOINC_TO_NAME = {
    "70274-6": "GAD-7",
    "55758-7": "PHQ-2",
    "44261-6": "PHQ-9",
    "75626-2": "AUDIT-C",
    "82667-7": "DAST-10",
    "76504-0": "HARK",
    # Panel LOINCs
    "69737-5": "GAD-7",
    "55757-9": "PHQ-2",
    "44249-1": "PHQ-9",
    "72109-2": "AUDIT-C",
    "82666-9": "DAST-10",
    "76499-3": "HARK",
}


def _xpath(element: etree._Element, path: str) -> list:
    """Run namespace-aware XPath query."""
    return element.xpath(path, namespaces=NAMESPACES)


def _xpath_text(element: etree._Element, path: str) -> Optional[str]:
    """Get text from first XPath match, or None."""
    results = _xpath(element, path)
    if results:
        val = results[0]
        if isinstance(val, str):
            return val.strip() or None
        if hasattr(val, "text") and val.text:
            return val.text.strip() or None
    return None


def _xpath_attr(element: etree._Element, path: str) -> Optional[str]:
    """Get attribute value from XPath (path should end with /@attr)."""
    results = _xpath(element, path)
    if results:
        val = results[0] if isinstance(results[0], str) else str(results[0])
        return val.strip() or None
    return None


def _resolve_code_system(oid: Optional[str]) -> Optional[str]:
    """Map OID to human-readable code system name."""
    if not oid:
        return None
    return CODE_SYSTEM_MAP.get(oid)


def _has_null_flavor(element: etree._Element) -> bool:
    """Check if element has nullFlavor attribute."""
    return element.get("nullFlavor") is not None


# ---------------------------------------------------------------------------
# Section parsers (§3.1 - §3.13)
# ---------------------------------------------------------------------------

def _find_section(root: etree._Element, section_code: str) -> Optional[etree._Element]:
    """Find a section by its LOINC code."""
    sections = _xpath(root, f"//cda:section[cda:code[@code='{section_code}']]")
    return sections[0] if sections else None


def parse_demographics(root: etree._Element) -> CCDPatient:
    """§3.1 Patient demographics."""
    pr = _xpath(root, "/cda:ClinicalDocument/cda:recordTarget/cda:patientRole")
    if not pr:
        return CCDPatient()
    pr = pr[0]

    # Check if telecom has nullFlavor
    phone = None
    telecoms = _xpath(pr, "cda:telecom")
    for t in telecoms:
        if not _has_null_flavor(t):
            phone = t.get("value")
            break

    address = CCDPatientAddress(
        street=_xpath_text(pr, "cda:addr/cda:streetAddressLine"),
        city=_xpath_text(pr, "cda:addr/cda:city"),
        state=_xpath_text(pr, "cda:addr/cda:state"),
        zip=_xpath_text(pr, "cda:addr/cda:postalCode"),
    )

    dob_raw = _xpath_attr(pr, "cda:patient/cda:birthTime/@value")

    return CCDPatient(
        first_name=_xpath_text(pr, "cda:patient/cda:name/cda:given"),
        last_name=_xpath_text(pr, "cda:patient/cda:name/cda:family"),
        dob_raw=dob_raw,
        dob_parsed=parse_hl7_date(dob_raw),
        sex=_xpath_attr(pr, "cda:patient/cda:administrativeGenderCode/@code"),
        race=_xpath_attr(pr, "cda:patient/cda:raceCode/@displayName"),
        ethnicity=_xpath_attr(pr, "cda:patient/cda:ethnicGroupCode/@displayName"),
        language=_xpath_attr(pr, "cda:patient/cda:languageCommunication/cda:languageCode/@code"),
        mrn=_xpath_attr(pr, "cda:id/@extension"),
        address=address,
        phone=phone,
    )


def parse_source_organization(root: etree._Element) -> Optional[CCDSourceOrganization]:
    """§3.2 Source organization."""
    orgs = _xpath(root, "/cda:ClinicalDocument/cda:author/cda:assignedAuthor/cda:representedOrganization")
    if not orgs:
        return None
    org = orgs[0]

    # Build address string
    parts = []
    street = _xpath_text(org, "cda:addr/cda:streetAddressLine")
    city = _xpath_text(org, "cda:addr/cda:city")
    state = _xpath_text(org, "cda:addr/cda:state")
    zip_code = _xpath_text(org, "cda:addr/cda:postalCode")
    if street:
        parts.append(street)
    if city:
        parts.append(city)
    if state:
        parts.append(state)
    if zip_code:
        parts.append(zip_code)

    phone = None
    telecoms = _xpath(org, "cda:telecom")
    for t in telecoms:
        if not _has_null_flavor(t):
            phone = t.get("value")
            break

    return CCDSourceOrganization(
        name=_xpath_text(org, "cda:name"),
        address=", ".join(parts) if parts else None,
        phone=phone,
    )


def parse_allergies(root: etree._Element) -> CCDAllergies:
    """§3.3 Allergies."""
    section = _find_section(root, "48765-2")
    if section is None:
        return CCDAllergies(no_known_allergies=False, entries=[])

    # Check if section has nullFlavor="NI" — no known allergies
    if _has_null_flavor(section):
        return CCDAllergies(no_known_allergies=True, entries=[])

    entries = []
    observations = _xpath(section, ".//cda:act/cda:entryRelationship/cda:observation")
    for obs in observations:
        substance = _xpath_attr(
            obs, "cda:participant/cda:participantRole/cda:playingEntity/cda:code/@displayName"
        )
        if not substance:
            continue
        substance_code = _xpath_attr(
            obs, "cda:participant/cda:participantRole/cda:playingEntity/cda:code/@code"
        )
        # Reaction and severity are in nested entryRelationship observations
        reaction = None
        severity = None
        nested_obs = _xpath(obs, "cda:entryRelationship/cda:observation")
        for nobs in nested_obs:
            val_display = _xpath_attr(nobs, "cda:value/@displayName")
            # Distinguish reaction vs severity by templateId or code
            code_val = _xpath_attr(nobs, "cda:code/@code")
            if val_display:
                if code_val == "SEV":
                    severity = val_display
                else:
                    reaction = val_display

        entries.append(CCDAllergyEntry(
            substance=substance,
            substance_code=substance_code,
            reaction=reaction,
            severity=severity,
            status=_xpath_attr(obs, "cda:statusCode/@code"),
        ))

    return CCDAllergies(
        no_known_allergies=len(entries) == 0,
        entries=entries,
    )


def parse_medications(root: etree._Element) -> list[CCDMedication]:
    """§3.4 Medications."""
    section = _find_section(root, "10160-0")
    if section is None:
        return []

    meds = []
    sub_admins = _xpath(section, ".//cda:substanceAdministration")
    today = date.today()

    for sa in sub_admins:
        name = _xpath_attr(
            sa, "cda:consumable/cda:manufacturedProduct/cda:manufacturedMaterial/cda:code/@displayName"
        )
        if not name:
            continue

        code = _xpath_attr(
            sa, "cda:consumable/cda:manufacturedProduct/cda:manufacturedMaterial/cda:code/@code"
        )
        code_system_oid = _xpath_attr(
            sa, "cda:consumable/cda:manufacturedProduct/cda:manufacturedMaterial/cda:code/@codeSystem"
        )

        start_raw = _xpath_attr(sa, "cda:effectiveTime/cda:low/@value")
        stop_raw = _xpath_attr(sa, "cda:effectiveTime/cda:high/@value")

        start_parsed = parse_hl7_date(start_raw)
        stop_parsed = parse_hl7_date(stop_raw)

        # Active inference: no stop date or stop date in the future
        is_active = stop_parsed is None
        if stop_parsed:
            try:
                is_active = date.fromisoformat(stop_parsed) > today
            except ValueError:
                is_active = False

        meds.append(CCDMedication(
            name=name,
            code=code,
            code_system=_resolve_code_system(code_system_oid),
            start_date_raw=start_raw,
            start_date_parsed=start_parsed,
            stop_date_raw=stop_raw,
            stop_date_parsed=stop_parsed,
            is_active=is_active,
        ))

    return meds


def parse_conditions(root: etree._Element) -> list[CCDCondition]:
    """§3.5 Problems / Conditions."""
    section = _find_section(root, "11450-4")
    if section is None:
        return []

    conditions = []
    observations = _xpath(section, ".//cda:act/cda:entryRelationship/cda:observation")

    for obs in observations:
        description = _xpath_attr(obs, "cda:value/@displayName")
        if not description:
            continue

        code = _xpath_attr(obs, "cda:value/@code")
        code_system_oid = _xpath_attr(obs, "cda:value/@codeSystem")

        onset_raw = _xpath_attr(obs, "cda:effectiveTime/cda:low/@value")
        resolution_raw = _xpath_attr(obs, "cda:effectiveTime/cda:high/@value")

        onset_parsed = parse_hl7_date(onset_raw)
        resolution_parsed = parse_hl7_date(resolution_raw)

        is_active = resolution_parsed is None
        is_clinical = code not in NON_CLINICAL_SNOMEDS if code else True

        conditions.append(CCDCondition(
            description=description,
            code=code,
            code_system=_resolve_code_system(code_system_oid),
            onset_date_raw=onset_raw,
            onset_date_parsed=onset_parsed,
            resolution_date_raw=resolution_raw,
            resolution_date_parsed=resolution_parsed,
            is_active=is_active,
            is_clinical=is_clinical,
        ))

    return conditions


def parse_lab_results(root: etree._Element) -> tuple[list[CCDLabResult], list[CCDFunctionalStatus]]:
    """§3.6 Diagnostic Results (Labs).

    Returns (lab_results, screening_results).
    Screening panels are routed to functional_status.
    """
    section = _find_section(root, "30954-2")
    if section is None:
        return [], []

    labs = []
    screenings = []
    organizers = _xpath(section, ".//cda:organizer[@classCode='BATTERY']")

    for org in organizers:
        panel_loinc = _xpath_attr(org, "cda:code/@code")
        panel_name = _xpath_attr(org, "cda:code/@displayName")
        panel_date_raw = _xpath_attr(org, "cda:effectiveTime/cda:low/@value")

        # Check if this is a screening instrument
        if panel_loinc in SCREENING_PANEL_LOINCS:
            # Extract the total score from components
            components = _xpath(org, "cda:component/cda:observation")
            for comp in components:
                score_val = _xpath_attr(comp, "cda:value/@value")
                score_display = _xpath_attr(comp, "cda:value/@displayName")
                comp_loinc = _xpath_attr(comp, "cda:code/@code")
                comp_date_raw = _xpath_attr(comp, "cda:effectiveTime/@value")
                unit = _xpath_attr(comp, "cda:value/@unit")

                instrument_name = SCREENING_LOINC_TO_NAME.get(
                    comp_loinc, SCREENING_LOINC_TO_NAME.get(panel_loinc, panel_name or "Unknown")
                )

                screenings.append(CCDFunctionalStatus(
                    instrument=instrument_name,
                    loinc=comp_loinc or panel_loinc,
                    score=score_val or score_display,
                    unit=unit,
                    date_parsed=parse_hl7_date(comp_date_raw or panel_date_raw),
                ))
            continue

        # Regular lab panel
        components = []
        comp_observations = _xpath(org, "cda:component/cda:observation")
        for comp in comp_observations:
            # Check value type
            value_elements = _xpath(comp, "cda:value")
            value = None
            unit = None
            if value_elements:
                val_el = value_elements[0]
                xsi_type = val_el.get(f"{{{NAMESPACES['xsi']}}}type")
                if xsi_type == "PQ":
                    value = val_el.get("value")
                    unit = val_el.get("unit")
                elif xsi_type == "CD":
                    value = val_el.get("displayName")
                elif xsi_type == "ST":
                    value = val_el.text
                else:
                    value = val_el.get("value") or val_el.get("displayName") or (val_el.text or "").strip()

            comp_date_raw = _xpath_attr(comp, "cda:effectiveTime/@value")

            components.append(CCDLabComponent(
                test_name=_xpath_attr(comp, "cda:code/@displayName") or "Unknown",
                loinc=_xpath_attr(comp, "cda:code/@code"),
                value=value,
                unit=unit,
                date_raw=comp_date_raw,
                date_parsed=parse_hl7_date(comp_date_raw),
            ))

        labs.append(CCDLabResult(
            panel_name=panel_name or "Unknown",
            panel_loinc=panel_loinc,
            date_raw=panel_date_raw,
            date_parsed=parse_hl7_date(panel_date_raw),
            components=components,
        ))

    return labs, screenings


def parse_vitals(root: etree._Element) -> list[CCDVital]:
    """§3.7 Vital Signs."""
    section = _find_section(root, "8716-3")
    if section is None:
        return []

    vitals = []
    # Vitals are in organizer/component/observation structure
    observations = _xpath(section, ".//cda:organizer/cda:component/cda:observation")

    for obs in observations:
        value_elements = _xpath(obs, "cda:value")
        value = None
        unit = None
        if value_elements:
            val_el = value_elements[0]
            value = val_el.get("value")
            unit = val_el.get("unit")

        date_raw = _xpath_attr(obs, "cda:effectiveTime/@value")

        vitals.append(CCDVital(
            measure=_xpath_attr(obs, "cda:code/@displayName") or "Unknown",
            loinc=_xpath_attr(obs, "cda:code/@code"),
            value=value,
            unit=unit,
            date_raw=date_raw,
            date_parsed=parse_hl7_date(date_raw),
        ))

    return vitals


def parse_procedures(root: etree._Element) -> list[CCDProcedure]:
    """§3.8 Procedures / Surgeries."""
    section = _find_section(root, "47519-4")
    if section is None:
        return []

    procedures = []
    procs = _xpath(section, ".//cda:procedure")

    for proc in procs:
        description = _xpath_attr(proc, "cda:code/@displayName")
        if not description:
            continue

        code = _xpath_attr(proc, "cda:code/@code")
        code_system_oid = _xpath_attr(proc, "cda:code/@codeSystem")

        # Date can be in effectiveTime/@value or effectiveTime/low/@value
        start_raw = _xpath_attr(proc, "cda:effectiveTime/cda:low/@value")
        if not start_raw:
            start_raw = _xpath_attr(proc, "cda:effectiveTime/@value")
        end_raw = _xpath_attr(proc, "cda:effectiveTime/cda:high/@value")

        procedures.append(CCDProcedure(
            description=description,
            code=code,
            code_system=_resolve_code_system(code_system_oid),
            start_date_parsed=parse_hl7_date(start_raw),
            end_date_parsed=parse_hl7_date(end_raw),
        ))

    return procedures


def parse_encounters(root: etree._Element) -> list[CCDEncounter]:
    """§3.9 Encounters."""
    section = _find_section(root, "46240-8")
    if section is None:
        return []

    encounters = []
    encs = _xpath(section, ".//cda:encounter")

    for enc in encs:
        description = _xpath_attr(enc, "cda:code/@displayName")
        if not description:
            continue

        start_raw = _xpath_attr(enc, "cda:effectiveTime/cda:low/@value")
        end_raw = _xpath_attr(enc, "cda:effectiveTime/cda:high/@value")

        # Provider name
        provider_parts = []
        given = _xpath_text(enc, "cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name/cda:given")
        family = _xpath_text(enc, "cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name/cda:family")
        if given:
            provider_parts.append(given)
        if family:
            provider_parts.append(family)

        encounters.append(CCDEncounter(
            description=description,
            code=_xpath_attr(enc, "cda:code/@code"),
            start_date_parsed=parse_hl7_date(start_raw),
            end_date_parsed=parse_hl7_date(end_raw),
            provider=" ".join(provider_parts) if provider_parts else None,
            location=None,  # Complex to extract; skip for MVP
        ))

    return encounters


def parse_immunizations(root: etree._Element) -> list[CCDImmunization]:
    """§3.10 Immunizations."""
    section = _find_section(root, "11369-6")
    if section is None:
        return []

    immunizations = []
    sub_admins = _xpath(section, ".//cda:substanceAdministration")

    for sa in sub_admins:
        vaccine = _xpath_attr(
            sa, "cda:consumable/cda:manufacturedProduct/cda:manufacturedMaterial/cda:code/@displayName"
        )
        if not vaccine:
            continue

        date_raw = _xpath_attr(sa, "cda:effectiveTime/@value")

        immunizations.append(CCDImmunization(
            vaccine=vaccine,
            code=_xpath_attr(
                sa, "cda:consumable/cda:manufacturedProduct/cda:manufacturedMaterial/cda:code/@code"
            ),
            date_parsed=parse_hl7_date(date_raw),
            status=_xpath_attr(sa, "cda:statusCode/@code"),
        ))

    return immunizations


def parse_social_history(root: etree._Element) -> CCDSocialHistory:
    """§3.11 Social History (smoking status)."""
    section = _find_section(root, "29762-2")
    if section is None:
        return CCDSocialHistory()

    # Look for smoking status observation
    smoking_obs = _xpath(section, ".//cda:observation[cda:code[@code='72166-2']]")
    if not smoking_obs:
        return CCDSocialHistory()

    obs = smoking_obs[0]
    return CCDSocialHistory(
        smoking_status=_xpath_attr(obs, "cda:value/@displayName"),
        smoking_snomed=_xpath_attr(obs, "cda:value/@code"),
        smoking_date=parse_hl7_date(_xpath_attr(obs, "cda:effectiveTime/@value")),
    )


def parse_functional_status(root: etree._Element) -> list[CCDFunctionalStatus]:
    """§3.12 Functional Status (Survey/Screening Scores)."""
    section = _find_section(root, "47420-5")
    if section is None:
        return []

    results = []
    observations = _xpath(section, ".//cda:observation")

    for obs in observations:
        loinc = _xpath_attr(obs, "cda:code/@code")
        display_name = _xpath_attr(obs, "cda:code/@displayName")
        date_raw = _xpath_attr(obs, "cda:effectiveTime/@value")

        # Get value — could be INT, PQ, or other
        value_elements = _xpath(obs, "cda:value")
        score = None
        unit = None
        if value_elements:
            val_el = value_elements[0]
            score = val_el.get("value")
            unit = val_el.get("unit")

        instrument_name = SCREENING_LOINC_TO_NAME.get(loinc, display_name or "Unknown")

        results.append(CCDFunctionalStatus(
            instrument=instrument_name,
            loinc=loinc,
            score=score,
            unit=unit,
            date_parsed=parse_hl7_date(date_raw),
        ))

    return results


def parse_care_plan(root: etree._Element) -> list[CCDCarePlan]:
    """§3.13 Plan of Care."""
    section = _find_section(root, "18776-5")
    if section is None:
        return []

    plans = []
    # Care plan entries can be various types
    # Look in the text table for entries, and in structured entries
    entries = _xpath(section, ".//cda:entry")
    for entry in entries:
        # Try different child element types
        for tag in ["cda:act", "cda:observation", "cda:procedure", "cda:substanceAdministration"]:
            items = _xpath(entry, tag)
            for item in items:
                desc = _xpath_attr(item, "cda:code/@displayName")
                if desc:
                    date_raw = _xpath_attr(item, "cda:effectiveTime/@value")
                    if not date_raw:
                        date_raw = _xpath_attr(item, "cda:effectiveTime/cda:low/@value")

                    plans.append(CCDCarePlan(
                        description=desc,
                        code=_xpath_attr(item, "cda:code/@code"),
                        status=_xpath_attr(item, "cda:statusCode/@code"),
                        date_parsed=parse_hl7_date(date_raw),
                    ))

    # If no structured entries found, parse from text table
    if not plans:
        text_el = _xpath(section, "cda:text")
        if text_el:
            rows = _xpath(section, "cda:text//cda:tbody/cda:tr")
            for row in rows:
                tds = _xpath(row, "cda:td")
                if len(tds) >= 3:
                    desc_el = tds[2]
                    desc = desc_el.text if desc_el.text else None
                    if desc:
                        plans.append(CCDCarePlan(
                            description=desc.strip(),
                            code=None,
                            status=None,
                            date_parsed=None,
                        ))

    return plans


def _dedup_screenings(
    from_labs: list[CCDFunctionalStatus],
    from_functional: list[CCDFunctionalStatus],
) -> list[CCDFunctionalStatus]:
    """Deduplicate screening results by LOINC + date.

    Prefer the functional status version (has individual score).
    """
    seen = set()
    results = []

    # Add functional status entries first (preferred)
    for fs in from_functional:
        key = (fs.loinc, fs.date_parsed)
        if key not in seen:
            seen.add(key)
            results.append(fs)

    # Add lab-derived entries only if not already present
    for fs in from_labs:
        key = (fs.loinc, fs.date_parsed)
        if key not in seen:
            seen.add(key)
            results.append(fs)

    return results


# ---------------------------------------------------------------------------
# Main parser entry point
# ---------------------------------------------------------------------------

def parse_ccda(xml_content: str | bytes | Path) -> CCDIntermediate:
    """Parse a CCD/CCDA XML document into the intermediate schema.

    Args:
        xml_content: XML string, bytes, or path to XML file.

    Returns:
        CCDIntermediate model with all parsed sections.
    """
    if isinstance(xml_content, Path) or (isinstance(xml_content, str) and len(xml_content) < 500 and not xml_content.strip().startswith("<")):
        # Treat as file path
        path = Path(xml_content)
        xml_bytes = path.read_bytes()
    elif isinstance(xml_content, str):
        xml_bytes = xml_content.encode("utf-8")
    else:
        xml_bytes = xml_content

    root = etree.fromstring(xml_bytes)

    # Document date
    doc_date_raw = _xpath_attr(root, "/cda:ClinicalDocument/cda:effectiveTime/@value")

    # Parse all sections
    patient = parse_demographics(root)
    source_org = parse_source_organization(root)
    allergies = parse_allergies(root)
    medications = parse_medications(root)
    conditions = parse_conditions(root)
    lab_results, screenings_from_labs = parse_lab_results(root)
    vitals = parse_vitals(root)
    procedures = parse_procedures(root)
    encounters = parse_encounters(root)
    immunizations = parse_immunizations(root)
    social_history = parse_social_history(root)
    functional_status = parse_functional_status(root)
    care_plans = parse_care_plan(root)

    # Deduplicate screening results (§6 pitfall #6)
    all_screenings = _dedup_screenings(screenings_from_labs, functional_status)

    return CCDIntermediate(
        document_id=uuid4(),
        document_date=parse_hl7_datetime(doc_date_raw),
        source_organization=source_org,
        patient=patient,
        allergies=allergies,
        medications_all=medications,
        conditions_all=conditions,
        lab_results_all=lab_results,
        vitals_all=vitals,
        procedures_all=procedures,
        encounters_all=encounters,
        social_history=social_history,
        immunizations_all=immunizations,
        functional_status_all=all_screenings,
        care_plan_all=care_plans,
    )
