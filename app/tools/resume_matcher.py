from __future__ import annotations

import re

from app.core.config import Settings
from app.schemas.resume import ResumeMatchRequest, ResumeMatchResponse
from app.tools.jd_analyzer import SKILL_ALIASES

PROJECT_MARKERS: tuple[str, ...] = (
    "项目",
    "project",
    "系统",
    "平台",
    "服务",
    "负责",
    "实现",
    "开发",
    "设计",
    "优化",
    "搭建",
    "建设",
    "上线",
    "落地",
)

DOMAIN_KEYWORDS: tuple[str, ...] = (
    "RAG",
    "LLM",
    "Embedding",
    "向量检索",
    "向量数据库",
    "后端",
    "API",
    "性能优化",
    "高并发",
    "数据库",
    "缓存",
    "微服务",
    "部署",
    "监控",
    "测试",
    "业务结果",
)

STOPWORDS: set[str] = {
    "and",
    "or",
    "the",
    "with",
    "for",
    "to",
    "in",
    "of",
    "a",
    "an",
    "is",
    "are",
    "job",
    "role",
    "team",
}


def match_resume_to_jd_tool(
    request: ResumeMatchRequest,
    settings: Settings,
) -> ResumeMatchResponse:
    resume_text: str = request.resume_text.strip()
    jd_text: str = request.jd_text.strip()
    if not resume_text or not jd_text:
        raise ValueError("resume_text and jd_text must not be empty")

    llm_result: ResumeMatchResponse | None = _try_llm_match(resume_text, jd_text, settings)
    if llm_result is not None:
        return llm_result

    return _match_with_rules(resume_text=resume_text, jd_text=jd_text, settings=settings)


def _try_llm_match(
    resume_text: str,
    jd_text: str,
    settings: Settings,
) -> ResumeMatchResponse | None:
    provider: str = settings.llm.provider.lower()
    api_key: str | None = _api_key_for_provider(settings)
    llm_config: tuple[str, str, float, int] = (
        provider,
        settings.llm.model,
        settings.llm.temperature,
        settings.llm.max_tokens,
    )

    if not api_key:
        return None

    _ = resume_text, jd_text, llm_config, api_key
    return None


def _api_key_for_provider(settings: Settings) -> str | None:
    provider: str = settings.llm.provider.lower()
    if provider == "openai":
        return settings.secrets.openai_api_key
    if provider == "dashscope":
        return settings.secrets.dashscope_api_key
    if provider == "deepseek":
        return settings.secrets.deepseek_api_key
    return None


def _match_with_rules(
    resume_text: str,
    jd_text: str,
    settings: Settings,
) -> ResumeMatchResponse:
    jd_skills: list[str] = _extract_skills(jd_text)
    resume_skills: list[str] = _extract_skills(resume_text)
    matched_skills: list[str] = [skill for skill in jd_skills if skill in resume_skills]
    missing_skills: list[str] = [skill for skill in jd_skills if skill not in resume_skills]

    skill_match_score: float = _coverage_score(matched_skills, jd_skills)

    jd_keywords: list[str] = _extract_keywords(jd_text)
    resume_keywords: list[str] = _extract_keywords(resume_text)
    matched_keywords: list[str] = [
        keyword for keyword in jd_keywords if _contains_keyword(keyword, resume_text, resume_keywords)
    ]
    keyword_coverage_score: float = _coverage_score(matched_keywords, jd_keywords)

    project_match_score: float = _calculate_project_match_score(
        resume_text=resume_text,
        jd_skills=jd_skills,
        jd_keywords=jd_keywords,
    )
    overall_score: float = _calculate_overall_score(
        skill_match_score=skill_match_score,
        project_match_score=project_match_score,
        keyword_coverage_score=keyword_coverage_score,
        settings=settings,
    )

    return ResumeMatchResponse(
        overall_score=overall_score,
        skill_match_score=skill_match_score,
        project_match_score=project_match_score,
        keyword_coverage_score=keyword_coverage_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        weaknesses=_build_weaknesses(
            missing_skills=missing_skills,
            skill_match_score=skill_match_score,
            project_match_score=project_match_score,
            keyword_coverage_score=keyword_coverage_score,
        ),
        suggestions=_build_suggestions(
            missing_skills=missing_skills,
            matched_skills=matched_skills,
            skill_match_score=skill_match_score,
            project_match_score=project_match_score,
            keyword_coverage_score=keyword_coverage_score,
        ),
        analysis_mode="rules",
    )


def _extract_skills(text: str) -> list[str]:
    normalized_text: str = f" {text.lower()} "
    skills: list[str] = []
    for skill, aliases in SKILL_ALIASES.items():
        if any(alias.lower() in normalized_text for alias in aliases):
            skills.append(skill)
    return skills


