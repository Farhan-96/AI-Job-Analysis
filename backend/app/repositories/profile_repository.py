"""Resume profile data-access helpers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.profile import ProfileSkill, ResumeProfile


def list_profiles(db: Session, *, active_only: bool = False) -> list[ResumeProfile]:
    stmt = select(ResumeProfile).options(selectinload(ResumeProfile.skills)).order_by(
        ResumeProfile.name
    )
    if active_only:
        stmt = stmt.where(ResumeProfile.active.is_(True))
    return list(db.scalars(stmt).all())


def get_profile(db: Session, profile_id: int) -> ResumeProfile | None:
    return db.scalar(
        select(ResumeProfile)
        .where(ResumeProfile.id == profile_id)
        .options(selectinload(ResumeProfile.skills))
    )


def get_profile_by_slug(db: Session, slug: str) -> ResumeProfile | None:
    return db.scalar(
        select(ResumeProfile)
        .where(ResumeProfile.slug == slug)
        .options(selectinload(ResumeProfile.skills))
    )


def replace_skills(
    profile: ResumeProfile,
    skills: list[ProfileSkill],
) -> None:
    profile.skills.clear()
    for skill in skills:
        profile.skills.append(skill)
