"""Import history and job-source config data access."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.import_history import JobImport, JobSourceConfig

DEFAULT_SOURCE_CONFIGS: list[dict[str, str | bool]] = [
    {"name": "Manual", "slug": "manual", "enabled": True},
    {"name": "Indeed", "slug": "indeed", "enabled": True},
    {"name": "LinkedIn", "slug": "linkedin", "enabled": False},
    {"name": "Company Careers", "slug": "company-careers", "enabled": False},
    {"name": "CSV", "slug": "csv", "enabled": True},
    {"name": "JSON", "slug": "json", "enabled": True},
]


def list_import_history(db: Session, *, limit: int = 50, offset: int = 0) -> list[JobImport]:
    stmt = (
        select(JobImport)
        .order_by(JobImport.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


def list_source_configs(db: Session, *, enabled_only: bool = False) -> list[JobSourceConfig]:
    stmt = select(JobSourceConfig).order_by(JobSourceConfig.name.asc())
    if enabled_only:
        stmt = stmt.where(JobSourceConfig.enabled.is_(True))
    return list(db.scalars(stmt).all())


def seed_source_configs(db: Session) -> int:
    """Insert default source configs if missing. Returns number created."""
    created = 0
    for item in DEFAULT_SOURCE_CONFIGS:
        slug = str(item["slug"])
        existing = db.scalar(select(JobSourceConfig).where(JobSourceConfig.slug == slug))
        if existing:
            continue
        db.add(
            JobSourceConfig(
                name=str(item["name"]),
                slug=slug,
                enabled=bool(item["enabled"]),
                config={},
            )
        )
        created += 1
    if created:
        db.commit()
    return created
