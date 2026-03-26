"""LLM extraction service for RefTriage (Path B — unstructured documents).

Provides text cleaning (gpt-4o-mini) and structured extraction (gpt-4o)
using OpenAI function/tool calling. Adapted from Prompts 1 and 2 in
reftriage_prompts.md.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from backend.app.models.schemas import CanonicalReferral
from backend.app.services.openai_client import (
    MODEL_CLEANING,
    MODEL_EXTRACTION,
    get_client,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt 1: Text cleaning
# ---------------------------------------------------------------------------

TEXT_CLEANING_SYSTEM_PROMPT = """\
You are a clinical document text cleaner. You receive raw text extracted from a clinical referral document via OCR or PDF text extraction.

Your job:
1. Fix obvious OCR artifacts: broken words, misrecognized characters (common: "rn" → "m", "1" ↔ "l", "0" ↔ "O", "cl" → "d"), formatting artifacts, stray symbols.
2. Identify and label document sections using brackets. Use these standard labels:
   [DEMOGRAPHICS]
   [REFERRING PROVIDER]
   [REFERRAL REASON]
   [MEDICATIONS]
   [ALLERGIES]
   [PROBLEM LIST]
   [ASSESSMENT]
   [HISTORY]
   [SURGICAL HISTORY]
   [SOCIAL HISTORY]
   [VITALS]
   [LABS]
   [IMAGING]
   [PLAN]
   [INSURANCE]
   [OTHER]
3. Preserve all clinical information EXACTLY as written. Do not add, remove, interpret, or rephrase any clinical content.
4. Flag regions where text is garbled or unreadable: [ILLEGIBLE: brief description of what might be there based on surrounding context].
5. Normalize formatting: remove excessive whitespace, fix line breaks that split words mid-word, merge hyphenated line-break words.
6. If the document has no clear section structure (e.g., a brief fax cover note), wrap the entire content in [REFERRAL REASON] and [OTHER] as appropriate.

Do NOT summarize. Do NOT interpret clinical meaning. Do NOT add any information not present in the original text. Your only job is to make the text clean and navigable for the extraction system that processes it next.
"""


# ---------------------------------------------------------------------------
# Prompt 2: Structured extraction
# ---------------------------------------------------------------------------

EXTRACTION_SYSTEM_PROMPT = """\
You are a clinical data extraction system. You receive cleaned text from a clinical referral document and must extract all available information into the structured schema provided via the extract_referral_data tool.

PATIENT SAFETY RULES — these are non-negotiable:

1. ONLY extract information EXPLICITLY stated in the document text. If the text says "patient takes metformin 500mg daily", extract that medication. If it does NOT mention diabetes anywhere, do NOT add diabetes to the problem list — even though metformin is a diabetes medication.

2. NEVER infer diagnoses from medications, labs, or other indirect evidence.

3. NEVER infer relationships between data points unless explicitly stated.

4. If a field cannot be populated from the document, set it to null. NEVER guess, estimate, or fill in plausible-sounding data. A null field is always safer than a fabricated one.

5. If information is ambiguous or contradictory, extract both versions and note the conflict in data_quality_notes.

EXTRACTION PRIORITIES (in order of importance):

1. Referral reason and clinical question — this is the most important clinical field. Extract verbatim from the document if possible. If the referring provider asks a specific question ("Is this patient a candidate for surgery?"), capture it in clinical_question.

2. Patient demographics — name, DOB, sex, contact info, insurance.

3. Referring provider — name, practice, contact info, NPI if present.

4. Active medications with doses and frequencies.

5. Active conditions/diagnoses with onset dates if available.

6. Recent labs and vitals — include values, units, and dates.

7. Allergies — or explicitly note "no known allergies" if the document states this.

8. Surgical/procedure history.

9. Social history — smoking, alcohol, substance use, living situation.

10. Missing information — list EVERYTHING that is clinically important but absent from the document. This is as valuable as what you extract.

HANDLING SPECIFIC SITUATIONS:

- Approximate dates: "about 3 months ago" from a document dated 2026-03-15 → "2025-12-15" with a note in data_quality_notes: "Date approximated from '3 months ago'".
- Medication lists without doses: Extract the medication name, set dose to null. Do NOT guess standard doses.
- Abbreviations: Expand common medical abbreviations (HTN → hypertension, DM → diabetes mellitus, SOB → shortness of breath) in the diagnosis field but preserve the original abbreviation in data_quality_notes if there's any ambiguity.
- Multiple pages with redundant information: Extract from the most recent/detailed version. Note redundancy in data_quality_notes.

TRIAGE CLASSIFICATION — assess AFTER completing extraction:

