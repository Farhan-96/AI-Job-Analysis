"""Worker smoke tests."""

from unittest.mock import MagicMock, patch

from app.tasks import TASK_REGISTRY, heartbeat, run_enabled_tasks


def test_task_registry_has_discovery_and_analysis() -> None:
    names = {task.name for task in TASK_REGISTRY}
    assert "heartbeat" in names
    assert "discover_jobs" in names
    assert "process_new_jobs" in names
    assert any(t.name == "discover_jobs" and t.enabled for t in TASK_REGISTRY)
    assert any(t.name == "process_new_jobs" and t.enabled for t in TASK_REGISTRY)


def test_run_enabled_tasks_isolates_failures() -> None:
    with patch("app.tasks.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value.get.side_effect = RuntimeError(
            "offline"
        )
        client_cls.return_value.__enter__.return_value.post.side_effect = RuntimeError(
            "offline"
        )
        run_enabled_tasks()


def test_discover_jobs_calls_run_due() -> None:
    from app.tasks import discover_jobs

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = [
        {
            "id": 1,
            "status": "completed",
            "jobs_found": 2,
            "jobs_imported": 1,
            "duplicates": 1,
        }
    ]

    with patch("app.tasks.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.post.return_value = mock_response
        discover_jobs()
        client.post.assert_called()
        assert "/api/search/run-due" in client.post.call_args[0][0]
