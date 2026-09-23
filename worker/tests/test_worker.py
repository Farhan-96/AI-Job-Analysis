"""Worker smoke tests."""

from app.tasks import TASK_REGISTRY, run_enabled_tasks


def test_task_registry_has_heartbeat() -> None:
    names = [task.name for task in TASK_REGISTRY]
    assert "heartbeat" in names


def test_run_enabled_tasks_does_not_raise() -> None:
    run_enabled_tasks()
