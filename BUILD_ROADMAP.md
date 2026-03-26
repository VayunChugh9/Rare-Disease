# RefTriage — Build Roadmap

Test patient for all stages: `synthea_sample_data_ccda_latest/Bryant814_Bins636_aa4061cf-0f5e-b627-252d-9a705eac4e70.xml`

---

## Chunk 1: CCD Parser
Build `ccda_parser.py` and `date_parser.py` using `reftriage_mappings.md`. Parse the test patient XML into the CCD intermediate schema (schema 2 in `reftriage_schemas.json`).

**Pass when**: Script prints structured JSON with patient demographics, all medications with dates, all conditions with active/resolved status, lab values with units, vitals, social history, and screening scores extracted from the test file. No nulls for fields that exist in the XML.

## Chunk 2: Recency Filter + Dedup
Build `recency_filter.py` and `deduplicator.py` using schema 3 config. Takes chunk 1 output, produces canonical schema (schema 1).

**Pass when**: Duplicate medication renewals collapse into single entries. Non-clinical conditions (employment, education) route to social history. Only recent labs/vitals appear in primary output. Active vs resolved conditions are correctly separated.

## Chunk 3: LLM Summarization
Build `llm_summarization.py` using prompt 3 from `reftriage_prompts.md`. Takes canonical JSON, calls Claude Sonnet, returns summary output (schema 6).

**Pass when**: Returns valid JSON with narrative summary, triage recommendation, red flags, missing info, and screening interpretations for the test patient.

## Chunk 4: FastAPI Backend
Wire up upload → parse → filter → summarize → store pipeline. Postgres with schema 7 DDL. S3 stub (local filesystem for now).

**Pass when**: POST a CCD XML to `/api/referrals/upload`, poll status, GET returns complete extracted data + summary.

## Chunk 5: React Frontend
Build queue, upload, split-panel review screen, inline editing with correction capture.

**Pass when**: Upload test XML, see parsed summary render, edit a field, confirm correction is saved to database.
