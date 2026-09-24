# AI Job Search & Application Assistant

An AI-powered personal job search, resume tailoring, and application management platform.

**Current status:** Phase 3 Step 2 — automated job search & collection (mock + approved feeds). No Gmail, no auto-apply, no CAPTCHA bypass.

## Architecture overview

```
Frontend (Next.js)
    ↓
FastAPI Backend  →  PostgreSQL
    ↑
Worker
  TASK A: due search profiles → JobSource.search → JobImportService
  TASK B: status=new jobs → analyze
```

Pipeline:

```
JobSearchProfile → JobSource.search() → JobImportService → DB (status=new) → Worker → Analysis
```

See [docs/architecture.md](docs/architecture.md) for details.

## Prerequisites

- Docker & Docker Compose (recommended)
- Node.js 20+ (for local frontend development)
- Python 3.12+ (for local backend/worker development)
- PostgreSQL 16 (or use the Compose service)

## Environment variables

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL (Compose: `@postgres:5432`, host: `@localhost:5433`) |
| `BACKEND_URL` | Worker → backend URL (`http://backend:8000` in Compose) |
| `NEXT_PUBLIC_API_URL` | Frontend → backend URL |
| `CORS_ORIGINS` | Allowed browser origins |
| `JOB_IMPORT_ENABLED` | Enable/disable import APIs |
| `JOB_SEARCH_ENABLED` | Enable/disable automated search |
| `SEARCH_MIN_INTERVAL_SECONDS` | Global minimum between scheduled searches |
| `MAX_JOBS_PER_SEARCH` | Cap jobs imported per search run |
| `MAX_SEARCHES_PER_CYCLE` | Cap scheduled searches per worker cycle |
| `INDEED_APPROVED_FEED_PATH` | Optional local JSON feed for Indeed adapter |
| `INDEED_APPROVED_FEED_URL` | Optional HTTP JSON feed for Indeed adapter |
| `WORKER_POLL_INTERVAL_SECONDS` | Worker poll interval |
| `WORKER_BATCH_SIZE` | Max new jobs analyzed per cycle |
| `LOG_LEVEL` | Logging level |

Do not commit `.env` or secrets. Never put API keys in `NEXT_PUBLIC_*` vars. Do not store passwords/API keys in search profiles or `job_source_configs`.

## Docker setup

