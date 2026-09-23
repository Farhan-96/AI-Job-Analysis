"""AI Job Assistant worker entrypoint.

Phase 1: start, log readiness, and remain running.
Future phases: scheduled job discovery and application automation.
"""

from __future__ import annotations

import logging
import signal
import sys
import time

from app.config import get_settings
from app.logging_config import configure_logging
from app.tasks import run_enabled_tasks

configure_logging()
logger = logging.getLogger(__name__)

_shutdown = False


def _handle_signal(signum: int, _frame: object) -> None:
    global _shutdown
    logger.info("Received signal %s — shutting down worker", signum)
    _shutdown = True


def main() -> int:
    settings = get_settings()
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("AI Job Assistant worker started")
    logger.info(
        "Poll interval: %s seconds (no job automation in Phase 1)",
        settings.worker_poll_interval_seconds,
    )

    while not _shutdown:
        run_enabled_tasks()
        # Sleep in small increments so SIGTERM is handled promptly
        for _ in range(settings.worker_poll_interval_seconds):
            if _shutdown:
                break
            time.sleep(1)

    logger.info("AI Job Assistant worker stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
