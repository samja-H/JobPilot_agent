from __future__ import annotations

import pytest

from app.core.config import LLMConfig, MatchingConfig, SecretConfig, Settings
from app.schemas.resume import ResumeMatchRequest
from app.tools.resume_matcher import match_resume_to_jd_tool


def test_resume_matcher_scores_skill_matches() -> None:
    settings = Settings()
    request = ResumeMatchRequest(
        resume_text="项目：使用 Python 和 FastAPI 开发后端 API。",
        jd_text="要求：熟悉 Python、FastAPI、SQL、Redis。",
    )

    result = match_resume_to_jd_tool(request=request, settings=settings)

    assert result.analysis_mode == "rules"
    assert result.skill_match_score == 50.0
    assert result.matched_skills == ["Python", "FastAPI"]
    assert result.missing_skills == ["SQL", "Redis"]
    assert any("SQL" in weakness and "Redis" in weakness for weakness in result.weaknesses)


def test_resume_matcher_scores_keyword_coverage() -> None:
    settings = Settings()
    request = ResumeMatchRequest(
        resume_text="Python FastAPI Docker",
        jd_text="Python FastAPI Docker",
    )

    result = match_resume_to_jd_tool(request=request, settings=settings)

    assert result.keyword_coverage_score == 100.0
    assert result.skill_match_score == 100.0


def test_resume_matcher_calculates_weighted_overall_score() -> None:
    settings = Settings(
        matching=MatchingConfig(
            skill_weight=0.5,
            project_weight=0.25,
            keyword_weight=0.25,
        )
    )
    request = ResumeMatchRequest(
        resume_text="""
技能：Python、FastAPI、Docker。
项目：负责 FastAPI 后端服务开发，使用 Docker 部署并支持 API 问题排查。
""",
        jd_text="要求：Python、FastAPI、SQL、Docker。职责：负责后端 API 开发和部署。",
    )

    result = match_resume_to_jd_tool(request=request, settings=settings)
    expected_score = round(
        result.skill_match_score * 0.5
        + result.project_match_score * 0.25
        + result.keyword_coverage_score * 0.25,
        2,
    )

    assert result.overall_score == expected_score
    assert 0.0 <= result.overall_score <= 100.0


def test_resume_matcher_rejects_empty_input() -> None:
    settings = Settings()

    with pytest.raises(ValueError, match="resume_text and jd_text must not be empty"):
        match_resume_to_jd_tool(
            request=ResumeMatchRequest(resume_text="", jd_text="Python"),
            settings=settings,
        )


def test_resume_matcher_uses_rules_without_api_key() -> None:
    settings = Settings(
        llm=LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=1200,
        ),
        secrets=SecretConfig(openai_api_key=None),
    )
    request = ResumeMatchRequest(
        resume_text="项目：使用 Python 和 FastAPI 构建 RAG 应用。",
        jd_text="要求：Python、FastAPI、RAG。",
    )

    result = match_resume_to_jd_tool(request=request, settings=settings)

    assert result.analysis_mode == "rules"
    assert result.overall_score > 0
    assert result.matched_skills == ["Python", "FastAPI", "RAG"]
