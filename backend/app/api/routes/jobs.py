"""Job API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import JobStatus
from app.repositories import job_repository
from app.schemas.job import (
    AnalyzeResponse,
    JobCreate,
    JobListItem,
    JobMatchOut,
    JobMatchSummary,
    JobOut,
    JobStats,
    JobStatusUpdate,
)
from app.services import job_service

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _to_list_item(job) -> JobListItem:
    top = None
    if job.matches:
        best = max(job.matches, key=lambda m: m.match_score)
        top = JobMatchSummary(
            id=best.id,
            profile_id=best.profile_id,
            profile_name=best.profile.name if best.profile else None,
            profile_slug=best.profile.slug if best.profile else None,
            match_score=best.match_score,
            role_match=best.role_match,
            recommendation=best.recommendation,
        )
    return JobListItem(
        id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        source=job.source,
        remote_type=job.remote_type,
        status=job.status,
        discovered_at=job.discovered_at,
        url=job.url,
        top_match=top,
    )


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, db: Session = Depends(get_db)) -> JobOut:
    job = job_service.create_job(db, payload)
    return job_service.serialize_job(job)


@router.get("", response_model=list[JobListItem])
def list_jobs(
    status_filter: str | None = Query(default=None, alias="status"),
    source: str | None = None,
    remote_type: str | None = None,
    location: str | None = None,
    profile_id: int | None = None,
    min_score: float | None = Query(default=None, ge=0, le=100),
    date_from: datetime | None = Query(
        default=None,
        description="Only jobs discovered on/after this timestamp (ISO-8601)",
    ),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[JobListItem]:
    jobs = job_repository.list_jobs(
        db,
        status=status_filter,
        source=source,
        remote_type=remote_type,
        location=location,
        profile_id=profile_id,
        min_score=min_score,
        date_from=date_from,
        limit=limit,
        offset=offset,
    )
    return [_to_list_item(job) for job in jobs]


@router.get("/stats", response_model=JobStats)
def get_job_stats(db: Session = Depends(get_db)) -> JobStats:
    return JobStats(**job_repository.job_stats(db))


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)) -> JobOut:
    job = job_repository.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job_service.serialize_job(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, db: Session = Depends(get_db)) -> None:
    job = job_repository.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    job_repository.delete_job(db, job)


@router.post("/{job_id}/analyze", response_model=AnalyzeResponse)
def analyze_job(job_id: int, db: Session = Depends(get_db)) -> AnalyzeResponse:
    job, matches = job_service.analyze_job(db, job_id)
    return AnalyzeResponse(
        job=job_service.serialize_job(job),
        matches=job_service.serialize_matches(matches),
    )


@router.get("/{job_id}/matches", response_model=list[JobMatchOut])
def get_job_matches(job_id: int, db: Session = Depends(get_db)) -> list[JobMatchOut]:
    job = job_repository.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    matches = sorted(job.matches, key=lambda m: m.match_score, reverse=True)
    return job_service.serialize_matches(matches)


@router.patch("/{job_id}/status", response_model=JobOut)
def patch_job_status(
    job_id: int,
    payload: JobStatusUpdate,
    db: Session = Depends(get_db),
) -> JobOut:
    if payload.status not in {s.value for s in JobStatus}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    job = job_service.update_job_status(db, job_id, payload.status)
    return job_service.serialize_job(job)