```bash
docker compose up --build -d
docker compose ps
docker compose logs worker
docker compose logs backend
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| FastAPI docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5433 |

## Phase 3 Step 2 — Job search profiles

### What is a search profile?

A `JobSearchProfile` is one independent search (keywords + locations + source + schedule). Examples seeded on startup:

- React Native Jobs
- IT Support Jobs
- Teaching Jobs
- Software Developer Jobs
- AI Python Jobs
- Automation Jobs

Each profile links to a primary resume profile for matching context, while analysis still scores against all active resume profiles.

### Create / edit a profile

- UI: **Job Search → New profile** or **Edit**
- API: `POST /api/search-profiles`, `PUT /api/search-profiles/{id}`

Configure: name, keywords, locations, remote types, source (`mock` / `indeed`), enabled, schedule enabled, interval minutes.

### Run a search

- UI: **Run now** on a search profile card/row
- API: `POST /api/search-profiles/{id}/run` → returns `202` immediately with `run_id`

The search runs in the background (or via the worker for scheduled due profiles). It does **not** analyze jobs in the HTTP request.

### Automatic scheduling

When `schedule_enabled` is true, the worker’s discovery task calls `POST /api/search/run-due` each poll cycle. A profile is due when:

- it is enabled
- schedule is enabled
- `now - last_run_at >= max(schedule_interval_minutes, SEARCH_MIN_INTERVAL_SECONDS)`

`MAX_SEARCHES_PER_CYCLE` limits how many due profiles run per cycle.

### Duplicate detection

Reuses Phase 3 Step 1 deduplication:

1. Primary: `source + source_job_id`
2. Fallback: normalized URL → stable `source_job_id`

Same job discovered by two search profiles or re-run searches is counted as a duplicate, not re-inserted.

### How jobs move into analysis

1. Search finds N jobs
2. Import: status=`new`
3. Worker TASK B polls `GET /api/jobs?status=new`
4. `POST /api/jobs/{id}/analyze` → skills + match scores

### Source limitations

| Source | Behavior |
|---|---|
| `mock` | Local catalog for development. Clearly marked — **not real jobs**. |
| `indeed` | Approved feed via `INDEED_APPROVED_FEED_PATH` / `_URL`, or CSV/JSON/manual import. **No HTML scraping, CAPTCHA bypass, stealth, or proxy rotation.** Without a feed, search status=`failed` with `source unavailable`. |
| manual / csv / json | Phase 3 Step 1 import paths (still available) |

## Phase 3 Step 1 — Job import

### Manual / CSV / JSON import

Still available under **Job Import** and `/api/jobs/import*`.

### Import history

- UI: Job Import page
- API: `GET /api/jobs/import/history`

## Phase 2 workflows (still available)

### Analyze a job

- UI: **Analyze** on the job row or detail page
- API: `POST /api/jobs/{id}/analyze`
- Or wait for the worker to pick up `status=new` jobs

### Seed sample development jobs

```bash
curl -X POST http://localhost:8000/api/admin/seed
```

### Run worker

```bash
docker compose up worker
# or locally:
cd worker && source .venv/bin/activate && BACKEND_URL=http://localhost:8000 python -m app.main
```

### Run tests

```bash
cd backend && source .venv/bin/activate && pytest -q
cd worker && source .venv/bin/activate && pytest -q
cd frontend && npm run lint && npm run build
```

## Local development

```bash
# DB
docker compose up postgres -d

# Backend
cd backend && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev

# Worker
cd worker && source .venv/bin/activate
pip install -r requirements.txt
BACKEND_URL=http://localhost:8000 python -m app.main
```

## Database migrations

```bash
cd backend && source .venv/bin/activate
alembic upgrade head
alembic current
```

## Key API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/api/health` | Service health |
| GET | `/api/health/database` | DB health |
| POST | `/api/jobs` | Create job |
| GET | `/api/jobs` | List / filter jobs |
| GET | `/api/jobs/stats` | Status counts |
| GET | `/api/jobs/{id}` | Job detail |
| DELETE | `/api/jobs/{id}` | Delete job |
| POST | `/api/jobs/{id}/analyze` | Run analysis |
| GET | `/api/jobs/{id}/matches` | Profile matches |
| PATCH | `/api/jobs/{id}/status` | Update status |
| POST | `/api/jobs/import` | Manual / bulk import |
| POST | `/api/jobs/import/csv` | CSV import |
| POST | `/api/jobs/import/json` | JSON import |
| GET | `/api/jobs/import/history` | Import history |
| GET | `/api/jobs/import/sources` | Source configs |
| POST/GET/PUT/DELETE | `/api/search-profiles` | Search profile CRUD |
| POST | `/api/search-profiles/{id}/run` | Enqueue search (non-blocking) |
| GET | `/api/search-profiles/{id}/runs` | Profile search history |
| GET | `/api/search-runs` | All search runs |
| GET | `/api/search-runs/{id}` | Search run detail |
| POST | `/api/search/run-due` | Worker: run due scheduled searches |
| GET/POST/PUT/DELETE | `/api/profiles` | Profile CRUD |
| POST | `/api/admin/seed` | Dev seed data |

## Project structure

```
├── frontend/     # Next.js — Jobs, Job Search, Import
├── backend/      # FastAPI + search + import + analysis + Alembic
├── worker/       # Discovery + analysis polling
├── docs/
├── docker-compose.yml
└── README.md
```

## Later phases (not implemented)

Gmail, resume attachment selection, email sending, automatic applications, browser application automation, LinkedIn/Indeed login automation, CAPTCHA bypass.
