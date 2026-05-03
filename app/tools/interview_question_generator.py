from __future__ import annotations

from app.core.config import Settings
from app.schemas.interview import InterviewQuestionRequest, InterviewQuestionResponse
from app.tools.prompts import render_interview_questions_prompt
from app.tools.resume_matcher import _extract_skills


def generate_interview_questions_tool(
    request: InterviewQuestionRequest,
    settings: Settings,
) -> InterviewQuestionResponse:
    resume_text: str = request.resume_text.strip()
    project_experience: str = request.project_experience.strip()
    jd_text: str = request.jd_text.strip()
    if not resume_text or not project_experience or not jd_text:
        raise ValueError("resume_text, project_experience and jd_text must not be empty")

    llm_result: InterviewQuestionResponse | None = _try_llm_generate(
        request=request,
        settings=settings,
    )
    if llm_result is not None:
        return llm_result

    return _generate_with_rules(request)


def _try_llm_generate(
    request: InterviewQuestionRequest,
    settings: Settings,
) -> InterviewQuestionResponse | None:
    provider: str = settings.llm.provider.lower()
    api_key: str | None = _api_key_for_provider(settings)
    prompt: str = render_interview_questions_prompt(
        resume_text=request.resume_text,
        project_experience=request.project_experience,
        jd_text=request.jd_text,
        rag_context=request.rag_context,
    )
    llm_config: tuple[str, str, float, int] = (
        provider,
        settings.llm.model,
        settings.llm.temperature,
        settings.llm.max_tokens,
    )

    if not api_key:
        return None

    _ = prompt, llm_config, api_key
    return None


def _generate_with_rules(request: InterviewQuestionRequest) -> InterviewQuestionResponse:
    skills: list[str] = _unique_non_empty(
        [
            *_extract_skills(request.jd_text),
            *_extract_skills(request.resume_text),
            *_extract_skills(request.project_experience),
        ]
    )
    primary_skills: list[str] = skills[:5] or ["目标岗位核心技术"]
    project_summary: str = _first_non_empty_line(request.project_experience)
    rag_topic: str = _first_non_empty_line("\n".join(request.rag_context)) if request.rag_context else "RAG 检索证据"

    technical_questions: list[str] = [
        f"你在项目中如何使用 {skill}？遇到过什么问题，如何定位和解决？"
        for skill in primary_skills[:4]
    ]
    project_questions: list[str] = [
        f"请围绕这个项目说明背景、目标、你的职责和最终结果：{project_summary}",
        "项目中最复杂的技术决策是什么？你如何评估不同方案？",
        "如果重新设计这个项目，你会优先改进哪些部分？",
    ]
    rag_agent_questions: list[str] = [
        f"如果把该项目接入 {rag_topic}，你会如何设计检索、上下文拼接和评估流程？",
        "如何降低 RAG 场景中的幻觉、召回不足和上下文污染风险？",
        "你会如何设计 Tool Calling 的输入输出 schema，保证工具调用稳定可测？",
    ]
    behavioral_questions: list[str] = [
        "讲一次你在项目中推动跨角色协作的经历，遇到了什么阻力？",
        "讲一次线上问题或高压交付场景，你如何判断优先级并推进解决？",
        "面对不熟悉的技术栈，你通常如何快速学习并形成可交付结果？",
    ]
    suggested_answers_outline: list[str] = [
        "回答技术问题时按背景、方案、取舍、问题、结果的顺序组织。",
        "项目问题要突出个人贡献，避免只描述团队整体成果。",
        "RAG/Agent 问题要覆盖数据来源、检索参数、Prompt、工具 schema 和评估指标。",
        "行为面回答建议使用 STAR：情境、任务、行动、结果。",
    ]

    return InterviewQuestionResponse(
        technical_questions=technical_questions,
        project_questions=project_questions,
        rag_agent_questions=rag_agent_questions,
        behavioral_questions=behavioral_questions,
        suggested_answers_outline=suggested_answers_outline,
        analysis_mode="rules",
    )


def _api_key_for_provider(settings: Settings) -> str | None:
    provider: str = settings.llm.provider.lower()
    if provider == "openai":
        return settings.secrets.openai_api_key
    if provider == "dashscope":
        return settings.secrets.dashscope_api_key
    if provider == "deepseek":
        return settings.secrets.deepseek_api_key
    return None


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped: str = line.strip()
        if stripped:
            return stripped
    return "项目经历"


def _unique_non_empty(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        normalized_item: str = item.strip()
        if not normalized_item or normalized_item in seen:
            continue
        seen.add(normalized_item)
        unique_items.append(normalized_item)
    return unique_items
