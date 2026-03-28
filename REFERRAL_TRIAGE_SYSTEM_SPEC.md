# RefTriage — Referral Triage & Summary System

> **Purpose**: This document is the single source of truth for building the RefTriage MVP. It is designed to be loaded as primary context into Claude Code or Cursor for AI-assisted development. Every architectural decision, schema definition, and implementation detail needed to build the system is contained here.

---

## 1. Product overview

RefTriage is a web application that ingests clinical referral documents (faxed PDFs, typed notes, free text), extracts and structures patient data using LLMs, generates a triage recommendation with confidence scoring, and produces a concise summary PDF with provenance back to source documents. The primary user is a **referral coordinator** (non-clinical staff) processing 20–50 referrals per day at a general-practice clinic.

### Core value proposition

- Reduce referral intake time from 15–20 minutes to 2–3 minutes per referral
- Surface missing information proactively so coordinators can request it upfront
- Standardize triage decisions across staff with auditable, AI-assisted classification
- Build a proprietary dataset of patient trajectories and labeled correction data

### Design principles

- **Human-in-the-loop always**: The system assists triage, never automates it. Every AI output requires coordinator review before finalization.
- **Fail loudly on missing data**: Never hallucinate or infer. If a field can't be extracted, flag it as missing — showing gaps is a feature.
- **Acquisition-ready architecture**: All data storage, schemas, and pipelines are designed for flexibility, portability, and eventual sale of de-identified datasets or the platform itself.
- **Progressive integration**: MVP is standalone web app. Architecture supports future EHR embedding and live HIE queries without rewrites.

---

## 2. System architecture

### Pipeline stages

```
[Fax/PDF Upload] → [OCR + Text Extraction] → [LLM Structured Extraction]
       ↓                                              ↓
[Patient Match/Register] ← ─ ─ ─ ─ ─ ─ ─ ─ ─  [Canonical JSON]
       ↓
[Query HIE / Retrieve Records]  ← (simulated for MVP)
       ↓
[Normalize to Canonical Schema]
       ↓
[Triage Classification]
       ↓
[Coordinator Review UI]  →  [Summary PDF with Provenance]
       ↑                           ↓
       └── Correction Feedback ────┘
```

### MVP scope

**In scope**: PDF upload, plain text input, OCR (typed + handwritten), LLM extraction to canonical JSON, triage classification, coordinator review/override UI, summary PDF generation, correction data capture, de-identified data storage.

**Out of scope (architected for but not built)**: Live HIE integration (Carequality/CommonWell), real patient matching (MPI), EHR embedding, FHIR/HL7 message ingestion, multi-user auth/roles, scheduling integration, analytics dashboards.

### Tech stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | React + TypeScript | Component-based, large ecosystem, familiar |
| Backend API | FastAPI (Python) | Async, type-safe, fast iteration, strong health-tech library ecosystem |
| LLM | Anthropic Claude API (tool use / structured output) | Best extraction quality, structured JSON output via tool use, BAA available |
| OCR | Google Cloud Document AI | Handles handwritten + typed, confidence scores, free tier for MVP |
| PDF generation | WeasyPrint or ReportLab | Python-native, supports HTML-to-PDF for templated summaries |
| Database | PostgreSQL | JSONB for flexible schemas, strong encryption support, production-grade |
| Object storage | S3-compatible (AWS S3 or MinIO for local dev) | Source document storage with server-side encryption |
| Auth | Supabase Auth or Auth0 (post-MVP) | Not needed for MVP with synthetic data; stub the auth layer |
| Deployment | Docker → AWS ECS or Railway | Containerized from day one |

---

## 3. Data architecture

### 3.1 Canonical output schema

This is the target schema for every referral, regardless of input format. Every field except those in the `required` group is nullable. The LLM extraction prompt enforces this schema via Claude's tool use.

