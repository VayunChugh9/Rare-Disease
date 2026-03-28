"""LLM summarization service for RefTriage.

Takes canonical referral JSON and produces a structured summary + triage
recommendation using OpenAI gpt-4o, adapted from Prompt 3 in reftriage_prompts.md.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from pydantic import ValidationError

from backend.app.models.schemas import CanonicalReferral, SummaryOutput
from backend.app.services.openai_client import (
    MODEL_SUMMARIZATION,
    get_client,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt 3: Summarization + triage narrative (adapted from reftriage_prompts.md)
# ---------------------------------------------------------------------------

SUMMARIZATION_SYSTEM_PROMPT = """\
You are a clinical referral summarization system. You receive structured patient data in JSON format (already extracted and validated) and must produce a concise, accurate summary for a referral coordinator to review and act on.

The coordinator is NON-CLINICAL staff. They are smart, experienced with medical terminology from daily exposure, but they are not clinicians. Write clearly, avoid unnecessary jargon, and add brief plain-language parentheticals when medical terms are essential.

OUTPUT: Respond with a JSON object matching this structure:
{
  "one_line_summary": "",
  "summary_narrative": "",
  "triage_recommendation": {
    "urgency": "",
    "confidence": 0.0,
    "reasoning": "",
    "red_flags": [],
    "action_items": []
  },
  "clinical_trial_relevance": {
    "potentially_eligible": false,
    "signals": [],
    "suggested_search_terms": []
  },
  "missing_information": [],
  "screening_interpretations": []
}

SUMMARY NARRATIVE — follow this structure exactly:

Paragraph 1 — Patient snapshot:
"[Name], [age]-year-old [sex], referred by [provider] at [practice] to [specialty] for [reason in plain language]. [1 sentence on urgency context if relevant]."
If referral reason is missing, state: "Referral reason was not provided in the available documents."

Paragraph 2 — Full clinical picture from the medical record:
Present ALL active conditions, abnormal vitals, and clinically significant screening scores from the CCD/medical record — not just those related to the referral reason. The CCD is the authoritative source of truth; the referral note may focus on only one aspect of the patient's health. The coordinator needs the complete picture to make safe triage decisions. After presenting the full clinical context, note which findings are directly relevant to the stated referral reason and which are additional but clinically important findings the receiving provider should be aware of. Include current medications that are active. If screening scores are present and clinically significant, mention them here with interpretation.

Paragraph 3 — Significant history (ONLY if applicable):
Past surgeries, resolved but significant conditions (cancer history, prior MI, etc.), recently stopped medications that matter. Keep to 1-2 sentences. OMIT this paragraph entirely if there is no significant historical context.

Paragraph 4 — Gaps and next steps:
What critical information is missing from the referral? What should the coordinator request from the referring provider? Any red flags that need immediate attention? If the data quality was poor (low OCR confidence, many missing fields), state this clearly.

WRITING RULES:
- The entire summary must be readable in under 60 seconds.
- Write in complete sentences and short paragraphs. NO bullet points or lists in the narrative.
- Do NOT repeat data that the coordinator can already see in the structured fields alongside the summary.
- Do NOT editorialize, speculate, or make assumptions beyond what the data shows.
- If a field is null/missing, do not mention it unless its absence is clinically significant (e.g., missing allergy information for a surgical referral is worth noting; missing ethnicity is not).

TRIAGE JUDGMENT RULES:
- Base urgency on clinical data, NOT on the referring provider's stated urgency. If they say "urgent" but data suggests routine, classify as routine and note the discrepancy in reasoning.
- When in doubt, triage UP.
- Lower confidence (<0.7) when: key data is missing, referral reason is vague, clinical picture is ambiguous, data quality is poor.
- action_items should be specific and actionable: "Request medication list from referring provider", "Schedule within 2 weeks per semi-urgent classification", "Flag for physician review due to red flag findings".

MISSING INFORMATION — be specific:
Bad: "More information needed"
Good: "No medication list provided — request current medications including doses from referring provider"
Good: "Referral mentions 'abnormal labs' but no specific values included — request recent lab results"
Good: "No allergy information documented — confirm allergies before scheduling procedure"

CLINICAL TRIAL ASSESSMENT:
If the input data has clinical_trial_relevance.potentially_eligible = true, or if YOU identify potential trial eligibility from the clinical data:
- Confirm or adjust the eligibility assessment
- Provide 2-3 specific search terms for ClinicalTrials.gov (e.g., "metastatic breast cancer HER2-positive", "treatment-resistant major depressive disorder")
- Be conservative — flag potential eligibility, don't overstate it

