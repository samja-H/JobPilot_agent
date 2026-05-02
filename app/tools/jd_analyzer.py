from __future__ import annotations

import re
from collections import Counter

from app.core.config import Settings
from app.schemas.job import JDAnalyzeRequest, JDAnalyzeResponse

SECTION_HEADERS: tuple[str, ...] = (
    "岗位职责",
    "工作职责",
    "职位职责",
    "职责描述",
    "任职要求",
    "职位要求",
    "岗位要求",
    "加分项",
    "优先条件",
    "bonus",
    "requirements",
    "responsibilities",
    "qualifications",
)

SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "FastAPI": ("fastapi",),
    "Django": ("django",),
    "Flask": ("flask",),
    "Java": ("java",),
    "Spring": ("spring", "spring boot", "springboot"),
    "Go": ("golang", " go ", "go语言"),
    "JavaScript": ("javascript", "js"),
    "TypeScript": ("typescript", "ts"),
    "React": ("react",),
    "Vue": ("vue", "vue.js"),
    "SQL": ("sql", "mysql", "postgresql", "postgres", "sqlite"),
    "Redis": ("redis",),
    "Docker": ("docker",),
    "Kubernetes": ("kubernetes", "k8s"),
    "Linux": ("linux",),
    "Git": ("git",),
    "REST API": ("rest", "restful", "api接口"),
    "微服务": ("微服务", "microservice", "microservices"),
    "LangChain": ("langchain",),
    "LangGraph": ("langgraph",),
    "RAG": ("rag", "检索增强", "retrieval augmented"),
    "LLM": ("llm", "大模型", "大型语言模型"),
    "Embedding": ("embedding", "向量化", "嵌入"),
    "Qdrant": ("qdrant",),
    "向量数据库": ("向量数据库", "vector database", "vector store"),
    "机器学习": ("机器学习", "machine learning", "ml"),
    "深度学习": ("深度学习", "deep learning", "dl"),
    "NLP": ("nlp", "自然语言处理"),
    "数据分析": ("数据分析", "data analysis"),
}

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "AI / RAG 应用": ("RAG", "LLM", "LangChain", "LangGraph", "Embedding", "向量数据库", "NLP"),
    "后端开发": ("Python", "FastAPI", "Django", "Flask", "Java", "Spring", "Go", "REST API", "微服务"),
    "前端开发": ("JavaScript", "TypeScript", "React", "Vue"),
    "数据 / 算法": ("机器学习", "深度学习", "数据分析"),
    "基础设施 / DevOps": ("Docker", "Kubernetes", "Linux"),
}

RESPONSIBILITY_MARKERS: tuple[str, ...] = (
    "负责",
    "参与",
    "设计",
    "开发",
    "建设",
    "优化",
    "维护",
    "implement",
    "build",
    "design",
    "develop",
    "maintain",
)

BONUS_MARKERS: tuple[str, ...] = (
    "加分",
    "优先",
    "bonus",
    "nice to have",
    "plus",
    "preferred",
)

RISK_MARKERS: dict[str, str] = {
    "加班": "JD 提到加班或高强度节奏，需要确认工作负载和团队节奏。",
    "996": "JD 存在 996 表述，需要谨慎评估工作时间预期。",
    "抗压": "JD 强调抗压能力，需要确认压力来源和支持机制。",
    "狼性": "JD 使用狼性等高压文化表述，需要评估团队文化匹配度。",
    "驻场": "JD 提到驻场，需要确认办公地点、客户环境和支持边界。",
    "外包": "JD 提到外包，需要确认雇佣主体、项目稳定性和成长空间。",
    "从0到1": "JD 强调从 0 到 1，职责范围可能较宽，需要确认资源配置。",
}


def analyze_jd_tool(request: JDAnalyzeRequest, settings: Settings) -> JDAnalyzeResponse:
    jd_text: str = request.jd_text.strip()
    if not jd_text:
        raise ValueError("JD text must not be empty")

    llm_result: JDAnalyzeResponse | None = _try_llm_analyze(jd_text, settings)
    if llm_result is not None:
        return llm_result

    return _analyze_with_rules(jd_text)


def _try_llm_analyze(jd_text: str, settings: Settings) -> JDAnalyzeResponse | None:
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

    _ = jd_text, llm_config, api_key
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


def _analyze_with_rules(jd_text: str) -> JDAnalyzeResponse:
    skills: list[str] = _extract_skills(jd_text)
    bonus_text: str = _extract_bonus_text(jd_text)
    bonus_skills: list[str] = _extract_skills(bonus_text)
    required_skills: list[str] = [skill for skill in skills if skill not in bonus_skills]
    if not required_skills:
        required_skills = skills

    responsibilities: list[str] = _extract_responsibilities(jd_text)
    job_category: str = _infer_job_category(skills, jd_text)

    return JDAnalyzeResponse(
        job_title=_extract_job_title(jd_text, job_category),
        job_category=job_category,
        responsibilities=responsibilities,
        required_skills=required_skills,
        bonus_skills=bonus_skills,
        resume_keywords=_build_resume_keywords(required_skills, bonus_skills, job_category),
        interview_topics=_build_interview_topics(required_skills, responsibilities, job_category),
        risk_points=_extract_risk_points(jd_text, responsibilities, required_skills),
        analysis_mode="rules",
    )


