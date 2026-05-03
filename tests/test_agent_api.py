from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import AgentConfig, AppConfig, LoggingConfig, Settings
from app.main import create_app


def test_agent_chat_route_runs_jd_analysis() -> None:
    settings = Settings(
        app=AppConfig(name="Test JobPilot", env="test", debug=False),
        agent=AgentConfig(
            allowed_tools=["jd_analyzer"],
            max_iterations=3,
            enable_tool_calling=True,
        ),
        logging=LoggingConfig(level="CRITICAL", log_file=None),
    )
    app: FastAPI = create_app(settings)
    client = TestClient(app)

    response = client.post(
        "/agent/chat",
        json={
            "message": "请分析这个岗位 JD",
            "jd_text": "职位：Python 后端工程师\n任职要求：Python、FastAPI、SQL。",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "jd_analysis"
    assert payload["tool_calls"][0]["tool_name"] == "jd_analyzer"
    assert payload["tool_calls"][0]["status"] == "success"
    assert "Python" in payload["data"]["required_skills"]
