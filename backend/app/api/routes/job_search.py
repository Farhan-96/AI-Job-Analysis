"""Job search profile API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal, get_db
from app.repositories import search_repository
from app.schemas.job_search import (
    SearchProfileCreate,
    SearchProfileOut,
    SearchProfileUpdate,
    SearchRunAccepted,
    SearchRunOut,
)
from app.services.job_search_service import job_search_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["job-search"])


def _serialize_profile(profile) -> SearchProfileOut:
    last_run = None
    if profile.runs:
        last_run = max(profile.runs, key=lambda r: r.started_at)

    resume = profile.resume_profile
    return SearchProfileOut(
        id=profile.id,
        name=profile.name,
        slug=profile.slug,
        enabled=profile.enabled,
        keywords=list(profile.keywords or []),
        locations=list(profile.locations or []),
        remote_types=list(profile.remote_types or []),
        source=profile.source,
        schedule_enabled=profile.schedule_enabled,
        schedule_interval_minutes=profile.schedule_interval_minutes,
        last_run_at=profile.last_run_at,
        resume_profile_id=profile.resume_profile_id,
        resume_profile_name=resume.name if resume else None,
        resume_profile_slug=resume.slug if resume else None,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        last_run_status=last_run.status if last_run else None,
        last_jobs_found=last_run.jobs_found if last_run else None,
        last_jobs_imported=last_run.jobs_imported if last_run else None,
        last_duplicates=last_run.duplicates if last_run else None,
    )


def _serialize_run(run) -> SearchRunOut:
    duration = None
    if run.completed_at and run.started_at:
        duration = (run.completed_at - run.started_at).total_seconds()
    profile = run.search_profile
    return SearchRunOut(
        id=run.id,
        search_profile_id=run.search_profile_id,
        search_profile_name=profile.name if profile else None,
        search_profile_slug=profile.slug if profile else None,
        source=run.source,
        started_at=run.started_at,
        completed_at=run.completed_at,
        status=run.status,
        jobs_found=run.jobs_found,
        jobs_imported=run.jobs_imported,
        duplicates=run.duplicates,
        failed=run.failed,
        error_message=run.error_message,
        duration_seconds=duration,
    )


def _execute_run_background(run_id: int) -> None:
    """Background task — uses its own DB session."""
    with SessionLocal() as db:
        try:
            job_search_service.execute_run(db, run_id)
        except Exception:
            logger.exception("Background search run failed run_id=%s", run_id)


@router.post(
    "/api/search-profiles",
    response_model=SearchProfileOut,
    status_code=status.HTTP_201_CREATED,
)
def create_search_profile(
    payload: SearchProfileCreate,
    db: Session = Depends(get_db),
) -> SearchProfileOut:
    settings = get_settings()
    if not settings.job_search_enabled:
        raise HTTPException(status_code=503, detail="Job search is disabled")
    try:
        profile = job_search_service.create_profile(
            db,
            name=payload.name,
            slug=payload.slug,
            keywords=payload.keywords,
            locations=payload.locations,
            remote_types=payload.remote_types,
            source=payload.source,
            enabled=payload.enabled,
            schedule_enabled=payload.schedule_enabled,
            schedule_interval_minutes=payload.schedule_interval_minutes,
            resume_profile_id=payload.resume_profile_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    # Reload with relationships
    profile = search_repository.get_profile(db, profile.id)
    return _serialize_profile(profile)


@router.get("/api/search-profiles", response_model=list[SearchProfileOut])
def list_search_profiles(
    enabled: bool | None = None,
    db: Session = Depends(get_db),
) -> list[SearchProfileOut]:
    profiles = search_repository.list_profiles(db, enabled=enabled)
    # Ensure runs are loaded for last-run summary
    result = []
    for p in profiles:
        full = search_repository.get_profile(db, p.id)
        result.append(_serialize_profile(full))
    return result


@router.get("/api/search-profiles/{profile_id}", response_model=SearchProfileOut)
def get_search_profile(
    profile_id: int,
    db: Session = Depends(get_db),
) -> SearchProfileOut:
    profile = search_repository.get_profile(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")
    return _serialize_profile(profile)


@router.put("/api/search-profiles/{profile_id}", response_model=SearchProfileOut)
def update_search_profile(
    profile_id: int,
    payload: SearchProfileUpdate,
    db: Session = Depends(get_db),
) -> SearchProfileOut:
    profile = search_repository.get_profile(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")
    try:
        job_search_service.update_profile(
            db,
            profile,
            name=payload.name,
            keywords=payload.keywords,
            locations=payload.locations,
            remote_types=payload.remote_types,
            source=payload.source,
            enabled=payload.enabled,
            schedule_enabled=payload.schedule_enabled,
            schedule_interval_minutes=payload.schedule_interval_minutes,
            resume_profile_id=payload.resume_profile_id,
            clear_resume_profile=payload.clear_resume_profile,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    profile = search_repository.get_profile(db, profile_id)
    return _serialize_profile(profile)


@router.delete(
    "/api/search-profiles/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_search_profile(
    profile_id: int,
    db: Session = Depends(get_db),
) -> None:
    profile = search_repository.get_profile(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")
    search_repository.delete_profile(db, profile)


@router.post(
    "/api/search-profiles/{profile_id}/run",
    response_model=SearchRunAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def run_search_profile(
    profile_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> SearchRunAccepted:
    """Enqueue a search — returns immediately; does not block on external I/O."""
    settings = get_settings()
    if not settings.job_search_enabled:
        raise HTTPException(status_code=503, detail="Job search is disabled")

    profile = search_repository.get_profile(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")
    if not profile.enabled:
        raise HTTPException(status_code=400, detail="Search profile is disabled")

    run = job_search_service.start_run(db, profile)
    background_tasks.add_task(_execute_run_background, run.id)
    return SearchRunAccepted(run_id=run.id, status=run.status)


@router.get(
    "/api/search-profiles/{profile_id}/runs",
    response_model=list[SearchRunOut],
)
def list_profile_runs(
    profile_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[SearchRunOut]:
    profile = search_repository.get_profile(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")
    runs = search_repository.list_runs(
        db, search_profile_id=profile_id, limit=limit, offset=offset
    )
    return [_serialize_run(run) for run in runs]


@router.get("/api/search-runs", response_model=list[SearchRunOut])
def list_search_runs(
    search_profile_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[SearchRunOut]:
    runs = search_repository.list_runs(
        db, search_profile_id=search_profile_id, limit=limit, offset=offset
    )
    return [_serialize_run(run) for run in runs]


@router.get("/api/search-runs/{run_id}", response_model=SearchRunOut)
def get_search_run(run_id: int, db: Session = Depends(get_db)) -> SearchRunOut:
    run = search_repository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Search run not found")
    return _serialize_run(run)


@router.post("/api/search/run-due", response_model=list[SearchRunOut])
def run_due_searches(db: Session = Depends(get_db)) -> list[SearchRunOut]:
    """
    Worker endpoint: execute due scheduled searches (rate-limited).

    Synchronous for the worker so it can log results; individual source
    failures are isolated inside the service.
    """
    settings = get_settings()
    if not settings.job_search_enabled:
        return []
    runs = job_search_service.run_due_profiles(db)
    return [_serialize_run(run) for run in runs]
