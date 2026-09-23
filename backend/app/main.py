"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, health, jobs, profiles
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.seed import seed_profiles

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Log startup and shutdown events; ensure default profiles exist."""
    settings = get_settings()
    logger.info("AI Job Assistant backend starting (Phase 2)")
    logger.info("CORS origins: %s", settings.cors_origin_list)
    # Do not log DATABASE_URL — it may contain credentials
    logger.info("Database engine configured")
    try:
        with SessionLocal() as db:
            created = seed_profiles(db)
            if created:
                logger.info("Default resume profiles seeded count=%s", created)
    except Exception:
        logger.exception("Profile seed on startup skipped (DB may not be ready yet)")
    yield
    logger.info("AI Job Assistant backend shutting down")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    application = FastAPI(
        title="AI Job Search & Application Assistant",
        description="Backend API for the AI Job Assistant (Phase 2 — job analysis)",
        version="0.2.0",
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
    application.include_router(jobs.router)
    application.include_router(profiles.router)
    application.include_router(admin.router)

    return application


app = create_app()
