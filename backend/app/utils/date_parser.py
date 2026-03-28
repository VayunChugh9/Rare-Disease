"""HL7 date format parser for CCD/CCDA documents.

Handles variable-precision HL7 dates: YYYYMMDDHHMMSS, YYYYMMDD, YYYYMM, YYYY.
"""

from datetime import date, datetime
from typing import Optional


def parse_hl7_date(raw: Optional[str]) -> Optional[str]:
    """Parse an HL7-format date string into ISO-8601 date (YYYY-MM-DD).

    Returns None for empty/missing input.
    """
    if not raw or not raw.strip():
        return None

    raw = raw.strip()

    # Remove any timezone suffix (e.g., +0000)
    if "+" in raw:
        raw = raw.split("+")[0]
    elif "-" in raw and len(raw) > 8:
        # Could be ISO format already or timezone offset
        pass

    try:
        length = len(raw)
        if length >= 8:
            # YYYYMMDD or longer
            return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
        elif length >= 6:
            # YYYYMM -> first of month
            return f"{raw[0:4]}-{raw[4:6]}-01"
        elif length >= 4:
            # YYYY -> first of year
            return f"{raw[0:4]}-01-01"
        else:
            return None
    except (ValueError, IndexError):
        return None


def parse_hl7_datetime(raw: Optional[str]) -> Optional[str]:
    """Parse an HL7-format date string into full ISO-8601 datetime if time is present,
    otherwise just the date portion."""
    if not raw or not raw.strip():
        return None

    raw = raw.strip()

    if "+" in raw:
        raw = raw.split("+")[0]

    try:
        length = len(raw)
        if length >= 14:
            return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}T{raw[8:10]}:{raw[10:12]}:{raw[12:14]}Z"
        elif length >= 8:
            return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
        elif length >= 6:
            return f"{raw[0:4]}-{raw[4:6]}-01"
        elif length >= 4:
            return f"{raw[0:4]}-01-01"
        else:
            return None
    except (ValueError, IndexError):
        return None


def parse_hl7_to_date_obj(raw: Optional[str]) -> Optional[date]:
    """Parse HL7 date string into a Python date object."""
    parsed = parse_hl7_date(raw)
    if not parsed:
        return None
    try:
        return date.fromisoformat(parsed)
    except ValueError:
        return None