```json
{
  "referral_id": "uuid",
  "ingested_at": "ISO-8601 timestamp",
  "source_document_ids": ["uuid"],

  "patient": {
    "first_name": "string | null",
    "last_name": "string | null",
    "date_of_birth": "YYYY-MM-DD | null",
    "sex": "M | F | Other | null",
    "mrn": "string | null",
    "insurance": {
      "plan_name": "string | null",
      "member_id": "string | null",
      "group_number": "string | null"
    },
    "contact": {
      "phone": "string | null",
      "address": "string | null"
    }
  },

  "referring_provider": {
    "name": "string",
    "npi": "string | null",
    "practice_name": "string | null",
    "phone": "string | null",
    "fax": "string | null"
  },

  "referral": {
    "receiving_specialty": "string | null",
    "receiving_provider": "string | null",
    "reason": "string — free text summary of why referred",
    "clinical_question": "string | null — specific question the referring provider is asking",
    "urgency_stated": "string | null — urgency as stated in the referral document",
    "date_of_referral": "YYYY-MM-DD | null"
  },

  "clinical_data": {
    "problem_list": [
      {
        "diagnosis": "string",
        "icd10": "string | null",
        "status": "active | resolved | null",
        "onset_date": "string | null"
      }
    ],
    "medications": [
      {
        "name": "string",
        "dose": "string | null",
        "frequency": "string | null",
        "rxnorm": "string | null"
      }
    ],
    "allergies": [
      {
        "substance": "string",
        "reaction": "string | null",
        "severity": "string | null"
      }
    ],
    "recent_labs": [
      {
        "test_name": "string",
        "value": "string",
        "unit": "string | null",
        "reference_range": "string | null",
        "date": "YYYY-MM-DD | null",
        "flag": "normal | abnormal | critical | null"
      }
    ],
    "recent_imaging": [
      {
        "modality": "string — e.g. MRI, CT, X-ray",
        "body_part": "string | null",
        "findings_summary": "string",
        "date": "YYYY-MM-DD | null"
      }
    ],
    "surgical_history": ["string"],
    "social_history": {
      "smoking": "string | null",
      "alcohol": "string | null",
      "substance_use": "string | null",
      "other": "string | null"
    },
    "vitals": {
      "bp": "string | null",
      "hr": "string | null",
      "temp": "string | null",
      "weight": "string | null",
      "bmi": "string | null",
      "date": "YYYY-MM-DD | null"
    }
  },

  "triage": {
    "urgency": "urgent | semi_urgent | routine | needs_clarification | inappropriate",
    "confidence": 0.0-1.0,
    "reasoning": "string — 1-2 sentence explanation",
    "red_flags": ["string — any concerning findings"],
    "missing_critical_info": ["string — fields that should be present but weren't found"]
  },

  "extraction_metadata": {
    "ocr_confidence_mean": 0.0-1.0,
    "ocr_low_confidence_regions": ["string — descriptions of regions with <0.7 confidence"],
    "extraction_model": "string — model identifier",
    "extraction_timestamp": "ISO-8601",
    "source_format": "pdf_typed | pdf_scanned | pdf_handwritten | plain_text | ccd_xml"
  }
}
```

### 3.2 Database schema

