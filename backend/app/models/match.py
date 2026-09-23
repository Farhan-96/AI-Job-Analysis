"""Job ↔ profile match analysis results."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.profile import ResumeProfile


class JobProfileMatch(Base):
    """Transparent profile match score and reasoning for a job."""

    __tablename__ = "job_profile_matches"
    __table_args__ = (
        UniqueConstraint("job_id", "profile_id", name="uq_job_profile_matches_job_profile"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("resume_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    matching_skills: Mapped[list[Any]] = mapped_column(JSONType, nullable=False, default=list)
    missing_skills: Mapped[list[Any]] = mapped_column(JSONType, nullable=False, default=list)
    matching_keywords: Mapped[list[Any]] = mapped_column(JSONType, nullable=False, default=list)
    missing_keywords: Mapped[list[Any]] = mapped_column(JSONType, nullable=False, default=list)
    experience_match: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    education_match: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    role_match: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    location_match: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    salary_match: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    analysis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recommendation: Mapped[str] = mapped_column(String(64), nullable=False, default="review")
    score_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    job: Mapped[Job] = relationship("Job", back_populates="matches")
    profile: Mapped[ResumeProfile] = relationship("ResumeProfile", back_populates="matches")
