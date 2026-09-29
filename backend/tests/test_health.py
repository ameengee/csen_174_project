import pytest
from fastapi.testclient import TestClient

from backend.configs.constants import API_VERSION, SERVICE_NAME


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"service": SERVICE_NAME, "status": "running", "version": API_VERSION}


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_reports_unhealthy_when_db_down(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _fail() -> None:
        raise ConnectionError("db down")

    monkeypatch.setattr("backend.server.routes.health.get_pool", _fail)

    response = client.get("/healthz/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy", "checks": {"database": False}}
