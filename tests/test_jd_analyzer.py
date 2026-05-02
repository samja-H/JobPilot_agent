from __future__ import annotations

import pytest

from app.core.config import LLMConfig, SecretConfig, Settings
from app.schemas.job import JDAnalyzeRequest
from app.tools.jd_analyzer import analyze_jd_tool


SAMPLE_JD: str = """
职位：AI 后端工程师

岗位职责：
1. 负责基于 FastAPI 的后端 API 设计与开发。
2. 参与 RAG 检索增强系统建设，优化 Qdrant 向量检索效果。
3. 维护 Docker 部署流程，支持线上问题排查。

任职要求：
- 熟悉 Python、FastAPI、SQL、Redis。
- 理解 LangChain、Embedding、LLM 应用开发。

加分项：
- 有 LangGraph 或 Kubernetes 经验优先。
- 有高压抗压项目经验优先。
"""


def test_analyze_jd_extracts_skill_keywords() -> None:
    settings = Settings()

    result = analyze_jd_tool(JDAnalyzeRequest(jd_text=SAMPLE_JD), settings)

    assert result.analysis_mode == "rules"
    assert result.job_title == "AI 后端工程师"
    assert result.job_category == "AI / RAG 应用"
    assert "Python" in result.required_skills
    assert "FastAPI" in result.required_skills
    assert "RAG" in result.required_skills
    assert "Qdrant" in result.required_skills
    assert "LangGraph" in result.bonus_skills
    assert "Kubernetes" in result.bonus_skills
    assert "AI / RAG 应用" in result.resume_keywords
    assert any("Python" in topic for topic in result.interview_topics)
    assert any("压力" in risk or "抗压" in risk for risk in result.risk_points)


def test_analyze_jd_rejects_empty_input() -> None:
    settings = Settings()

    with pytest.raises(ValueError, match="JD text must not be empty"):
        analyze_jd_tool(JDAnalyzeRequest(jd_text="   "), settings)


def test_analyze_jd_uses_rules_without_api_key() -> None:
    settings = Settings(
        llm=LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=1200,
        ),
        secrets=SecretConfig(openai_api_key=None),
    )

    result = analyze_jd_tool(JDAnalyzeRequest(jd_text=SAMPLE_JD), settings)

    assert result.analysis_mode == "rules"
    assert result.required_skills
    assert result.resume_keywords
