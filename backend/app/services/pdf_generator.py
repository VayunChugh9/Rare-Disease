"""Generate a concise summary PDF from a ReferralRow using WeasyPrint."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from weasyprint import HTML


def _val(obj: dict | None, *keys: str, default: str = "N/A") -> str:
    """Safely traverse nested dict keys."""
    current: Any = obj
    for k in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(k)
    return str(current) if current is not None else default


def _build_html(row: Any) -> str:
    """Build the HTML string for the PDF."""
    ed = row.extracted_data or {}
    patient = ed.get("patient", {}) or {}
    referral = ed.get("referral", {}) or {}
    provider = ed.get("referring_provider", {}) or {}
    cd = ed.get("clinical_data", {}) or {}

    name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() or "Unknown Patient"
    age_sex = " / ".join(filter(None, [
        f"{patient['age']}y" if patient.get("age") else None,
        patient.get("sex", "").upper()[:1] if patient.get("sex") else None,
    ]))
    dob = patient.get("date_of_birth", "N/A")
    mrn = patient.get("mrn", "N/A")

    urgency = (row.triage_urgency or "unknown").replace("_", " ").title()
    confidence = f"{(row.triage_confidence or 0) * 100:.0f}%"
    urgency_color = {
        "urgent": "#DC2626", "semi_urgent": "#EA580C", "routine": "#0D9488",
        "needs_clarification": "#CA8A04", "inappropriate": "#6B7280",
    }.get(row.triage_urgency, "#6B7280")

    # Red flags
    red_flags = row.triage_red_flags or []
    red_flags_html = "".join(f"<li>{rf}</li>" for rf in red_flags) if red_flags else "<li>None identified</li>"

    # Action items
    action_items = row.triage_action_items or []
    action_items_html = "".join(f"<li>{ai}</li>" for ai in action_items) if action_items else "<li>None</li>"

    # Missing info
    missing = row.triage_missing_info or []
    missing_html = "".join(f"<li>{m}</li>" for m in missing) if missing else "<li>None</li>"

    # Active conditions (limit to 8)
    conditions = (cd.get("problem_list", {}) or {}).get("active", []) or []
    cond_display = conditions[:8]
    conditions_html = "".join(
        f"<li>{c.get('diagnosis', 'Unknown')}{' (' + c['code'] + ')' if c.get('code') else ''}</li>"
        for c in cond_display
    ) if cond_display else "<li>None listed</li>"
    if len(conditions) > 8:
        conditions_html += f"<li style='color:#94a3b8;'>+{len(conditions) - 8} more</li>"

    # Active medications (limit to 6)
    meds = (cd.get("medications", {}) or {}).get("active", []) or []
    meds_display = meds[:6]
    meds_html = "".join(
        f"<li>{m.get('name', 'Unknown')}{' ' + m['dose'] if m.get('dose') else ''}"
        f"{' ' + m['frequency'] if m.get('frequency') else ''}</li>"
        for m in meds_display
    ) if meds_display else "<li>None listed</li>"
    if len(meds) > 6:
        meds_html += f"<li style='color:#94a3b8;'>+{len(meds) - 6} more</li>"

    # Allergies
    allergies_data = cd.get("allergies", {}) or {}
    known_allergies = allergies_data.get("known_allergies", []) or []
    if allergies_data.get("no_known_allergies"):
        allergies_html = "<li>No known allergies</li>"
    elif known_allergies:
        allergies_html = "".join(
            f"<li>{a.get('substance', 'Unknown')}"
            f"{' - ' + a['reaction'] if a.get('reaction') else ''}</li>"
            for a in known_allergies
        )
    else:
        allergies_html = "<li>Not documented</li>"

    # Vitals
    vitals = cd.get("recent_vitals", {}) or {}
    vitals_rows = ""
    for label, key in [("BP", "blood_pressure"), ("HR", "heart_rate"), ("BMI", "bmi"),
                        ("Weight", "weight"), ("Temp", "temperature"), ("SpO2", "oxygen_saturation")]:
        val = vitals.get(key)
        if val:
            vitals_rows += f"<tr><td>{label}</td><td>{val}</td></tr>"
    if not vitals_rows:
        vitals_rows = "<tr><td colspan='2'>No recent vitals</td></tr>"

    # Labs (most recent abnormal)
    labs = cd.get("recent_labs", []) or []
    abnormal_labs = []
    for panel in labs:
        for result in panel.get("results", []):
            if result.get("flag") in ("abnormal", "critical"):
                abnormal_labs.append(f"{result.get('test_name', '?')}: {result.get('value', '?')} {result.get('unit', '')} ({result.get('flag', '')})")
    labs_html = "".join(f"<li>{l}</li>" for l in abnormal_labs[:8]) if abnormal_labs else "<li>No abnormal results</li>"

    # Screenings (deduplicate by instrument, keep most recent, limit to 6)
    screenings_raw = cd.get("screenings", []) or []
    seen_instruments: dict[str, dict] = {}
    for s in screenings_raw:
        key = s.get("instrument", "?")
        existing = seen_instruments.get(key)
        if not existing or (s.get("date", "") > existing.get("date", "")):
            seen_instruments[key] = s
    screenings = list(seen_instruments.values())[:6]
    screenings_html = "".join(
        f"<li>{s.get('instrument', '?')}: {s.get('score', '?')}"
        f"{' - ' + s['interpretation'] if s.get('interpretation') else ''}</li>"
        for s in screenings
    ) if screenings else "<li>None documented</li>"

    generated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Truncate summary to ~400 chars for single-page fit
    summary_text = row.summary_narrative or ""
    if len(summary_text) > 400:
        summary_text = summary_text[:397] + "..."

    return f"""<!DOCTYPE html>
