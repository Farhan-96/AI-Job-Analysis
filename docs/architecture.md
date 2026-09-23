# AI Job Search & Application Assistant — Architecture

## Overview

Phase 1 establishes the foundation for a multi-service platform that will later automate job search, resume tailoring, and application management.

```
┌─────────────┐     HTTP      ┌─────────────┐     SQL      ┌──────────────┐
│  Frontend   │ ────────────► │   FastAPI   │ ──────────► │  PostgreSQL  │
│  (Next.js)  │               │   Backend   │             │              │
└─────────────┘               └─────────────┘             └──────────────┘
                                     ▲
                                     │ (future shared DB / queues)
                                     │
                              ┌─────────────┐
                              │   Worker    │
                              │  (Python)   │
                              └─────────────┘
```

## Services

### Frontend
- **Stack:** Next.js, TypeScript, React, Tailwind CSS
- **Role:** User-facing dashboard and future workflows (jobs, applications, resumes)
- **Talks to:** FastAPI backend via `NEXT_PUBLIC_API_URL`

### Backend
- **Stack:** FastAPI, Pydantic, SQLAlchemy, Alembic
- **Role:** REST API, health checks, database access
- **Talks to:** PostgreSQL

### PostgreSQL
- Persistent application database
- Phase 1 includes only connectivity verification (simple health/test table)

### Worker
- **Stack:** Python
- **Role:** Long-running process for future scheduled automation
- Phase 1 only starts and logs readiness; no job/search automation yet

```
Worker
  ↓
Future scheduled automation
  (job discovery, applications, notifications)
```

## Phase 1 scope

- Project layout and Docker Compose
- Dashboard shell with live backend/database status
- Health endpoints (`/health`, `/api/health`, `/api/health/database`)
- SQLAlchemy + Alembic baseline
- Worker process that stays alive

## Later phases (not implemented yet)

- Job discovery / scraping
- JD analysis and AI matching
- Resume selection and tailoring
- ATS scoring
- Gmail OAuth and sending
- Application tracking
- Notifications and analytics

## Data flow (Phase 1)

1. User opens the dashboard in the browser.
2. Frontend calls `GET /api/health` and `GET /api/health/database`.
3. Backend responds with service and database connectivity status.
4. Dashboard renders Connected / Unavailable based on real responses.