```sql
-- Core tables

CREATE TABLE source_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    storage_key TEXT NOT NULL,              -- S3 key for encrypted source file
    original_filename TEXT,
    mime_type TEXT,
    file_size_bytes BIGINT,
    ocr_text TEXT,                          -- extracted text (encrypted at rest via pgcrypto)
    ocr_confidence_mean FLOAT,
    uploaded_at TIMESTAMPTZ DEFAULT now(),
    uploaded_by UUID                        -- FK to users table (post-MVP)
);

CREATE TABLE referrals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_document_ids UUID[] NOT NULL,
    extracted_data JSONB NOT NULL,          -- canonical schema JSON
    triage_urgency TEXT NOT NULL,
    triage_confidence FLOAT NOT NULL,
    triage_reasoning TEXT,
    triage_red_flags TEXT[],
    triage_missing_info TEXT[],
    status TEXT DEFAULT 'pending_review',   -- pending_review | reviewed | finalized | archived
    created_at TIMESTAMPTZ DEFAULT now(),
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID,                       -- FK to users table (post-MVP)
    finalized_at TIMESTAMPTZ,
    summary_pdf_key TEXT                    -- S3 key for generated summary PDF
);

CREATE TABLE corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referral_id UUID NOT NULL REFERENCES referrals(id),
    field_path TEXT NOT NULL,               -- JSON path of corrected field, e.g. "triage.urgency"
    original_value JSONB,
    corrected_value JSONB,
    corrected_by UUID,                      -- FK to users table (post-MVP)
    corrected_at TIMESTAMPTZ DEFAULT now(),
    correction_reason TEXT                  -- optional free text
);

CREATE TABLE patient_trajectories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_hash TEXT NOT NULL,             -- deterministic hash of de-identified patient identifiers
    referral_id UUID NOT NULL REFERENCES referrals(id),
    encounter_date DATE,
    specialty TEXT,
    triage_urgency TEXT,
    outcome TEXT,                           -- seen | no_show | redirected | null
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX idx_referrals_status ON referrals(status);
CREATE INDEX idx_referrals_triage ON referrals(triage_urgency);
CREATE INDEX idx_referrals_created ON referrals(created_at);
CREATE INDEX idx_corrections_referral ON corrections(referral_id);
CREATE INDEX idx_trajectories_patient ON patient_trajectories(patient_hash);
CREATE INDEX idx_trajectories_specialty ON patient_trajectories(specialty);

-- Row-level security (enable post-MVP with multi-tenancy)
-- ALTER TABLE referrals ENABLE ROW LEVEL SECURITY;
```

### 3.3 De-identification and data security

**Encryption layers**:
- Source documents: AES-256 server-side encryption in S3 (SSE-S3 or SSE-KMS)
- Database: PostgreSQL TDE (Transparent Data Encryption) or pgcrypto for column-level encryption on PHI fields
- In transit: TLS 1.3 everywhere, no exceptions
- At rest: All volumes encrypted (EBS encryption on AWS)

**De-identification strategy for stored analytics data**:
- Patient identifiers (name, DOB, MRN, SSN, contact info) are stripped before writing to `patient_trajectories`
- `patient_hash` is a salted SHA-256 of (first_name + last_name + DOB) — allows linking trajectories without storing identifiers
- The salt is stored separately from the database (AWS Secrets Manager or HashiCorp Vault) and rotated quarterly
- Clinical data in trajectories is stored at the condition/specialty level, not at the note level — no free-text clinical notes in analytics tables
- All de-identification follows HIPAA Safe Harbor method (18 identifiers removed)
- Automated de-identification audit runs nightly: regex scan for SSN patterns, phone numbers, addresses, names against a known-names list in free-text fields

**Access control**:
- API keys rotated every 90 days
- All data access logged to immutable audit table (who accessed what, when, from where)
- No PHI in application logs — structured logging with referral_id only
- Database credentials via environment variables, never in code
- Separate read/write database users with minimal privileges

**Breach prevention**:
- No PHI cached in browser (no localStorage, no sessionStorage for clinical data)
- API responses containing PHI include `Cache-Control: no-store` headers
- Session tokens expire after 30 minutes of inactivity
- Rate limiting on all API endpoints (100 req/min per user)
- Input validation and parameterized queries everywhere — no string concatenation in SQL
- Dependency scanning (Dependabot or Snyk) on every PR

---

## 4. LLM pipeline design

### 4.1 Stage 1 — Text extraction and cleaning

**Input**: Raw text from OCR or pdfplumber extraction
**Output**: Cleaned text with section headers identified
**Model**: Claude Haiku (fast, cheap — this is preprocessing)

