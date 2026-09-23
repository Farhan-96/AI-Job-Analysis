"""Resume profile and profile skill models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")

if TYPE_CHECKING:
    from app.models.match import JobProfileMatch


class ResumeProfile(Base):
    """Configurable career/resume profile used for classification and matching."""

    __tablename__ = "resume_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_file: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Title signals used for classification (JSON list of strings)
    title_keywords: Mapped[list[Any]] = mapped_column(JSONType, nullable=False, default=list)
    # Preferred location names / remote indicators
    preferred_locations: Mapped[list[Any]] = mapped_column(JSONType, nullable=False, default=list)
    remote_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    min_experience_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_experience_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    education_keywords: Mapped[list[Any]] = mapped_column(JSONType, nullable=False, default=list)
    # Optional per-profile weight overrides: {role, skills, experience, education, location}
    match_weights: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    skills: Mapped[list[ProfileSkill]] = relationship(
        "ProfileSkill",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matches: Mapped[list[JobProfileMatch]] = relationship(
        "JobProfileMatch",
        back_populates="profile",
        cascade="all, delete-orphan",
    )


class ProfileSkill(Base):
    """Weighted skill belonging to a resume profile."""

    __tablename__ = "profile_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("resume_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill: Mapped[str] = mapped_column(String(128), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    profile: Mapped[ResumeProfile] = relationship("ResumeProfile", back_populates="skills")
