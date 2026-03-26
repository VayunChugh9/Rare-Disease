# RefTriage Agent State

## Current Phase
- Chunk 3 — LLM Summarization & Extraction
- Branch: `chunks-1-3`
- Objective: Implement `llm_summarization.py` and `llm_extraction.py` using OpenAI

## What Is Already Working
- **Chunk 1 (CCD Parser)**: `ccda_parser.py` + `date_parser.py` — verified via `test_ccda_parser.py`, all assertions pass
- **Chunk 2 (Recency Filter + Dedup)**: `recency_filter.py` + `deduplicator.py` — verified via `test_recency_filter.py`, all assertions pass
- **Pydantic schemas**: `schemas.py` with `CanonicalReferral` (schema 1) and `CCDIntermediate` (schema 2) models
- **Test patient data**: Bryant814 XML parses correctly, filters to canonical correctly

## What Is Partially Implemented
- `.env` has `OPENAI_API_KEY=your-key-here` (placeholder, not a real key)
- `openai` package now installed in venv but connectivity not yet verified

## Current Focus Files
- `backend/app/services/llm_summarization.py` (to be created)
- `backend/app/services/llm_extraction.py` (to be created)
- `backend/app/services/openai_client.py` (to be created)
- `backend/app/models/schemas.py` (adding SummaryOutput model)
- `backend/tests/test_chunk3.py` (to be created)

## Constraints
- Architecture: Do not redesign — extend existing services layer
- Schema: Canonical schema (schema 1) is the system-wide contract, do not modify
- OpenAI models: `gpt-4o` for extraction + summarization, `gpt-4o-mini` for text cleaning
- PHI: Never log raw patient data or API keys
- Parse first, LLM second: CCD/XML parsing is deterministic, not LLM-based

## Environment Status
- `.env` loads via `python-dotenv` — key is placeholder, needs real key
- `OPENAI_API_KEY` present but not yet valid
- OpenAI connectivity NOT yet verified
- Venv path: `./venv`, activate with `source venv/bin/activate`
- Python: `python` (via venv)

## Git Status
- Branch: `chunks-1-3`
- Most recent commit: `e911b9a chunks 1-3: CCD parser, recency filter, LLM summarization`
- Repo is clean (no uncommitted changes except untracked `opencode.json`)
- Next: checkpoint after initial setup

## Outstanding Issues
- `.env` has placeholder API key — must be updated before integration tests
- No `SummaryOutput` Pydantic model yet (schema 6)
- No LLM service files exist

## Next Exact Steps
1. Add `SummaryOutput` model to `schemas.py`
2. Create `openai_client.py` shared client
3. Create `llm_summarization.py`
4. Create `llm_extraction.py`
5. Create `test_chunk3.py`
6. Verify OpenAI connectivity with real key
7. Run integration tests
8. Git checkpoint at each milestone

## Handoff Notes
- The `reftriage_prompts.md` specifies Claude models — we are using OpenAI instead
- Prompt text stays identical, only API wrapping changes
- Test patient: `Bryant814_Bins636_aa4061cf-0f5e-b627-252d-9a705eac4e70.xml`
- Referral text for extraction testing: `Bryant814_Bins636_referral_realistic.txt`
