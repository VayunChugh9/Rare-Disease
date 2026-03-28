"""Test script for CCDA parser against the test patient XML.

Verifies all expected data extraction per Chunk 1 pass criteria.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.parsers.ccda_parser import parse_ccda

TEST_XML = project_root / "synthea_sample_data_ccda_latest" / "Bryant814_Bins636_aa4061cf-0f5e-b627-252d-9a705eac4e70.xml"


def test_parser():
    result = parse_ccda(TEST_XML)

    print("=" * 70)
    print("CCDA PARSER TEST — Bryant814 Bins636")
    print("=" * 70)

    # 1. Demographics
    p = result.patient
    print(f"\n--- DEMOGRAPHICS ---")
    print(f"Name: {p.first_name} {p.last_name}")
    print(f"DOB: {p.dob_parsed} (raw: {p.dob_raw})")
    print(f"Sex: {p.sex}")
    print(f"Race: {p.race}")
    print(f"Ethnicity: {p.ethnicity}")
    print(f"Language: {p.language}")
    print(f"MRN: {p.mrn}")
    print(f"Address: {p.address}")
    print(f"Phone: {p.phone}")

    assert p.first_name == "Bryant814", f"Expected Bryant814, got {p.first_name}"
    assert p.last_name == "Bins636", f"Expected Bins636, got {p.last_name}"
    assert p.dob_parsed == "1984-11-12", f"Expected 1984-11-12, got {p.dob_parsed}"
    assert p.sex == "M", f"Expected M, got {p.sex}"
    print("✓ Demographics OK")

    # 2. Source organization
    org = result.source_organization
    print(f"\n--- SOURCE ORG ---")
    print(f"Name: {org.name}")
    print(f"Address: {org.address}")
    assert org.name == "BOSTON HEALTH CARE INC"
    print("✓ Source org OK")

    # 3. Allergies
    print(f"\n--- ALLERGIES ---")
    print(f"No known allergies: {result.allergies.no_known_allergies}")
    print(f"Entries: {len(result.allergies.entries)}")
    assert result.allergies.no_known_allergies is True
    assert len(result.allergies.entries) == 0
    print("✓ Allergies OK (no known allergies)")

    # 4. Medications
    print(f"\n--- MEDICATIONS ({len(result.medications_all)} entries) ---")
    for med in result.medications_all:
        print(f"  {med.name} | code={med.code} | start={med.start_date_parsed} | stop={med.stop_date_parsed} | active={med.is_active}")

    assert len(result.medications_all) == 2, f"Expected 2 medication entries, got {len(result.medications_all)}"
    assert all("Acetaminophen" in m.name for m in result.medications_all)
    print("✓ Medications OK")

    # 5. Conditions
    print(f"\n--- CONDITIONS ({len(result.conditions_all)} entries) ---")
    active_clinical = [c for c in result.conditions_all if c.is_active and c.is_clinical]
    non_clinical = [c for c in result.conditions_all if not c.is_clinical]
    resolved = [c for c in result.conditions_all if not c.is_active and c.is_clinical]

    print(f"  Active clinical: {len(active_clinical)}")
    for c in active_clinical:
        print(f"    - {c.description} (code={c.code}, onset={c.onset_date_parsed})")

    print(f"  Non-clinical: {len(non_clinical)}")
    for c in non_clinical:
        print(f"    - {c.description} (code={c.code})")

    print(f"  Resolved clinical: {len(resolved)}")
    for c in resolved:
        print(f"    - {c.description} (onset={c.onset_date_parsed}, resolved={c.resolution_date_parsed})")

    # Check expected active conditions
    active_names = [c.description for c in active_clinical]
    assert any("Prediabetes" in n for n in active_names), "Missing Prediabetes"
    assert any("Anemia" in n for n in active_names), "Missing Anemia"
    assert any("obesity" in n.lower() for n in active_names), "Missing Obesity"
    assert any("Stress" in n for n in active_names), "Missing Stress"
    assert any("Limited social contact" in n for n in active_names), "Missing Limited social contact"

    # Check non-clinical entries identified
    non_clin_names = [c.description for c in non_clinical]
    assert any("employment" in n.lower() for n in non_clin_names), "Employment not flagged as non-clinical"
    assert any("education" in n.lower() or "higher education" in n.lower() for n in non_clin_names), "Education not flagged as non-clinical"
    assert any("Medication review" in n for n in non_clin_names), "Medication review not flagged as non-clinical"
    print("✓ Conditions OK")

    # 6. Vitals
    print(f"\n--- VITALS ({len(result.vitals_all)} entries) ---")
    # Get most recent vitals (Nov 2024)
    recent_vitals = [v for v in result.vitals_all if v.date_parsed and v.date_parsed.startswith("2024-11")]
    print(f"  Most recent set ({len(recent_vitals)} measures):")
    for v in recent_vitals:
        print(f"    {v.measure}: {v.value} {v.unit} ({v.date_parsed})")

    recent_dict = {v.loinc: v for v in recent_vitals}
    assert "39156-5" in recent_dict, "Missing BMI in recent vitals"
    assert recent_dict["39156-5"].value == "30.13", f"Expected BMI 30.13, got {recent_dict['39156-5'].value}"
    assert "29463-7" in recent_dict, "Missing weight"
    assert recent_dict["29463-7"].value == "102.2", f"Expected weight 102.2, got {recent_dict['29463-7'].value}"
    assert "8867-4" in recent_dict, "Missing heart rate"
    assert recent_dict["8867-4"].value == "95", f"Expected HR 95, got {recent_dict['8867-4'].value}"
    print("✓ Recent vitals OK (BMI 30.13, weight 102.2kg, HR 95)")

    # 7. Lab results
    print(f"\n--- LAB RESULTS ({len(result.lab_results_all)} panels) ---")
    for lab in result.lab_results_all:
        print(f"  {lab.panel_name} ({lab.date_parsed}) — {len(lab.components)} components")

    assert len(result.lab_results_all) > 0, "No lab results found"
    print("✓ Lab results OK")

    # 8. Screening scores (functional status)
    print(f"\n--- SCREENING SCORES ({len(result.functional_status_all)} entries) ---")
    for fs in result.functional_status_all:
        print(f"  {fs.instrument}: {fs.score} ({fs.date_parsed})")

    # Check for specific screenings
    fs_by_instrument = {}
    for fs in result.functional_status_all:
        key = (fs.instrument, fs.date_parsed)
        fs_by_instrument[key] = fs

    # PHQ-2 score of 6 (May 2024)
    phq2_may = [fs for fs in result.functional_status_all if fs.instrument == "PHQ-2" and fs.score == "6"]
    assert len(phq2_may) > 0, "Missing PHQ-2 score of 6"
    print("✓ PHQ-2: 6 found")

    # PHQ-9 score of 18 (May 2024)
    phq9 = [fs for fs in result.functional_status_all if fs.instrument == "PHQ-9" and fs.score == "18"]
    assert len(phq9) > 0, "Missing PHQ-9 score of 18"
    print("✓ PHQ-9: 18 found")

    # GAD-7 score of 1
    gad7 = [fs for fs in result.functional_status_all if fs.instrument == "GAD-7" and fs.score == "1"]
    assert len(gad7) > 0, "Missing GAD-7 score of 1"
    print("✓ GAD-7: 1 found")

    # HARK score of 0
    hark = [fs for fs in result.functional_status_all if fs.instrument == "HARK" and fs.score == "0"]
    assert len(hark) > 0, "Missing HARK score of 0"
    print("✓ HARK: 0 found")

    # AUDIT-C score of 2
    auditc = [fs for fs in result.functional_status_all if fs.instrument == "AUDIT-C" and fs.score == "2"]
    assert len(auditc) > 0, "Missing AUDIT-C score of 2"
    print("✓ AUDIT-C: 2 found")

    # 9. Social history
    print(f"\n--- SOCIAL HISTORY ---")
    sh = result.social_history
    print(f"Smoking: {sh.smoking_status} (code={sh.smoking_snomed}, date={sh.smoking_date})")
    assert "Never smoked" in sh.smoking_status, f"Expected never smoker, got {sh.smoking_status}"
    print("✓ Social history OK (never smoker)")

    # 10. Procedures
    print(f"\n--- PROCEDURES ({len(result.procedures_all)} entries) ---")
    for proc in result.procedures_all[:5]:
        print(f"  {proc.description} ({proc.start_date_parsed})")
    if len(result.procedures_all) > 5:
        print(f"  ... and {len(result.procedures_all) - 5} more")

    # 11. Immunizations
    print(f"\n--- IMMUNIZATIONS ({len(result.immunizations_all)} entries) ---")
    for imm in result.immunizations_all:
        print(f"  {imm.vaccine} ({imm.date_parsed})")

    # 12. Care plans
    print(f"\n--- CARE PLANS ({len(result.care_plan_all)} entries) ---")
    for cp in result.care_plan_all:
        print(f"  {cp.description} ({cp.date_parsed})")

    # 13. Check for violence report in conditions
    violence = [c for c in result.conditions_all if "violence" in c.description.lower()]
    print(f"\n--- SAFETY FLAGS ---")
    print(f"Violence reports: {len(violence)}")
    for v in violence:
        print(f"  {v.description} (onset={v.onset_date_parsed}, resolved={v.resolution_date_parsed})")
    assert len(violence) > 0, "Missing 'Reports of violence in the environment'"
    print("✓ Violence report found")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED")
    print("=" * 70)

    # Print full JSON for inspection
    print("\n\n--- FULL JSON OUTPUT ---")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    test_parser()
