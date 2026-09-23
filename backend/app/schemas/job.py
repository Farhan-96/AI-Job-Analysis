"""Pydantic schemas for jobs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    company: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=2048)
    description: str = Field(default="", max_length=100_000)
    source: str = Field(default="manual", max_length=64)
    source_job_id: str | None = Field(default=None, max_length=512)
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = Field(default=None, max_length=16)
    employment_type: str | None = Field(default=None, max_length=64)
    remote_type: str | None = Field(default=None, max_length=32)
    posted_at: datetime | None = None
    raw_data: dict[str, Any] | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must not be blank")
        return cleaned


class JobStatusUpdate(BaseModel):
    status: Literal["new", "analyzed", "reviewed", "shortlisted", "rejected", "applied"]


class JobSkillOut(BaseModel):
    id: int
    skill: str
    source: str
    confidence: float

    model_config = {"from_attributes": True}


class JobMatchSummary(BaseModel):
    id: int
    profile_id: int
    profile_name: str | None = None
    profile_slug: str | None = None
    match_score: float
    role_match: str
    recommendation: str

    model_config = {"from_attributes": True}


class JobListItem(BaseModel):
    id: int
    title: str
    company: str | None
    location: str | None
    source: str
    remote_type: str
    status: str
    discovered_at: datetime
    url: str | None = None
    top_match: JobMatchSummary | None = None

    model_config = {"from_attributes": True}


class JobOut(BaseModel):
    id: int
    source: str
    source_job_id: str
    title: str
    company: str | None
    location: str | None
    remote_type: str
    url: str | None
    description: str
    salary_min: float | None
    salary_max: float | None
    salary_currency: str | None
    employment_type: str | None
    posted_at: datetime | None
    discovered_at: datetime
    status: str
    normalized_title: str | None
    extracted_experience_years: float | None
    extracted_education: str | None
    skills: list[JobSkillOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobStats(BaseModel):
    total: int
    new: int
    analyzed: int
    reviewed: int
    shortlisted: int
    rejected: int
    applied: int


class JobMatchOut(BaseModel):
    id: int
    job_id: int
    profile_id: int
    profile_name: str | None = None
    profile_slug: str | None = None
    match_score: float
    matching_skills: list[Any]
    missing_skills: list[Any]
    matching_keywords: list[Any]
    missing_keywords: list[Any]
    experience_match: str
    education_match: str
    role_match: str
    location_match: str
    salary_match: str
    analysis: str
    recommendation: str
    score_breakdown: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalyzeResponse(BaseModel):
    job: JobOut
    matches: list[JobMatchOut]
