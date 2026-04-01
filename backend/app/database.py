"""Database setup for RefTriage.

Uses SQLAlchemy with SQLite for development, Postgres-ready for production.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Default to SQLite in the project root for dev; override with DATABASE_URL for Postgres
_project_root = Path(__file__).resolve().parents[2]
_default_db = f"sqlite:///{_project_root / 'reftriage.db'}"
DATABASE_URL = os.getenv("DATABASE_URL", _default_db)

# Render provides postgres:// but SQLAlchemy requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    # SQLite needs check_same_thread=False for FastAPI's async usage
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yield a DB session, auto-close after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Call once at startup."""
    Base.metadata.create_all(bind=engine)
