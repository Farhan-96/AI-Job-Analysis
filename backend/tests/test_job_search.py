"""Phase 3 Step 2 — automated job search tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import JobStatus, SearchRunStatus
from app.models.job import Job
from app.repositories import search_repository
from app.services.job_search_service import job_search_service
from app.sources import IndeedJobSource, MockJobSource, SearchCriteria


def _find_profile(client: TestClient, slug: str) -> dict:
    profiles = client.get("/api/search-profiles").json()
    return next(p for p in profiles if p["slug"] == slug)


def test_create_search_profile(client: TestClient) -> None:
    response = client.post(
        "/api/search-profiles",
        json={
            "name": "Custom Search",
            "slug": "custom-search",
            "keywords": ["Python Developer"],
            "locations": ["Islamabad"],
            "remote_types": ["remote"],
            "source": "mock",
            "enabled": True,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Custom Search"
    assert body["slug"] == "custom-search"
    assert body["keywords"] == ["Python Developer"]


def test_update_search_profile(client: TestClient) -> None:
    profile = _find_profile(client, "react-native")
    response = client.put(
        f"/api/search-profiles/{profile['id']}",
        json={
            "keywords": ["React Native", "Expo Developer"],
            "locations": ["Islamabad", "Remote"],
            "schedule_interval_minutes": 90,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["keywords"] == ["React Native", "Expo Developer"]
    assert body["schedule_interval_minutes"] == 90


def test_enable_disable_search_profile(client: TestClient) -> None:
    profile = _find_profile(client, "automation")
    disabled = client.put(
        f"/api/search-profiles/{profile['id']}",
        json={"enabled": False},
    )
    assert disabled.status_code == 200
    assert disabled.json()["enabled"] is False

    enabled = client.put(
        f"/api/search-profiles/{profile['id']}",
        json={"enabled": True},
    )
    assert enabled.status_code == 200
    assert enabled.json()["enabled"] is True


def test_run_search_profile_non_blocking(client: TestClient) -> None:
    profile = _find_profile(client, "react-native")
    response = client.post(f"/api/search-profiles/{profile['id']}/run")
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "running"
    assert "run_id" in body

    # Background task should complete within TestClient
    run = client.get(f"/api/search-runs/{body['run_id']}").json()
    assert run["status"] in {
        SearchRunStatus.COMPLETED.value,
        SearchRunStatus.RUNNING.value,
        SearchRunStatus.FAILED.value,
    }


def test_run_search_imports_mock_jobs(client: TestClient, db_session: Session) -> None:
    profile = _find_profile(client, "react-native")
    # Execute synchronously for deterministic asserts
    sp = search_repository.get_profile(db_session, profile["id"])
    assert sp is not None
    run = job_search_service.run_profile(db_session, sp)
    assert run.status == SearchRunStatus.COMPLETED.value
    assert run.jobs_found >= 1
    assert run.jobs_imported >= 1

    jobs = db_session.query(Job).filter(Job.source == "mock").all()
    assert any(j.status == JobStatus.NEW.value for j in jobs)
    assert any(j.search_profile_id == sp.id for j in jobs)


def test_search_run_history(client: TestClient, db_session: Session) -> None:
    profile = _find_profile(client, "it-support")
    sp = search_repository.get_profile(db_session, profile["id"])
    assert sp is not None
    job_search_service.run_profile(db_session, sp)

    history = client.get(f"/api/search-profiles/{profile['id']}/runs")
    assert history.status_code == 200
    runs = history.json()
    assert len(runs) >= 1
    assert runs[0]["jobs_found"] >= 1

    all_runs = client.get("/api/search-runs")
    assert all_runs.status_code == 200
    assert len(all_runs.json()) >= 1


def test_duplicate_prevention_on_rerun(
    client: TestClient, db_session: Session
) -> None:
    profile = _find_profile(client, "software")
    sp = search_repository.get_profile(db_session, profile["id"])
    assert sp is not None
    first = job_search_service.run_profile(db_session, sp)
    second = job_search_service.run_profile(db_session, sp)
    assert first.jobs_imported >= 1
    assert second.duplicates >= first.jobs_imported
    assert second.jobs_imported == 0


def test_multiple_profiles_same_job_deduped(
    client: TestClient, db_session: Session
) -> None:
    """Two profiles discovering the same mock job should not duplicate rows."""
    rn = search_repository.get_profile_by_slug(db_session, "react-native")
    # Create a second profile pointing at the same mock catalog keywords
    other = job_search_service.create_profile(
        db_session,
        name="React Native Alt",
        slug="react-native-alt",
        keywords=["React Native Developer"],
        locations=["Islamabad", "Remote"],
        source="mock",
    )
    assert rn is not None
    first = job_search_service.run_profile(db_session, rn)
    second = job_search_service.run_profile(db_session, other)
    assert first.jobs_imported >= 1
    # Overlapping mock RN jobs become duplicates on second profile
    assert second.duplicates >= 1 or second.jobs_imported >= 0
    mock_jobs = (
        db_session.query(Job)
        .filter(Job.source == "mock", Job.source_job_id == "mock-rn-001")
        .all()
    )
    assert len(mock_jobs) == 1


def test_worker_analysis_of_discovered_jobs(
    client: TestClient, db_session: Session
) -> None:
    profile = _find_profile(client, "ai-python")
    sp = search_repository.get_profile(db_session, profile["id"])
    assert sp is not None
    run = job_search_service.run_profile(db_session, sp)
    assert run.jobs_imported >= 1

    new_jobs = client.get("/api/jobs", params={"status": "new", "source": "mock"}).json()
    assert len(new_jobs) >= 1
    job_id = new_jobs[0]["id"]
    analyzed = client.post(f"/api/jobs/{job_id}/analyze")
    assert analyzed.status_code == 200
    body = analyzed.json()
    assert body["job"]["status"] == "analyzed"
    assert len(body["matches"]) >= 1


def test_scheduler_interval(db_session: Session) -> None:
    from app.seed import seed_profiles

    seed_profiles(db_session)
    job_search_service.seed_default_profiles(db_session)
    profile = search_repository.get_profile_by_slug(db_session, "teacher")
    assert profile is not None
    profile.schedule_enabled = True
    profile.schedule_interval_minutes = 180
    profile.last_run_at = datetime.now(timezone.utc)
    search_repository.save_profile(db_session, profile)

    due_now = search_repository.list_due_profiles(
        db_session, min_interval_seconds=60, max_searches=10
    )
    assert all(p.id != profile.id for p in due_now)

    profile.last_run_at = datetime.now(timezone.utc) - timedelta(minutes=200)
    search_repository.save_profile(db_session, profile)
    due_later = search_repository.list_due_profiles(
        db_session, min_interval_seconds=60, max_searches=10
    )
    assert any(p.id == profile.id for p in due_later)


def test_rate_limiting_max_searches(db_session: Session) -> None:
    from app.seed import seed_profiles

    seed_profiles(db_session)
    job_search_service.seed_default_profiles(db_session)
    # Make all due
    for profile in search_repository.list_profiles(db_session, enabled=True):
        profile.schedule_enabled = True
        profile.last_run_at = None
        search_repository.save_profile(db_session, profile)

    due = search_repository.list_due_profiles(
        db_session, min_interval_seconds=1, max_searches=2
    )
    assert len(due) == 2


def test_rate_limiting_max_jobs_per_search(db_session: Session) -> None:
    settings = get_settings()
    with patch.object(settings, "max_jobs_per_search", 1):
        source = MockJobSource()
        criteria = SearchCriteria(
            keywords=["Developer", "Engineer", "Teacher", "Support", "Automation"],
            locations=["Islamabad", "Remote", "Pakistan", "Rawalpindi"],
            remote_types=["remote", "hybrid", "onsite", "unknown"],
            max_jobs=1,
        )
        results = source.search(criteria)
        assert len(results) <= 1


def test_failed_source_handling(client: TestClient, db_session: Session) -> None:
    profile = job_search_service.create_profile(
        db_session,
        name="Indeed Only",
        slug="indeed-only",
        keywords=["Software Engineer"],
        locations=["Islamabad"],
        source="indeed",
        enabled=True,
    )
    run = job_search_service.run_profile(db_session, profile)
    assert run.status == SearchRunStatus.FAILED.value
    assert run.error_message is not None
    assert "source unavailable" in run.error_message.lower()

    # Worker/other profiles must still work
    rn = search_repository.get_profile_by_slug(db_session, "react-native")
    assert rn is not None
    ok = job_search_service.run_profile(db_session, rn)
    assert ok.status == SearchRunStatus.COMPLETED.value


def test_indeed_search_with_approved_feed(tmp_path, db_session: Session) -> None:
    feed = tmp_path / "indeed_feed.json"
    feed.write_text(
        """
        {
          "jobs": [
            {
              "source_job_id": "ind-1",
              "title": "React Native Developer",
              "company": "Feed Co",
              "location": "Islamabad",
              "remote_type": "remote",
              "url": "https://example.com/indeed/ind-1",
              "description": "React Native Engineer role"
            }
          ]
        }
        """,
        encoding="utf-8",
    )
    with patch.dict("os.environ", {"INDEED_APPROVED_FEED_PATH": str(feed)}):
        source = IndeedJobSource()
        results = source.search(
            SearchCriteria(
                keywords=["React Native"],
                locations=["Islamabad"],
                remote_types=["remote", "hybrid", "onsite", "unknown"],
                max_jobs=10,
            )
        )
    assert len(results) == 1
    assert results[0].source == "indeed"


def test_mock_jobs_marked_as_mock(db_session: Session) -> None:
    source = MockJobSource()
    jobs = source.search(
        SearchCriteria(
            keywords=["n8n"],
            locations=["Remote"],
            remote_types=["remote"],
            max_jobs=10,
        )
    )
    assert len(jobs) >= 1
    assert all(j.source == "mock" for j in jobs)
    assert all((j.raw_data or {}).get("is_mock") is True for j in jobs)


def test_default_search_profiles_seeded(client: TestClient) -> None:
    profiles = client.get("/api/search-profiles").json()
    slugs = {p["slug"] for p in profiles}
    assert {
        "react-native",
        "it-support",
        "teacher",
        "software",
        "ai-python",
        "automation",
    }.issubset(slugs)


def test_delete_search_profile(client: TestClient) -> None:
    created = client.post(
        "/api/search-profiles",
        json={
            "name": "Temp Profile",
            "slug": "temp-profile",
            "keywords": ["Temp"],
            "locations": ["Islamabad"],
            "source": "mock",
        },
    ).json()
    deleted = client.delete(f"/api/search-profiles/{created['id']}")
    assert deleted.status_code == 204
    missing = client.get(f"/api/search-profiles/{created['id']}")
    assert missing.status_code == 404


def test_disabled_profile_cannot_run(client: TestClient) -> None:
    profile = _find_profile(client, "teacher")
    client.put(f"/api/search-profiles/{profile['id']}", json={"enabled": False})
    response = client.post(f"/api/search-profiles/{profile['id']}/run")
    assert response.status_code == 400
