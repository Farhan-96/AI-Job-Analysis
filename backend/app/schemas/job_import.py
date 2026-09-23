"""Pydantic schemas for job import endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ImportJobItem(BaseModel):
    """Single job payload for bulk/manual import."""

    source_job_id: str | None = Field(default=None, max_length=512)
    title: str = Field(min_length=1, max_length=512)
    company: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=2048)
    description: str = Field(default="", max_length=100_000)
    employment_type: str | None = Field(default=None, max_length=64)
    remote_type: str | None = Field(default=None, max_length=32)
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = Field(default=None, max_length=16)
    posted_at: datetime | None = None
    raw_data: dict[str, Any] | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must not be blank")
        return cleaned


class JobImportRequest(BaseModel):
    """POST /api/jobs/import body."""

    source: str = Field(default="manual", max_length=64)
    jobs: list[ImportJobItem] = Field(min_length=1, max_length=1000)

    @field_validator("source")
    @classmethod
    def source_not_blank(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("source must not be blank")
        return cleaned


class JobImportResult(BaseModel):
    """Summary returned by import endpoints."""

    imported: int = 0
    duplicates: int = 0
    failed: int = 0
    total_rows: int | None = None
    errors: list[str] = Field(default_factory=list)
    import_id: int | None = None


class JobImportHistoryItem(BaseModel):
    id: int
    source: str
    import_type: str
    total_count: int
    imported_count: int
    duplicate_count: int
    failed_count: int
    error_summary: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobSourceConfigOut(BaseModel):
    id: int
    name: str
    slug: str
    enabled: bool
    config: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
