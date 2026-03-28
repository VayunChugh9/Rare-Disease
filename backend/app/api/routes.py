"""FastAPI routes for RefTriage."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.db_models import CorrectionRow, ReferralRow
from backend.app.services.pipeline import process_referral
from backend.app.services.pdf_generator import generate_summary_pdf

router = APIRouter(prefix="/api/referrals", tags=["referrals"])


def _normalize_urgency(raw: str | None) -> str:
    """Normalize triage urgency to lowercase_underscore format."""
    if not raw:
        return "needs_clarification"
    return raw.strip().lower().replace("-", "_").replace(" ", "_")


# ---------------------------------------------------------------------------
# Upload + process
# ---------------------------------------------------------------------------


@router.post("/upload")
async def upload_referral(
    file: Optional[UploadFile] = File(None),
    referral_note: Optional[UploadFile] = File(None),
    hie_file: Optional[UploadFile] = File(None),
    referral_specialty: Optional[str] = Form(None),
    referral_reason: Optional[str] = Form(None),
    referral_urgency: Optional[str] = Form(None),
    referring_provider_name: Optional[str] = Form(None),
    referring_provider_practice: Optional[str] = Form(None),
    referring_provider_phone: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload referral documents for processing.

    Supports two modes:
    - Single file via 'file' field (legacy)
    - Dual files: 'referral_note' (txt/pdf) + 'hie_file' (CCD/CCDA XML)
    """
    # Determine which files we have
    note_content = None
    note_filename = None
    hie_content = None
    hie_filename = None

    if referral_note:
        note_content = await referral_note.read()
        note_filename = referral_note.filename or "referral_note.txt"
    if hie_file:
        hie_content = await hie_file.read()
        hie_filename = hie_file.filename or "patient_hie.xml"
    if file:
        # Legacy single-file mode
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
        fname = file.filename or "unknown"
        # Auto-detect which slot it belongs to
        if fname.lower().endswith(".xml"):
            hie_content = content
            hie_filename = fname
        else:
            note_content = content
            note_filename = fname

    if not note_content and not hie_content:
        raise HTTPException(status_code=400, detail="At least one file is required")

    # Build optional referral context from form fields
    referral_info = None
    if any([referral_specialty, referral_reason, referral_urgency]):
        referral_info = {
            "receiving_specialty": referral_specialty,
            "reason": referral_reason,
            "urgency_stated": referral_urgency,
        }

    referring_provider = None
    if any([referring_provider_name, referring_provider_practice, referring_provider_phone]):
        referring_provider = {
            "name": referring_provider_name,
            "practice_name": referring_provider_practice,
            "phone": referring_provider_phone,
        }

    referral_id = process_referral(
        db,
        filename=note_filename or hie_filename or "unknown",
        content_bytes=note_content or b"",
        hie_filename=hie_filename,
        hie_content_bytes=hie_content,
        referral_info=referral_info,
        referring_provider=referring_provider,
    )

    return {"referral_id": referral_id, "status": "processing"}


# ---------------------------------------------------------------------------
# Status + detail
# ---------------------------------------------------------------------------


@router.get("/{referral_id}")
def get_referral(referral_id: str, db: Session = Depends(get_db)):
    """Get full referral data including extracted data, summary, and triage."""
    row = db.query(ReferralRow).filter(ReferralRow.id == referral_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Referral not found")

    return {
        "referral_id": row.id,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "one_line_summary": row.one_line_summary,
        "summary_narrative": row.summary_narrative,
        "triage": {
            "urgency": _normalize_urgency(row.triage_urgency),
            "confidence": row.triage_confidence,
            "reasoning": row.triage_reasoning,
            "red_flags": row.triage_red_flags or [],
            "action_items": row.triage_action_items or [],
            "missing_info": row.triage_missing_info or [],
        },
        "clinical_trial_flagged": row.clinical_trial_flagged,
        "clinical_trial_signals": row.clinical_trial_signals,
        "extracted_data": row.extracted_data,
    }


@router.get("/{referral_id}/status")
def get_referral_status(referral_id: str, db: Session = Depends(get_db)):
    """Lightweight status poll endpoint."""
    row = db.query(ReferralRow).filter(ReferralRow.id == referral_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Referral not found")

    return {
        "referral_id": row.id,
        "status": row.status,
        "triage_urgency": _normalize_urgency(row.triage_urgency),
    }


# ---------------------------------------------------------------------------
# Queue listing
# ---------------------------------------------------------------------------


@router.get("/")
def list_referrals(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List referrals with optional status filter."""
    query = db.query(ReferralRow).order_by(ReferralRow.created_at.desc())
    if status:
        query = query.filter(ReferralRow.status == status)
    rows = query.offset(offset).limit(limit).all()

    return {
        "total": query.count(),
        "referrals": [
            {
                "referral_id": r.id,
                "status": r.status,
                "one_line_summary": r.one_line_summary,
                "triage_urgency": _normalize_urgency(r.triage_urgency),
                "triage_confidence": r.triage_confidence,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------


@router.get("/{referral_id}/summary-pdf")
def get_summary_pdf(referral_id: str, db: Session = Depends(get_db)):
    """Generate a concise summary PDF for the referral."""
    row = db.query(ReferralRow).filter(ReferralRow.id == referral_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Referral not found")
    if row.status == "processing":
        raise HTTPException(status_code=409, detail="Referral is still processing")

    pdf_bytes = generate_summary_pdf(row)

    patient = (row.extracted_data or {}).get("patient", {})
    name = f"{patient.get('last_name', 'Unknown')}_{patient.get('first_name', '')}"
    filename = f"RefTriage_{name}_{referral_id[:8]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Finalize
# ---------------------------------------------------------------------------


@router.post("/{referral_id}/finalize")
def finalize_referral(referral_id: str, db: Session = Depends(get_db)):
    """Mark a referral as finalized."""
    row = db.query(ReferralRow).filter(ReferralRow.id == referral_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Referral not found")
    if row.status == "finalized":
        return {"referral_id": row.id, "status": "finalized", "message": "Already finalized"}

    row.status = "finalized"
    row.finalized_at = datetime.utcnow()
    db.commit()

    return {"referral_id": row.id, "status": "finalized"}


# ---------------------------------------------------------------------------
# Corrections
# ---------------------------------------------------------------------------


@router.post("/{referral_id}/corrections")
def add_correction(
    referral_id: str,
    correction: dict,
    db: Session = Depends(get_db),
):
    """Record a coordinator correction to extracted data."""
    row = db.query(ReferralRow).filter(ReferralRow.id == referral_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Referral not found")

    corr = CorrectionRow(
        referral_id=referral_id,
        field_path=correction.get("field_path", ""),
        original_value=correction.get("original_value"),
        corrected_value=correction.get("corrected_value"),
        correction_type=correction.get("correction_type", "value_change"),
        correction_reason=correction.get("reason"),
    )
    db.add(corr)
    db.commit()

    return {"correction_id": corr.id, "status": "saved"}
