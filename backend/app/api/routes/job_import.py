"""Job import API routes — manual, CSV, JSON, history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.repositories import import_repository
from app.schemas.job_import import (
    JobImportHistoryItem,
    JobImportRequest,
    JobImportResult,
    JobSourceConfigOut,
)
from app.services.job_import_service import job_import_service

router = APIRouter(prefix="/api/jobs/import", tags=["job-import"])


def _ensure_import_enabled() -> None:
    if not get_settings().job_import_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Job import is disabled (JOB_IMPORT_ENABLED=false)",
        )


def _to_result(stats) -> JobImportResult:
    return JobImportResult(
        imported=stats.imported,
        duplicates=stats.duplicates,
        failed=stats.failed,
        total_rows=stats.total_rows,
        errors=stats.errors,
        import_id=stats.import_id,
    )


@router.post("", response_model=JobImportResult)
def import_jobs_manual(
    payload: JobImportRequest,
    db: Session = Depends(get_db),
) -> JobImportResult:
    """Import one or more jobs from a JSON body. Analysis is deferred to the worker."""
    _ensure_import_enabled()
    jobs = [item.model_dump(mode="json") for item in payload.jobs]
    stats = job_import_service.import_jobs(
        db,
        source=payload.source,
        jobs=jobs,
        import_type="manual",
    )
    return _to_result(stats)


@router.post("/csv", response_model=JobImportResult)
async def import_jobs_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> JobImportResult:
    """Import jobs from a CSV file. Bad rows are isolated; analysis is deferred."""
    _ensure_import_enabled()
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty CSV file",
        )
    stats = job_import_service.import_csv(db, content)
    return _to_result(stats)


@router.post("/json", response_model=JobImportResult)
async def import_jobs_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> JobImportResult:
    """Import jobs from a JSON file. Uses the same JobImportService pipeline."""
    _ensure_import_enabled()
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty JSON file",
        )
    stats = job_import_service.import_json(db, content)
    return _to_result(stats)


@router.get("/history", response_model=list[JobImportHistoryItem])
def import_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[JobImportHistoryItem]:
    records = import_repository.list_import_history(db, limit=limit, offset=offset)
    return [JobImportHistoryItem.model_validate(r) for r in records]


@router.get("/sources", response_model=list[JobSourceConfigOut])
def list_import_sources(
    enabled_only: bool = False,
    db: Session = Depends(get_db),
) -> list[JobSourceConfigOut]:
    configs = import_repository.list_source_configs(db, enabled_only=enabled_only)
    return [JobSourceConfigOut.model_validate(c) for c in configs]
