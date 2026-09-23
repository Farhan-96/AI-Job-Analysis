"""Pydantic schemas for resume profiles."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ProfileSkillIn(BaseModel):
    skill: str = Field(min_length=1, max_length=128)
    weight: float = Field(default=5.0, ge=0, le=100)
    required: bool = False


class ProfileSkillOut(ProfileSkillIn):
    id: int

    model_config = {"from_attributes": True}


class ProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    slug: str = Field(min_length=1, max_length=128)
    description: str | None = None
    resume_file: str = Field(min_length=1, max_length=255)
    active: bool = True
    title_keywords: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    remote_ok: bool = True
    min_experience_years: float | None = None
    max_experience_years: float | None = None
    education_keywords: list[str] = Field(default_factory=list)
    match_weights: dict[str, float] | None = None
    skills: list[ProfileSkillIn] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def slug_format(cls, value: str) -> str:
        cleaned = value.strip().lower().replace(" ", "-")
        if not cleaned:
            raise ValueError("slug must not be blank")
        return cleaned


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    resume_file: str | None = Field(default=None, min_length=1, max_length=255)
    active: bool | None = None
    title_keywords: list[str] | None = None
    preferred_locations: list[str] | None = None
    remote_ok: bool | None = None
    min_experience_years: float | None = None
    max_experience_years: float | None = None
    education_keywords: list[str] | None = None
    match_weights: dict[str, float] | None = None
    skills: list[ProfileSkillIn] | None = None


class ProfileOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    resume_file: str
    active: bool
    title_keywords: list[Any]
    preferred_locations: list[Any]
    remote_ok: bool
    min_experience_years: float | None
    max_experience_years: float | None
    education_keywords: list[Any]
    match_weights: dict[str, Any] | None
    skills: list[ProfileSkillOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
