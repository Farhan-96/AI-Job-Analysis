"""Job CRUD and analysis orchestration."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import JobStatus
from app.models.job import Job, JobSkill
from app.models.match import JobProfileMatch
from app.repositories import job_repository, profile_repository
from app.schemas.job import JobCreate
from app.services.analyzers import get_default_analyzer
from app.services.job_serializers import serialize_job, serialize_matches
from app.services.normalization import (
    detect_remote_type,
    normalize_company,
    normalize_employment_type,
    normalize_location,
    normalize_title,
)
from app.sources import get_source

logger = logging.getLogger(__name__)

__all__ = [
    "analyze_job",
    "create_job",
    "serialize_job",
    "serialize_matches",
    "update_job_status",
]


def create_job(db: Session, payload: JobCreate) -> Job:
    source = get_source(payload.source)
    raw = source.parse_job(payload.model_dump())
    raw = source.normalize_job(raw)

    existing = job_repository.get_job_by_source(db, raw.source, raw.source_job_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Duplicate job for this source",
                "existing_job_id": existing.id,
            },
        )

    title = normalize_title(raw.title)
    location = normalize_location(raw.location)
    remote = raw.remote_type or detect_remote_type(location, raw.description)

    job = Job(
        source=raw.source,
        source_job_id=raw.source_job_id,
        title=title,
        company=normalize_company(raw.company),
        location=location,
        remote_type=remote,
        url=raw.url,
        description=raw.description,
        salary_min=raw.salary_min if raw.salary_min is not None else payload.salary_min,
        salary_max=raw.salary_max if raw.salary_max is not None else payload.salary_max,
        salary_currency=raw.salary_currency or payload.salary_currency,
        employment_type=normalize_employment_type(
            raw.employment_type or payload.employment_type
        ),
        posted_at=payload.posted_at,
        raw_data=raw.raw_data,
        status=JobStatus.NEW.value,
        normalized_title=title,
    )
    db.add(job)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.warning("Duplicate job insert rejected")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Duplicate job for this source"},
        ) from exc
    db.refresh(job)
    logger.info("Job created id=%s source=%s", job.id, job.source)
    return job


def analyze_job(db: Session, job_id: int) -> tuple[Job, list[JobProfileMatch]]:
    job = job_repository.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    profiles = profile_repository.list_profiles(db, active_only=True)
    if not profiles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active resume profiles configured. Seed profiles first.",
        )

    logger.info("Analyzing job id=%s", job.id)
    result = get_default_analyzer().analyze(
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        employment_type=job.employment_type,
        remote_type=job.remote_type,
        profiles=profiles,
    )

    job.normalized_title = result.normalized_title
    job.company = result.company or job.company
    job.location = result.location or job.location
    job.remote_type = result.remote_type
    job.employment_type = result.employment_type or job.employment_type
    job.extracted_experience_years = result.experience.years
    job.extracted_education = result.education.level
    job.status = JobStatus.ANALYZED.value

    job_repository.replace_job_skills(
        db,
        job,
        [
            JobSkill(skill=s.skill, source=s.source, confidence=s.confidence)
            for s in result.skills
        ],
    )
    job_repository.replace_job_matches(
        db,
        job,
        [
            JobProfileMatch(
                profile_id=m.profile_id,
                match_score=m.match_score,
                matching_skills=m.matching_skills,
                missing_skills=m.missing_skills,
                matching_keywords=m.matching_keywords,
                missing_keywords=m.missing_keywords,
                experience_match=m.experience_match,
                education_match=m.education_match,
                role_match=m.role_match,
                location_match=m.location_match,
                salary_match=m.salary_match,
                analysis=m.analysis,
                recommendation=m.recommendation,
                score_breakdown=m.score_breakdown,
            )
            for m in result.matches
        ],
    )

    db.commit()
    job = job_repository.get_job(db, job_id)
    assert job is not None

    logger.info(
        "Job analyzed id=%s skills=%s matches=%s",
        job.id,
        len(job.skills),
        len(job.matches),
    )
    for match in job.matches:
        logger.info(
            "Profile match profile=%s score=%s",
            match.profile.slug if match.profile else match.profile_id,
            match.match_score,
        )

    return job, list(job.matches)


def update_job_status(db: Session, job_id: int, new_status: str) -> Job:
    job = job_repository.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    job.status = new_status
    db.commit()
    db.refresh(job)
    return job
