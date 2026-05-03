from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import AppConfig, DatabaseConfig, LoggingConfig, Settings
from app.main import create_app


def test_applications_api_create_search_update(tmp_path: Path) -> None:
    settings = Settings(
        app=AppConfig(name="Test JobPilot", env="test", debug=False),
        database=DatabaseConfig(
            type="sqlite",
            sqlite_path=str(tmp_path / "api-applications.db"),
        ),
        logging=LoggingConfig(level="CRITICAL", log_file=None),
    )
    app: FastAPI = create_app(settings)
    client = TestClient(app)

    create_response = client.post(
        "/applications",
        json={
            "company": "Delta",
            "position": "Backend Engineer",
            "jd_text": "Python FastAPI",
            "resume_version": "v1",
            "status": "applied",
            "source": "Company site",
            "notes": "Submitted manually",
            "match_score": 88.0,
            "next_action": "Follow up",
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["company"] == "Delta"
    assert created["status"] == "applied"

    search_response = client.get("/applications", params={"status": "applied"})
    assert search_response.status_code == 200
    results = search_response.json()
    assert len(results) == 1
    assert results[0]["id"] == created["id"]

    update_response = client.patch(
        f"/applications/{created['id']}",
        json={
            "status": "interviewing",
            "next_action": "Prepare interview",
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == "interviewing"
    assert updated["next_action"] == "Prepare interview"
