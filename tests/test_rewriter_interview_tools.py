from __future__ import annotations

from app.core.config import LLMConfig, SecretConfig, Settings
from app.schemas.interview import InterviewQuestionRequest
from app.schemas.resume import ResumeRewriteRequest
from app.tools.interview_question_generator import generate_interview_questions_tool
from app.tools.resume_rewriter import rewrite_resume_project_tool


def test_resume_rewriter_generates_template_without_api_key() -> None:
    settings = Settings(
        llm=LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=1200,
        ),
        secrets=SecretConfig(openai_api_key=None),
    )
    request = ResumeRewriteRequest(
        resume_text="熟悉 Python、FastAPI、RAG。",
        project_experience="项目：负责使用 FastAPI 搭建 RAG 检索服务。",
        jd_text="要求：Python、FastAPI、RAG、Qdrant。",
        rag_context=["候选人有 Qdrant 向量检索经验。"],
    )

    result = rewrite_resume_project_tool(request=request, settings=settings)

    assert result.analysis_mode == "rules"
    assert "Python" in result.skill_keywords
    assert "FastAPI" in result.skill_keywords
    assert result.optimized_project_description
    assert len(result.bullet_points) >= 3
    assert all("编造" not in bullet for bullet in result.bullet_points)


def test_interview_generator_generates_template_without_api_key() -> None:
    settings = Settings(
        llm=LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=1200,
        ),
        secrets=SecretConfig(openai_api_key=None),
    )
    request = InterviewQuestionRequest(
        resume_text="熟悉 Python、FastAPI、RAG。",
        project_experience="项目：负责使用 FastAPI 搭建 RAG 检索服务。",
        jd_text="要求：Python、FastAPI、RAG、Qdrant。",
        rag_context=["候选人有 Qdrant 向量检索经验。"],
    )

    result = generate_interview_questions_tool(request=request, settings=settings)

    assert result.analysis_mode == "rules"
    assert any("Python" in question for question in result.technical_questions)
    assert result.project_questions
    assert result.rag_agent_questions
    assert result.behavioral_questions
    assert result.suggested_answers_outline
