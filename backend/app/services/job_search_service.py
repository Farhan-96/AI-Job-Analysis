"""Job search orchestration — discover via JobSource, import via JobImportService."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import SearchRunStatus
from app.models.search import JobSearchProfile, JobSearchRun
from app.repositories import profile_repository, search_repository
from app.seed_data.search_profiles import SEARCH_PROFILE_SEEDS
from app.services.job_import_service import job_import_service
from app.sources import SearchCriteria, get_source

logger = logging.getLogger(__name__)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "search-profile"


class JobSearchService:
    """
    Search scheduler / runner.

    Flow: JobSearchProfile → JobSource.search() → JobImportService → status=new
    Analysis is left to the worker (never run inside the search request).
    """

    def seed_default_profiles(self, db: Session) -> int:
        created = 0
        for data in SEARCH_PROFILE_SEEDS:
            if search_repository.get_profile_by_slug(db, data["slug"]):
                continue
            resume = profile_repository.get_profile_by_slug(
                db, data["resume_profile_slug"]
            )
            profile = JobSearchProfile(
                name=data["name"],
                slug=data["slug"],
                enabled=data.get("enabled", True),
                keywords=list(data["keywords"]),
                locations=list(data["locations"]),
                remote_types=list(data.get("remote_types") or []),
                source=data.get("source", "mock"),
                schedule_enabled=data.get("schedule_enabled", False),
                schedule_interval_minutes=int(
                    data.get("schedule_interval_minutes") or 60
                ),
                resume_profile_id=resume.id if resume else None,
            )
            db.add(profile)
            created += 1
        if created:
            db.commit()
        logger.info("Seeded search profiles created=%s", created)
        return created

    def create_profile(
        self,
        db: Session,
        *,
        name: str,
        slug: str | None = None,
        keywords: list[str],
        locations: list[str],
        remote_types: list[str] | None = None,
        source: str = "mock",
        enabled: bool = True,
        schedule_enabled: bool = False,
        schedule_interval_minutes: int = 60,
        resume_profile_id: int | None = None,
    ) -> JobSearchProfile:
        resolved_slug = slug or _slugify(name)
        if search_repository.get_profile_by_slug(db, resolved_slug):
            raise ValueError(f"Search profile slug already exists: {resolved_slug}")
        if resume_profile_id is not None:
            if not profile_repository.get_profile(db, resume_profile_id):
                raise ValueError("resume_profile_id not found")

        settings = get_settings()
        interval = max(
            schedule_interval_minutes,
            max(1, settings.search_min_interval_seconds // 60),
        )
        profile = JobSearchProfile(
            name=name.strip(),
            slug=resolved_slug,
            enabled=enabled,
            keywords=[k.strip() for k in keywords if k and str(k).strip()],
            locations=[loc.strip() for loc in locations if loc and str(loc).strip()],
            remote_types=[
                rt.strip().lower() for rt in (remote_types or []) if rt and str(rt).strip()
            ],
            source=(source or "mock").strip().lower(),
            schedule_enabled=schedule_enabled,
            schedule_interval_minutes=interval,
            resume_profile_id=resume_profile_id,
        )
        return search_repository.create_profile(db, profile)

    def update_profile(
        self,
        db: Session,
        profile: JobSearchProfile,
        *,
        name: str | None = None,
        keywords: list[str] | None = None,
        locations: list[str] | None = None,
        remote_types: list[str] | None = None,
        source: str | None = None,
        enabled: bool | None = None,
        schedule_enabled: bool | None = None,
        schedule_interval_minutes: int | None = None,
        resume_profile_id: int | None = None,
        clear_resume_profile: bool = False,
    ) -> JobSearchProfile:
        settings = get_settings()
        if name is not None:
            profile.name = name.strip()
        if keywords is not None:
            profile.keywords = [k.strip() for k in keywords if k and str(k).strip()]
        if locations is not None:
            profile.locations = [
                loc.strip() for loc in locations if loc and str(loc).strip()
            ]
        if remote_types is not None:
            profile.remote_types = [
                rt.strip().lower() for rt in remote_types if rt and str(rt).strip()
            ]
        if source is not None:
            profile.source = source.strip().lower()
        if enabled is not None:
            profile.enabled = enabled
        if schedule_enabled is not None:
            profile.schedule_enabled = schedule_enabled
        if schedule_interval_minutes is not None:
            profile.schedule_interval_minutes = max(
                schedule_interval_minutes,
                max(1, settings.search_min_interval_seconds // 60),
            )
        if clear_resume_profile:
            profile.resume_profile_id = None
        elif resume_profile_id is not None:
            if not profile_repository.get_profile(db, resume_profile_id):
                raise ValueError("resume_profile_id not found")
            profile.resume_profile_id = resume_profile_id
        return search_repository.save_profile(db, profile)

    def start_run(self, db: Session, profile: JobSearchProfile) -> JobSearchRun:
        """Create a running JobSearchRun without executing the search yet."""
        run = JobSearchRun(
            search_profile_id=profile.id,
            source=profile.source,
            status=SearchRunStatus.RUNNING.value,
            started_at=datetime.now(timezone.utc),
        )
        return search_repository.create_run(db, run)

    def execute_run(self, db: Session, run_id: int) -> JobSearchRun:
        """
        Execute a previously created search run.

        Isolates source failures — marks run failed, never crashes the caller.
        """
        run = search_repository.get_run(db, run_id)
        if not run:
            raise ValueError(f"Search run {run_id} not found")
        profile = search_repository.get_profile(db, run.search_profile_id)
        if not profile:
            run.status = SearchRunStatus.FAILED.value
            run.error_message = "search profile missing"
            run.completed_at = datetime.now(timezone.utc)
            return search_repository.save_run(db, run)

        settings = get_settings()
        keywords = list(profile.keywords or [])
        locations = list(profile.locations or [])

        logger.info("Starting job search")
        logger.info("Search profile: %s", profile.name)
        logger.info("Source: %s", profile.source)
        logger.info("Keywords: %s", len(keywords))
        logger.info("Locations: %s", len(locations))

        try:
            source = get_source(profile.source)
            criteria = SearchCriteria(
                keywords=keywords,
                locations=locations,
                remote_types=list(profile.remote_types or []),
                max_jobs=settings.max_jobs_per_search,
                profile_slug=profile.slug,
                profile_name=profile.name,
            )
            discovered = source.search(criteria)
            # Cap again in case adapter ignores max_jobs
            discovered = discovered[: settings.max_jobs_per_search]
            run.jobs_found = len(discovered)

            stats = job_import_service.import_raw_jobs(
                db,
                source=profile.source,
                raw_jobs=discovered,
                import_type="search",
                search_profile_id=profile.id,
                record_history=True,
            )
            run.jobs_imported = stats.imported
            run.duplicates = stats.duplicates
            run.failed = stats.failed
            run.status = SearchRunStatus.COMPLETED.value
            run.error_message = None
            if stats.errors:
                run.error_message = "; ".join(stats.errors[:10])[:2000]

            logger.info("Search completed")
            logger.info("Found: %s", run.jobs_found)
            logger.info("Imported: %s", run.jobs_imported)
            logger.info("Duplicates: %s", run.duplicates)
        except Exception as exc:  # noqa: BLE001 — isolate source failures
            logger.warning(
                "Search failed for profile=%s source=%s: %s",
                profile.name,
                profile.source,
                exc,
            )
            run.status = SearchRunStatus.FAILED.value
            run.error_message = str(exc)[:2000]
            # Prefer a stable short message for unavailable sources
            if "source unavailable" in str(exc).lower():
                run.error_message = "source unavailable"

        run.completed_at = datetime.now(timezone.utc)
        profile.last_run_at = run.completed_at
        search_repository.save_profile(db, profile)
        return search_repository.save_run(db, run)

    def run_profile(self, db: Session, profile: JobSearchProfile) -> JobSearchRun:
        """Synchronous helper used by tests — start + execute."""
        run = self.start_run(db, profile)
        return self.execute_run(db, run.id)

    def run_due_profiles(self, db: Session) -> list[JobSearchRun]:
        """Run scheduled profiles that are due (rate-limited)."""
        settings = get_settings()
        due = search_repository.list_due_profiles(
            db,
            min_interval_seconds=settings.search_min_interval_seconds,
            max_searches=settings.max_searches_per_cycle,
        )
        results: list[JobSearchRun] = []
        for profile in due:
            try:
                results.append(self.run_profile(db, profile))
            except Exception:
                logger.exception(
                    "Scheduled search crashed for profile=%s — continuing",
                    profile.name,
                )
        return results


job_search_service = JobSearchService()
