"""Development seed orchestration for profiles and sample jobs."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.profile import ProfileSkill, ResumeProfile
from app.repositories import profile_repository
from app.schemas.job import JobCreate
from app.seed_data.jobs import SAMPLE_JOBS
from app.seed_data.profiles import DEFAULT_LOCATIONS, PROFILE_SEEDS
from app.services import job_service

logger = logging.getLogger(__name__)


def seed_profiles(db: Session) -> int:
    created = 0
    for data in PROFILE_SEEDS:
        if profile_repository.get_profile_by_slug(db, data["slug"]):
            continue
        profile = ResumeProfile(
            name=data["name"],
            slug=data["slug"],
            description=data["description"],
            resume_file=data["resume_file"],
            active=True,
            title_keywords=data["title_keywords"],
            preferred_locations=data.get("preferred_locations", DEFAULT_LOCATIONS),
            remote_ok=data.get("remote_ok", True),
            min_experience_years=data.get("min_experience_years"),
            max_experience_years=data.get("max_experience_years"),
            education_keywords=data.get("education_keywords", []),
            match_weights=None,
        )
        for skill, weight, required in data["skills"]:
            profile.skills.append(
                ProfileSkill(skill=skill, weight=float(weight), required=required)
            )
        db.add(profile)
        created += 1
    db.commit()
    logger.info("Seeded profiles created=%s", created)
    return created


def seed_sample_jobs(db: Session, *, analyze: bool = True) -> int:
    seed_profiles(db)
    created = 0
    for item in SAMPLE_JOBS:
        existing = db.scalar(
            select(Job).where(
                Job.source == item["source"],
                Job.source_job_id == item["source_job_id"],
            )
        )
        if existing:
            continue
        job = job_service.create_job(db, JobCreate(**item))
        created += 1
        if analyze:
            job_service.analyze_job(db, job.id)
    logger.info("Seeded sample jobs created=%s", created)
    return created


def run_seed(db: Session) -> dict[str, int]:
    profiles = seed_profiles(db)
    jobs = seed_sample_jobs(db, analyze=True)
    return {"profiles": profiles, "jobs": jobs}
