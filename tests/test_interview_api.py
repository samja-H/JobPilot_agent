from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import AppConfig, LoggingConfig, Settings
from app.main import create_app


def test_interview_questions_route_returns_structured_questions() -> None:
    settings = Settings(
        app=AppConfig(name="Test JobPilot", env="test", debug=False),
        logging=LoggingConfig(level="CRITICAL", log_file=None),
    )
    app: FastAPI = create_app(settings)
    client = TestClient(app)

    response = client.post(
        "/interview/questions",
        json={
            "resume_text": "熟悉 Python、FastAPI、RAG。",
            "project_experience": "项目：负责使用 FastAPI 搭建 RAG 检索服务。",
            "jd_text": "要求：Python、FastAPI、RAG、Qdrant。",
            "rag_context": ["候选人有 Qdrant 向量检索经验。"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_mode"] == "rules"
    assert payload["technical_questions"]
    assert payload["project_questions"]
    assert payload["rag_agent_questions"]
    assert payload["behavioral_questions"]
    assert payload["suggested_answers_outline"]
