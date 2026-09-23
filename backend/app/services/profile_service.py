"""Resume profile CRUD service."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.profile import ProfileSkill, ResumeProfile
from app.repositories import profile_repository
from app.schemas.profile import ProfileCreate, ProfileUpdate

logger = logging.getLogger(__name__)


def create_profile(db: Session, payload: ProfileCreate) -> ResumeProfile:
    if profile_repository.get_profile_by_slug(db, payload.slug):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile slug already exists",
        )
    profile = ResumeProfile(
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        resume_file=payload.resume_file,
        active=payload.active,
        title_keywords=payload.title_keywords,
        preferred_locations=payload.preferred_locations,
        remote_ok=payload.remote_ok,
        min_experience_years=payload.min_experience_years,
        max_experience_years=payload.max_experience_years,
        education_keywords=payload.education_keywords,
        match_weights=payload.match_weights,
    )
    for skill in payload.skills:
        profile.skills.append(
            ProfileSkill(skill=skill.skill, weight=skill.weight, required=skill.required)
        )
    db.add(profile)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile name or slug already exists",
        ) from exc
    db.refresh(profile)
    logger.info("Profile created slug=%s", profile.slug)
    return profile


def update_profile(db: Session, profile_id: int, payload: ProfileUpdate) -> ResumeProfile:
    profile = profile_repository.get_profile(db, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    data = payload.model_dump(exclude_unset=True)
    skills_data = data.pop("skills", None)
    for key, value in data.items():
        setattr(profile, key, value)

    if skills_data is not None:
        profile_repository.replace_skills(
            profile,
            [
                ProfileSkill(
                    skill=s["skill"],
                    weight=s.get("weight", 5.0),
                    required=s.get("required", False),
                )
                for s in skills_data
            ],
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile name conflict",
        ) from exc
    return profile_repository.get_profile(db, profile_id)  # type: ignore[return-value]


def delete_profile(db: Session, profile_id: int) -> None:
    profile = profile_repository.get_profile(db, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    db.delete(profile)
    db.commit()
    logger.info("Profile deleted id=%s", profile_id)
