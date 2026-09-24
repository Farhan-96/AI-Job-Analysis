"""Job import orchestration — validate, normalize, dedupe, insert, record history."""

from __future__ import annotations

import csv
import io
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import JobStatus
from app.models.import_history import JobImport
from app.models.job import Job
from app.repositories import job_repository
from app.services.normalization import (
    detect_remote_type,
    normalize_company,
    normalize_employment_type,
    normalize_location,
    normalize_title,
)
from app.sources import RawJob, get_source, normalize_via_attributed_source

logger = logging.getLogger(__name__)

_META_IMPORT_CHANNELS = frozenset({"csv", "json", "json_import", "api"})

CSV_COLUMNS = (
    "source",
    "source_job_id",
    "title",
    "company",
    "location",
    "remote_type",
    "url",
    "description",
    "salary_min",
    "salary_max",
    "salary_currency",
    "employment_type",
    "posted_at",
)


@dataclass
class ImportStats:
    imported: int = 0
    duplicates: int = 0
    failed: int = 0
    total_rows: int = 0
    errors: list[str] = field(default_factory=list)
    import_id: int | None = None
    created_job_ids: list[int] = field(default_factory=list)


def _parse_posted_at(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    # Prefer ISO-8601; tolerate trailing Z
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _job_from_raw(
    raw: RawJob,
    posted_at: datetime | None = None,
    *,
    search_profile_id: int | None = None,
) -> Job:
    title = normalize_title(raw.title)
    location = normalize_location(raw.location)
    remote = raw.remote_type or detect_remote_type(location, raw.description)
    resolved_posted = posted_at or _parse_posted_at(raw.posted_at)

    return Job(
        source=raw.source,
        source_job_id=raw.source_job_id,
        search_profile_id=search_profile_id,
        title=title,
        company=normalize_company(raw.company),
        location=location,
        remote_type=remote,
        url=raw.url,
        description=raw.description or "",
        salary_min=raw.salary_min,
        salary_max=raw.salary_max,
        salary_currency=raw.salary_currency,
        employment_type=normalize_employment_type(raw.employment_type),
        posted_at=resolved_posted,
        raw_data=raw.raw_data,
        status=JobStatus.NEW.value,
        normalized_title=title,
    )


def _find_duplicate(db: Session, raw: RawJob) -> Job | None:
    """Prefer source + source_job_id; URL-based ids already encode normalized URL."""
    return job_repository.get_job_by_source(db, raw.source, raw.source_job_id)


def _record_history(
    db: Session,
    *,
    source: str,
    import_type: str,
    stats: ImportStats,
) -> JobImport:
    error_summary = None
    if stats.errors:
        # Cap stored summary length
        joined = "; ".join(stats.errors[:20])
        error_summary = joined[:4000]

    record = JobImport(
        source=source,
        import_type=import_type,
        total_count=stats.total_rows,
        imported_count=stats.imported,
        duplicate_count=stats.duplicates,
        failed_count=stats.failed,
        error_summary=error_summary,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    stats.import_id = record.id
    return record


class JobImportService:
    """
    Shared import pipeline used by manual, CSV, and JSON endpoints.

    Flow: validate → normalize (JobSource) → dedupe → insert (status=new) → history
    Analysis is left to the worker.
    """

    def import_jobs(
        self,
        db: Session,
        *,
        source: str,
        jobs: list[dict[str, Any]],
        import_type: str = "manual",
        search_profile_id: int | None = None,
        record_history: bool = True,
    ) -> ImportStats:
        stats = ImportStats(total_rows=len(jobs))
        primary_source = (source or "manual").strip().lower() or "manual"

        for index, payload in enumerate(jobs):
            try:
                row = dict(payload)
                if not row.get("source"):
                    row["source"] = primary_source
                row_source = str(row["source"]).strip().lower() or primary_source

                if row_source in _META_IMPORT_CHANNELS:
                    raw = normalize_via_attributed_source(row, default_source="manual")
                else:
                    raw = get_source(row_source).normalize_job({**row, "source": row_source})

                existing = _find_duplicate(db, raw)
                if existing:
                    stats.duplicates += 1
                    continue

                job = _job_from_raw(
                    raw,
                    posted_at=_parse_posted_at(row.get("posted_at")),
                    search_profile_id=search_profile_id,
                )
                db.add(job)
                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()
                    stats.duplicates += 1
                    continue
                db.refresh(job)
                stats.imported += 1
                stats.created_job_ids.append(job.id)
                logger.info(
                    "Imported job id=%s source=%s source_job_id=%s",
                    job.id,
                    job.source,
                    job.source_job_id,
                )
            except Exception as exc:  # noqa: BLE001 — isolate per-row failures
                db.rollback()
                stats.failed += 1
                stats.errors.append(f"row {index + 1}: {exc}")
                logger.warning("Import row %s failed: %s", index + 1, exc)

        if record_history:
            _record_history(
                db,
                source=primary_source,
                import_type=import_type,
                stats=stats,
            )
        return stats

    def import_raw_jobs(
        self,
        db: Session,
        *,
        source: str,
        raw_jobs: list[RawJob],
        import_type: str = "search",
        search_profile_id: int | None = None,
        record_history: bool = True,
    ) -> ImportStats:
        """Import already-normalized RawJob objects (search pipeline)."""
        payloads: list[dict[str, Any]] = []
        for raw in raw_jobs:
            payloads.append(
                {
                    "source": raw.source,
                    "source_job_id": raw.source_job_id,
                    "title": raw.title,
                    "company": raw.company,
                    "location": raw.location,
                    "url": raw.url,
                    "description": raw.description,
                    "salary_min": raw.salary_min,
                    "salary_max": raw.salary_max,
                    "salary_currency": raw.salary_currency,
                    "employment_type": raw.employment_type,
                    "remote_type": raw.remote_type,
                    "posted_at": raw.posted_at,
                    "raw_data": raw.raw_data,
                }
            )
        return self.import_jobs(
            db,
            source=source,
            jobs=payloads,
            import_type=import_type,
            search_profile_id=search_profile_id,
            record_history=record_history,
        )

    def import_csv(self, db: Session, content: str | bytes) -> ImportStats:
        if isinstance(content, bytes):
            content = content.decode("utf-8-sig")

        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            stats = ImportStats(failed=1, total_rows=0, errors=["CSV has no header row"])
            _record_history(db, source="csv", import_type="csv", stats=stats)
            return stats

        fieldnames = [f.strip().lower() for f in reader.fieldnames if f]
        if "title" not in fieldnames:
            stats = ImportStats(
                failed=1,
                total_rows=0,
                errors=["CSV must include a 'title' column"],
            )
            _record_history(db, source="csv", import_type="csv", stats=stats)
            return stats

        rows: list[dict[str, Any]] = []
        for row in reader:
            cleaned: dict[str, Any] = {}
            for key, value in row.items():
                if key is None:
                    continue
                cleaned[key.strip().lower()] = (
                    value.strip() if isinstance(value, str) else value
                )
            if not any(v not in (None, "") for v in cleaned.values()):
                continue
            rows.append(cleaned)

        history_source = "csv"
        for row in rows:
            if row.get("source"):
                history_source = str(row["source"]).strip().lower()
                break

        return self.import_jobs(
            db,
            source=history_source,
            jobs=rows,
            import_type="csv",
        )

    def import_json(self, db: Session, content: str | bytes | list | dict) -> ImportStats:
        if isinstance(content, (str, bytes)):
            if isinstance(content, bytes):
                content = content.decode("utf-8-sig")
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as exc:
                stats = ImportStats(
                    failed=1,
                    total_rows=0,
                    errors=[f"Invalid JSON: {exc}"],
                )
                _record_history(db, source="json", import_type="json", stats=stats)
                return stats
        else:
            parsed = content

        jobs: list[dict[str, Any]]
        source = "manual"

        if isinstance(parsed, dict):
            if "jobs" in parsed and isinstance(parsed["jobs"], list):
                jobs = parsed["jobs"]
                source = str(parsed.get("source") or "manual").strip().lower() or "manual"
            else:
                jobs = [parsed]
                source = str(parsed.get("source") or "manual").strip().lower() or "manual"
        elif isinstance(parsed, list):
            jobs = parsed
            if jobs and isinstance(jobs[0], dict) and jobs[0].get("source"):
                source = str(jobs[0]["source"]).strip().lower()
        else:
            stats = ImportStats(
                failed=1,
                total_rows=0,
                errors=["JSON must be an object, an array of jobs, or {source, jobs}"],
            )
            _record_history(db, source="json", import_type="json", stats=stats)
            return stats

        normalized_jobs: list[dict[str, Any]] = []
        pre_errors: list[str] = []
        for index, item in enumerate(jobs):
            if not isinstance(item, dict):
                pre_errors.append(
                    f"row {index + 1}: expected object, got {type(item).__name__}"
                )
                continue
            normalized_jobs.append(item)

        stats = self.import_jobs(
            db,
            source=source,
            jobs=normalized_jobs,
            import_type="json",
        )
        if pre_errors:
            stats.failed += len(pre_errors)
            stats.total_rows += len(pre_errors)
            stats.errors = pre_errors + stats.errors
            if stats.import_id:
                record = db.get(JobImport, stats.import_id)
                if record:
                    record.failed_count = stats.failed
                    record.total_count = stats.total_rows
                    record.error_summary = "; ".join(stats.errors[:20])[:4000]
                    db.commit()
        return stats


job_import_service = JobImportService()
