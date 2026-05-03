from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import AppConfig, LoggingConfig, Settings
from app.main import create_app


def test_resume_match_route_returns_structured_scores() -> None:
    settings = Settings(
        app=AppConfig(name="Test JobPilot", env="test", debug=False),
        logging=LoggingConfig(level="CRITICAL", log_file=None),
    )
    app: FastAPI = create_app(settings)
    client = TestClient(app)

    response = client.post(
        "/resume/match",
        json={
            "resume_text": "项目：使用 Python 和 FastAPI 开发后端服务，并用 Docker 部署。",
            "jd_text": "要求：Python、FastAPI、SQL、Docker。",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_mode"] == "rules"
    assert payload["overall_score"] >= 0
    assert payload["skill_match_score"] == 75.0
    assert payload["matched_skills"] == ["Python", "FastAPI", "Docker"]
    assert payload["missing_skills"] == ["SQL"]
    assert payload["suggestions"]


def test_resume_match_route_rejects_empty_input() -> None:
    settings = Settings(
        app=AppConfig(name="Test JobPilot", env="test", debug=False),
        logging=LoggingConfig(level="CRITICAL", log_file=None),
    )
    app: FastAPI = create_app(settings)
    client = TestClient(app)

    response = client.post(
        "/resume/match",
        json={
            "resume_text": "",
            "jd_text": "Python",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "resume_text and jd_text must not be empty"


def test_resume_rewrite_route_returns_template_result() -> None:
    settings = Settings(
        app=AppConfig(name="Test JobPilot", env="test", debug=False),
        logging=LoggingConfig(level="CRITICAL", log_file=None),
    )
    app: FastAPI = create_app(settings)
    client = TestClient(app)

    response = client.post(
        "/resume/rewrite",
        json={
            "resume_text": "熟悉 Python、FastAPI 和 RAG 应用开发。",
            "project_experience": "项目：负责使用 FastAPI 搭建 RAG 检索服务。",
            "jd_text": "要求：Python、FastAPI、RAG、Qdrant。",
            "rag_context": ["历史项目中使用 Qdrant 做向量检索。"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_mode"] == "rules"
    assert "FastAPI" in payload["skill_keywords"]
    assert payload["optimized_project_description"]
    assert payload["bullet_points"]
    assert payload["highlight_points"]
    assert payload["risk_warnings"]
