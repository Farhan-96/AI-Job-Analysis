"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health
from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Log startup and shutdown events."""
    settings = get_settings()
    logger.info("AI Job Assistant backend starting")
    logger.info("CORS origins: %s", settings.cors_origin_list)
    # Do not log DATABASE_URL — it may contain credentials
    logger.info("Database engine configured")
    yield
    logger.info("AI Job Assistant backend shutting down")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    application = FastAPI(
        title="AI Job Search & Application Assistant",
        description="Backend API for the AI Job Assistant (Phase 1 foundation)",
        version="0.1.0",
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

    return application


app = create_app()
