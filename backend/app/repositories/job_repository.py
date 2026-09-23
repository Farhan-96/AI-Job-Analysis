"""Job data-access helpers."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import JobStatus
from app.models.job import Job, JobSkill
from app.models.match import JobProfileMatch


def get_job(db: Session, job_id: int) -> Job | None:
    return db.scalar(
        select(Job)
        .where(Job.id == job_id)
        .options(
            selectinload(Job.skills),
            selectinload(Job.matches).selectinload(JobProfileMatch.profile),
        )
    )


def get_job_by_source(db: Session, source: str, source_job_id: str) -> Job | None:
    return db.scalar(
        select(Job).where(Job.source == source, Job.source_job_id == source_job_id)
    )


def list_jobs(
    db: Session,
    *,
    status: str | None = None,
    source: str | None = None,
    remote_type: str | None = None,
    location: str | None = None,
    profile_id: int | None = None,
    min_score: float | None = None,
    date_from: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Job]:
    stmt: Select[tuple[Job]] = (
        select(Job)
        .options(
            selectinload(Job.skills),
            selectinload(Job.matches).selectinload(JobProfileMatch.profile),
        )
        .order_by(Job.discovered_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        stmt = stmt.where(Job.status == status)
    if source:
        stmt = stmt.where(Job.source == source)
    if remote_type:
        stmt = stmt.where(Job.remote_type == remote_type)
    if location:
        stmt = stmt.where(Job.location.ilike(f"%{location}%"))
    if date_from is not None:
        stmt = stmt.where(Job.discovered_at >= date_from)
    if profile_id is not None or min_score is not None:
        stmt = stmt.join(JobProfileMatch)
        if profile_id is not None:
            stmt = stmt.where(JobProfileMatch.profile_id == profile_id)
        if min_score is not None:
            stmt = stmt.where(JobProfileMatch.match_score >= min_score)
        stmt = stmt.distinct()

    return list(db.scalars(stmt).unique().all())


def job_stats(db: Session) -> dict[str, int]:
    rows = db.execute(select(Job.status, func.count()).group_by(Job.status)).all()
    counts = {status: 0 for status in JobStatus}
    total = 0
    for status, count in rows:
        counts[status] = count
        total += count
    return {
        "total": total,
        "new": counts.get(JobStatus.NEW.value, 0),
        "analyzed": counts.get(JobStatus.ANALYZED.value, 0),
        "reviewed": counts.get(JobStatus.REVIEWED.value, 0),
        "shortlisted": counts.get(JobStatus.SHORTLISTED.value, 0),
        "rejected": counts.get(JobStatus.REJECTED.value, 0),
        "applied": counts.get(JobStatus.APPLIED.value, 0),
    }


def delete_job(db: Session, job: Job) -> None:
    db.delete(job)
    db.commit()


def replace_job_skills(db: Session, job: Job, skills: list[JobSkill]) -> None:
    job.skills.clear()
    db.flush()
    for skill in skills:
        job.skills.append(skill)


def replace_job_matches(db: Session, job: Job, matches: list[JobProfileMatch]) -> None:
    job.matches.clear()
    db.flush()
    for match in matches:
        job.matches.append(match)
