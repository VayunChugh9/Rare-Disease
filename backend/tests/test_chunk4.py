"""Chunk 4 validation: FastAPI backend end-to-end test.

Starts the FastAPI app, uploads the test CCD XML via the API,
polls for completion, and verifies the full pipeline output.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient

from backend.app.database import Base, engine
from backend.app.main import app

TEST_XML = (
    project_root
    / "synthea_sample_data_ccda_latest"
    / "Bryant814_Bins636_aa4061cf-0f5e-b627-252d-9a705eac4e70.xml"
)


def setup():
    """Reset database for clean test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✓ Database reset (SQLite)")


def test_full_pipeline():
    """POST XML → poll status → GET full referral → validate."""
    client = TestClient(app)

    # --- Health check ---
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    print("✓ Health endpoint OK")

    # --- Upload CCD XML with referral context ---
    print("\n  Uploading CCD XML with referral context...")
    xml_bytes = TEST_XML.read_bytes()
    resp = client.post(
        "/api/referrals/upload",
        files={"file": ("Bryant814_test.xml", xml_bytes, "application/xml")},
        data={
            "referral_specialty": "Endocrinology",
            "referral_reason": "Prediabetes management — patient has had prediabetes 20+ years, weight gain, BMI >30, glucose trending up.",
            "referral_urgency": "Routine — schedule within 4-6 weeks",
            "referring_provider_name": "Dr. M. Chen",
            "referring_provider_practice": "Walpole Primary Care",
            "referring_provider_phone": "(508) 555-0198",
        },
    )
    assert resp.status_code == 200, f"Upload failed: {resp.status_code} {resp.text}"
    upload_data = resp.json()
    referral_id = upload_data["referral_id"]
    print(f"✓ Upload accepted, referral_id={referral_id}")

    # --- Poll status ---
    resp = client.get(f"/api/referrals/{referral_id}/status")
    assert resp.status_code == 200
    status_data = resp.json()
    print(f"✓ Status: {status_data['status']}, triage: {status_data['triage_urgency']}")
    assert status_data["status"] == "pending_review", f"Expected pending_review, got {status_data['status']}"

    # --- GET full referral ---
    resp = client.get(f"/api/referrals/{referral_id}")
    assert resp.status_code == 200
    referral = resp.json()
    print(f"✓ Full referral retrieved")

    # --- Validate response structure ---
    print("\n--- VALIDATION CHECKS ---")

    # 1. Has extracted data
    ed = referral["extracted_data"]
    assert ed, "FAIL: No extracted data"
    assert "patient" in ed, "FAIL: No patient in extracted data"
    assert "clinical_data" in ed, "FAIL: No clinical_data in extracted data"
    print("✓ Extracted data present with patient + clinical_data")

    # 2. Patient demographics
    patient = ed["patient"]
    assert patient.get("first_name"), "FAIL: No patient first name"
    assert patient.get("date_of_birth"), "FAIL: No DOB"
    print(f"✓ Patient: {patient['first_name']} {patient.get('last_name')}, DOB: {patient['date_of_birth']}")

    # 3. Summary narrative exists
    assert referral["summary_narrative"], "FAIL: No summary narrative"
    assert len(referral["summary_narrative"]) > 100, "FAIL: Summary narrative too short"
    print(f"✓ Summary narrative ({len(referral['summary_narrative'])} chars)")

    # 4. One-line summary
    assert referral["one_line_summary"], "FAIL: No one-line summary"
    print(f"✓ One-line: {referral['one_line_summary'][:80]}...")

    # 5. Triage
    triage = referral["triage"]
    assert triage["urgency"] in ("routine", "semi_urgent", "semi-urgent", "Routine", "Semi-urgent", "Semi_urgent"), \
        f"FAIL: Unexpected triage urgency: {triage['urgency']}"
    assert triage["confidence"] > 0, "FAIL: No triage confidence"
    assert triage["reasoning"], "FAIL: No triage reasoning"
    print(f"✓ Triage: {triage['urgency']} (confidence={triage['confidence']})")

    # 6. Red flags or action items
    has_flags = len(triage.get("red_flags", [])) > 0
    has_actions = len(triage.get("action_items", [])) > 0
    assert has_flags or has_actions, "FAIL: No red flags or action items"
    print(f"✓ Red flags: {triage.get('red_flags', [])}")
    print(f"✓ Action items: {triage.get('action_items', [])}")

    # 7. Clinical data integrity
    cd = ed.get("clinical_data", {})
    problems = cd.get("problem_list", {})
    active = problems.get("active", [])
    assert len(active) > 0, "FAIL: No active conditions"
    active_names = [c["diagnosis"].lower() for c in active]
    assert any("prediabetes" in d for d in active_names), f"FAIL: No prediabetes. Got: {active_names}"
    print(f"✓ Active conditions ({len(active)}): includes prediabetes")

    # 8. Screenings preserved
    screenings = cd.get("screenings", [])
    assert len(screenings) > 0, "FAIL: No screenings"
    phq9 = [s for s in screenings if s.get("instrument") == "PHQ-9"]
    assert len(phq9) > 0, "FAIL: PHQ-9 not in screenings"
    print(f"✓ Screenings ({len(screenings)}): PHQ-9 present")

    # 9. Referral info persisted
    ref_info = ed.get("referral", {})
    assert ref_info.get("receiving_specialty"), "FAIL: No receiving specialty"
    assert "endocrin" in ref_info["receiving_specialty"].lower(), \
        f"FAIL: Expected endocrinology, got {ref_info['receiving_specialty']}"
    print(f"✓ Referral info: {ref_info['receiving_specialty']} from {ed.get('referring_provider', {}).get('name')}")

    # --- List endpoint ---
    resp = client.get("/api/referrals/")
    assert resp.status_code == 200
    listing = resp.json()
    assert listing["total"] >= 1, "FAIL: No referrals in list"
    print(f"✓ Queue listing: {listing['total']} referral(s)")

    # --- Correction endpoint ---
    resp = client.post(
        f"/api/referrals/{referral_id}/corrections",
        json={
            "field_path": "triage.urgency",
            "original_value": triage["urgency"],
            "corrected_value": "semi_urgent",
            "correction_type": "triage_override",
            "reason": "PHQ-9 of 18 warrants closer attention",
        },
    )
    assert resp.status_code == 200
    print(f"✓ Correction saved: {resp.json()['correction_id']}")

    print("\n✓✓ ALL CHUNK 4 TESTS PASSED ✓✓")


def main():
    print("=" * 70)
    print("CHUNK 4 VALIDATION — FastAPI Backend Pipeline")
    print("=" * 70)
    setup()
    test_full_pipeline()
    print("\n" + "=" * 70)
    print("ALL CHUNK 4 TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
