"""Job search profile and search-run history models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.profile import ResumeProfile


class JobSearchProfile(Base):
    """
    Configurable automated job search criteria.

    Secrets never live here — source credentials stay in environment variables.
    """

    __tablename__ = "job_search_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    keywords: Mapped[list[Any]] = mapped_column(JSONType, nullable=False, default=list)
    locations: Mapped[list[Any]] = mapped_column(JSONType, nullable=False, default=list)
    remote_types: Mapped[list[Any]] = mapped_column(JSONType, nullable=False, default=list)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="mock")
    schedule_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    schedule_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resume_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("resume_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    resume_profile: Mapped[ResumeProfile | None] = relationship(
        "ResumeProfile",
        back_populates="search_profiles",
    )
    runs: Mapped[list[JobSearchRun]] = relationship(
        "JobSearchRun",
        back_populates="search_profile",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    jobs: Mapped[list[Job]] = relationship(
        "Job",
        back_populates="search_profile",
    )


class JobSearchRun(Base):
    """Record of a single automated (or manual) search execution."""

    __tablename__ = "job_search_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    search_profile_id: Mapped[int] = mapped_column(
        ForeignKey("job_search_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="running", index=True
    )
    jobs_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    jobs_imported: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    search_profile: Mapped[JobSearchProfile] = relationship(
        "JobSearchProfile",
        back_populates="runs",
    )
