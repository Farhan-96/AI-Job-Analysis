"""Pydantic schemas for job search profiles and runs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SearchProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    slug: str | None = Field(default=None, max_length=128)
    keywords: list[str] = Field(min_length=1)
    locations: list[str] = Field(default_factory=list)
    remote_types: list[str] = Field(default_factory=list)
    source: str = Field(default="mock", max_length=64)
    enabled: bool = True
    schedule_enabled: bool = False
    schedule_interval_minutes: int = Field(default=60, ge=1, le=10_080)
    resume_profile_id: int | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be blank")
        return cleaned

    @field_validator("keywords")
    @classmethod
    def keywords_not_empty(cls, value: list[str]) -> list[str]:
        cleaned = [k.strip() for k in value if k and str(k).strip()]
        if not cleaned:
            raise ValueError("at least one keyword is required")
        return cleaned


class SearchProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    keywords: list[str] | None = None
    locations: list[str] | None = None
    remote_types: list[str] | None = None
    source: str | None = Field(default=None, max_length=64)
    enabled: bool | None = None
    schedule_enabled: bool | None = None
    schedule_interval_minutes: int | None = Field(default=None, ge=1, le=10_080)
    resume_profile_id: int | None = None
    clear_resume_profile: bool = False


class SearchProfileOut(BaseModel):
    id: int
    name: str
    slug: str
    enabled: bool
    keywords: list[str]
    locations: list[str]
    remote_types: list[str]
    source: str
    schedule_enabled: bool
    schedule_interval_minutes: int
    last_run_at: datetime | None
    resume_profile_id: int | None
    resume_profile_name: str | None = None
    resume_profile_slug: str | None = None
    created_at: datetime
    updated_at: datetime
    last_run_status: str | None = None
    last_jobs_found: int | None = None
    last_jobs_imported: int | None = None
    last_duplicates: int | None = None

    model_config = {"from_attributes": True}


class SearchRunOut(BaseModel):
    id: int
    search_profile_id: int
    search_profile_name: str | None = None
    search_profile_slug: str | None = None
    source: str
    started_at: datetime
    completed_at: datetime | None
    status: Literal["running", "completed", "failed"]
    jobs_found: int
    jobs_imported: int
    duplicates: int
    failed: int
    error_message: str | None
    duration_seconds: float | None = None

    model_config = {"from_attributes": True}


class SearchRunAccepted(BaseModel):
    """Immediate response when a search is enqueued (non-blocking)."""

    run_id: int
    status: str
    message: str = "Search started"
