from __future__ import annotations

from app.core.config import Settings
from app.schemas.resume import ResumeRewriteRequest, ResumeRewriteResponse
from app.tools.prompts import render_resume_rewrite_prompt
from app.tools.resume_matcher import _extract_skills


def rewrite_resume_project_tool(
    request: ResumeRewriteRequest,
    settings: Settings,
) -> ResumeRewriteResponse:
    resume_text: str = request.resume_text.strip()
    project_experience: str = request.project_experience.strip()
    jd_text: str = request.jd_text.strip()
    if not resume_text or not project_experience or not jd_text:
        raise ValueError("resume_text, project_experience and jd_text must not be empty")

    llm_result: ResumeRewriteResponse | None = _try_llm_rewrite(
        request=request,
        settings=settings,
    )
    if llm_result is not None:
        return llm_result

    return _rewrite_with_rules(request)


def _try_llm_rewrite(
    request: ResumeRewriteRequest,
    settings: Settings,
) -> ResumeRewriteResponse | None:
    provider: str = settings.llm.provider.lower()
    api_key: str | None = _api_key_for_provider(settings)
    prompt: str = render_resume_rewrite_prompt(
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


def _rewrite_with_rules(request: ResumeRewriteRequest) -> ResumeRewriteResponse:
    jd_skills: list[str] = _extract_skills(request.jd_text)
    resume_skills: list[str] = _extract_skills(request.resume_text)
    project_skills: list[str] = _extract_skills(request.project_experience)
    skill_keywords: list[str] = _unique_non_empty([*jd_skills, *resume_skills, *project_skills])[:10]
    missing_skills: list[str] = [skill for skill in jd_skills if skill not in project_skills]
    action: str = _pick_action(request.project_experience)
    project_summary: str = _compact_text(request.project_experience, max_length=120)
    target_skills: str = "、".join(skill_keywords[:5]) if skill_keywords else "岗位相关技术栈"

    optimized_project_description: str = (
        f"围绕目标岗位要求，突出使用 {target_skills} {action}核心模块，"
        f"结合项目背景说明个人贡献，并用可量化结果支撑影响：{project_summary}"
    )
    bullet_points: list[str] = [
        f"使用 {target_skills} {action}项目核心功能，明确承担的模块边界和技术决策。",
        "补充性能、稳定性、交付效率或业务指标，形成可验证的量化结果。",
        "将 JD 中出现的关键技能自然嵌入项目描述，避免无证据的关键词堆砌。",
    ]
    highlight_points: list[str] = [
        "个人职责清晰：写清自己负责的模块、接口、数据流或工程化工作。",
        "技术取舍清晰：说明为什么选择对应方案，以及如何处理复杂问题。",
        "结果导向清晰：补充吞吐、延迟、准确率、转化率、交付周期等指标。",
    ]
    risk_warnings: list[str] = _build_risk_warnings(
        missing_skills=missing_skills,
        rag_context=request.rag_context,
    )

    return ResumeRewriteResponse(
        optimized_project_description=optimized_project_description,
        bullet_points=bullet_points,
        skill_keywords=skill_keywords,
        highlight_points=highlight_points,
        risk_warnings=risk_warnings,
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


def _pick_action(project_experience: str) -> str:
    text: str = project_experience.lower()
    if "优化" in text or "performance" in text:
        return "优化"
    if "设计" in text or "架构" in text or "design" in text:
        return "设计"
    if "搭建" in text or "建设" in text or "build" in text:
        return "搭建"
    return "开发"


def _compact_text(text: str, max_length: int) -> str:
    normalized: str = " ".join(line.strip() for line in text.splitlines() if line.strip())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[:max_length].rstrip()}..."


def _build_risk_warnings(
    missing_skills: list[str],
    rag_context: list[str],
) -> list[str]:
    warnings: list[str] = []
    if missing_skills:
        warnings.append(f"项目经历尚未体现 JD 技能：{', '.join(missing_skills[:6])}。")
    if not rag_context:
        warnings.append("缺少 RAG 检索证据，优化建议仅基于输入文本生成。")
    warnings.append("不要编造未真实参与的职责、指标或技术细节。")
    return warnings


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
