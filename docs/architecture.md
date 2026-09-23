# AI Job Search & Application Assistant — Architecture

## Overview

```
┌─────────────┐     HTTP      ┌─────────────┐     SQL      ┌──────────────┐
│  Frontend   │ ────────────► │   FastAPI   │ ──────────► │  PostgreSQL  │
│  (Next.js)  │               │   Backend   │             │              │
└─────────────┘               └─────────────┘             └──────────────┘
                                     ▲
                                     │ HTTP analyze
                              ┌─────────────┐
                              │   Worker    │
                              │  (Python)   │
                              └─────────────┘
```

## Phase 1 (complete)

- Health endpoints, Docker Compose, dashboard system status
- Alembic baseline + `health_checks` table
- Worker heartbeat

## Phase 2 (complete)

Job analysis engine (no auto-apply):

```
Job input (manual / import adapters)
  → Normalization
  → Skill extraction (dictionary)
  → Profile classification
  → Transparent Profile Match Score
  → PostgreSQL storage
  → Frontend review
```

### Data model

- `resume_profiles` / `profile_skills` — configurable career profiles
- `jobs` / `job_skills` — postings + extracted skills
- `job_profile_matches` — per-profile scores and reasoning

### Analyzer

- `JobAnalyzer` interface
- `RuleBasedJobAnalyzer` (default, deterministic)
- `LLMJobAnalyzer` placeholder (falls back to rules; no keys required)

## Phase 3 Step 1 (current)

Controlled job collection & import (no scraping / no Gmail / no auto-apply):

```
API / CSV / JSON
  → JobImportService
  → JobSource.normalize_job()
  → Deduplicate (source + source_job_id | URL)
  → Insert Job (status=new)
  → Record JobImport history
  → Worker batch (WORKER_BATCH_SIZE)
  → POST /api/jobs/{id}/analyze
```

### Job sources

`JobSource` with `fetch_jobs()`, `normalize_job()`, `get_source_name()`:

- `ManualJobSource` — UI/API paste
- `IndeedJobSource` — approved input only (no CAPTCHA bypass / stealth scraping)
- `CsvImportJobSource` / `JsonImportJobSource` — file import channels

### New tables

- `job_imports` — batch import history
- `job_source_configs` — non-secret source enablement (secrets stay in env)

### Worker

Polls `GET /api/jobs?status=new&limit=WORKER_BATCH_SIZE` and calls `POST /api/jobs/{id}/analyze`.

## Later phases

Automated job discovery (within ToS), Gmail, resume selection, application sending, tracking.