<html>
<head>
<style>
    @page {{ size: letter; margin: 0.4in 0.5in; }}
    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 8pt; color: #1e293b; line-height: 1.35; }}
    h1 {{ font-size: 14pt; color: #0D9488; margin: 0 0 1pt; }}
    h2 {{ font-size: 8.5pt; color: #334155; border-bottom: 1px solid #e2e8f0; padding-bottom: 2pt; margin: 8pt 0 3pt; text-transform: uppercase; letter-spacing: 0.5pt; }}
    .referral-reason {{ background: #f0fdfa; border: 1.5px solid #0D9488; border-radius: 4pt; padding: 6pt 10pt; margin: 6pt 0 4pt; }}
    .referral-reason h2 {{ font-size: 9pt; color: #0D9488; border: none; margin: 0 0 2pt; padding: 0; }}
    .referral-reason p {{ font-size: 9.5pt; font-weight: 600; color: #0F172A; margin: 0; line-height: 1.4; }}
    .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #0D9488; padding-bottom: 6pt; margin-bottom: 6pt; }}
    .header-left {{ flex: 1; }}
    .header-right {{ text-align: right; }}
    .badge {{ display: inline-block; padding: 2pt 8pt; border-radius: 3pt; color: white; font-weight: bold; font-size: 8pt; }}
    .meta {{ color: #64748b; font-size: 7pt; }}
    .three-col {{ display: flex; gap: 12pt; }}
    .three-col > div {{ flex: 1; }}
    .two-col {{ display: flex; gap: 12pt; }}
    .two-col > div {{ flex: 1; }}
    ul {{ margin: 1pt 0; padding-left: 12pt; }}
    li {{ margin-bottom: 1pt; font-size: 7.5pt; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 7.5pt; }}
    td {{ padding: 1pt 4pt; border-bottom: 1px solid #f1f5f9; }}
    td:first-child {{ font-weight: 600; width: 40pt; color: #64748b; }}
    .summary {{ background: #f8fafc; padding: 5pt 8pt; border-left: 3px solid #0D9488; margin: 4pt 0; font-size: 7.5pt; line-height: 1.3; }}
    .red-flag {{ color: #DC2626; }}
    .footer {{ margin-top: 8pt; padding-top: 4pt; border-top: 1px solid #e2e8f0; font-size: 6pt; color: #94a3b8; text-align: center; }}
</style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            <h1>{name}</h1>
            <div class="meta">{age_sex} &bull; DOB: {dob} &bull; MRN: {mrn}</div>
            <div class="meta">To: {referral.get('receiving_specialty', 'N/A')} &bull; From: {provider.get('name', 'N/A')}{', ' + provider['practice_name'] if provider.get('practice_name') else ''}</div>
        </div>
        <div class="header-right">
            <div class="badge" style="background:{urgency_color};">{urgency}</div>
            <div class="meta" style="margin-top:2pt;">Confidence: {confidence}</div>
        </div>
    </div>

    {f'<div class="referral-reason"><h2>REASON FOR REFERRAL</h2><p>{referral.get("reason", "")}</p></div>' if referral.get('reason') else ''}

    <div class="two-col">
        <div>
            <h2 class="red-flag">Red Flags</h2>
            <ul class="red-flag">{red_flags_html}</ul>
        </div>
        <div>
            <h2>Action Items</h2>
            <ul>{action_items_html}</ul>
        </div>
    </div>

    {f'<div class="summary">{summary_text}</div>' if summary_text else ''}

    <div class="three-col">
        <div>
            <h2>Active Conditions</h2>
            <ul>{conditions_html}</ul>

            <h2>Allergies</h2>
            <ul>{allergies_html}</ul>
        </div>
        <div>
            <h2>Medications</h2>
            <ul>{meds_html}</ul>

            <h2>Screenings</h2>
            <ul>{screenings_html}</ul>
        </div>
        <div>
            <h2>Vitals</h2>
            <table>{vitals_rows}</table>

            <h2>Abnormal Labs</h2>
            <ul>{labs_html}</ul>

            <h2>Missing Info</h2>
            <ul>{missing_html}</ul>
        </div>
    </div>

    <div class="footer">
        Antechamber Health &bull; RefTriage AI Summary &bull; {generated} &bull; Verify all information before clinical decisions.
    </div>
</body>
</html>"""


def generate_summary_pdf(row: Any) -> bytes:
    """Generate PDF bytes from a ReferralRow."""
    html_str = _build_html(row)
    return HTML(string=html_str).write_pdf()
