"""SQLAlchemy ORM models for RefTriage (derived from schema 7 DDL)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.sqlite import JSON  # works for both SQLite and Postgres
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class SourceDocumentRow(Base):
    __tablename__ = "source_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(Text)
    mime_type: Mapped[str | None] = mapped_column(Text)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    document_format: Mapped[str] = mapped_column(String(30), nullable=False)
    extraction_path: Mapped[str] = mapped_column(String(30), nullable=False)
    ocr_text: Mapped[str | None] = mapped_column(Text)
    ocr_confidence_mean: Mapped[float | None] = mapped_column(Float)
    sections_found: Mapped[dict | None] = mapped_column(JSON)  # stored as JSON array
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class ReferralRow(Base):
    __tablename__ = "referrals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source_document_ids: Mapped[dict] = mapped_column(JSON, nullable=False)  # JSON array of UUIDs
    extracted_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    summary_narrative: Mapped[str | None] = mapped_column(Text)
    one_line_summary: Mapped[str | None] = mapped_column(Text)
    triage_urgency: Mapped[str] = mapped_column(String(30), nullable=False)
    triage_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    triage_reasoning: Mapped[str | None] = mapped_column(Text)
    triage_red_flags: Mapped[dict | None] = mapped_column(JSON)
    triage_missing_info: Mapped[dict | None] = mapped_column(JSON)
    triage_action_items: Mapped[dict | None] = mapped_column(JSON)
    clinical_trial_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    clinical_trial_signals: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        String(20), default="pending_review"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    reviewed_by: Mapped[str | None] = mapped_column(String(36))
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime)
    summary_pdf_key: Mapped[str | None] = mapped_column(Text)


class CorrectionRow(Base):
    __tablename__ = "corrections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    referral_id: Mapped[str] = mapped_column(String(36), nullable=False)
    field_path: Mapped[str] = mapped_column(Text, nullable=False)
    original_value: Mapped[dict | None] = mapped_column(JSON)
    corrected_value: Mapped[dict | None] = mapped_column(JSON)
    correction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    corrected_by: Mapped[str | None] = mapped_column(String(36))
    corrected_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    correction_reason: Mapped[str | None] = mapped_column(Text)


class AuditLogRow(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    resource_type: Mapped[str] = mapped_column(Text, nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(36))
    details: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
