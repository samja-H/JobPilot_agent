from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response

from app.core.config import Settings
from app.main import create_app


def test_health_check_returns_app_metadata() -> None:
    settings: Settings = Settings(
        app_name="Test JobPilot",
        environment="test",
        log_level="CRITICAL",
    )
    app: FastAPI = create_app(settings)
    client: TestClient = TestClient(app)

    response: Response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app_name": "Test JobPilot",
        "environment": "test",
    }

