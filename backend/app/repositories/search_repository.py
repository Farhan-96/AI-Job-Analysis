"""Data-access helpers for job search profiles and runs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.models.search import JobSearchProfile, JobSearchRun


def get_profile(db: Session, profile_id: int) -> JobSearchProfile | None:
    return db.scalar(
        select(JobSearchProfile)
        .where(JobSearchProfile.id == profile_id)
        .options(
            selectinload(JobSearchProfile.resume_profile),
            selectinload(JobSearchProfile.runs),
        )
    )


def get_profile_by_slug(db: Session, slug: str) -> JobSearchProfile | None:
    return db.scalar(
        select(JobSearchProfile).where(JobSearchProfile.slug == slug)
    )


def list_profiles(db: Session, *, enabled: bool | None = None) -> list[JobSearchProfile]:
    stmt: Select[tuple[JobSearchProfile]] = (
        select(JobSearchProfile)
        .options(selectinload(JobSearchProfile.resume_profile))
        .order_by(JobSearchProfile.name.asc())
    )
    if enabled is not None:
        stmt = stmt.where(JobSearchProfile.enabled.is_(enabled))
    return list(db.scalars(stmt).all())


def create_profile(db: Session, profile: JobSearchProfile) -> JobSearchProfile:
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def save_profile(db: Session, profile: JobSearchProfile) -> JobSearchProfile:
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def delete_profile(db: Session, profile: JobSearchProfile) -> None:
    db.delete(profile)
    db.commit()


def get_run(db: Session, run_id: int) -> JobSearchRun | None:
    return db.scalar(
        select(JobSearchRun)
        .where(JobSearchRun.id == run_id)
        .options(selectinload(JobSearchRun.search_profile))
    )


def list_runs(
    db: Session,
    *,
    search_profile_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[JobSearchRun]:
    stmt: Select[tuple[JobSearchRun]] = (
        select(JobSearchRun)
        .options(selectinload(JobSearchRun.search_profile))
        .order_by(JobSearchRun.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if search_profile_id is not None:
        stmt = stmt.where(JobSearchRun.search_profile_id == search_profile_id)
    return list(db.scalars(stmt).all())


def create_run(db: Session, run: JobSearchRun) -> JobSearchRun:
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def save_run(db: Session, run: JobSearchRun) -> JobSearchRun:
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def list_due_profiles(
    db: Session,
    *,
    now: datetime | None = None,
    min_interval_seconds: int = 60,
    max_searches: int = 3,
) -> list[JobSearchProfile]:
    """
    Return enabled profiles whose schedule is due.

    Respects schedule_interval_minutes and a global minimum interval.
    """
    clock = now or datetime.now(timezone.utc)
    profiles = list_profiles(db, enabled=True)
    due: list[JobSearchProfile] = []

    for profile in profiles:
        if not profile.schedule_enabled:
            continue
        interval_minutes = max(
            profile.schedule_interval_minutes,
            max(1, min_interval_seconds // 60),
        )
        # Also enforce raw second minimum when interval is sub-minute in tests
        min_delta = timedelta(seconds=max(min_interval_seconds, interval_minutes * 60))
        if profile.last_run_at is not None:
            last = profile.last_run_at
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            if clock - last < min_delta:
                continue
        due.append(profile)
        if len(due) >= max_searches:
            break

    return due
