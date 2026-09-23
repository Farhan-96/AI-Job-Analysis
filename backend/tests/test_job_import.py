"""Phase 3 Step 1 — job import pipeline tests."""

from __future__ import annotations

import io
import json

from fastapi.testclient import TestClient

SAMPLE_CSV = """source,source_job_id,title,company,location,url,description
indeed,1001,React Native Developer,Example,Islamabad,https://example.com/1,"React Native developer with TypeScript"
indeed,1002,IT Support Engineer,Example,Rawalpindi,https://example.com/2,"IT support and networking"
"""

SAMPLE_JSON = {
    "source": "indeed",
    "jobs": [
        {
            "source_job_id": "j1",
            "title": "Software Developer",
            "company": "Acme",
            "location": "Lahore",
            "url": "https://example.com/j1",
            "description": "Python and FastAPI developer",
        },
        {
            "source_job_id": "j2",
            "title": "Teacher",
            "company": "School",
            "location": "Islamabad",
            "url": "https://example.com/j2",
            "description": "Mathematics teacher",
        },
    ],
}


def test_manual_import(client: TestClient) -> None:
    response = client.post(
        "/api/jobs/import",
        json={
            "source": "indeed",
            "jobs": [
                {
                    "source_job_id": "12345",
                    "title": "React Native Developer",
                    "company": "Example Company",
                    "location": "Islamabad",
                    "url": "https://example.com/job",
                    "description": "React Native with TypeScript",
                    "employment_type": "Full-time",
                }
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["imported"] == 1
    assert body["duplicates"] == 0
    assert body["failed"] == 0

    jobs = client.get("/api/jobs", params={"status": "new"}).json()
    assert any(j["title"] == "React Native Developer" for j in jobs)


def test_csv_import(client: TestClient) -> None:
    files = {"file": ("jobs.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")}
    response = client.post("/api/jobs/import/csv", files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["imported"] == 2
    assert body["duplicates"] == 0
    assert body["failed"] == 0
    assert body["total_rows"] == 2


def test_json_import(client: TestClient) -> None:
    payload = json.dumps(SAMPLE_JSON).encode("utf-8")
    files = {"file": ("jobs.json", payload, "application/json")}
    response = client.post("/api/jobs/import/json", files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["imported"] == 2
    assert body["failed"] == 0


def test_duplicate_detection_same_csv_twice(client: TestClient) -> None:
    files = {"file": ("jobs.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")}
    first = client.post("/api/jobs/import/csv", files=files)
    assert first.status_code == 200
    assert first.json()["imported"] == 2

    files2 = {"file": ("jobs.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")}
    second = client.post("/api/jobs/import/csv", files=files2)
    assert second.status_code == 200
    body = second.json()
    assert body["imported"] == 0
    assert body["duplicates"] == 2
    assert body["failed"] == 0


def test_invalid_csv_missing_title_column(client: TestClient) -> None:
    bad = b"source,company\nindeed,Acme\n"
    files = {"file": ("bad.csv", bad, "text/csv")}
    response = client.post("/api/jobs/import/csv", files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["failed"] >= 1
    assert body["imported"] == 0
    assert any("title" in e.lower() for e in body["errors"])


def test_invalid_csv_bad_row_isolated(client: TestClient) -> None:
    csv_text = (
        "source,source_job_id,title,company,location,url,description\n"
        "indeed,ok1,Good Job,Co,Islamabad,https://example.com/ok,Desc\n"
        "indeed,bad1,,Co,Islamabad,https://example.com/bad,Missing title\n"
        "indeed,ok2,Another Job,Co,Lahore,https://example.com/ok2,Desc\n"
    )
    files = {"file": ("mixed.csv", csv_text.encode("utf-8"), "text/csv")}
    response = client.post("/api/jobs/import/csv", files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["imported"] == 2
    assert body["failed"] == 1
    assert body["total_rows"] == 3


def test_invalid_json(client: TestClient) -> None:
    files = {"file": ("bad.json", b"{not-json", "application/json")}
    response = client.post("/api/jobs/import/json", files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["imported"] == 0
    assert body["failed"] >= 1
    assert any("json" in e.lower() for e in body["errors"])


def test_missing_required_fields(client: TestClient) -> None:
    response = client.post(
        "/api/jobs/import",
        json={"source": "indeed", "jobs": [{"description": "no title"}]},
    )
    # Pydantic validation on request body
    assert response.status_code == 422


def test_indeed_requires_id_or_url(client: TestClient) -> None:
    response = client.post(
        "/api/jobs/import",
        json={
            "source": "indeed",
            "jobs": [{"title": "No Id Job", "description": "x"}],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["imported"] == 0
    assert body["failed"] == 1


def test_bulk_import_marks_new_without_analyzing(client: TestClient) -> None:
    jobs = [
        {
            "source_job_id": f"bulk-{i}",
            "title": f"Bulk Job {i}",
            "company": "BulkCo",
            "location": "Islamabad",
            "url": f"https://example.com/bulk/{i}",
            "description": "React Native TypeScript developer role",
        }
        for i in range(25)
    ]
    response = client.post(
        "/api/jobs/import",
        json={"source": "indeed", "jobs": jobs},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["imported"] == 25
    assert body["failed"] == 0

    listed = client.get("/api/jobs", params={"status": "new", "limit": 50}).json()
    bulk = [j for j in listed if j["title"].startswith("Bulk Job")]
    assert len(bulk) == 25
    # Import must not analyze synchronously
    assert all(j["status"] == "new" for j in bulk)
    assert all(j.get("top_match") is None for j in bulk)


def test_import_history(client: TestClient) -> None:
    client.post(
        "/api/jobs/import",
        json={
            "source": "manual",
            "jobs": [
                {
                    "source_job_id": "hist-1",
                    "title": "History Job",
                    "description": "desc",
                }
            ],
        },
    )
    history = client.get("/api/jobs/import/history")
    assert history.status_code == 200
    rows = history.json()
    assert len(rows) >= 1
    latest = rows[0]
    assert "import_type" in latest
    assert "imported_count" in latest
    assert "duplicate_count" in latest
    assert "failed_count" in latest
    assert "created_at" in latest


def test_worker_can_process_imported_jobs(client: TestClient) -> None:
    """Imported jobs stay new until analyze is called (worker path)."""
    created = client.post(
        "/api/jobs/import",
        json={
            "source": "indeed",
            "jobs": [
                {
                    "source_job_id": "worker-1",
                    "title": "React Native Engineer",
                    "company": "WorkerCo",
                    "location": "Islamabad",
                    "description": "React Native TypeScript Redux Expo",
                }
            ],
        },
    )
    assert created.json()["imported"] == 1

    new_jobs = client.get("/api/jobs", params={"status": "new"}).json()
    target = next(j for j in new_jobs if j["title"] == "React Native Engineer")
    analyzed = client.post(f"/api/jobs/{target['id']}/analyze")
    assert analyzed.status_code == 200
    assert analyzed.json()["job"]["status"] == "analyzed"
    assert len(analyzed.json()["matches"]) >= 1


def test_list_source_configs(client: TestClient) -> None:
    # Seed happens on app lifespan; for TestClient lifespan runs
    response = client.get("/api/jobs/import/sources")
    assert response.status_code == 200
    slugs = {s["slug"] for s in response.json()}
    assert "manual" in slugs
    assert "indeed" in slugs
    assert "csv" in slugs


def test_date_filter_on_list(client: TestClient) -> None:
    client.post(
        "/api/jobs/import",
        json={
            "source": "manual",
            "jobs": [{"source_job_id": "df-1", "title": "Date Filter Job", "description": "x"}],
        },
    )
    # Far-future date → empty
    empty = client.get("/api/jobs", params={"date_from": "2099-01-01T00:00:00Z"})
    assert empty.status_code == 200
    assert empty.json() == []

    # Past date → includes job
    found = client.get("/api/jobs", params={"date_from": "2020-01-01T00:00:00Z"})
    assert found.status_code == 200
    assert any(j["title"] == "Date Filter Job" for j in found.json())
