from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import AppConfig, LoggingConfig, Settings
from app.main import create_app


def test_jobs_analyze_route_returns_structured_result() -> None:
    settings = Settings(
        app=AppConfig(name="Test JobPilot", env="test", debug=False),
        logging=LoggingConfig(level="CRITICAL", log_file=None),
    )
    app: FastAPI = create_app(settings)
    client = TestClient(app)

    response = client.post(
        "/jobs/analyze",
        json={
            "jd_text": """
职位：Python 后端工程师
岗位职责：
1. 负责 FastAPI 服务开发和 REST API 设计。
任职要求：
- 熟悉 Python、FastAPI、SQL、Docker。
""",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_title"] == "Python 后端工程师"
    assert payload["job_category"] == "后端开发"
    assert "Python" in payload["required_skills"]
    assert "FastAPI" in payload["required_skills"]
    assert payload["analysis_mode"] == "rules"


def test_jobs_analyze_route_rejects_empty_jd() -> None:
    settings = Settings(
        app=AppConfig(name="Test JobPilot", env="test", debug=False),
        logging=LoggingConfig(level="CRITICAL", log_file=None),
    )
    app: FastAPI = create_app(settings)
    client = TestClient(app)

    response = client.post("/jobs/analyze", json={"jd_text": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "JD text must not be empty"
