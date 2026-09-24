# AI Job Search & Application Assistant — Architecture

## Overview

```
┌─────────────┐     HTTP      ┌─────────────┐     SQL      ┌──────────────┐
│  Frontend   │ ────────────► │   FastAPI   │ ──────────► │  PostgreSQL  │
│  (Next.js)  │               │   Backend   │             │              │
└─────────────┘               └─────────────┘             └──────────────┘
                                     ▲
                                     │ HTTP discover + analyze
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

## Phase 3 Step 1 (complete)

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

`JobSource` with `fetch_jobs()`, `normalize_job()`, `search()`, `get_source_name()`:

- `ManualJobSource` — UI/API paste
- `IndeedJobSource` — approved feed/import only (no CAPTCHA bypass / stealth scraping)
- `MockJobSource` — local development catalog (`source=mock`)
- `CsvImportJobSource` / `JsonImportJobSource` — file import channels

### Tables

- `job_imports` — batch import history
- `job_source_configs` — non-secret source enablement (secrets stay in env)

## Phase 3 Step 2 (current)

Automated job discovery through search profiles:

```
JobSearchScheduler / Worker TASK A
  → JobSource.search(profile)
  → JobImportService
  → PostgreSQL (status=new)
  → Worker TASK B
  → JobAnalyzer
```

### New tables

- `job_search_profiles` — keywords, locations, remote_types, source, schedule, resume link
- `job_search_runs` — per-run history (found / imported / duplicates / failed)
- `jobs.search_profile_id` — optional link to the discovering profile

### Worker tasks

| Task | Role |
|---|---|
| `discover_jobs` | `POST /api/search/run-due` for scheduled profiles |
| `process_new_jobs` | Analyze `status=new` jobs (unchanged) |

### Rate limits

- `SEARCH_MIN_INTERVAL_SECONDS`
- `MAX_JOBS_PER_SEARCH`
- `MAX_SEARCHES_PER_CYCLE`

### Scope limits

No Gmail, no auto-apply, no browser application automation, no CAPTCHA/anti-bot bypass.

## Later phases

Gmail, resume selection, application sending, tracking.
