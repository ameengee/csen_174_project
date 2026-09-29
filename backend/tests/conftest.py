import os
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Settings are read at import time (rate limits, CORS), so set the environment before any test
# module imports the app. A monkeypatch fixture would run too late.
os.environ["APP_ENV"] = "test"
os.environ["AUTO_FAIL_ALL"] = "false"
os.environ["JSON_LOGS"] = "true"
os.environ["LOG_LEVEL"] = "WARNING"


@pytest.fixture
def app() -> FastAPI:
    """Provide FastAPI application instance for testing."""
    from backend.main import app as fastapi_app

    return fastapi_app


@pytest.fixture
def client(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Provide FastAPI test client with external clients stubbed out."""

    async def _noop() -> None:
        return None

    monkeypatch.setattr("backend.main.init_clients", _noop)
    monkeypatch.setattr("backend.main.close_clients", _noop)

    with TestClient(app) as test_client:
        yield test_client
