# RefTriage Agent State

## Current Phase
- Chunk 3 — LLM Summarization & Extraction
- Branch: `chunks-1-3`
- Objective: Verify `llm_summarization.py` and `llm_extraction.py` pass integration tests, then commit

## What Is Already Working
- **Chunk 1 (CCD Parser)**: `ccda_parser.py` + `date_parser.py` — verified via `test_ccda_parser.py`, all assertions pass
- **Chunk 2 (Recency Filter + Dedup)**: `recency_filter.py` + `deduplicator.py` — verified via `test_recency_filter.py`, all assertions pass
- **Pydantic schemas**: `schemas.py` with `CanonicalReferral` (schema 1), `CCDIntermediate` (schema 2), and `SummaryOutput` (schema 6)
- **Test patient data**: Bryant814 XML parses correctly, filters to canonical correctly
- **OpenAI client**: `openai_client.py` — loads API key from .env, exports `get_client()` and model constants

## What Is Implemented But Untested
- **`llm_summarization.py`** — `summarize_and_triage(canonical) -> SummaryOutput` using gpt-4o with JSON mode
- **`llm_extraction.py`** — `clean_text()` (gpt-4o-mini) + `extract_structured()` (gpt-4o with tool calling) → `CanonicalReferral`
- **`test_chunk3.py`** — Full integration test: connectivity, summarization pipeline, extraction pipeline

## Current Focus Files
- `backend/app/services/llm_summarization.py` — DONE, needs test run
- `backend/app/services/llm_extraction.py` — DONE, needs test run
- `backend/app/services/openai_client.py` — DONE
- `backend/app/models/schemas.py` — SummaryOutput model added
- `backend/tests/test_chunk3.py` — DONE, needs test run

## Constraints
- Architecture: Do not redesign — extend existing services layer
- Schema: Canonical schema (schema 1) is the system-wide contract, do not modify
- OpenAI models: `gpt-4o` for extraction + summarization, `gpt-4o-mini` for text cleaning
- PHI: Never log raw patient data or API keys
- Parse first, LLM second: CCD/XML parsing is deterministic, not LLM-based

## Environment Status
- `.env` has valid `OPENAI_API_KEY` (sk-proj-...TJYA, 164 chars)
- OpenAI connectivity confirmed working (previous session)
- Venv path: `./venv`, activate with `source venv/bin/activate`
- Python: `python` (via venv)
- Required packages: lxml, pydantic, openai, python-dotenv

## Git Status
- Branch: `chunks-1-3`
- Most recent commit: `e911b9a chunks 1-3: CCD parser, recency filter, LLM summarization`
- Uncommitted files: Chunk 3 service files + test + schema updates
- Next: run test_chunk3.py, fix failures, commit

## Key Files Map
| File | Purpose |
|------|---------|
| `backend/app/parsers/ccda_parser.py` | Chunk 1: CCD/CCDA XML → CCDIntermediate |
| `backend/app/utils/date_parser.py` | HL7 date parsing utility |
| `backend/app/services/recency_filter.py` | Chunk 2: CCDIntermediate → CanonicalReferral |
| `backend/app/services/deduplicator.py` | Chunk 2: Medication/condition/lab dedup |
| `backend/app/services/openai_client.py` | Shared OpenAI client + model constants |
| `backend/app/services/llm_summarization.py` | Chunk 3: CanonicalReferral → SummaryOutput |
| `backend/app/services/llm_extraction.py` | Chunk 3: Raw text → clean → CanonicalReferral |
| `backend/app/models/schemas.py` | All Pydantic models (schemas 1, 2, 6) |
| `backend/tests/test_ccda_parser.py` | Chunk 1 tests |
| `backend/tests/test_recency_filter.py` | Chunk 2 tests |
| `backend/tests/test_chunk3.py` | Chunk 3 tests |

## Test Patient Data
- XML: `synthea_sample_data_ccda_latest/Bryant814_Bins636_aa4061cf-0f5e-b627-252d-9a705eac4e70.xml`
- Referral text: `Bryant814_Bins636_referral_realistic.txt`
- Patient: Bryant814 Bins636, male, ~60yo, prediabetes + obesity + anemia
- Referral: Endocrinology from Dr. M. Chen at Walpole Primary Care
- Key findings: PHQ-9=18 (moderately severe), HARK=1 (violence), BMI>30

## Next Exact Steps
1. Run `test_chunk3.py` to verify all 3 tests pass
2. Fix any failures in LLM output validation
3. Git commit Chunk 3
4. Proceed to Chunk 4 (FastAPI Backend)

## Handoff Notes
- The `reftriage_prompts.md` specifies Claude models — we are using OpenAI instead
- Prompt text stays identical, only API wrapping changes
- Summarization uses JSON mode (`response_format={"type": "json_object"}`)
- Extraction uses tool/function calling with `EXTRACT_REFERRAL_TOOL` schema
- `_normalize_screening_interpretations()` handles LLM returning strings vs dicts
- Chunks 4-5 remain: FastAPI backend + React frontend