```
System prompt:
You are a clinical document text cleaner. Your job is to:
1. Fix OCR artifacts (broken words, misrecognized characters)
2. Identify and label document sections (e.g., MEDICATIONS, ASSESSMENT, HISTORY)
3. Preserve all clinical information exactly as written — do not add, remove, or rephrase
4. Flag any regions where text is garbled or unreadable as [ILLEGIBLE]
5. Output the cleaned text with section headers in brackets like [MEDICATIONS]

Do not interpret or summarize. Only clean and structure.
```

### 4.2 Stage 2 — Structured extraction (critical path)

**Input**: Cleaned text from Stage 1
**Output**: Canonical JSON schema (see section 3.1)
**Model**: Claude Sonnet (best quality-to-cost ratio for extraction)

Use Claude's **tool use** to enforce the output schema. Define the canonical schema as a tool, and the model will populate it.

```python
# Pseudocode for extraction call
tools = [{
    "name": "extract_referral_data",
    "description": "Extract all available clinical information from the referral document into a structured format.",
    "input_schema": {
        # ... canonical schema as JSON Schema (see section 3.1)
        # Every field except referral_id, ingested_at, extraction_metadata has type: ["string", "null"]
    }
}]

system_prompt = """You are a clinical data extraction system. Extract information from the referral document into the structured schema provided via the tool.

CRITICAL RULES:
1. ONLY extract information that is EXPLICITLY stated in the document.
2. NEVER infer diagnoses from medications (e.g., do not infer "diabetes" from "metformin").
3. NEVER infer relationships between data points unless explicitly stated.
4. If a field cannot be populated from the document, pass null — never guess.
5. For triage urgency, classify based on:
   - urgent: symptoms suggesting acute/rapidly deteriorating condition, words like "emergent", "stat", "ASAP"
   - semi_urgent: needs to be seen within 1-2 weeks, moderate symptom progression
   - routine: standard referral, stable condition
   - needs_clarification: referral reason unclear, insufficient clinical information to assess
   - inappropriate: referral clearly does not match receiving specialty
6. List ALL missing critical information in missing_critical_info — this is as important as what you extract.
7. Copy exact values from the document for labs, vitals, medications — do not normalize units unless asked.
8. For red_flags, look for: chest pain, shortness of breath, sudden onset symptoms, cancer keywords, fall risk, suicidal ideation, pediatric concerns, pregnancy complications, abnormal vitals.
"""
```

### 4.3 Stage 3 — Summary generation

**Input**: Canonical JSON from Stage 2
**Output**: Human-readable narrative summary with provenance annotations
**Model**: Claude Haiku (structured-to-prose is reliable even with smaller models)

```
System prompt:
Generate a concise clinical referral summary from the structured data provided. The summary should be readable by non-clinical staff (referral coordinators).

Format:
- Patient: [name, DOB, sex, insurance]
- Referring provider: [name, practice, contact]
- Reason for referral: [1-2 sentences]
- Clinical context: [key diagnoses, relevant medications, recent test results — 3-5 bullet points max]
- Triage recommendation: [urgency level] — [1 sentence reasoning]
- Missing information: [list anything flagged as missing that the coordinator should request]
- Red flags: [any urgent findings, or "None identified"]

For every clinical fact, include a bracketed source reference like [Source: uploaded document, page 2] or [Source: OCR region, confidence 0.73].
```

### 4.4 Prompt engineering principles

- **No system prompt > 800 words**: Long prompts degrade extraction quality. Be precise.
- **Use few-shot examples**: Include 2-3 example input/output pairs in the system prompt for Stage 2. Use synthetic examples that cover edge cases (minimal referral, detailed referral, handwritten-heavy referral).
- **Structured output via tool use, not free text**: Claude's tool use enforces the JSON schema and eliminates parsing errors.
- **Separate extraction from triage**: Stage 2 does both, but the triage section of the prompt is explicitly separated from the extraction section. This makes it easy to split into two calls later if needed.
- **Temperature 0 for extraction, 0.3 for summary**: Extraction needs determinism. Summaries benefit from slight variation for readability.

