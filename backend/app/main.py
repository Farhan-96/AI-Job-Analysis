"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, health, job_import, job_search, jobs, profiles
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.repositories import import_repository
from app.seed import seed_profiles
from app.services.job_search_service import job_search_service

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Log startup and shutdown events; ensure default profiles exist."""
    settings = get_settings()
    logger.info("AI Job Assistant backend starting (Phase 3 Step 2 — job search)")
    logger.info("CORS origins: %s", settings.cors_origin_list)
    logger.info("Job import enabled: %s", settings.job_import_enabled)
    logger.info("Job search enabled: %s", settings.job_search_enabled)
    # Do not log DATABASE_URL — it may contain credentials
    logger.info("Database engine configured")
    try:
        with SessionLocal() as db:
            created = seed_profiles(db)
            if created:
                logger.info("Default resume profiles seeded count=%s", created)
            sources = import_repository.seed_source_configs(db)
            if sources:
                logger.info("Default job source configs seeded count=%s", sources)
            search_created = job_search_service.seed_default_profiles(db)
            if search_created:
                logger.info("Default search profiles seeded count=%s", search_created)
    except Exception:
        logger.exception("Seed on startup skipped (DB may not be ready yet)")
    yield
    logger.info("AI Job Assistant backend shutting down")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    application = FastAPI(
        title="AI Job Search & Application Assistant",
        description="Backend API for the AI Job Assistant (Phase 3 — automated job search)",
        version="0.3.2",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router)
    application.include_router(job_import.router)
    application.include_router(job_search.router)
    application.include_router(jobs.router)
    application.include_router(profiles.router)
    application.include_router(admin.router)

    return application


app = create_app()
