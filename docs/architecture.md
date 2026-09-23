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

## Phase 2 (current)

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

### Job sources

`JobSource` abstraction with:

- `ManualJobSource` — UI/API paste
- `IndeedJobSource` — adapter scaffold (no scraping / no ToS bypass)
- `JsonImportJobSource` — offline JSON import

### Analyzer

- `JobAnalyzer` interface
- `RuleBasedJobAnalyzer` (default, deterministic)
- `LLMJobAnalyzer` placeholder (falls back to rules; no keys required)

### Worker

Polls `GET /api/jobs?status=new` and calls `POST /api/jobs/{id}/analyze`.

## Later phases

Job discovery automation, Gmail, resume selection, application sending, tracking.