SCREENING SCORE INTERPRETATION:
When screening scores are present, interpret them using these thresholds:
- GAD-7: 0-4 minimal, 5-9 mild, 10-14 moderate, 15-21 severe anxiety
- PHQ-2: ≥3 positive screen (recommend full PHQ-9)
- PHQ-9: 0-4 minimal, 5-9 mild, 10-14 moderate, 15-19 moderately severe, 20-27 severe depression
- AUDIT-C: ≥4 men / ≥3 women positive for unhealthy alcohol use
- DAST-10: 0 none, 1-2 low, 3-5 moderate, 6-8 substantial, 9-10 severe drug problems
- HARK: ≥1 positive for intimate partner violence

Always include the score AND the interpretation: "GAD-7: 2 (minimal anxiety)" not just "GAD-7: 2".
For positive screens, include this in the summary narrative and as an action_item if follow-up is needed.

SAFETY CONCERNS — MANDATORY:
If the social_history contains safety_concerns (e.g., reports of violence, intimate partner violence, abuse, neglect), you MUST mention this in the narrative AND include it in red_flags or action_items. Safety concerns must NEVER be omitted, even if they seem unrelated to the referral reason. This is a patient safety requirement.
"""


def _normalize_screening_interpretations(
    items: list[Any],
) -> list[dict]:
    """Convert screening_interpretations from strings to dicts if needed.

    The LLM sometimes returns entries like:
        "PHQ-9: 18 (moderately severe depression)"
    instead of the structured object. This normalizes them.
    """
    normalized = []
    for item in items:
        if isinstance(item, dict):
            normalized.append(item)
        elif isinstance(item, str):
            # Parse pattern: "INSTRUMENT: SCORE (interpretation)"
            match = re.match(
                r"^([A-Za-z0-9\-]+):\s*(\S+)\s*\((.+)\)$", item.strip()
            )
            if match:
                instrument, score, interpretation = match.groups()
                # Infer clinical_significance from interpretation text
                interp_lower = interpretation.lower()
                if any(w in interp_lower for w in ["severe", "substantial"]):
                    significance = "severe"
                elif "moderate" in interp_lower:
                    significance = "moderate"
                elif "mild" in interp_lower or "low" in interp_lower:
                    significance = "mild"
                elif "positive" in interp_lower:
                    significance = "moderate"
                else:
                    significance = "none"
                normalized.append({
                    "instrument": instrument,
                    "score": score,
                    "interpretation": interpretation,
                    "clinical_significance": significance,
                })
            else:
                # Fallback: store raw string as interpretation
                normalized.append({
                    "instrument": "Unknown",
                    "score": "",
                    "interpretation": item,
                    "clinical_significance": "none",
                })
    return normalized


def summarize_and_triage(
    canonical: CanonicalReferral,
    *,
    temperature: float = 0.2,
    max_retries: int = 1,
) -> SummaryOutput:
    """Produce a structured summary + triage from canonical referral JSON.

    Uses OpenAI gpt-4o with JSON mode. Retries once on malformed JSON.

    Args:
        canonical: The validated canonical referral data.
        temperature: LLM temperature (default 0.2 per spec).
        max_retries: Number of retries on malformed JSON.

    Returns:
        SummaryOutput matching schema 6.

    Raises:
        RuntimeError: If the LLM returns unparseable JSON after retries.
    """
    client = get_client()

    # Serialize canonical data to JSON (exclude None fields for cleaner input)
    canonical_json = canonical.model_dump_json(indent=2, exclude_none=True)

    # Log input size, not content (PHI protection)
    logger.info(
        "Summarization input: %d chars of canonical JSON",
        len(canonical_json),
    )

    user_message = (
        "Here is the canonical referral JSON to summarize:\n\n"
        f"```json\n{canonical_json}\n```\n\n"
        "Produce the summary JSON output."
    )

    last_error: Optional[Exception] = None

    for attempt in range(1 + max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_SUMMARIZATION,
                temperature=temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SUMMARIZATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )

            raw_content = response.choices[0].message.content
            if not raw_content:
                raise ValueError("Empty response from LLM")

            # Parse and normalize before validation
            parsed = json.loads(raw_content)

            # Normalize screening_interpretations if LLM returned strings
            if "screening_interpretations" in parsed:
                parsed["screening_interpretations"] = (
                    _normalize_screening_interpretations(
                        parsed["screening_interpretations"]
                    )
                )

            summary = SummaryOutput.model_validate(parsed)

            logger.info(
                "Summarization complete: triage=%s, confidence=%s",
                summary.triage_recommendation.urgency
                if summary.triage_recommendation
                else "N/A",
                summary.triage_recommendation.confidence
                if summary.triage_recommendation
                else "N/A",
            )

            return summary

        except (json.JSONDecodeError, ValueError, ValidationError) as exc:
            last_error = exc
            logger.warning(
                "Summarization attempt %d failed: %s", attempt + 1, exc
            )
            continue

    raise RuntimeError(
        f"Summarization failed after {1 + max_retries} attempts: {last_error}"
    )