def _extract_keywords(text: str) -> list[str]:
    keywords: list[str] = _extract_skills(text)
    lower_text: str = text.lower()

    for keyword in DOMAIN_KEYWORDS:
        if keyword.lower() in lower_text:
            keywords.append(keyword)

    english_terms: list[str] = re.findall(r"\b[A-Za-z][A-Za-z0-9+#.\-]{2,}\b", text)
    for term in english_terms:
        normalized_term: str = term.strip()
        if normalized_term.lower() in STOPWORDS:
            continue
        keywords.append(normalized_term)

    return _unique_non_empty(keywords)[:30]


def _calculate_project_match_score(
    resume_text: str,
    jd_skills: list[str],
    jd_keywords: list[str],
) -> float:
    project_text: str = _extract_project_text(resume_text)
    if not project_text:
        return 0.0

    signals: list[str] = _unique_non_empty([*jd_skills, *jd_keywords])[:20]
    if not signals:
        return 0.0

    covered_signals: list[str] = [
        signal for signal in signals if _contains_text(project_text, signal)
    ]
    signal_score: float = _coverage_score(covered_signals, signals)

    project_line_count: int = len(
        [
            line
            for line in _non_empty_lines(resume_text)
            if any(marker.lower() in line.lower() for marker in PROJECT_MARKERS)
        ]
    )
    evidence_score: float = min(100.0, project_line_count * 20.0)
    return _round_score(signal_score * 0.75 + evidence_score * 0.25)


def _extract_project_text(resume_text: str) -> str:
    lines: list[str] = _non_empty_lines(resume_text)
    project_lines: list[str] = [
        line
        for line in lines
        if any(marker.lower() in line.lower() for marker in PROJECT_MARKERS)
    ]
    return "\n".join(project_lines)


def _calculate_overall_score(
    skill_match_score: float,
    project_match_score: float,
    keyword_coverage_score: float,
    settings: Settings,
) -> float:
    skill_weight, project_weight, keyword_weight = _normalized_weights(settings)
    return _round_score(
        skill_match_score * skill_weight
        + project_match_score * project_weight
        + keyword_coverage_score * keyword_weight
    )


def _normalized_weights(settings: Settings) -> tuple[float, float, float]:
    skill_weight: float = max(0.0, settings.matching.skill_weight)
    project_weight: float = max(0.0, settings.matching.project_weight)
    keyword_weight: float = max(0.0, settings.matching.keyword_weight)
    total_weight: float = skill_weight + project_weight + keyword_weight
    if total_weight == 0:
        return 0.4, 0.35, 0.25
    return (
        skill_weight / total_weight,
        project_weight / total_weight,
        keyword_weight / total_weight,
    )


def _build_weaknesses(
    missing_skills: list[str],
    skill_match_score: float,
    project_match_score: float,
    keyword_coverage_score: float,
) -> list[str]:
    weaknesses: list[str] = []
    if missing_skills:
        weaknesses.append(f"JD 要求的技能尚未覆盖：{', '.join(missing_skills[:8])}。")
    if skill_match_score < 70:
        weaknesses.append("技能匹配度不足，需要更明确地呈现与 JD 对应的技术栈。")
    if project_match_score < 60:
        weaknesses.append("项目经历与岗位职责的关联度不够，需要补充相关项目证据。")
    if keyword_coverage_score < 60:
        weaknesses.append("简历关键词覆盖不足，可能影响初筛和 ATS 命中。")
    if not weaknesses:
        weaknesses.append("主要技能和关键词覆盖较好，后续可进一步强化量化结果。")
    return weaknesses


def _build_suggestions(
    missing_skills: list[str],
    matched_skills: list[str],
    skill_match_score: float,
    project_match_score: float,
    keyword_coverage_score: float,
) -> list[str]:
    suggestions: list[str] = []
    if missing_skills:
        suggestions.append(f"补充或强化这些 JD 技能的项目证据：{', '.join(missing_skills[:6])}。")
    if matched_skills:
        suggestions.append(f"将已匹配技能前置到简历摘要或技能栏：{', '.join(matched_skills[:6])}。")
    if project_match_score < 80:
        suggestions.append("在项目经历中写清背景、个人动作、技术方案和量化结果。")
    if keyword_coverage_score < 80:
        suggestions.append("参考 JD 原词补齐关键词，但避免无经验关键词堆砌。")
    if skill_match_score >= 80 and project_match_score >= 80:
        suggestions.append("当前匹配度较高，可重点优化业务影响和面试可讲述案例。")
    return _unique_non_empty(suggestions)


def _coverage_score(matched_items: list[str], required_items: list[str]) -> float:
    unique_required: list[str] = _unique_non_empty(required_items)
    if not unique_required:
        return 0.0
    unique_matched: set[str] = set(_unique_non_empty(matched_items))
    return _round_score((len(unique_matched) / len(unique_required)) * 100.0)


def _contains_keyword(keyword: str, text: str, extracted_keywords: list[str]) -> bool:
    return keyword in extracted_keywords or _contains_text(text, keyword)


def _contains_text(text: str, keyword: str) -> bool:
    return keyword.lower() in text.lower()


def _round_score(score: float) -> float:
    return round(max(0.0, min(100.0, score)), 2)


def _non_empty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


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
