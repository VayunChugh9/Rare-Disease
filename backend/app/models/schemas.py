"""Pydantic models for RefTriage data schemas.

Schema 1: Canonical Output Schema — the single target data contract.
Schema 2: CCD Intermediate Schema — raw parsed CCD output before filtering.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Schema 1: Canonical Output Schema
# ---------------------------------------------------------------------------

class DocumentFormat(str, Enum):
    CCDA_XML = "ccda_xml"
    FHIR_JSON = "fhir_json"
    PDF_TYPED = "pdf_typed"
    PDF_SCANNED = "pdf_scanned"
    PDF_HANDWRITTEN = "pdf_handwritten"
    PLAIN_TEXT = "plain_text"


class ExtractionPath(str, Enum):
    STRUCTURED_PARSE = "structured_parse"
    LLM_EXTRACTION = "llm_extraction"
    HYBRID = "hybrid"


class TriageUrgency(str, Enum):
    URGENT = "urgent"
    SEMI_URGENT = "semi_urgent"
    ROUTINE = "routine"
    NEEDS_CLARIFICATION = "needs_clarification"
    INAPPROPRIATE = "inappropriate"


class ScreeningType(str, Enum):
    MENTAL_HEALTH = "mental_health"
    SUBSTANCE_USE = "substance_use"
    SAFETY = "safety"
    COGNITIVE = "cognitive"
    FUNCTIONAL = "functional"


class SourceDocument(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: Optional[str] = None
    format: Optional[DocumentFormat] = None
    extraction_path: Optional[ExtractionPath] = None
    page_count: Optional[int] = None


class PatientInsurance(BaseModel):
    plan_name: Optional[str] = None
    member_id: Optional[str] = None
    group_number: Optional[str] = None


class PatientAddress(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None


class PatientContact(BaseModel):
    phone: Optional[str] = None
    address: Optional[PatientAddress] = None


class CanonicalPatient(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    race: Optional[str] = None
    ethnicity: Optional[str] = None
    language: Optional[str] = None
    mrn: Optional[str] = None
    insurance: Optional[PatientInsurance] = None
    contact: Optional[PatientContact] = None


class ReferringProvider(BaseModel):
    name: Optional[str] = None
    npi: Optional[str] = None
    practice_name: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    address: Optional[str] = None


class ReferralInfo(BaseModel):
    receiving_specialty: Optional[str] = None
    receiving_provider: Optional[str] = None
    reason: Optional[str] = None
    clinical_question: Optional[str] = None
    urgency_stated: Optional[str] = None
    date_of_referral: Optional[str] = None


class ActiveCondition(BaseModel):
    diagnosis: str
    code: Optional[str] = None
    code_system: Optional[str] = None
    onset_date: Optional[str] = None


class SignificantHistory(BaseModel):
    diagnosis: str
    code: Optional[str] = None
    code_system: Optional[str] = None
    onset_date: Optional[str] = None
    resolution_date: Optional[str] = None
    significance_reason: Optional[str] = None


class ProblemList(BaseModel):
    active: list[ActiveCondition] = Field(default_factory=list)
    significant_history: list[SignificantHistory] = Field(default_factory=list)


class ActiveMedication(BaseModel):
    name: str
    dose: Optional[str] = None
    frequency: Optional[str] = None
    rxnorm: Optional[str] = None
    first_prescribed: Optional[str] = None
    source: Optional[str] = None


class RecentlyStoppedMedication(BaseModel):
    name: str
    dose: Optional[str] = None
    rxnorm: Optional[str] = None
    stop_date: Optional[str] = None
    duration_on_med: Optional[str] = None
    reason_stopped: Optional[str] = None


class Medications(BaseModel):
    active: list[ActiveMedication] = Field(default_factory=list)
    recently_stopped: list[RecentlyStoppedMedication] = Field(default_factory=list)


class KnownAllergy(BaseModel):
    substance: str
    reaction: Optional[str] = None
    severity: Optional[str] = None


class Allergies(BaseModel):
    known_allergies: list[KnownAllergy] = Field(default_factory=list)
    no_known_allergies: bool = False


class LabTestResult(BaseModel):
    test_name: str
    loinc: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    flag: Optional[str] = None
    prior_value: Optional[str] = None
    prior_date: Optional[str] = None


class LabPanel(BaseModel):
    panel_name: Optional[str] = None
    panel_loinc: Optional[str] = None
    date: Optional[str] = None
    results: list[LabTestResult] = Field(default_factory=list)


class VitalTrends(BaseModel):
    weight_3_visits: list[str] = Field(default_factory=list)
    bp_3_visits: list[str] = Field(default_factory=list)
    a1c_3_visits: list[str] = Field(default_factory=list)


class RecentVitals(BaseModel):
    date: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    bmi: Optional[str] = None
    heart_rate: Optional[str] = None
    respiratory_rate: Optional[str] = None
    blood_pressure: Optional[str] = None
    temperature: Optional[str] = None
    pain_score: Optional[str] = None
    oxygen_saturation: Optional[str] = None
    trends: Optional[VitalTrends] = None


class Screening(BaseModel):
    instrument: str
    score: str
    interpretation: Optional[str] = None
    date: Optional[str] = None
    screening_type: Optional[ScreeningType] = None


class ProcedureEntry(BaseModel):
    description: str
    code: Optional[str] = None
    code_system: Optional[str] = None
    date: Optional[str] = None
    is_surgical: bool = False


class SocialHistory(BaseModel):
    smoking_status: Optional[str] = None
    alcohol_use: Optional[str] = None
    substance_use: Optional[str] = None
    employment: Optional[str] = None
    education: Optional[str] = None
    housing: Optional[str] = None
    safety_concerns: Optional[str] = None
    other: Optional[str] = None


class ClinicalData(BaseModel):
    problem_list: Optional[ProblemList] = None
    medications: Optional[Medications] = None
    allergies: Optional[Allergies] = None
    recent_labs: list[LabPanel] = Field(default_factory=list)
    recent_vitals: Optional[RecentVitals] = None
    screenings: list[Screening] = Field(default_factory=list)
    procedures_and_surgeries: list[ProcedureEntry] = Field(default_factory=list)
    social_history: Optional[SocialHistory] = None
    immunizations_summary: Optional[str] = None


class TriageInfo(BaseModel):
    urgency: Optional[TriageUrgency] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    red_flags: list[str] = Field(default_factory=list)
    missing_critical_info: list[str] = Field(default_factory=list)
    data_quality_notes: list[str] = Field(default_factory=list)


class TrialSignal(BaseModel):
    signal_type: Optional[str] = None
    detail: Optional[str] = None
    source_field: Optional[str] = None


class ClinicalTrialRelevance(BaseModel):
    potentially_eligible: bool = False
    signals: list[TrialSignal] = Field(default_factory=list)
    suggested_search_terms: list[str] = Field(default_factory=list)


class ExtractionMetadata(BaseModel):
    extraction_path: Optional[ExtractionPath] = None
    ocr_confidence_mean: Optional[float] = None
    ocr_low_confidence_regions: list[str] = Field(default_factory=list)
    extraction_model: Optional[str] = None
    extraction_timestamp: Optional[str] = None
    sections_found: list[str] = Field(default_factory=list)
    sections_missing: list[str] = Field(default_factory=list)


class CanonicalReferral(BaseModel):
    """The single target schema — canonical output from both extraction paths."""
    referral_id: UUID = Field(default_factory=uuid4)
    ingested_at: Optional[str] = None
    source_documents: list[SourceDocument] = Field(default_factory=list)
    patient: Optional[CanonicalPatient] = None
    referring_provider: Optional[ReferringProvider] = None
    referral: Optional[ReferralInfo] = None
    clinical_data: Optional[ClinicalData] = None
    triage: Optional[TriageInfo] = None
    clinical_trial_relevance: Optional[ClinicalTrialRelevance] = None
    extraction_metadata: Optional[ExtractionMetadata] = None


# ---------------------------------------------------------------------------
# Schema 2: CCD Intermediate Schema
# ---------------------------------------------------------------------------

class CCDSourceOrganization(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class CCDPatientAddress(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None


class CCDPatient(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob_raw: Optional[str] = None
    dob_parsed: Optional[str] = None
    sex: Optional[str] = None
    race: Optional[str] = None
    ethnicity: Optional[str] = None
    language: Optional[str] = None
    mrn: Optional[str] = None
    address: Optional[CCDPatientAddress] = None
    phone: Optional[str] = None


class CCDAllergyEntry(BaseModel):
    substance: str
    substance_code: Optional[str] = None
    code_system: Optional[str] = None
    reaction: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None


class CCDAllergies(BaseModel):
    no_known_allergies: bool = False
    entries: list[CCDAllergyEntry] = Field(default_factory=list)


class CCDMedication(BaseModel):
    name: str
    code: Optional[str] = None
    code_system: Optional[str] = None
    start_date_raw: Optional[str] = None
    start_date_parsed: Optional[str] = None
    stop_date_raw: Optional[str] = None
    stop_date_parsed: Optional[str] = None
    is_active: bool = False


class CCDCondition(BaseModel):
    description: str
    code: Optional[str] = None
    code_system: Optional[str] = None
    onset_date_raw: Optional[str] = None
    onset_date_parsed: Optional[str] = None
    resolution_date_raw: Optional[str] = None
    resolution_date_parsed: Optional[str] = None
    is_active: bool = False
    is_clinical: bool = True


class CCDLabComponent(BaseModel):
    test_name: str
    loinc: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    date_raw: Optional[str] = None
    date_parsed: Optional[str] = None


class CCDLabResult(BaseModel):
    panel_name: str
    panel_loinc: Optional[str] = None
    date_raw: Optional[str] = None
    date_parsed: Optional[str] = None
    components: list[CCDLabComponent] = Field(default_factory=list)


class CCDVital(BaseModel):
    measure: str
    loinc: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    date_raw: Optional[str] = None
    date_parsed: Optional[str] = None


class CCDProcedure(BaseModel):
    description: str
    code: Optional[str] = None
    code_system: Optional[str] = None
    start_date_parsed: Optional[str] = None
    end_date_parsed: Optional[str] = None


class CCDEncounter(BaseModel):
    description: str
    code: Optional[str] = None
    start_date_parsed: Optional[str] = None
    end_date_parsed: Optional[str] = None
    provider: Optional[str] = None
    location: Optional[str] = None


class CCDSocialHistory(BaseModel):
    smoking_status: Optional[str] = None
    smoking_snomed: Optional[str] = None
    smoking_date: Optional[str] = None


class CCDImmunization(BaseModel):
    vaccine: str
    code: Optional[str] = None
    date_parsed: Optional[str] = None
    status: Optional[str] = None


class CCDFunctionalStatus(BaseModel):
    instrument: str
    loinc: Optional[str] = None
    score: Optional[str] = None
    unit: Optional[str] = None
    date_parsed: Optional[str] = None


class CCDCarePlan(BaseModel):
    description: str
    code: Optional[str] = None
    status: Optional[str] = None
    date_parsed: Optional[str] = None


class CCDIntermediate(BaseModel):
    """Raw parsed output from CCD/CCDA XML before recency filtering."""
    document_id: UUID = Field(default_factory=uuid4)
    document_date: Optional[str] = None
    source_organization: Optional[CCDSourceOrganization] = None
    patient: Optional[CCDPatient] = None
    allergies: Optional[CCDAllergies] = None
    medications_all: list[CCDMedication] = Field(default_factory=list)
    conditions_all: list[CCDCondition] = Field(default_factory=list)
    lab_results_all: list[CCDLabResult] = Field(default_factory=list)
    vitals_all: list[CCDVital] = Field(default_factory=list)
    procedures_all: list[CCDProcedure] = Field(default_factory=list)
    encounters_all: list[CCDEncounter] = Field(default_factory=list)
    social_history: Optional[CCDSocialHistory] = None
    immunizations_all: list[CCDImmunization] = Field(default_factory=list)
    functional_status_all: list[CCDFunctionalStatus] = Field(default_factory=list)
    care_plan_all: list[CCDCarePlan] = Field(default_factory=list)
