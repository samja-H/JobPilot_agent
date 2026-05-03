from __future__ import annotations

from app.agent.graph import run_agent_chat
from app.agent.nodes import intent_router
from app.core.config import AgentConfig, Settings
from app.schemas.agent import AgentChatRequest


def test_intent_router_detects_supported_intents() -> None:
    settings = _settings(["jd_analyzer", "resume_matcher", "rag_retriever"])

    jd_state = intent_router(
        {
            "request": AgentChatRequest(message="请分析这个岗位 JD", jd_text="Python 后端工程师"),
            "settings": settings,
        }
    )
    match_state = intent_router(
        {
            "request": AgentChatRequest(
                message="请做简历匹配评分",
                resume_text="Python FastAPI",
                jd_text="Python FastAPI SQL",
            ),
            "settings": settings,
        }
    )
    rag_state = intent_router(
        {
            "request": AgentChatRequest(message="请检索知识库回答这个问题"),
            "settings": settings,
        }
    )

    assert jd_state["intent"] == "jd_analysis"
    assert match_state["intent"] == "resume_match"
    assert rag_state["intent"] == "rag_qa"


def test_agent_blocks_tools_outside_allowed_list() -> None:
    settings = _settings(["jd_analyzer"])

    response = run_agent_chat(
        request=AgentChatRequest(
            message="请做简历匹配评分",
            resume_text="Python FastAPI",
            jd_text="Python FastAPI SQL",
        ),
        settings=settings,
    )

    assert response.intent == "resume_match"
    assert response.tool_calls[0].tool_name == "resume_matcher"
    assert response.tool_calls[0].status == "blocked"
    assert "白名单" in response.answer or "工具" in response.answer


def test_agent_resume_match_end_to_end_rules_flow() -> None:
    settings = _settings(["resume_matcher"])

    response = run_agent_chat(
        request=AgentChatRequest(
            message="请做简历匹配评分",
            resume_text="项目：使用 Python 和 FastAPI 开发后端服务。",
            jd_text="要求：Python、FastAPI、SQL。",
        ),
        settings=settings,
    )

    assert response.intent == "resume_match"
    assert response.tool_calls[0].tool_name == "resume_matcher"
    assert response.tool_calls[0].status == "success"
    assert response.data["overall_score"] >= 0
    assert response.data["matched_skills"] == ["Python", "FastAPI"]
    assert response.data["missing_skills"] == ["SQL"]


def test_agent_jd_analysis_end_to_end_rules_flow() -> None:
    settings = _settings(["jd_analyzer"])

    response = run_agent_chat(
        request=AgentChatRequest(
            message="请分析这个岗位 JD",
            jd_text="""
职位：AI 后端工程师
岗位职责：负责 FastAPI 后端 API 和 RAG 应用开发。
任职要求：Python、FastAPI、RAG、Qdrant。
""",
        ),
        settings=settings,
    )

    assert response.intent == "jd_analysis"
    assert response.tool_calls[0].tool_name == "jd_analyzer"
    assert response.tool_calls[0].status == "success"
    assert response.data["job_category"] == "AI / RAG 应用"
    assert "Python" in response.data["required_skills"]


def test_agent_rag_qa_uses_request_context_without_qdrant() -> None:
    settings = _settings(["rag_retriever"])

    response = run_agent_chat(
        request=AgentChatRequest(
            message="请检索知识库回答 JobPilot 的定位",
            rag_context=["JobPilot-Agent 是面向求职流程的 RAG 与 Tool Calling 应用。"],
        ),
        settings=settings,
    )

    assert response.intent == "rag_qa"
    assert response.tool_calls[0].tool_name == "rag_retriever"
    assert response.tool_calls[0].status == "success"
    assert "JobPilot-Agent" in response.answer


def _settings(allowed_tools: list[str]) -> Settings:
    return Settings(
        agent=AgentConfig(
            allowed_tools=allowed_tools,
            max_iterations=3,
            enable_tool_calling=True,
        )
    )
