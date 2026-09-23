"""Worker smoke tests."""

from unittest.mock import patch

from app.tasks import TASK_REGISTRY, heartbeat, run_enabled_tasks


def test_task_registry_has_process_new_jobs() -> None:
    names = {task.name for task in TASK_REGISTRY}
    assert "heartbeat" in names
    assert "process_new_jobs" in names
    assert any(t.name == "process_new_jobs" and t.enabled for t in TASK_REGISTRY)


def test_run_enabled_tasks_isolates_failures() -> None:
    with patch("app.tasks.process_new_jobs", side_effect=RuntimeError("boom")):
        with patch("app.tasks.heartbeat", wraps=heartbeat):
            # Should not raise even if process_new_jobs fails inside run_enabled_tasks
            # because each task is wrapped — but process_new_jobs is called via registry
            # reference. Patch the registry entry by patching httpx instead.
            pass

    with patch("app.tasks.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value.get.side_effect = RuntimeError(
            "offline"
        )
        run_enabled_tasks()
