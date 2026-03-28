"""Deduplication logic for CCD intermediate data.

Collapses duplicate entries per rules in schema 3 (deduplication_rules)
before the recency filter produces the canonical schema.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from backend.app.models.schemas import (
    CCDCondition,
    CCDLabResult,
    CCDMedication,
    CCDVital,
)


def dedup_medications(meds: list[CCDMedication]) -> list[CCDMedication]:
    """Collapse consecutive entries with same drug name into single entry.

    Keeps the earliest start_date and latest stop_date.
    If any instance has no stop_date, the result is active.
    """
    if not meds:
        return []

    # Group by normalized drug name (case-insensitive)
    groups: dict[str, list[CCDMedication]] = {}
    for med in meds:
        key = med.name.strip().lower()
        groups.setdefault(key, []).append(med)

    deduped = []
    for key, group in groups.items():
        if len(group) == 1:
            deduped.append(group[0])
            continue

        # Find earliest start and latest stop
        earliest_start_raw = None
        earliest_start_parsed = None
        latest_stop_raw = None
        latest_stop_parsed = None
        any_active = False
        representative = group[0]

        for med in group:
            if med.start_date_parsed:
                if earliest_start_parsed is None or med.start_date_parsed < earliest_start_parsed:
                    earliest_start_parsed = med.start_date_parsed
                    earliest_start_raw = med.start_date_raw

            if med.is_active or med.stop_date_parsed is None:
                any_active = True
            elif med.stop_date_parsed:
                if latest_stop_parsed is None or med.stop_date_parsed > latest_stop_parsed:
                    latest_stop_parsed = med.stop_date_parsed
                    latest_stop_raw = med.stop_date_raw

        deduped.append(CCDMedication(
            name=representative.name,
            code=representative.code,
            code_system=representative.code_system,
            start_date_raw=earliest_start_raw,
            start_date_parsed=earliest_start_parsed,
            stop_date_raw=None if any_active else latest_stop_raw,
            stop_date_parsed=None if any_active else latest_stop_parsed,
            is_active=any_active,
        ))

    return deduped


def dedup_conditions(conditions: list[CCDCondition]) -> list[CCDCondition]:
    """Deduplicate by SNOMED code.

    Keep the instance with earliest onset and latest resolution.
    If any instance is active (no resolution), result is active.
    """
    if not conditions:
        return []

    # Group by code (or description if no code)
    groups: dict[str, list[CCDCondition]] = {}
    for cond in conditions:
        key = cond.code if cond.code else cond.description.strip().lower()
        groups.setdefault(key, []).append(cond)

    deduped = []
    for key, group in groups.items():
        if len(group) == 1:
            deduped.append(group[0])
            continue

        # Find earliest onset and latest resolution
        earliest_onset_raw = None
        earliest_onset_parsed = None
        latest_resolution_raw = None
        latest_resolution_parsed = None
        any_active = False
        representative = group[0]

        for cond in group:
            if cond.onset_date_parsed:
                if earliest_onset_parsed is None or cond.onset_date_parsed < earliest_onset_parsed:
                    earliest_onset_parsed = cond.onset_date_parsed
                    earliest_onset_raw = cond.onset_date_raw

            if cond.is_active:
                any_active = True
            elif cond.resolution_date_parsed:
                if latest_resolution_parsed is None or cond.resolution_date_parsed > latest_resolution_parsed:
                    latest_resolution_parsed = cond.resolution_date_parsed
                    latest_resolution_raw = cond.resolution_date_raw

        deduped.append(CCDCondition(
            description=representative.description,
            code=representative.code,
            code_system=representative.code_system,
            onset_date_raw=earliest_onset_raw,
            onset_date_parsed=earliest_onset_parsed,
            resolution_date_raw=None if any_active else latest_resolution_raw,
            resolution_date_parsed=None if any_active else latest_resolution_parsed,
            is_active=any_active,
            is_clinical=representative.is_clinical,
        ))

    return deduped


def dedup_labs(labs: list[CCDLabResult]) -> list[CCDLabResult]:
    """For recurring panel types (same LOINC), keep only the most recent result.

    Returns (deduped_labs, prior_values_map) where prior_values_map contains
    prior values for trending context.
    """
    if not labs:
        return []

    # Group by panel LOINC
    groups: dict[str, list[CCDLabResult]] = {}
    for lab in labs:
        key = lab.panel_loinc if lab.panel_loinc else lab.panel_name
        groups.setdefault(key, []).append(lab)

    deduped = []
    for key, group in groups.items():
        # Sort by date descending
        sorted_group = sorted(
            group,
            key=lambda x: x.date_parsed or "",
            reverse=True,
        )

        most_recent = sorted_group[0]

        # If there's a prior result, annotate components with prior values
        if len(sorted_group) > 1:
            prior = sorted_group[1]
            prior_map = {}
            for comp in prior.components:
                if comp.loinc and comp.value:
                    prior_map[comp.loinc] = (comp.value, comp.date_parsed)

            # Annotate most_recent components are returned as-is
            # Prior values are tracked separately for the recency filter
            most_recent._prior_values = prior_map  # type: ignore[attr-defined]

        deduped.append(most_recent)

    return deduped


def get_most_recent_vitals_set(vitals: list[CCDVital], n_sets: int = 1) -> list[CCDVital]:
    """Get the most recent N complete vital sign sets.

    Groups vitals by date and returns the most recent N groups.
    """
    if not vitals:
        return []

    # Group by date
    by_date: dict[str, list[CCDVital]] = {}
    for v in vitals:
        date_key = v.date_parsed or "unknown"
        by_date.setdefault(date_key, []).append(v)

    # Sort dates descending
    sorted_dates = sorted(by_date.keys(), reverse=True)

    result = []
    for d in sorted_dates[:n_sets]:
        result.extend(by_date[d])

    return result


def get_vital_trends(vitals: list[CCDVital], n_sets: int = 3) -> dict[str, list[str]]:
    """Extract trending data for weight, BP, and A1c from the last N visit dates."""
    if not vitals:
        return {"weight": [], "bp_systolic": [], "bp_diastolic": []}

    # Group by date
    by_date: dict[str, dict[str, CCDVital]] = {}
    for v in vitals:
        date_key = v.date_parsed or "unknown"
        if date_key not in by_date:
            by_date[date_key] = {}
        if v.loinc:
            by_date[date_key][v.loinc] = v

    sorted_dates = sorted(by_date.keys(), reverse=True)[:n_sets]

    weights = []
    bp_values = []

    for d in sorted_dates:
        vitals_on_date = by_date[d]

        # Weight (LOINC 29463-7)
        if "29463-7" in vitals_on_date:
            w = vitals_on_date["29463-7"]
            weights.append(f"{w.value} {w.unit}" if w.value else "")

        # Systolic BP (LOINC 8480-6) + Diastolic (8462-4)
        sys_v = vitals_on_date.get("8480-6")
        dia_v = vitals_on_date.get("8462-4")
        if sys_v and dia_v:
            bp_values.append(f"{sys_v.value}/{dia_v.value}")

    return {
        "weight": weights,
        "bp": bp_values,
        "a1c": [],  # A1c comes from labs, not vitals
    }
