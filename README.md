# RefTriage — Developer Context Guide

> **For Claude Code / Cursor**: This file tells you which reference doc to read when building each component. Load all four files (`REFTRIAGE_SPEC.md`, `reftriage_schemas.json`, `reftriage_mappings.md`, `reftriage_prompts.md`) into context, then use this guide to navigate.

---

## File → source code mapping

### `REFTRIAGE_SPEC.md`
**Read this first.** Product overview, architecture, tech stack, project structure, development phases. Gives you the full picture before you build anything.

### `reftriage_schemas.json`
Contains 7 numbered schemas. Here's what each one builds:

| Schema | Builds | Source files |
|---|---|---|
| `1_canonical_output_schema` | Pydantic models for the core data contract. Also the tool use schema for LLM extraction (see prompts.md). | `backend/app/models/schemas.py`, `frontend/src/types/referral.ts` |
| `2_ccd_intermediate_schema` | Pydantic models for raw CCD parser output (before filtering). | `backend/app/models/schemas.py` (separate class) |
| `3_recency_filter_config` | Business logic config — NOT a data model. Drives the filtering, dedup, and tier classification. | `backend/app/services/recency_filter.py`, `backend/app/services/deduplicator.py`, `backend/app/config.py` |
| `4_correction_record_schema` | Correction capture on field edits. | `backend/app/models/database.py` (corrections table), `frontend/src/components/InlineEditor.tsx` |
| `5_patient_trajectory_schema` | De-identified analytics records created on finalization. | `backend/app/services/deidentification.py`, `backend/app/models/database.py` |
| `6_summary_output_schema` | Expected JSON output from the summarization LLM call. Parse and validate against this. | `backend/app/services/llm_summarization.py`, `frontend/src/components/StructuredSummary.tsx` |
| `7_database_ddl` | Copy the SQL directly into your migration. | Database init script or Alembic migration |

### `reftriage_mappings.md`
**Single-purpose file.** Everything needed to build the CCD/CCDA XML parser.

| Section | Builds |
|---|---|
| §1 Namespace setup | Top of `ccda_parser.py` — the NAMESPACES dict |
| §2 Date format | `backend/app/utils/date_parser.py` |
| §3.1–3.13 Section extractions | Core of `ccda_parser.py` — one function per section |
| §4 Code system OIDs | Lookup dict in `ccda_parser.py` or `backend/app/models/enums.py` |
| §5 Screening interpretation | `backend/app/services/llm_summarization.py` (reference table), `frontend/src/components/ScreeningScoreCard.tsx` |
| §6 Common pitfalls | Read before writing any parser code — saves debugging time |

### `reftriage_prompts.md`
LLM integration layer. Each prompt maps to a specific service function.

| Prompt | Builds | Source file |
|---|---|---|
| Prompt 1: Text cleaning | `clean_text()` function, Haiku call | `backend/app/services/llm_extraction.py` |
| Prompt 2: Structured extraction | `extract_structured()` function, Sonnet call with tool use | `backend/app/services/llm_extraction.py` |
| Prompt 3: Summarization + triage | `summarize_and_triage()` function, Sonnet call | `backend/app/services/llm_summarization.py` |
| Prompt 4: Synthetic letter gen | Test data generation script only | `backend/scripts/generate_synthetic_referrals.py` |
| Tool use config section | How to wire up the extraction tool call | `backend/app/services/llm_extraction.py` |
| Token budget section | Cost estimation, model selection | `backend/app/config.py` |

---

## Build order

Follow this sequence — each step depends on the one before it.

**Step 1**: `models/schemas.py` — Pydantic models from schemas 1 and 2. Everything else imports these.

**Step 2**: Database init — Run the DDL from schema 7. Set up Docker + Postgres.

**Step 3**: `parsers/ccda_parser.py` + `utils/date_parser.py` — Build from `reftriage_mappings.md`. Test against the Synthea XML fixtures in `/tests/fixtures/ccda/`.

**Step 4**: `services/recency_filter.py` + `services/deduplicator.py` — Build from schema 3. Takes CCD intermediate output, produces canonical schema output.

**Step 5**: `services/llm_extraction.py` — Build from prompts 1 and 2. Only needed for PDF/text path.

**Step 6**: `services/llm_summarization.py` — Build from prompt 3. Takes canonical JSON (from either path), returns summary output schema.

**Step 7**: API endpoints — Wire up FastAPI routes connecting upload → parse/extract → summarize → store.

**Step 8**: Frontend — React components referencing the canonical schema types.

---

## Key concept: the canonical schema is shared

The canonical output schema (`schemas.json` section 1) appears in three places and must stay in sync:

1. **Pydantic model** in `schemas.py` — used for validation throughout the backend
2. **Tool use schema** in the extraction prompt — Claude outputs JSON matching this structure
3. **TypeScript types** in `referral.ts` — frontend renders and edits this data

If you change the schema, update all three. The Pydantic model is the source of truth.