---

## 5. Document handling

### Supported input formats (MVP)

| Format | Parser | Notes |
|---|---|---|
| PDF (typed/digital) | PyMuPDF (fitz) | Direct text extraction, fastest path |
| PDF (scanned) | Google Document AI | Returns text + bounding boxes + confidence |
| PDF (handwritten) | Google Document AI | Lower confidence, flag regions <0.7 |
| Plain text | Direct passthrough | Pasted or emailed referral text |
| CCD/CCDA XML | lxml + custom parser | Post-MVP, but define the interface now |
| FHIR Bundle JSON | Direct JSON parsing | Post-MVP, but define the interface now |

### Document classification logic

```python
def classify_document(pdf_path: str) -> str:
    """Determine if PDF is typed, scanned, or handwritten."""
    text = extract_text_pymupdf(pdf_path)
    if len(text.strip()) > 100:
        return "pdf_typed"  # has embedded text layer
    # No text layer — needs OCR
    ocr_result = run_document_ai(pdf_path)
    handwriting_ratio = ocr_result.handwritten_char_count / ocr_result.total_char_count
    if handwriting_ratio > 0.3:
        return "pdf_handwritten"
    return "pdf_scanned"
```

### Source document abstraction

Define a `DocumentSource` interface so all input formats produce the same intermediate representation:

```python
@dataclass
class ExtractedDocument:
    raw_text: str
    source_format: str  # pdf_typed | pdf_scanned | pdf_handwritten | plain_text | ccd_xml | fhir_json
    pages: list[PageContent]  # for provenance tracking
    confidence_scores: list[float]  # per-page or per-region OCR confidence
    metadata: dict  # original filename, page count, etc.

@dataclass
class PageContent:
    page_number: int
    text: str
    regions: list[TextRegion]  # for provenance linking

@dataclass
class TextRegion:
    text: str
    bounding_box: tuple[float, float, float, float] | None  # x1, y1, x2, y2
    confidence: float
    is_handwritten: bool
```

---

## 6. Frontend design

### User flow

```
1. Coordinator opens dashboard → sees queue of pending referrals
2. Clicks "New Referral" → upload PDF or paste text
3. System processes (loading state with progress: "Extracting text..." → "Analyzing clinical data..." → "Generating triage...")
4. Review screen displays:
   - Left panel: Source document viewer (PDF rendered inline, with highlighted regions)
   - Right panel: Structured summary with triage badge
   - Each extracted field is editable inline
   - Each field shows provenance link (click to highlight source region in left panel)
   - Missing fields highlighted in yellow with "Request from provider" button
5. Coordinator reviews, edits if needed, confirms triage
6. System generates summary PDF → available for download or (future) push to EHR
7. All edits saved as corrections for training data
```

### Key UI components

- **Referral queue table**: Status, patient name, referring provider, urgency badge, timestamp. Sortable and filterable.
- **Document viewer**: Render uploaded PDF inline (use react-pdf or pdf.js). Support zoom, page navigation. Highlight regions referenced by extracted fields.
- **Structured summary card**: Display canonical schema fields in grouped sections. Each field is inline-editable. Triage urgency is a dropdown with color-coded badge (red=urgent, orange=semi_urgent, green=routine, yellow=needs_clarification, gray=inappropriate).
- **Confidence indicators**: Show extraction confidence per field. Low confidence (<0.7) fields get a warning icon.
- **Correction capture**: When a coordinator edits a field, capture original value + new value + timestamp. This is silent — no extra modal or form.
- **Summary PDF preview**: Show generated PDF inline before download.

### Design constraints

- No unnecessary animations or transitions — coordinators are processing volume
- Information-dense layout — minimize scrolling, use collapsible sections for secondary data
- Keyboard navigable — power users will tab through fields
- Mobile-responsive is NOT a priority — this is a desktop workflow

---

## 7. Correction data and patient trajectories

