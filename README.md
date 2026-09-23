# AI Job Search & Application Assistant

An AI-powered personal job search, resume tailoring, and application management platform.

**Current status:** Phase 1 — project foundation only (no job scraping, AI analysis, resume tailoring, Gmail, or application automation yet).

## Architecture overview

```
Frontend (Next.js) → FastAPI Backend → PostgreSQL
Worker (Python) → Future scheduled automation
```

See [docs/architecture.md](docs/architecture.md) for details.

## Prerequisites

- Docker & Docker Compose (recommended)
- Node.js 20+ (for local frontend development)
- Python 3.12+ (for local backend/worker development)
- PostgreSQL 16 (or use the Compose service)

## Environment variables

Copy the example file and adjust if needed:

```bash
cp .env.example .env
```

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy PostgreSQL URL | Docker: `...@postgres:5432/...` · Host: `...@localhost:5433/...` |
| `BACKEND_URL` | Backend base URL | `http://localhost:8000` |
| `NEXT_PUBLIC_API_URL` | Frontend → backend URL | `http://localhost:8000` |
| `CORS_ORIGINS` | Allowed browser origins | `http://localhost:3000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `WORKER_POLL_INTERVAL_SECONDS` | Worker loop interval | `60` |

Do not commit `.env` or real secrets.

## Docker setup (recommended)

Start all services:

```bash
docker compose up --build
```

This starts:

| Service | Port |
|---|---|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| FastAPI docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5433 (container port 5432) |
| Worker | (background process) |

Stop:

```bash
docker compose down
```

## Local development

### 1. Database

```bash
docker compose up postgres -d
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # if not already created
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend

```bash
cd frontend
cp ../.env.example .env.local   # or set NEXT_PUBLIC_API_URL
npm install
npm run dev
```

Open http://localhost:3000

### 4. Worker

```bash
cd worker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

## Backend commands

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
pytest
alembic upgrade head
alembic revision --autogenerate -m "message"
```

## Frontend commands

```bash
cd frontend
npm run dev
npm run lint
npm run build
npm start
```

## Worker commands

```bash
cd worker
source .venv/bin/activate
python -m app.main
pytest
```

## Database migration commands

```bash
cd backend
source .venv/bin/activate
alembic upgrade head          # apply migrations
alembic downgrade -1          # roll back one revision
alembic current               # show current revision
```

## Testing commands

```bash
# Backend
cd backend && source .venv/bin/activate && pytest -q

# Worker
cd worker && source .venv/bin/activate && pytest -q

# Frontend
cd frontend && npm run lint && npm run build
```

## Project structure

```
├── frontend/          # Next.js + TypeScript + Tailwind
├── backend/           # FastAPI + SQLAlchemy + Alembic
├── worker/            # Python worker foundation
├── docs/              # Architecture documentation
├── docker-compose.yml
├── .env.example
└── README.md
```

## Phase 1 health endpoints

- `GET /health` → `{ "status": "ok" }`
- `GET /api/health` → `{ "status": "ok", "service": "backend" }`
- `GET /api/health/database` → `{ "status": "ok", "database": "connected" }`

## Later phases (not implemented)

Job discovery, JD analysis, resume selection/tailoring, AI matching, Gmail, application tracking, and notifications.