- urgent: Acute or rapidly deteriorating symptoms. Keywords: "emergent", "stat", "ASAP", "immediate", "acute", "worsening rapidly". Clinical indicators: chest pain, acute neurological symptoms, hemodynamic instability, acute abdomen, suicidal ideation with plan.
- semi_urgent: Progressive symptoms needing evaluation within 1-2 weeks. Moderate clinical concern but not immediately life-threatening.
- routine: Stable condition, standard specialty evaluation, preventive care referral, chronic disease management.
- needs_clarification: Referral reason is vague, insufficient clinical context to assess urgency, or critical information is missing (no diagnosis, no symptoms described).
- inappropriate: Referral clearly does not match the receiving specialty, or the clinical situation does not warrant specialty referral.

When in doubt between two urgency levels, always triage UP (more urgent). It is safer to over-triage than under-triage.

Set triage confidence LOWER (<0.7) when: key clinical data is missing, OCR quality was poor, the referral reason is vague, or the clinical picture is complex/ambiguous.

RED FLAGS — always include in red_flags if detected:

- Chest pain or pressure
- Shortness of breath at rest
- Sudden-onset neurological symptoms (weakness, numbness, vision changes, speech difficulty)
- Unintentional weight loss >10%
- New mass, lump, or unexplained lymphadenopathy
- Hemoptysis (coughing blood)
- Melena or hematochezia (GI bleeding)
- Suicidal ideation, homicidal ideation, or self-harm
- Signs of abuse or neglect (in any age group)
- Pediatric safeguarding concerns
- Pregnancy complications
- Unstable vital signs (if vitals are present)
- Acute vision loss
- Severe pain (>8/10)
- Signs of sepsis (fever + tachycardia + hypotension)
- Falls in elderly patients

CLINICAL TRIAL RELEVANCE — assess AFTER extraction:

Set clinical_trial_relevance.potentially_eligible = true if ANY of the following are present:
- Active cancer or malignancy of any type
- Rare disease (any condition affecting <200,000 people in the US)
- Treatment-resistant condition (failed 2+ standard therapies)
- Genetic or biomarker data mentioned (e.g., BRCA, HER2, EGFR, specific mutations)
- Advanced or refractory disease on current therapy
- Autoimmune conditions on biologic therapy
- Neurological conditions (ALS, MS, Parkinson's, Alzheimer's, rare epilepsies)
- Specific lab values outside normal range that could be biomarker-eligible