### Correction data pipeline

Every coordinator edit generates a correction record:

```json
{
  "referral_id": "uuid",
  "field_path": "clinical_data.medications[2].dose",
  "original_value": "500mg",
  "corrected_value": "250mg",
  "corrected_at": "ISO-8601",
  "corrected_by": "user_id"
}
```

This data serves three purposes:
1. **Quality measurement**: Track extraction accuracy over time (% of fields requiring correction)
2. **Model improvement**: Corrections become labeled training data for fine-tuning or prompt optimization
3. **Acquisition value**: A labeled clinical NLP dataset with ground truth corrections is extremely valuable

### Patient trajectory tracking

When a referral is finalized, a de-identified trajectory record is created:

```json
{
  "patient_hash": "sha256(salt + first + last + dob)",
  "encounter_date": "2026-03-15",
  "specialty": "cardiology",
  "triage_urgency": "semi_urgent",
  "referral_reason_category": "chest_pain",  // normalized category, not free text
  "outcome": null  // populated later: seen | no_show | redirected
}
```

Over time, this builds a longitudinal dataset of referral patterns:
- Which triage urgencies actually result in being seen vs. no-show?
- What's the average time from referral to appointment by specialty?
- Which referring providers send the most incomplete referrals?
- What are the most common referral-to-specialty pathways?

This dataset is stored fully de-identified and is the primary IP asset for acquisition.

---

## 8. API design

### Core endpoints

```
POST   /api/referrals/upload          — Upload source document, kick off processing
GET    /api/referrals/{id}/status      — Poll processing status
GET    /api/referrals/{id}             — Get extracted data + triage
PATCH  /api/referrals/{id}             — Update fields (captures corrections automatically)
POST   /api/referrals/{id}/finalize    — Mark as reviewed, generate summary PDF
GET    /api/referrals/{id}/summary-pdf — Download generated summary PDF
GET    /api/referrals                  — List referrals with filters (status, urgency, date range)

POST   /api/documents/upload           — Upload raw document (returns document_id)
GET    /api/documents/{id}/text        — Get extracted text
GET    /api/documents/{id}/render      — Get document for inline viewing

GET    /api/analytics/corrections      — Correction rates by field, over time
GET    /api/analytics/trajectories     — De-identified trajectory aggregates
```

### Processing flow (async)

```python
@app.post("/api/referrals/upload")
async def upload_referral(file: UploadFile):
    # 1. Store source document in S3 (encrypted)
    doc_id = store_document(file)

    # 2. Create referral record with status "processing"
    referral_id = create_referral(doc_id, status="processing")

    # 3. Kick off async pipeline
    background_tasks.add_task(process_referral, referral_id, doc_id)

    return {"referral_id": referral_id, "status": "processing"}


async def process_referral(referral_id: str, doc_id: str):
    # Stage 1: Extract text
    doc = extract_document(doc_id)  # handles PDF classification + OCR routing
    update_status(referral_id, "extracting")

    # Stage 2: Clean text
    cleaned = await clean_text_llm(doc.raw_text)  # Claude Haiku
    update_status(referral_id, "analyzing")

    # Stage 3: Structured extraction
    extracted = await extract_structured(cleaned)  # Claude Sonnet with tool use
    update_status(referral_id, "triaging")

    # Stage 4: Save results
    save_extraction(referral_id, extracted)
    update_status(referral_id, "pending_review")
```

---

## 9. Testing with synthetic data

### Data generation strategy

1. **Synthea** — Generate 30 synthetic patient records with varied conditions (cardiac, orthopedic, neurological, oncological, pediatric, mental health). Export as FHIR JSON and CCD XML. These serve as "ground truth" patient records.

2. **Claude-generated referral letters** — For each Synthea patient, generate 2-3 referral documents in different styles:
   - Formal typed referral letter (structured, detailed)
   - Brief fax cover sheet (minimal info, abbreviations)
   - Handwritten-style notes (simulate OCR challenges by introducing typos, abbreviations, incomplete sentences)
   - Multi-page chart dump (lots of data, referral reason buried on page 3)

