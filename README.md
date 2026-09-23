# AI Job Search & Application Assistant

An AI-powered personal job search, resume tailoring, and application management platform.

**Current status:** Phase 3 Step 1 — controlled job import pipeline (manual / CSV / JSON). No automatic scraping, Gmail, or auto-apply.

## Architecture overview

```
Frontend (Next.js)
    ↓
FastAPI Backend  →  PostgreSQL
    ↑
Worker (polls new jobs → POST /api/jobs/{id}/analyze)
```

Phase 3 Step 1 pipeline:

```
Source adapter → JobImportService → DB (status=new) → Worker → Analysis
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
| `JOB_IMPORT_ENABLED` | Enable/disable import APIs (`true` / `false`) |
| `WORKER_POLL_INTERVAL_SECONDS` | Worker poll interval |
| `WORKER_BATCH_SIZE` | Max new jobs processed per worker cycle |
| `LOG_LEVEL` | Logging level |

Do not commit `.env` or secrets. Never put API keys in `NEXT_PUBLIC_*` vars. Do not store passwords/API keys in `job_source_configs`.

## Docker setup

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| FastAPI docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5433 |

## Phase 3 Step 1 — Job import

### Manual import

- UI: **Job Import → Manual Job**
- API: `POST /api/jobs/import`

```json
{
  "source": "indeed",
  "jobs": [
    {
      "source_job_id": "12345",
      "title": "React Native Developer",
      "company": "Example Company",
      "location": "Islamabad",
      "url": "https://example.com/job",
      "description": "...",
      "employment_type": "Full-time"
    }
  ]
}
```

Response:

```json
{ "imported": 1, "duplicates": 0, "failed": 0 }
```

### CSV import

- UI: **Job Import → CSV Import**
- API: `POST /api/jobs/import/csv` (multipart file)

Supported columns: `source`, `source_job_id`, `title`, `company`, `location`, `remote_type`, `url`, `description`, `salary_min`, `salary_max`, `salary_currency`, `employment_type`, `posted_at`.

Malformed rows are reported in `errors` without aborting the whole batch.

### JSON import

- UI: **Job Import → JSON Import**
- API: `POST /api/jobs/import/json` (multipart file)

Accepts an array of jobs or `{ "source": "...", "jobs": [...] }`. Both CSV and JSON use the same `JobImportService`.

### Import history

- UI: table on the Job Import page
- API: `GET /api/jobs/import/history`

### Worker processing

Imported jobs are inserted with `status=new`. The worker polls in batches of `WORKER_BATCH_SIZE` and calls `POST /api/jobs/{id}/analyze`. Analysis is **not** run inside the import HTTP request.

### Deduplication

Uses existing uniqueness on `source + source_job_id`. When `source_job_id` is missing, a stable id is derived from the normalized URL (or title+company for manual).

Re-importing the same CSV yields `imported=0`, `duplicates=N`.

### Source adapters

`JobSource` with `fetch_jobs()`, `normalize_job()`, `get_source_name()`:

- `ManualJobSource`
- `IndeedJobSource` (permitted/approved input only — no scraping / CAPTCHA bypass)
- `CsvImportJobSource` / `JsonImportJobSource`

Future sources (LinkedIn, company careers, RSS, email alerts) plug into the same abstraction. `job_source_configs` stores non-secret enablement metadata only.

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
| GET/POST/PUT/DELETE | `/api/profiles` | Profile CRUD |
| POST | `/api/admin/seed` | Dev seed data |

## Project structure

```
├── frontend/     # Next.js dashboard + Jobs + Import UI
├── backend/      # FastAPI + import service + analysis + Alembic
├── worker/       # Polls new jobs and triggers analysis
├── docs/
├── docker-compose.yml
└── README.md
```

## Later phases (not implemented)

Automatic scraping, Gmail, resume attachment selection, email sending, Indeed application workflows, application tracking.
