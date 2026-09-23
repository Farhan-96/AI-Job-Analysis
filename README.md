# AI Job Search & Application Assistant

An AI-powered personal job search, resume tailoring, and application management platform.

**Current status:** Phase 2 — job discovery foundation, parsing, classification, and resume-profile matching (manual job input; no auto-apply).

## Architecture overview

```
Frontend (Next.js)
    ↓
FastAPI Backend  →  PostgreSQL
    ↑
Worker (polls new jobs → POST /api/jobs/{id}/analyze)
```

Phase 2 pipeline:

```
Job input → Normalize → Extract skills → Classify profiles → Match scores → Store → Review UI
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
| `WORKER_POLL_INTERVAL_SECONDS` | Worker poll interval |
| `WORKER_BATCH_SIZE` | Max new jobs processed per cycle |
| `LOG_LEVEL` | Logging level |

Do not commit `.env` or secrets. Never put API keys in `NEXT_PUBLIC_*` vars.

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

## Phase 2 workflows

### 1. Add a job manually

- UI: **Jobs → Add job** (paste title + description)
- API: `POST /api/jobs`

### 2. Analyze a job

- UI: **Analyze** on the job row or detail page
- API: `POST /api/jobs/{id}/analyze`
- Or wait for the worker to pick up `status=new` jobs

### 3. View profile matches

- UI: open `/jobs/{id}`
- API: `GET /api/jobs/{id}/matches`

### 4. Configure profiles / skills

- API: `GET/POST/PUT/DELETE /api/profiles`
- Default profiles are seeded on backend startup

### 5. Seed sample development jobs

```bash
curl -X POST http://localhost:8000/api/admin/seed
```

Or use **Seed sample data** on the Jobs page. Sample companies are prefixed with `[DEV SEED]`.

### 6. Run worker

```bash
docker compose up worker
# or locally:
cd worker && source .venv/bin/activate && python -m app.main
```

### 7. Run tests

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
| GET/POST/PUT/DELETE | `/api/profiles` | Profile CRUD |
| POST | `/api/admin/seed` | Dev seed data |

## Project structure

```
├── frontend/     # Next.js dashboard + Jobs UI
├── backend/      # FastAPI + analysis engine + Alembic
├── worker/       # Polls new jobs and triggers analysis
├── docs/
├── docker-compose.yml
└── README.md
```

## Later phases (not implemented)

Automated job collection, Gmail, resume attachment selection, email sending, Indeed application workflows, application tracking.
