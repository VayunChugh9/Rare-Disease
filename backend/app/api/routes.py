"""FastAPI routes for RefTriage."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.db_models import CorrectionRow, ReferralRow
from backend.app.services.pipeline import process_referral

router = APIRouter(prefix="/api/referrals", tags=["referrals"])


# ---------------------------------------------------------------------------
# Upload + process
# ---------------------------------------------------------------------------


@router.post("/upload")
async def upload_referral(
    file: UploadFile = File(...),
    referral_specialty: Optional[str] = Form(None),
    referral_reason: Optional[str] = Form(None),
    referral_urgency: Optional[str] = Form(None),
    referring_provider_name: Optional[str] = Form(None),
    referring_provider_practice: Optional[str] = Form(None),
    referring_provider_phone: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload a referral document for processing.

    Accepts CCD/CCDA XML, plain text, or PDF files.
    Optional form fields provide referral context not in the document.
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

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
        filename=file.filename or "unknown",
        content_bytes=content,
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
            "urgency": row.triage_urgency,
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
        "triage_urgency": row.triage_urgency,
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
                "triage_urgency": r.triage_urgency,
                "triage_confidence": r.triage_confidence,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


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
