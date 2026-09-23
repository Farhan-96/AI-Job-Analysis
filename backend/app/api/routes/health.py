"""Health check API routes."""

import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import check_database_connection
from app.schemas.health import (
    DatabaseHealthResponse,
    RootHealthResponse,
    ServiceHealthResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=RootHealthResponse)
def root_health() -> RootHealthResponse:
    """Liveness probe for the backend process."""
    return RootHealthResponse()


@router.get("/api/health", response_model=ServiceHealthResponse)
def api_health() -> ServiceHealthResponse:
    """Service-level health for frontend status checks."""
    return ServiceHealthResponse()


@router.get(
    "/api/health/database",
    response_model=DatabaseHealthResponse,
    responses={
        503: {
            "description": "Database unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "database": "disconnected",
                        "detail": "could not connect to server",
                    }
                }
            },
        }
    },
)
def database_health() -> DatabaseHealthResponse:
    """Verify PostgreSQL connectivity with a live query."""
    try:
        check_database_connection()
    except SQLAlchemyError as exc:
        logger.error("Database health check failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "database": "disconnected",
                "detail": str(exc.__cause__ or exc),
            },
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during database health check")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "database": "disconnected",
                "detail": str(exc),
            },
        ) from exc

    return DatabaseHealthResponse()
