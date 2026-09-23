"""Job CRUD API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.sample_jobs import RN_JOB


def test_create_and_get_job(client: TestClient) -> None:
    created = client.post("/api/jobs", json=RN_JOB)
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "React Native Developer"
    assert body["status"] == "new"

    fetched = client.get(f"/api/jobs/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


def test_list_jobs(client: TestClient) -> None:
    client.post("/api/jobs", json=RN_JOB)
    listed = client.get("/api/jobs")
    assert listed.status_code == 200
    assert len(listed.json()) >= 1


def test_delete_job(client: TestClient) -> None:
    created = client.post("/api/jobs", json=RN_JOB).json()
    deleted = client.delete(f"/api/jobs/{created['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/jobs/{created['id']}").status_code == 404


def test_duplicate_job_prevention(client: TestClient) -> None:
    assert client.post("/api/jobs", json=RN_JOB).status_code == 201
    dup = client.post("/api/jobs", json=RN_JOB)
    assert dup.status_code == 409


def test_job_analysis_endpoint(client: TestClient) -> None:
    created = client.post("/api/jobs", json=RN_JOB).json()
    analyzed = client.post(f"/api/jobs/{created['id']}/analyze")
    assert analyzed.status_code == 200
    payload = analyzed.json()
    assert payload["job"]["status"] == "analyzed"
    assert len(payload["job"]["skills"]) >= 5
    assert len(payload["matches"]) >= 1
    rn_matches = [m for m in payload["matches"] if m["profile_slug"] == "react-native"]
    assert rn_matches
    assert rn_matches[0]["role_match"] == "high"
    assert rn_matches[0]["match_score"] > 50

    matches = client.get(f"/api/jobs/{created['id']}/matches")
    assert matches.status_code == 200
    assert len(matches.json()) >= 1


def test_profiles_list(client: TestClient) -> None:
    response = client.get("/api/profiles")
    assert response.status_code == 200
    slugs = {p["slug"] for p in response.json()}
    assert {
        "react-native",
        "it-support",
        "teacher",
        "software-developer",
        "ai-python",
        "automation",
    }.issubset(slugs)


def test_health_still_works(client: TestClient) -> None:
    assert client.get("/health").status_code == 200
    assert client.get("/api/health").json()["service"] == "backend"
