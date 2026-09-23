"""Serialize job ORM models to API schemas."""

from __future__ import annotations

from app.models.job import Job
from app.models.match import JobProfileMatch
from app.schemas.job import JobMatchOut, JobOut, JobSkillOut


def job_out(job: Job) -> JobOut:
    return JobOut(
        id=job.id,
        source=job.source,
        source_job_id=job.source_job_id,
        title=job.title,
        company=job.company,
        location=job.location,
        remote_type=job.remote_type,
        url=job.url,
        description=job.description,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        employment_type=job.employment_type,
        posted_at=job.posted_at,
        discovered_at=job.discovered_at,
        status=job.status,
        normalized_title=job.normalized_title,
        extracted_experience_years=job.extracted_experience_years,
        extracted_education=job.extracted_education,
        skills=[JobSkillOut.model_validate(s) for s in job.skills],
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def match_out(match: JobProfileMatch) -> JobMatchOut:
    return JobMatchOut(
        id=match.id,
        job_id=match.job_id,
        profile_id=match.profile_id,
        profile_name=match.profile.name if match.profile else None,
        profile_slug=match.profile.slug if match.profile else None,
        match_score=match.match_score,
        matching_skills=match.matching_skills or [],
        missing_skills=match.missing_skills or [],
        matching_keywords=match.matching_keywords or [],
        missing_keywords=match.missing_keywords or [],
        experience_match=match.experience_match,
        education_match=match.education_match,
        role_match=match.role_match,
        location_match=match.location_match,
        salary_match=match.salary_match,
        analysis=match.analysis,
        recommendation=match.recommendation,
        score_breakdown=match.score_breakdown,
        created_at=match.created_at,
    )


def serialize_job(job: Job) -> JobOut:
    return job_out(job)


def serialize_matches(matches: list[JobProfileMatch]) -> list[JobMatchOut]:
    return [match_out(m) for m in matches]
