# RefTriage Agent State

## Current Phase
- Chunk 5 — React Frontend (COMPLETE)
- Branch: `chunks-1-3`
- All 5 chunks implemented and verified

## What Is Working
- **Chunk 1 (CCD Parser)**: `ccda_parser.py` + `date_parser.py`
- **Chunk 2 (Recency Filter + Dedup)**: `recency_filter.py` + `deduplicator.py`
- **Chunk 3 (LLM Services)**: `llm_summarization.py` + `llm_extraction.py` + `openai_client.py`
- **Chunk 4 (FastAPI Backend)**: Full pipeline with SQLite, upload/status/detail/list/corrections endpoints
- **Chunk 5 (React Frontend)**: Queue dashboard, upload flow, split-panel review workspace

## Architecture
- **Path A (CCD/CCDA XML)**: Deterministic parse → recency filter → canonical → LLM summarize
- **Path B (Text/PDF)**: LLM clean text → LLM extract structured → canonical → LLM summarize
- **CCD is authoritative source** — referral note provides metadata only, not clinical data
- **Summarization sees full unbiased CCD picture** — not filtered by referral reason

## Key Files
| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI entry point |
| `backend/app/database.py` | SQLAlchemy setup (SQLite dev / Postgres prod) |
| `backend/app/api/routes.py` | REST endpoints |
| `backend/app/services/pipeline.py` | Upload → parse → filter → summarize → store |
| `backend/app/services/llm_summarization.py` | Canonical JSON → SummaryOutput (gpt-4o) |
| `backend/app/services/llm_extraction.py` | Raw text → clean → CanonicalReferral (gpt-4o) |
| `backend/app/services/openai_client.py` | Shared client + model constants |
| `backend/app/parsers/ccda_parser.py` | CCD/CCDA XML parser |
| `backend/app/services/recency_filter.py` | CCDIntermediate → CanonicalReferral |
| `backend/app/models/schemas.py` | Pydantic models (schemas 1, 2, 6) |
| `backend/app/models/db_models.py` | SQLAlchemy ORM (schema 7) |
| `frontend/src/App.tsx` | React Router setup |
| `frontend/src/api/client.ts` | API client |
| `frontend/src/components/queue/ReferralQueue.tsx` | Queue dashboard |
| `frontend/src/components/upload/UploadPanel.tsx` | Upload flow |
| `frontend/src/components/review/ReviewWorkspace.tsx` | Split-panel review |

## Running the App
```bash
# Backend
cd "Referral Triage" && source venv/bin/activate
python -m uvicorn backend.app.main:app --port 8000

# Frontend (separate terminal)
cd frontend && npm run dev
# → http://localhost:5173
```

## Environment
- `.env` has valid `OPENAI_API_KEY` (sk-proj-...TJYA)
- Venv: `./venv` with all deps installed
- Frontend: `./frontend/node_modules` with React, Tailwind, Vite
- Database: SQLite at `./reftriage.db` (auto-created on startup)

## Test Commands
```bash
# Chunk 1-3 tests (require OpenAI API key)
source venv/bin/activate
python backend/tests/test_ccda_parser.py
python backend/tests/test_recency_filter.py
python backend/tests/test_chunk3.py
python backend/tests/test_chunk4.py
```

## Next Steps (Post-MVP)
- Postgres + Docker Compose for production deployment
- WeasyPrint PDF generation
- Finalize/archive workflow
- Authentication + audit trail
- Patient trajectory tracking
- Multi-document merge (CCD + referral letter for same patient)