3. **Edge cases to test**:
   - Referral with almost no information (just patient name and "please evaluate")
   - Referral with conflicting information (two different medication lists)
   - Referral where urgency is ambiguous
   - Pediatric referral
   - Mental health referral (sensitive data handling)
   - Referral to wrong specialty

### Evaluation metrics

| Metric | Target | How measured |
|---|---|---|
| Field extraction accuracy | >90% on typed, >75% on handwritten | Compare extracted JSON to ground truth |
| Triage agreement | >85% agreement with clinician panel | Have 3 clinicians triage the same 50 referrals, compare |
| Missing data detection | >95% recall | Intentionally omit fields, check if flagged |
| End-to-end latency | <15 seconds per referral | Time from upload to review-ready |
| Hallucination rate | <2% of extracted fields | Fields present in output but absent in source |

---

## 10. Development roadmap

### Phase 1: Core pipeline (weeks 1–2)

- [ ] Set up FastAPI project with Docker
- [ ] Implement document upload + S3 storage with encryption
- [ ] Build PDF text extraction (PyMuPDF for typed, Google Doc AI for scanned)
- [ ] Build document classification (typed vs scanned vs handwritten)
- [ ] Implement Stage 1 (text cleaning) LLM call
- [ ] Implement Stage 2 (structured extraction) LLM call with tool use
- [ ] Define canonical JSON schema as Pydantic models
- [ ] Generate 30 synthetic test referrals (10 typed, 10 scanned-style, 10 edge cases)
- [ ] Test extraction accuracy against ground truth
- [ ] Set up PostgreSQL with schema from section 3.2

### Phase 2: Frontend (weeks 2–3)

- [ ] Set up React + TypeScript project
- [ ] Build referral queue dashboard
- [ ] Build document upload flow with progress indicators
- [ ] Build split-panel review screen (document viewer + structured summary)
- [ ] Implement inline field editing with correction capture
- [ ] Build triage urgency badge + dropdown override
- [ ] Add confidence indicators per field
- [ ] Connect to backend API (polling for processing status)

### Phase 3: Summary PDF + feedback loop (weeks 3–4)

- [ ] Build summary PDF template (HTML → PDF via WeasyPrint)
- [ ] Add provenance annotations (source document + page/region references)
- [ ] Implement correction data pipeline (edits → corrections table)
- [ ] Build patient trajectory de-identification and storage
- [ ] Add correction analytics endpoint
- [ ] Add export functionality for de-identified datasets

### Phase 4: Hardening (weeks 4–6)

- [ ] Run full test suite against 100+ synthetic referrals
- [ ] Measure and optimize end-to-end latency
- [ ] Add rate limiting, input validation, error handling
- [ ] Set up audit logging (immutable, no PHI in logs)
- [ ] Set up nightly de-identification audit scan
- [ ] Document all API endpoints (OpenAPI/Swagger auto-generated by FastAPI)
- [ ] Prepare demo environment with synthetic data
- [ ] Write deployment runbook

### Future phases (post-MVP)

- [ ] Multi-user auth with role-based access (coordinator vs. admin)
- [ ] CCD/CCDA XML parser for structured HIE documents
- [ ] FHIR Bundle JSON ingestion
- [ ] Live HIE integration via Carequality/CommonWell
- [ ] Patient matching (MPI integration)
- [ ] Cloud fax webhook (Documo/Phaxio) for automatic intake
- [ ] EHR-embedded view (Epic App Orchard, Cerner App Gallery)
- [ ] Fine-tuned extraction model using correction data
- [ ] Analytics dashboard (referral volume, triage distribution, correction rates)
- [ ] Multi-tenancy with row-level security

---

## 11. Project structure

