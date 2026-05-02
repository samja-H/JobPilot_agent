from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import AppConfig, LoggingConfig, Settings
from app.main import create_app


def test_health_check_returns_app_metadata() -> None:
    settings: Settings = Settings(
        app=AppConfig(name="Test JobPilot", env="test", debug=False),
        logging=LoggingConfig(level="CRITICAL", log_file=None),
    )
    app: FastAPI = create_app(settings)
    client: TestClient = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app_name": "Test JobPilot",
        "environment": "test",
    }