def _extract_skills(text: str) -> list[str]:
    normalized: str = f" {text.lower()} "
    matched: list[str] = []
    for skill, aliases in SKILL_ALIASES.items():
        if any(alias.lower() in normalized for alias in aliases):
            matched.append(skill)
    return matched


def _extract_bonus_text(jd_text: str) -> str:
    lines: list[str] = _non_empty_lines(jd_text)
    bonus_lines: list[str] = []
    in_bonus_section: bool = False

    for line in lines:
        lower_line: str = line.lower()
        if any(marker in lower_line for marker in BONUS_MARKERS):
            in_bonus_section = True
            bonus_lines.append(line)
            continue
        if in_bonus_section and _looks_like_section_header(line):
            in_bonus_section = False
        if in_bonus_section:
            bonus_lines.append(line)

    return "\n".join(bonus_lines)


def _extract_responsibilities(jd_text: str) -> list[str]:
    lines: list[str] = _non_empty_lines(jd_text)
    responsibility_lines: list[str] = []
    in_responsibility_section: bool = False

    for line in lines:
        lower_line: str = line.lower()
        if any(header.lower() in lower_line for header in ("岗位职责", "工作职责", "职位职责", "responsibilities")):
            in_responsibility_section = True
            continue
        if in_responsibility_section and _looks_like_section_header(line):
            break
        if in_responsibility_section:
            responsibility_lines.append(line)

    if not responsibility_lines:
        responsibility_lines = [
            line
            for line in lines
            if any(marker in line.lower() for marker in RESPONSIBILITY_MARKERS)
        ]

    cleaned: list[str] = [_clean_bullet(line) for line in responsibility_lines]
    return _unique_non_empty(cleaned)[:6]


def _extract_job_title(jd_text: str, job_category: str) -> str:
    lines: list[str] = _non_empty_lines(jd_text)
    title_patterns: tuple[re.Pattern[str], ...] = (
        re.compile(r"(?:岗位|职位|招聘|job title|position)[:：]\s*(.+)", re.IGNORECASE),
        re.compile(r"(.{0,30}(?:工程师|开发|架构师|研究员|算法|产品经理|designer|engineer|developer).{0,20})", re.IGNORECASE),
    )

    for line in lines[:5]:
        for pattern in title_patterns:
            match: re.Match[str] | None = pattern.search(line)
            if match:
                return _clean_bullet(match.group(1)).strip(" -")

    return f"{job_category}岗位"


def _infer_job_category(skills: list[str], jd_text: str) -> str:
    scores: Counter[str] = Counter()
    normalized_text: str = jd_text.lower()
    for category, category_skills in CATEGORY_KEYWORDS.items():
        scores[category] += sum(1 for skill in category_skills if skill in skills)

    if any(keyword in normalized_text for keyword in ("大模型", "llm", "rag", "langchain", "langgraph")):
        scores["AI / RAG 应用"] += 2
    if any(keyword in normalized_text for keyword in ("后端", "backend", "api", "服务端")):
        scores["后端开发"] += 2
    if any(keyword in normalized_text for keyword in ("前端", "frontend", "react", "vue")):
        scores["前端开发"] += 2

    if not scores:
        return "通用软件研发"
    category, _ = scores.most_common(1)[0]
    return category


def _build_resume_keywords(
    required_skills: list[str],
    bonus_skills: list[str],
    job_category: str,
) -> list[str]:
    keywords: list[str] = [job_category, *required_skills, *bonus_skills]
    keywords.extend(["项目经验", "问题排查", "性能优化", "业务结果"])
    return _unique_non_empty(keywords)[:12]


def _build_interview_topics(
    required_skills: list[str],
    responsibilities: list[str],
    job_category: str,
) -> list[str]:
    topics: list[str] = []
    for skill in required_skills[:5]:
        topics.append(f"{skill} 在真实项目中的使用经验、取舍和问题排查")

    if responsibilities:
        topics.append("围绕核心职责追问项目背景、个人贡献和量化结果")
    topics.append(f"{job_category}相关系统设计、稳定性和扩展性问题")
    return _unique_non_empty(topics)[:8]


def _extract_risk_points(
    jd_text: str,
    responsibilities: list[str],
    required_skills: list[str],
) -> list[str]:
    risk_points: list[str] = []
    for marker, message in RISK_MARKERS.items():
        if marker.lower() in jd_text.lower():
            risk_points.append(message)

    if not responsibilities:
        risk_points.append("JD 中职责描述不够清晰，建议面试中确认具体工作边界。")
    if not required_skills:
        risk_points.append("JD 中技术要求不够明确，建议确认核心技术栈和考核重点。")

    return _unique_non_empty(risk_points)


def _looks_like_section_header(line: str) -> bool:
    stripped: str = line.strip().strip(":：")
    if len(stripped) > 32:
        return False
    lower_stripped: str = stripped.lower()
    return any(header.lower() in lower_stripped for header in SECTION_HEADERS)


def _clean_bullet(line: str) -> str:
    return re.sub(r"^[\s\-*•\d.、)）]+", "", line.strip()).strip()


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