```
reftriage/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── config.py                # Environment config, secrets
│   │   ├── models/
│   │   │   ├── schemas.py           # Pydantic models (canonical schema)
│   │   │   ├── database.py          # SQLAlchemy models
│   │   │   └── enums.py             # TriageUrgency, DocumentFormat, etc.
│   │   ├── api/
│   │   │   ├── referrals.py         # Referral CRUD + processing endpoints
│   │   │   ├── documents.py         # Document upload + retrieval
│   │   │   └── analytics.py         # Correction + trajectory endpoints
│   │   ├── services/
│   │   │   ├── document_processor.py  # OCR routing, text extraction
│   │   │   ├── llm_extraction.py      # Claude API calls (stages 1-3)
│   │   │   ├── triage_engine.py       # Triage classification logic
│   │   │   ├── pdf_generator.py       # Summary PDF generation
│   │   │   ├── deidentification.py    # PHI stripping, hashing
│   │   │   └── storage.py             # S3 operations
│   │   ├── middleware/
│   │   │   ├── audit_log.py           # Request/response audit logging
│   │   │   └── security.py            # Rate limiting, headers
│   │   └── utils/
│   │       ├── ocr.py                 # Google Document AI wrapper
│   │       └── provenance.py          # Source tracking helpers
│   ├── tests/
│   │   ├── test_extraction.py
│   │   ├── test_triage.py
│   │   ├── test_deidentification.py
│   │   └── fixtures/                  # Synthetic referral documents
│   ├── scripts/
│   │   ├── generate_synthetic_data.py
│   │   ├── run_extraction_eval.py
│   │   └── audit_phi_scan.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── ReferralQueue.tsx
│   │   │   ├── DocumentViewer.tsx
│   │   │   ├── StructuredSummary.tsx
│   │   │   ├── TriageBadge.tsx
│   │   │   ├── InlineEditor.tsx
│   │   │   └── ConfidenceIndicator.tsx
│   │   ├── hooks/
│   │   │   ├── useReferral.ts
│   │   │   └── usePolling.ts
│   │   ├── services/
│   │   │   └── api.ts                 # Backend API client
│   │   └── types/
│   │       └── referral.ts            # TypeScript types matching canonical schema
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml                 # Local dev: API + DB + MinIO + frontend
├── .env.example
└── README.md
```

---

## 12. Key risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| LLM hallucination in extraction | Patient safety | Strict "only extract explicit" prompt rules + confidence scores + human review required |
| OCR failure on handwritten notes | Incomplete data | Flag low-confidence regions, don't force extraction from illegible text |
| HIPAA violation | Legal / financial | Encryption everywhere, no PHI in logs, de-identification audits, BAA with Anthropic |
| Slow LLM latency | Poor UX | Async processing with progress updates, cache common patterns, optimize prompt length |
| Coordinator over-trust in AI | Liability | UI design emphasizes "suggestion" framing, mandatory review before finalization |
| Data breach | Company-ending | Encrypted storage, minimal PHI surface area, audit logging, penetration testing |
| Schema rigidity blocks new use cases | Technical debt | JSONB storage for extracted data, schema versioning from day one |

---

## 13. Environment variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/reftriage
DATABASE_ENCRYPTION_KEY=  # for pgcrypto column encryption

# Storage
S3_BUCKET=reftriage-documents
S3_REGION=us-west-2
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_ENCRYPTION_KEY=  # SSE-KMS key ARN

# LLM
ANTHROPIC_API_KEY=
EXTRACTION_MODEL=claude-sonnet-4-20250514
CLEANING_MODEL=claude-haiku-4-5-20251001
SUMMARY_MODEL=claude-haiku-4-5-20251001

# OCR
GOOGLE_CLOUD_PROJECT=
GOOGLE_APPLICATION_CREDENTIALS=

# Security
JWT_SECRET=
SALT_SECRET=  # for patient hash de-identification
AUDIT_LOG_BUCKET=reftriage-audit-logs

# App
APP_ENV=development  # development | staging | production
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=100
```
