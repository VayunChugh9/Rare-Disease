"""Shared OpenAI client initialization for RefTriage.

Loads .env, validates OPENAI_API_KEY is present, and exports
a configured OpenAI client instance.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Load .env from the project root
_project_root = Path(__file__).resolve().parents[3]  # backend/app/services -> repo root
_env_path = _project_root / ".env"
load_dotenv(_env_path)

_api_key = os.getenv("OPENAI_API_KEY")

if not _api_key or _api_key == "your-key-here":
    print(
        "ERROR: OPENAI_API_KEY is missing or still set to placeholder in .env",
        file=sys.stderr,
    )
    _client: OpenAI | None = None
else:
    # Confirm key is loaded without exposing the raw secret
    _masked = _api_key[:8] + "..." + _api_key[-4:]
    print(f"OpenAI API key loaded: {_masked}")
    _client = OpenAI(api_key=_api_key)


def get_client() -> OpenAI:
    """Return the shared OpenAI client, raising if not configured."""
    if _client is None:
        raise RuntimeError(
            "OpenAI client not initialized. "
            "Set a valid OPENAI_API_KEY in .env and restart."
        )
    return _client


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
MODEL_EXTRACTION = "gpt-4o"
MODEL_SUMMARIZATION = "gpt-4o"
MODEL_CLEANING = "gpt-4o-mini"
