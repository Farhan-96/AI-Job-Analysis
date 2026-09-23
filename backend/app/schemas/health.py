"""Pydantic schemas for health endpoints."""

from typing import Literal

from pydantic import BaseModel, Field


class RootHealthResponse(BaseModel):
    """Response for GET /health."""

    status: Literal["ok"] = "ok"


class ServiceHealthResponse(BaseModel):
    """Response for GET /api/health."""

    status: Literal["ok"] = "ok"
    service: Literal["backend"] = "backend"


class DatabaseHealthResponse(BaseModel):
    """Response for GET /api/health/database when connected."""

    status: Literal["ok"] = "ok"
    database: Literal["connected"] = "connected"


class DatabaseHealthErrorResponse(BaseModel):
    """Error body when the database is unavailable."""

    status: Literal["error"] = "error"
    database: Literal["disconnected"] = "disconnected"
    detail: str = Field(description="Human-readable connection failure message")
