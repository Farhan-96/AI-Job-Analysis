"""Backend health endpoint tests."""

from collections.abc import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.main import create_app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Provide a TestClient for the FastAPI app."""
    with TestClient(create_app()) as test_client:
        yield test_client


def test_root_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_health_returns_200(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "backend"}


def test_database_health_connected(client: TestClient) -> None:
    with patch("app.api.routes.health.check_database_connection", return_value=True):
        response = client.get("/api/health/database")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_database_health_disconnected(client: TestClient) -> None:
    with patch(
        "app.api.routes.health.check_database_connection",
        side_effect=OperationalError("SELECT 1", {}, Exception("connection refused")),
    ):
        response = client.get("/api/health/database")

    assert response.status_code == 503
    body = response.json()
    assert body["detail"]["status"] == "error"
    assert body["detail"]["database"] == "disconnected"
