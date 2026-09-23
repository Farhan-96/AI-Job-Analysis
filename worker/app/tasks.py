"""Worker task registry — Phase 2 analyzes new jobs via backend API."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

TaskFn = Callable[[], None]


@dataclass(frozen=True)
class ScheduledTask:
    """Descriptor for a scheduled worker task."""

    name: str
    run: TaskFn
    enabled: bool = False


def heartbeat() -> None:
    """Lightweight heartbeat used to prove the worker loop is alive."""
    logger.debug("Worker heartbeat")


def process_new_jobs() -> None:
    """
    Find jobs with status=new and ask the backend to analyze them.

    Uses the backend HTTP API so analysis logic stays in one place.
    Failed jobs are logged; processing continues for the rest of the batch.
    """
    settings = get_settings()
    base = settings.backend_url.rstrip("/")
    batch_size = settings.worker_batch_size

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.get(
                f"{base}/api/jobs",
                params={"status": "new", "limit": batch_size},
            )
            response.raise_for_status()
            jobs = response.json()
    except Exception:
        logger.exception("Failed to fetch new jobs from backend")
        return

    if not jobs:
        logger.debug("No new jobs to process")
        return

    logger.info("Found %s new job(s) to analyze", len(jobs))

    with httpx.Client(timeout=120.0) as client:
        for job in jobs:
            job_id = job.get("id")
            title = job.get("title", "")
            try:
                logger.info("Processing job %s (%s)", job_id, title)
                analyze = client.post(f"{base}/api/jobs/{job_id}/analyze")
                analyze.raise_for_status()
                payload = analyze.json()
                matches = payload.get("matches") or []
                skills = (payload.get("job") or {}).get("skills") or []
                logger.info("Extracted %s skills for job %s", len(skills), job_id)
                if matches:
                    best = max(matches, key=lambda m: m.get("match_score", 0))
                    logger.info(
                        "Matched profile: %s",
                        best.get("profile_name") or best.get("profile_id"),
                    )
                    logger.info("Match score: %s", best.get("match_score"))
                logger.info("Job %s analyzed successfully", job_id)
            except Exception:
                logger.exception("Job analysis failed for id=%s — continuing", job_id)


TASK_REGISTRY: list[ScheduledTask] = [
    ScheduledTask(name="heartbeat", run=heartbeat, enabled=True),
    ScheduledTask(name="process_new_jobs", run=process_new_jobs, enabled=True),
]


def run_enabled_tasks() -> None:
    """Execute enabled tasks. Individual task failures are isolated."""
    for task in TASK_REGISTRY:
        if not task.enabled:
            continue
        try:
            task.run()
        except Exception:
            logger.exception("Task failed: %s", task.name)
