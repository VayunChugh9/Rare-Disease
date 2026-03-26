"""Recency filter that transforms CCD intermediate schema into canonical schema.

Applies time windows, tier classification, deduplication, and non-clinical routing
per the config in schema 3 (3_recency_filter_config).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional
from uuid import uuid4

from backend.app.models.schemas import (
    ActiveCondition,
    ActiveMedication,
    Allergies,
    CanonicalPatient,
    CanonicalReferral,
    ClinicalData,
    DocumentFormat,
    ExtractionMetadata,
    ExtractionPath,
    KnownAllergy,
    LabPanel,
    LabTestResult,
    Medications,
    PatientAddress,
    PatientContact,
    ProblemList,
    ProcedureEntry,
    RecentlyStoppedMedication,
    RecentVitals,
    Screening,
    ScreeningType,
    SignificantHistory,
    SocialHistory,
    SourceDocument,
    VitalTrends,
    CCDIntermediate,
    CCDCondition,
    CCDMedication,
    CCDVital,
)
from backend.app.services.deduplicator import (
    dedup_conditions,
    dedup_labs,
    dedup_medications,
    get_most_recent_vitals_set,
    get_vital_trends,
)

# ---------------------------------------------------------------------------
# Configuration (from schema 3)
# ---------------------------------------------------------------------------

LABS_RECENT_MONTHS = 12
ENCOUNTERS_RECENT_MONTHS = 6
MEDS_RECENTLY_STOPPED_MONTHS = 6
VITALS_MOST_RECENT_SETS = 1
VITALS_TREND_SETS = 3

# Tier 2: Always-surface keywords (serious conditions)
TIER_2_KEYWORDS = [
    "cancer", "malignant", "carcinoma", "tumor", "metast", "neoplasm",
    "lymphoma", "leukemia", "melanoma",
    "stroke", "CVA", "TIA", "cerebrovascular",
    "myocardial infarction", "MI", "STEMI", "NSTEMI", "heart attack",
    "transplant",
    "HIV", "AIDS",
    "hepatitis B", "hepatitis C", "HBV", "HCV",
    "seizure", "epilepsy",
    "anaphylaxis",
    "pulmonary embolism", "PE", "DVT", "deep vein thrombosis",
    "suicide", "self-harm", "overdose",
    "fracture", "amputation",
]

# Tier 2: Always-surface medication classes
TIER_2_MED_KEYWORDS = [
    "chemotherapy", "antineoplastic",
    "anticoagulant", "warfarin", "heparin", "apixaban", "rivaroxaban",
    "immunosuppressant", "tacrolimus", "cyclosporine", "mycophenolate",
    "opioid", "morphine", "oxycodone", "fentanyl", "hydrocodone", "methadone", "buprenorphine",
    "insulin",
    "antipsychotic", "lithium", "clozapine",
    "biologic", "adalimumab", "infliximab", "rituximab",
]

# Tier 2: Screening thresholds
SCREENING_THRESHOLDS = {
    "GAD-7": {"concerning_score": 10, "label": "moderate or higher anxiety"},
    "PHQ-2": {"concerning_score": 3, "label": "positive depression screen"},
    "PHQ-9": {"concerning_score": 10, "label": "moderate or higher depression"},
    "AUDIT-C": {"concerning_score_male": 4, "concerning_score_female": 3, "label": "positive alcohol screen"},
    "DAST-10": {"concerning_score": 3, "label": "moderate or higher drug problems"},
    "HARK": {"concerning_score": 1, "label": "positive IPV screen"},
}

# Screening interpretation tables
SCREENING_INTERPRETATIONS = {
    "GAD-7": [(0, 4, "Minimal anxiety"), (5, 9, "Mild anxiety"), (10, 14, "Moderate anxiety"), (15, 21, "Severe anxiety")],
    "PHQ-2": [(0, 2, "Negative screen"), (3, 6, "Positive (warrants full PHQ-9)")],
    "PHQ-9": [(0, 4, "Minimal depression"), (5, 9, "Mild depression"), (10, 14, "Moderate depression"), (15, 19, "Moderately severe depression"), (20, 27, "Severe depression")],
    "AUDIT-C": [(0, 3, "Negative screen"), (4, 12, "Positive for unhealthy alcohol use")],
    "DAST-10": [(0, 0, "No problems reported"), (1, 2, "Low level"), (3, 5, "Moderate level"), (6, 8, "Substantial level"), (9, 10, "Severe level")],
    "HARK": [(0, 0, "Negative screen"), (1, 4, "Positive for intimate partner violence")],
}

# Non-clinical condition codes to route to social_history
EMPLOYMENT_CODES = {"160903007", "160904001", "741062008"}
EDUCATION_CODES = {"473461003", "224299000", "224298008"}

# Surgical heuristic keywords
SURGICAL_KEYWORDS = [
    "surgery", "repair", "replacement", "excision", "removal", "implant",
    "biopsy", "graft", "-ectomy", "-otomy", "-plasty", "-oscopy",
]
NON_SURGICAL_KEYWORDS = [
    "assessment", "screening", "evaluation", "counseling", "education",
    "reconciliation", "measurement",
]

# Screening type mapping by instrument name
SCREENING_TYPE_MAP = {
    "GAD-7": ScreeningType.MENTAL_HEALTH,
    "PHQ-2": ScreeningType.MENTAL_HEALTH,
    "PHQ-9": ScreeningType.MENTAL_HEALTH,
    "AUDIT-C": ScreeningType.SUBSTANCE_USE,
    "DAST-10": ScreeningType.SUBSTANCE_USE,
    "HARK": ScreeningType.SAFETY,
}


def _months_ago(months: int) -> str:
    """Return ISO date string for N months ago from today."""
    d = date.today() - timedelta(days=months * 30)
    return d.isoformat()


def _is_tier2_condition(cond: CCDCondition) -> bool:
    """Check if condition matches tier 2 always-surface keywords."""
    desc_lower = cond.description.lower()
    return any(kw.lower() in desc_lower for kw in TIER_2_KEYWORDS)


def _is_tier2_medication(med: CCDMedication) -> bool:
    """Check if medication matches tier 2 always-surface classes."""
    name_lower = med.name.lower()
    return any(kw.lower() in name_lower for kw in TIER_2_MED_KEYWORDS)


def _is_surgical(description: str) -> bool:
    """Classify procedure as surgical vs assessment."""
    desc_lower = description.lower()
    if any(kw in desc_lower for kw in NON_SURGICAL_KEYWORDS):
        return False
    if any(kw in desc_lower for kw in SURGICAL_KEYWORDS):
        return True
    return False


def _interpret_screening(instrument: str, score_str: str) -> Optional[str]:
    """Get interpretation for a screening score."""
    try:
        score = int(float(score_str))
    except (ValueError, TypeError):
        return None

    ranges = SCREENING_INTERPRETATIONS.get(instrument)
    if not ranges:
        return None

    for low, high, label in ranges:
        if low <= score <= high:
            return label
    return None


def _is_screening_concerning(instrument: str, score_str: str) -> bool:
    """Check if screening score exceeds concerning threshold."""
    try:
        score = int(float(score_str))
    except (ValueError, TypeError):
        return False

    threshold = SCREENING_THRESHOLDS.get(instrument)
    if not threshold:
        return False

    concerning = threshold.get("concerning_score")
    if concerning is not None:
        return score >= concerning

    # AUDIT-C has gender-specific thresholds; use male (more conservative) as default
    male_threshold = threshold.get("concerning_score_male")
    if male_threshold is not None:
        return score >= male_threshold

    return False


def _calculate_age(dob: Optional[str]) -> Optional[int]:
    """Calculate age from DOB string."""
    if not dob:
        return None
    try:
        birth = date.fromisoformat(dob)
        today = date.today()
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    except ValueError:
        return None


def _extract_social_from_conditions(conditions: list[CCDCondition]) -> dict[str, Optional[str]]:
    """Extract employment and education from non-clinical conditions."""
    employment = None
    education = None

    for cond in conditions:
        if not cond.is_clinical and cond.code:
            if cond.code in EMPLOYMENT_CODES:
                if cond.is_active:
                    employment = cond.description
            elif cond.code in EDUCATION_CODES:
                education = cond.description

    return {"employment": employment, "education": education}


def _extract_safety_concerns(conditions: list[CCDCondition]) -> Optional[str]:
    """Extract safety-related conditions."""
    safety = []
    for cond in conditions:
        desc_lower = cond.description.lower()
        if any(kw in desc_lower for kw in ["violence", "abuse", "neglect", "self-harm", "suicide"]):
            safety.append(cond.description)
    return "; ".join(safety) if safety else None


# ---------------------------------------------------------------------------
# Main filter
# ---------------------------------------------------------------------------

def filter_to_canonical(
    intermediate: CCDIntermediate,
    filename: Optional[str] = None,
) -> CanonicalReferral:
    """Transform CCD intermediate data into the canonical referral schema.

    Applies:
    - Deduplication (medications, conditions, labs)
    - Time windowing (labs, encounters, vitals)
    - Tier classification (active/significant/archived)
    - Non-clinical routing (employment/education → social_history)
    - Screening interpretation and flagging
    """
    now_str = datetime.utcnow().isoformat() + "Z"
    cutoff_labs = _months_ago(LABS_RECENT_MONTHS)
    cutoff_meds = _months_ago(MEDS_RECENTLY_STOPPED_MONTHS)

    # --- Patient ---
    patient = None
    if intermediate.patient:
        p = intermediate.patient
        patient = CanonicalPatient(
            first_name=p.first_name,
            last_name=p.last_name,
            date_of_birth=p.dob_parsed,
            age=_calculate_age(p.dob_parsed),
            sex=p.sex,
            race=p.race,
            ethnicity=p.ethnicity,
            language=p.language,
            mrn=p.mrn,
            contact=PatientContact(
                phone=p.phone,
                address=PatientAddress(
                    street=p.address.street if p.address else None,
                    city=p.address.city if p.address else None,
                    state=p.address.state if p.address else None,
                    zip=p.address.zip if p.address else None,
                ) if p.address else None,
            ),
        )

    # --- Medications (dedup then classify) ---
    deduped_meds = dedup_medications(intermediate.medications_all)

    active_meds = []
    recently_stopped_meds = []

    for med in deduped_meds:
        if med.is_active or _is_tier2_medication(med):
            active_meds.append(ActiveMedication(
                name=med.name,
                dose=None,  # Synthea doesn't include dose in structured data
                frequency=None,
                rxnorm=med.code if med.code_system == "RxNorm" else None,
                first_prescribed=med.start_date_parsed,
                source="CCD",
            ))
        elif med.stop_date_parsed and med.stop_date_parsed >= cutoff_meds:
            recently_stopped_meds.append(RecentlyStoppedMedication(
                name=med.name,
                rxnorm=med.code if med.code_system == "RxNorm" else None,
                stop_date=med.stop_date_parsed,
            ))

    # --- Conditions (dedup, classify, route non-clinical) ---
    clinical_conditions = [c for c in intermediate.conditions_all if c.is_clinical]
    non_clinical_conditions = [c for c in intermediate.conditions_all if not c.is_clinical]

    deduped_clinical = dedup_conditions(clinical_conditions)

    active_conditions = []
    significant_history = []

    for cond in deduped_clinical:
        if cond.is_active:
            active_conditions.append(ActiveCondition(
                diagnosis=cond.description,
                code=cond.code,
                code_system=cond.code_system,
                onset_date=cond.onset_date_parsed,
            ))
        elif _is_tier2_condition(cond):
            # Tier 2: always surface significant resolved conditions
            significant_history.append(SignificantHistory(
                diagnosis=cond.description,
                code=cond.code,
                code_system=cond.code_system,
                onset_date=cond.onset_date_parsed,
                resolution_date=cond.resolution_date_parsed,
                significance_reason="Clinically significant condition (always surfaced)",
            ))
        # Tier 3: resolved minor conditions — not included

    # Route non-clinical to social history
    social_from_conditions = _extract_social_from_conditions(non_clinical_conditions)
    safety_concerns = _extract_safety_concerns(intermediate.conditions_all)

    # --- Allergies ---
    allergies = Allergies(no_known_allergies=True)
    if intermediate.allergies:
        if intermediate.allergies.entries:
            allergies = Allergies(
                known_allergies=[
                    KnownAllergy(
                        substance=a.substance,
                        reaction=a.reaction,
                        severity=a.severity,
                    )
                    for a in intermediate.allergies.entries
                ],
                no_known_allergies=False,
            )
        else:
            allergies = Allergies(
                no_known_allergies=intermediate.allergies.no_known_allergies,
            )

    # --- Labs (dedup, filter by recency) ---
    recent_labs_raw = [
        lab for lab in intermediate.lab_results_all
        if lab.date_parsed and lab.date_parsed >= cutoff_labs
    ]
    deduped_labs = dedup_labs(recent_labs_raw)

    recent_labs = []
    for lab in deduped_labs:
        results = []
        prior_map = getattr(lab, "_prior_values", {})

        for comp in lab.components:
            prior_val, prior_date = prior_map.get(comp.loinc, (None, None)) if prior_map else (None, None)
            results.append(LabTestResult(
                test_name=comp.test_name,
                loinc=comp.loinc,
                value=comp.value,
                unit=comp.unit,
                prior_value=prior_val,
                prior_date=prior_date,
            ))

        recent_labs.append(LabPanel(
            panel_name=lab.panel_name,
            panel_loinc=lab.panel_loinc,
            date=lab.date_parsed,
            results=results,
        ))

    # --- Vitals (most recent + trends) ---
    most_recent_vitals = get_most_recent_vitals_set(intermediate.vitals_all, VITALS_MOST_RECENT_SETS)
    trends = get_vital_trends(intermediate.vitals_all, VITALS_TREND_SETS)

    recent_vitals = None
    if most_recent_vitals:
        vitals_by_loinc = {v.loinc: v for v in most_recent_vitals}
        vitals_date = most_recent_vitals[0].date_parsed if most_recent_vitals else None

        # Build BP from systolic + diastolic
        sys_bp = vitals_by_loinc.get("8480-6")
        dia_bp = vitals_by_loinc.get("8462-4")
        bp_str = None
        if sys_bp and dia_bp:
            bp_str = f"{sys_bp.value}/{dia_bp.value}"

        recent_vitals = RecentVitals(
            date=vitals_date,
            height=_vital_str(vitals_by_loinc.get("8302-2")),
            weight=_vital_str(vitals_by_loinc.get("29463-7")),
            bmi=_vital_str(vitals_by_loinc.get("39156-5")),
            heart_rate=_vital_str(vitals_by_loinc.get("8867-4")),
            respiratory_rate=_vital_str(vitals_by_loinc.get("9279-1")),
            blood_pressure=bp_str,
            temperature=_vital_str(vitals_by_loinc.get("8310-5")),
            pain_score=_vital_str(vitals_by_loinc.get("72514-3")),
            oxygen_saturation=_vital_str(vitals_by_loinc.get("2708-6")),
            trends=VitalTrends(
                weight_3_visits=trends.get("weight", []),
                bp_3_visits=trends.get("bp", []),
                a1c_3_visits=trends.get("a1c", []),
            ),
        )

    # --- Screenings ---
    screenings = []
    for fs in intermediate.functional_status_all:
        if fs.score is not None:
            interpretation = _interpret_screening(fs.instrument, fs.score)
            screening_type = SCREENING_TYPE_MAP.get(fs.instrument)

            screenings.append(Screening(
                instrument=fs.instrument,
                score=fs.score,
                interpretation=interpretation,
                date=fs.date_parsed,
                screening_type=screening_type,
            ))

    # --- Procedures (classify surgical vs assessment) ---
    procedures = []
    for proc in intermediate.procedures_all:
        is_surg = _is_surgical(proc.description)
        procedures.append(ProcedureEntry(
            description=proc.description,
            code=proc.code,
            code_system=proc.code_system,
            date=proc.start_date_parsed,
            is_surgical=is_surg,
        ))

    # --- Social history ---
    social_history = SocialHistory(
        smoking_status=intermediate.social_history.smoking_status if intermediate.social_history else None,
        employment=social_from_conditions.get("employment"),
        education=social_from_conditions.get("education"),
        safety_concerns=safety_concerns,
    )

    # --- Immunizations summary ---
    imm_summary = None
    if intermediate.immunizations_all:
        imm_names = list(set(i.vaccine for i in intermediate.immunizations_all))
        imm_summary = f"{len(intermediate.immunizations_all)} immunizations on file: " + ", ".join(imm_names[:5])
        if len(imm_names) > 5:
            imm_summary += f" (+{len(imm_names) - 5} more)"

    # --- Sections found/missing ---
    sections_found = []
    sections_missing = []

    section_checks = [
        ("demographics", intermediate.patient is not None),
        ("allergies", intermediate.allergies is not None),
        ("medications", len(intermediate.medications_all) > 0),
        ("conditions", len(intermediate.conditions_all) > 0),
        ("labs", len(intermediate.lab_results_all) > 0),
        ("vitals", len(intermediate.vitals_all) > 0),
        ("procedures", len(intermediate.procedures_all) > 0),
        ("encounters", len(intermediate.encounters_all) > 0),
        ("social_history", intermediate.social_history is not None),
        ("immunizations", len(intermediate.immunizations_all) > 0),
        ("screenings", len(intermediate.functional_status_all) > 0),
        ("care_plan", len(intermediate.care_plan_all) > 0),
    ]

    for name, present in section_checks:
        if present:
            sections_found.append(name)
        else:
            sections_missing.append(name)

    # --- Assemble canonical output ---
    return CanonicalReferral(
        referral_id=uuid4(),
        ingested_at=now_str,
        source_documents=[SourceDocument(
            filename=filename,
            format=DocumentFormat.CCDA_XML,
            extraction_path=ExtractionPath.STRUCTURED_PARSE,
        )],
        patient=patient,
        clinical_data=ClinicalData(
            problem_list=ProblemList(
                active=active_conditions,
                significant_history=significant_history,
            ),
            medications=Medications(
                active=active_meds,
                recently_stopped=recently_stopped_meds,
            ),
            allergies=allergies,
            recent_labs=recent_labs,
            recent_vitals=recent_vitals,
            screenings=screenings,
            procedures_and_surgeries=procedures,
            social_history=social_history,
            immunizations_summary=imm_summary,
        ),
        extraction_metadata=ExtractionMetadata(
            extraction_path=ExtractionPath.STRUCTURED_PARSE,
            extraction_timestamp=now_str,
            sections_found=sections_found,
            sections_missing=sections_missing,
        ),
    )


def _vital_str(vital: Optional[CCDVital]) -> Optional[str]:
    """Format a vital sign as 'value unit'."""
    if not vital or not vital.value:
        return None
    if vital.unit:
        return f"{vital.value} {vital.unit}"
    return vital.value
