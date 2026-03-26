"""Pydantic models for RefTriage data schemas.

Schema 2: CCD Intermediate Schema — raw parsed CCD output before filtering.
Schema 1: Canonical Output Schema — the single target schema (built in Chunk 2).
"""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


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
