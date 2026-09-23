"""Placeholder task registry for future scheduled automation."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

TaskFn = Callable[[], None]


@dataclass(frozen=True)
class ScheduledTask:
    """Descriptor for a future worker task."""

    name: str
    run: TaskFn
    enabled: bool = False


def heartbeat() -> None:
    """Lightweight heartbeat used to prove the worker loop is alive."""
    logger.debug("Worker heartbeat")


# Future tasks (job discovery, applications, etc.) register here.
TASK_REGISTRY: list[ScheduledTask] = [
    ScheduledTask(name="heartbeat", run=heartbeat, enabled=True),
]


def run_enabled_tasks() -> None:
    """Execute enabled tasks. Ready for Phase 2+ automation hooks."""
    for task in TASK_REGISTRY:
        if not task.enabled:
            continue
        try:
            task.run()
        except Exception:
            logger.exception("Task failed: %s", task.name)