For each signal, record what triggered it (signal_type, detail, source_field) and suggest search terms a coordinator could use on ClinicalTrials.gov.
"""


# ---------------------------------------------------------------------------
# OpenAI Tool schema for extraction (derived from canonical schema 1)
# ---------------------------------------------------------------------------

EXTRACT_REFERRAL_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_referral_data",
        "description": (
            "Extract all available clinical information from the referral "
            "document into a structured format. Call this tool with all "
            "extracted data."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "patient": {
                    "type": "object",
                    "properties": {
                        "first_name": {"type": ["string", "null"]},
                        "last_name": {"type": ["string", "null"]},
                        "date_of_birth": {"type": ["string", "null"], "description": "YYYY-MM-DD format"},
                        "age": {"type": ["integer", "null"]},
                        "sex": {"type": ["string", "null"], "enum": ["M", "F", "Other", None]},
                        "race": {"type": ["string", "null"]},
                        "ethnicity": {"type": ["string", "null"]},
                        "language": {"type": ["string", "null"]},
                        "mrn": {"type": ["string", "null"]},
                        "insurance": {
                            "type": ["object", "null"],
                            "properties": {
                                "plan_name": {"type": ["string", "null"]},
                                "member_id": {"type": ["string", "null"]},
                                "group_number": {"type": ["string", "null"]},
                            },
                        },
                        "contact": {
                            "type": ["object", "null"],
                            "properties": {
                                "phone": {"type": ["string", "null"]},
                                "address": {
                                    "type": ["object", "null"],
                                    "properties": {
                                        "street": {"type": ["string", "null"]},
                                        "city": {"type": ["string", "null"]},
                                        "state": {"type": ["string", "null"]},
                                        "zip": {"type": ["string", "null"]},
                                    },
                                },
                            },
                        },
                    },
                },
                "referring_provider": {
                    "type": ["object", "null"],
                    "properties": {
                        "name": {"type": ["string", "null"]},
                        "npi": {"type": ["string", "null"]},
                        "practice_name": {"type": ["string", "null"]},
                        "phone": {"type": ["string", "null"]},
                        "fax": {"type": ["string", "null"]},
                        "address": {"type": ["string", "null"]},
                    },
                },
                "referral": {
                    "type": ["object", "null"],
                    "properties": {
                        "receiving_specialty": {"type": ["string", "null"]},
                        "receiving_provider": {"type": ["string", "null"]},
                        "reason": {"type": ["string", "null"]},
                        "clinical_question": {"type": ["string", "null"]},
                        "urgency_stated": {"type": ["string", "null"]},
                        "date_of_referral": {"type": ["string", "null"], "description": "YYYY-MM-DD"},
                    },
                },
                "clinical_data": {
                    "type": "object",
                    "properties": {
                        "problem_list": {
                            "type": "object",
                            "properties": {
                                "active": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "diagnosis": {"type": "string"},
                                            "code": {"type": ["string", "null"]},
                                            "code_system": {"type": ["string", "null"]},
                                            "onset_date": {"type": ["string", "null"]},
                                        },
                                        "required": ["diagnosis"],
                                    },
                                },
                                "significant_history": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "diagnosis": {"type": "string"},
                                            "code": {"type": ["string", "null"]},
                                            "code_system": {"type": ["string", "null"]},
                                            "onset_date": {"type": ["string", "null"]},
                                            "resolution_date": {"type": ["string", "null"]},
                                            "significance_reason": {"type": ["string", "null"]},
                                        },
                                        "required": ["diagnosis"],
                                    },
                                },
                            },
                        },
                        "medications": {
                            "type": "object",
                            "properties": {
                                "active": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "dose": {"type": ["string", "null"]},
                                            "frequency": {"type": ["string", "null"]},
                                            "rxnorm": {"type": ["string", "null"]},
                                            "first_prescribed": {"type": ["string", "null"]},
                                            "source": {"type": ["string", "null"]},
                                        },
                                        "required": ["name"],
                                    },
                                },
                                "recently_stopped": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "dose": {"type": ["string", "null"]},
                                            "rxnorm": {"type": ["string", "null"]},
                                            "stop_date": {"type": ["string", "null"]},
                                            "duration_on_med": {"type": ["string", "null"]},
                                            "reason_stopped": {"type": ["string", "null"]},
                                        },
                                        "required": ["name"],
                                    },
                                },
                            },
                        },
                        "allergies": {
                            "type": "object",
                            "properties": {
                                "known_allergies": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "substance": {"type": "string"},
                                            "reaction": {"type": ["string", "null"]},
                                            "severity": {"type": ["string", "null"]},
                                        },
                                        "required": ["substance"],
                                    },
                                },
                                "no_known_allergies": {"type": "boolean"},
                            },
                        },
                        "recent_labs": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "panel_name": {"type": ["string", "null"]},
                                    "panel_loinc": {"type": ["string", "null"]},
                                    "date": {"type": ["string", "null"]},
                                    "results": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "test_name": {"type": "string"},
                                                "loinc": {"type": ["string", "null"]},
                                                "value": {"type": ["string", "null"]},
                                                "unit": {"type": ["string", "null"]},
                                                "flag": {"type": ["string", "null"]},
                                                "prior_value": {"type": ["string", "null"]},
                                                "prior_date": {"type": ["string", "null"]},
                                            },
                                            "required": ["test_name"],
                                        },
                                    },
                                },
                            },
                        },
                        "recent_vitals": {
                            "type": ["object", "null"],
                            "properties": {
                                "date": {"type": ["string", "null"]},
                                "height": {"type": ["string", "null"]},
                                "weight": {"type": ["string", "null"]},
                                "bmi": {"type": ["string", "null"]},
                                "heart_rate": {"type": ["string", "null"]},
                                "respiratory_rate": {"type": ["string", "null"]},
                                "blood_pressure": {"type": ["string", "null"]},
                                "temperature": {"type": ["string", "null"]},
                                "pain_score": {"type": ["string", "null"]},
                                "oxygen_saturation": {"type": ["string", "null"]},
                            },
                        },
                        "screenings": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "instrument": {"type": "string"},
                                    "score": {"type": "string"},
                                    "interpretation": {"type": ["string", "null"]},
                                    "date": {"type": ["string", "null"]},
                                    "screening_type": {"type": ["string", "null"]},
                                },
                                "required": ["instrument", "score"],
                            },
                        },
                        "procedures_and_surgeries": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string"},
                                    "code": {"type": ["string", "null"]},
                                    "code_system": {"type": ["string", "null"]},
                                    "date": {"type": ["string", "null"]},
                                    "is_surgical": {"type": "boolean"},
                                },
                                "required": ["description"],
                            },
                        },
                        "social_history": {
                            "type": ["object", "null"],
                            "properties": {
                                "smoking_status": {"type": ["string", "null"]},
                                "alcohol_use": {"type": ["string", "null"]},
                                "substance_use": {"type": ["string", "null"]},
                                "employment": {"type": ["string", "null"]},
                                "education": {"type": ["string", "null"]},
                                "housing": {"type": ["string", "null"]},
                                "safety_concerns": {"type": ["string", "null"]},
                                "other": {"type": ["string", "null"]},
                            },
                        },
                        "immunizations_summary": {"type": ["string", "null"]},
                    },
                },
                "triage": {
                    "type": "object",
                    "properties": {
                        "urgency": {
                            "type": "string",
                            "enum": ["urgent", "semi_urgent", "routine", "needs_clarification", "inappropriate"],
                        },
                        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "reasoning": {"type": "string"},
                        "red_flags": {"type": "array", "items": {"type": "string"}},
                        "missing_critical_info": {"type": "array", "items": {"type": "string"}},
                        "data_quality_notes": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["urgency", "confidence", "reasoning"],
                },
                "clinical_trial_relevance": {
                    "type": "object",
                    "properties": {
                        "potentially_eligible": {"type": "boolean"},
                        "signals": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "signal_type": {"type": "string"},
                                    "detail": {"type": "string"},
                                    "source_field": {"type": "string"},
                                },
                            },
                        },
                        "suggested_search_terms": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "extraction_metadata": {
                    "type": "object",
                    "properties": {
                        "extraction_path": {"type": "string", "enum": ["llm_extraction"]},
                        "extraction_model": {"type": ["string", "null"]},
                        "sections_found": {"type": "array", "items": {"type": "string"}},
                        "sections_missing": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "required": ["patient", "clinical_data", "triage"],
        },
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def clean_text(raw_text: str) -> str:
    """Clean raw document text using gpt-4o-mini (Prompt 1).

    Fixes OCR artifacts, labels sections, and normalizes formatting.
    Only used for unstructured documents (Path B), NOT for CCD/XML.

    Args:
        raw_text: Raw text from OCR or PDF text extraction.

    Returns:
        Cleaned text with section labels.
    """
    client = get_client()

    logger.info("Text cleaning: %d chars of raw input", len(raw_text))

    response = client.chat.completions.create(
        model=MODEL_CLEANING,
        temperature=0,
        messages=[
            {"role": "system", "content": TEXT_CLEANING_SYSTEM_PROMPT},
            {"role": "user", "content": raw_text},
        ],
    )

    cleaned = response.choices[0].message.content or ""
    logger.info("Text cleaning complete: %d chars output", len(cleaned))
    return cleaned


def extract_structured(
    cleaned_text: str,
    *,
    source_filename: Optional[str] = None,
) -> CanonicalReferral:
    """Extract structured data from cleaned text via OpenAI tool calling.

    Uses gpt-4o with function calling to populate the canonical schema.
    Only used for unstructured documents (Path B).

    Args:
        cleaned_text: Output from clean_text().
        source_filename: Optional filename for metadata.

    Returns:
        CanonicalReferral populated from LLM extraction.

    Raises:
        RuntimeError: If the LLM does not produce a valid tool call.
    """
    client = get_client()

    logger.info("Structured extraction: %d chars of cleaned text", len(cleaned_text))

    response = client.chat.completions.create(
        model=MODEL_EXTRACTION,
        temperature=0,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": cleaned_text},
        ],
        tools=[EXTRACT_REFERRAL_TOOL],
        tool_choice={
            "type": "function",
            "function": {"name": "extract_referral_data"},
        },
    )

    message = response.choices[0].message

    # Extract tool call arguments
    if not message.tool_calls or len(message.tool_calls) == 0:
        raise RuntimeError("LLM did not produce a tool call for extraction")

    tool_call = message.tool_calls[0]
    if tool_call.function.name != "extract_referral_data":
        raise RuntimeError(
            f"Unexpected tool call: {tool_call.function.name}"
        )

    raw_args = tool_call.function.arguments
    parsed = json.loads(raw_args)

    # Add extraction metadata
    if "extraction_metadata" not in parsed:
        parsed["extraction_metadata"] = {}
    parsed["extraction_metadata"]["extraction_path"] = "llm_extraction"
    parsed["extraction_metadata"]["extraction_model"] = MODEL_EXTRACTION

    # Add source document info if filename provided
    if source_filename:
        parsed.setdefault("source_documents", [])
        parsed["source_documents"].append({
            "filename": source_filename,
            "format": "plain_text",
            "extraction_path": "llm_extraction",
        })

    # Validate through Pydantic
    canonical = CanonicalReferral.model_validate(parsed)

    logger.info(
        "Extraction complete: triage=%s",
        canonical.triage.urgency if canonical.triage else "N/A",
    )

    return canonical
