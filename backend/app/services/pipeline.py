"""Referral processing pipeline for RefTriage.

Orchestrates: upload → detect format → parse/extract → filter → summarize → store.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.db_models import (
    AuditLogRow,
    ReferralRow,
    SourceDocumentRow,
)
from backend.app.models.schemas import (
    CanonicalReferral,
    ReferralInfo,
    ReferringProvider,
    SummaryOutput,
)
from backend.app.parsers.ccda_parser import parse_ccda
from backend.app.services.llm_extraction import clean_text, extract_structured
from backend.app.services.llm_summarization import summarize_and_triage
from backend.app.services.recency_filter import filter_to_canonical

logger = logging.getLogger(__name__)

# Local file storage root (S3 stub)
UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def detect_format(filename: str, content_bytes: bytes) -> str:
    """Detect document format from filename and content."""
    lower = filename.lower()
    if lower.endswith(".xml"):
        # Check if it's CCD/CCDA
        head = content_bytes[:2000].decode("utf-8", errors="ignore")
        if "ClinicalDocument" in head or "urn:hl7-org:v3" in head:
            return "ccda_xml"
        return "ccda_xml"  # assume XML is CCDA for now
    elif lower.endswith(".json"):
        return "fhir_json"
    elif lower.endswith(".pdf"):
        return "pdf_typed"
    elif lower.endswith(".txt"):
        return "plain_text"
    return "plain_text"


def process_referral(
    db: Session,
    filename: str,
    content_bytes: bytes,
    *,
    hie_filename: Optional[str] = None,
    hie_content_bytes: Optional[bytes] = None,
    referral_info: Optional[dict] = None,
    referring_provider: Optional[dict] = None,
) -> str:
    """Process referral document(s) end-to-end.

    Args:
        db: Database session.
        filename: Original filename of referral note.
        content_bytes: Raw file bytes of referral note.
        hie_filename: Optional HIE/CCDA filename.
        hie_content_bytes: Optional HIE/CCDA file bytes.
        referral_info: Optional dict with referral context (specialty, reason, etc.).
        referring_provider: Optional dict with referring provider info.

    Returns:
        Referral ID (UUID string) for status polling.
    """
    referral_id = str(uuid.uuid4())
    storage_path = UPLOAD_DIR / referral_id
    storage_path.mkdir(parents=True, exist_ok=True)

    doc_ids = []

    # Store referral note if provided
    if content_bytes:
        doc_format = detect_format(filename, content_bytes)
        (storage_path / filename).write_bytes(content_bytes)
        doc_id = str(uuid.uuid4())
        db.add(SourceDocumentRow(
            id=doc_id,
            storage_key=f"{referral_id}/{filename}",
            original_filename=filename,
            mime_type=_guess_mime(filename),
            file_size_bytes=len(content_bytes),
            document_format=doc_format,
            extraction_path="llm_extraction" if doc_format != "ccda_xml" else "structured_parse",
        ))
        doc_ids.append(doc_id)

    # Store HIE/CCDA file if provided
    if hie_content_bytes and hie_filename:
        (storage_path / hie_filename).write_bytes(hie_content_bytes)
        hie_doc_id = str(uuid.uuid4())
        db.add(SourceDocumentRow(
            id=hie_doc_id,
            storage_key=f"{referral_id}/{hie_filename}",
            original_filename=hie_filename,
            mime_type=_guess_mime(hie_filename),
            file_size_bytes=len(hie_content_bytes),
            document_format="ccda_xml",
            extraction_path="structured_parse",
        ))
        doc_ids.append(hie_doc_id)

    # Create referral row in "processing" status
    ref_row = ReferralRow(
        id=referral_id,
        source_document_ids=doc_ids,
        extracted_data={},
        triage_urgency="needs_clarification",
        triage_confidence=0.0,
        status="processing",
    )
    db.add(ref_row)
    db.commit()

    logger.info("Referral %s: processing (note=%s, hie=%s)", referral_id, filename, hie_filename)

    try:
        # --- Step 2: Parse/Extract ---
        canonical = None

        # Process HIE/CCDA first (structured data)
        if hie_content_bytes and hie_filename:
            canonical = _process_ccda(hie_content_bytes, hie_filename)

        # Process referral note (unstructured)
        if content_bytes and detect_format(filename, content_bytes) != "ccda_xml":
            note_canonical = _process_unstructured(content_bytes, filename)
            if canonical:
                # Merge: note data fills gaps in CCDA data
                canonical = _merge_canonical(canonical, note_canonical)
            else:
                canonical = note_canonical
        elif content_bytes and not canonical:
            # Only file is CCDA
            canonical = _process_ccda(content_bytes, filename)

        if not canonical:
            raise ValueError("No processable content found")

        # --- Step 2b: Inject referral context if provided ---
        if referral_info:
            canonical.referral = ReferralInfo.model_validate(referral_info)
        if referring_provider:
            canonical.referring_provider = ReferringProvider.model_validate(
                referring_provider
            )

        # --- Step 3: Summarize ---
        summary = summarize_and_triage(canonical)

        # --- Step 4: Store results ---
        _store_results(db, ref_row, canonical, summary)

        # Audit log
        db.add(AuditLogRow(
            action="referral_processed",
            resource_type="referral",
            resource_id=referral_id,
            details={"filename": filename, "format": doc_format},
        ))
        db.commit()

        logger.info("Referral %s: processing complete", referral_id)

    except Exception:
        logger.exception("Referral %s: processing failed", referral_id)
        ref_row.status = "pending_review"
        ref_row.triage_reasoning = "Processing failed — requires manual review"
        db.commit()
        raise

    return referral_id


def _merge_canonical(primary: CanonicalReferral, secondary: CanonicalReferral) -> CanonicalReferral:
    """Merge two canonical referrals. Primary (CCDA) is authoritative; secondary (note) fills gaps."""
    # Fill missing top-level fields from secondary
    if not primary.referral and secondary.referral:
        primary.referral = secondary.referral
    elif primary.referral and secondary.referral:
        # Merge referral fields
        for field in ("receiving_specialty", "reason", "clinical_question", "urgency_stated"):
            if not getattr(primary.referral, field) and getattr(secondary.referral, field):
                setattr(primary.referral, field, getattr(secondary.referral, field))

    if not primary.referring_provider and secondary.referring_provider:
        primary.referring_provider = secondary.referring_provider

    if not primary.patient and secondary.patient:
        primary.patient = secondary.patient
    elif primary.patient and secondary.patient:
        for field in ("age", "insurance"):
            if not getattr(primary.patient, field) and getattr(secondary.patient, field):
                setattr(primary.patient, field, getattr(secondary.patient, field))

    return primary


def _process_ccda(content_bytes: bytes, filename: str) -> CanonicalReferral:
    """Path A: Deterministic CCD/CCDA XML parse → filter → canonical."""
    intermediate = parse_ccda(content_bytes)
    canonical = filter_to_canonical(intermediate, filename=filename)
    return canonical


def _process_unstructured(content_bytes: bytes, filename: str) -> CanonicalReferral:
    """Path B: LLM extraction for unstructured documents."""
    raw_text = content_bytes.decode("utf-8", errors="replace")
    cleaned = clean_text(raw_text)
    canonical = extract_structured(cleaned, source_filename=filename)
    return canonical


def _store_results(
    db: Session,
    ref_row: ReferralRow,
    canonical: CanonicalReferral,
    summary: SummaryOutput,
) -> None:
    """Persist canonical data and summary to the referral row."""
    ref_row.extracted_data = canonical.model_dump(mode="json", exclude_none=True)
    ref_row.summary_narrative = summary.summary_narrative
    ref_row.one_line_summary = summary.one_line_summary

    tr = summary.triage_recommendation
    if tr:
        raw_urgency = (tr.urgency or "needs_clarification").strip().lower().replace("-", "_").replace(" ", "_")
        ref_row.triage_urgency = raw_urgency
        ref_row.triage_confidence = tr.confidence or 0.0
        ref_row.triage_reasoning = tr.reasoning
        ref_row.triage_red_flags = tr.red_flags
        ref_row.triage_action_items = tr.action_items
    ref_row.triage_missing_info = summary.missing_information

    ct = summary.clinical_trial_relevance
    if ct:
        ref_row.clinical_trial_flagged = ct.potentially_eligible
        ref_row.clinical_trial_signals = ct.model_dump(mode="json")

    ref_row.status = "pending_review"


def _guess_mime(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".xml"):
        return "application/xml"
    if lower.endswith(".json"):
        return "application/json"
    if lower.endswith(".pdf"):
        return "application/pdf"
    if lower.endswith(".txt"):
        return "text/plain"
    return "application/octet-stream"
