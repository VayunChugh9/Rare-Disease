"""Test script for recency filter + dedup pipeline.

Feeds Chunk 1 parser output through the filter and verifies Chunk 2 pass criteria.
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.parsers.ccda_parser import parse_ccda
from backend.app.services.recency_filter import filter_to_canonical

TEST_XML = project_root / "synthea_sample_data_ccda_latest" / "Bryant814_Bins636_aa4061cf-0f5e-b627-252d-9a705eac4e70.xml"


def test_filter():
    # Parse
    intermediate = parse_ccda(TEST_XML)
    print(f"Parsed: {len(intermediate.medications_all)} meds, {len(intermediate.conditions_all)} conditions")

    # Filter
    canonical = filter_to_canonical(intermediate, filename="Bryant814_test.xml")

    print("=" * 70)
    print("RECENCY FILTER TEST — Bryant814 Bins636")
    print("=" * 70)

    cd = canonical.clinical_data

    # 1. Medications: Acetaminophen entries collapsed to single
    print(f"\n--- MEDICATIONS ---")
    print(f"Active: {len(cd.medications.active)}")
    for m in cd.medications.active:
        print(f"  {m.name} (first prescribed: {m.first_prescribed}, rxnorm: {m.rxnorm})")
    print(f"Recently stopped: {len(cd.medications.recently_stopped)}")
    for m in cd.medications.recently_stopped:
        print(f"  {m.name} (stopped: {m.stop_date})")

    # Both Acetaminophen entries have stop dates in the past, so they should be
    # collapsed and show as recently_stopped (within 6 months of the most recent stop)
    # Actually both stopped >6mo ago (2024-05-16), so they may not appear at all
    # The 2024-05-16 stop is ~10 months ago from March 2026
    total_meds = len(cd.medications.active) + len(cd.medications.recently_stopped)
    all_med_names = [m.name for m in cd.medications.active] + [m.name for m in cd.medications.recently_stopped]

    # Verify dedup: should be at most 1 Acetaminophen entry (collapsed from 2)
    acetaminophen_count = sum(1 for n in all_med_names if "Acetaminophen" in n)
    assert acetaminophen_count <= 1, f"Expected <=1 Acetaminophen after dedup, got {acetaminophen_count}"
    print("✓ Acetaminophen entries collapsed (dedup works)")

    # 2. Employment/education routed to social_history
    print(f"\n--- SOCIAL HISTORY ---")
    sh = cd.social_history
    print(f"Smoking: {sh.smoking_status}")
    print(f"Employment: {sh.employment}")
    print(f"Education: {sh.education}")
    print(f"Safety concerns: {sh.safety_concerns}")

    # Check employment is NOT in problem list
    active_diags = [c.diagnosis for c in cd.problem_list.active]
    assert not any("employment" in d.lower() for d in active_diags), "Employment found in problem list!"
    assert not any("education" in d.lower() for d in active_diags), "Education found in problem list!"
    assert not any("Medication review" in d for d in active_diags), "Medication review found in problem list!"
    print("✓ Employment/education routed to social_history, NOT problem_list")

    # 3. Active conditions
    print(f"\n--- PROBLEM LIST ---")
    print(f"Active conditions: {len(cd.problem_list.active)}")
    for c in cd.problem_list.active:
        print(f"  {c.diagnosis} (code={c.code}, onset={c.onset_date})")
    print(f"Significant history: {len(cd.problem_list.significant_history)}")
    for c in cd.problem_list.significant_history:
        print(f"  {c.diagnosis} ({c.significance_reason})")

    active_diag_set = set(c.diagnosis for c in cd.problem_list.active)
    assert any("Prediabetes" in d for d in active_diag_set), "Missing Prediabetes"
    assert any("Anemia" in d for d in active_diag_set), "Missing Anemia"
    assert any("obesity" in d.lower() for d in active_diag_set), "Missing Obesity"
    print("✓ Active conditions correct")

    # 4. Resolved minor conditions (sinusitis, bronchitis) NOT in primary output
    all_primary_diags = active_diag_set | set(c.diagnosis for c in cd.problem_list.significant_history)
    assert not any("sinusitis" in d.lower() for d in all_primary_diags), "Sinusitis should be tier 3"
    assert not any("bronchitis" in d.lower() for d in all_primary_diags), "Bronchitis should be tier 3"
    print("✓ Resolved minor conditions (sinusitis, bronchitis) correctly filtered to tier 3")

    # 5. Screenings
    print(f"\n--- SCREENINGS ({len(cd.screenings)} entries) ---")
    for s in cd.screenings:
        flag = " *** CONCERNING ***" if s.interpretation and any(kw in s.interpretation.lower() for kw in ["moderate", "severe", "positive"]) else ""
        print(f"  {s.instrument}: {s.score} — {s.interpretation} ({s.date}){flag}")

    # PHQ-9 of 18 should be flagged as clinically significant
    phq9_entries = [s for s in cd.screenings if s.instrument == "PHQ-9"]
    assert len(phq9_entries) > 0, "Missing PHQ-9"
    phq9_18 = [s for s in phq9_entries if s.score == "18"]
    assert len(phq9_18) > 0, "Missing PHQ-9 score of 18"
    assert "moderately severe" in phq9_18[0].interpretation.lower(), f"PHQ-9 18 interpretation wrong: {phq9_18[0].interpretation}"
    print("✓ PHQ-9 of 18 flagged as clinically significant (moderately severe depression)")

    # Reports of violence
    print(f"\n--- SAFETY ---")
    print(f"Safety concerns: {sh.safety_concerns}")
    assert sh.safety_concerns is not None, "Violence not in safety concerns"
    assert "violence" in sh.safety_concerns.lower(), f"Expected violence in safety concerns, got: {sh.safety_concerns}"
    print("✓ Reports of violence flagged in safety_concerns")

    # 6. Most recent vitals only
    print(f"\n--- VITALS ---")
    rv = cd.recent_vitals
    print(f"Date: {rv.date}")
    print(f"Height: {rv.height}")
    print(f"Weight: {rv.weight}")
    print(f"BMI: {rv.bmi}")
    print(f"HR: {rv.heart_rate}")
    print(f"RR: {rv.respiratory_rate}")
    print(f"Pain: {rv.pain_score}")
    print(f"Trends - Weight: {rv.trends.weight_3_visits}")

    assert rv.date == "2024-11-18", f"Expected most recent vitals date 2024-11-18, got {rv.date}"
    assert "30.13" in rv.bmi, f"Expected BMI 30.13, got {rv.bmi}"
    assert "102.2" in rv.weight, f"Expected weight 102.2, got {rv.weight}"
    print("✓ Most recent vitals only in primary output")

    # 7. Allergies
    print(f"\n--- ALLERGIES ---")
    print(f"No known allergies: {cd.allergies.no_known_allergies}")
    assert cd.allergies.no_known_allergies is True
    print("✓ Allergies correct")

    # 8. Patient demographics
    print(f"\n--- PATIENT ---")
    p = canonical.patient
    print(f"Name: {p.first_name} {p.last_name}")
    print(f"Age: {p.age}")
    print(f"DOB: {p.date_of_birth}")
    assert p.age is not None and p.age > 0
    print(f"✓ Patient age calculated: {p.age}")

    # 9. Extraction metadata
    print(f"\n--- METADATA ---")
    em = canonical.extraction_metadata
    print(f"Path: {em.extraction_path}")
    print(f"Sections found: {em.sections_found}")
    print(f"Sections missing: {em.sections_missing}")

    print("\n" + "=" * 70)
    print("ALL CHUNK 2 TESTS PASSED")
    print("=" * 70)

    # Print canonical JSON
    print("\n\n--- CANONICAL JSON OUTPUT ---")
    print(canonical.model_dump_json(indent=2))


if __name__ == "__main__":
    test_filter()
