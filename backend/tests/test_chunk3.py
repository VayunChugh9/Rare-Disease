"""Chunk 3 validation script for LLM summarization and extraction.

Runs all Chunk 3 pass criteria against the test patient data.
Requires a valid OPENAI_API_KEY in .env.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


TEST_XML = project_root / "synthea_sample_data_ccda_latest" / "Bryant814_Bins636_aa4061cf-0f5e-b627-252d-9a705eac4e70.xml"
TEST_TXT = project_root / "Bryant814_Bins636_referral_realistic.txt"


def test_openai_connectivity():
    """Verify OpenAI API key loads and authenticates."""
    print("\n" + "=" * 70)
    print("TEST: OpenAI Connectivity")
    print("=" * 70)

    from backend.app.services.openai_client import get_client

    client = get_client()
    # Minimal API call to verify connectivity
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=10,
        messages=[{"role": "user", "content": "Say OK"}],
    )
    result = response.choices[0].message.content
    assert result is not None and len(result) > 0, "Empty response from OpenAI"
    print(f"✓ OpenAI connectivity verified (response: {result.strip()[:20]})")


def test_summarization():
    """Test summarization pipeline: parse → filter → summarize."""
    print("\n" + "=" * 70)
    print("TEST: Summarization Pipeline (Chunk 3)")
    print("=" * 70)

    from backend.app.parsers.ccda_parser import parse_ccda
    from backend.app.services.recency_filter import filter_to_canonical
    from backend.app.services.llm_summarization import summarize_and_triage
    from backend.app.models.schemas import (
        SummaryOutput, ReferralInfo, ReferringProvider,
    )

    # Step 1: Parse and filter (reuses Chunk 1+2)
    intermediate = parse_ccda(TEST_XML)
    canonical = filter_to_canonical(intermediate, filename="Bryant814_test.xml")
    print("✓ Canonical JSON produced from Chunk 1+2 pipeline")

    # Step 1b: Inject referral context (simulates real workflow where
    # the referral letter provides context the CCD XML does not contain)
    canonical.referral = ReferralInfo(
        receiving_specialty="Endocrinology",
        reason="Prediabetes management — patient has had prediabetes 20+ years, weight gain, BMI >30, glucose trending up. Requesting A1c and metabolic workup.",
        clinical_question="Would like A1c and metabolic workup for prediabetes with worsening metabolic trajectory",
        urgency_stated="Routine — schedule within 4-6 weeks",
        date_of_referral="2026-03-08",
    )
    canonical.referring_provider = ReferringProvider(
        name="Dr. M. Chen",
        practice_name="Walpole Primary Care",
        phone="(508) 555-0198",
    )
    print("✓ Referral context injected (endocrinology referral from Dr. Chen)")

    # Step 2: Summarize
    print("  Calling OpenAI for summarization...")
    summary = summarize_and_triage(canonical)
    assert isinstance(summary, SummaryOutput), "Output is not SummaryOutput"
    print("✓ SummaryOutput returned and validated against schema 6")

    # Step 3: Print output for inspection
    print(f"\n--- ONE-LINE SUMMARY ---")
    print(f"  {summary.one_line_summary}")

    print(f"\n--- NARRATIVE ---")
    print(f"  {summary.summary_narrative[:500]}...")

    print(f"\n--- TRIAGE ---")
    tr = summary.triage_recommendation
    if tr:
        print(f"  Urgency: {tr.urgency}")
        print(f"  Confidence: {tr.confidence}")
        print(f"  Reasoning: {tr.reasoning}")
        print(f"  Red flags: {tr.red_flags}")
        print(f"  Action items: {tr.action_items}")

    print(f"\n--- MISSING INFO ---")
    for mi in summary.missing_information:
        print(f"  - {mi}")

    print(f"\n--- SCREENING INTERPRETATIONS ---")
    for si in summary.screening_interpretations:
        print(f"  {si.instrument}: {si.score} → {si.interpretation} ({si.clinical_significance})")

    # Step 4: Validation checks
    print("\n--- VALIDATION CHECKS ---")

    # Check 1: Narrative mentions prediabetes
    narrative = (summary.summary_narrative or "").lower()
    assert "prediabetes" in narrative, "FAIL: Narrative should mention prediabetes"
    print("✓ Narrative mentions prediabetes")

    # Check 2: Narrative mentions obesity
    assert "obes" in narrative, "FAIL: Narrative should mention obesity"
    print("✓ Narrative mentions obesity")

    # Check 3: Narrative mentions metabolic trajectory / metabolic context
    metabolic_mentioned = any(
        term in narrative
        for term in ["metabolic", "weight gain", "bmi", "glucose", "trending"]
    )
    assert metabolic_mentioned, "FAIL: Narrative should mention metabolic trajectory or indicators"
    print("✓ Narrative mentions metabolic trajectory/indicators")

    # Check 4: PHQ-9 of 18 surfaced as significant
    full_text = narrative + " " + json.dumps(
        [si.model_dump() for si in summary.screening_interpretations]
    ).lower()
    phq9_found = "phq-9" in full_text or "phq9" in full_text
    assert phq9_found, "FAIL: PHQ-9 should be surfaced"
    print("✓ PHQ-9 score surfaced (significant even for endocrine referral)")

    # Check 5: Violence flag mentioned (in narrative, red_flags, action_items, or screening interpretations)
    violence_parts = [narrative, full_text]
    if tr and tr.red_flags:
        violence_parts.append(" ".join(tr.red_flags).lower())
    if tr and tr.action_items:
        violence_parts.append(" ".join(tr.action_items).lower())
    violence_text = " ".join(violence_parts)
    violence_found = any(
        term in violence_text
        for term in ["violence", "safety", "hark", "intimate partner", "ipv", "abuse"]
    )
    assert violence_found, (
        f"FAIL: Violence/safety flag should be mentioned somewhere in output. "
        f"Red flags: {tr.red_flags if tr else 'N/A'}, "
        f"Screening instruments: {[si.instrument for si in summary.screening_interpretations]}"
    )
    print("✓ Violence/safety flag mentioned")

    # Check 6: Triage is routine or semi-urgent
    # With full clinical picture (PHQ-9: 18, violence flag), the LLM may
    # appropriately triage UP per the prompt rule "When in doubt, triage UP."
    # Both are clinically valid given the data.
    assert tr is not None, "FAIL: No triage recommendation"
    valid_triage = tr.urgency.lower() in ("routine", "semi-urgent", "semi_urgent")
    assert valid_triage, f"FAIL: Expected routine or semi-urgent triage, got {tr.urgency}"
    print(f"✓ Triage is {tr.urgency} (clinically appropriate)")

    # Check 7: Missing info includes key labs
    missing_lower = " ".join(summary.missing_information).lower()
    a1c_missing = "a1c" in missing_lower or "hemoglobin a1c" in missing_lower
    assert a1c_missing, f"FAIL: Missing info should mention A1c. Got: {summary.missing_information}"
    print("✓ Missing info includes A1c")

    # Check for fasting insulin or lipid panel
    insulin_or_lipid = "insulin" in missing_lower or "lipid" in missing_lower
    if insulin_or_lipid:
        print("✓ Missing info includes fasting insulin or lipid panel")
    else:
        print("⚠ Missing info does not explicitly mention fasting insulin or lipid panel (may be OK)")

    print("\n✓✓ ALL SUMMARIZATION TESTS PASSED ✓✓")
    return summary


def test_extraction():
    """Test extraction pipeline on realistic referral text."""
    print("\n" + "=" * 70)
    print("TEST: Extraction Pipeline (Chunk 3)")
    print("=" * 70)

    from backend.app.services.llm_extraction import clean_text, extract_structured
    from backend.app.models.schemas import CanonicalReferral

    # Read test document
    raw_text = TEST_TXT.read_text()
    print(f"Raw referral text ({len(raw_text)} chars):")
    print(f"  {raw_text[:200]}...")

    # Step 1: Clean text
    print("\n  Calling OpenAI for text cleaning...")
    cleaned = clean_text(raw_text)
    print(f"✓ Text cleaned ({len(cleaned)} chars)")
    print(f"  Cleaned output preview:\n  {cleaned[:300]}...")

    # Step 2: Extract structured data
    print("\n  Calling OpenAI for structured extraction...")
    canonical = extract_structured(cleaned, source_filename="Bryant814_Bins636_referral_realistic.txt")
    assert isinstance(canonical, CanonicalReferral), "Output is not CanonicalReferral"
    print("✓ CanonicalReferral returned and validated")

    # Step 3: Print key fields
    print(f"\n--- EXTRACTED DATA ---")
    p = canonical.patient
    if p:
        print(f"  Patient: {p.first_name} {p.last_name}, DOB: {p.date_of_birth}")

    rp = canonical.referring_provider
    if rp:
        print(f"  Referring: {rp.name} at {rp.practice_name}, phone: {rp.phone}")

    ref = canonical.referral
    if ref:
        print(f"  Specialty: {ref.receiving_specialty}")
        print(f"  Reason: {ref.reason}")
        print(f"  Urgency stated: {ref.urgency_stated}")

    cd = canonical.clinical_data
    if cd:
        if cd.problem_list:
            print(f"  Active conditions: {[c.diagnosis for c in cd.problem_list.active]}")
        if cd.medications:
            print(f"  Active meds: {[m.name for m in cd.medications.active]}")
        if cd.allergies:
            print(f"  NKDA: {cd.allergies.no_known_allergies}")
        if cd.social_history:
            print(f"  Smoking: {cd.social_history.smoking_status}")
        if cd.recent_vitals:
            print(f"  Vitals: wt={cd.recent_vitals.weight}, BMI={cd.recent_vitals.bmi}, HR={cd.recent_vitals.heart_rate}")

    t = canonical.triage
    if t:
        print(f"  Triage: {t.urgency} (confidence={t.confidence})")
        print(f"  Missing info: {t.missing_critical_info}")

    # Step 4: Validation checks
    print("\n--- VALIDATION CHECKS ---")

    # Check abbreviation handling
    # The original text has: w/, NKDA, Hx, PRN
    # After extraction, these should be handled correctly

    # NKDA → no known drug allergies
    if cd and cd.allergies:
        assert cd.allergies.no_known_allergies is True, \
            "FAIL: NKDA should be recognized as no known allergies"
        print("✓ NKDA handled correctly (no known allergies = True)")

    # Check referral to endocrinology
    if ref:
        assert ref.receiving_specialty is not None, "FAIL: Receiving specialty should be extracted"
        assert "endocrin" in ref.receiving_specialty.lower(), \
            f"FAIL: Expected endocrinology, got {ref.receiving_specialty}"
        print("✓ Referral to Endocrinology extracted")

    # Check prediabetes in conditions
    if cd and cd.problem_list:
        active_diags = [c.diagnosis.lower() for c in cd.problem_list.active]
        prediabetes_found = any("prediabetes" in d or "pre-diabetes" in d for d in active_diags)
        assert prediabetes_found, f"FAIL: Prediabetes should be in active conditions. Got: {active_diags}"
        print("✓ Prediabetes extracted as active condition")

    # Check Tylenol/Acetaminophen
    if cd and cd.medications:
        all_meds = [m.name.lower() for m in cd.medications.active]
        med_found = any("tylenol" in m or "acetaminophen" in m for m in all_meds)
        assert med_found, f"FAIL: Tylenol/Acetaminophen should be extracted. Got: {all_meds}"
        print("✓ Tylenol/Acetaminophen extracted (PRN handled)")

    # Check referring provider
    if rp:
        assert rp.name is not None and "chen" in rp.name.lower(), \
            f"FAIL: Referring provider should be Dr. Chen. Got: {rp.name}"
        print("✓ Dr. Chen extracted as referring provider")

    # Check never smoker
    if cd and cd.social_history:
        assert cd.social_history.smoking_status is not None, "FAIL: Smoking status should be extracted"
        assert "never" in cd.social_history.smoking_status.lower(), \
            f"FAIL: Should be never smoker. Got: {cd.social_history.smoking_status}"
        print("✓ Never smoker extracted from social history")

    # Hx abbreviation: "Hx anemia" should extract anemia
    if cd and cd.problem_list:
        all_diags = [c.diagnosis.lower() for c in cd.problem_list.active]
        all_hist = [h.diagnosis.lower() for h in cd.problem_list.significant_history] if cd.problem_list.significant_history else []
        all_conditions = all_diags + all_hist
        anemia_found = any("anemia" in d for d in all_conditions)
        assert anemia_found, f"FAIL: Hx anemia should be extracted. Got: {all_conditions}"
        print("✓ 'Hx anemia' abbreviation handled — anemia extracted")

    print("\n✓✓ ALL EXTRACTION TESTS PASSED ✓✓")
    return canonical


def main():
    """Run all Chunk 3 tests."""
    print("=" * 70)
    print("CHUNK 3 VALIDATION — LLM Summarization + Extraction")
    print("=" * 70)

    # Test 1: OpenAI connectivity
    test_openai_connectivity()

    # Test 2: Summarization
    summary = test_summarization()

    # Test 3: Extraction
    extracted = test_extraction()

    print("\n" + "=" * 70)
    print("ALL CHUNK 3 TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
